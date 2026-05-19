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

    MAX_RESPONSE_SIZE = 5 * 1024 * 1024  # 5 MB

    MAX_REDIRECTS = 3

    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'TianYan-Agent-Fetcher/1.0'}
    )
    # Limit redirects and reject non-HTTP/HTTPS protocols on redirect
    redirect_handler = urllib.request.HTTPRedirectHandler()
    original_redirect = redirect_handler.redirect_request

    def _limited_redirect(self, req, fp, code, msg, headers, newurl):
        if not newurl.startswith(('http://', 'https://')):
            raise urllib.error.HTTPError(newurl, code, "Redirect to non-HTTP protocol blocked", headers, fp)
        if not hasattr(req, '_redirect_count'):
            req._redirect_count = 0
        req._redirect_count += 1
        if req._redirect_count > MAX_REDIRECTS:
            raise urllib.error.HTTPError(newurl, code, "Too many redirects", headers, fp)
        return original_redirect(req, fp, code, msg, headers, newurl)

    redirect_handler.redirect_request = _limited_redirect
    opener = urllib.request.build_opener(redirect_handler)

    try:
        with opener.open(req, timeout=10) as response:
            data = response.read(MAX_RESPONSE_SIZE + 1)
            if len(data) > MAX_RESPONSE_SIZE:
                return f"ERROR_RESPONSE_TOO_LARGE: Response exceeds {MAX_RESPONSE_SIZE} bytes limit."
            return data.decode('utf-8')
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
