import urllib.request
import urllib.error
import argparse
import sys

def fetch_doc(url: str) -> str:
    """
    Attempts to fetch a web document.
    Returns the content or a standardized error code that triggers Agent fallbacks.
    """
    if not url.startswith(('http://', 'https://')):
        return "ERROR_INVALID_PROTOCOL: Only HTTP and HTTPS URLs are supported."

    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'TianYan-Agent-Fetcher/1.0'}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        if e.code in [401, 403]:
            return "ERROR_AUTH_BLOCKED: The document is behind an authentication wall or WAF. Trigger Anti-Auth Fallback (Plan C / Plan A)."
        return f"ERROR_HTTP_{e.code}: Failed to fetch documentation."
    except urllib.error.URLError as e:
        return f"ERROR_NETWORK: {e.reason}"
    except Exception as e:
        return f"ERROR_UNKNOWN: {str(e)}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="The URL to fetch")
    args = parser.parse_args()
    
    result = fetch_doc(args.url)
    print(result)
