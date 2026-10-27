"""Node endpoint + Python reader integration, all channel/image dependencies faked.
Uses synthetic in-memory PNG 1x1 white pixel, NEVER an actual pairing QR.
"""
from concurrent.futures import ThreadPoolExecutor
import http.client
import importlib.util
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'tests'))
from viewer_core import GatewayReader
from test_viewer_core import PNG

BAILEYS=r'''
import {EventEmitter} from 'node:events';
import {existsSync,readFileSync,writeFileSync} from 'node:fs';
import {join} from 'node:path';
export async function useMultiFileAuthState(){return {state:{creds:{registered:false},keys:{}},saveCreds:async()=>{}};}
export function generateMessageIDV2(){throw Error('send forbidden in viewer test');}
export default function makeWASocket(){
 const ev=new EventEmitter(); let seq=0;
 const timer=setInterval(()=>{
  const path=join(process.env.DATA_DIR,'control.json');if(!existsSync(path))return;
  const cmd=JSON.parse(readFileSync(path,'utf8')); if(cmd.seq<=seq)return; seq=cmd.seq;
  ev.emit('connection.update',cmd.update);writeFileSync(join(process.env.DATA_DIR,'applied'),String(seq));
 },10);
 return {ev,end(){clearInterval(timer);},sendMessage(){throw Error('send forbidden in viewer test');}};
}
'''
QRCODE=r'''
import {existsSync,writeFileSync} from 'node:fs';import {join} from 'node:path';
export default {async toBuffer(value){
 if(value==='synthetic-race'){
  writeFileSync(join(process.env.DATA_DIR,'render-started'),'yes');
  while(!existsSync(join(process.env.DATA_DIR,'render-release')))await new Promise(r=>setTimeout(r,10));
 }
 return Buffer.from(process.env.SYNTHETIC_PIXEL,'base64');
}};
'''

def wait_until(check):
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        if check(): return
        time.sleep(.02)
    raise AssertionError('Synthetic HTTP condition not reached')

class MockHttpTests(unittest.TestCase):
    def test_frame_auth_rotation_latch_race_and_reader(self):
        import base64
        if not shutil.which('node'): self.skipTest('Node unavailable; no install attempted')
        with tempfile.TemporaryDirectory(prefix='private_viewer_mock_') as folder:
            work=Path(folder); data=work/'data';data.mkdir()
            with socket.socket() as probe:
                probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
            for name in ['server.mjs','guard.mjs','disconnect-diagnostic.mjs','qr-lifecycle.mjs','qr-frame.mjs']:
                content=(ROOT/'gateway'/name).read_text()
                # Temporary test copy only; production candidate stays fixed at127.0.0.1:3210.
                if name=='server.mjs': content=content.replace('server.listen(3210, bindHost',f'server.listen({port}, bindHost')
                (work/name).write_text(content)
            for name,code in [('baileys',BAILEYS),('qrcode',QRCODE)]:
                target=work/'node_modules'/name;target.mkdir(parents=True)
                (target/'package.json').write_text(json.dumps({'name':name,'type':'module','exports':'./index.mjs'}))
                (target/'index.mjs').write_text(code)
            token=secrets.token_hex(32)
            env={**os.environ,'GATEWAY_TOKEN':token,'ALLOWED_NUMBERS':'+15555550123','WHATSAPP_PAIRING_CONSENT':'SIM',
                 'DATA_DIR':str(data),'GATEWAY_BIND_HOST':'127.0.0.1','SYNTHETIC_PIXEL':base64.b64encode(PNG).decode()}
            proc=subprocess.Popen(['node','server.mjs'],cwd=work,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            def call(auth=True,origin=None):
                conn=http.client.HTTPConnection('127.0.0.1',port,timeout=3)
                headers={'Authorization':'Bearer '+token} if auth else {}
                if origin:headers['Origin']=origin
                try:
                    conn.request('GET','/qr/frame',headers=headers);r=conn.getresponse()
                    return r.status,json.loads(r.read()),dict(r.headers)
                finally:conn.close()
            seq=0
            def emit(update):
                nonlocal seq
                seq+=1
                tmp=data/'control.tmp';tmp.write_text(json.dumps({'seq':seq,'update':update}));tmp.replace(data/'control.json')
                wait_until(lambda:(data/'applied').exists() and (data/'applied').read_text()==str(seq))
            def ready():
                if proc.poll() is not None: raise AssertionError('Mock Node process exited; no real gateway involved')
                try:return call()[0]==200
                except OSError:return False
            try:
                wait_until(ready)
                self.assertEqual(call(False)[0],401)
                self.assertEqual(call(origin='https://outside.invalid')[0],403)
                self.assertEqual(call()[1]['png_base64'],'')
                emit({'qr':'synthetic-one'})
                code,first,headers=call();self.assertEqual(code,200)
                self.assertEqual(headers['Cache-Control'],'no-store');self.assertEqual(first['generation'],1)
                self.assertEqual(base64.b64decode(first['png_base64']),PNG)
                self.assertNotIn('synthetic-one',json.dumps(first))
                reader=GatewayReader(token,connection_factory=lambda host,ignored_port,timeout:http.client.HTTPConnection(host,port,timeout=timeout))
                self.assertEqual(reader.fetch().frame.png,PNG)
                emit({'qr':'synthetic-two'});self.assertEqual(call()[1]['generation'],2)
                emit({'qr':'synthetic-race'})
                with ThreadPoolExecutor(max_workers=1) as pool:
                    future=pool.submit(call);wait_until(lambda:(data/'render-started').exists())
                    emit({'isNewLogin':True});(data/'render-release').write_text('release')
                    code,body,_=future.result(timeout=3)
                    self.assertEqual(code,409);self.assertEqual(body['png_base64'],'')
                emit({'qr':'synthetic-late-timer'})
                self.assertIsNone(reader.fetch().frame);self.assertEqual(call()[1]['png_base64'],'')
                emit({'connection':'close','lastDisconnect':{'error':{'output':{'statusCode':408}}}})
                self.assertIsNone(reader.fetch().frame)
                self.assertFalse((data/'send-journal.json').exists())
                self.assertFalse(list(work.rglob('*.png')));self.assertFalse(list(work.rglob('*.svg')))
            finally:
                proc.terminate();stdout,stderr=proc.communicate(timeout=5)
                self.assertNotIn(token,stdout+stderr)
                self.assertNotIn('synthetic-',stdout+stderr)

if __name__=='__main__':unittest.main()
