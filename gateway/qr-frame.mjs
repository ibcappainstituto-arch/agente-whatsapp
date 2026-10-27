/** Authenticated read-only frame helper. Caller owns Bearer auth + no-store headers.
 * No raw QR value, credentials or PNG is written to disk or logs.
 */
export async function renderPrivateFrame({state, status, active, renderPng}) {
  const empty = (code = 200) => ({code, body: {protocol: 1, status: status(), generation: 0, expires_in_ms: 0, png_base64: ''}});
  const current = active() ? state.snapshot() : null;
  if (!current) return empty();
  const png = await renderPng(current.value);
  // Every async boundary may rotate/invalidate the QR or close the transport.
  if (!active() || !state.isCurrent(current)) return empty(409);
  if (!Buffer.isBuffer(png) || png.length > 200_000 || !png.subarray(0, 8).equals(Buffer.from([137,80,78,71,13,10,26,10])))
    throw new Error('qr_render_rejected');
  const remaining = state.remainingMs(current);
  if (remaining <= 0) return empty(409);
  return {code: 200, body: {protocol: 1, status: status(), generation: current.generation,
    expires_in_ms: remaining, png_base64: png.toString('base64')}};
}
