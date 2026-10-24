/** totp-core (TypeScript): misma lógica que totp-core/python, verificada con ../spec.json. */
export { base32Decode, base32Encode, groupBase32, isValidBase32, normalizeBase32 } from './base32';
export { hmacSha1 } from './hmac';
export { parseOtpAuthUri, type OtpAuthData } from './otpauth';
export { selfTest, spec } from './selftest';
export { sha1 } from './sha1';
export { counterAt, DIGITS, hotp, PERIOD, secondsRemaining, totp } from './totp';
