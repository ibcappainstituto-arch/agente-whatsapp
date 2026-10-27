import test from 'node:test';
import assert from 'node:assert/strict';
import {createQrLifecycle, QR_LOCAL_TTL_MS} from './qr-lifecycle.mjs';

function fixture() {
  let time = 100;
  return {qr: createQrLifecycle({clock: () => time}), tick: ms => {time += ms;}};
}
test('QR expires at 15s exactly, before subsequent Baileys 20s default', () => {
  const {qr,tick} = fixture();
  assert.equal(QR_LOCAL_TTL_MS, 15_000);
  qr.apply({qr:'synthetic-one'});
  const first = qr.snapshot();
  tick(14_999); assert.equal(qr.isCurrent(first),true); assert.equal(qr.remainingMs(first),1);
  tick(1); assert.equal(qr.snapshot(),null); assert.equal(qr.isCurrent(first),false);
});
test('duplicate QR never extends expiry or resurrects an old value', () => {
  const {qr,tick} = fixture();
  qr.apply({qr:'synthetic-one'}); tick(14_000); qr.apply({qr:'synthetic-one'});
  tick(1000); assert.equal(qr.snapshot(),null);
  qr.apply({qr:'synthetic-one'}); assert.equal(qr.snapshot(),null);
});
test('rotation replaces old snapshot; stale SVG rendering is rejected', () => {
  const {qr} = fixture(); qr.apply({qr:'synthetic-one'}); const first=qr.snapshot();
  qr.apply({qr:'synthetic-two'});
  assert.equal(qr.isCurrent(first),false); assert.equal(qr.snapshot().value,'synthetic-two');
});
test('explicit qr undefined, empty and null invalidate; absent qr does not', () => {
  for (const value of [undefined,'',null]) {
    const {qr} = fixture(); qr.apply({qr:'synthetic-one'});
    qr.apply({receivedPendingNotifications:true}); assert.ok(qr.snapshot());
    qr.apply({qr:value}); assert.equal(qr.snapshot(),null);
    qr.apply({qr:'synthetic-one'}); assert.equal(qr.snapshot(),null);
  }
});
test('pair success, open, close and connecting invalidate despite coalesced QR', () => {
  for (const update of [{isNewLogin:true}, {connection:'open'}, {connection:'close'}, {connection:'connecting'}]) {
    const {qr} = fixture(); qr.apply({qr:'synthetic-one'});
    qr.apply({...update, qr:'synthetic-two'}); assert.equal(qr.snapshot(),null);
    assert.equal(qr.hasSeen(),true);
  }
});
test('shutdown/storage invalidation and elapsed renderer cannot return stale QR', () => {
  const {qr,tick}=fixture(); qr.apply({qr:'synthetic-one'}); const first=qr.snapshot();
  qr.invalidate(); assert.equal(qr.isCurrent(first),false);
  qr.apply({qr:'synthetic-two'}); const second=qr.snapshot(); tick(15_000);
  assert.equal(qr.isCurrent(second),false);
});
test('backward injected clock fails closed and empty initial state exposes no QR', () => {
  const {qr,tick}=fixture(); assert.equal(qr.snapshot(),null); assert.equal(qr.hasSeen(),false);
  qr.apply({qr:'synthetic-one'}); tick(-1); assert.equal(qr.snapshot(),null);
});
test('late timer QR after pair success/open/close stays blocked until a new transport', () => {
  for (const terminal of [{isNewLogin:true,qr:undefined}, {connection:'open'}, {connection:'close'}]) {
    const {qr}=fixture(); qr.apply({qr:'synthetic-one'}); qr.apply(terminal);
    qr.apply({qr:'synthetic-late-timer'}); assert.equal(qr.snapshot(),null);
    qr.apply({connection:'connecting'}); qr.apply({qr:'synthetic-later'}); assert.equal(qr.snapshot(),null);
    qr.beginTransport(); assert.equal(qr.hasSeen(),false);
    qr.apply({qr:'synthetic-fresh-transport'}); assert.ok(qr.snapshot());
  }
});
