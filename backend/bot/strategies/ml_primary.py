"""
MLPrimaryStrategy — Machine Learning as primary signal generator.

Upgrades MLSignalFilter from a simple confirmation gate to a primary strategy:
  - Trained RandomForest + GradientBoosting models predict direction
  - Feature engineering extracts 20+ features from OHLCV data
  - Models retrain periodically on recent trades
  - Falls back to ensemble heuristic when model confidence < threshold

Compatible regimes: all (adaptive)
"""

from __future__ import annotations

import logging
import os
import pickle
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from bot.strategy_engine import BaseStrategy, MarketRegime, StrategySignal

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "ml" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


class MLPrimaryStrategy(BaseStrategy):
    """ML-driven strategy: model predicts direction, technicals provide scoring."""

    name = "ml_primary"
    compatible_regimes = ["trending", "ranging", "volatile"]

    def __init__(
        self,
        client=None,
        *,
        model_confidence_threshold: float = 0.55,
        min_score: int = 50,
        retrain_interval_hours: int = 24,
        feature_lookback: int = 50,
        **kwargs,
    ):
        super().__init__(client, **kwargs)
        self.model_confidence_threshold = model_confidence_threshold
        self.min_score = min_score
        self.retrain_interval_hours = retrain_interval_hours
        self.feature_lookback = feature_lookback
        self._model = None
        self._last_train_time: datetime | None = None
        self._load_or_init_model()

    def _load_or_init_model(self):
        """Load existing model or initialize a new one."""
        model_path = MODEL_DIR / "ml_primary_strategy.pkl"
        if model_path.exists():
            try:
                with open(model_path, "rb") as f:
                    data = pickle.load(f)
                self._model = data.get("model")
                self._last_train_time = data.get("trained_at")
                logger.info("Loaded ML model trained at %s", self._last_train_time)
            except Exception as e:
                logger.warning("Failed to load ML model: %s — will train fresh", e)
                self._model = None
        else:
            logger.info("No existing ML model — will use heuristic until trained")

    def analyze(self, symbol: str, df: pd.DataFrame, regime: MarketRegime) -> StrategySignal | None:
        try:
            if len(df) < self.feature_lookback:
                return None

            df = self._ensure_indicators(df)
            latest = df.iloc[-1]
            price = float(latest["close"])
            atr = float(latest.get("atr", 0)) or price * 0.01

            # Extract features
            features = self._extract_features(df)
            if features is None:
                return None

            # Get prediction
            if self._model is not None:
                try:
                    X = np.array(list(features.values())).reshape(1, -1)
                    proba = self._model.predict_proba(X)[0]
                    # Map probabilities to classes
                    classes = self._model.classes_
                    prediction = classes[np.argmax(proba)]
                    confidence = float(np.max(proba))
                except Exception as e:
                    logger.warning("ML prediction failed: %s", e)
                    prediction, confidence = self._heuristic_prediction(df)
            else:
                prediction, confidence = self._heuristic_prediction(df)

            if prediction == 0 or confidence < self.model_confidence_threshold:
                return None

            signal = "BUY" if prediction == 1 else "SELL"

            # Score = confidence * 100 + technical alignment bonus
            score = confidence * 60

            # Technical alignment
            rsi = float(latest.get("rsi", 50)) if not pd.isna(latest.get("rsi", np.nan)) else 50.0
            ema_fast = latest.get("ema_fast")
            ema_slow = latest.get("ema_slow")

            if signal == "BUY" and rsi < 50: score += 15
            elif signal == "SELL" and rsi > 50: score += 15

            if ema_fast and ema_slow and not pd.isna(ema_fast) and not pd.isna(ema_slow):
                if signal == "BUY" and ema_fast > ema_slow: score += 10
                elif signal == "SELL" and ema_fast < ema_slow: score += 10

            # Volume confirmation
            vol_ratio = features.get("volume_ratio", 1.0)
            if vol_ratio > 1.2: score += 10

            # Regime alignment
            if signal == "BUY" and regime.direction == "up": score += 5
            elif signal == "SELL" and regime.direction == "down": score += 5
            elif regime.regime == "volatile": score += 5  # ML shines in volatility

            if score < self.min_score:
                return None

            # Stop loss / take profit
            if signal == "BUY":
                sl = price - atr * 2.0
                tp = price + atr * 3.5
            else:
                sl = price + atr * 2.0
                tp = price - atr * 3.5

            return StrategySignal(
                strategy_name=self.name,
                symbol=symbol,
                signal=signal,
                score=min(score, 100),
                confidence=confidence,
                entry_price=price,
                stop_loss=sl,
                take_profit=tp,
                regime=regime,
                metadata={
                    "ml_confidence": round(confidence, 3),
                    "ml_prediction": prediction,
                    "feature_count": len(features),
                },
            )

        except Exception as e:
            logger.error("MLPrimaryStrategy error on %s: %s", symbol, e)
            return None

    def _extract_features(self, df: pd.DataFrame) -> dict | None:
        """Extract 20+ features for ML model."""
        try:
            if len(df) < 50:
                return None

            close = df["close"].values
            high = df["high"].values
            low = df["low"].values
            volume = df["volume"].values

            features = {}

            # Price returns
            features["return_1"] = (close[-1] / close[-2] - 1) * 100
            features["return_5"] = (close[-1] / close[-6] - 1) * 100
            features["return_10"] = (close[-1] / close[-11] - 1) * 100

            # RSI zones
            rsi = df["rsi"].values[-1]
            features["rsi"] = rsi if not np.isnan(rsi) else 50.0
            features["rsi_ma3"] = np.nanmean(df["rsi"].values[-3:])

            # MACD
            macd_hist = df["macd_hist"].values
            features["macd_hist"] = macd_hist[-1] if not np.isnan(macd_hist[-1]) else 0.0
            features["macd_hist_change"] = macd_hist[-1] - macd_hist[-2] if not np.isnan(macd_hist[-1]) and not np.isnan(macd_hist[-2]) else 0.0

            # Bollinger position
            bb_low = df["bb_lower"].values[-1]
            bb_up = df["bb_upper"].values[-1]
            features["bb_position"] = (close[-1] - bb_low) / (bb_up - bb_low) if bb_up > bb_low else 0.5

            # Volatility
            returns = np.diff(close[-20:]) / close[-20:-1]
            features["volatility_20"] = np.std(returns) * 100

            # Volume
            vol_20ma = np.mean(volume[-20:])
            features["volume_ratio"] = volume[-1] / vol_20ma if vol_20ma > 0 else 1.0
            features["volume_trend"] = np.mean(volume[-5:]) / np.mean(volume[-10:-5]) if np.mean(volume[-10:-5]) > 0 else 1.0

            # ATR
            atr = df["atr"].values[-1]
            features["atr_pct"] = (atr / close[-1]) * 100 if close[-1] > 0 else 1.0

            # EMA relationships
            ema_12 = df["ema_fast"].values[-1] if "ema_fast" in df.columns else close[-1]
            ema_26 = df["ema_slow"].values[-1] if "ema_slow" in df.columns else close[-1]
            features["ema_cross"] = (ema_12 / ema_26 - 1) * 100 if ema_26 > 0 else 0.0

            # Price vs moving averages
            features["price_vs_sma20"] = (close[-1] / np.mean(close[-20:]) - 1) * 100
            features["price_vs_sma50"] = (close[-1] / np.mean(close[-50:]) - 1) * 100 if len(close) >= 50 else 0.0

            # High-low range
            features["hl_range"] = (high[-1] / low[-1] - 1) * 100
            features["hl_range_ma5"] = np.mean([(high[-i] / low[-i] - 1) * 100 for i in range(1, 6)])

            # Momentum
            features["momentum_10"] = close[-1] - close[-10] if len(close) >= 10 else 0.0

            # ADX
            adx = df["adx"].values[-1] if "adx" in df.columns else 20.0
            features["adx"] = adx if not np.isnan(adx) else 20.0

            return features

        except Exception as e:
            logger.warning("Feature extraction error: %s", e)
            return None

    def _heuristic_prediction(self, df: pd.DataFrame) -> tuple[int, float]:
        """Fallback prediction when no ML model is available."""
        try:
            latest = df.iloc[-1]
            buy_points, sell_points = 0.0, 0.0

            # EMA trend
            ema_fast = latest.get("ema_fast")
            ema_slow = latest.get("ema_slow")
            if ema_fast is not None and ema_slow is not None and not pd.isna(ema_fast) and not pd.isna(ema_slow):
                if ema_fast > ema_slow: buy_points += 2
                else: sell_points += 2

            # RSI
            rsi = latest.get("rsi", 50)
            if not pd.isna(rsi):
                if rsi < 40: buy_points += 1.5
                elif rsi > 60: sell_points += 1.5

            # MACD
            macd_hist = latest.get("macd_hist", 0)
            if not pd.isna(macd_hist):
                if macd_hist > 0: buy_points += 1
                else: sell_points += 1

            if buy_points > sell_points:
                return 1, min(0.7, buy_points / (buy_points + sell_points))
            elif sell_points > buy_points:
                return -1, min(0.7, sell_points / (buy_points + sell_points))
            else:
                return 0, 0.5

        except Exception:
            return 0, 0.5

    def train(self, trades_data: list[dict]) -> bool:
        """Train ML model on historical trade data."""
        try:
            from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier
        except ImportError:
            logger.warning("scikit-learn not available — skipping ML training")
            return False

        if len(trades_data) < 20:
            logger.info("Not enough trades (%d) to train ML model", len(trades_data))
            return False

        try:
            X_list, y_list = [], []
            for trade in trades_data:
                feats = trade.get("features", {})
                if not feats:
                    continue
                X_list.append(list(feats.values()))
                y_list.append(1 if trade.get("pnl_pct", 0) > 0 else -1 if trade.get("pnl_pct", 0) < 0 else 0)

            if len(X_list) < 10:
                return False

            X = np.array(X_list)
            y = np.array(y_list)

            # Ensemble: RF + GB
            rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
            gb = GradientBoostingClassifier(n_estimators=100, max_depth=4, random_state=42)
            ensemble = VotingClassifier(
                estimators=[("rf", rf), ("gb", gb)],
                voting="soft",
            )
            ensemble.fit(X, y)

            self._model = ensemble
            self._last_train_time = datetime.now(timezone.utc)

            # Save model
            model_path = MODEL_DIR / "ml_primary_strategy.pkl"
            with open(model_path, "wb") as f:
                pickle.dump({"model": ensemble, "trained_at": self._last_train_time}, f)

            logger.info("ML model trained on %d trades — saved to %s", len(X), model_path)
            return True

        except Exception as e:
            logger.error("ML training failed: %s", e)
            return False
