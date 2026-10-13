from fastapi import Request
from slowapi import Limiter

def get_real_ip(request: Request) -> str:
    return request.headers.get("CF-Connecting-IP", request.client.host if request.client else "127.0.0.1")

limiter = Limiter(key_func=get_real_ip)
