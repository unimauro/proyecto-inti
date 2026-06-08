-- Proyecto INTI — Turismo & economía local (comunitario)
create table if not exists public.inti_turismo (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  ubigeo text not null,
  distrito text,
  categoria text not null default 'turismo',
  nombre text not null,
  descripcion text,
  contacto text,
  url text not null,
  thumb_url text,
  likes int not null default 0,
  reports int not null default 0
);
create index if not exists inti_turismo_ubigeo_idx on public.inti_turismo (ubigeo, created_at desc);
alter table public.inti_turismo enable row level security;
drop policy if exists "tur lectura" on public.inti_turismo;
create policy "tur lectura" on public.inti_turismo for select using (reports < 5);
drop policy if exists "tur insert" on public.inti_turismo;
create policy "tur insert" on public.inti_turismo for insert with check (
  char_length(coalesce(nombre,''))<=80 and char_length(coalesce(descripcion,''))<=240 and char_length(coalesce(contacto,''))<=120
);
create or replace function public.tur_like(fid uuid) returns int language sql security definer set search_path=public as $$ update public.inti_turismo set likes=likes+1 where id=fid returning likes; $$;
create or replace function public.tur_report(fid uuid) returns void language sql security definer set search_path=public as $$ update public.inti_turismo set reports=reports+1 where id=fid; $$;
grant execute on function public.tur_like(uuid) to anon, authenticated;
grant execute on function public.tur_report(uuid) to anon, authenticated;
