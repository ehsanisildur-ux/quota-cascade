const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process');
const {root,assert,equal,digest,rpc,read,receiptSummary,save}=require('./transport.cjs');
const load=n=>JSON.parse(fs.readFileSync(path.join(root,'proofs',n+'.json')));
async function main(){
 const offline=process.argv.includes('--offline'),deployments=load('deployments'),code=fs.readFileSync(path.join(root,'contracts/quota_cascade.py'));
 assert(deployments.length===3&&equal(deployments.map(d=>d.name),['surplus','elimination','review']),'Three scenarios');
 const journal=load('transactions'),all=new Set(),summary={source_sha256:digest(code),mode:offline?'offline-artifact':'fresh-rpc-and-state',contracts:[],transactions:[]};
 assert(journal.source_sha256===digest(code),'Journal source');
 if(!offline)assert(await rpc('eth_chainId',[])==='0xf22f','StudioNet only');
 async function verify(label,hash,contract,success,sender){
  assert(!all.has(hash)&&journal.hashes[label]===hash,'Unique journal-bound receipt');all.add(hash);
  const saved=load(label+'-receipt'),r=offline?saved:await rpc('eth_getTransactionByHash',[hash]),s=receiptSummary(r);
  assert(s.hash===hash&&s.status==='FINALIZED'&&s.result==='MAJORITY_AGREE'&&s.agree>(s.agree+s.disagree+s.idle)/2,'Finalized strict majority');
  assert((r.to_address||r.recipient).toLowerCase()===contract.toLowerCase(),'Receipt destination');
  assert(equal(r.consensus_data.votes,saved.consensus_data.votes),'Saved vote binding');
  assert(success?['SUCCESS','FINISHED_WITH_RETURN'].includes(s.execution):s.execution==='ERROR','Execution result');
  if(sender)assert((r.from_address||r.sender).toLowerCase()===sender,'Signing wallet');
  summary.transactions.push({label,...s});
 }
 for(const d of deployments){
  const {name,contract}=d;
  assert(d.publisher==='ehsanisildur-ux/quota-cascade'&&d.network==='studionet'&&d.chain_id===61999&&d.source_sha256===digest(code),'Deployment/source domain');
  assert(d.fixture_revision===fs.readFileSync(path.join(root,'config/fixture-revision.txt'),'utf8').trim(),'Pinned source revision');
  assert(d.voters.length===3&&new Set(d.voters.map(v=>v.address)).size===3,'Distinct voter wallets');
  await verify(name+'-deployment',d.transaction,contract,true,d.voters[0].address);
  if(!offline)assert(code.equals(Buffer.from(await rpc('gen_getContractCode',[contract]),'base64')),'Live deployed code');
  let previous=load(name+'-initial-state');
  assert(equal(previous,{publisher:d.publisher,election:d.election,candidates:d.candidates,voters:d.voters.map(v=>({...v,ballot:{status:'PENDING'}})),seats:d.seats,result:null}),'Initial state');
  const labels=name==='surplus'?['unauthorized','bad-hash',...Array.from({length:3},(_,i)=>name+'-cast-'+i),'duplicate',name+'-finalize']:name==='review'?[...Array.from({length:3},(_,i)=>name+'-cast-'+i),'review-blocked','review-abstain',name+'-finalize']:[...Array.from({length:3},(_,i)=>name+'-cast-'+i),name+'-finalize'];
  for(const label of labels){
   const p=load(label);assert(p.contract===contract&&equal(p.state_before,previous),'Proof state chain');
   assert(p.args[0]==='write'&&p.args[1]===contract,'CLI command target');
   await verify(label,p.transaction,contract,p.success,p.sender);
   if(!p.success){assert(equal(p.state,previous),'Rejected mutation');assert(JSON.stringify(load(label+'-decoded-receipt')).includes(p.reason),'Rejection reason');}
   previous=p.state;
  }
  for(let i=0;i<3;i++){
   const f=d.fixtures[i],bytes=fs.readFileSync(path.join(root,'ballots',`${name}-${String.fromCharCode(97+i)}.json`)),b=previous.voters[i].ballot;
   assert(f.url===`https://raw.githubusercontent.com/${d.publisher}/${d.fixture_revision}/ballots/${name}-${String.fromCharCode(97+i)}.json`&&f.sha256===digest(bytes)&&equal(f.source,JSON.parse(bytes)),'Pinned fixture binding');
   assert(b.url===f.url&&b.sha256===f.sha256&&equal(b.source,f.source),'Accepted full source binding');
   const expected=name==='review'?[[],['birch','cedar'],[]]:name==='surplus'?[['amber','birch','cedar'],['birch','cedar','amber'],['cedar','birch']]:[['amber'],['birch','amber','cedar'],['cedar','birch','amber']];
   assert(equal(b.decision.order,expected[i])&&b.decision.status===(name==='review'&&i===0?'REVIEW':'RANKED'),'Independent scenario semantics');
   assert(b.status===(name==='review'&&i===0?'ABSTAIN':'RANKED'),'Final ballot disposition');
  }
  assert(equal(previous,load(name+'-final-state')),'Final snapshot');
  cp.execFileSync(process.env.CASCADE_PYTHON||'python',[path.join(__dirname,'check-state.py')],{input:JSON.stringify(previous),stdio:['pipe','inherit','pipe'],windowsHide:true});
  assert(equal(previous.result.winners,name==='surplus'?[0,1]:[1]),'Expected seat assignment');
  if(!offline)assert(equal(previous,await read(name+'-fresh',['call',contract,'get_state'])),'Fresh state');
  summary.contracts.push({name,contract,winners:previous.result.winners});
 }
 assert(all.size===20&&Object.keys(journal.hashes).length===20,'Complete twenty-receipt proof set');
 if(!offline){summary.live_state_match=true;save('verification',summary);}
 console.log(JSON.stringify(summary,null,2));
}
main().catch(e=>{console.error(e.stack);process.exitCode=1;});
