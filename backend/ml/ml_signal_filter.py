"""
Filtro de Sinais ML
Integra modelo treinado ao bot de trading
"""

import os
import sys
import logging
import pickle
from datetime import datetime, timezone
from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class MLSignalFilter:
    """Filtro de sinais usando modelo ML treinado"""

    def __init__(self, model_name: str = 'signal_filter', min_confidence: float = 0.5):
        self.model_name = model_name
        self.min_confidence = min_confidence

        # MongoDB
        mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.getenv('DB_NAME', 'trading_bot')
        self.mongo_client = MongoClient(mongo_url)
        self.db = self.mongo_client[db_name]

        # Modelo
        self.model = None
        self.scaler = None
        self.feature_columns = []
        self.metrics = {}
        self.loaded = False

        # Estatisticas de uso
        self.stats = {
            'total_signals': 0,
            'approved': 0,
            'rejected': 0,
            'errors': 0
        }

        # Tentar carregar modelo
        self._load_model()

    def _load_model(self) -> bool:
        """Carrega modelo do MongoDB"""
        try:
            doc = self.db.ml_models.find_one({'name': self.model_name})

            if not doc:
                logger.warning(f"[MLFilter] Modelo '{self.model_name}' nao encontrado. Filtro desabilitado.")
                return False

            self.model = pickle.loads(doc['model_bytes'])
            self.scaler = pickle.loads(doc['scaler_bytes'])
            self.feature_columns = doc['feature_columns']
            self.metrics = doc.get('metrics', {})
            self.loaded = True

            logger.info(f"[MLFilter] Modelo carregado: {self.model_name}")
            logger.info(f"[MLFilter] Accuracy: {self.metrics.get('accuracy', 0):.2%}")
            logger.info(f"[MLFilter] Features: {len(self.feature_columns)}")

            return True

        except Exception as e:
            logger.error(f"[MLFilter] Erro ao carregar modelo: {e}")
            return False

    def reload_model(self) -> bool:
        """Recarrega modelo (util apos retreino)"""
        self.loaded = False
        return self._load_model()

    def extract_features(self, opportunity: Dict, indicators: Dict) -> Dict:
        """Extrai features de uma oportunidade de trade"""
        features = {}

        # Indicadores
        features['rsi'] = indicators.get('rsi', 50)
        features['macd'] = indicators.get('macd', 0)
        features['macd_signal'] = indicators.get('macd_signal', 0)
        features['macd_hist'] = indicators.get('macd_hist', 0)

        # Distancias EMA
        close = indicators.get('close', 0)
        for ema_name in ['ema_fast', 'ema_slow', 'ema_50', 'ema_200']:
            ema_val = indicators.get(ema_name, close)
            if close > 0 and ema_val > 0:
                features[f'{ema_name}_dist'] = (close - ema_val) / ema_val * 100
            else:
                features[f'{ema_name}_dist'] = 0

        # Bollinger
        bb_upper = indicators.get('bb_upper', close)
        bb_lower = indicators.get('bb_lower', close)
        if bb_upper > bb_lower:
            bb_width = bb_upper - bb_lower
            features['bb_width_pct'] = bb_width / close * 100 if close > 0 else 0
            features['bb_position'] = (close - bb_lower) / bb_width
        else:
            features['bb_width_pct'] = 0
            features['bb_position'] = 0.5

        # ATR e VWAP
        atr = indicators.get('atr', 0)
        features['atr_pct'] = atr / close * 100 if close > 0 else 0

        vwap = indicators.get('vwap', close)
        features['vwap_dist'] = (close - vwap) / vwap * 100 if vwap > 0 else 0

        # Momentum (se disponivel)
        features['return_1'] = indicators.get('return_1', 0)
        features['return_3'] = indicators.get('return_3', 0)
        features['return_5'] = indicators.get('return_5', 0)
        features['volume_ratio'] = indicators.get('volume_ratio', 1)

        # Candle
        features['body_pct'] = indicators.get('body_pct', 0)
        features['upper_wick_pct'] = indicators.get('upper_wick_pct', 0)
        features['lower_wick_pct'] = indicators.get('lower_wick_pct', 0)
        features['is_bullish'] = indicators.get('is_bullish', 0)

        # Sinal
        features['signal_strength'] = opportunity.get('strength', opportunity.get('score', 50))

        # Temporal
        now = datetime.now(timezone.utc)
        features['hour'] = now.hour
        features['day_of_week'] = now.weekday()

        return features

    def should_take_trade(
        self,
        opportunity: Dict,
        indicators: Dict = None
    ) -> Tuple[bool, float, str]:
        """
        Decide se deve entrar no trade

        Returns:
            (should_trade, confidence, reason)
        """
        self.stats['total_signals'] += 1

        # Se modelo nao carregado, aceitar todos
        if not self.loaded or self.model is None:
            return True, 0.5, "Modelo ML nao carregado - usando regras base"

        try:
            # Extrair features
            if indicators is None:
                indicators = opportunity.get('indicators', {})

            features = self.extract_features(opportunity, indicators)

            # Preparar para predicao
            X = []
            for col in self.feature_columns:
                val = features.get(col, 0)
                if pd.isna(val) or np.isinf(val):
                    val = 0
                X.append(val)

            X = np.array([X])
            X_scaled = self.scaler.transform(X)

            # Predicao
            pred = self.model.predict(X_scaled)[0]
            prob = self.model.predict_proba(X_scaled)[0][1]

            # Decisao
            if prob >= self.min_confidence and pred == 1:
                self.stats['approved'] += 1
                return True, prob, f"ML aprovado (confianca: {prob:.2%})"
            else:
                self.stats['rejected'] += 1
                return False, prob, f"ML rejeitado (confianca: {prob:.2%}, minimo: {self.min_confidence:.2%})"

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"[MLFilter] Erro na predicao: {e}")
            return True, 0.5, f"Erro no ML: {e}"

    def get_stats(self) -> Dict:
        """Retorna estatisticas de uso"""
        total = self.stats['total_signals']
        return {
            'total_signals': total,
            'approved': self.stats['approved'],
            'rejected': self.stats['rejected'],
            'errors': self.stats['errors'],
            'approval_rate': self.stats['approved'] / total * 100 if total > 0 else 0,
            'model_loaded': self.loaded,
            'model_name': self.model_name,
            'min_confidence': self.min_confidence,
            'model_accuracy': self.metrics.get('accuracy', 0)
        }

    def get_model_info(self) -> Dict:
        """Retorna informacoes do modelo"""
        if not self.loaded:
            return {'loaded': False}

        return {
            'loaded': True,
            'name': self.model_name,
            'accuracy': self.metrics.get('accuracy'),
            'precision': self.metrics.get('precision'),
            'recall': self.metrics.get('recall'),
            'f1': self.metrics.get('f1'),
            'win_rate_improvement': (
                self.metrics.get('win_rate_with_model', 0) -
                self.metrics.get('win_rate_without_model', 0)
            ),
            'pnl_improvement': self.metrics.get('pnl_improvement'),
            'features': len(self.feature_columns),
            'trained_at': self.metrics.get('trained_at')
        }

    def close(self):
        self.mongo_client.close()


# Singleton para uso global
_ml_filter_instance: Optional[MLSignalFilter] = None


def get_ml_filter() -> MLSignalFilter:
    """Retorna instancia singleton do filtro ML"""
    global _ml_filter_instance
    if _ml_filter_instance is None:
        _ml_filter_instance = MLSignalFilter()
    return _ml_filter_instance


def reset_ml_filter():
    """Reseta instancia (util para testes)"""
    global _ml_filter_instance
    if _ml_filter_instance:
        _ml_filter_instance.close()
    _ml_filter_instance = None
