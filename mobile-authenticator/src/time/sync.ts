/**
 * Sincronización del reloj del celular con el del servidor (algoritmo de Cristian, como NTP simplificado).
 *
 *   t0 = hora del celular al enviar la petición
 *   ts = hora del servidor (respuesta de GET /time)
 *   t1 = hora del celular al recibir la respuesta
 *
 *   rtt    = t1 - t0                 (ida y vuelta)
 *   offset = ts - (t0 + t1) / 2      (se asume que la ida y la vuelta tardan lo mismo)
 *
 * El error máximo del offset es ±rtt/2, así que se toman varias muestras y se usa la de menor RTT.
 * Después, la "hora del servidor" en el celular es simplemente Date.now() + offset, y con ella se
 * calcula el contador TOTP. Así el código coincide aunque el reloj del teléfono esté desfasado.
 */
import { API_URL, type TimeResponse } from '@/api/client';
import { secureStorage } from '@/storage/secure';

export type TimeSyncInfo = {
  offsetMs: number; // servidor - celular
  rttMs: number; // RTT de la mejor muestra; precisión = ±rttMs/2
  syncedAt: number; // Date.now() del celular al sincronizar
  samples: number;
  serverNtpOffsetMs: number | null; // desfase del propio servidor contra NTP (diagnóstico)
};

const STORAGE_KEY = 'time_sync';
let current: TimeSyncInfo | null = null;
// Referencia monotónica para detectar si alguien cambia la hora del celular después de sincronizar.
let monotonicAtSync = 0;

/** Hora del servidor estimada en el celular, en ms Unix. Úsala en lugar de Date.now() para TOTP. */
export function serverNow(): number {
  return Date.now() + (current?.offsetMs ?? 0);
}

export function getSyncInfo(): TimeSyncInfo | null {
  return current;
}

async function takeSample() {
  const t0 = Date.now();
  const res = await fetch(`${API_URL}/time`, { headers: { 'Cache-Control': 'no-cache' } });
  const t1 = Date.now();
  if (!res.ok) throw new Error(`GET /time respondió ${res.status}`);
  const body = (await res.json()) as TimeResponse;
  return {
    rtt: t1 - t0,
    offset: body.server_time_ms - (t0 + t1) / 2,
    ntp: body.server_ntp_offset_ms,
  };
}

export async function syncTime(sampleCount = 5): Promise<TimeSyncInfo> {
  const results: Awaited<ReturnType<typeof takeSample>>[] = [];
  for (let i = 0; i < sampleCount; i++) {
    try {
      results.push(await takeSample());
    } catch {
      // Una muestra fallida no invalida las demás.
    }
  }
  if (results.length === 0) throw new Error(`No se pudo contactar a ${API_URL}/time`);

  const best = results.reduce((a, b) => (b.rtt < a.rtt ? b : a));
  current = {
    offsetMs: Math.round(best.offset),
    rttMs: best.rtt,
    syncedAt: Date.now(),
    samples: results.length,
    serverNtpOffsetMs: best.ntp,
  };
  monotonicAtSync = performance.now();
  await secureStorage.set(STORAGE_KEY, JSON.stringify(current));
  return current;
}

/** Recupera el último offset guardado (sirve sin red: los relojes derivan pocos ms por día). */
export async function loadSavedSync(): Promise<TimeSyncInfo | null> {
  const raw = await secureStorage.get(STORAGE_KEY);
  if (!raw) return null;
  try {
    current = JSON.parse(raw) as TimeSyncInfo;
    monotonicAtSync = performance.now() - (Date.now() - current.syncedAt);
    return current;
  } catch {
    return null;
  }
}

/**
 * true si la hora del celular saltó desde la última sincronización (el usuario la cambió a mano
 * o el sistema la corrigió). Compara el reloj de pared con un reloj monotónico que no se ve afectado.
 */
export function clockJumped(thresholdMs = 2000): boolean {
  if (!current) return false;
  const wallElapsed = Date.now() - current.syncedAt;
  const monotonicElapsed = performance.now() - monotonicAtSync;
  return Math.abs(wallElapsed - monotonicElapsed) > thresholdMs;
}
