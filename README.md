# Laboratorio 2FA (TOTP) desde cero + Observabilidad con Prefect

| Carpeta | Qué es |
|---|---|
| `totp-core/` | **Librería compartida** del cálculo TOTP (Base32, SHA-1, HMAC, HOTP RFC 4226, TOTP RFC 6238, URI `otpauth://`) en **Python** y **TypeScript**, más `spec.json` con la especificación y los vectores oficiales. Backend y app la cargan **antes** de calcular y se autoverifican: si no cumplen `spec.json`, no arrancan. |
| `backend-prefect/` | API FastAPI con Step-Up Auth, máquina de estados, Strategy, anti-replay y flows de **Prefect**. Sirve también la **web app de login** en `/`. Usuarios en **Supabase** (solo como base de datos). |
| `supabase/` | Configuración de la CLI de Supabase y la migración de la tabla `users` (Supabase se usa solo como base de datos). |
| `mobile-authenticator/` | App **React Native + Expo Go**. Authenticator offline (modo avión): escanea el QR con `expo-camera` o recibe el secreto a mano, y muestra el código de 6 dígitos con barra de 30 s. Sincroniza su reloj con el backend cuando hay red. |

## Arquitectura

```
Web app (/)  ──login──▶  POST /auth/login            ──▶ flow login-password        ─▶ pre_auth_token
             ──setup──▶  POST /2fa/setup  (QR)        ─▶ estado PENDING_VERIFICATION
             ──código─▶  POST /2fa/activate           ──▶ flow activate-2fa         ─▶ ACTIVE + códigos de respaldo + access_token
             ──código─▶  POST /auth/verify-2fa        ──▶ flow verify-2fa:
                                                            1. validate_pre_auth_state
                                                            2. check_anti_replay_cache   (ReplayAttackDetected)
                                                            3. execute_mfa_strategy      (TOTPStrategy | BackupCodeStrategy, log C-1/C/C+1)
                                                            4. issue_elevated_session    (JWT mfa_verified: true)
             ──token──▶  GET /api/boveda-secreta      (solo con mfa_verified)

App móvil (modo avión): HMAC-SHA1(secreto, floor(UnixTime/30)) con totp-core  ──▶ código de 6 dígitos
```

| Requisito de la guía | Dónde |
|---|---|
| TOTP desde cero (sin otplib/speakeasy) | `totp-core/ts/*.ts` (SHA-1 y HMAC escritos a mano), `totp-core/python/totp_core/` |
| QR `otpauth://` + ingreso manual | `backend-prefect/app/routes/twofa.py` (QR con `segno`), `mobile-authenticator/src/app/scan.tsx`, `src/app/(tabs)/add.tsx` |
| Código grande + cuenta regresiva 30 → 0 | `mobile-authenticator/src/components/code-row.tsx` |
| Máquina de estados `PENDING_VERIFICATION → ACTIVE` | `backend-prefect/app/db.py` (`TotpStatus`), task `transition_to_active` |
| Step-Up: `pre_auth_token` vs `access_token` con `mfa_verified` | `app/security.py`, `app/flows.py`, `app/deps.py` (`elevated_user`) |
| Strategy: `SecondFactorStrategy`, `TOTPStrategy`, `BackupCodeStrategy` | `backend-prefect/app/strategies.py` |
| Anti-replay `(user_id, código)` 90 s | `backend-prefect/app/replay_cache.py`, task `check_anti_replay_cache` |
| `@flow` / `@task` con logs de ventana | `backend-prefect/app/flows.py` |
| Ruta protegida | `GET /api/boveda-secreta` (`app/routes/vault.py`) |

### Sincronización de hora (extra)
El TOTP depende de que celular y servidor tengan la misma hora. La app mide el desfase con `GET /time`
(algoritmo de Cristian: `offset = t_servidor − (t0 + t1)/2`, se toma la muestra con menor ida y vuelta) y calcula
los códigos con `Date.now() + offset`. Se resincroniza al abrir, al volver a la app, cada 10 min y si detecta que
alguien cambió la hora del teléfono. **Sin red (modo avión) usa el último desfase guardado**, así que sigue funcionando.
El servidor además acepta las ventanas C-1, C y C+1 y registra en Prefect cuál coincidió.

## Puesta en marcha

Requisitos: Python 3.11+, Node 20+, la app **Expo Go** en el celular y el celular en la misma red WiFi que el PC.

### 1. Supabase
La tabla `users` está en `supabase/migrations/` y se aplica con la CLI de Supabase (desde la raíz del repo):
```bash
supabase login
supabase link --project-ref <ref-del-proyecto>
supabase db push
```
Luego copia la URL (`https://<ref>.supabase.co`) y la **service_role key** (`supabase projects api-keys --project-ref <ref>`)
a `backend-prefect/.env`. Alternativa sin CLI: pegar el archivo de la migración en el **SQL Editor**.

> Para probar sin Supabase: `USE_MEMORY_DB=1` en `.env` (los datos se borran al reiniciar).

### 2. Prefect (terminal 1)
```bash
cd backend-prefect
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
prefect server start
```
UI de Prefect: http://127.0.0.1:4200

### 3. Backend (terminal 2)
```bash
cd backend-prefect
.venv\Scripts\activate
copy .env.example .env
```
Completa `.env` (los comandos para generar `JWT_SECRET` y `FERNET_KEY` están en el archivo) y arranca:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- Web app de login: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Permite el puerto 8000 en el Firewall de Windows para que el celular llegue al backend.

### 4. App móvil (terminal 3)
```bash
cd mobile-authenticator
npm install
npx expo start
```
Escanea el QR de Metro con Expo Go. La app detecta sola la IP del PC; si no, crea `mobile-authenticator/.env` con
`EXPO_PUBLIC_API_URL=http://<IP-del-PC>:8000`.

## Pruebas automáticas
```bash
cd backend-prefect && pytest                     # 4 pruebas de aceptación con Prefect real
cd totp-core/python && pytest                    # librería compartida (Python)
cd mobile-authenticator && npm run test:totp-core   # librería compartida (TypeScript)
```

## Guion de la demo (pruebas de aceptación)
1. **Paridad**: en la web app crea una cuenta → aparece el QR. Escanéalo con esta app y con Google/Microsoft
   Authenticator: muestran el mismo código al mismo tiempo. Escribe el código para pasar a `ACTIVE`.
2. **Modo avión**: activa el modo avión, espera a que cambie la ventana de 30 s, entra en la web app con el código
   nuevo y abre `GET /api/boveda-secreta`.
3. **Anti-Replay**: pulsa *Salir*, vuelve a entrar y escribe el **mismo** código. La web muestra
   `ReplayAttackDetected` y en Prefect el flow `verify-2fa-totp` aparece en rojo en `check_anti_replay_cache`.
4. **Clock skew / respaldo**: en Prefect, el log de `execute_mfa_strategy` dice `Match TOTP en la ventana C-1/C/C+1`.
   O elige *Código de respaldo* y entra con uno de los 8 códigos que se mostraron al activar.
