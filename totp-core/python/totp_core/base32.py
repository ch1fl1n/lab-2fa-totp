"""Base32 (RFC 4648) implementado a mano, sin base64.b32encode/b32decode."""

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
_LOOKUP = {c: i for i, c in enumerate(ALPHABET)}


def encode(data: bytes, padding: bool = False) -> str:
    """Convierte bytes a Base32 agrupando los bits de 5 en 5."""
    out = []
    buffer = 0  # acumulador de bits
    bits = 0  # cuántos bits válidos hay en el acumulador
    for byte in data:
        buffer = (buffer << 8) | byte
        bits += 8
        while bits >= 5:
            bits -= 5
            out.append(ALPHABET[(buffer >> bits) & 0x1F])
    if bits > 0:
        # Bits sobrantes: se rellenan con ceros a la derecha.
        out.append(ALPHABET[(buffer << (5 - bits)) & 0x1F])
    result = "".join(out)
    if padding:
        result += "=" * (-len(result) % 8)
    return result


def normalize(text: str) -> str:
    """Quita espacios, guiones y '=' y pasa a mayúsculas (como lo teclea un humano)."""
    return "".join(ch for ch in text.upper() if ch not in " -=\t\n")


def decode(text: str) -> bytes:
    """Convierte Base32 a bytes. Lanza ValueError si hay caracteres inválidos."""
    clean = normalize(text)
    out = bytearray()
    buffer = 0
    bits = 0
    for ch in clean:
        if ch not in _LOOKUP:
            raise ValueError(f"Carácter Base32 inválido: {ch!r}")
        buffer = (buffer << 5) | _LOOKUP[ch]
        bits += 5
        if bits >= 8:
            bits -= 8
            out.append((buffer >> bits) & 0xFF)
    return bytes(out)


def group(text: str, size: int = 4) -> str:
    """'JBSWY3DPEHPK3PXP' -> 'JBSW Y3DP EHPK 3PXP' para que sea fácil de teclear."""
    return " ".join(text[i : i + size] for i in range(0, len(text), size))
