import { isValidBase32, normalizeBase32 } from './base32';

export type OtpAuthData = { secret: string; account: string; issuer: string };

/**
 * Lee un URI otpauth://totp/Emisor:cuenta?secret=...&issuer=... (el contenido del QR).
 * Se parsea a mano porque `URL` de React Native no soporta esquemas personalizados de forma fiable.
 */
export function parseOtpAuthUri(uri: string): OtpAuthData {
  const match = /^otpauth:\/\/totp\/([^?]*)\?(.*)$/i.exec(uri.trim());
  if (!match) throw new Error('El QR no contiene un URI otpauth://totp/');

  const label = decodeURIComponent(match[1]);
  const params: Record<string, string> = {};
  for (const pair of match[2].split('&')) {
    const [k, v = ''] = pair.split('=');
    params[decodeURIComponent(k).toLowerCase()] = decodeURIComponent(v.replace(/\+/g, ' '));
  }

  const secret = normalizeBase32(params.secret ?? '');
  if (!isValidBase32(secret)) throw new Error('El QR no trae un secreto Base32 válido');
  if ((params.algorithm ?? 'SHA1').toUpperCase() !== 'SHA1') throw new Error('Solo se soporta SHA1');

  const sep = label.lastIndexOf(':');
  const account = sep >= 0 ? label.slice(sep + 1) : label;
  const issuer = params.issuer ?? (sep >= 0 ? label.slice(0, sep) : '');
  return { secret, account: account.trim(), issuer: issuer.trim() };
}
