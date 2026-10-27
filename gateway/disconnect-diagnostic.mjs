/** Allowlisted metadata only: never serialize the upstream error/session. */
export function disconnectDiagnostic(update, {qrSeen = false, stopping = false} = {}) {
  const error = update?.lastDisconnect?.error;
  const code = error?.output?.statusCode;
  const statusCode = Number.isInteger(code) && code >= 100 && code <= 999 ? code : null;
  const reasons = {401:'logged_out',403:'forbidden',408:'timeout_or_connection_lost',411:'multidevice_mismatch',428:'connection_closed',440:'connection_replaced',500:'bad_session',503:'service_unavailable',515:'restart_required'};
  const messages = new Map([
    ['QR refs attempts ended','qr_references_exhausted'],
    ['Connection was lost','connection_lost'],
    ['Connection Terminated','connection_terminated'],
    ['Connection Terminated by Server','connection_terminated_by_server'],
    ['Connection Failure','connection_failure'],
    ['operator_stop','operator_stop']
  ]);
  return {event:'whatsapp_disconnect',at_utc:new Date().toISOString(),status_code:statusCode,
    reason:reasons[statusCode] || 'unknown',
    error_name:['Error','Boom','TypeError','TimeoutError'].includes(error?.name) ? error.name : 'other',
    message_class:messages.get(error?.message) || 'redacted_unknown',
    qr_seen:qrSeen === true,operator_stopping:stopping === true};
}
