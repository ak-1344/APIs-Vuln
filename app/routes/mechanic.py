import requests
from fastapi import APIRouter, HTTPException
from urllib.parse import urlparse
import ipaddress

router = APIRouter()

ALLOWED_DOMAINS = ["api.partner.com", "maps.service.com", "trusted-mechanic.com"]

PRIVATE_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
]

def is_private_ip(hostname: str) -> bool:
    try:
        ip = ipaddress.ip_address(hostname)
        return any(ip in net for net in PRIVATE_RANGES)
    except ValueError:
        return False

def validate_url(url: str):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ["https", "http"]:
            raise HTTPException(400, "Only http/https allowed")
        hostname = parsed.hostname
        if not hostname:
            raise HTTPException(400, "Invalid URL")
        if is_private_ip(hostname):
            raise HTTPException(400, "Internal addresses not permitted")
        if hostname not in ALLOWED_DOMAINS:
            raise HTTPException(400, f"Domain not in allowlist")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(400, "Invalid URL")

# FIXED: URL validated before fetch
@router.get("/mechanic/fetch")
def fetch_url(url: str):
    validate_url(url)
    try:
        response = requests.get(url, timeout=5)
        return {"status": response.status_code, "body": response.text[:500]}
    except Exception as e:
        return {"error": "Request failed"}  # no internal details leaked
