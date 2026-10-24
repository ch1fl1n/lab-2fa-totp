import time

import totp_core
from fastapi import APIRouter

from .. import timesync
from ..schemas import TimeOut

router = APIRouter(tags=["time"])


@router.get("/time", response_model=TimeOut)
def server_time():
    """Hora del servidor en ms. La app la usa para calcular su desfase (mobile-authenticator/src/time/sync.ts)."""
    now_ms = time.time_ns() // 1_000_000
    seconds = now_ms / 1000
    return TimeOut(
        server_time_ms=now_ms,
        counter=totp_core.counter_at(seconds),
        period=totp_core.PERIOD,
        seconds_remaining=round(totp_core.PERIOD - (seconds % totp_core.PERIOD), 3),
        server_ntp_offset_ms=timesync.ntp_offset_ms,
    )
