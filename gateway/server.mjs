/** Local-only teaching gateway: never a public API, no outbound campaigns. */
import http from 'node:http';
import { createHash } from 'node:crypto';
import { mkdirSync, existsSync, readFileSync, writeFileSync, renameSync } from 'node:fs';
import { join, isAbsolute } from 'node:path';
import { allowlist, authorized, normalize, verifySend, mayRestartTransport, TTL_SECONDS } from './guard.mjs';
import { disconnectDiagnostic } from './disconnect-diagnostic.mjs';
import { createQrLifecycle } from './qr-lifecycle.mjs';
import { renderPrivateFrame } from './qr-frame.mjs';

const token = process.env.GATEWAY_TOKEN || '';
if (!/^[A-Za-z0-9_-]{32,256}$/.test(token)) throw new Error('GATEWAY_TOKEN must be 32+ random URL-safe characters.');
const allowed = allowlist(process.env.ALLOWED_NUMBERS || '');
const consent = process.env.WHATSAPP_PAIRING_CONSENT === 'SIM';
const dataDir = process.env.DATA_DIR;
if (!dataDir || !isAbsolute(dataDir)) throw new Error('DATA_DIR must be an explicit absolute private path.');
const bindHost = process.env.GATEWAY_BIND_HOST || '127.0.0.1';
if (!['127.0.0.1', '0.0.0.0'].includes(bindHost)) throw new Error('Invalid gateway bind host.');
mkdirSync(dataDir, { recursive: true, mode: 0o700 });
const stateFile = join(dataDir, 'send-journal.json');
// Corrupt journal is fatal: never silently discard uncertain sends and retry them.
const journal = existsSync(stateFile) ? JSON.parse(readFileSync(stateFile, 'utf8')) : {};
const saveJournal = () => {
  const tmp = stateFile + '.tmp';
  writeFileSync(tmp, JSON.stringify(journal), { mode: 0o600, flush: true });
  renameSync(tmp, stateFile);
};
const ownIds = new Set(Object.values(journal).map(x => x.message_id).filter(Boolean));
const events = new Map();
let cursor = Date.now() * 1000;
const startedAt = Math.ceil(Date.now() / 1000);
const qrState = createQrLifecycle();
let socket, generateId, status = consent ? 'starting' : 'consent_required';
let transportRestarts = 0, stopping = false;
const now = () => Date.now() / 1000;
const safeHeaders = { 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
  'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'" };
function reply(res, code, data) {
  res.writeHead(code, { ...safeHeaders, 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(data));
}
async function bodyOf(req) {
  let size = 0, parts = [];
  for await (const part of req) {
    size += part.length;
    if (size > 20000) throw new Error('body_too_large');
    parts.push(part);
  }
  return JSON.parse(Buffer.concat(parts).toString('utf8'));
}
function purge() {
  for (const [id, event] of events) if (now() - event.timestamp > TTL_SECONDS) events.delete(id);
  while (events.size > 1000) events.delete(events.keys().next().value);
}
function putEvent(event) {
  if (!event || events.has(event.id) || journal[event.id]) return;
  event.cursor = ++cursor;
  events.set(event.id, event);
  purge();
}
const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, 'http://127.0.0.1');
    if (req.method === 'GET' && url.pathname === '/health') return reply(res, 200, {status, connected: status === 'connected'});
    if (!authorized(req.headers.authorization, token)) return reply(res, 401, {error: 'unauthorized'});
    // No browser-origin API access; local PowerShell/Python clients use a Bearer token.
    if (req.headers.origin) return reply(res, 403, {error: 'browser_origin_not_allowed'});
    if (req.method === 'GET' && url.pathname === '/qr') {
      const current = consent && !stopping && status === 'qr_required' ? qrState.snapshot() : null;
      return reply(res, 200, {status, qr: current?.value || '', expires_in_ms: qrState.remainingMs(current)});
    }
    if (req.method === 'GET' && url.pathname === '/qr/frame') {
      const result = await renderPrivateFrame({
        state: qrState, status: () => status,
        active: () => consent && !stopping && status === 'qr_required',
        renderPng: async value => {
          const QRCode = (await import('qrcode')).default;
          return QRCode.toBuffer(value, {type: 'png', errorCorrectionLevel: 'L', margin: 4, width: 400});
        }
      });
      return reply(res, result.code, result.body);
    }
    if (req.method === 'GET' && url.pathname === '/qr.svg') {
      const current = consent && !stopping && status === 'qr_required' ? qrState.snapshot() : null;
      if (!current) return reply(res, 409, {error: 'qr_not_available'});
      const QRCode = (await import('qrcode')).default;
      const svg = await QRCode.toString(current.value, {type: 'svg', errorCorrectionLevel: 'L', margin: 4});
      // Rotation, pairing, disconnection or expiry may happen during async rendering.
      if (stopping || status !== 'qr_required' || !qrState.isCurrent(current)) return reply(res, 409, {error: 'qr_not_available'});
      res.writeHead(200, {...safeHeaders, 'Content-Type': 'image/svg+xml'});
      return res.end(svg);
    }
    if (req.method === 'GET' && url.pathname === '/events') {
      const after = Number(url.searchParams.get('after') || 0);
      if (!Number.isSafeInteger(after) || after < 0) return reply(res, 400, {error: 'invalid_cursor'});
      purge();
      return reply(res, 200, {events: [...events.values()].filter(x => x.cursor > after), cursor});
    }
    if (req.method === 'POST' && url.pathname === '/send') {
      if (!consent || status !== 'connected') return reply(res, 503, {error: 'not_connected'});
      if (!String(req.headers['content-type'] || '').startsWith('application/json')) return reply(res, 415, {error: 'json_required'});
      const body = await bodyOf(req);
      purge();
      const event = verifySend(body, events, allowed, now());
      const fingerprint = createHash('sha256').update(JSON.stringify([body.chat_id, body.text, body.idempotency_key])).digest('hex');
      const previous = journal[event.id];
      if (previous) {
        if (previous.fingerprint !== fingerprint) return reply(res, 409, {error: 'already_claimed'});
        if (previous.state === 'sent') return reply(res, 200, {message_id: previous.message_id, state: 'sent'});
        return reply(res, 409, {error: 'uncertain_send_do_not_retry', state: previous.state});
      }
      if (Object.values(journal).some(x => x.idempotency_key === body.idempotency_key)) return reply(res, 409, {error: 'idempotency_conflict'});
      const messageId = generateId(socket.user?.id);
      ownIds.add(messageId);
      // Claim durably BEFORE the network effect; any ambiguity is terminal, not a retry.
      journal[event.id] = {idempotency_key: body.idempotency_key, fingerprint, message_id: messageId, state: 'sending', at: now()};
      saveJournal();
      try {
        const receipt = await socket.sendMessage(event.chat_id, {text: body.text}, {messageId});
        if (!receipt?.key?.id) throw new Error('no_receipt');
        ownIds.add(receipt.key.id);
        journal[event.id].message_id = receipt.key.id;
        journal[event.id].state = 'sent';
        saveJournal();
        return reply(res, 200, {message_id: receipt.key.id, state: 'sent'});
      } catch {
        journal[event.id].state = 'uncertain';
        saveJournal();
        return reply(res, 502, {error: 'uncertain_send_do_not_retry', state: 'uncertain'});
      }
    }
    reply(res, 404, {error: 'not_found'});
  } catch (err) {
    // Never log message content, QR, credentials or upstream error details.
    if (!res.headersSent) reply(res, 400, {error: ['body_too_large', 'invalid_body', 'invalid_idempotency_key', 'invalid_text', 'inbound_required', 'expired_inbound', 'human_takeover'].includes(err.message) ? err.message : 'request_rejected'});
    else res.end();
  }
});
server.requestTimeout = 15000;
server.headersTimeout = 10000;
server.listen(3210, bindHost, () => console.log('Gateway HTTP ready; host access must be loopback only.'));

async function connect(allowPairing = true) {
  qrState.beginTransport();
  if (!consent || !allowed.size) { status = !consent ? 'consent_required' : 'allowlist_required'; return; }
  const {default: makeWASocket, useMultiFileAuthState, generateMessageIDV2} = await import('baileys');
  generateId = generateMessageIDV2;
  const logger = {level: 'silent', child() { return this; }, trace() {}, debug() {}, info() {}, warn() {}, error() {}, fatal() {}};
  const {state, saveCreds} = await useMultiFileAuthState(join(dataDir, 'session'));
  if (stopping) return;
  if (!allowPairing && state.creds.registered !== true) {status = 'session_review_required'; return;}
  let credentialWrites = Promise.resolve(), transportClosed = false;
  const activeSocket = makeWASocket({auth: state, logger, markOnlineOnConnect: false, syncFullHistory: false,
    shouldSyncHistoryMessage: () => false, shouldIgnoreJid: jid => !allowed.has(jid),
    getMessage: async () => undefined});
  socket = activeSocket;
  activeSocket.ev.on('creds.update', () => {
    if (socket !== activeSocket || stopping) return;
    credentialWrites = credentialWrites.then(() => saveCreds());
    credentialWrites.catch(() => {qrState.invalidate(); status = 'storage_error'; activeSocket.end(new Error('storage_error'));});
  });
  activeSocket.ev.on('connection.update', update => {
    if (socket !== activeSocket || stopping || transportClosed) return;
    if (update.qr && !allowPairing) {qrState.invalidate(); status = 'session_review_required'; activeSocket.end(new Error('new_pairing_not_allowed')); return;}
    qrState.apply(update);
    if (qrState.snapshot()) {status = 'qr_required';}
    else if (update.isNewLogin) {status = 'pairing_in_progress';}
    else if (update.connection === 'connecting') {status = 'starting';}
    else if (Object.hasOwn(update, 'qr') && status === 'qr_required') {status = 'qr_unavailable';}
    if (update.connection === 'open') {status = 'connected'; console.log('WhatsApp connected. Only allowlisted inbound text can receive a reply.');}
    if (update.connection === 'close') {
      transportClosed = true;
      const diagnostic = disconnectDiagnostic(update, {qrSeen: qrState.hasSeen(), stopping});
      console.log(JSON.stringify(diagnostic));
      try { writeFileSync(join(dataDir, 'last-disconnect.json'), JSON.stringify(diagnostic), {mode: 0o600}); }
      catch { console.error('Safe disconnect diagnostic could not be persisted.'); }
      qrState.invalidate();
      const reason = update.lastDisconnect?.error?.output?.statusCode;
      if (mayRestartTransport(reason, state.creds.registered, transportRestarts, stopping)) {
        transportRestarts += 1;
        status = 'restarting_transport';
        // One 515 handshake restart with persisted credentials; no new QR, replay or send retry.
        credentialWrites.then(() => saveCreds()).then(() => connect(false)).catch(() => {status = 'session_review_required';});
      } else {
        status = 'disconnected';
        console.log('Connection closed. Review locally and restart manually; no automatic pairing/send retry.');
      }
    }
  });
  activeSocket.ev.on('messages.upsert', upsert => {
    if (socket !== activeSocket || stopping || transportClosed) return;
    if (upsert.type !== 'notify') return;
    for (const message of upsert.messages || []) putEvent(normalize(message, allowed, now(), startedAt, ownIds));
  });
}
connect().catch(() => { status = 'startup_error'; console.error('WhatsApp startup failed. No pairing/send confirmed; inspect configuration and dependency installation.'); });
function shutdown() { stopping = true; qrState.invalidate(); socket?.end(new Error('operator_stop')); server.close(() => process.exit(0)); setTimeout(() => process.exit(0), 1000).unref(); }
process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);
