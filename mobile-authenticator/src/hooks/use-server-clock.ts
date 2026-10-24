import { useEffect, useState } from 'react';

import { serverNow } from '@/time/sync';

/** Hora sincronizada con el servidor, re-renderizando cada `intervalMs`. */
export function useServerClock(intervalMs = 250): number {
  const [now, setNow] = useState(serverNow);

  useEffect(() => {
    const id = setInterval(() => setNow(serverNow()), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);

  return now;
}
