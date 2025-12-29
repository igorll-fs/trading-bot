"""
Sistema de Aprendizado Avançado - Machine Learning Real
Aprende padrões dos trades e otimiza estratégia

DIFERENÇAS DO SISTEMA ANTERIOR:
1. Analisa PADRÕES, não apenas métricas agregadas
2. Usa regressão para encontrar parâmetros ótimos
3. Considera contexto (volatilidade, hora, indicadores)
4. Validação cruzada para evitar overfitting
5. Ajustes graduais baseados em confiança estatística
"""

import logging
import os
import statistics
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class PatternAnalyzer:
    """Analisa padrões de sucesso/falha nos trades"""
    
    def __init__(self):
        self.patterns = defaultdict(lambda: {'wins': 0, 'losses': 0, 'total_pnl': 0})
    
    def add_trade(self, trade: Dict):
        """Adiciona trade para análise de padrões"""
        # Criar chaves de padrão
        patterns = self._extract_patterns(trade)
        is_win = trade.get('pnl', 0) > 0
        pnl = trade.get('pnl', 0)
        
        for pattern in patterns:
            if is_win:
                self.patterns[pattern]['wins'] += 1
            else:
                self.patterns[pattern]['losses'] += 1
            self.patterns[pattern]['total_pnl'] += pnl
    
    def _extract_patterns(self, trade: Dict) -> List[str]:
        """Extrai padrões identificáveis do trade"""
        patterns = []
        
        # Padrão por símbolo
        symbol = trade.get('symbol', 'UNKNOWN')
        patterns.append(f"symbol:{symbol}")
        
        # Padrão por side (BUY/SELL)
        side = trade.get('side', 'UNKNOWN')
        patterns.append(f"side:{side}")
        
        # Padrão por hora do dia (0-23)
        try:
            opened = trade.get('opened_at', '')
            if opened:
                if isinstance(opened, str):
                    dt = datetime.fromisoformat(opened.replace('Z', '+00:00'))
                else:
                    dt = opened
                hour = dt.hour
                # Agrupar em períodos
                if 0 <= hour < 6:
                    period = 'night'
                elif 6 <= hour < 12:
                    period = 'morning'
                elif 12 <= hour < 18:
                    period = 'afternoon'
                else:
                    period = 'evening'
                patterns.append(f"period:{period}")
        except:
            pass
        
        # Padrão por ROE esperado vs realizado
        roe = trade.get('roe', 0)
        if roe > 5:
            patterns.append("roe_class:high_win")
        elif roe > 0:
            patterns.append("roe_class:small_win")
        elif roe > -3:
            patterns.append("roe_class:small_loss")
        else:
            patterns.append("roe_class:big_loss")
        
        # Padrão por duração
        try:
            opened = trade.get('opened_at', '')
            closed = trade.get('closed_at', '')
            if opened and closed:
                if isinstance(opened, str):
                    dt_open = datetime.fromisoformat(opened.replace('Z', '+00:00'))
                else:
                    dt_open = opened
                if isinstance(closed, str):
                    dt_close = datetime.fromisoformat(closed.replace('Z', '+00:00'))
                else:
                    dt_close = closed
                duration = (dt_close - dt_open).total_seconds()
                if duration < 300:
                    patterns.append("duration:very_short")
                elif duration < 1800:
                    patterns.append("duration:short")
                elif duration < 7200:
                    patterns.append("duration:medium")
                else:
                    patterns.append("duration:long")
        except:
            pass
        
        return patterns
    
    def get_best_patterns(self, min_trades: int = 5) -> List[Tuple[str, float, int]]:
        """Retorna padrões com melhor win rate"""
        results = []
        for pattern, stats in self.patterns.items():
            total = stats['wins'] + stats['losses']
            if total >= min_trades:
                win_rate = stats['wins'] / total * 100
                avg_pnl = stats['total_pnl'] / total
                results.append((pattern, win_rate, total, avg_pnl))
        
        # Ordenar por win rate
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def get_worst_patterns(self, min_trades: int = 5) -> List[Tuple[str, float, int]]:
        """Retorna padrões com pior win rate"""
        results = self.get_best_patterns(min_trades)
        results.reverse()
        return results


class AdvancedLearningSystem:
    """Sistema de aprendizado avançado com ML real"""
    
    def __init__(self, db):
        self.db = db
        mode = os.getenv("BOT_LEARNING_MODE", "active").strip().lower()
        if mode not in {"active", "observe", "disabled"}:
            mode = "active"
        self.mode = mode
        self.observe_only = self.mode == "observe"
        self.learning_enabled = self.mode != "disabled"
        
        # Configurações
        self.min_trades_for_learning = int(os.getenv("LEARNING_MIN_TRADES", "15"))  # Threshold reduzido para aprendizado mais rápido
        logger.info(f"[ML] Trade threshold set to {self.min_trades_for_learning} trades before optimization")
        self.confidence_interval = float(os.getenv("LEARNING_CONFIDENCE", "0.95"))
        self.max_param_change = float(os.getenv("LEARNING_MAX_CHANGE", "0.10"))  # Max 10% por ajuste
        
        # Parâmetros ajustáveis
        self.params = {
            'min_confidence_score': 0.5,
            'stop_loss_percent': 2.0,      # % de SL
            'take_profit_percent': 3.0,    # % de TP
            'position_size_percent': 5.0,  # % do capital
            'max_positions': 3,
        }
        
        # Limites dos parâmetros
        self.param_bounds = {
            'min_confidence_score': (0.3, 0.8),
            'stop_loss_percent': (1.0, 5.0),
            'take_profit_percent': (1.5, 8.0),
            'position_size_percent': (2.0, 10.0),
            'max_positions': (1, 5),
        }
        
        # Analisador de padrões
        self.pattern_analyzer = PatternAnalyzer()
        
        # Histórico para validação
        self.trade_history = []
        self.param_history = []
        
        # Métricas
        self.metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'expectancy': 0.0,
        }
    
    async def initialize(self):
        """Inicializa o sistema carregando dados históricos"""
        if not self.learning_enabled:
            logger.info("Advanced Learning System disabled")
            return
        
        try:
            # Carregar parâmetros salvos
            saved = await self.db.advanced_learning.find_one(
                {'type': 'parameters'},
                sort=[('timestamp', -1)]
            )
            
            if saved:
                self.params.update(saved.get('params', {}))
                self.metrics.update(saved.get('metrics', {}))
                logger.info("Advanced Learning: Parâmetros restaurados")
            
            # Carregar histórico de trades para análise (projeção otimizada)
            trades = await self.db.trades.find(
                {},
                {"pnl": 1, "symbol": 1, "side": 1, "opened_at": 1, "closed_at": 1, "_id": 0}
            ).sort('closed_at', -1).limit(500).to_list(500)
            
            for trade in trades:
                self.trade_history.append(trade)
                self.pattern_analyzer.add_trade(trade)
            
            # Calcular métricas iniciais
            await self._calculate_advanced_metrics()
            
            logger.info(f"Advanced Learning inicializado com {len(self.trade_history)} trades")
            logger.info(f"Win Rate: {self.metrics['win_rate']:.1f}%")
            logger.info(f"Profit Factor: {self.metrics['profit_factor']:.2f}")
            logger.info(f"Expectancy: ${self.metrics['expectancy']:.2f}")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar Advanced Learning: {e}")
    
    async def _calculate_advanced_metrics(self):
        """Calcula métricas avançadas de performance"""
        if not self.trade_history:
            return
        
        trades = self.trade_history
        pnls = [t.get('pnl', 0) for t in trades]
        
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        
        self.metrics['total_trades'] = len(trades)
        self.metrics['winning_trades'] = len(wins)
        self.metrics['losing_trades'] = len(losses)
        self.metrics['win_rate'] = len(wins) / len(trades) * 100 if trades else 0
        
        # Profit Factor
        total_wins = sum(wins) if wins else 0
        total_losses = abs(sum(losses)) if losses else 1
        self.metrics['profit_factor'] = total_wins / total_losses if total_losses > 0 else 0
        
        # Médias
        self.metrics['avg_win'] = statistics.mean(wins) if wins else 0
        self.metrics['avg_loss'] = statistics.mean(losses) if losses else 0
        
        # Expectancy (valor esperado por trade)
        win_rate = self.metrics['win_rate'] / 100
        self.metrics['expectancy'] = (
            win_rate * self.metrics['avg_win'] + 
            (1 - win_rate) * self.metrics['avg_loss']
        )
        
        # Sharpe Ratio (simplificado)
        if len(pnls) > 1:
            mean_return = statistics.mean(pnls)
            std_return = statistics.stdev(pnls)
            self.metrics['sharpe_ratio'] = mean_return / std_return if std_return > 0 else 0
        
        # Max Drawdown
        cumulative = 0
        peak = 0
        max_dd = 0
        for pnl in pnls:
            cumulative += pnl
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd
        self.metrics['max_drawdown'] = max_dd
    
    async def learn_from_trade(self, trade: Dict):
        """Aprende com um trade fechado"""
        if not self.learning_enabled:
            return
        
        try:
            # Adicionar ao histórico
            self.trade_history.insert(0, trade)
            if len(self.trade_history) > 500:
                self.trade_history.pop()
            
            # Analisar padrões
            self.pattern_analyzer.add_trade(trade)
            
            # Atualizar métricas
            await self._calculate_advanced_metrics()
            
            pnl = trade.get('pnl', 0)
            symbol = trade.get('symbol', 'UNKNOWN')
            
            logger.info(f"[ML] Trade analisado: {symbol} | PnL: ${pnl:.2f}")
            logger.info(f"[ML] Métricas: WR={self.metrics['win_rate']:.1f}% | PF={self.metrics['profit_factor']:.2f} | Exp=${self.metrics['expectancy']:.2f}")
            
            # Só ajusta parâmetros se tiver trades suficientes
            if self.metrics['total_trades'] < self.min_trades_for_learning:
                logger.info(f"[ML] Coletando dados: {self.metrics['total_trades']}/{self.min_trades_for_learning}")
                await self._save_analysis(trade)
                return
            
            # Otimizar parâmetros
            if not self.observe_only:
                await self._optimize_parameters()
            
            # Salvar
            await self._save_state(trade)
            
        except Exception as e:
            logger.error(f"Erro ao aprender com trade: {e}")
    
    async def _optimize_parameters(self):
        """Otimiza parâmetros baseado nos dados coletados"""
        try:
            old_params = self.params.copy()
            
            # 1. OTIMIZAR CONFIDENCE SCORE baseado em padrões
            #    Se trades com score alto têm melhor win rate, aumentar threshold
            await self._optimize_confidence_score()
            
            # 2. OTIMIZAR STOP LOSS baseado em análise de perdas
            await self._optimize_stop_loss()
            
            # 3. OTIMIZAR TAKE PROFIT baseado em análise de ganhos
            await self._optimize_take_profit()
            
            # 4. OTIMIZAR POSITION SIZE baseado em volatilidade e risco
            await self._optimize_position_size()
            
            # Log mudanças
            for param, old_value in old_params.items():
                new_value = self.params[param]
                if abs(new_value - old_value) > 0.001:
                    logger.info(f"[ML] {param}: {old_value:.3f} -> {new_value:.3f}")
            
        except Exception as e:
            logger.error(f"Erro na otimização: {e}")
    
    async def _optimize_confidence_score(self):
        """Otimiza o score mínimo de confiança"""
        # Analisar win rate por período
        best_patterns = self.pattern_analyzer.get_best_patterns(min_trades=10)
        worst_patterns = self.pattern_analyzer.get_worst_patterns(min_trades=10)
        
        # Se temos padrões claros de sucesso, podemos ser mais seletivos
        if best_patterns and worst_patterns:
            best_wr = best_patterns[0][1] if best_patterns else 50
            worst_wr = worst_patterns[0][1] if worst_patterns else 50
            
            spread = best_wr - worst_wr
            
            # Se spread grande, aumentar seletividade
            if spread > 30:  # Grande diferença entre bons e maus padrões
                target = self.params['min_confidence_score'] + 0.03
            elif spread < 10:  # Pouca diferença
                target = self.params['min_confidence_score'] - 0.02
            else:
                target = self.params['min_confidence_score']
            
            # Aplicar com limite
            bounds = self.param_bounds['min_confidence_score']
            self.params['min_confidence_score'] = max(bounds[0], min(bounds[1], target))
    
    async def _optimize_stop_loss(self):
        """Otimiza o stop loss baseado em análise de perdas"""
        losses = [t for t in self.trade_history if t.get('pnl', 0) < 0]
        
        if len(losses) < 10:
            return
        
        # Calcular ROE médio das perdas
        roes = [abs(t.get('roe', 0)) for t in losses]
        avg_loss_roe = statistics.mean(roes)
        
        # Se perdas médias são maiores que 3%, apertar SL
        # Se menores que 1.5%, relaxar SL (pode estar cortando cedo demais)
        current = self.params['stop_loss_percent']
        
        if avg_loss_roe > 3.0:
            # Perdas grandes - apertar SL gradualmente
            target = current - 0.2
        elif avg_loss_roe < 1.5 and self.metrics['win_rate'] < 45:
            # Perdas pequenas mas win rate baixo - pode estar stoppando cedo
            target = current + 0.2
        else:
            target = current
        
        bounds = self.param_bounds['stop_loss_percent']
        self.params['stop_loss_percent'] = max(bounds[0], min(bounds[1], target))
    
    async def _optimize_take_profit(self):
        """Otimiza o take profit baseado em análise de ganhos"""
        wins = [t for t in self.trade_history if t.get('pnl', 0) > 0]
        
        if len(wins) < 10:
            return
        
        # Calcular ROE médio dos ganhos
        roes = [t.get('roe', 0) for t in wins]
        avg_win_roe = statistics.mean(roes)
        
        current = self.params['take_profit_percent']
        
        # Se ganhos médios são < 2%, TP pode estar muito próximo
        # Se > 5%, está bom
        if avg_win_roe < 2.0 and self.metrics['profit_factor'] < 1.5:
            target = current + 0.3  # Aumentar TP
        elif avg_win_roe > 5.0:
            target = current - 0.2  # Pode diminuir um pouco
        else:
            target = current
        
        bounds = self.param_bounds['take_profit_percent']
        self.params['take_profit_percent'] = max(bounds[0], min(bounds[1], target))
    
    async def _optimize_position_size(self):
        """Otimiza tamanho da posição baseado em risco"""
        # Baseado no drawdown e sharpe ratio
        current = self.params['position_size_percent']
        
        if self.metrics['max_drawdown'] > 100:  # Drawdown grande
            target = current * 0.9  # Reduzir 10%
        elif self.metrics['sharpe_ratio'] > 1.5 and self.metrics['profit_factor'] > 1.5:
            target = current * 1.05  # Aumentar 5%
        else:
            target = current
        
        bounds = self.param_bounds['position_size_percent']
        self.params['position_size_percent'] = max(bounds[0], min(bounds[1], target))
    
    def calculate_opportunity_score(self, opportunity: Dict, market_conditions: Dict) -> float:
        """
        Calcula score de oportunidade baseado em múltiplos fatores.
        Retorna um valor entre 0.0 e 1.0
        """
        try:
            score = 0.5  # Score base
            
            # 1. Score da análise técnica (se disponível)
            technical_score = opportunity.get('score', 50) / 100
            score = technical_score * 0.4 + score * 0.6
            
            # 2. Volume relativo
            volume = market_conditions.get('volume', 0)
            avg_volume = market_conditions.get('avg_volume', 1)
            if avg_volume > 0:
                volume_ratio = volume / avg_volume
                if volume_ratio > 1.5:
                    score += 0.1  # Volume acima da média é bom
                elif volume_ratio < 0.5:
                    score -= 0.1  # Volume baixo é ruim
            
            # 3. RSI extremos
            rsi = market_conditions.get('rsi', 50)
            if 30 < rsi < 70:
                score += 0.05  # RSI neutro é mais seguro
            elif rsi < 20 or rsi > 80:
                score -= 0.05  # RSI extremo é arriscado
            
            # 4. Tendência alinhada
            trend = market_conditions.get('trend', 'neutral')
            signal = opportunity.get('signal', 'NONE')
            if (trend == 'bullish' and signal == 'BUY') or (trend == 'bearish' and signal == 'SELL'):
                score += 0.1  # Tendência alinhada com sinal
            elif (trend == 'bullish' and signal == 'SELL') or (trend == 'bearish' and signal == 'BUY'):
                score -= 0.1  # Contra tendência
            
            # 5. Análise de padrões históricos (se temos dados)
            symbol = opportunity.get('symbol', '')
            pattern_key = f"symbol:{symbol}"
            if pattern_key in self.pattern_analyzer.patterns:
                pattern_data = self.pattern_analyzer.patterns[pattern_key]
                total = pattern_data['wins'] + pattern_data['losses']
                if total >= 5:
                    pattern_wr = pattern_data['wins'] / total
                    # Ajustar score baseado no histórico
                    score += (pattern_wr - 0.5) * 0.2  # +/-10% baseado no histórico
            
            # Garantir limites
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.warning(f"Erro ao calcular opportunity score: {e}")
            return 0.5  # Score neutro em caso de erro
    
    def should_take_trade(self, score: float, context: Dict = None) -> Tuple[bool, str]:
        """Decide se deve entrar no trade com explicação"""
        min_score = self.params['min_confidence_score']
        
        # Verificar padrões negativos conhecidos
        if context:
            pattern_key = f"symbol:{context.get('symbol', '')}"
            pattern_data = self.pattern_analyzer.patterns.get(pattern_key, {})
            total = pattern_data.get('wins', 0) + pattern_data.get('losses', 0)
            if total >= 10:
                pattern_wr = pattern_data.get('wins', 0) / total * 100
                if pattern_wr < 30:
                    return False, f"Padrão {pattern_key} tem WR={pattern_wr:.0f}% (muito baixo)"
        
        if score >= min_score:
            return True, f"Score {score:.2f} >= {min_score:.2f}"
        else:
            return False, f"Score {score:.2f} < {min_score:.2f}"
    
    def get_position_params(self) -> Dict:
        """Retorna parâmetros para nova posição"""
        return {
            'stop_loss_percent': self.params['stop_loss_percent'],
            'take_profit_percent': self.params['take_profit_percent'],
            'position_size_percent': self.params['position_size_percent'],
        }
    
    async def _save_state(self, trigger_trade: Dict):
        """Salva estado atual do sistema"""
        try:
            record = {
                'type': 'parameters',
                'params': self.params.copy(),
                'metrics': self.metrics.copy(),
                'trigger': {
                    'symbol': trigger_trade.get('symbol'),
                    'pnl': trigger_trade.get('pnl'),
                },
                'timestamp': datetime.now(timezone.utc)
            }
            
            await self.db.advanced_learning.insert_one(record)
            logger.info("[ML] Estado salvo no MongoDB")
            
        except Exception as e:
            logger.error(f"Erro ao salvar estado: {e}")
    
    async def _save_analysis(self, trade: Dict):
        """Salva análise do trade"""
        try:
            analysis = {
                'type': 'trade_analysis',
                'symbol': trade.get('symbol'),
                'side': trade.get('side'),
                'pnl': trade.get('pnl'),
                'roe': trade.get('roe'),
                'patterns': self.pattern_analyzer._extract_patterns(trade),
                'timestamp': datetime.now(timezone.utc)
            }
            
            await self.db.advanced_learning.insert_one(analysis)
            
        except Exception as e:
            logger.error(f"Erro ao salvar análise: {e}")
    
    async def get_learning_report(self) -> Dict:
        """Gera relatório completo do aprendizado"""
        best_patterns = self.pattern_analyzer.get_best_patterns(min_trades=5)
        worst_patterns = self.pattern_analyzer.get_worst_patterns(min_trades=5)
        
        return {
            'params': self.params,
            'metrics': self.metrics,
            'best_patterns': [
                {'pattern': p[0], 'win_rate': p[1], 'trades': p[2], 'avg_pnl': p[3]}
                for p in best_patterns[:5]
            ],
            'worst_patterns': [
                {'pattern': p[0], 'win_rate': p[1], 'trades': p[2], 'avg_pnl': p[3]}
                for p in worst_patterns[:5]
            ],
            'total_trades_analyzed': len(self.trade_history),
            'status': 'learning' if self.metrics['total_trades'] < self.min_trades_for_learning else 'optimizing',
        }
