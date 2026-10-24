import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';
import { AppState } from 'react-native';

import { clockJumped, getSyncInfo, loadSavedSync, syncTime, type TimeSyncInfo } from '@/time/sync';

const RESYNC_EVERY_MS = 10 * 60 * 1000;
const JUMP_CHECK_EVERY_MS = 5 * 1000;

type TimeSyncState = {
  info: TimeSyncInfo | null;
  syncing: boolean;
  error: string | null;
  sync: () => Promise<void>;
};

const TimeSyncContext = createContext<TimeSyncState | null>(null);

/** Mantiene el offset al día: al abrir la app, al volver a primer plano, cada 10 min y si la hora salta. */
export function TimeSyncProvider({ children }: { children: ReactNode }) {
  const [info, setInfo] = useState<TimeSyncInfo | null>(getSyncInfo());
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sync = useCallback(async () => {
    setSyncing(true);
    setError(null);
    try {
      setInfo(await syncTime());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSyncing(false);
    }
  }, []);

  useEffect(() => {
    // Primero el último offset guardado (sirve sin red) y luego una medición nueva.
    loadSavedSync().then((saved) => {
      if (saved) setInfo(saved);
      return sync();
    });

    const periodic = setInterval(sync, RESYNC_EVERY_MS);
    const jumpCheck = setInterval(() => {
      if (clockJumped()) sync();
    }, JUMP_CHECK_EVERY_MS);
    const appState = AppState.addEventListener('change', (state) => {
      if (state === 'active') sync();
    });

    return () => {
      clearInterval(periodic);
      clearInterval(jumpCheck);
      appState.remove();
    };
  }, [sync]);

  return (
    <TimeSyncContext.Provider value={{ info, syncing, error, sync }}>
      {children}
    </TimeSyncContext.Provider>
  );
}

export function useTimeSync(): TimeSyncState {
  const ctx = useContext(TimeSyncContext);
  if (!ctx) throw new Error('useTimeSync debe usarse dentro de <TimeSyncProvider>');
  return ctx;
}
