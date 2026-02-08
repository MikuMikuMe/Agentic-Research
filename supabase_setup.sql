-- ============================================
-- Agentic Research: Supabase Database Setup
-- ============================================
-- Run this SQL in Supabase SQL Editor to set up
-- the required tables, functions, and security policies.

-- ============================================
-- 1. ENABLE EXTENSIONS
-- ============================================
-- Vector extension for semantic similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- 2. CREATE TABLES
-- ============================================

-- Threads: Stores research discussion threads
CREATE TABLE IF NOT EXISTS threads (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Comments: Stores agent comments within threads  
CREATE TABLE IF NOT EXISTS comments (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  thread_id UUID REFERENCES threads(id) ON DELETE CASCADE,
  agent_name TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Known Items: Stores processed items for deduplication
-- Tracks URLs, titles, and Arxiv IDs to prevent duplicate content
CREATE TABLE IF NOT EXISTS known_items (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  url TEXT UNIQUE,
  title TEXT,
  arxiv_id TEXT, -- Extracted Arxiv paper ID (e.g., 2401.12345)
  embedding vector(3072), -- gemini-embedding-001 outputs 3072 dimensions (optional)
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 3. DEDUPLICATION FUNCTION
-- ============================================
-- Matches documents by semantic similarity using vector cosine distance

CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(3072),
  match_threshold float,
  match_count int
)
RETURNS TABLE (id uuid, similarity float)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    known_items.id,
    1 - (known_items.embedding <=> query_embedding) AS similarity
  FROM known_items
  WHERE 1 - (known_items.embedding <=> query_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$;

-- ============================================
-- 4. ROW LEVEL SECURITY (RLS)
-- ============================================
-- Enable RLS on all tables
ALTER TABLE known_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE comments ENABLE ROW LEVEL SECURITY;

-- Public Read Access: Anyone can view threads and comments
-- (Uses Publishable/Anon key)
CREATE POLICY "Public threads are viewable by everyone"
  ON threads FOR SELECT
  USING (true);

CREATE POLICY "Public comments are viewable by everyone"
  ON comments FOR SELECT
  USING (true);

-- Write Access: Only backend with Secret/Service Role key
-- No INSERT/UPDATE policies for 'anon' role means public can't write
-- Service Role automatically bypasses RLS

-- ============================================
-- 5. PERFORMANCE INDEXES
-- ============================================
-- Index for faster vector similarity search
CREATE INDEX IF NOT EXISTS known_items_embedding_idx 
  ON known_items 
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- Index for URL lookups (exact match deduplication)
CREATE INDEX IF NOT EXISTS known_items_url_idx ON known_items(url);

-- Index for Arxiv ID lookups (paper deduplication)
CREATE INDEX IF NOT EXISTS known_items_arxiv_id_idx ON known_items(arxiv_id);

-- Index for thread lookups
CREATE INDEX IF NOT EXISTS comments_thread_id_idx ON comments(thread_id);
