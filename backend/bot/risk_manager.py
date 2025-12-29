import logging
from typing import Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class RiskManager:
    """Risk management for Spot trading positions"""

    def __init__(
        self,
        risk_percentage=2.0,
        max_positions=3,
        leverage=1,
        stop_loss_percentage=1.5,
        reward_ratio=2.0,
        trailing_activation=0.75,
        trailing_step=0.5,
        use_position_cap=True,
    ):
        self.risk_percentage = risk_percentage
        self.max_positions = max_positions
        self.default_leverage = 1  # Spot trading = no leverage
        self.use_position_cap = use_position_cap

        self.stop_loss_percentage = stop_loss_percentage
        self.reward_ratio = reward_ratio
        self.take_profit_percentage = self.stop_loss_percentage * self.reward_ratio

        self.trailing_activation = trailing_activation
        self.trailing_step = trailing_step
    
    def calculate_position_size(
        self,
        balance: float,
        entry_price: float,
        atr: Optional[float] = None,
        volatility_regime: str = 'normal'
    ) -> Dict:
        """
        Calculate position size for Spot trading (no leverage).

        Args:
            balance: Available balance
            entry_price: Entry price for the trade
            atr: Current ATR value (optional, for dynamic stops)
            volatility_regime: 'low', 'normal', or 'high' (used with ATR)

        Returns:
            Dict with position sizing details including stops
        """
        try:
            # Calculate risk amount (capital at risk for the trade)
            target_risk_amount = balance * (self.risk_percentage / 100)

            if self.stop_loss_percentage <= 0:
                raise ValueError("stop_loss_percentage must be greater than zero")

            stop_loss_pct_decimal = self.stop_loss_percentage / 100

            # Capital allocation (evita comprometer todo o balanço em uma única posição)
            capital_ceiling = balance / max(self.max_positions, 1)

            # Position sizing targeting the predefined risk
            theoretical_position_size = target_risk_amount / stop_loss_pct_decimal

            # Limites sem alavancagem: não ultrapassar saldo, e opcionalmente o teto por posição
            if self.use_position_cap:
                position_size_usdt = min(theoretical_position_size, balance, capital_ceiling)
            else:
                position_size_usdt = min(theoretical_position_size, balance)
            quantity = position_size_usdt / entry_price
            effective_risk_amount = position_size_usdt * stop_loss_pct_decimal

            # Se não for possível atingir o risco desejado (por limite de saldo ou teto), avisar nos logs
            if effective_risk_amount < target_risk_amount * 0.9:
                logger.warning(
                    "Risco efetivo menor que o alvo: desejado=%.2f (%.2f%%), efetivo=%.2f (%.2f%%), stop=%.2f%%, max_positions=%s",
                    target_risk_amount,
                    self.risk_percentage,
                    effective_risk_amount,
                    (effective_risk_amount / balance * 100) if balance else 0,
                    self.stop_loss_percentage,
                    self.max_positions,
                )

            # Calculate Stop Loss and Take Profit levels
            # Use dynamic ATR-based stops if provided, otherwise use percentage-based
            if atr is not None:
                stops = self.calculate_dynamic_stops(atr, entry_price, 'BUY', volatility_regime)
                if stops:
                    stop_loss_price = stops['stop_loss']
                    take_profit_price = stops['take_profit']
                    logger.info(
                        f"[Position Sizing] Using ATR stops - "
                        f"SL: {stop_loss_price:.4f}, TP: {take_profit_price:.4f}, R/R: 1:{stops['risk_reward']}"
                    )
                else:
                    # Fallback to percentage-based
                    stop_loss_price = entry_price * (1 - stop_loss_pct_decimal)
                    take_profit_price = entry_price * (1 + self.take_profit_percentage / 100)
                    logger.warning("[Position Sizing] ATR stops calculation failed, using percentage-based")
            else:
                # Legacy percentage-based stops
                stop_loss_price = entry_price * (1 - stop_loss_pct_decimal)
                take_profit_price = entry_price * (1 + self.take_profit_percentage / 100)
                logger.debug("[Position Sizing] Using percentage-based stops (no ATR provided)")
            
            return {
                'quantity': round(quantity, 6),
                'position_size_usdt': round(position_size_usdt, 2),
                'leverage': 1,  # No leverage in Spot
                'stop_loss': round(stop_loss_price, 4),
                'take_profit': round(take_profit_price, 4),
                'margin_required': round(position_size_usdt, 2),  # Full amount needed
                'risk_amount': round(effective_risk_amount, 2),
                'risk_amount_target': round(target_risk_amount, 2),
                'risk_percent_effective': round((effective_risk_amount / balance * 100), 3) if balance else 0,
                'trailing_activation': self.trailing_activation,
                'trailing_step': self.trailing_step,
            }
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return None

    def calculate_dynamic_stops(
        self,
        atr: float,
        entry_price: float,
        side: str,
        volatility_regime: str = 'normal'
    ) -> Dict:
        """
        Calculate dynamic stop loss and take profit based on ATR.

        Volatility Regimes:
        - 'low': Use 3x ATR for SL, 10x for TP (R/R 1:3.33)
        - 'normal': Use 3.5x ATR for SL, 12x for TP (R/R 1:3.43)
        - 'high': Use 5x ATR for SL, 15x for TP (R/R 1:3.0)

        Args:
            atr: Current ATR value
            entry_price: Entry price
            side: 'BUY' or 'SELL'
            volatility_regime: 'low', 'normal', or 'high'

        Returns:
            Dict with 'stop_loss', 'take_profit', 'risk_reward', 'atr', 'sl_multiplier', 'tp_multiplier'
        """
        try:
            # Determine multipliers based on regime
            if volatility_regime == 'high':
                sl_mult = 2.5  # CORREÇÃO: Reduzido de 5.0 para 2.5
                tp_mult = 7.5  # CORREÇÃO: Reduzido de 15.0 para 7.5
            elif volatility_regime == 'low':
                sl_mult = 1.8  # CORREÇÃO: Reduzido de 3.0 para 1.8
                tp_mult = 5.4  # CORREÇÃO: Reduzido de 10.0 para 5.4
            else:  # normal
                sl_mult = 2.0  # CORREÇÃO: Reduzido de 3.5 para 2.0
                tp_mult = 6.0  # CORREÇÃO: Reduzido de 12.0 para 6.0

            # Calculate stops
            if side == 'BUY':
                stop_loss = round(entry_price - (sl_mult * atr), 4)
                take_profit = round(entry_price + (tp_mult * atr), 4)
            else:  # SELL
                stop_loss = round(entry_price + (sl_mult * atr), 4)
                take_profit = round(entry_price - (tp_mult * atr), 4)

            # Calculate risk/reward
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            risk_reward = round(reward / risk, 2) if risk > 0 else 0

            # CORREÇÃO: Garantir Risk/Reward mínimo de 2.5 (mais realista que 3.0)
            if risk_reward < 2.5:
                logger.warning(f"R/R {risk_reward} below minimum 2.5, adjusting TP")
                if side == 'BUY':
                    take_profit = entry_price + (risk * 2.5)
                else:
                    take_profit = entry_price - (risk * 2.5)
                take_profit = round(take_profit, 4)
                risk_reward = 2.5

            logger.info(
                f"[ATR Stops] Regime: {volatility_regime}, ATR: {atr:.4f}, "
                f"SL mult: {sl_mult}x, TP mult: {tp_mult}x, R/R: 1:{risk_reward}"
            )

            return {
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'risk_reward': risk_reward,
                'atr': atr,
                'sl_multiplier': sl_mult,
                'tp_multiplier': tp_mult,
                'volatility_regime': volatility_regime
            }

        except Exception as e:
            logger.error(f"Error calculating dynamic stops: {e}")
            return None

    def should_close_by_time(self, opened_at: datetime, max_hold_hours: int = 4) -> bool:
        """
        Check if position should be closed due to time limit.
        Prevents capital being tied up in dead positions.

        Args:
            opened_at: Position opening time (datetime or ISO string)
            max_hold_hours: Maximum hours to hold position (default 4)

        Returns:
            True if position should be closed
        """
        try:
            now = datetime.now(timezone.utc)
            if isinstance(opened_at, str):
                opened_at = datetime.fromisoformat(opened_at.replace('Z', '+00:00'))

            hours_open = (now - opened_at).total_seconds() / 3600

            if hours_open >= max_hold_hours:
                logger.info(f"[Time Stop] Position open for {hours_open:.1f}h >= {max_hold_hours}h limit")
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking time stop: {e}")
            return False

    def calculate_pnl(self, entry_price: float, exit_price: float, 
                     quantity: float, side: str, leverage: int = 1) -> Dict:
        """Calculate profit and loss for Spot trading"""
        try:
            if side == 'BUY':
                price_diff = exit_price - entry_price
            else:  # SELL
                price_diff = entry_price - exit_price
            
            pnl = price_diff * quantity
            position_value = entry_price * quantity
            roe = (pnl / position_value) * 100  # No leverage in Spot
            
            return {
                'pnl': round(pnl, 2),
                'roe': round(roe, 2),
                'price_diff': round(price_diff, 4),
                'price_diff_percentage': round((price_diff / entry_price) * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating PnL: {e}")
            return None
    
    def should_close_position(self, current_price: float, entry_price: float, 
                             stop_loss: float, take_profit: float, side: str) -> tuple:
        """Check if position should be closed"""
        try:
            if side == 'BUY':
                if current_price <= stop_loss:
                    return True, 'STOP_LOSS'
                elif current_price >= take_profit:
                    return True, 'TAKE_PROFIT'
            else:  # SELL
                if current_price >= stop_loss:
                    return True, 'STOP_LOSS'
                elif current_price <= take_profit:
                    return True, 'TAKE_PROFIT'
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error checking position close: {e}")
            return False, None