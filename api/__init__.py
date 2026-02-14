# API package
from engine.logger import setup_logging

# Configure logging for the API (default to dev mode/colors)
# In production, this can be overridden by env vars or main.py
logger = setup_logging(json_output=False, verbose=True)

__all__ = ["logger"]
