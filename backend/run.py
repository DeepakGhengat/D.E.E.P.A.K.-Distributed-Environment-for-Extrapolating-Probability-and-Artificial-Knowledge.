"""
D.E.E.P.A.K. Backend Entry Point
Distributed Environment for Extrapolating Probability and Artificial Knowledge
"""

import os
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.config import Config


def main():
    """Start D.E.E.P.A.K. backend server"""
    # Validate configuration
    errors = Config.validate()
    if errors:
        print("Configuration errors:")
        for err in errors:
            print(f"  - {err}")
        print("\nPlease check your .env file")
        sys.exit(1)

    # Create application
    app = create_app()

    # Run server
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5001))
    debug = Config.DEBUG

    print(f"D.E.E.P.A.K. backend starting on {host}:{port}")
    print(f"Claude model: {Config.LLM_MODEL_NAME}")
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    main()
