"""
Treinador de Modelo ML
Treina e avalia modelos para filtragem de sinais
"""

import os
import sys
import logging
import pickle
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv

# Sklearn
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)

load_dotenv()

logger = logging.getLogger(__name__)


# Features a usar para treinamento
FEATURE_COLUMNS = [
    # Indicadores principais
    'rsi', 'macd', 'macd_signal', 'macd_hist',
    'ema_fast_dist', 'ema_slow_dist', 'ema_50_dist', 'ema_200_dist',
    'bb_width_pct', 'bb_position',
    'atr_pct', 'vwap_dist',

    # Momentum
    'return_1', 'return_3', 'return_5',
    'volume_ratio',

    # Candle
    'body_pct', 'upper_wick_pct', 'lower_wick_pct', 'is_bullish',

    # Sinal
    'signal_strength',

    # Temporal
    'hour', 'day_of_week',
]


class ModelTrainer:
    """Treina e gerencia modelos de ML"""

    def __init__(self):
        # MongoDB
        mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.getenv('DB_NAME', 'trading_bot')
        self.mongo_client = MongoClient(mongo_url)
        self.db = self.mongo_client[db_name]

        self.scaler = StandardScaler()
        self.model = None
        self.feature_columns = FEATURE_COLUMNS.copy()
        self.metrics = {}

    def load_dataset(self, name: str = 'training_data') -> pd.DataFrame:
        """Carrega dataset do MongoDB"""
        cursor = self.db.ml_training_data.find({'dataset_name': name})
        data = list(cursor)

        if not data:
            logger.error(f"[Trainer] Dataset '{name}' nao encontrado")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df = df.drop(columns=['_id', 'generated_at', 'dataset_name'], errors='ignore')

        logger.info(f"[Trainer] Dataset carregado: {len(df)} amostras")

        return df

    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepara features e target"""

        # Filtrar colunas que existem
        available_cols = [c for c in self.feature_columns if c in df.columns]
        missing_cols = [c for c in self.feature_columns if c not in df.columns]

        if missing_cols:
            logger.warning(f"[Trainer] Colunas faltando: {missing_cols}")

        self.feature_columns = available_cols

        X = df[available_cols].copy()
        y = df['is_win'].values

        # Preencher NaN com mediana
        X = X.fillna(X.median())

        # Substituir infinitos
        X = X.replace([np.inf, -np.inf], 0)

        return X.values, y

    def train_test_split_temporal(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2
    ) -> Tuple:
        """Split temporal (ultimos X% para teste)"""
        split_idx = int(len(X) * (1 - test_size))

        X_train = X[:split_idx]
        X_test = X[split_idx:]
        y_train = y[:split_idx]
        y_test = y[split_idx:]

        return X_train, X_test, y_train, y_test

    def train(
        self,
        dataset_name: str = 'training_data',
        model_type: str = 'random_forest',
        test_size: float = 0.2
    ) -> Dict:
        """Treina modelo"""

        logger.info(f"[Trainer] Iniciando treinamento...")

        # Carregar dados
        df = self.load_dataset(dataset_name)
        if df.empty:
            return {'error': 'Dataset vazio'}

        # Preparar features
        X, y = self.prepare_features(df)

        logger.info(f"[Trainer] Features: {len(self.feature_columns)}")
        logger.info(f"[Trainer] Amostras: {len(X)}")
        logger.info(f"[Trainer] Distribuicao: {np.bincount(y.astype(int))}")

        # Split temporal
        X_train, X_test, y_train, y_test = self.train_test_split_temporal(X, y, test_size)

        logger.info(f"[Trainer] Train: {len(X_train)} | Test: {len(X_test)}")

        # Normalizar
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Escolher modelo
        if model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        else:
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=20,
                min_samples_leaf=10,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            )

        # Treinar
        logger.info(f"[Trainer] Treinando {model_type}...")
        self.model.fit(X_train_scaled, y_train)

        # Avaliar
        y_pred = self.model.predict(X_test_scaled)
        y_prob = self.model.predict_proba(X_test_scaled)[:, 1]

        # Metricas
        self.metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1': f1_score(y_test, y_pred, zero_division=0),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'win_rate_actual': y_test.mean(),
            'win_rate_predicted': y_pred.mean(),
            'model_type': model_type,
            'features_used': len(self.feature_columns),
            'trained_at': datetime.now(timezone.utc).isoformat()
        }

        # Simular PnL com modelo
        df_test = df.iloc[-len(y_test):].copy()
        df_test['predicted'] = y_pred

        # PnL se seguir modelo
        trades_with_model = df_test[df_test['predicted'] == 1]
        pnl_with_model = trades_with_model['pnl_pct'].sum() if len(trades_with_model) > 0 else 0
        win_rate_with_model = trades_with_model['is_win'].mean() * 100 if len(trades_with_model) > 0 else 0

        # PnL sem modelo (todos trades)
        pnl_without_model = df_test['pnl_pct'].sum()
        win_rate_without_model = df_test['is_win'].mean() * 100

        self.metrics['pnl_with_model'] = pnl_with_model
        self.metrics['pnl_without_model'] = pnl_without_model
        self.metrics['pnl_improvement'] = pnl_with_model - pnl_without_model
        self.metrics['win_rate_with_model'] = win_rate_with_model
        self.metrics['win_rate_without_model'] = win_rate_without_model
        self.metrics['trades_filtered'] = len(df_test) - len(trades_with_model)
        self.metrics['trades_taken'] = len(trades_with_model)

        # Feature importance
        if hasattr(self.model, 'feature_importances_'):
            importance = dict(zip(self.feature_columns, self.model.feature_importances_))
            importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
            self.metrics['feature_importance'] = importance

        logger.info(f"[Trainer] Treinamento concluido!")
        logger.info(f"[Trainer] Accuracy: {self.metrics['accuracy']:.2%}")
        logger.info(f"[Trainer] Win Rate com modelo: {win_rate_with_model:.1f}%")
        logger.info(f"[Trainer] Win Rate sem modelo: {win_rate_without_model:.1f}%")
        logger.info(f"[Trainer] PnL com modelo: {pnl_with_model:.2f}%")
        logger.info(f"[Trainer] PnL sem modelo: {pnl_without_model:.2f}%")

        return self.metrics

    def save_model(self, name: str = 'signal_filter'):
        """Salva modelo no MongoDB"""
        if self.model is None:
            logger.error("[Trainer] Nenhum modelo para salvar")
            return

        # Serializar modelo
        model_bytes = pickle.dumps(self.model)
        scaler_bytes = pickle.dumps(self.scaler)

        doc = {
            'name': name,
            'model_bytes': model_bytes,
            'scaler_bytes': scaler_bytes,
            'feature_columns': self.feature_columns,
            'metrics': self.metrics,
            'created_at': datetime.now(timezone.utc)
        }

        # Upsert
        self.db.ml_models.update_one(
            {'name': name},
            {'$set': doc},
            upsert=True
        )

        logger.info(f"[Trainer] Modelo '{name}' salvo")

    def load_model(self, name: str = 'signal_filter') -> bool:
        """Carrega modelo do MongoDB"""
        doc = self.db.ml_models.find_one({'name': name})

        if not doc:
            logger.error(f"[Trainer] Modelo '{name}' nao encontrado")
            return False

        self.model = pickle.loads(doc['model_bytes'])
        self.scaler = pickle.loads(doc['scaler_bytes'])
        self.feature_columns = doc['feature_columns']
        self.metrics = doc.get('metrics', {})

        logger.info(f"[Trainer] Modelo '{name}' carregado")
        return True

    def predict(self, features: Dict) -> Tuple[bool, float]:
        """Faz predicao para um trade"""
        if self.model is None:
            return True, 0.5  # Sem modelo, aceitar tudo

        # Preparar features
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

        return bool(pred), float(prob)

    def close(self):
        self.mongo_client.close()


def run_trainer():
    """CLI para treinar modelo"""
    import argparse

    parser = argparse.ArgumentParser(description='Treinar modelo ML')
    parser.add_argument('--dataset', default='training_data', help='Nome do dataset')
    parser.add_argument('--model', default='random_forest', choices=['random_forest', 'gradient_boosting'])
    parser.add_argument('--name', default='signal_filter', help='Nome para salvar modelo')
    parser.add_argument('--test-size', type=float, default=0.2, help='Proporcao de teste')

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    trainer = ModelTrainer()

    print("\n" + "=" * 60)
    print("TREINAMENTO DE MODELO ML")
    print("=" * 60)

    metrics = trainer.train(
        dataset_name=args.dataset,
        model_type=args.model,
        test_size=args.test_size
    )

    if 'error' not in metrics:
        trainer.save_model(args.name)

        print("\n" + "-" * 60)
        print("RESULTADOS:")
        print(f"  Accuracy: {metrics['accuracy']:.2%}")
        print(f"  Precision: {metrics['precision']:.2%}")
        print(f"  Recall: {metrics['recall']:.2%}")
        print(f"  F1 Score: {metrics['f1']:.2%}")

        print("\n" + "-" * 60)
        print("IMPACTO NO TRADING:")
        print(f"  Win Rate SEM modelo: {metrics['win_rate_without_model']:.1f}%")
        print(f"  Win Rate COM modelo: {metrics['win_rate_with_model']:.1f}%")
        print(f"  PnL SEM modelo: {metrics['pnl_without_model']:.2f}%")
        print(f"  PnL COM modelo: {metrics['pnl_with_model']:.2f}%")
        print(f"  Trades filtrados: {metrics['trades_filtered']}")

        if 'feature_importance' in metrics:
            print("\n" + "-" * 60)
            print("TOP 10 FEATURES:")
            for i, (feat, imp) in enumerate(list(metrics['feature_importance'].items())[:10], 1):
                print(f"  {i}. {feat}: {imp:.4f}")

    trainer.close()


if __name__ == '__main__':
    run_trainer()
