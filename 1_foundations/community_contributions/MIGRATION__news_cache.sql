-- Create table for caching news stories by industry and type
create table if not exists news_cache (
  id uuid primary key default gen_random_uuid(),
  industry text not null,
  type text not null, -- general, hiring, layoffs
  stories jsonb not null, -- array of story objects
  fetched_at timestamptz not null default now()
);

-- Index for fast lookup by industry/type
create index if not exists idx_news_cache_industry_type on news_cache (industry, type);

-- Only keep the latest cache per industry/type (optional, for cleanup)
-- You may want to add a unique constraint if you only want one row per industry/type
-- alter table news_cache add constraint unique_industry_type unique (industry, type); 