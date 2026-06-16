-- Primemash Marketing Agent System — Supabase Schema
-- Run this entire file in your Supabase SQL Editor (Dashboard → SQL Editor → New query)

-- ── Posts ────────────────────────────────────────────────────────────────────
create table if not exists posts (
  id              uuid primary key default gen_random_uuid(),
  platform        text not null check (platform in ('linkedin', 'twitter', 'instagram')),
  content         text not null,
  content_type    text not null,
  status          text not null default 'draft'
                  check (status in ('draft', 'scheduled', 'published', 'failed')),
  scheduled_at    timestamptz,
  published_at    timestamptz,
  platform_post_id text,
  campaign_id     uuid,
  error_message   text,
  metadata        jsonb not null default '{}',
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

-- ── Campaigns ────────────────────────────────────────────────────────────────
create table if not exists campaigns (
  id            uuid primary key default gen_random_uuid(),
  name          text not null,
  objective     text not null,
  platforms     text[] not null default '{}',
  duration_days integer not null default 14,
  status        text not null default 'active'
                check (status in ('active', 'paused', 'completed')),
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

-- ── Analytics ────────────────────────────────────────────────────────────────
create table if not exists analytics (
  id         uuid primary key default gen_random_uuid(),
  post_id    uuid references posts(id) on delete cascade,
  platform   text not null,
  metrics    jsonb not null default '{}',
  recorded_at timestamptz not null default now()
);

-- ── Foreign key: posts → campaigns ──────────────────────────────────────────
alter table posts
  add constraint fk_posts_campaign
  foreign key (campaign_id) references campaigns(id)
  on delete set null;

-- ── Auto-update updated_at ────────────────────────────────────────────────────
create or replace function update_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger posts_updated_at
  before update on posts
  for each row execute function update_updated_at();

create trigger campaigns_updated_at
  before update on campaigns
  for each row execute function update_updated_at();

-- ── Indexes ───────────────────────────────────────────────────────────────────
create index if not exists idx_posts_status      on posts(status);
create index if not exists idx_posts_platform    on posts(platform);
create index if not exists idx_posts_scheduled   on posts(scheduled_at) where status = 'scheduled';
create index if not exists idx_posts_campaign    on posts(campaign_id);
create index if not exists idx_posts_created     on posts(created_at desc);
create index if not exists idx_campaigns_status  on campaigns(status);

-- ── Row Level Security (RLS) — disable for service role key usage ─────────────
-- The Python backend uses the service role key which bypasses RLS.
-- Enable RLS only if you also add frontend direct Supabase queries.
-- alter table posts     enable row level security;
-- alter table campaigns enable row level security;
-- alter table analytics enable row level security;
