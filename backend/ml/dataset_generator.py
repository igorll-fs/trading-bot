"""
Gerador de Dataset Rotulado para ML
Simula trades e rotula como WIN/LOSS para treinamento
"""

import os
import sys
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv

# Adicionar path do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.strategy import TradingStrategy
from bot.risk_manager import RiskManager

load_dotenv()

logger = logging.getLogger(__name__)


class DatasetGenerator:
    """Gera dataset rotulado para treinamento de ML"""

    def __init__(
        self,
        stop_loss_pct: float = 1.5,
        take_profit_pct: float = 4.0,
        fee_pct: float = 0.1,       # Fee da Binance
        slippage_pct: float = 0.05,  # Slippage estimado
        min_signal_strength: int = 40
    ):
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.fee_pct = fee_pct
        self.slippage_pct = slippage_pct
        self.min_signal_strength = min_signal_strength

        # Custo total por trade (entrada + saida)
        self.total_cost_pct = (fee_pct + slippage_pct) * 2

        # MongoDB
        mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.getenv('DB_NAME', 'trading_bot')
        self.mongo_client = MongoClient(mongo_url)
        self.db = self.mongo_client[db_name]

        # Strategy para calcular indicadores
        self.strategy = TradingStrategy(None, min_signal_strength=min_signal_strength)

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula todos os indicadores tecnicos"""
        return self.strategy.calculate_indicators(df)

    def _generate_simple_signal(self, row: pd.Series, df: pd.DataFrame, idx: int) -> Dict:
        """
        Gera sinais simples baseados em indicadores
        Mais permissivo que a estrategia original para gerar mais amostras
        """
        signal = {'signal': 'NONE', 'strength': 0}

        # Verificar se indicadores existem
        rsi = row.get('rsi', 50)
        macd = row.get('macd', 0)
        macd_signal = row.get('macd_signal', 0)
        ema_fast = row.get('ema_fast', row['close'])
        ema_slow = row.get('ema_slow', row['close'])
        close = row['close']

        if pd.isna(rsi) or pd.isna(macd):
            return signal

        # Calcular forca do sinal
        strength = 50

        # === SINAL DE COMPRA ===
        buy_signals = 0

        # RSI abaixo de 40 (oversold)
        if rsi < 40:
            buy_signals += 1
            strength += 10

        # MACD cruzando para cima
        if macd > macd_signal:
            buy_signals += 1
            strength += 10

        # Preco acima da EMA rapida
        if close > ema_fast:
            buy_signals += 1
            strength += 5

        # EMA rapida acima da lenta (tendencia de alta)
        if ema_fast > ema_slow:
            buy_signals += 1
            strength += 5

        # === SINAL DE VENDA ===
        sell_signals = 0

        # RSI acima de 60 (overbought)
        if rsi > 60:
            sell_signals += 1

        # MACD cruzando para baixo
        if macd < macd_signal:
            sell_signals += 1

        # Preco abaixo da EMA rapida
        if close < ema_fast:
            sell_signals += 1

        # EMA rapida abaixo da lenta (tendencia de baixa)
        if ema_fast < ema_slow:
            sell_signals += 1

        # Decidir sinal (precisa de pelo menos 2 confirmacoes)
        if buy_signals >= 2 and buy_signals > sell_signals:
            signal = {'signal': 'BUY', 'strength': min(100, strength)}
        elif sell_signals >= 2 and sell_signals > buy_signals:
            signal = {'signal': 'SELL', 'strength': min(100, 50 + sell_signals * 10)}

        return signal

    def _extract_features(self, row: pd.Series, df: pd.DataFrame, idx: int) -> Dict:
        """Extrai features de uma vela para ML"""
        features = {}

        # === FEATURES DE PRECO ===
        features['close'] = row['close']
        features['open'] = row['open']
        features['high'] = row['high']
        features['low'] = row['low']
        features['volume'] = row['volume']

        # Candle body
        features['body_pct'] = abs(row['close'] - row['open']) / row['open'] * 100
        features['upper_wick_pct'] = (row['high'] - max(row['open'], row['close'])) / row['close'] * 100
        features['lower_wick_pct'] = (min(row['open'], row['close']) - row['low']) / row['close'] * 100
        features['is_bullish'] = 1 if row['close'] > row['open'] else 0

        # === FEATURES DE INDICADORES ===
        # EMAs
        for col in ['ema_fast', 'ema_slow', 'ema_50', 'ema_200']:
            if col in row and pd.notna(row[col]):
                features[col] = row[col]
                features[f'{col}_dist'] = (row['close'] - row[col]) / row[col] * 100

        # RSI
        if 'rsi' in row and pd.notna(row['rsi']):
            features['rsi'] = row['rsi']
            features['rsi_oversold'] = 1 if row['rsi'] < 30 else 0
            features['rsi_overbought'] = 1 if row['rsi'] > 70 else 0

        # MACD
        for col in ['macd', 'macd_signal', 'macd_hist']:
            if col in row and pd.notna(row[col]):
                features[col] = row[col]

        if 'macd' in row and 'macd_signal' in row:
            if pd.notna(row['macd']) and pd.notna(row['macd_signal']):
                features['macd_cross_up'] = 1 if row['macd'] > row['macd_signal'] else 0

        # Bollinger Bands
        for col in ['bb_upper', 'bb_middle', 'bb_lower']:
            if col in row and pd.notna(row[col]):
                features[col] = row[col]

        if 'bb_upper' in row and 'bb_lower' in row:
            if pd.notna(row['bb_upper']) and pd.notna(row['bb_lower']):
                bb_width = row['bb_upper'] - row['bb_lower']
                features['bb_width_pct'] = bb_width / row['close'] * 100
                features['bb_position'] = (row['close'] - row['bb_lower']) / bb_width if bb_width > 0 else 0.5

        # ATR
        if 'atr' in row and pd.notna(row['atr']):
            features['atr'] = row['atr']
            features['atr_pct'] = row['atr'] / row['close'] * 100

        # VWAP
        if 'vwap' in row and pd.notna(row['vwap']):
            features['vwap'] = row['vwap']
            features['vwap_dist'] = (row['close'] - row['vwap']) / row['vwap'] * 100

        # OBV (normalizado)
        if 'obv' in row and pd.notna(row['obv']):
            features['obv'] = row['obv']

        # === FEATURES TEMPORAIS ===
        if 'timestamp' in row:
            ts = row['timestamp']
            if hasattr(ts, 'hour'):
                features['hour'] = ts.hour
                features['day_of_week'] = ts.dayofweek
                features['is_weekend'] = 1 if ts.dayofweek >= 5 else 0

        # === FEATURES DE MOMENTUM ===
        if idx >= 5:
            # Retorno ultimas N velas
            for n in [1, 3, 5]:
                if idx >= n:
                    past_close = df.iloc[idx - n]['close']
                    features[f'return_{n}'] = (row['close'] - past_close) / past_close * 100

            # Volume relativo
            vol_mean = df.iloc[max(0, idx-20):idx]['volume'].mean()
            if vol_mean > 0:
                features['volume_ratio'] = row['volume'] / vol_mean

        return features

    def _simulate_trade_outcome(
        self,
        df: pd.DataFrame,
        entry_idx: int,
        side: str,
        entry_price: float
    ) -> Tuple[str, float, int]:
        """
        Simula o resultado de um trade
        Retorna: (resultado, pnl_pct, duracao_candles)
        """
        # Calcular niveis com custos
        if side == 'BUY':
            stop_loss = entry_price * (1 - self.stop_loss_pct / 100)
            take_profit = entry_price * (1 + self.take_profit_pct / 100)
        else:
            stop_loss = entry_price * (1 + self.stop_loss_pct / 100)
            take_profit = entry_price * (1 - self.take_profit_pct / 100)

        # Simular velas futuras
        max_candles = min(100, len(df) - entry_idx - 1)

        for i in range(1, max_candles + 1):
            candle = df.iloc[entry_idx + i]
            high = candle['high']
            low = candle['low']

            if side == 'BUY':
                # Stop loss atingido?
                if low <= stop_loss:
                    pnl = -self.stop_loss_pct - self.total_cost_pct
                    return 'STOP_LOSS', pnl, i

                # Take profit atingido?
                if high >= take_profit:
                    pnl = self.take_profit_pct - self.total_cost_pct
                    return 'TAKE_PROFIT', pnl, i
            else:
                # Stop loss atingido?
                if high >= stop_loss:
                    pnl = -self.stop_loss_pct - self.total_cost_pct
                    return 'STOP_LOSS', pnl, i

                # Take profit atingido?
                if low <= take_profit:
                    pnl = self.take_profit_pct - self.total_cost_pct
                    return 'TAKE_PROFIT', pnl, i

        # Timeout - fechar no ultimo preco
        last_price = df.iloc[min(entry_idx + max_candles, len(df) - 1)]['close']
        if side == 'BUY':
            pnl = (last_price - entry_price) / entry_price * 100 - self.total_cost_pct
        else:
            pnl = (entry_price - last_price) / entry_price * 100 - self.total_cost_pct

        return 'TIMEOUT', pnl, max_candles

    def generate_from_ohlcv(
        self,
        symbol: str,
        timeframe: str = '15m',
        start_date: datetime = None,
        end_date: datetime = None
    ) -> pd.DataFrame:
        """Gera dataset a partir de dados OHLCV salvos"""

        # Buscar dados
        query = {'symbol': symbol, 'timeframe': timeframe}

        if start_date:
            query['timestamp'] = {'$gte': start_date}
        if end_date:
            if 'timestamp' in query:
                query['timestamp']['$lte'] = end_date
            else:
                query['timestamp'] = {'$lte': end_date}

        cursor = self.db.ohlcv_data.find(query).sort('timestamp', 1)
        data = list(cursor)

        if len(data) < 200:
            logger.warning(f"[Generator] Dados insuficientes para {symbol}: {len(data)} velas")
            return pd.DataFrame()

        # Converter para DataFrame
        df = pd.DataFrame(data)
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

        logger.info(f"[Generator] Processando {symbol} {timeframe}: {len(df)} velas")

        # Calcular indicadores
        df = self._calculate_indicators(df)

        # Encontrar primeiro indice valido (apos indicadores)
        start_idx = 200  # Pular warmup dos indicadores

        samples = []

        for idx in range(start_idx, len(df) - 100):  # Deixar espaco para simulacao
            row = df.iloc[idx]

            # Gerar sinal baseado em indicadores simples (nao depende da estrategia)
            signal = self._generate_simple_signal(row, df, idx)

            if signal['signal'] not in ['BUY', 'SELL']:
                continue

            # Extrair features
            features = self._extract_features(row, df, idx)
            features['symbol'] = symbol
            features['timeframe'] = timeframe
            features['signal'] = signal['signal']
            features['signal_strength'] = signal.get('strength', 50)

            # Simular resultado
            outcome, pnl, duration = self._simulate_trade_outcome(
                df, idx, signal['signal'], row['close']
            )

            # Labels
            features['outcome'] = outcome
            features['pnl_pct'] = pnl
            features['duration_candles'] = duration
            features['is_win'] = 1 if pnl > 0 else 0
            features['is_good_trade'] = 1 if pnl > 1.0 else 0  # Trade que vale a pena

            samples.append(features)

        logger.info(f"[Generator] {symbol}: {len(samples)} amostras geradas")

        return pd.DataFrame(samples)

    def generate_full_dataset(
        self,
        symbols: List[str] = None,
        timeframe: str = '15m'
    ) -> pd.DataFrame:
        """Gera dataset completo para todos os simbolos"""

        if symbols is None:
            # Pegar simbolos disponiveis no banco
            symbols = self.db.ohlcv_data.distinct('symbol')

        logger.info(f"[Generator] Gerando dataset para {len(symbols)} simbolos...")

        all_samples = []

        for symbol in symbols:
            try:
                df = self.generate_from_ohlcv(symbol, timeframe)
                if not df.empty:
                    all_samples.append(df)
            except Exception as e:
                logger.error(f"[Generator] Erro em {symbol}: {e}")

        if not all_samples:
            logger.error("[Generator] Nenhuma amostra gerada!")
            return pd.DataFrame()

        dataset = pd.concat(all_samples, ignore_index=True)

        # Estatisticas
        wins = (dataset['is_win'] == 1).sum()
        losses = (dataset['is_win'] == 0).sum()
        win_rate = wins / len(dataset) * 100

        logger.info(f"[Generator] Dataset completo: {len(dataset)} amostras")
        logger.info(f"[Generator] Win Rate: {win_rate:.1f}% ({wins} wins / {losses} losses)")
        logger.info(f"[Generator] PnL medio: {dataset['pnl_pct'].mean():.2f}%")

        return dataset

    def save_dataset(self, dataset: pd.DataFrame, name: str = 'training_data'):
        """Salva dataset no MongoDB"""
        if dataset.empty:
            return

        # Converter para documentos
        records = dataset.to_dict('records')

        # Adicionar metadata
        for r in records:
            r['generated_at'] = datetime.now(timezone.utc)
            r['dataset_name'] = name

        # Salvar
        collection = self.db['ml_training_data']

        # Limpar dataset antigo com mesmo nome
        collection.delete_many({'dataset_name': name})

        # Inserir novo
        collection.insert_many(records)

        logger.info(f"[Generator] Dataset '{name}' salvo: {len(records)} amostras")

    def load_dataset(self, name: str = 'training_data') -> pd.DataFrame:
        """Carrega dataset do MongoDB"""
        cursor = self.db.ml_training_data.find({'dataset_name': name})
        data = list(cursor)

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # Remover campos do mongo
        df = df.drop(columns=['_id', 'generated_at', 'dataset_name'], errors='ignore')

        return df

    def close(self):
        self.mongo_client.close()


def run_generator():
    """CLI para gerar dataset"""
    import argparse

    parser = argparse.ArgumentParser(description='Gerar dataset para ML')
    parser.add_argument('--symbols', nargs='+', help='Simbolos especificos')
    parser.add_argument('--timeframe', default='15m', help='Timeframe')
    parser.add_argument('--name', default='training_data', help='Nome do dataset')
    parser.add_argument('--stats', action='store_true', help='Apenas mostrar stats')

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    generator = DatasetGenerator()

    if args.stats:
        dataset = generator.load_dataset(args.name)
        if dataset.empty:
            print("Dataset vazio ou nao encontrado")
        else:
            print(f"\nDataset: {args.name}")
            print(f"Amostras: {len(dataset)}")
            print(f"Features: {len(dataset.columns)}")
            print(f"\nDistribuicao:")
            print(dataset['is_win'].value_counts())
            print(f"\nPnL medio: {dataset['pnl_pct'].mean():.2f}%")
    else:
        print("\n" + "=" * 60)
        print("GERACAO DE DATASET ML")
        print("=" * 60)

        dataset = generator.generate_full_dataset(
            symbols=args.symbols,
            timeframe=args.timeframe
        )

        if not dataset.empty:
            generator.save_dataset(dataset, args.name)

            print("\n" + "-" * 60)
            print("RESUMO:")
            print(f"  Amostras: {len(dataset)}")
            print(f"  Win Rate: {(dataset['is_win'].mean() * 100):.1f}%")
            print(f"  PnL medio: {dataset['pnl_pct'].mean():.2f}%")
            print(f"  Dataset salvo como: {args.name}")

    generator.close()


if __name__ == '__main__':
    run_generator()
