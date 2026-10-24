import { DarkTheme, DefaultTheme, Stack, ThemeProvider } from 'expo-router';
import { useColorScheme } from 'react-native';
import { selfTest } from '@totp-core';

import { ThemedText } from '@/components/themed-text';
import { Danger, Screen } from '@/components/ui';
import { AccountsProvider } from '@/state/accounts';
import { TimeSyncProvider } from '@/state/time-sync';

// La librería compartida se verifica contra totp-core/spec.json ANTES de montar la app:
// si este dispositivo no calcula igual que el estándar (y que el backend), no se muestran códigos.
let selfTestError: string | null = null;
try {
  selfTest();
} catch (e) {
  selfTestError = e instanceof Error ? e.message : String(e);
}

export default function RootLayout() {
  const colorScheme = useColorScheme();

  if (selfTestError) {
    return (
      <Screen tabInset={false}>
        <ThemedText type="subtitle" style={{ color: Danger }}>
          Error en totp-core
        </ThemedText>
        <ThemedText type="code">{selfTestError}</ThemedText>
      </Screen>
    );
  }

  return (
    <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
      <TimeSyncProvider>
        <AccountsProvider>
          <Stack>
            <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
            <Stack.Screen name="scan" options={{ title: 'Escanear QR', presentation: 'modal' }} />
          </Stack>
        </AccountsProvider>
      </TimeSyncProvider>
    </ThemeProvider>
  );
}
