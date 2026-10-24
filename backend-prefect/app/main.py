import logging
from contextlib import asynccontextmanager
from pathlib import Path

import totp_core
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from . import timesync
from .errors import AuthError
from .routes import auth, time, twofa, vault

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("app")
WEB_DIR = Path(__file__).resolve().parent.parent / "web"


@asynccontextmanager
async def lifespan(_: FastAPI):
    # La librería compartida se verifica ANTES de aceptar peticiones: si no cumple spec.json, no arranca.
    log.info("totp-core: %d vectores de spec.json verificados", totp_core.self_test())
    timesync.check_in_background()
    yield


app = FastAPI(title="Backend 2FA (Step-Up + Prefect)", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router)
app.include_router(twofa.router)
app.include_router(vault.router)
app.include_router(time.router)


@app.exception_handler(AuthError)
def auth_error_handler(_: Request, exc: AuthError):
    """Errores lanzados dentro de los Flows de Prefect -> respuesta HTTP clara."""
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc), "error": type(exc).__name__})


@app.get("/", include_in_schema=False)
def web_app():
    """Web app de login (registro, Step-Up, activación con QR y bóveda)."""
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
def health():
    return {"ok": True}
