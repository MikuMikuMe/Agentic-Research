import sys
import os

# Set dummy env vars for testing
os.environ["SUPABASE_URL"] = "https://example.supabase.co"
os.environ["SUPABASE_KEY"] = "dummy-key"
os.environ["GOOGLE_API_KEY"] = "dummy-key"

# Add backend to path
sys.path.append(os.getcwd())

try:
    from app.main import app
    from app.agents.graph import workflow
    print("Imports successful!")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
