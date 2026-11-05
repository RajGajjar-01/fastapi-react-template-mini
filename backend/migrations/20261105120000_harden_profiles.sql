-- Hardening for public.profiles, which holds the role that the access-token
-- hook copies into the JWT. Found by the security audit.

-- 1. Row level security. Without it, a project that exposes the public schema
--    through the Supabase Data API (PostgREST) lets any signed-in user update
--    their own profiles.role, and that value becomes their admin claim.
--    The backend connects as the table owner (postgres), which bypasses RLS,
--    so the app is unaffected. The token hook runs as supabase_auth_admin and
--    gets an explicit read policy.
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.profiles FROM anon, authenticated, public;

GRANT SELECT ON TABLE public.profiles TO supabase_auth_admin;

DROP POLICY IF EXISTS "auth admin can read profiles" ON public.profiles;
CREATE POLICY "auth admin can read profiles"
    ON public.profiles
    AS PERMISSIVE
    FOR SELECT
    TO supabase_auth_admin
    USING (true);

-- 2. Tie each profile to its auth user, so deleting the user removes the
--    profile (and any elevated role) instead of leaving a stale row.
--    NOT VALID: existing rows are not checked, so the migration cannot fail on
--    old orphans. Remove them, then run:
--      ALTER TABLE public.profiles VALIDATE CONSTRAINT profiles_id_fkey;
DO $$
BEGIN
    IF to_regclass('auth.users') IS NOT NULL
       AND NOT EXISTS (
           SELECT 1 FROM pg_constraint
           WHERE conname = 'profiles_id_fkey'
             AND conrelid = 'public.profiles'::regclass
       ) THEN
        ALTER TABLE public.profiles
            ADD CONSTRAINT profiles_id_fkey
            FOREIGN KEY (id) REFERENCES auth.users (id) ON DELETE CASCADE NOT VALID;
    END IF;
END
$$;

-- 3. The profile id is the identity; the email is a copy that can change in
--    the auth service. A UNIQUE email made a re-created or renamed user fail
--    to log in (500) when an old row still held the address.
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS profiles_email_key;

-- 4. Bound the free-text fields (the API enforces the same limits).
--    NOT VALID so that existing long values do not block the migration.
ALTER TABLE public.profiles
    ADD CONSTRAINT profiles_full_name_len CHECK (char_length(full_name) <= 200) NOT VALID,
    ADD CONSTRAINT profiles_avatar_url_len CHECK (char_length(avatar_url) <= 2048) NOT VALID;

-- 5. Pin the search path of the trigger function.
ALTER FUNCTION public.update_updated_at() SET search_path = pg_catalog, public;
