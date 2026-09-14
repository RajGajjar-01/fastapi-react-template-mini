-- Injects the user's role into the JWT as app_metadata.user_role so the
-- backend can authorize requests without a DB round-trip per request.
-- Must be enabled as a Custom Access Token Hook (Supabase dashboard for
-- hosted projects; GOTRUE_HOOK_CUSTOM_ACCESS_TOKEN_* env vars locally).
create or replace function public.custom_access_token_hook(event jsonb)
returns jsonb
language plpgsql
stable
as $$
declare
  claims jsonb;
  user_role text;
begin
  select role into user_role from public.profiles where id = (event->>'user_id')::uuid;

  claims := event->'claims';
  if jsonb_typeof(claims->'app_metadata') is null then
    claims := jsonb_set(claims, '{app_metadata}', '{}');
  end if;
  claims := jsonb_set(claims, '{app_metadata,user_role}', to_jsonb(coalesce(user_role, 'user')));

  event := jsonb_set(event, '{claims}', claims);
  return event;
end;
$$;

grant execute on function public.custom_access_token_hook to supabase_auth_admin;
revoke execute on function public.custom_access_token_hook from authenticated, anon, public;
