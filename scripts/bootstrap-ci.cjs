// Encrypted disposable CLI accounts; no private key is exported.
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto');
if(!process.env.GITHUB_ACTIONS||!process.env.GITHUB_ENV)throw Error('Disposable CI runner only');
const cli=path.join(cp.execFileSync('npm',['root','-g'],{encoding:'utf8'}).trim(),'genlayer/dist/index.js');
const password=crypto.randomBytes(24).toString('hex');console.log('::add-mask::'+password);
const accounts=[];
for(let i=0;i<4;i++){
 const name='cascade-proof-'+i;
 const out=cp.execFileSync(process.execPath,[cli,'account','create','--name',name,'--password',password],{encoding:'utf8',stdio:['ignore','pipe','pipe']});
 const address=out.match(/0x[a-fA-F0-9]{40}/)?.[0];
 if(!address)throw Error('Account creation did not return a public address');
 accounts.push({name,address:address.toLowerCase()});
}
cp.execFileSync(process.execPath,[cli,'network','set','studionet'],{stdio:['ignore','ignore','pipe']});
fs.appendFileSync(process.env.GITHUB_ENV,`GENLAYER_CLI_PATH=${cli}\nCASCADE_PASSWORD=${password}\nCASCADE_ACCOUNTS=${JSON.stringify(accounts)}\n`);
console.log('Prepared four encrypted test accounts: '+accounts.map(a=>a.address).join(', '));
