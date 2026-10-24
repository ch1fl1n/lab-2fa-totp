import { router } from 'expo-router';
import { Alert } from 'react-native';

import { CodeRow } from '@/components/code-row';
import { SyncBadge } from '@/components/sync-badge';
import { ThemedText } from '@/components/themed-text';
import { Button, Card, Screen } from '@/components/ui';
import { useServerClock } from '@/hooks/use-server-clock';
import { useAccounts, type Account } from '@/state/accounts';

export default function CodesScreen() {
  const { accounts, loaded, remove } = useAccounts();
  const now = useServerClock(); // un solo reloj para toda la lista

  const confirmRemove = (account: Account) =>
    Alert.alert('Eliminar cuenta', `¿Eliminar "${account.label}" del authenticator?`, [
      { text: 'Cancelar', style: 'cancel' },
      { text: 'Eliminar', style: 'destructive', onPress: () => remove(account.id) },
    ]);

  return (
    <Screen>
      <ThemedText type="subtitle">Authenticator</ThemedText>
      <SyncBadge />

      {loaded && accounts.length === 0 && (
        <Card>
          <ThemedText type="smallBold">Aún no hay cuentas</ThemedText>
          <ThemedText type="small" themeColor="textSecondary">
            Agrega el secreto que te entrega el servidor para empezar a generar códigos.
          </ThemedText>
          <Button title="Agregar cuenta" onPress={() => router.navigate('/add')} />
        </Card>
      )}

      {accounts.map((account) => (
        <CodeRow key={account.id} account={account} now={now} onLongPress={() => confirmRemove(account)} />
      ))}

      {accounts.length > 0 && (
        <ThemedText type="small" themeColor="textSecondary">
          Toca un código para copiarlo. Mantén presionado para eliminar.
        </ThemedText>
      )}
    </Screen>
  );
}
