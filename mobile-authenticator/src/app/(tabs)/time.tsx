import { formatOffset } from '@/components/sync-badge';
import { ThemedText } from '@/components/themed-text';
import { Button, Card, ErrorText, Row, Screen } from '@/components/ui';
import { counterAt, secondsRemaining } from '@totp-core';
import { useServerClock } from '@/hooks/use-server-clock';
import { API_URL } from '@/api/client';
import { useTimeSync } from '@/state/time-sync';

const clock = (ms: number) => {
  const d = new Date(ms);
  const pad = (n: number, size = 2) => String(n).padStart(size, '0');
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}.${pad(d.getMilliseconds(), 3)}`;
};

export default function TimeScreen() {
  const { info, syncing, error, sync } = useTimeSync();
  const serverTime = useServerClock(100);
  const deviceTime = serverTime - (info?.offsetMs ?? 0);

  return (
    <Screen>
      <ThemedText type="subtitle">Sincronización</ThemedText>
      <ThemedText type="small" themeColor="textSecondary">
        Los códigos se calculan con la hora del servidor, no con la del celular. La app mide la
        diferencia (desfase) consultando {API_URL}/time varias veces y usa la medición más rápida.
      </ThemedText>

      <Card>
        <Row label="Hora del celular" value={clock(deviceTime)} />
        <Row label="Hora del servidor (estimada)" value={clock(serverTime)} />
        <Row label="Contador TOTP" value={counterAt(serverTime)} />
        <Row label="Siguiente código en" value={`${secondsRemaining(serverTime).toFixed(1)} s`} />
      </Card>

      <Card>
        {info ? (
          <>
            <Row label="Desfase (servidor − celular)" value={formatOffset(info.offsetMs)} />
            <Row label="Ida y vuelta (RTT)" value={`${info.rttMs} ms`} />
            <Row label="Precisión" value={`± ${Math.ceil(info.rttMs / 2)} ms`} />
            <Row label="Muestras válidas" value={info.samples} />
            <Row label="Última sincronización" value={new Date(info.syncedAt).toLocaleTimeString()} />
            <Row
              label="Reloj del servidor vs NTP"
              value={info.serverNtpOffsetMs == null ? 'sin dato' : formatOffset(Math.round(info.serverNtpOffsetMs))}
            />
          </>
        ) : (
          <ThemedText type="small" themeColor="textSecondary">
            Aún no se ha sincronizado. Se usa la hora del celular.
          </ThemedText>
        )}
        <ErrorText>{error}</ErrorText>
      </Card>

      <Button title="Sincronizar ahora" onPress={sync} loading={syncing} />
      <ThemedText type="small" themeColor="textSecondary">
        Se sincroniza sola al abrir la app, al volver a ella, cada 10 minutos y si detecta que la hora del
        celular cambió. Si no hay conexión se usa el último desfase guardado.
      </ThemedText>
    </Screen>
  );
}
