import { Pressable, StyleSheet } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Danger, Success } from '@/components/ui';
import { Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import { useTimeSync } from '@/state/time-sync';

export function formatOffset(ms: number): string {
  const sign = ms >= 0 ? '+' : '−';
  const abs = Math.abs(ms);
  return abs >= 1000 ? `${sign}${(abs / 1000).toFixed(2)} s` : `${sign}${abs} ms`;
}

/** Indicador compacto del estado de sincronización; tocarlo vuelve a sincronizar. */
export function SyncBadge() {
  const theme = useTheme();
  const { info, syncing, error, sync } = useTimeSync();

  let text = 'Sin sincronizar';
  let color: string = theme.textSecondary;
  if (syncing) text = 'Sincronizando…';
  else if (error && !info) {
    text = 'Servidor no disponible';
    color = Danger;
  } else if (info) {
    text = `Hora sincronizada · desfase ${formatOffset(info.offsetMs)}`;
    color = error ? theme.textSecondary : Success;
  }

  return (
    <Pressable onPress={sync} style={[styles.badge, { backgroundColor: theme.backgroundElement }]}>
      <ThemedText type="small" style={{ color }}>
        ● {text}
      </ThemedText>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  badge: { alignSelf: 'flex-start', borderRadius: 999, paddingHorizontal: Spacing.three, paddingVertical: Spacing.one },
});
