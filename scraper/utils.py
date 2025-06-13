import requests


def resolve_short_url(url):
    """
    Resolve a short URL to its final destination.
    Returns the resolved URL or the original URL if resolution fails.
    """
    if not url.startswith('https://t.co/'):
        return url
    
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        return response.url
    except Exception as e:
        print(f"Warning: Could not resolve short URL {url}: {e}")
        return url