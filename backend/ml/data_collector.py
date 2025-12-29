"""
Coletor de Dados OHLCV Historicos
Baixa dados da Binance e salva para treinamento ML
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import pandas as pd
from binance.client import Client
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Simbolos para coleta
DEFAULT_SYMBOLS = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
    'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'DOTUSDT', 'MATICUSDT',
    'LINKUSDT', 'ATOMUSDT', 'LTCUSDT', 'UNIUSDT', 'NEARUSDT'
]

# Timeframes para coleta
TIMEFRAMES = ['15m', '1h', '4h']


class OHLCVCollector:
    """Coleta e armazena dados OHLCV da Binance"""

    def __init__(
        self,
        symbols: List[str] = None,
        timeframes: List[str] = None,
        days_back: int = 14,
        use_testnet: bool = None
    ):
        self.symbols = symbols or DEFAULT_SYMBOLS
        self.timeframes = timeframes or TIMEFRAMES
        self.days_back = days_back

        # Detectar modo testnet
        if use_testnet is None:
            use_testnet = os.getenv('TESTNET_MODE', 'true').lower() == 'true'
        self.use_testnet = use_testnet

        # Inicializar cliente Binance
        api_key = os.getenv('BINANCE_API_KEY', '')
        api_secret = os.getenv('BINANCE_API_SECRET', '')

        if use_testnet:
            self.client = Client(api_key, api_secret, testnet=True)
            logger.info("[Collector] Usando Binance TESTNET")
        else:
            self.client = Client(api_key, api_secret)
            logger.info("[Collector] Usando Binance MAINNET")

        # MongoDB
        mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.getenv('DB_NAME', 'trading_bot')
        self.mongo_client = MongoClient(mongo_url)
        self.db = self.mongo_client[db_name]

        # Colecao para dados OHLCV
        self.ohlcv_collection = self.db['ohlcv_data']

        # Criar indice para consultas rapidas
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Cria indices necessarios"""
        try:
            self.ohlcv_collection.create_index([
                ('symbol', 1),
                ('timeframe', 1),
                ('timestamp', 1)
            ], unique=True)

            self.ohlcv_collection.create_index([('timestamp', -1)])
            self.ohlcv_collection.create_index([('symbol', 1)])

            logger.info("[Collector] Indices criados/verificados")
        except Exception as e:
            logger.warning(f"[Collector] Erro ao criar indices: {e}")

    def fetch_klines(
        self,
        symbol: str,
        interval: str,
        start_time: datetime,
        end_time: datetime
    ) -> pd.DataFrame:
        """Baixa klines da Binance"""
        try:
            start_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
            end_str = end_time.strftime('%Y-%m-%d %H:%M:%S')

            klines = self.client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_str,
                end_str=end_str
            )

            if not klines:
                return pd.DataFrame()

            columns = [
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ]

            df = pd.DataFrame(klines, columns=columns)

            # Converter tipos
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'quote_volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            df['trades'] = pd.to_numeric(df['trades'], errors='coerce').astype(int)

            # Limpar
            df = df.dropna(subset=['close', 'high', 'low', 'volume'])
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'quote_volume', 'trades']]

            return df

        except Exception as e:
            logger.error(f"[Collector] Erro ao baixar {symbol} {interval}: {e}")
            return pd.DataFrame()

    def save_to_mongo(self, df: pd.DataFrame, symbol: str, timeframe: str) -> int:
        """Salva dados no MongoDB"""
        if df.empty:
            return 0

        documents = []
        for _, row in df.iterrows():
            doc = {
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': row['timestamp'].to_pydatetime(),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume']),
                'quote_volume': float(row['quote_volume']),
                'trades': int(row['trades']),
                'collected_at': datetime.now(timezone.utc)
            }
            documents.append(doc)

        # Upsert para evitar duplicatas
        saved = 0
        for doc in documents:
            try:
                self.ohlcv_collection.update_one(
                    {
                        'symbol': doc['symbol'],
                        'timeframe': doc['timeframe'],
                        'timestamp': doc['timestamp']
                    },
                    {'$set': doc},
                    upsert=True
                )
                saved += 1
            except Exception as e:
                logger.debug(f"[Collector] Erro ao salvar documento: {e}")

        return saved

    def collect_symbol(self, symbol: str) -> Dict:
        """Coleta todos os timeframes de um simbolo"""
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(days=self.days_back)

        result = {
            'symbol': symbol,
            'timeframes': {},
            'total_candles': 0
        }

        for tf in self.timeframes:
            logger.info(f"[Collector] Baixando {symbol} {tf}...")

            df = self.fetch_klines(symbol, tf, start_time, now)

            if not df.empty:
                saved = self.save_to_mongo(df, symbol, tf)
                result['timeframes'][tf] = {
                    'candles': len(df),
                    'saved': saved,
                    'start': df['timestamp'].min().isoformat(),
                    'end': df['timestamp'].max().isoformat()
                }
                result['total_candles'] += len(df)

                logger.info(f"[Collector] {symbol} {tf}: {len(df)} velas salvas")
            else:
                result['timeframes'][tf] = {'candles': 0, 'error': 'no data'}

        return result

    def collect_all(self) -> Dict:
        """Coleta dados de todos os simbolos"""
        logger.info(f"[Collector] Iniciando coleta de {len(self.symbols)} simbolos...")
        logger.info(f"[Collector] Timeframes: {self.timeframes}")
        logger.info(f"[Collector] Periodo: ultimos {self.days_back} dias")

        results = {
            'started_at': datetime.now(timezone.utc).isoformat(),
            'symbols': {},
            'total_candles': 0,
            'errors': []
        }

        for i, symbol in enumerate(self.symbols, 1):
            logger.info(f"[Collector] [{i}/{len(self.symbols)}] Processando {symbol}...")

            try:
                result = self.collect_symbol(symbol)
                results['symbols'][symbol] = result
                results['total_candles'] += result['total_candles']
            except Exception as e:
                logger.error(f"[Collector] Erro em {symbol}: {e}")
                results['errors'].append({'symbol': symbol, 'error': str(e)})

        results['finished_at'] = datetime.now(timezone.utc).isoformat()

        # Resumo
        logger.info(f"[Collector] Coleta concluida!")
        logger.info(f"[Collector] Total: {results['total_candles']} velas de {len(self.symbols)} simbolos")

        return results

    def get_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> pd.DataFrame:
        """Recupera dados do MongoDB"""
        query = {
            'symbol': symbol,
            'timeframe': timeframe
        }

        if start_time:
            query['timestamp'] = {'$gte': start_time}
        if end_time:
            if 'timestamp' in query:
                query['timestamp']['$lte'] = end_time
            else:
                query['timestamp'] = {'$lte': end_time}

        cursor = self.ohlcv_collection.find(query).sort('timestamp', 1)
        data = list(cursor)

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'quote_volume', 'trades']]
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

        return df

    def get_stats(self) -> Dict:
        """Retorna estatisticas dos dados coletados"""
        pipeline = [
            {
                '$group': {
                    '_id': {'symbol': '$symbol', 'timeframe': '$timeframe'},
                    'count': {'$sum': 1},
                    'min_date': {'$min': '$timestamp'},
                    'max_date': {'$max': '$timestamp'}
                }
            },
            {'$sort': {'_id.symbol': 1, '_id.timeframe': 1}}
        ]

        results = list(self.ohlcv_collection.aggregate(pipeline))

        stats = {}
        for r in results:
            symbol = r['_id']['symbol']
            tf = r['_id']['timeframe']

            if symbol not in stats:
                stats[symbol] = {}

            stats[symbol][tf] = {
                'count': r['count'],
                'from': r['min_date'].isoformat() if r['min_date'] else None,
                'to': r['max_date'].isoformat() if r['max_date'] else None
            }

        return stats

    def close(self):
        """Fecha conexoes"""
        self.mongo_client.close()


def run_collection():
    """Funcao para rodar coleta via CLI"""
    import argparse

    parser = argparse.ArgumentParser(description='Coletar dados OHLCV da Binance')
    parser.add_argument('--days', type=int, default=14, help='Dias de historico')
    parser.add_argument('--symbols', nargs='+', help='Simbolos especificos')
    parser.add_argument('--timeframes', nargs='+', help='Timeframes especificos')
    parser.add_argument('--stats', action='store_true', help='Mostrar apenas estatisticas')

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    collector = OHLCVCollector(
        symbols=args.symbols,
        timeframes=args.timeframes,
        days_back=args.days
    )

    if args.stats:
        print("\n" + "=" * 60)
        print("ESTATISTICAS DOS DADOS COLETADOS")
        print("=" * 60)

        stats = collector.get_stats()
        for symbol, timeframes in stats.items():
            print(f"\n{symbol}:")
            for tf, data in timeframes.items():
                print(f"  {tf}: {data['count']} velas ({data['from'][:10]} a {data['to'][:10]})")
    else:
        print("\n" + "=" * 60)
        print("COLETA DE DADOS OHLCV")
        print("=" * 60)

        results = collector.collect_all()

        print("\n" + "-" * 60)
        print("RESUMO:")
        print(f"  Total de velas: {results['total_candles']}")
        print(f"  Simbolos processados: {len(results['symbols'])}")
        if results['errors']:
            print(f"  Erros: {len(results['errors'])}")

    collector.close()


if __name__ == '__main__':
    run_collection()
