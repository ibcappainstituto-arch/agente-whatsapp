import test from 'node:test';
import assert from 'node:assert/strict';
import {createQrLifecycle} from './qr-lifecycle.mjs';
import {renderPrivateFrame} from './qr-frame.mjs';
const PNG=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4//8/AAX+Av4N70a4AAAAAElFTkSuQmCC','base64'); // 1x1 white pixel, NOT QR
function fixture() {
  let clock=10, status='qr_required', active=true;
  const state=createQrLifecycle({clock:()=>clock});
  state.apply({qr:'synthetic-not-a-real-qr'});
  const options={state,status:()=>status,active:()=>active,renderPng:async()=>PNG};
  return {state,options,tick:ms=>clock+=ms,setStatus:value=>status=value,setActive:value=>active=value};
}
test('private frame contains PNG and generation but no raw QR',async()=>{
  const {options}=fixture(); const result=await renderPrivateFrame(options);
  assert.equal(result.code,200); assert.equal(result.body.protocol,1);
  assert.equal(result.body.generation,1); assert.equal(result.body.expires_in_ms,15000);
  assert.equal(result.body.png_base64,PNG.toString('base64'));
  assert(!JSON.stringify(result.body).includes('synthetic'));
});
test('generation increases on rotation and new transport, not duplicate events',()=>{
  const {state}=fixture(); assert.equal(state.snapshot().generation,1);
  state.apply({qr:'synthetic-not-a-real-qr'}); assert.equal(state.snapshot().generation,1);
  state.apply({qr:'synthetic-rotated'}); assert.equal(state.snapshot().generation,2);
  state.beginTransport(); state.apply({qr:'synthetic-fresh'}); assert.equal(state.snapshot().generation,3);
});
test('inactive viewer endpoint never calls renderer',async()=>{
  const f=fixture(); f.setActive(false); f.options.renderPng=()=>{throw Error('must not render');};
  const r=await renderPrivateFrame(f.options); assert.equal(r.code,200); assert.equal(r.body.png_base64,'');
});
test('expiration while rendering rejects bytes',async()=>{
  const f=fixture(); f.options.renderPng=async()=>{f.tick(15000);return PNG;};
  const r=await renderPrivateFrame(f.options); assert.equal(r.code,409); assert.equal(r.body.png_base64,'');
});
test('rotation while rendering rejects old generation',async()=>{
  const f=fixture(); f.options.renderPng=async()=>{f.state.apply({qr:'synthetic-new'});return PNG;};
  const r=await renderPrivateFrame(f.options); assert.equal(r.code,409); assert.equal(r.body.generation,0);
});
test('pair/open/close invalidates rendering and blocks late timer QR',async()=>{
  for(const update of [{isNewLogin:true},{connection:'open'},{connection:'close'}]) {
    const f=fixture(); f.options.renderPng=async()=>{f.state.apply(update);return PNG;};
    const r=await renderPrivateFrame(f.options); assert.equal(r.code,409);
    f.state.apply({qr:'synthetic-late'}); assert.equal(f.state.snapshot(),null);
    assert.equal((await renderPrivateFrame(f.options)).body.png_base64,'');
  }
});
test('consent/status change during rendering rejects frame',async()=>{
  const f=fixture(); f.options.renderPng=async()=>{f.setActive(false);f.setStatus('disconnected');return PNG;};
  const r=await renderPrivateFrame(f.options); assert.equal(r.code,409); assert.equal(r.body.status,'disconnected');
});
test('unsafe rendered payload rejected before response',async()=>{
  for(const png of ['not-buffer',Buffer.from('not-png'),Buffer.alloc(200001)]) {
    const f=fixture(); f.options.renderPng=async()=>png;
    await assert.rejects(renderPrivateFrame(f.options),/qr_render_rejected/);
  }
});
