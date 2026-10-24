import { sha1 } from './sha1';

const BLOCK_SIZE = 64; // bytes de bloque de SHA-1

/** HMAC-SHA1 (RFC 2104): H((K ^ opad) || H((K ^ ipad) || mensaje)). */
export function hmacSha1(key: Uint8Array, message: Uint8Array): Uint8Array {
  // Claves más largas que el bloque se reducen con el hash; las cortas se rellenan con ceros.
  const block = new Uint8Array(BLOCK_SIZE);
  block.set(key.length > BLOCK_SIZE ? sha1(key) : key);

  const inner = new Uint8Array(BLOCK_SIZE + message.length);
  const outer = new Uint8Array(BLOCK_SIZE + 20);
  for (let i = 0; i < BLOCK_SIZE; i++) {
    inner[i] = block[i] ^ 0x36;
    outer[i] = block[i] ^ 0x5c;
  }
  inner.set(message, BLOCK_SIZE);
  outer.set(sha1(inner), BLOCK_SIZE);
  return sha1(outer);
}
