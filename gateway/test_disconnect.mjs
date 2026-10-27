import test from 'node:test';
import assert from 'node:assert/strict';
import {disconnectDiagnostic} from './disconnect-diagnostic.mjs';
test('distinguishes exhausted QR references from generic 408',()=>{
  const a=disconnectDiagnostic({lastDisconnect:{error:{name:'Error',message:'QR refs attempts ended',output:{statusCode:408}}}},{qrSeen:true});
  assert.equal(a.message_class,'qr_references_exhausted');
  assert.equal(a.status_code,408);assert.equal(a.qr_seen,true);
  assert.equal(disconnectDiagnostic({lastDisconnect:{error:{output:{statusCode:408}}}}).message_class,'redacted_unknown');
});
test('never serializes secrets in arbitrary error fields',()=>{
  const secret='SYNTHETIC_PRIVATE_PAYLOAD';
  const a=disconnectDiagnostic({lastDisconnect:{error:{name:secret,message:secret,stack:secret,data:{token:secret},output:{statusCode:secret}}}});
  assert.equal(JSON.stringify(a).includes(secret),false);
  assert.equal(a.status_code,null);assert.equal(a.error_name,'other');
});
test('handles missing errors and safe known termination',()=>{
  assert.equal(disconnectDiagnostic({}).reason,'unknown');
  assert.equal(disconnectDiagnostic({lastDisconnect:{error:{message:'Connection Terminated by Server',output:{statusCode:428}}}}).message_class,'connection_terminated_by_server');
});
