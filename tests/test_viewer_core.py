import base64
import io
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from viewer_core import (DisplayGate, Frame, GatewayReader, Result, ViewerError, load_token,
                         parse_result, validate_png, HOST, PORT, FRAME_PATH)

# A 1x1 white pixel, deliberately NOT a QR code.
def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
PNG = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b'\0\xff\xff\xff')) + chunk(b'IEND', b'')
TOKEN = 'a' * 64

def payload(**changes):
    data = {'protocol':1, 'status':'qr_required', 'generation':1, 'expires_in_ms':15_000,
            'png_base64':base64.b64encode(PNG).decode()}
    data.update(changes)
    return json.dumps(data).encode()

class ConfigTests(unittest.TestCase):
    def test_valid_private_existing_env_only(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'.env'
            content='OTHER_KEY=ignored\nGATEWAY_TOKEN='+TOKEN+'\n'
            path.write_text(content); path.chmod(0o600)
            self.assertEqual(load_token(path),TOKEN)
            self.assertEqual(path.read_text(),content)
    def test_absent_duplicate_invalid_token_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'.env'
            for text in ['', 'GATEWAY_TOKEN', 'GATEWAY_TOKEN=short', 'GATEWAY_TOKEN='+TOKEN+'\n GATEWAY_TOKEN = '+TOKEN,
                         'GATEWAY_TOKEN="'+TOKEN+'"', 'GATEWAY_TOKEN='+('A'*64), 'export GATEWAY_TOKEN='+TOKEN]:
                path.write_text(text); path.chmod(0o600)
                with self.assertRaises(ViewerError): load_token(path)
    def test_large_file_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'.env'; path.write_text('x'*16385); path.chmod(0o600)
            with self.assertRaises(ViewerError): load_token(path)
    def test_symlink_rejected_when_platform_allows_creation(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'.env';path.write_text('GATEWAY_TOKEN='+TOKEN);path.chmod(0o600)
            link=Path(folder)/'link'
            try:
                link.symlink_to(path)
            except (OSError, NotImplementedError):
                self.skipTest('Creating symlinks requires privileges/Developer Mode on this platform')
            with self.assertRaises(ViewerError): load_token(link)
    @unittest.skipIf(os.name=='nt','POSIX mode check; Windows ACL verification is manual')
    def test_world_readable_secret_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'.env'; path.write_text('GATEWAY_TOKEN='+TOKEN); path.chmod(0o644)
            with self.assertRaises(ViewerError): load_token(path)

class TimingTests(unittest.TestCase):
    def test_lease_starts_before_request_and_not_on_arrival(self):
        result=parse_result(payload(expires_in_ms=500),started=10.0,received=10.1)
        self.assertAlmostEqual(result.frame.deadline,10.3)
        self.assertEqual(result.frame.valid_from,10.1)
    def test_max_lease_is_less_than_one_second(self):
        result=parse_result(payload(),started=10,received=10.1)
        self.assertEqual(result.frame.deadline,10.75)
    def test_slow_or_backward_response_rejected(self):
        for received in [9.99,10.751,12]:
            with self.assertRaises(ViewerError): parse_result(payload(),started=10,received=received)
    def test_expired_short_window_discarded(self):
        self.assertIsNone(parse_result(payload(expires_in_ms=200),started=10,received=10.05).frame)
    def test_terminal_states_never_return_image(self):
        for status in ['connected','disconnected','pairing_in_progress','consent_required','invented_raw_secret']:
            result=parse_result(payload(status=status),started=10,received=10.01)
            self.assertIsNone(result.frame)
            self.assertNotIn('secret',result.state)
    def test_bad_protocol_generation_expiry_and_json(self):
        for changes in [{'generation':0},{'generation':True},{'expires_in_ms':15001},{'expires_in_ms':True},{'expires_in_ms':0}]:
            self.assertIsNone(parse_result(payload(**changes),started=10,received=10.1).frame)
        for value in [b'invalid',b'[]',payload(protocol=2),payload(png_base64='%%%')]:
            with self.assertRaises(ViewerError): parse_result(value,started=10,received=10.1)
    def test_png_dimensions_and_bytes_bounded(self):
        self.assertEqual(validate_png(PNG),PNG)
        for data in [b'invalid',PNG+b'x'*200_000,PNG[:16]+struct.pack('>II',10000,10000)+PNG[24:]]:
            with self.assertRaises(ViewerError): validate_png(data)

class DisplayTests(unittest.TestCase):
    def test_begin_invalidates_old_qr_before_network(self):
        gate=DisplayGate(); serial=gate.begin(); gate.accept(serial,Result('qr_required',Frame(1,10,PNG,1)),2)
        self.assertTrue(gate.visible(2)); gate.begin(); self.assertFalse(gate.visible(2))
    def test_stale_worker_result_cannot_restore_after_hide(self):
        gate=DisplayGate(); serial=gate.begin(); gate.hide()
        self.assertFalse(gate.accept(serial,Result('qr_required',Frame(1,10,PNG,1)),2))
    def test_delivery_at_expiry_or_backwards_clock_rejected(self):
        for now in [0.9,10,11]:
            gate=DisplayGate(); serial=gate.begin()
            self.assertFalse(gate.accept(serial,Result('qr_required',Frame(1,10,PNG,1)),now))
    def test_deadline_clears_even_without_response(self):
        gate=DisplayGate(); serial=gate.begin(); gate.accept(serial,Result('qr_required',Frame(1,10,PNG,1)),2)
        self.assertFalse(gate.visible(10)); self.assertIsNone(gate.frame)
    def test_generation_never_regresses_even_after_pause(self):
        gate=DisplayGate();serial=gate.begin()
        self.assertTrue(gate.accept(serial,Result('qr_required',Frame(5,10,PNG,1)),2))
        gate.hide();serial=gate.begin()
        self.assertFalse(gate.accept(serial,Result('qr_required',Frame(4,10,PNG,1)),2))
        self.assertTrue(gate.accept(serial,Result('qr_required',Frame(5,10,PNG,1)),2))
    def test_close_and_failure_clear_all_frames(self):
        gate=DisplayGate(); serial=gate.begin(); gate.accept(serial,Result('qr_required',Frame(1,10,PNG,1)),2)
        self.assertFalse(gate.accept(serial,Result('unavailable'),3)); gate.close()
        self.assertFalse(gate.accept(gate.serial,Result('qr_required',Frame(1,10,PNG,1)),4))

class FakeResponse:
    def __init__(self,status=200,body=None,headers=None):
        self.status=status; self.stream=io.BytesIO(payload() if body is None else body)
        self.headers={'Content-Type':'application/json','Cache-Control':'no-store',**(headers or {})}
    def getheader(self,key,default=None): return self.headers.get(key,default)
    def read1(self,size): return self.stream.read(size)
class FakeConnection:
    def __init__(self,response): self.response=response; self.calls=[]; self.closed=False
    def request(self,*args,**kwargs): self.calls.append((args,kwargs))
    def getresponse(self): return self.response
    def close(self): self.closed=True

class TransportTests(unittest.TestCase):
    def reader(self,response,clock=lambda:10):
        connection=FakeConnection(response); parameters=[]
        def factory(*args,**kwargs): parameters.append((args,kwargs)); return connection
        return GatewayReader(TOKEN,clock=clock,connection_factory=factory),connection,parameters
    def test_only_loopback_exact_get_and_authorization_header(self):
        reader,connection,parameters=self.reader(FakeResponse())
        with patch.dict(os.environ,{'HTTP_PROXY':'http://outside.invalid:80','HTTPS_PROXY':'http://outside.invalid:80'}):
            self.assertIsNotNone(reader.fetch().frame)
        self.assertEqual(parameters[0][0],(HOST,PORT))
        args,kwargs=connection.calls[0]; self.assertEqual(args,('GET',FRAME_PATH))
        self.assertEqual(kwargs['headers']['Authorization'],'Bearer '+TOKEN)
        self.assertNotIn(TOKEN,FRAME_PATH); self.assertTrue(connection.closed)
    def test_redirects_are_rejected_never_followed(self):
        reader,connection,_=self.reader(FakeResponse(302,headers={'Location':'https://outside.invalid/'+TOKEN}))
        with self.assertRaisesRegex(ViewerError,'^http_unavailable$'): reader.fetch()
        self.assertEqual(len(connection.calls),1); self.assertTrue(connection.closed)
    def test_auth_failure_and_rotated_frame_safe(self):
        for status in [401,403]:
            reader,_,_=self.reader(FakeResponse(status,body=TOKEN.encode()))
            with self.assertRaisesRegex(ViewerError,'^unauthorized$'): reader.fetch()
        reader,_,_=self.reader(FakeResponse(409)); self.assertIsNone(reader.fetch().frame)
    def test_content_type_cache_and_size_rejected(self):
        for headers in [{'Content-Type':'image/png'},{'Cache-Control':'public'},{'Content-Length':'999999'},{'Content-Length':'-1'}]:
            reader,_,_=self.reader(FakeResponse(headers=headers))
            with self.assertRaises(ViewerError): reader.fetch()
        reader,_,_=self.reader(FakeResponse(body=b'x'*300001))
        with self.assertRaises(ViewerError): reader.fetch()
    def test_delayed_reads_discarded(self):
        times=iter([10,10.8]); reader,_,_=self.reader(FakeResponse(),clock=lambda:next(times))
        with self.assertRaisesRegex(ViewerError,'^slow_response$'): reader.fetch()
    def test_token_absent_from_frame_repr(self):
        self.assertNotIn('png=',repr(Frame(1,10,PNG,1)))

if __name__=='__main__': unittest.main()
