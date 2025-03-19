"""
Configuration settings for the CV generator application.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI Config
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))

# File Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Ensure necessary directories exist
for directory in [OUTPUT_DIR, LOG_DIR]:
    os.makedirs(directory, exist_ok=True)

# Logging Config
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.path.join(LOG_DIR, "cv_generator.log")

# Application Settings
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4000"))