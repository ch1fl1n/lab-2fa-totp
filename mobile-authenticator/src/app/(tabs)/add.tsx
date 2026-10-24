import { router } from 'expo-router';
import { useState } from 'react';
import { base32Decode, isValidBase32, totp } from '@totp-core';

import { ThemedText } from '@/components/themed-text';
import { Button, Card, ErrorText, Field, Screen } from '@/components/ui';
import { useServerClock } from '@/hooks/use-server-clock';
import { useAccounts } from '@/state/accounts';

const MIN_SECRET_BYTES = 10; // 80 bits; el servidor genera 20 bytes (160 bits)

export default function AddAccountScreen() {
  const { add } = useAccounts();
  const now = useServerClock(1000);
  const [label, setLabel] = useState('');
  const [issuer, setIssuer] = useState('');
  const [secret, setSecret] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const validSecret = isValidBase32(secret) && base32Decode(secret).length >= MIN_SECRET_BYTES;
  const preview = validSecret ? totp(base32Decode(secret), now) : null;

  const save = async () => {
    if (!label.trim()) return setError('Ponle un nombre a la cuenta');
    if (!validSecret) return setError('El secreto debe ser Base32 (A-Z y 2-7) de al menos 16 caracteres');
    setSaving(true);
    try {
      await add({ label, issuer, secret });
      setLabel('');
      setIssuer('');
      setSecret('');
      setError(null);
      router.navigate('/');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Screen>
      <ThemedText type="subtitle">Agregar cuenta</ThemedText>
      <Button title="Escanear código QR" onPress={() => router.push('/scan')} />
      <ThemedText type="small" themeColor="textSecondary">
        O escribe a mano el secreto Base32 que muestra la web app. Los espacios no importan.
      </ThemedText>

      <Field label="Nombre (ej. tu email)" value={label} onChangeText={setLabel} />
      <Field label="Emisor (opcional)" value={issuer} onChangeText={setIssuer} />
      <Field
        label="Secreto"
        value={secret}
        onChangeText={(t) => setSecret(t.toUpperCase())}
        placeholder="ABCD EFGH IJKL ..."
        autoCapitalize="characters"
        mono
        multiline
      />
      <ErrorText>{error}</ErrorText>

      {preview && (
        <Card>
          <ThemedText type="small" themeColor="textSecondary">
            Código actual con este secreto
          </ThemedText>
          <ThemedText type="subtitle">{`${preview.slice(0, 3)} ${preview.slice(3)}`}</ThemedText>
        </Card>
      )}

      <Button title="Guardar" onPress={save} loading={saving} />
    </Screen>
  );
}
