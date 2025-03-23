"""
Fuzzy string matching and comparison utilities.
"""
from difflib import SequenceMatcher

def fuzzy_match(str1, str2, threshold=0.85):
    """
    Compare two strings using fuzzy matching
    Returns True if similarity ratio is above threshold
    """
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio() >= threshold

def get_similarity_ratio(str1, str2):
    """
    Get the similarity ratio between two strings
    """
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
