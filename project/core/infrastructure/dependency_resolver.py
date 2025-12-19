"""
Dependency Resolver Module

This module provides a smart mechanism to resolve Python import names to their
corresponding PyPI package names. It uses a hybrid approach:
1.  **Static Mapping:** Checks a hardcoded dictionary for common mismatches (e.g., PIL -> Pillow).
2.  **Standard Library Check:** Verifies if the import is part of the Python Standard Library (3.9+).
3.  **Tavily Search:** If not found, queries the web (via Tavily) to find the package name.
"""
import os
import json
import re
import sys
import httpx
from typing import Optional, Dict
from dotenv import load_dotenv

# Load Tavily Key
load_dotenv(".env.tavily")

# Known mappings to avoid unnecessary API calls
KNOWN_PACKAGE_MAPPINGS = {
    "PIL": "Pillow",
    "sklearn": "scikit-learn",
    "cv2": "opencv-python",
    "yaml": "pyyaml",
    "bs4": "beautifulsoup4",
    "png": "pypng",
    "barcode": "python-barcode",
    "dotenv": "python-dotenv",
    "dateutil": "python-dateutil",
    "jwt": "PyJWT",
    "fitz": "pymupdf",
}

# Static list of stdlib modules for Python 3.9+ (Common baseline)
# We use this because sys.stdlib_module_names is only available in 3.10+
# and we want to be safe across versions.
STDLIB_MODULES = {
    'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio', 'asyncore', 'atexit',
    'audioop', 'base64', 'bdb', 'binascii', 'binhex', 'bisect', 'builtins', 'bz2', 'cProfile',
    'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd', 'code', 'codecs', 'codeop',
    'collections', 'colorsys', 'compileall', 'concurrent', 'configparser', 'contextlib',
    'contextvars', 'copy', 'copyreg', 'crypt', 'csv', 'ctypes', 'curses', 'dataclasses',
    'datetime', 'dbm', 'decimal', 'difflib', 'dis', 'distutils', 'doctest', 'email',
    'encodings', 'ensurepip', 'enum', 'errno', 'faulthandler', 'fcntl', 'filecmp', 'fileinput',
    'fnmatch', 'formatter', 'fractions', 'ftplib', 'functools', 'gc', 'getopt', 'getpass',
    'gettext', 'glob', 'graphlib', 'grp', 'gzip', 'hashlib', 'heapq', 'hmac', 'html', 'http',
    'imaplib', 'imghdr', 'imp', 'importlib', 'inspect', 'io', 'ipaddress', 'itertools',
    'json', 'keyword', 'lib2to3', 'linecache', 'locale', 'logging', 'lzma', 'mailbox',
    'mailcap', 'marshal', 'math', 'mimetypes', 'mmap', 'modulefinder', 'msilib', 'msvcrt',
    'multiprocessing', 'netrc', 'nis', 'nntplib', 'numbers', 'operator', 'optparse', 'os',
    'ossaudiodev', 'parser', 'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil',
    'platform', 'plistlib', 'poplib', 'posix', 'pprint', 'profile', 'pstats', 'pty', 'pwd',
    'py_compile', 'pyclbr', 'pydoc', 'queue', 'quopri', 'random', 're', 'readline', 'reprlib',
    'resource', 'rlcompleter', 'runpy', 'sched', 'secrets', 'select', 'selectors', 'shelve',
    'shlex', 'shutil', 'signal', 'site', 'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver',
    'spwd', 'sqlite3', 'ssl', 'stat', 'statistics', 'string', 'stringprep', 'struct',
    'subprocess', 'sunau', 'symbol', 'symtable', 'sys', 'sysconfig', 'syslog', 'tabnanny',
    'tarfile', 'telnetlib', 'tempfile', 'termios', 'textwrap', 'threading', 'time', 'timeit',
    'tkinter', 'token', 'tokenize', 'trace', 'traceback', 'tracemalloc', 'tty', 'turtle',
    'turtledemo', 'types', 'typing', 'unicodedata', 'unittest', 'urllib', 'uu', 'uuid', 'venv',
    'warnings', 'wave', 'weakref', 'webbrowser', 'winreg', 'winsound', 'wsgiref', 'xdrlib',
    'xml', 'xmlrpc', 'zipapp', 'zipfile', 'zipimport', 'zlib', 'zoneinfo'
}

class DependencyResolver:
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.cache: Dict[str, str] = KNOWN_PACKAGE_MAPPINGS.copy()

    def resolve(self, import_name: str) -> Optional[str]:
        """
        Resolves an import name (e.g., 'cv2') to a PyPI package name (e.g., 'opencv-python').
        Returns None if the import is part of the standard library.
        """
        # 0. Check Standard Library
        # Check against sys.stdlib_module_names if available (Python 3.10+)
        if sys.version_info >= (3, 10):
            if import_name in sys.stdlib_module_names:
                print(f"DependencyResolver: '{import_name}' is in standard library (sys check).")
                return None

        # Fallback to static list for older python or robust check
        if import_name in STDLIB_MODULES:
            print(f"DependencyResolver: '{import_name}' is in standard library (static check).")
            return None

        # 1. Check Cache / Static Mapping
        if import_name in self.cache:
            return self.cache[import_name]

        # 2. Tavily Search
        print(f"DependencyResolver: resolving '{import_name}' via Tavily...")
        package_name = self._search_pypi_name(import_name)

        if package_name:
            print(f"DependencyResolver: Found '{import_name}' -> '{package_name}'")
            self.cache[import_name] = package_name
            return package_name

        # 3. Fallback: assume package name = import name
        print(f"DependencyResolver: Could not resolve '{import_name}'. Assuming package name is '{import_name}'.")
        return import_name

    def _search_pypi_name(self, import_name: str) -> Optional[str]:
        """
        Queries Tavily to find the PyPI package name for a given import.
        """
        if not self.api_key:
            print("DependencyResolver: No TAVILY_API_KEY found. Skipping search.")
            return None

        query = f"python pip package name for import {import_name}"

        try:
            response = httpx.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "search_depth": "basic",
                    "include_answer": True,
                    "topic": "general"
                },
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            # 1. Check AI Answer first
            answer = data.get("answer", "")
            # Look for patterns like "pip install <package>"
            pip_match = re.search(r"pip install ([\w\-]+)", answer)
            if pip_match:
                return pip_match.group(1)

            # 2. Check Search Results
            for result in data.get("results", []):
                title = result.get("title", "")
                url = result.get("url", "")
                content = result.get("content", "")

                # Check PyPI URLs
                if "pypi.org/project/" in url:
                    # extract package name from url
                    # https://pypi.org/project/opencv-python/ -> opencv-python
                    match = re.search(r"pypi\.org/project/([\w\-]+)", url)
                    if match:
                        return match.group(1)

                # Check content for "pip install"
                pip_match_content = re.search(r"pip install ([\w\-]+)", content)
                if pip_match_content:
                    return pip_match_content.group(1)

        except Exception as e:
            print(f"DependencyResolver: Search failed: {e}")
            return None

        return None

# Global instance
dependency_resolver = DependencyResolver()
