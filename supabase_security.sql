-- Enable RLS on all tables
alter table known_items enable row level security;
alter table threads enable row level security;
alter table comments enable row level security;

-- Policies
-- 1. Public Read Access (Anyone can view threads/comments)
create policy "Public threads are viewable by everyone"
  on threads for select
  using ( true );

create policy "Public comments are viewable by everyone"
  on comments for select
  using ( true );

-- 2. Service Role Only Write Access (Only Backend can create/edit)
-- Implicitly, if no policy allows INSERT/UPDATE for 'anon', it's blocked.
-- So we just don't create an INSERT policy for public.
-- The Service Role bypasses RLS, so it can still write.
