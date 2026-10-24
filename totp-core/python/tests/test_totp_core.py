import base64
import os

import pytest

import totp_core as tc


def test_self_test_passes():
    assert tc.self_test() >= 20


@pytest.mark.parametrize("size", [0, 1, 5, 10, 16, 20, 33])
def test_base32_matches_stdlib(size):
    data = os.urandom(size)
    ours = tc.base32_encode(data)
    assert ours == base64.b32encode(data).decode().rstrip("=")
    assert tc.base32_decode(tc.base32_group(ours).lower()) == data


def test_windows_c_minus_1_c_c_plus_1():
    key, now = os.urandom(20), 1_700_000_000
    assert tc.find_match(key, tc.totp(key, now), now).window == "C"
    assert tc.find_match(key, tc.totp(key, now - 30), now).window == "C-1"
    assert tc.find_match(key, tc.totp(key, now + 30), now).window == "C+1"
    assert tc.find_match(key, tc.totp(key, now - 60), now) is None


def test_otpauth_roundtrip():
    uri = tc.build_otpauth_uri("JBSW Y3DP EHPK 3PXP", "ana@example.com", "Lab 2FA")
    assert uri.startswith("otpauth://totp/Lab%202FA%3Aana%40example.com?secret=JBSWY3DPEHPK3PXP")
    assert tc.parse_otpauth_uri(uri) == {"secret": "JBSWY3DPEHPK3PXP", "account": "ana@example.com", "issuer": "Lab 2FA"}
