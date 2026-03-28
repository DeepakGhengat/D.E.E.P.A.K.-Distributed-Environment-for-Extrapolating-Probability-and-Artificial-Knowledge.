"""
Configuration Management
Loads configuration from the project root .env file.
"""

import os
from dotenv import load_dotenv

# Load .env from project root
# Path: D.E.E.P.A.K./.env (relative to backend/app/config.py)
project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=True)
else:
    # Fall back to environment variables (for production / Docker)
    load_dotenv(override=True)


class Config:
    """Flask & Application Configuration"""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'deepak-secret-key')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    JSON_AS_ASCII = False

    # LLM Provider: "anthropic" (direct Claude API) or "openrouter" (OpenRouter)
    # Auto-detected from which API key is set. Anthropic takes priority.
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')

    # Determine active provider
    LLM_PROVIDER = 'anthropic' if ANTHROPIC_API_KEY else ('openrouter' if OPENROUTER_API_KEY else None)
    LLM_API_KEY = ANTHROPIC_API_KEY or OPENROUTER_API_KEY
    LLM_MODEL_NAME = os.environ.get('CLAUDE_MODEL_NAME', 'claude-sonnet-4-20250514')

    # OpenRouter base URL
    OPENROUTER_BASE_URL = os.environ.get('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')

    # Zep Cloud (knowledge graph memory)
    ZEP_API_KEY = os.environ.get('ZEP_API_KEY')

    # File upload
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}

    # Text processing
    DEFAULT_CHUNK_SIZE = 500
    DEFAULT_CHUNK_OVERLAP = 50

    # OASIS simulation
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get('OASIS_DEFAULT_MAX_ROUNDS', '10'))
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/simulations')

    # OASIS platform available actions
    OASIS_TWITTER_ACTIONS = [
        'CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST'
    ]
    OASIS_REDDIT_ACTIONS = [
        'LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT',
        'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER',
        'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE'
    ]

    # Report Agent
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get('REPORT_AGENT_MAX_TOOL_CALLS', '5'))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get('REPORT_AGENT_MAX_REFLECTION_ROUNDS', '2'))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get('REPORT_AGENT_TEMPERATURE', '0.5'))

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []
        if not cls.LLM_API_KEY:
            errors.append("No LLM API key configured. Set ANTHROPIC_API_KEY or OPENROUTER_API_KEY")
        if not cls.ZEP_API_KEY:
            errors.append("ZEP_API_KEY is not configured")
        return errors
