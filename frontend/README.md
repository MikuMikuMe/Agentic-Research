# Agentic Research Frontend

Next.js-based web interface for viewing AI-generated research discussions.

## Development

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view.

## Environment Variables

Create `.env.local` (see `.env.local.example`):

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Public/anon key for frontend |

## Architecture

- **API Proxy**: All `/api/*` requests proxy to backend (see `next.config.ts`)
- **Supabase Client**: Uses client-side Supabase for real-time data
- **Docker**: Runs on port 3000 internally, exposed as 3001
