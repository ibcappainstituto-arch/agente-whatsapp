/** Baileys rc14 defaults: first QR 60s, subsequent QRs 20s. Expose at most
 * 15s locally, measured monotonically. This is not a server validity guarantee.
 * Never log or persist the value. A saved SVG cannot be remotely invalidated.
 */
export const QR_LOCAL_TTL_MS = 15_000;

export function createQrLifecycle({clock = () => performance.now()} = {}) {
  let current = null, lastValue = '', seen = false, pairingFinished = false;
  function invalidate() { current = null; }
  function beginTransport() { invalidate(); lastValue = ''; seen = false; pairingFinished = false; }
  function snapshot() {
    if (current && (clock() < current.createdAt || clock() >= current.expiresAt)) invalidate();
    return current;
  }
  function apply(update) {
    // rc14 can emit one more timer QR after pair-success, before open/close.
    // Pair success/open/close latch off QRs for this transport, not just one event.
    if (update.isNewLogin === true || ['open', 'close'].includes(update.connection)) pairingFinished = true;
    // Terminal/transition events take precedence even if they contain a QR.
    if (pairingFinished || update.connection === 'connecting' ||
        (Object.hasOwn(update, 'qr') && (typeof update.qr !== 'string' || !update.qr))) {
      invalidate();
      return;
    }
    if (typeof update.qr === 'string' && update.qr && update.qr !== lastValue) {
      lastValue = update.qr;
      seen = true;
      const createdAt = clock();
      current = Object.freeze({value: update.qr, createdAt, expiresAt: createdAt + QR_LOCAL_TTL_MS});
    }
    // Duplicate events never extend or resurrect an expired/invalidated QR.
  }
  return {apply, invalidate, beginTransport, snapshot,
    isCurrent: candidate => candidate !== null && candidate === snapshot(),
    remainingMs: candidate => candidate !== null && candidate === snapshot()
      ? Math.max(0, Math.floor(candidate.expiresAt - clock())) : 0,
    hasSeen: () => seen};
}
