/** Base32 (RFC 4648) a mano: el mismo algoritmo que server/app/otp/base32.py. */

const ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';

/** Quita espacios, guiones y '=' y pasa a mayúsculas (como lo teclea un humano). */
export function normalizeBase32(text: string): string {
  return text.toUpperCase().replace(/[\s=-]/g, '');
}

export function isValidBase32(text: string): boolean {
  const clean = normalizeBase32(text);
  return clean.length > 0 && /^[A-Z2-7]+$/.test(clean);
}

export function base32Encode(data: Uint8Array): string {
  let out = '';
  let buffer = 0;
  let bits = 0;
  for (const byte of data) {
    buffer = ((buffer << 8) | byte) & 0xffff; // solo hacen falta los bits pendientes
    bits += 8;
    while (bits >= 5) {
      bits -= 5;
      out += ALPHABET[(buffer >> bits) & 0x1f];
    }
  }
  if (bits > 0) out += ALPHABET[(buffer << (5 - bits)) & 0x1f];
  return out;
}

export function base32Decode(text: string): Uint8Array {
  const clean = normalizeBase32(text);
  const out: number[] = [];
  let buffer = 0;
  let bits = 0;
  for (const ch of clean) {
    const value = ALPHABET.indexOf(ch);
    if (value === -1) throw new Error(`Carácter Base32 inválido: "${ch}"`);
    buffer = ((buffer << 5) | value) & 0xffff;
    bits += 5;
    if (bits >= 8) {
      bits -= 8;
      out.push((buffer >> bits) & 0xff);
    }
  }
  return Uint8Array.from(out);
}

/** 'JBSWY3DPEHPK3PXP' -> 'JBSW Y3DP EHPK 3PXP' */
export function groupBase32(text: string, size = 4): string {
  return normalizeBase32(text).match(new RegExp(`.{1,${size}}`, 'g'))?.join(' ') ?? '';
}
