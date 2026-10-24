/**
 * Carga totp-core/spec.json (la misma que usa el backend Python) y verifica esta implementación.
 * La app la ejecuta antes de mostrar cualquier código: si falla, no muestra códigos incorrectos.
 */
import spec from '../spec.json';
import { base32Decode, base32Encode } from './base32';
import { hotp, totp } from './totp';

export { spec };

const ascii = (s: string) => Uint8Array.from(s, (c) => c.charCodeAt(0));
const toAscii = (b: Uint8Array) => String.fromCharCode(...b);

export function selfTest(): number {
  const v = spec.vectors;
  const checks: [string, string, string][] = [];

  v.hotp_rfc4226.codes.forEach((code, i) =>
    checks.push([`HOTP c=${i}`, hotp(ascii(v.hotp_rfc4226.secret_ascii), i), code])
  );
  for (const c of v.totp_rfc6238.cases) {
    const key = ascii(v.totp_rfc6238.secret_ascii);
    checks.push([`TOTP t=${c.time}`, totp(key, c.time * 1000, spec.period, v.totp_rfc6238.digits), c.code]);
  }
  for (const b of v.base32) {
    checks.push([`Base32 ${b.ascii}`, base32Encode(ascii(b.ascii)), b.base32]);
    checks.push([`Base32 decode ${b.base32}`, toAscii(base32Decode(b.base32)), b.ascii]);
  }
  for (const c of v.cross_check) {
    checks.push([`Cruce ${c.secret_base32}`, totp(base32Decode(c.secret_base32), c.time * 1000), c.code]);
  }

  const failed = checks.filter(([, got, want]) => got !== want);
  if (failed.length) {
    throw new Error(
      'totp-core no cumple la especificación:\n' +
        failed.map(([name, got, want]) => `${name}: obtuvo ${got}, esperaba ${want}`).join('\n')
    );
  }
  return checks.length;
}
