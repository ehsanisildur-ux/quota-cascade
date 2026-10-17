const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process');
const {root,assert,equal,digest,sourceHash,save,invoke,read,rpc,receipt,delay}=require('./transport.cjs');
const publisher='ehsanisildur-ux/quota-cascade',candidates=['amber','birch','cedar'];
const cases=[{name:'surplus',weights:[6,1,2],seats:2,winners:[0,1]},{name:'elimination',weights:[4,3,2],seats:1,winners:[1]},{name:'review',weights:[6,1,2],seats:1,winners:[1]}];
async function main(){
 assert(await rpc('eth_chainId',[])==='0xf22f','Gasless StudioNet only');
 const accounts=JSON.parse(process.env.CASCADE_ACCOUNTS||'null');assert(accounts?.length===4,'Four public test account descriptors required');
 const revision=fs.readFileSync(path.join(root,'config/fixture-revision.txt'),'utf8').trim();assert(/^[a-f0-9]{40}$/.test(revision),'Pinned fixture commit');
 const manifests=[];
 for(const test of cases){
  const {name}=test,election=name.toUpperCase(),fixtures=[];
  for(let i=0;i<3;i++){
   const file=`${name}-${String.fromCharCode(97+i)}.json`,body=fs.readFileSync(path.join(root,'ballots',file)),url=`https://raw.githubusercontent.com/${publisher}/${revision}/ballots/${file}`;
   const res=await fetch(url,{signal:AbortSignal.timeout(45000)});assert(res.ok&&body.equals(Buffer.from(await res.arrayBuffer())),'Published fixture mismatch');
   fixtures.push({url,sha256:digest(body),source:JSON.parse(body)});
  }
  const voters=accounts.slice(0,3).map((a,i)=>({id:'voter-'+String.fromCharCode(97+i),address:a.address,weight:test.weights[i]}));
  process.env.CASCADE_ACCOUNT=accounts[0].name;
  const deployHash=await invoke(name+'-deployment',['deploy','--contract','contracts/quota_cascade.py','--args',publisher,election,JSON.stringify(candidates),JSON.stringify(voters.map(v=>v.id)),JSON.stringify(voters.map(v=>v.address)),JSON.stringify(test.weights),String(test.seats)]);
  const r=await receipt(name+'-deployment',deployHash,true),contract=r.to_address||r.recipient;
  assert(/^0x[a-f0-9]{40}$/i.test(contract),'Deployment address');
  assert(fs.readFileSync(path.join(root,'contracts/quota_cascade.py')).equals(Buffer.from(await rpc('gen_getContractCode',[contract]),'base64')),'Exact deployed source');
  const manifest={name,publisher,election,candidates,voters,seats:test.seats,contract,transaction:deployHash,source_sha256:sourceHash,fixture_revision:revision,fixtures,network:'studionet',chain_id:61999};
  manifests.push(manifest);save('deployments',manifests);
  let state=await read(name+'-initial',['call',contract,'get_state']);
  assert(equal(state,{publisher,election,candidates,voters:voters.map(v=>({...v,ballot:{status:'PENDING'}})),seats:test.seats,result:null}),'Initial roster');
  save(name+'-initial-state',state);
  async function step(label,args,account,success,reason){
   process.env.CASCADE_ACCOUNT=accounts[account].name;
   const before=state,hash=await invoke(label,args);const rr=await receipt(label,hash,success);
   state=await read(label+'-state',['call',contract,'get_state']);
   if(!success){
    assert(equal(before,state),'Rejected call changed state');
    const decoded=await read(label+'-decoded',['receipt',hash,'--status','FINALIZED','--retries','2']);
    assert(JSON.stringify(decoded).includes(reason),'Incorrect rejection reason');save(label+'-decoded-receipt',decoded);
   }
   const from=rr.from_address||rr.sender;assert(typeof from==='string'&&from.toLowerCase()===accounts[account].address,'Actual signing voter');
   save(label,{contract,transaction:hash,sender:accounts[account].address,success,reason:reason||null,args,state_before:before,state});
  }
  if(name==='surplus'){
   await step('unauthorized',['write',contract,'abstain'],3,false,'[EXPECTED] Voter not admitted');
   await step('bad-hash',['write',contract,'cast','--args',fixtures[0].url,'f'.repeat(64)],0,false,'[EXTERNAL] Ballot commitment mismatch');
  }
  for(let i=0;i<3;i++){
   const f=fixtures[i];await step(name+'-cast-'+i,['write',contract,'cast','--args',f.url,f.sha256],i,true);
   const b=state.voters[i].ballot;assert(b.url===f.url&&b.sha256===f.sha256&&equal(b.source,f.source),'Source bound ballot');
   const expected=name==='review'?[[],['birch','cedar'],[]]:name==='surplus'?[['amber','birch','cedar'],['birch','cedar','amber'],['cedar','birch']]:[['amber'],['birch','amber','cedar'],['cedar','birch','amber']];
   assert(b.status===(name==='review'&&i===0?'REVIEW':'RANKED')&&equal(b.decision.order,expected[i]),'Substantive ranking differs');
   await delay(3000);
  }
  if(name==='surplus')await step('duplicate',['write',contract,'cast','--args',fixtures[0].url,fixtures[0].sha256],0,false,'[EXPECTED] Ballot already submitted');
  if(name==='review'){
   await step('review-blocked',['write',contract,'finalize'],1,false,'[EXPECTED] Every voter must rank or abstain');
   await step('review-abstain',['write',contract,'abstain'],0,true);
   assert(state.voters[0].ballot.decision.status==='REVIEW','Preserved unresolved decision');
  }
  await step(name+'-finalize',['write',contract,'finalize'],3,true);
  assert(equal(state.result.winners,test.winners),'Scenario winners');
  cp.execFileSync(process.env.CASCADE_PYTHON||'python',[path.join(__dirname,'check-state.py')],{input:JSON.stringify(state),stdio:['pipe','inherit','pipe'],windowsHide:true});
  save(name+'-final-state',state);console.log('VERIFIED',name,contract);
 }
}
main().catch(e=>{console.error(e.stack,e.cause?.message||'');process.exitCode=1;});
