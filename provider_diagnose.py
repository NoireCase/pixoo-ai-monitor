"""Check configured providers without printing credentials or account values."""
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from providers.sources import fetch, secret, URLS

for provider in ('go', 'cx', 'ds'):
    if provider != 'cx':
        key=secret(provider)
        print(f'{provider}: credential configured={bool(key)}', flush=True)
        if key:
            print(f'{provider}: credential has whitespace={any(c.isspace() for c in key)}, non-ASCII={not key.isascii()}, contains Bearer prefix={key.lower().startswith("bearer ")}',flush=True)
            print(f'{provider}: credential length >= 20={len(key)>=20}, contains quote={any(c in key for c in (chr(34), chr(39)))}',flush=True)
    try:
        result=fetch(provider)
        print(f'{provider}:', [(r.status, r.window, r.unit) for r in result], flush=True)
    except HTTPError as exc:
        print(f'{provider}: HTTP {exc.code}', flush=True)
        print(f'{provider}: content-type={exc.headers.get("Content-Type", "unknown")} server={exc.headers.get("Server", "unknown")}', flush=True)
        body=exc.read(32768).decode('utf-8','replace')
        print(f'{provider}: response bytes={len(body)}',flush=True)
        import json
        try:
            data=json.loads(body)
            error=data.get('error',data) if isinstance(data,dict) else {}
            if isinstance(error,dict):
                print(f'{provider}: error keys={sorted(error.keys())}; code={error.get("code", "unavailable")}; type={error.get("type", "unavailable")}',flush=True)
        except (ValueError,TypeError):
            print(f'{provider}: non-JSON response',flush=True)
    except URLError as exc:
        print(f'{provider}: network error ({type(exc.reason).__name__})', flush=True)
    except Exception as exc:
        print(f'{provider}: {type(exc).__name__}', flush=True)
    if provider in URLS:
        try:
            with urlopen(Request(URLS[provider]),timeout=10) as response:
                print(f'{provider}: unauthenticated HTTP {response.status}',flush=True)
        except HTTPError as exc:
            print(f'{provider}: unauthenticated HTTP {exc.code}',flush=True)
        except URLError as exc:
            print(f'{provider}: unauthenticated network error ({type(exc.reason).__name__})',flush=True)
