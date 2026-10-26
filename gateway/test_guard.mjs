import test from 'node:test';
import assert from 'node:assert/strict';
import {allowlist, authorized, normalize, verifySend, stamp, mayRestartTransport} from './guard.mjs';
const jid = '15555550123@s.whatsapp.net'; // synthetic fixture, never connected
const other = '15555550999@s.whatsapp.net';
const now = 1900000000;
const allowed = allowlist('+15555550123');
const message = (changes = {}) => ({key: {id: 'FAKE-ONE', remoteJid: jid, fromMe: false}, messageTimestamp: now, message: {conversation: 'Preciso de apoio técnico'}, ...changes});
function event(changes = {}) { return {...normalize(message(), allowed, now, now - 5), cursor: 1, ...changes}; }
const body = (changes = {}) => ({event_id: event().id, chat_id: jid, text: 'Qual é a fase da demanda?', idempotency_key: 'synthetic_idempotency_123', ...changes});
const entries = () => new Map([[event().id, event()]]);
test('allowlist empty is closed', () => assert.equal(allowlist('').size, 0));
test('allowlist normalizes only explicit E164 values', () => assert.deepEqual([...allowlist(' +15555550123 , 15555550999 ')], [jid, other]));
test('wildcard, group and malformed allowlist fail closed', () => {
  for (const value of ['*', '@all', jid, '1555-555-0123', '0015555550123', '123']) assert.throws(() => allowlist(value));
});
test('Bearer token exact comparison', () => {
  assert(authorized('Bearer token', 'token'));
  for (const actual of ['', undefined, 'bearer token', 'Bearer tokenX']) assert(!authorized(actual, 'token'));
});
test('incoming plain text yields normalized event', () => {
  const result = normalize(message(), allowed, now, now - 5);
  assert.equal(result.chat_id, jid); assert.equal(result.kind, 'incoming'); assert.equal(result.text, 'Preciso de apoio técnico');
  assert.match(result.id, /^[0-9a-f]{64}$/);
});
test('extended text supported, media-only ignored', () => {
  assert.equal(normalize(message({message: {extendedTextMessage: {text: 'Olá'}}}), allowed, now, now - 5).text, 'Olá');
  assert.equal(normalize(message({message: {imageMessage: {caption: 'not processed'}}}), allowed, now, now - 5), null);
});
test('groups status broadcast LID nonallowlisted rejected', () => {
  for (const remoteJid of ['1@g.us', 'status@broadcast', '1@newsletter', '15555550123@lid', other, '15555550123:1@s.whatsapp.net']) {
    assert.equal(normalize(message({key: {id: 'X', remoteJid, fromMe: false}}), allowed, now, now - 5), null);
  }
});
test('history, stale and future inputs rejected', () => {
  for (const messageTimestamp of [now - 10, now - 601, now + 31, undefined, 'bad']) assert.equal(normalize(message({messageTimestamp}), allowed, now, now - 5), null);
});
test('known own send ignored; unknown own send pauses', () => {
  const own = message({key: {id: 'OUR-SEND', remoteJid: jid, fromMe: true}});
  assert.equal(normalize(own, allowed, now, now - 5, new Set(['OUR-SEND'])), null);
  assert.equal(normalize(own, allowed, now, now - 5).kind, 'human_takeover');
  assert.equal(normalize(own, allowed, now, now - 5).text, '');
});
test('supports Baileys long timestamps', () => {
  assert.equal(stamp({toNumber: () => now}), now);
  assert.equal(stamp({low: now, high: 0}), now);
  assert(stamp({low: now, high: 1}) > now + 30);
});
test('valid send needs a recorded inbound', () => assert.equal(verifySend(body(), entries(), allowed, now).id, event().id));
test('cannot initiate or change recipient', () => {
  assert.throws(() => verifySend(body(), new Map(), allowed, now), /inbound_required/);
  assert.throws(() => verifySend(body({chat_id: other}), entries(), allowed, now), /inbound_required/);
});
test('cannot answer expired event or takeover marker', () => {
  assert.throws(() => verifySend(body(), entries(), allowed, now + 601), /expired_inbound/);
  assert.throws(() => verifySend(body(), new Map([[event().id, event({kind: 'human_takeover'})]]), allowed, now), /inbound_required/);
});
test('later human message blocks pending send', () => {
  const events = entries(); events.set('human', event({id: 'human', kind: 'human_takeover', cursor: 2}));
  assert.throws(() => verifySend(body(), events, allowed, now), /human_takeover/);
});
test('bad send body, key and text rejected', () => {
  for (const value of [null, [], '', 1]) assert.throws(() => verifySend(value, entries(), allowed, now), /invalid_body/);
  for (const key of ['', 'short', 'secret\nkey', 42]) assert.throws(() => verifySend(body({idempotency_key: key}), entries(), allowed, now), /invalid_idempotency_key/);
  for (const text of ['', ' ', 'x'.repeat(4001), 42]) assert.throws(() => verifySend(body({text}), entries(), allowed, now), /invalid_text/);
});

test('missing fromMe flag rejected rather than treated as inbound', () => {
  assert.equal(normalize(message({key: {id: 'X', remoteJid: jid}}), allowed, now, now - 5), null);
});

test('only one documented restartRequired transport restart with saved registration', () => {
  assert(mayRestartTransport(515, true, 0));
  for (const reason of [401, 403, 408, 428, 440, 500, 503, undefined, '515']) assert(!mayRestartTransport(reason, true, 0));
  assert(!mayRestartTransport(515, false, 0));
  assert(!mayRestartTransport(515, true, 1));
  assert(!mayRestartTransport(515, true, 0, true));
});
