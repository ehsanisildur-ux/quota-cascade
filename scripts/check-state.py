"""Independent proof oracle: never imports or executes the contract source."""
import json
import sys
from fractions import Fraction as F


def pair(value):
    return [value.numerator, value.denominator]


def reference(orders, powers, size, seats):
    total = sum(powers)
    quota = total // (seats + 1) + 1
    if total == 0:
        return dict(status='NO_VOTES', quota=quota, total=0, winners=[], rounds=[])
    alive, winners, rounds = set(range(size)), [], []
    parcels = [[list(order), F(w)] for order, w in zip(orders, powers)]
    locked_total = F()

    def piles():
        result = {c: [] for c in alive}
        exhausted = F()
        for p in parcels:
            while p[0] and p[0][0] not in alive:
                p[0].pop(0)
            if p[0]:
                result[p[0][0]].append(p)
            else:
                exhausted += p[1]
        return result, exhausted

    while alive and len(winners) < seats:
        buckets, exhausted = piles()
        tallies = {c: sum((p[1] for p in bucket), F()) for c, bucket in buckets.items()}
        qualified = sorted((c for c in alive if tallies[c] >= quota), key=lambda c: (-tallies[c], c))
        if len(alive) <= seats - len(winners):
            chosen, action, factor = min(alive), 'ELECT_REMAINING', F()
        elif qualified:
            chosen = qualified[0]
            action, factor = 'ELECT_QUOTA', (tallies[chosen] - quota) / tallies[chosen]
        else:
            chosen = min(alive, key=lambda c: (tallies[c], -c))
            action, factor = 'ELIMINATE', F(1)
        locked = tallies[chosen] * (1 - factor)
        for p in buckets[chosen]:
            p[1] *= factor
        locked_total += locked
        if action != 'ELIMINATE':
            winners.append(chosen)
        alive.remove(chosen)
        after, exhausted_after = piles()
        active = sum((p[1] for bucket in after.values() for p in bucket), F())
        assert active + exhausted_after + locked_total == total
        rounds.append(dict(action=action, candidate=chosen, tallies=[pair(tallies.get(c, F())) for c in range(size)],
                           exhausted_before=pair(exhausted), transfer_factor=pair(factor), locked_this_round=pair(locked),
                           retained=pair(locked_total), continuing=sorted(alive), active_after=pair(active), exhausted_after=pair(exhausted_after)))
    return dict(status='COUNTED', quota=quota, total=total, winners=winners, rounds=rounds)


def check(state):
    candidates, orders, powers = state['candidates'], [], []
    for row in state['voters']:
        ballot = row['ballot']
        assert ballot['status'] in ('RANKED', 'ABSTAIN')
        if ballot['status'] == 'RANKED' and ballot['decision']['order']:
            orders.append([candidates.index(c) for c in ballot['decision']['order']])
            powers.append(row['weight'])
    assert state['result'] == reference(orders, powers, len(candidates), state['seats']), 'Independent count differs'


if __name__ == '__main__':
    check(json.load(sys.stdin))
    print('Independent full-round oracle passed')
