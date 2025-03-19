"""
Helper functions for the CV generator application.
"""
import re
import json
from typing import Dict, List, Any, Optional, Tuple, Union

def extract_text_between(text: str, start_pattern: str, end_pattern: str) -> str:
    """
    Extract text between two patterns using regex.
    
    Args:
        text: Text to search within
        start_pattern: Starting pattern
        end_pattern: Ending pattern
        
    Returns:
        Extracted text or empty string if not found
    """
    pattern = f"{start_pattern}(.*?){end_pattern}"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def clean_bullet_points(text: str) -> List[str]:
    """
    Clean and extract bullet points from text.
    
    Args:
        text: Text containing bullet points
        
    Returns:
        List of cleaned bullet points
    """
    bullets = []
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('•') or line.startswith('-') or re.match(r'^\d+\.', line):
            bullet = re.sub(r'^[•\-\d\.]+\s*', '', line)
            if bullet.strip():
                bullets.append(bullet.strip())
    return bullets

def safe_json_loads(text: str, default: Any = None) -> Any:
    """
    Safely parse JSON from text with a default fallback.
    
    Args:
        text: JSON text to parse
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON object or default value
    """
    try:
        # Handle cases where text might be surrounded by markdown code blocks
        if text.startswith("```json") and text.endswith("```"):
            text = text[7:-3].strip()
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {} if default is None else default

def format_dates(date_str: str) -> str:
    """
    Format date strings consistently.
    
    Args:
        date_str: Date string to format
        
    Returns:
        Formatted date string
    """
    # Replace "to" with more professional dash
    date_str = date_str.replace(" to ", " — ")
    
    # Format date patterns
    date_str = re.sub(r'(\b\d{4})\s*-\s*(\b\d{4}|Present)', r'\1 — \2', date_str)
    
    return date_str

def format_list_as_bullet_string(items: List[str], bullet_char: str = "•") -> str:
    """
    Format a list as a string with bullet separators.
    
    Args:
        items: List of items
        bullet_char: Character to use as bullet
        
    Returns:
        String with items separated by bullets
    """
    if not items:
        return ""
    return f" {bullet_char} ".join(items)

def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory
    """
    import os
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        
def clean_text(text: str) -> str:
    """
    Clean and normalize text by removing extra whitespace and normalizing newlines.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Normalize newlines
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text

def extract_achievements(description: str) -> List[str]:
    """
    Attempt to extract achievements from a job description.
    
    Args:
        description: Job description text
        
    Returns:
        List of extracted achievements
    """
    achievements = []
    
    # Look for achievement indicators
    indicators = [
        "increased", "decreased", "improved", "reduced", "achieved", 
        "developed", "launched", "created", "led", "managed",
        "implemented", "executed", "generated", "delivered"
    ]
    
    # Split by sentences
    sentences = re.split(r'(?<=[.!?])\s+', description)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Check if sentence starts with an achievement indicator
        if any(sentence.lower().startswith(ind) for ind in indicators):
            achievements.append(sentence)
            continue
            
        # Check if sentence contains metrics (%, numbers, currency)
        if re.search(r'(\d+%|\$\d+|\d+\s*%)', sentence):
            achievements.append(sentence)
            
    return achievements