/** Ejecutar desde mobile-authenticator: npm run test:totp-core */
import assert from 'node:assert/strict';
import { createHash, createHmac, randomBytes } from 'node:crypto';
import { test } from 'node:test';

import { base32Decode, base32Encode, groupBase32, hmacSha1, parseOtpAuthUri, selfTest, sha1 } from './index';

const hex = (b: Uint8Array) => Buffer.from(b).toString('hex');

test('autoverificación contra spec.json (misma que el backend)', () => {
  assert.ok(selfTest() >= 20);
});

test('SHA-1 y HMAC-SHA1 coinciden con node:crypto', () => {
  for (const size of [0, 1, 55, 56, 63, 64, 65, 200]) {
    const data = new Uint8Array(randomBytes(size));
    assert.equal(hex(sha1(data)), createHash('sha1').update(data).digest('hex'));
    const key = new Uint8Array(randomBytes(size + 1));
    assert.equal(hex(hmacSha1(key, data)), createHmac('sha1', key).update(data).digest('hex'));
  }
});

test('Base32 ida y vuelta', () => {
  for (const size of [0, 1, 5, 10, 20, 33]) {
    const data = new Uint8Array(randomBytes(size));
    assert.deepEqual(base32Decode(groupBase32(base32Encode(data)).toLowerCase()), data);
  }
  assert.throws(() => base32Decode('ABC1'));
});

test('URI otpauth del QR (formato generado por el backend)', () => {
  const uri =
    'otpauth://totp/Lab%202FA%3Aana%40example.com?secret=JBSWY3DPEHPK3PXP&issuer=Lab%202FA&algorithm=SHA1&digits=6&period=30';
  assert.deepEqual(parseOtpAuthUri(uri), { secret: 'JBSWY3DPEHPK3PXP', account: 'ana@example.com', issuer: 'Lab 2FA' });
  assert.throws(() => parseOtpAuthUri('https://example.com'));
});
