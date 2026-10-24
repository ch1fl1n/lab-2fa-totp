import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';

import { normalizeBase32 } from '@totp-core';
import { secureStorage } from '@/storage/secure';

/** Una cuenta del authenticator. El secreto nunca sale del dispositivo. */
export type Account = { id: string; label: string; issuer: string; secret: string };
type AccountMeta = Omit<Account, 'secret'>;

// El índice (sin secretos) y cada secreto se guardan en claves separadas de SecureStore,
// porque algunos iOS limitan el tamaño de cada valor (~2 KB).
const INDEX_KEY = 'accounts_index';
const secretKey = (id: string) => `account_secret_${id}`;

type AccountsState = {
  accounts: Account[];
  loaded: boolean;
  add: (input: Omit<Account, 'id'>) => Promise<Account>;
  remove: (id: string) => Promise<void>;
};

const AccountsContext = createContext<AccountsState | null>(null);

async function saveIndex(accounts: Account[]) {
  const index: AccountMeta[] = accounts.map(({ id, label, issuer }) => ({ id, label, issuer }));
  await secureStorage.set(INDEX_KEY, JSON.stringify(index));
}

export function AccountsProvider({ children }: { children: ReactNode }) {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    (async () => {
      const raw = await secureStorage.get(INDEX_KEY);
      const index: AccountMeta[] = raw ? JSON.parse(raw) : [];
      const full = await Promise.all(
        index.map(async (meta) => ({ ...meta, secret: (await secureStorage.get(secretKey(meta.id))) ?? '' }))
      );
      setAccounts(full.filter((a) => a.secret));
      setLoaded(true);
    })();
  }, []);

  const add = async (input: Omit<Account, 'id'>) => {
    const account: Account = {
      id: `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`,
      label: input.label.trim(),
      issuer: input.issuer.trim(),
      secret: normalizeBase32(input.secret),
    };
    const next = [...accounts, account];
    await secureStorage.set(secretKey(account.id), account.secret);
    await saveIndex(next);
    setAccounts(next);
    return account;
  };

  const remove = async (id: string) => {
    const next = accounts.filter((a) => a.id !== id);
    await saveIndex(next);
    await secureStorage.remove(secretKey(id));
    setAccounts(next);
  };

  return (
    <AccountsContext.Provider value={{ accounts, loaded, add, remove }}>
      {children}
    </AccountsContext.Provider>
  );
}

export function useAccounts(): AccountsState {
  const ctx = useContext(AccountsContext);
  if (!ctx) throw new Error('useAccounts debe usarse dentro de <AccountsProvider>');
  return ctx;
}
