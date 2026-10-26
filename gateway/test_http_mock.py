"""Offline integration test: temporary, locally-written Baileys mock; NO WhatsApp.
Run: python gateway/test_http_mock.py. Requires Node only, no npm packages.
"""
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
MOCK = r'''
import {EventEmitter} from 'node:events';
import {appendFileSync} from 'node:fs';
import {join} from 'node:path';
export async function useMultiFileAuthState() {return {state:{creds:{registered:true},keys:{}},saveCreds:async()=>{appendFileSync(join(process.env.DATA_DIR,'mock-creds-saved'),'x');}};}
let sequence=0, connections=0;
export function generateMessageIDV2() {return 'MOCK-SEND-'+(++sequence);}
export default function makeWASocket() {
  const ev=new EventEmitter();
  const connection=++connections;
  appendFileSync(join(process.env.DATA_DIR,'mock-connect-count'),'x');
  setTimeout(()=>{
    if(connection===1) {ev.emit('connection.update',{connection:'close',lastDisconnect:{error:{output:{statusCode:515}}}}); return;}
    ev.emit('connection.update',{connection:'open'});
    ev.emit('messages.upsert',{type:'notify',messages:['FAKE-A','FAKE-B'].map(id=>({
      key:{id,remoteJid:'15555550123@s.whatsapp.net',fromMe:false},
      messageTimestamp:Math.ceil(Date.now()/1000),message:{conversation:'Synthetic inbound; no person.'}
    }))});
  },50);
  return {ev,user:{id:'synthetic-self'},end(){},async sendMessage(jid,content,options) {
    appendFileSync(join(process.env.DATA_DIR,'mock-send-count'),'x');
    if(content.text==='SIMULATE_UNCERTAIN') throw new Error('synthetic transport failure');
    ev.emit('messages.upsert',{type:'notify',messages:[{key:{id:options.messageId,remoteJid:jid,fromMe:true},messageTimestamp:Math.ceil(Date.now()/1000),message:{conversation:content.text}}]});
    return {key:{id:options.messageId}};
  }};
}
'''

def main():
    if not shutil.which('node'):
        raise SystemExit('Node required; no dependencies will be installed.')
    with tempfile.TemporaryDirectory(prefix='kit_mock_gateway_') as temp:
        work = Path(temp)
        for name in ('server.mjs', 'guard.mjs'):
            shutil.copy2(ROOT / name, work / name)
        mock_dir = work / 'node_modules' / 'baileys'
        mock_dir.mkdir(parents=True)
        (mock_dir / 'package.json').write_text(json.dumps({'name':'baileys','type':'module','exports':'./index.mjs'}))
        (mock_dir / 'index.mjs').write_text(MOCK)
        data=work/'data'; data.mkdir()
        token=secrets.token_urlsafe(32)
        env={**os.environ,'GATEWAY_TOKEN':token,'ALLOWED_NUMBERS':'+15555550123','WHATSAPP_PAIRING_CONSENT':'SIM','DATA_DIR':str(data)}
        proc=subprocess.Popen(['node','server.mjs'],cwd=work,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        def call(path,body=None):
            headers={'Authorization':'Bearer '+token}
            if body is not None: headers['Content-Type']='application/json'
            req=urllib.request.Request('http://127.0.0.1:3210'+path,headers=headers,data=json.dumps(body).encode() if body is not None else None)
            try:
                with urllib.request.urlopen(req,timeout=3) as response: return response.status,json.load(response)
            except urllib.error.HTTPError as error: return error.code,json.load(error)
        try:
            for _ in range(50):
                if proc.poll() is not None: raise RuntimeError('Temporary mock server failed: '+proc.stderr.read())
                try:
                    code,result=call('/events')
                    if code==200 and len(result['events'])==2: break
                except OSError: pass
                time.sleep(.1)
            else: raise AssertionError('Mock events not available; verify loopback port3210 unused.')
            assert (data/'mock-connect-count').read_text()=='xx', 'Handshake transport restart not bounded to once'
            assert (data/'mock-creds-saved').exists(), 'Credentials not saved before handshake restart'
            first, second=result['events']
            send={'event_id':first['id'],'chat_id':first['chat_id'],'text':'Synthetic approved reply','idempotency_key':'mock_idempotency_0001'}
            code,receipt=call('/send',send); assert code==200 and receipt['state']=='sent', (code,receipt)
            assert call('/send',send)==(200,receipt)
            assert (data/'mock-send-count').read_text()=='x', 'Duplicate network effect'
            assert call('/send',{**send,'idempotency_key':'mock_idempotency_0002'})[0]==409
            assert call('/send',{**send,'event_id':'missing_event'})[0]==400
            bad={'event_id':second['id'],'chat_id':second['chat_id'],'text':'SIMULATE_UNCERTAIN','idempotency_key':'mock_idempotency_0003'}
            code,result=call('/send',bad); assert code==502 and result['state']=='uncertain', (code,result)
            code,result=call('/send',bad); assert code==409 and result['state']=='uncertain', (code,result)
            assert (data/'mock-send-count').read_text()=='xx', 'Uncertain send retried'
            assert len(call('/events')[1]['events'])==2, 'Own generated send mistaken for human takeover'
            journal=json.loads((data/'send-journal.json').read_text())
            assert journal[first['id']]['state']=='sent' and journal[second['id']]['state']=='uncertain'
            print('PASS: mocked HTTP integration; one saved-session515 restart; duplicate/uncertain sends blocked; journal persisted; no real Baileys/WhatsApp.')
        finally:
            proc.terminate()
            proc.wait(timeout=5)

if __name__=='__main__':
    main()
