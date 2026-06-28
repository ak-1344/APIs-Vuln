import atheris
import sys
import os

sys.path.insert(0, os.path.abspath('.'))

with atheris.instrument_imports():
    from app.routes.mechanic import fetch_url

def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)
    url_input = fdp.ConsumeUnicodeNoSurrogates(256)
    try:
        result = fetch_url(url=url_input)
        status = result.get('status')
        body = result.get('body', '')
        err = result.get('error', '')
        if status == 200:
            print(f"[SUCCESS] {repr(url_input[:80])} → {str(body)[:60]}", flush=True)
        elif err and 'connection refused' not in err.lower():
            print(f"[ERROR] {repr(url_input[:60])} → {err[:80]}", flush=True)
    except Exception as e:
        print(f"[CRASH] {repr(url_input[:60])} | {str(e)[:80]}", flush=True)

atheris.Setup(sys.argv, TestOneInput)
atheris.Fuzz()
