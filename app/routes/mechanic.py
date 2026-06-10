import requests
from fastapi import APIRouter

router = APIRouter()

# VULN: SSRF — fetches any URL supplied by user, no validation
@router.get("/mechanic/fetch")
def fetch_url(url: str):
    try:
        response = requests.get(url, timeout=5)
        return {"status": response.status_code, "body": response.text[:500]}
    except Exception as e:
        return {"error": str(e)}
