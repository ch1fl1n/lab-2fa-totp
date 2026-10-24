import { CameraView, useCameraPermissions, type BarcodeScanningResult } from 'expo-camera';
import { router } from 'expo-router';
import { useRef, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { parseOtpAuthUri } from '@totp-core';

import { ThemedText } from '@/components/themed-text';
import { Button, ErrorText, Screen } from '@/components/ui';
import { Spacing } from '@/constants/theme';
import { useAccounts } from '@/state/accounts';

/** Escanea el QR otpauth://totp/... que muestra la web app del backend y guarda la cuenta. */
export default function ScanScreen() {
  const [permission, requestPermission] = useCameraPermissions();
  const { add } = useAccounts();
  const [error, setError] = useState<string | null>(null);
  const handled = useRef(false); // la cámara dispara el evento varias veces por segundo

  const onScanned = async ({ data }: BarcodeScanningResult) => {
    if (handled.current) return;
    handled.current = true;
    try {
      const { secret, account, issuer } = parseOtpAuthUri(data);
      await add({ label: account || 'Cuenta', issuer, secret });
      router.dismissTo('/');
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setTimeout(() => (handled.current = false), 1500); // permitir reintentar
    }
  };

  if (!permission) return <Screen edges={[]} tabInset={false}>{null}</Screen>;

  if (!permission.granted) {
    return (
      <Screen edges={[]} tabInset={false}>
        <ThemedText>Se necesita la cámara para leer el código QR del 2FA.</ThemedText>
        <Button title="Permitir cámara" onPress={requestPermission} />
        <Button title="Escribir el secreto a mano" variant="secondary" onPress={() => router.back()} />
      </Screen>
    );
  }

  return (
    <View style={styles.container}>
      <CameraView
        style={StyleSheet.absoluteFill}
        facing="back"
        barcodeScannerSettings={{ barcodeTypes: ['qr'] }}
        onBarcodeScanned={onScanned}
      />
      <View style={styles.frame} pointerEvents="none" />
      <View style={styles.footer}>
        <ThemedText style={styles.hint}>Apunta al QR que muestra la web app</ThemedText>
        <ErrorText>{error}</ErrorText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000', alignItems: 'center', justifyContent: 'center' },
  frame: { width: 240, height: 240, borderWidth: 3, borderColor: '#ffffff', borderRadius: 24 },
  footer: {
    position: 'absolute',
    bottom: Spacing.six,
    left: Spacing.three,
    right: Spacing.three,
    alignItems: 'center',
    gap: Spacing.two,
  },
  hint: { color: '#ffffff', textAlign: 'center' },
});
