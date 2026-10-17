import ast
import copy
import hashlib
import itertools
import json
import re
import runpy
from fractions import Fraction
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
PUBLISHER = 'ehsanisildur-ux/quota-cascade'
CANDIDATES = ['amber', 'birch', 'cedar']
EXPECTED = {
    'surplus-a': ('RANKED', CANDIDATES),
    'surplus-b': ('RANKED', ['birch', 'cedar', 'amber']),
    'surplus-c': ('RANKED', ['cedar', 'birch']),
    'elimination-a': ('RANKED', ['amber']),
    'elimination-b': ('RANKED', ['birch', 'amber', 'cedar']),
    'elimination-c': ('RANKED', ['cedar', 'birch', 'amber']),
    'review-a': ('REVIEW', []),
    'review-b': ('RANKED', ['birch', 'cedar']),
    'review-c': ('RANKED', []),
}


def source(name):
    body = (ROOT / ('ballots/' + name + '.json')).read_bytes()
    return body, 'https://raw.githubusercontent.com/' + PUBLISHER + '/' + 'a' * 40 + '/ballots/' + name + '.json', hashlib.sha256(body).hexdigest()


def mock(vm, name, decision=None, body=None, audit=True, status=200):
    raw, url, digest = source(name)
    label, order = EXPECTED[name]
    vm.clear_mocks()
    vm.mock_web(re.escape(url), {'status': status, 'body': raw if body is None else body})
    vm.mock_llm('.*CASCADE-RANK.*', json.dumps(decision if decision is not None else {'status': label, 'order': order, 'paragraph': 0}))
    vm.mock_llm('.*CASCADE-AUDIT.*', json.dumps({'valid': audit}))
    return url, digest


def deploy(factory, accounts, election='SURPLUS', weights=(6, 1, 2), seats=2, candidates=None):
    return factory(str(ROOT / 'contracts/quota_cascade.py'), PUBLISHER, election,
                   candidates or CANDIDATES, ['voter-' + chr(97+i) for i in range(len(accounts))], list(accounts), list(weights), seats)


@pytest.fixture
def accounts(direct_alice, direct_bob, direct_charlie):
    return [direct_alice, direct_bob, direct_charlie]


@pytest.fixture
def contract(direct_deploy, accounts):
    return deploy(direct_deploy, accounts)


def cast(c, vm, account, name):
    vm.sender = account
    c.cast(*mock(vm, name))
    assert vm.run_validator() is True


def test_fractional_surplus_is_consequential(contract, direct_vm, accounts):
    for a, name in zip(accounts, ['surplus-a', 'surplus-b', 'surplus-c']):
        cast(contract, direct_vm, a, name)
    contract.finalize()
    result = contract.get_state()['result']
    assert result['quota'] == 4 and result['total'] == 9
    assert result['winners'] == [0, 1]
    assert [r['action'] for r in result['rounds']] == ['ELECT_QUOTA', 'ELIMINATE', 'ELECT_REMAINING']
    assert result['rounds'][0]['transfer_factor'] == [1, 3]
    assert result['rounds'][1]['tallies'] == [[0, 1], [3, 1], [2, 1]]
    assert result['rounds'][-1]['retained'] == [9, 1]


def test_elimination_respects_final_voter_not_quote(direct_deploy, direct_vm, accounts):
    c = deploy(direct_deploy, accounts, 'ELIMINATION', (4, 3, 2), 1)
    for a, name in zip(accounts, ['elimination-a', 'elimination-b', 'elimination-c']):
        cast(c, direct_vm, a, name)
    c.finalize()
    result = c.get_state()['result']
    assert result['quota'] == 5 and result['winners'] == [1]
    assert result['rounds'][0]['candidate'] == 2


def test_review_blocks_until_own_abstention_and_preserves_statement(direct_deploy, direct_vm, accounts):
    c = deploy(direct_deploy, accounts, 'REVIEW', (6, 1, 2), 1)
    for a, name in zip(accounts, ['review-a', 'review-b', 'review-c']):
        cast(c, direct_vm, a, name)
    before = c.get_state()
    with direct_vm.expect_revert('Every voter must rank or abstain'):
        c.finalize()
    direct_vm.sender = accounts[1]
    with direct_vm.expect_revert('Only pending or unresolved voter may abstain'):
        c.abstain()
    direct_vm.sender = accounts[0]
    c.abstain()
    after = c.get_state()['voters'][0]['ballot']
    assert after['status'] == 'ABSTAIN'
    assert after['source'] == before['voters'][0]['ballot']['source']
    assert after['decision']['status'] == 'REVIEW'
    c.finalize()
    assert c.get_state()['result']['winners'] == [1]
    assert c.get_state()['result']['total'] == 1


def test_all_abstain_has_no_winner(contract, direct_vm, accounts):
    for a in accounts:
        direct_vm.sender = a
        contract.abstain()
    contract.finalize()
    assert contract.get_state()['result']['status'] == 'NO_VOTES'
    assert contract.get_state()['result']['winners'] == []


@pytest.mark.parametrize('method', ['cast', 'abstain'])
def test_unauthorized(contract, direct_vm, direct_owner, method):
    direct_vm.sender = direct_owner
    with direct_vm.expect_revert('Voter not admitted'):
        getattr(contract, method)(*source('surplus-a')[1:]) if method == 'cast' else contract.abstain()


def test_immutable_vote_and_finalization(contract, direct_vm, accounts):
    cast(contract, direct_vm, accounts[0], 'surplus-a')
    with direct_vm.expect_revert('Ballot already submitted'):
        contract.cast(*mock(direct_vm, 'surplus-a'))
    for a in accounts[1:]:
        direct_vm.sender = a
        contract.abstain()
    contract.finalize()
    for method in ['finalize', 'abstain']:
        with direct_vm.expect_revert('Election finalized'):
            getattr(contract, method)()


@pytest.mark.parametrize('decision', [
    {'status': 'RANKED', 'order': ['birch', 'amber', 'cedar'], 'paragraph': 0},
    {'status': 'REVIEW', 'order': [], 'paragraph': 0},
    {'status': 'RANKED', 'order': ['amber'], 'paragraph': 0},
])
def test_validator_independent_decision_disagreement(contract, direct_vm, accounts, decision):
    direct_vm.sender = accounts[0]
    contract.cast(*mock(direct_vm, 'surplus-a'))
    mock(direct_vm, 'surplus-a', decision=decision)
    assert direct_vm.run_validator() is False


@pytest.mark.parametrize('audit', [False, 'true', 1, None])
def test_validator_requires_substantive_boolean_audit(contract, direct_vm, accounts, audit):
    direct_vm.sender = accounts[0]
    contract.cast(*mock(direct_vm, 'surplus-a'))
    mock(direct_vm, 'surplus-a', audit=audit)
    assert direct_vm.run_validator() is False


def test_validator_refetches_and_hash_checks(contract, direct_vm, accounts):
    direct_vm.sender = accounts[0]
    contract.cast(*mock(direct_vm, 'surplus-a'))
    mock(direct_vm, 'surplus-a', body=b'changed full source')
    assert direct_vm.run_validator() is False


@pytest.mark.parametrize('decision', [
    {}, {'status': 'OTHER', 'order': [], 'paragraph': 0},
    {'status': 'RANKED', 'order': ['amber', 'amber'], 'paragraph': 0},
    {'status': 'RANKED', 'order': ['intruder'], 'paragraph': 0},
    {'status': 'RANKED', 'order': CANDIDATES, 'paragraph': True},
    {'status': 'RANKED', 'order': CANDIDATES, 'paragraph': -1},
    {'status': 'REVIEW', 'order': ['amber'], 'paragraph': 0},
])
def test_malformed_model_never_stores_ballot(contract, direct_vm, accounts, decision):
    direct_vm.sender = accounts[0]
    with direct_vm.expect_revert('LLM_ERROR'):
        contract.cast(*mock(direct_vm, 'surplus-a', decision=decision))
    assert contract.get_state()['voters'][0]['ballot'] == {'status': 'PENDING'}


@pytest.mark.parametrize('name', ['surplus-b', 'review-a'])
def test_source_cannot_impersonate_voter_or_election(contract, direct_vm, accounts, name):
    direct_vm.sender = accounts[0]
    with direct_vm.expect_revert('Ballot election or voter mismatch'):
        contract.cast(*mock(direct_vm, name))


@pytest.mark.parametrize('body', [b'not JSON', b'\xff', b'{"election":"SURPLUS","election":"SURPLUS"}', b'x' * 8001])
def test_bad_source(contract, direct_vm, accounts, body):
    direct_vm.sender = accounts[0]
    url, _ = mock(direct_vm, 'surplus-a', body=body)
    with direct_vm.expect_revert('EXTERNAL'):
        contract.cast(url, hashlib.sha256(body).hexdigest())


@pytest.mark.parametrize('suffix,digest', [('/main/ballots/a.json', 'f'*64), ('/'+'a'*40+'/ballots/a.json', 'z'*64), ('/'+'a'*40+'/elsewhere/a.json', 'f'*64)])
def test_locator_restrictions(contract, direct_vm, accounts, suffix, digest):
    direct_vm.sender = accounts[0]
    with direct_vm.expect_revert('Commit-pinned ballot'):
        contract.cast('https://raw.githubusercontent.com/' + PUBLISHER + suffix, digest)


def pure():
    tree = ast.parse((ROOT / 'contracts/quota_cascade.py').read_text())
    tree.body = [n for n in tree.body if not isinstance(n, ast.ClassDef) and not (isinstance(n, ast.ImportFrom) and n.module == 'genlayer')]
    namespace = {}
    exec(compile(tree, '<pure>', 'exec'), namespace)
    return namespace


def oracle(orders, powers, count, seats):
    """Independent parcel ledger using Fraction, explicit owners, and sorting."""
    if sum(powers) == 0:
        return [], []
    quota = sum(powers) // (seats + 1) + 1
    parcels = [[list(order), Fraction(w)] for order, w in zip(orders, powers)]
    alive, winners, snapshots = set(range(count)), [], []
    while alive and len(winners) < seats:
        piles = {c: [] for c in alive}
        for p in parcels:
            while p[0] and p[0][0] not in alive:
                p[0].pop(0)
            if p[0]:
                piles[p[0][0]].append(p)
        totals = {c: sum((p[1] for p in pile), Fraction()) for c, pile in piles.items()}
        eligible = sorted((c for c in alive if totals[c] >= quota), key=lambda c: (-totals[c], c))
        if len(alive) <= seats - len(winners):
            c, action, factor = min(alive), 'ELECT_REMAINING', Fraction()
        elif eligible:
            c = eligible[0]
            action, factor = 'ELECT_QUOTA', (totals[c] - quota) / totals[c]
        else:
            c = min(alive, key=lambda i: (totals[i], -i))
            action, factor = 'ELIMINATE', Fraction(1)
        for p in piles[c]:
            p[1] *= factor
        alive.remove(c)
        if action != 'ELIMINATE':
            winners.append(c)
        snapshots.append((action, c, factor))
    return winners, snapshots


def test_exhaustive_rankings_against_independent_fraction_oracle():
    run = pure()['count_votes']
    full_reference = runpy.run_path(str(ROOT / 'scripts/check-state.py'))['reference']
    orders = list(itertools.permutations(range(3))) + [(0,), (1,), (2,), (0, 2)]
    cases = 0
    for ballot_orders in itertools.product(orders, repeat=3):
        for seats in (1, 2):
            result = run(ballot_orders, [6, 3, 2], 3, seats)
            assert result == full_reference(ballot_orders, [6, 3, 2], 3, seats)
            winners, trace = oracle(ballot_orders, [6, 3, 2], 3, seats)
            assert result['winners'] == winners
            assert [(r['action'], r['candidate'], Fraction(*r['transfer_factor'])) for r in result['rounds']] == trace
            for r in result['rounds']:
                assert sum((Fraction(*r[k]) for k in ('retained', 'active_after', 'exhausted_after')), Fraction()) == 11
            cases += 1
    assert cases == 2000


def test_tie_breaking_zero_support_exhaustion_and_multi_surplus():
    run = pure()['count_votes']
    for orders, weights, n, seats in [
        ([[0], [1], [2]], [1, 1, 1], 3, 1),
        ([[0], [1], [2]], [2, 1, 1], 3, 1),
        ([[0]], [1], 5, 3),
        ([[0, 1, 2, 3], [1, 2, 3], [2, 3]], [20, 11, 2], 4, 3),
    ]:
        result = run(orders, weights, n, seats)
        assert result['winners'] == oracle(orders, weights, n, seats)[0]
    assert run([[0], [1], [2]], [1, 1, 1], 3, 1)['winners'] == [0]
    exhausted = run([[0], [1], [2]], [2, 1, 1], 3, 1)
    assert any(r['exhausted_after'][0] > 0 for r in exhausted['rounds'])


@pytest.mark.parametrize('seats', [0, 3, True])
def test_constructor_seats(direct_deploy, accounts, seats):
    with pytest.raises(Exception, match='Invalid seats'):
        deploy(direct_deploy, accounts, seats=seats)


def test_constructor_accepts_actual_calldata_address_objects(direct_deploy, accounts, monkeypatch):
    from gltest.direct import loader
    original = loader._allocate_contract
    def allocate(cls, vm, *args, **kwargs):
        from genlayer import Address
        native = list(args)
        native[4] = [Address(a) for a in native[4]]
        return original(cls, vm, *native, **kwargs)
    monkeypatch.setattr(loader, '_allocate_contract', allocate)
    c = deploy(direct_deploy, accounts)
    assert [v['address'] for v in c.get_state()['voters']] == ['0x' + a.hex() for a in accounts]


@pytest.mark.parametrize('case', ['duplicate-wallet', 'duplicate-id', 'zero-wallet', 'zero-weight', 'large-weight', 'boolean-weight', 'missing-wallet', 'missing-weight'])
def test_constructor_rejects_invalid_native_roster(direct_deploy, accounts, case):
    ids, addresses, weights = ['voter-a', 'voter-b', 'voter-c'], list(accounts), [6, 1, 2]
    if case == 'duplicate-wallet': addresses[1] = addresses[0]
    if case == 'duplicate-id': ids[1] = ids[0]
    if case == 'zero-wallet': addresses[0] = bytes(20)
    if case == 'zero-weight': weights[0] = 0
    if case == 'large-weight': weights[0] = 21
    if case == 'boolean-weight': weights[0] = True
    if case == 'missing-wallet': addresses.pop()
    if case == 'missing-weight': weights.pop()
    with pytest.raises(Exception, match='Invalid weighted voter|One to eight voters required'):
        direct_deploy(str(ROOT / 'contracts/quota_cascade.py'), PUBLISHER, 'SURPLUS', CANDIDATES, ids, addresses, weights, 2)
