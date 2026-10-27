"""Offline QR HTTP regression: locally written Baileys/qrcode fakes only.
No dependencies installed, credentials used, or connection to WhatsApp.
Run separately from test_http_mock.py; both use loopback port 3210.
"""
from concurrent.futures import ThreadPoolExecutor
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
BAILEYS = r'''
import {EventEmitter} from 'node:events';
import {existsSync,readFileSync,writeFileSync} from 'node:fs';
import {join} from 'node:path';
export async function useMultiFileAuthState() {return {state:{creds:{registered:false},keys:{}},saveCreds:async()=>{}};}
export function generateMessageIDV2() {throw new Error('No send in QR test');}
export default function makeWASocket() {
  const ev=new EventEmitter(); let sequence=0;
  const timer=setInterval(()=>{
    const path=join(process.env.DATA_DIR,'control.json');
    if(!existsSync(path)) return;
    const command=JSON.parse(readFileSync(path,'utf8'));
    if(command.sequence<=sequence) return;
    sequence=command.sequence;
    const update=command.clearQr?{qr:undefined}:command.update;
    ev.emit('connection.update',update);
    writeFileSync(join(process.env.DATA_DIR,'applied'),String(sequence));
  },10);
  return {ev,end(){clearInterval(timer);},sendMessage(){throw new Error('No send in QR test');}};
}
'''
QRCODE = r'''
import {existsSync,writeFileSync} from 'node:fs';
import {join} from 'node:path';
export default {async toString(value) {
  if(value.startsWith('synthetic-race')) {
    writeFileSync(join(process.env.DATA_DIR,'render-started'),'yes');
    const deadline=Date.now()+3000;
    while(!existsSync(join(process.env.DATA_DIR,'render-release')) && Date.now()<deadline)
      await new Promise(resolve=>setTimeout(resolve,10));
  }
  return '<svg>'+value+'</svg>'; // Deliberately NOT an actual QR.
}};
'''


def wait_for(check, label):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if check():
            return
        time.sleep(.02)
    raise AssertionError(label)


def run_case(terminal):
    if not shutil.which('node'):
        raise SystemExit('Node required; no dependencies will be installed.')
    with tempfile.TemporaryDirectory(prefix='kit_mock_qr_') as temp:
        work = Path(temp)
        for name in ('server.mjs', 'guard.mjs', 'disconnect-diagnostic.mjs', 'qr-lifecycle.mjs'):
            shutil.copy2(ROOT / name, work / name)
        for name, code in [('baileys', BAILEYS), ('qrcode', QRCODE)]:
            target = work / 'node_modules' / name
            target.mkdir(parents=True)
            (target / 'package.json').write_text(json.dumps({'name': name, 'type': 'module', 'exports': './index.mjs'}), encoding='utf-8')
            (target / 'index.mjs').write_text(code, encoding='utf-8')
        data = work / 'data'; data.mkdir()
        token = secrets.token_urlsafe(32)
        env = {**os.environ, 'GATEWAY_TOKEN': token, 'ALLOWED_NUMBERS': '+15555550123',
               'WHATSAPP_PAIRING_CONSENT': 'SIM', 'DATA_DIR': str(data), 'GATEWAY_BIND_HOST': '127.0.0.1'}
        proc = subprocess.Popen(['node', 'server.mjs'], cwd=work, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # Do not allow proxy environment to divert private synthetic requests.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        def call(path, auth=True):
            headers = {'Authorization': 'Bearer ' + token} if auth else {}
            req = urllib.request.Request('http://127.0.0.1:3210' + path, headers=headers)
            try:
                response = opener.open(req, timeout=5)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                return response.code, response.read().decode(), dict(response.headers)

        sequence = 0

        def emit(update=None, clear=False):
            nonlocal sequence
            sequence += 1
            tmp = data / 'control.tmp'
            tmp.write_text(json.dumps({'sequence': sequence, 'update': update, 'clearQr': clear}), encoding='utf-8')
            tmp.replace(data / 'control.json')
            wait_for(lambda: (data / 'applied').exists() and (data / 'applied').read_text() == str(sequence), 'mock event not applied')

        try:
            for _ in range(100):
                if proc.poll() is not None:
                    raise RuntimeError('Mock QR server failed: ' + proc.stderr.read())
                try:
                    if call('/health')[0] == 200:
                        break
                except OSError:
                    pass
                time.sleep(.05)
            else:
                raise AssertionError('Mock server not ready; loopback port3210 must be unused.')
            assert call('/qr.svg', auth=False)[0] == 401
            assert call('/qr.svg')[0] == 409
            emit({'qr': 'synthetic-first'})
            qr = json.loads(call('/qr')[1]); assert qr['qr'] == 'synthetic-first' and 0 < qr['expires_in_ms'] <= 15000
            code, svg, headers = call('/qr.svg')
            assert code == 200 and 'synthetic-first' in svg and headers['Cache-Control'] == 'no-store'
            emit({'qr': 'synthetic-second'})
            assert 'synthetic-first' not in call('/qr.svg')[1]
            emit(clear=True)
            assert call('/qr.svg')[0] == 409 and json.loads(call('/qr')[1])['qr'] == ''
            # Rendering started for a valid QR, but the event invalidated it before completion.
            for index, transition in enumerate([{'qr': 'synthetic-rotated'}, terminal]):
                for marker in ['render-started', 'render-release']:
                    (data / marker).unlink(missing_ok=True)
                emit({'qr': f'synthetic-race-{index}'})
                with ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(call, '/qr.svg')
                    wait_for(lambda: (data / 'render-started').exists(), 'render did not start')
                    emit(transition)
                    (data / 'render-release').write_text('release')
                    code, payload, _ = future.result(timeout=5)
                    assert code == 409 and 'synthetic-race' not in payload
            emit({'qr': 'synthetic-late-terminal-timer'})
            assert call('/qr.svg')[0] == 409 and json.loads(call('/qr')[1])['qr'] == ''
            emit({'connection': 'close', 'lastDisconnect': {'error': {'name': 'SYNTHETIC_SECRET', 'message': 'SYNTHETIC_SECRET', 'output': {'statusCode': 408}}}})
            diagnostic = (data / 'last-disconnect.json').read_text()
            assert 'SYNTHETIC_SECRET' not in diagnostic and json.loads(diagnostic)['status_code'] == 408
            assert json.loads(call('/qr')[1])['qr'] == ''
            assert call('/qr.svg')[0] == 409
            assert json.loads(call('/health')[1]) == {'status': 'disconnected', 'connected': False}
            emit({'qr': 'synthetic-late-closed-transport'})
            assert call('/qr.svg')[0] == 409 and json.loads(call('/qr')[1])['qr'] == ''
            assert not (data / 'send-journal.json').exists()
        finally:
            proc.terminate()
            stdout, stderr = proc.communicate(timeout=5)
            assert 'synthetic-race' not in stdout + stderr and 'SYNTHETIC_SECRET' not in stdout + stderr


def main():
    for terminal in [{'isNewLogin': True}, {'connection': 'open'},
                     {'connection': 'close', 'lastDisconnect': {'error': {'output': {'statusCode': 408}}}}]:
        run_case(terminal)
    print('PASS: mocked QR HTTP; private no-store; rotation/clear/pair/open/close invalidation; render races and late timer QRs rejected; safe diagnostic persisted; no real QR/WhatsApp.')


if __name__ == '__main__':
    main()
