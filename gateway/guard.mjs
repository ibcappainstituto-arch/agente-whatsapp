/** Small fail-closed policy. No network or third-party dependencies. */
import { createHash, timingSafeEqual } from 'node:crypto';

export const TTL_SECONDS = 600;
export function allowlist(value = '') {
  const result = new Set();
  for (const item of value.split(',').map(x => x.trim()).filter(Boolean)) {
    if (!/^\+?[1-9][0-9]{7,14}$/.test(item)) throw new Error('ALLOWED_NUMBERS: use E164 separated by commas, never wildcards.');
    result.add(item.replace(/^\+/, '') + '@s.whatsapp.net');
  }
  return result;
}
export function authorized(value, token) {
  const actual = Buffer.from(String(value || ''));
  const expected = Buffer.from(`Bearer ${token}`);
  return actual.length === expected.length && timingSafeEqual(actual, expected);
}
export function stamp(value) {
  if (value && typeof value.toNumber === 'function') return value.toNumber();
  if (value && typeof value === 'object' && Number.isInteger(value.low) && Number.isInteger(value.high)) return value.high * 4294967296 + (value.low >>> 0);
  return Number(value);
}
export function normalize(message, allowed, now, startedAt, knownOwnIds = new Set()) {
  const key = message?.key;
  const jid = key?.remoteJid;
  // Reject groups, broadcasts, status, newsletter, LID and device-specific ambiguous JIDs.
  if (typeof key?.fromMe !== 'boolean' || !key?.id || typeof key.id !== 'string' || !/^[1-9][0-9]{7,14}@s\.whatsapp\.net$/.test(jid || '') || !allowed.has(jid)) return null;
  const timestamp = stamp(message.messageTimestamp);
  if (!Number.isFinite(timestamp) || timestamp < startedAt || timestamp > now + 30 || now - timestamp > TTL_SECONDS) return null;
  if (key.fromMe && knownOwnIds.has(key.id)) return null;
  const kind = key.fromMe ? 'human_takeover' : 'incoming';
  const text = message.message?.conversation ?? message.message?.extendedTextMessage?.text;
  if (kind === 'incoming' && (typeof text !== 'string' || !text.trim() || text.length > 8000)) return null;
  return {id: createHash('sha256').update(`${jid}\0${key.id}`).digest('hex'), chat_id: jid,
    text: kind === 'incoming' ? text.trim() : '', timestamp, kind};
}
export function verifySend(body, events, allowed, now) {
  if (!body || typeof body !== 'object' || Array.isArray(body)) throw new Error('invalid_body');
  if (typeof body.idempotency_key !== 'string' || !/^[a-zA-Z0-9_-]{16,128}$/.test(body.idempotency_key)) throw new Error('invalid_idempotency_key');
  if (typeof body.text !== 'string' || !body.text.trim() || body.text.length > 4000) throw new Error('invalid_text');
  const event = events.get(body.event_id);
  if (!event || event.kind !== 'incoming' || event.chat_id !== body.chat_id || !allowed.has(body.chat_id)) throw new Error('inbound_required');
  if (now - event.timestamp > TTL_SECONDS || event.timestamp > now + 30) throw new Error('expired_inbound');
  const laterHuman = [...events.values()].some(x => x.kind === 'human_takeover' && x.chat_id === body.chat_id && x.cursor > event.cursor);
  if (laterHuman) throw new Error('human_takeover');
  return event;
}

/** Only the documented post-pairing transport restart, never general reconnect/re-pair. */
export function mayRestartTransport(reason, registered, attempts, stopping = false) {
  return reason === 515 && registered === true && attempts === 0 && !stopping;
}
