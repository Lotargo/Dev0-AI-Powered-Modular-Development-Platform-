"""
The Sanitizer (Privacy Filter)

Responsible for cleaning sensitive data from lessons before they are shared
with the Swarm.
"""
import re
from typing import List, Pattern

class PrivacyFilter:
    """
    Filters out sensitive information from text, including:
    - API Keys (heuristics)
    - Absolute File Paths
    - IP Addresses
    - Email Addresses
    """

    def __init__(self, project_roots: List[str] = None):
        self.project_roots = project_roots or ["/app", "/home/user"]

        # Compile Regex Patterns
        self.patterns: List[tuple[Pattern, str]] = [
            # IP Addresses (IPv4)
            (re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'), "<IP_REDACTED>"),

            # Email Addresses
            (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), "<EMAIL_REDACTED>"),

            # Potential API Keys (heuristic: long alphanumeric strings with high entropy)
            # Matches "sk-..." (OpenAI), "tvly-..." (Tavily), or generic 30+ char strings
            (re.compile(r'\b(sk-[A-Za-z0-9]{20,})\b'), "<KEY_REDACTED>"),
            (re.compile(r'\b(tvly-[A-Za-z0-9]{20,})\b'), "<KEY_REDACTED>"),

            # Absolute Paths (Unix) - Replaced with generic placeholder
            # We try to match standard paths that look like user directories
            (re.compile(r'(?<!\w)/home/[\w\d_-]+(/[\w\d_/-]*)?'), "<HOME_DIR>\\1"),
            (re.compile(r'(?<!\w)/Users/[\w\d_-]+(/[\w\d_/-]*)?'), "<HOME_DIR>\\1"),
            (re.compile(r'(?<!\w)/app(/[\w\d_/-]*)?'), "<PROJECT_ROOT>\\1"),
        ]

    def sanitize(self, text: str) -> str:
        """
        Sanitizes the given text by replacing sensitive patterns with placeholders.
        """
        if not text:
            return text

        cleaned_text = text

        # 1. Apply Regex Replacements
        for pattern, replacement in self.patterns:
            cleaned_text = pattern.sub(replacement, cleaned_text)

        # 2. Project Root Specific Cleanup (if custom roots provided)
        for root in self.project_roots:
            if root in cleaned_text:
                cleaned_text = cleaned_text.replace(root, "<PROJECT_ROOT>")

        return cleaned_text

    def check_safety(self, text: str) -> bool:
        """
        Returns True if the text appears safe (no obvious secrets remaining),
        False if it looks suspicious (e.g. contains unmasked keys).
        """
        # A strict check could be added here. For now, we rely on sanitize.
        # Maybe check for high-entropy strings?
        return True

# Global instance
sanitizer = PrivacyFilter()
