import Constants from 'expo-constants';

/**
 * URL del backend. La app NO necesita el backend para generar códigos (funciona en modo avión);
 * solo lo usa, cuando hay red, para medir el desfase de reloj con GET /time.
 *
 * 1. EXPO_PUBLIC_API_URL en mobile-authenticator/.env si está definida.
 * 2. Si no, la IP del PC que corre Metro (la misma que usa Expo Go) con el puerto 8000.
 */
function resolveApiUrl(): string {
  const fromEnv = process.env.EXPO_PUBLIC_API_URL;
  if (fromEnv) return fromEnv.replace(/\/$/, '');
  const host = Constants.expoConfig?.hostUri?.split(':')[0];
  return host ? `http://${host}:8000` : 'http://localhost:8000';
}

export const API_URL = resolveApiUrl();

/** Respuesta de GET /time (backend-prefect/app/schemas.py). */
export type TimeResponse = {
  server_time_ms: number;
  counter: number;
  period: number;
  seconds_remaining: number;
  server_ntp_offset_ms: number | null;
};
