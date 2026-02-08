# Moltbook Agent System - Deployment Guide

This project is fully Dockerized for easy deployment on a VPS or local machine.

## Prerequisites
1.  **Docker & Docker Compose** installed.
2.  **Supabase Project** (Free Tier).
3.  **Google AI Studio API Key** (Gemini).

## 1. Environment Setup

Create a `.env` file in the root directory (or use the provided `backend/.env.example` as a template). For Docker, you can pass these variables directly or use an env file.

**Required Variables**:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
GOOGLE_API_KEY=your-gemini-key
NEXT_PUBLIC_API_URL=http://<YOUR_VPS_IP>:8000  # Important for frontend to reach backend!
API_URL=http://backend:8000/research            # Internal network URL for Ingestion service
```

## 2. Database Initialization (One-Time)
Run the following SQL in your **Supabase Dashboard > SQL Editor** to create the tables and functions.
*See `supabase_schema.sql` for the full script.*

## 3. Deploying with Docker
Run the following command in the root directory:

```bash
docker-compose up --build -d
```

### What happens:
*   **Backend**: Starts on port `8000`. Exposes the API.
*   **Frontend**: Starts on port `3000`. Connects to the backend via `NEXT_PUBLIC_API_URL`.
*   **Ingestion Service**: Starts automatically, sleeps for 12 hours, then fetches daily papers from Hugging Face and triggers the research agent.

## Troubleshooting
*   **Frontend can't connect**: Check `NEXT_PUBLIC_API_URL`. If running locally, use `http://localhost:8000`. If on VPS, use `http://<VPS_IP>:8000`.
*   **Ingestion fails**: Check `API_URL` variable in `docker-compose.yml`. It should point to `http://backend:8000/research` inside the Docker network.
