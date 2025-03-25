"""
Configuration settings for the CV generator application.
"""
import os
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

# API Keys
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    OPENAI_MODEL = st.secrets.get("OPENAI_MODEL", "gpt-4o")
    OPENAI_TEMPERATURE = float(st.secrets.get("OPENAI_TEMPERATURE", "0.0"))
except (KeyError, FileNotFoundError):
    # Fall back to environment variables when not running in Streamlit Cloud
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
    OPENAI_TEMPERATURE = float(os.environ.get("OPENAI_TEMPERATURE", "0.0"))

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