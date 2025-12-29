"""
Configuração de Rate Limiting para a API.

Protege contra abuso e garante disponibilidade.
Usa slowapi com diferentes limites por tipo de endpoint.
"""

import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from typing import Callable

# Configurações via environment
RATE_LIMIT_DEFAULT = os.environ.get('RATE_LIMIT_DEFAULT', '100/minute')
RATE_LIMIT_CONTROL = os.environ.get('RATE_LIMIT_CONTROL', '10/minute')  # start/stop/sync
RATE_LIMIT_CONFIG = os.environ.get('RATE_LIMIT_CONFIG', '20/minute')    # save config
RATE_LIMIT_STREAM = os.environ.get('RATE_LIMIT_STREAM', '5/minute')     # SSE streams


def get_client_ip(request: Request) -> str:
    """
    Obtém IP do cliente, considerando proxies.
    """
    # Tenta X-Forwarded-For primeiro (para proxies/load balancers)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Pega o primeiro IP (cliente original)
        return forwarded.split(",")[0].strip()
    
    # Tenta X-Real-IP (comum em nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback para IP direto
    return get_remote_address(request)


# Criar limiter com função de identificação customizada
limiter = Limiter(key_func=get_client_ip)


def setup_rate_limiting(app) -> None:
    """
    Configura rate limiting na aplicação FastAPI.
    
    Args:
        app: Instância FastAPI
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def limit_default(func: Callable) -> Callable:
    """Decorator para limite padrão (100/min)."""
    return limiter.limit(RATE_LIMIT_DEFAULT)(func)


def limit_control(func: Callable) -> Callable:
    """Decorator para endpoints de controle do bot (10/min)."""
    return limiter.limit(RATE_LIMIT_CONTROL)(func)


def limit_config(func: Callable) -> Callable:
    """Decorator para salvamento de config (20/min)."""
    return limiter.limit(RATE_LIMIT_CONFIG)(func)


def limit_stream(func: Callable) -> Callable:
    """Decorator para streams SSE (5/min)."""
    return limiter.limit(RATE_LIMIT_STREAM)(func)
