"""Testa a conexão com Binance usando as credenciais salvas no MongoDB."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient
from binance.client import Client
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / '.env')


async def _fetch_bot_config(db):
    return await db.configs.find_one({'type': 'bot_config'})


async def test_binance_connection() -> None:
    """Valida se conseguimos conectar ao Mongo e autenticar na Binance."""

    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'trading_bot')

    print('=' * 60)
    print('TESTE: CONEXAO BINANCE/SPOT')
    print('=' * 60)
    print(f"Mongo URL........: {mongo_url}")
    print(f"Database.........: {db_name}\n")

    client = AsyncIOMotorClient(mongo_url)
    try:
        db = client[db_name]
        config = await _fetch_bot_config(db)

        if not config:
            print('[ALERTA] Nenhuma configuração encontrada em configs.bot_config')
            return

        api_key = (config.get('binance_api_key') or '').strip()
        api_secret = (config.get('binance_api_secret') or '').strip()
        testnet = bool(config.get('binance_testnet', True))

        print('Config encontrada:')
        print(f"  - API Key.......: {api_key[:10] + '...' if api_key else '<vazio>'}")
        print(f"  - Testnet.......: {testnet}\n")

        if not api_key or not api_secret:
            print('[ERRO] API Key/Secret não configurados no banco.')
            return

        print('Conectando à Binance...')
        client_kwargs = dict(testnet=testnet)
        binance_client = Client(api_key, api_secret, **client_kwargs)
        if testnet:
            binance_client.API_URL = 'https://testnet.binance.vision/api'

        binance_client.ping()
        print('  - Ping OK')

        server_time = binance_client.get_server_time()
        import time
        local_time = int(time.time() * 1000)
        time_diff = server_time['serverTime'] - local_time
        binance_client.timestamp_offset = time_diff
        print(f"  - Offset de timestamp aplicado: {time_diff} ms")

        account = binance_client.get_account(recvWindow=10_000)
        usdt_balance = next((b for b in account['balances'] if b['asset'] == 'USDT'), None)
        if usdt_balance:
            print(
                f"  - Saldo USDT....: free={float(usdt_balance['free']):.2f} "
                f"| locked={float(usdt_balance['locked']):.2f}"
            )
        else:
            print('  - Saldo USDT não encontrado (conta vazia?)')

        print('\n[OK] Conexão com Binance concluída com sucesso!')

    except Exception as exc:  # pragma: no cover - comando manual
        print('\n[ERRO] Falha ao validar a conexão:')
        print(f'  Tipo: {type(exc).__name__}')
        print(f'  Mensagem: {exc}')
    finally:
        client.close()


if __name__ == '__main__':
    asyncio.run(test_binance_connection())

