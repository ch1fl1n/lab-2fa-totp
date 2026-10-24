-- Migración: se aplica con `supabase db push` (o pegándola en el SQL Editor de Supabase).
-- Supabase se usa solo como base de datos: no se usa Supabase Auth ni su MFA.

create table if not exists public.users (
  id                 uuid primary key default gen_random_uuid(),
  email              text not null unique,
  password_hash      text not null,                       -- PBKDF2-HMAC-SHA256
  totp_status        text not null default 'DISABLED'
                     check (totp_status in ('DISABLED', 'PENDING_VERIFICATION', 'ACTIVE')),
  totp_secret_enc    text,                                -- secreto TOTP cifrado con Fernet
  backup_codes       jsonb not null default '[]'::jsonb,  -- [{ "hash": "...", "used_at": null }]
  totp_activated_at  timestamptz,
  created_at         timestamptz not null default now()
);

-- RLS activado y sin políticas: solo la service_role (el backend Python) puede leer/escribir.
alter table public.users enable row level security;
