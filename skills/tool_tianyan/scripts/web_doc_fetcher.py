import urllib.request
import urllib.error
import os
import argparse
import sys

def fetch_doc(url):
    if not url or not url.startswith(('http://', 'https://')):
        return "ERROR_INVALID_PROTOCOL: Only HTTP and HTTPS URLs are supported."
    host_part = url.split('://', 1)[1] if '://' in url else ''
    if not host_part or not host_part.strip():
        return "ERROR_INVALID_PROTOCOL: URL has no host component."
    MAX_RESPONSE_SIZE = 5 * 1024 * 1024
    MAX_REDIRECTS = 3
    proxy_url = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy") or os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or None
    if proxy_url:
        proxy_handler = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
    else:
        proxy_handler = urllib.request.ProxyHandler()
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
    opener = urllib.request.build_opener(proxy_handler, redirect_handler)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; TianYan-Agent/2.0)', 'Accept': 'text/html, application/json, text/plain, */*'})
    try:
        with opener.open(req, timeout=10) as response:
            data = response.read(MAX_RESPONSE_SIZE + 1)
            if len(data) > MAX_RESPONSE_SIZE:
                return "ERROR_RESPONSE_TOO_LARGE: Response exceeds %d bytes limit." % MAX_RESPONSE_SIZE
            return data.decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        return _classify_http_error(e)
    except urllib.error.URLError as e:
        reason = str(e.reason)
        if "Tunnel connection failed" in reason or "403" in reason:
            return "ERROR_NETWORK: %s (hint: check HTTP_PROXY/HTTPS_PROXY)" % reason
        return "ERROR_NETWORK: %s" % reason
    except Exception as e:
        return "ERROR_UNKNOWN: %s" % str(e)

def _classify_http_error(e):
    code = e.code
    headers = e.headers if hasattr(e, 'headers') else None
    if code == 401:
        return "ERROR_AUTH_REQUIRED: Server returned 401 Unauthorized. Trigger Anti-Auth Fallback (Plan C / Plan A)."
    if code == 403:
        www_auth = headers.get("WWW-Authenticate", "") if headers else ""
        server_header = headers.get("Server", "") if headers else ""
        if www_auth or "login" in server_header.lower():
            return "ERROR_AUTH_BLOCKED: 403 Forbidden with authentication indicators. Trigger Anti-Auth Fallback (Plan C / Plan A)."
        waf_indicators = ["cloudflare", "akamai", "incapsula", "sucuri", "waf"]
        if any(w in server_header.lower() for w in waf_indicators):
            return "ERROR_WAF_BLOCKED: 403 Forbidden, likely WAF or security filter. Trigger Anti-Auth Fallback (Plan C / Plan A)."
        return "ERROR_FORBIDDEN: 403 Forbidden. Cause may be authentication, WAF, IP restriction, or proxy interception. Trigger Anti-Auth Fallback (Plan C / Plan A)."
    if code == 404:
        return "ERROR_HTTP_404: Resource not found at the given URL."
    if code >= 500:
        return "ERROR_HTTP_%d: Server error. The remote service may be temporarily unavailable." % code
    return "ERROR_HTTP_%d: Failed to fetch documentation (HTTP %d)." % (code, code)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="The URL to fetch")
    args = parser.parse_args()
    print(fetch_doc(args.url))
