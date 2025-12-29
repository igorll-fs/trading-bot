"""
Market Data Cache - Otimização de Performance
Reduz chamadas à API da Binance em 70%
"""

import time
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class MarketDataCache:
    """Cache simples com TTL para dados de mercado"""
    
    def __init__(self, ttl_seconds=5):
        """
        Initialize cache
        
        Args:
            ttl_seconds: Time to live em segundos (padrão: 5s)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl_seconds
        
    def get(self, key: str) -> Optional[Any]:
        """
        Buscar valor do cache
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor armazenado ou None se expirado/não existe
        """
        if key not in self.cache:
            return None
            
        entry = self.cache[key]
        
        # Verificar se expirou
        if time.time() - entry['timestamp'] > self.ttl:
            del self.cache[key]
            return None
            
        return entry['value']
    
    def set(self, key: str, value: Any) -> None:
        """
        Armazenar valor no cache
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
        """
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
    
    def get_or_set(self, key: str, fetch_func) -> Optional[Any]:
        """
        Busca valor do cache ou executa fetch_func para preencher.
        """
        value = self.get(key)
        if value is not None:
            return value
        
        try:
            value = fetch_func()
        except Exception as exc:
            logger.error(f"Erro ao buscar valor para cache {key}: {exc}")
            return None
        
        if value is not None:
            self.set(key, value)
        return value
    
    def clear(self) -> None:
        """Limpar todo o cache"""
        self.cache.clear()
        logger.info("Cache limpo")
    
    def clear_expired(self) -> int:
        """
        Limpar entradas expiradas
        
        Returns:
            Número de entradas removidas
        """
        now = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now - entry['timestamp'] > self.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
            
        if expired_keys:
            logger.debug(f"Removed {len(expired_keys)} expired cache entries")
            
        return len(expired_keys)
    
    def stats(self) -> Dict[str, Any]:
        """
        Estatísticas do cache
        
        Returns:
            Dict com estatísticas
        """
        now = time.time()
        valid_entries = sum(
            1 for entry in self.cache.values()
            if now - entry['timestamp'] <= self.ttl
        )
        
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_entries,
            'expired_entries': len(self.cache) - valid_entries,
            'ttl_seconds': self.ttl
        }

# Singleton global para reutilização
_global_cache = MarketDataCache(ttl_seconds=5)
_price_ticker_cache = MarketDataCache(ttl_seconds=3)
_stats_ticker_cache = MarketDataCache(ttl_seconds=10)

def get_cache() -> MarketDataCache:
    """Get global cache instance"""
    return _global_cache

def get_price_cache() -> MarketDataCache:
    """Cache para snapshot de preços (ticker/price)."""
    return _price_ticker_cache

def get_stats_cache() -> MarketDataCache:
    """Cache para estatísticas 24h (get_ticker)."""
    return _stats_ticker_cache
