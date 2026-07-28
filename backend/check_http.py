import sys
try:
    import httpx
    print("httpx is installed")
except ImportError:
    print("httpx NOT installed")

try:
    import aiohttp
    print("aiohttp is installed")
except ImportError:
    print("aiohttp NOT installed")
