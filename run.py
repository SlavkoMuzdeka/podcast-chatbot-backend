"""
Startup script for the Podcast Chatbot Flask API
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_ENV", "production") == "development"

    print(f"🚀 Starting Podcast Chatbot API on {host}:{port}")
    print(f"📝 Debug mode: {debug}")
    print(f"🌐 Frontend URL: {os.getenv('FRONTEND_URL', 'http://localhost:3000')}")

    app.run(host=host, port=port, debug=debug, threaded=True)
