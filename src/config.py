import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
load_dotenv(override=True)

# Base directory for spooling
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SPOOL_DIR = os.path.join(BASE_DIR, 'spool')
INPUT_DIR = os.path.join(SPOOL_DIR, 'input')
OUTPUT_DIR = os.path.join(SPOOL_DIR, 'output')

os.makedirs(SPOOL_DIR, exist_ok=True)
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Example: Get OpenAI API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.path.join(BASE_DIR, "app.log")

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Add other global config here as needed