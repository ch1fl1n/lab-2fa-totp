/** HOTP (RFC 4226) y TOTP (RFC 6238): el mismo algoritmo que server/app/otp/. */
import { hmacSha1 } from './hmac';

export const PERIOD = 30;
export const DIGITS = 6;

export function hotp(key: Uint8Array, counter: number, digits = DIGITS): string {
  // 1. Contador como entero de 8 bytes big-endian.
  const msg = new Uint8Array(8);
  const view = new DataView(msg.buffer);
  view.setUint32(0, Math.floor(counter / 2 ** 32));
  view.setUint32(4, counter >>> 0);
  // 2. HMAC-SHA1.
  const mac = hmacSha1(key, msg);
  // 3. Dynamic truncation: los 4 bits bajos del último byte dan el offset.
  const offset = mac[mac.length - 1] & 0x0f;
  const binary =
    ((mac[offset] & 0x7f) << 24) |
    (mac[offset + 1] << 16) |
    (mac[offset + 2] << 8) |
    mac[offset + 3];
  // 4. Módulo 10^digits con ceros a la izquierda.
  return (binary % 10 ** digits).toString().padStart(digits, '0');
}

/** Contador T = floor(tiempo_unix / periodo). */
export function counterAt(unixMs: number, period = PERIOD): number {
  return Math.floor(unixMs / 1000 / period);
}

export function totp(key: Uint8Array, unixMs: number, period = PERIOD, digits = DIGITS): string {
  return hotp(key, counterAt(unixMs, period), digits);
}

export function secondsRemaining(unixMs: number, period = PERIOD): number {
  return period - ((unixMs / 1000) % period);
}
