-- Enable the pgvector extension to work with embedding vectors
create extension if not exists vector;

-- 1. Table to track unique items (Deduplication)
create table if not exists known_items (
  id uuid primary key default gen_random_uuid(),
  url text unique,
  title text,
  embedding vector(768), -- Dimension for Gemini (change to 1536 for OpenAI)
  created_at timestamptz default now()
);

-- 2. Threads (Discussion Topics)
create table if not exists threads (
  id uuid primary key default gen_random_uuid(),
  topic_title text not null,
  summary text,
  research_brief text, -- Deep research notes
  created_at timestamptz default now()
);

-- 3. Comments (Agent Discussions)
create table if not exists comments (
  id uuid primary key default gen_random_uuid(),
  thread_id uuid references threads(id) on delete cascade,
  agent_persona text not null, -- "Skeptic", "Hype", "Aggregator"
  content text not null,
  created_at timestamptz default now()
);

-- 4. Function for Semantic Search (Deduplication)
create or replace function match_documents (
  query_embedding vector(768),
  match_threshold float,
  match_count int
)
returns table (
  id uuid,
  title text,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    known_items.id,
    known_items.title,
    1 - (known_items.embedding <=> query_embedding) as similarity
  from known_items
  where 1 - (known_items.embedding <=> query_embedding) > match_threshold
  order by known_items.embedding <=> query_embedding
  limit match_count;
end;
$$;
