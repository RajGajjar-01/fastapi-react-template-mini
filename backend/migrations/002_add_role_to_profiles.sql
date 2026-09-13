ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'user'
  CONSTRAINT profiles_role_check CHECK (role IN ('user', 'moderator', 'admin'));
