"""
Globaler Image Cache Manager für alle Analysen.
Verhindert zirkuläre Imports und bietet zentrale Cache-Verwaltung.
"""

_cache = {}

def get_cache():
    """Rückgabe des globalen Image Cache Dictionary"""
    return _cache

def clear_cache():
    """Leeren des Image Cache"""
    global _cache
    _cache = {}
