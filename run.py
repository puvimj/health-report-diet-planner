"""
Runner script for Personal Health Report Manager and Diet Planner
Starts the FastAPI server with automatic database initialization and seeding.
"""
import uvicorn
import os
import sys

# Ensure project root is in Python path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

def main():
    print("=" * 65)
    print(" HealthTrack & DietRx - Personal Medical Archive & Diet Planner")
    print("=" * 65)

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")

    print(f"\n🚀 Server starting at: http://{host}:{port}")
    print(f"📖 Interactive API Docs: http://{host}:{port}/docs")
    print("\nPress Ctrl+C to stop the server.\n")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True
    )

if __name__ == "__main__":
    main()
