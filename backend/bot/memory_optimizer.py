"""
🧹 Memory Optimizer - Dell E7450 RAM Management

Implementa garbage collection agressivo e memory awareness.
Target: Manter uso do bot <500MB mesmo com sistema pressionado.
"""

import gc
import sys
from typing import Any, Callable
from functools import wraps
import psutil
from datetime import datetime


class MemoryOptimizer:
    """
    Gerenciador de memória otimizado para Dell E7450.

    CONTEXT: Sistema opera com ~11GB/12GB RAM usados (95%).
    Chrome consome 3.16GB, VS Code ~2.5GB.
    Bot precisa operar em <500MB para não causar thrashing.
    """

    # 🛡️ CONSTRAINTS: Dell E7450 (12GB RAM)
    SYSTEM_RAM_GB = 12
    SYSTEM_RAM_WARN = 0.90  # 10.8GB
    SYSTEM_RAM_CRITICAL = 0.95  # 11.4GB
    BOT_MAX_RAM_MB = 500  # Bot não deve exceder 500MB

    def __init__(self):
        self.process = psutil.Process()
        self.gc_count = 0
        self.memory_freed_mb = 0.0

    def get_memory_status(self) -> dict:
        """
        Retorna status atual de memória.

        Returns:
            Dict com métricas de RAM system e process
        """
        # System memory
        ram = psutil.virtual_memory()
        ram_gb = ram.used / (1024**3)
        ram_percent = ram.percent / 100

        # Process memory
        process_mb = self.process.memory_info().rss / (1024**2)

        return {
            "system_ram_gb": ram_gb,
            "system_ram_percent": ram_percent,
            "system_ram_available_gb": ram.available / (1024**3),
            "process_ram_mb": process_mb,
            "status": self._get_status_level(ram_percent, process_mb),
            "should_gc": ram_percent > self.SYSTEM_RAM_WARN
            or process_mb > self.BOT_MAX_RAM_MB * 0.8,
        }

    def _get_status_level(self, system_percent: float, process_mb: float) -> str:
        """Determina nível de criticidade."""
        if system_percent >= self.SYSTEM_RAM_CRITICAL:
            return "CRITICAL"
        elif system_percent >= self.SYSTEM_RAM_WARN:
            return "WARNING"
        elif process_mb > self.BOT_MAX_RAM_MB:
            return "BOT_OVER_LIMIT"
        else:
            return "OK"

    def force_gc(self, reason: str = "manual") -> dict:
        """
        Força garbage collection agressivo.

        Args:
            reason: Motivo da coleta (para logging)

        Returns:
            Dict com RAM liberada
        """
        before_mb = self.process.memory_info().rss / (1024**2)

        # Garbage collection triplo (0, 1, 2 generations)
        collected = gc.collect(0)
        collected += gc.collect(1)
        collected += gc.collect(2)

        after_mb = self.process.memory_info().rss / (1024**2)
        freed_mb = before_mb - after_mb

        self.gc_count += 1
        self.memory_freed_mb += freed_mb

        print(f"[GC] 🧹 Garbage collection ({reason}): {collected} objects | {freed_mb:+.2f}MB")

        return {
            "collected_objects": collected,
            "freed_mb": freed_mb,
            "ram_before_mb": before_mb,
            "ram_after_mb": after_mb,
        }

    def auto_gc_if_needed(self) -> bool:
        """
        Executa GC automaticamente se necessário.

        Returns:
            True se GC foi executado
        """
        status = self.get_memory_status()

        if status["should_gc"]:
            reason = f"{status['status']} - System: {status['system_ram_gb']:.2f}GB, Process: {status['process_ram_mb']:.1f}MB"
            self.force_gc(reason=reason)
            return True

        return False

    def check_and_warn(self) -> None:
        """Verifica memória e alerta se crítico."""
        status = self.get_memory_status()

        if status["status"] == "CRITICAL":
            print(
                f"[MEMORY] 🚨 CRÍTICO: Sistema em {status['system_ram_gb']:.2f}GB ({status['system_ram_percent']:.1%})"
            )
            print(f"[MEMORY] 💡 Fechar Chrome ou outros apps para liberar RAM")

        elif status["status"] == "WARNING":
            print(
                f"[MEMORY] ⚠️ Sistema em {status['system_ram_gb']:.2f}GB ({status['system_ram_percent']:.1%})"
            )

        elif status["status"] == "BOT_OVER_LIMIT":
            print(
                f"[MEMORY] ⚠️ Bot em {status['process_ram_mb']:.1f}MB (limite: {self.BOT_MAX_RAM_MB}MB)"
            )

    def get_stats(self) -> dict:
        """Retorna estatísticas acumuladas."""
        return {
            "gc_count": self.gc_count,
            "total_memory_freed_mb": self.memory_freed_mb,
            "avg_freed_per_gc_mb": self.memory_freed_mb / self.gc_count if self.gc_count > 0 else 0,
        }


# Global instance
_optimizer = MemoryOptimizer()


def memory_aware(threshold_mb: float = 400):
    """
    Decorator para funções que consomem muita memória.
    Executa GC antes e depois se necessário.

    Args:
        threshold_mb: Executar GC se processo > N MB

    Example:
        @memory_aware(threshold_mb=300)
        async def process_large_dataframe():
            df = pd.read_csv('huge.csv')
            # ... processing
            return result
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Check before
            status_before = _optimizer.get_memory_status()
            if status_before["process_ram_mb"] > threshold_mb:
                _optimizer.force_gc(reason=f"before {func.__name__}")

            # Execute function
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                # Always GC after heavy operations
                _optimizer.force_gc(reason=f"after {func.__name__}")

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Check before
            status_before = _optimizer.get_memory_status()
            if status_before["process_ram_mb"] > threshold_mb:
                _optimizer.force_gc(reason=f"before {func.__name__}")

            # Execute function
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Always GC after heavy operations
                _optimizer.force_gc(reason=f"after {func.__name__}")

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def get_optimizer() -> MemoryOptimizer:
    """Retorna instância global do optimizer."""
    return _optimizer


# 🧪 Example usage
if __name__ == "__main__":
    optimizer = get_optimizer()

    print("=== MEMORY STATUS ===")
    status = optimizer.get_memory_status()
    for key, value in status.items():
        print(f"{key}: {value}")

    print("\n=== FORCE GC ===")
    result = optimizer.force_gc(reason="test")
    print(f"Objects collected: {result['collected_objects']}")
    print(f"Memory freed: {result['freed_mb']:.2f}MB")

    print("\n=== STATS ===")
    stats = optimizer.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
