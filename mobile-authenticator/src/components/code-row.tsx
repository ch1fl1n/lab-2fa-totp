import * as Clipboard from 'expo-clipboard';
import { useMemo, useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Accent, Danger } from '@/components/ui';
import { Fonts, Spacing } from '@/constants/theme';
import { base32Decode, counterAt, hotp, PERIOD, secondsRemaining } from '@totp-core';
import { useTheme } from '@/hooks/use-theme';
import type { Account } from '@/state/accounts';

/** Muestra el código TOTP de una cuenta calculado con la hora sincronizada `now`. */
export function CodeRow({ account, now, onLongPress }: { account: Account; now: number; onLongPress?: () => void }) {
  const theme = useTheme();
  const [copied, setCopied] = useState(false);
  const key = useMemo(() => base32Decode(account.secret), [account.secret]);
  const counter = counterAt(now);
  // Solo se recalcula el HMAC cuando cambia el contador (cada 30 s), no en cada tick.
  const code = useMemo(() => hotp(key, counter), [key, counter]);
  const remaining = secondsRemaining(now);
  const urgent = remaining < 5;

  const copy = async () => {
    await Clipboard.setStringAsync(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };

  return (
    <Pressable
      onPress={copy}
      onLongPress={onLongPress}
      style={({ pressed }) => [styles.card, { backgroundColor: theme.backgroundElement, opacity: pressed ? 0.8 : 1 }]}>
      <ThemedText type="small" themeColor="textSecondary" numberOfLines={1}>
        {account.issuer ? `${account.issuer} · ${account.label}` : account.label}
      </ThemedText>
      <View style={styles.codeLine}>
        <ThemedText style={[styles.code, { color: urgent ? Danger : theme.text }]}>
          {`${code.slice(0, 3)} ${code.slice(3)}`}
        </ThemedText>
        <ThemedText type="smallBold" style={{ color: urgent ? Danger : theme.textSecondary }}>
          {copied ? 'Copiado' : `${Math.ceil(remaining)} s`}
        </ThemedText>
      </View>
      <View style={[styles.track, { backgroundColor: theme.backgroundSelected }]}>
        <View
          style={[
            styles.bar,
            { width: `${(remaining / PERIOD) * 100}%`, backgroundColor: urgent ? Danger : Accent },
          ]}
        />
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: { borderRadius: 16, padding: Spacing.three, gap: Spacing.two },
  codeLine: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  code: { fontFamily: Fonts?.mono, fontSize: 34, lineHeight: 40, fontWeight: 700, letterSpacing: 2 },
  track: { height: 4, borderRadius: 2, overflow: 'hidden' },
  bar: { height: 4, borderRadius: 2 },
});
