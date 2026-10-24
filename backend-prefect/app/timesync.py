"""Diagnóstico del reloj del propio servidor contra NTP.

La app sincroniza su reloj con el del servidor, así que el servidor debe tener la hora bien.
Al arrancar se consulta pool.ntp.org y se guarda el desfase (solo informativo).
"""

import logging
import threading

log = logging.getLogger("timesync")
ntp_offset_ms: float | None = None


def _check() -> None:
    global ntp_offset_ms
    try:
        import ntplib

        response = ntplib.NTPClient().request("pool.ntp.org", version=3, timeout=3)
        ntp_offset_ms = round(response.offset * 1000, 1)
        level = logging.WARNING if abs(ntp_offset_ms) > 2000 else logging.INFO
        log.log(level, "Desfase del reloj del servidor vs NTP: %.1f ms", ntp_offset_ms)
    except Exception as exc:  # sin internet o UDP 123 bloqueado
        log.warning("No se pudo consultar NTP: %s", exc)


def check_in_background() -> None:
    threading.Thread(target=_check, daemon=True).start()
