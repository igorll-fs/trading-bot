"""
Sistema de Logging Centralizado para o Trading Bot.

Fornece:
- RotatingFileHandler para evitar arquivos de log gigantes
- Formatação consistente em todos os módulos
- Logs separados por nível (info, error)
- Configuração via variáveis de ambiente
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Configurações via environment
LOG_DIR = Path(os.environ.get('LOG_DIR', Path(__file__).parent / 'logs'))
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10 * 1024 * 1024))  # 10MB default
LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))
LOG_FORMAT = os.environ.get(
    'LOG_FORMAT', 
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Garantir que diretório de logs existe
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Flag para evitar configuração duplicada
_logging_configured = False


def setup_logging(
    level: Optional[str] = None,
    log_dir: Optional[Path] = None,
    console_output: bool = True
) -> None:
    """
    Configura logging centralizado para toda a aplicação.
    
    Args:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Diretório para arquivos de log
        console_output: Se deve também logar no console
    """
    global _logging_configured
    
    if _logging_configured:
        return
    
    log_level = getattr(logging, level or LOG_LEVEL, logging.INFO)
    log_directory = log_dir or LOG_DIR
    log_directory.mkdir(parents=True, exist_ok=True)
    
    # Formatter padrão
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Limpar handlers existentes para evitar duplicação
    root_logger.handlers.clear()
    
    # Handler para arquivo principal (tudo)
    main_handler = RotatingFileHandler(
        log_directory / 'trading_bot.log',
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    main_handler.setLevel(log_level)
    main_handler.setFormatter(formatter)
    root_logger.addHandler(main_handler)
    
    # Handler para erros (apenas ERROR e CRITICAL)
    error_handler = RotatingFileHandler(
        log_directory / 'trading_bot_errors.log',
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # Handler para console (opcional)
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Reduzir verbosidade de bibliotecas externas
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('websockets').setLevel(logging.WARNING)
    logging.getLogger('binance').setLevel(logging.WARNING)
    
    _logging_configured = True
    
    logging.info(f"Logging configurado: level={LOG_LEVEL}, dir={log_directory}")


def get_logger(name: str) -> logging.Logger:
    """
    Obtém um logger configurado para o módulo especificado.
    
    Args:
        name: Nome do módulo (use __name__)
        
    Returns:
        Logger configurado
    """
    if not _logging_configured:
        setup_logging()
    
    return logging.getLogger(name)


def log_trade_event(
    symbol: str,
    event: str,
    details: Optional[dict] = None,
    level: str = 'INFO'
) -> None:
    """
    Loga evento de trade com formato padronizado.
    
    Args:
        symbol: Símbolo do par (ex: BTCUSDT)
        event: Tipo de evento (OPEN, CLOSE, SIGNAL, etc)
        details: Detalhes adicionais
        level: Nível de log
    """
    logger = get_logger('trading.events')
    log_func = getattr(logger, level.lower(), logger.info)
    
    msg = f"[{symbol}] {event}"
    if details:
        detail_str = ' | '.join(f"{k}={v}" for k, v in details.items())
        msg = f"{msg} | {detail_str}"
    
    log_func(msg)


def log_api_request(
    method: str,
    endpoint: str,
    status_code: int,
    duration_ms: float,
    error: Optional[str] = None
) -> None:
    """
    Loga requisição API com métricas.
    
    Args:
        method: Método HTTP
        endpoint: Endpoint chamado
        status_code: Código de resposta
        duration_ms: Duração em milissegundos
        error: Mensagem de erro se houver
    """
    logger = get_logger('api.requests')
    
    msg = f"{method} {endpoint} -> {status_code} ({duration_ms:.0f}ms)"
    
    if error:
        logger.error(f"{msg} | error={error}")
    elif status_code >= 400:
        logger.warning(msg)
    else:
        logger.info(msg)


def log_binance_call(
    operation: str,
    symbol: Optional[str] = None,
    success: bool = True,
    error: Optional[str] = None,
    retry_count: int = 0
) -> None:
    """
    Loga chamadas à API da Binance.
    
    Args:
        operation: Nome da operação
        symbol: Símbolo se aplicável
        success: Se a operação teve sucesso
        error: Mensagem de erro se houver
        retry_count: Número de tentativas
    """
    logger = get_logger('binance.api')
    
    parts = [operation]
    if symbol:
        parts.append(f"symbol={symbol}")
    if retry_count > 0:
        parts.append(f"retries={retry_count}")
    
    msg = ' | '.join(parts)
    
    if not success:
        logger.error(f"{msg} | FAILED | {error}")
    elif retry_count > 0:
        logger.warning(f"{msg} | SUCCESS (after retries)")
    else:
        logger.debug(f"{msg} | SUCCESS")
