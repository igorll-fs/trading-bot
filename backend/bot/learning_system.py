"""
Sistema de Aprendizado do Bot - Machine Learning Simplificado
Aprende com cada trade e ajusta parametros automaticamente
"""

import logging
import os
import statistics
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class BotLearningSystem:
    """Sistema que aprende com trades e melhora performance"""
    
    def __init__(self, db):
        self.db = db
        mode = os.getenv("BOT_LEARNING_MODE", "active").strip().lower()
        if mode not in {"active", "observe", "disabled"}:
            mode = "active"
        self.mode = mode
        self.observe_only = self.mode == "observe"
        self.learning_enabled = self.mode != "disabled"
        self.rollback_threshold = float(os.getenv("LEARNING_ROLLBACK_THRESHOLD", "10"))
        
        # MELHORIA: Parâmetros de suavização para evitar oscilações
        self.smoothing_factor = float(os.getenv("LEARNING_SMOOTHING_FACTOR", "0.15"))  # EMA alpha
        self.min_trades_for_adjustment = int(os.getenv("LEARNING_MIN_TRADES", "20"))  # Janela mínima
        
        # Parametros que podem ser ajustados
        self.adjustable_params = {
            'min_confidence_score': 0.5,  # Score minimo para entrar em trade
            'stop_loss_multiplier': 1.0,   # Multiplicador do stop loss
            'take_profit_multiplier': 1.0, # Multiplicador do take profit
            'position_size_multiplier': 1.0, # Multiplicador do tamanho da posicao
        }
        self.param_bounds = {
            'min_confidence_score': (0.3, 0.9),
            'stop_loss_multiplier': (0.5, 1.2),
            'take_profit_multiplier': (0.5, 1.5),
            'position_size_multiplier': (0.5, 1.5),
        }
        self._last_saved_params = self.adjustable_params.copy()
        self._last_metrics_snapshot = {}
        
        # Metricas de performance
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'avg_profit': 0.0,
            'avg_loss': 0.0,
            'best_conditions': {},
            'worst_conditions': {}
        }
    
    async def initialize(self):
        """Carregar parametros aprendidos anteriormente"""
        try:
            if not self.learning_enabled:
                logger.info("Learning system disabled (BOT_LEARNING_MODE=%s)", self.mode)
                return

            # Buscar ultimos parametros salvos
            learned_params = await self.db.learning_data.find_one(
                {'type': 'parameters'},
                sort=[('timestamp', -1)]
            )
            
            if learned_params:
                # Carregar parametros salvos
                saved_params = learned_params.get('parameters', {})
                if saved_params:
                    self.adjustable_params.update(saved_params)
                
                # Carregar metricas salvas
                saved_metrics = learned_params.get('metrics', {})
                if saved_metrics:
                    self.performance_metrics.update(saved_metrics)
                
                logger.info("APRENDIZADO ANTERIOR RESTAURADO COM SUCESSO!")
                logger.info(f"Total de trades anteriores: {self.performance_metrics.get('total_trades', 0)}")
                logger.info(f"Win Rate historico: {self.performance_metrics.get('win_rate', 0):.1f}%")
                logger.info(f"Confidence Score Minimo: {self.adjustable_params['min_confidence_score']:.2f}")
                logger.info(f"Stop Loss Multiplier: {self.adjustable_params['stop_loss_multiplier']:.2f}x")
                logger.info(f"Take Profit Multiplier: {self.adjustable_params['take_profit_multiplier']:.2f}x")
                logger.info(f"Position Size Multiplier: {self.adjustable_params['position_size_multiplier']:.2f}x")
            else:
                logger.info("Nenhum aprendizado anterior encontrado. Iniciando com parametros padrao.")
                logger.info("O bot vai aprender do zero e salvar seu aprendizado!")
            
            # Atualizar metricas com historico
            await self._update_performance_metrics()
            self._snapshot_parameters()
            
        except Exception as e:
            logger.error(f"Erro ao inicializar sistema de aprendizado: {e}")
    
    async def _update_performance_metrics(self):
        """Atualizar metricas baseado em todos os trades"""
        try:
            # Buscar ultimos 1000 trades (projeção otimizada - só pnl necessário)
            trades = await self.db.trades.find(
                {},
                {"pnl": 1, "_id": 0}
            ).sort('timestamp', -1).limit(1000).to_list(1000)
            
            if not trades:
                return
            
            self.performance_metrics['total_trades'] = len(trades)
            
            # Separar ganhos e perdas
            winning = [t for t in trades if t.get('pnl', 0) > 0]
            losing = [t for t in trades if t.get('pnl', 0) <= 0]
            
            self.performance_metrics['winning_trades'] = len(winning)
            self.performance_metrics['losing_trades'] = len(losing)
            self.performance_metrics['win_rate'] = (len(winning) / len(trades) * 100) if trades else 0
            
            # Calcular medias
            if winning:
                self.performance_metrics['avg_profit'] = statistics.mean([t['pnl'] for t in winning])
            if losing:
                self.performance_metrics['avg_loss'] = statistics.mean([t['pnl'] for t in losing])
            
            logger.info(f"Metricas atualizadas: {self.performance_metrics['total_trades']} trades, Win Rate: {self.performance_metrics['win_rate']:.1f}%")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar metricas: {e}")
    
    def _snapshot_parameters(self):
        self._last_saved_params = self.adjustable_params.copy()
        self._last_metrics_snapshot = self.performance_metrics.copy()
    
    def _update_param(self, name: str, new_value: float, reason: str):
        """Atualiza parametro com suavização EMA e dentro dos limites.
        
        MELHORIA: Usa Exponential Moving Average para suavizar mudanças.
        new_param = alpha * target + (1 - alpha) * current
        
        Isso evita oscilações bruscas e torna o aprendizado mais estável.
        """
        bounds = self.param_bounds.get(name, (0.0, 1.0))
        current = self.adjustable_params.get(name, new_value)
        
        # Aplicar suavização EMA: valor_novo = alpha * target + (1-alpha) * current
        smoothed = self.smoothing_factor * new_value + (1 - self.smoothing_factor) * current
        
        # Aplicar limites após suavização
        clamped = max(bounds[0], min(bounds[1], smoothed))
        
        if self.observe_only:
            if abs(clamped - current) > 0.001:
                logger.info(
                    "OBSERVE-ONLY: %s permaneceria em %.3f (target %.3f -> suavizado %.3f) motivo=%s",
                    name,
                    current,
                    new_value,
                    clamped,
                    reason,
                )
            return current
        
        if abs(clamped - current) > 0.001:  # Só atualiza se houver mudança significativa
            logger.info(
                "Parametro %s: %.3f -> %.3f (target: %.3f, alpha: %.2f) - %s",
                name,
                current,
                clamped,
                new_value,
                self.smoothing_factor,
                reason,
            )
            self.adjustable_params[name] = clamped
        return self.adjustable_params[name]
    
    def _log_parameter_changes(self, before: Dict[str, float]):
        if self.observe_only:
            return
        for key, old_value in before.items():
            new_value = self.adjustable_params.get(key)
            if new_value != old_value:
                logger.debug("Parametro %s: %.2f -> %.2f", key, old_value, new_value)
    
    def _maybe_snapshot(self):
        if self.observe_only:
            return
        current = self.performance_metrics.get('win_rate', 0.0)
        previous = self._last_metrics_snapshot.get('win_rate', current)
        total_trades = self.performance_metrics.get('total_trades', 0)
        if total_trades >= 20 and (previous - current) >= self.rollback_threshold:
            logger.warning(
                "Win rate caiu de %.1f%% para %.1f%% (limite %.1f%%). Retornando parametros anteriores.",
                previous,
                current,
                self.rollback_threshold,
            )
            self.adjustable_params = self._last_saved_params.copy()
        else:
            self._snapshot_parameters()
    
    def calculate_opportunity_score(self, opportunity: Dict, market_conditions: Dict) -> float:
        """
        Calcula score de confianca para uma oportunidade (0.0 a 1.0)
        Baseado em indicadores tecnicos e condicoes de mercado
        """
        try:
            score = 0.5  # Score base
            
            # 1. Analise de Forca do Sinal (30% do score)
            signal_strength = opportunity.get('confidence', 0.5)
            score += (signal_strength - 0.5) * 0.3
            
            # 2. Analise de Volume (20% do score)
            volume = market_conditions.get('volume', 0)
            avg_volume = market_conditions.get('avg_volume', 1)
            if avg_volume > 0:
                volume_ratio = volume / avg_volume
                if volume_ratio > 1.5:  # Volume alto
                    score += 0.2
                elif volume_ratio > 1.2:  # Volume medio
                    score += 0.1
            
            # 3. Analise de Tendencia (30% do score)
            trend = market_conditions.get('trend', 'neutral')
            signal = opportunity.get('signal', '')
            
            if trend == 'uptrend' and signal == 'BUY':
                score += 0.3  # Trade alinhado com tendencia
            elif trend == 'downtrend' and signal == 'SELL':
                score += 0.3
            elif trend == 'neutral':
                score += 0.1  # Tendencia neutra e ok
            else:
                score -= 0.2  # Trade contra a tendencia
            
            # 4. Analise de RSI (20% do score)
            rsi = market_conditions.get('rsi', 50)
            if signal == 'BUY' and rsi < 40:  # Sobrevenda
                score += 0.2
            elif signal == 'SELL' and rsi > 60:  # Sobrecompra
                score += 0.2
            elif 45 <= rsi <= 55:  # RSI neutro
                score += 0.1
            
            # Limitar entre 0 e 1
            score = max(0.0, min(1.0, score))
            
            return score
            
        except Exception as e:
            logger.error(f"Erro ao calcular score: {e}")
            return 0.5
    
    def should_take_trade(self, opportunity_score: float) -> bool:
        """Decide se deve entrar no trade baseado no score"""
        if not self.learning_enabled:
            return opportunity_score >= 0.5

        min_score = self.adjustable_params['min_confidence_score']
        
        should_take = opportunity_score >= min_score
        
        if should_take:
            logger.info(f"Trade aprovado | Score: {opportunity_score:.2f} >= {min_score:.2f}")
        else:
            logger.info(f"Trade rejeitado | Score: {opportunity_score:.2f} < {min_score:.2f}")
        
        return should_take
    
    def adjust_stop_loss(self, base_stop_loss: float, entry_price: float = None) -> float:
        """Ajusta stop loss baseado em aprendizado.
        
        NOTA: O multiplicador ajusta a DISTÂNCIA do SL ao entry, não o preço em si.
        - Multiplicador > 1: SL mais distante (mais risco, menos stops prematuros)
        - Multiplicador < 1: SL mais próximo (menos risco, mais stops prematuros)
        
        Para BUY: SL está ABAIXO do entry
        Para SELL: SL está ACIMA do entry
        """
        if not self.learning_enabled:
            return base_stop_loss
        
        # Se não temos entry_price, não podemos ajustar corretamente
        # Retorna o SL original para evitar bugs
        if entry_price is None:
            logger.warning("adjust_stop_loss chamado sem entry_price - retornando SL original")
            return base_stop_loss

        multiplier = self.adjustable_params['stop_loss_multiplier']
        
        # Calcular a distância original do SL ao entry
        original_distance = abs(entry_price - base_stop_loss)
        
        # Ajustar a distância pelo multiplicador
        adjusted_distance = original_distance * multiplier
        
        # Para BUY, SL está abaixo do entry
        # Para SELL, SL está acima do entry
        # Detectar automaticamente baseado na posição do SL original
        if base_stop_loss < entry_price:
            # BUY - SL abaixo do entry
            adjusted = entry_price - adjusted_distance
        else:
            # SELL - SL acima do entry
            adjusted = entry_price + adjusted_distance
        
        logger.debug(f"SL ajustado: {base_stop_loss:.4f} -> {adjusted:.4f} (dist: {original_distance:.4f} -> {adjusted_distance:.4f}, mult: {multiplier:.2f}x)")
        return round(adjusted, 4)
    
    def adjust_take_profit(self, base_take_profit: float, entry_price: float = None) -> float:
        """Ajusta take profit baseado em aprendizado.
        
        NOTA: O multiplicador ajusta a DISTÂNCIA do TP ao entry, não o preço em si.
        - Multiplicador > 1: TP mais distante (mais lucro potencial, menos trades fechados)
        - Multiplicador < 1: TP mais próximo (menos lucro potencial, mais trades fechados)
        
        Para BUY: TP está ACIMA do entry
        Para SELL: TP está ABAIXO do entry
        """
        if not self.learning_enabled:
            return base_take_profit
        
        # Se não temos entry_price, não podemos ajustar corretamente
        if entry_price is None:
            logger.warning("adjust_take_profit chamado sem entry_price - retornando TP original")
            return base_take_profit

        multiplier = self.adjustable_params['take_profit_multiplier']
        
        # Calcular a distância original do TP ao entry
        original_distance = abs(base_take_profit - entry_price)
        
        # Ajustar a distância pelo multiplicador
        adjusted_distance = original_distance * multiplier
        
        # Para BUY, TP está acima do entry
        # Para SELL, TP está abaixo do entry
        if base_take_profit > entry_price:
            # BUY - TP acima do entry
            adjusted = entry_price + adjusted_distance
        else:
            # SELL - TP abaixo do entry
            adjusted = entry_price - adjusted_distance
        
        logger.debug(f"TP ajustado: {base_take_profit:.4f} -> {adjusted:.4f} (dist: {original_distance:.4f} -> {adjusted_distance:.4f}, mult: {multiplier:.2f}x)")
        return round(adjusted, 4)
    
    def adjust_position_size(self, base_position_size: float) -> float:
        """Ajusta tamanho da posicao baseado em aprendizado"""
        if not self.learning_enabled:
            return base_position_size

        multiplier = self.adjustable_params['position_size_multiplier']
        adjusted = base_position_size * multiplier
        
        logger.debug(f"Position size ajustado: {base_position_size:.2f} -> {adjusted:.2f} (mult: {multiplier:.2f}x)")
        return adjusted
    
    async def learn_from_trade(self, trade: Dict):
        """
        Aprende com um trade fechado e ajusta parametros.
        
        MELHORIA: Só ajusta após min_trades_for_adjustment (default 20) para
        ter amostra estatisticamente relevante. Usa suavização EMA.
        """
        try:
            if not self.learning_enabled:
                logger.debug("Learning disabled - ignorando learn_from_trade")
                return

            pnl = trade.get('pnl', 0)
            roe = trade.get('roe', 0)
            symbol = trade.get('symbol', 'UNKNOWN')
            
            logger.info(f"Aprendendo com trade: {symbol} | PnL: ${pnl:.2f} | ROE: {roe:.2f}%")
            
            # Atualizar metricas
            await self._update_performance_metrics()
            
            total_trades = self.performance_metrics.get('total_trades', 0)
            
            # MELHORIA: Só ajusta parâmetros após ter amostra mínima
            if total_trades < self.min_trades_for_adjustment:
                logger.info(
                    "Coletando dados... (%d/%d trades para iniciar ajustes)",
                    total_trades,
                    self.min_trades_for_adjustment
                )
                # Mesmo sem ajustar, salva análise do trade
                await self._save_trade_analysis(trade)
                return
            
            # REGRA 1: Ajustar Confidence Score baseado em Win Rate
            win_rate = self.performance_metrics['win_rate']
            before_changes = self.adjustable_params.copy()
            
            # Calcular target para confidence score baseado no win rate
            current_confidence = self.adjustable_params['min_confidence_score']
            if win_rate < 40:  # Win rate muito baixo - aumentar exigência
                target_confidence = current_confidence + 0.05
            elif win_rate > 65:  # Win rate muito alto - relaxar um pouco
                target_confidence = current_confidence - 0.02
            else:
                target_confidence = current_confidence  # Manter
            
            if target_confidence != current_confidence:
                self._update_param(
                    'min_confidence_score',
                    target_confidence,
                    f"Win Rate {win_rate:.1f}%"
                )
            
            # REGRA 2: Ajustar Stop Loss baseado em perdas
            if pnl < 0:  # Trade perdedor
                avg_loss = abs(self.performance_metrics.get('avg_loss', 0))
                current_sl_mult = self.adjustable_params['stop_loss_multiplier']
                if avg_loss > 50:  # Perdas muito grandes - apertar SL
                    self._update_param(
                        'stop_loss_multiplier',
                        current_sl_mult - 0.05,
                        "Perdas grandes detectadas"
                    )
            
            # REGRA 3: Ajustar Take Profit baseado em ganhos
            if pnl > 0:  # Trade vencedor
                avg_profit = self.performance_metrics.get('avg_profit', 0)
                current_tp_mult = self.adjustable_params['take_profit_multiplier']
                
                if avg_profit < 30:  # Ganhos muito pequenos - esticar TP
                    self._update_param(
                        'take_profit_multiplier',
                        current_tp_mult + 0.05,
                        "Ganhos pequenos detectados"
                    )
            
            # REGRA 4: Ajustar tamanho da posicao baseado em volatilidade
            if self.performance_metrics['total_trades'] >= 10:
                # Se ultimos 5 trades foram muito volateis, reduzir position size
                recent_trades = await self.db.trades.find(
                    {},
                    {"pnl": 1, "_id": 0}
                ).sort('closed_at', -1).limit(5).to_list(5)
                if recent_trades:
                    pnls = [abs(t.get('pnl', 0)) for t in recent_trades]
                    volatility = statistics.stdev(pnls) if len(pnls) > 1 else 0
                    
                    if volatility > 50:  # Alta volatilidade
                        self._update_param(
                            'position_size_multiplier',
                            self.adjustable_params['position_size_multiplier'] - 0.05,
                            "Alta volatilidade detectada"
                        )
                    elif volatility < 20 and pnl > 0:
                        self._update_param(
                            'position_size_multiplier',
                            self.adjustable_params['position_size_multiplier'] + 0.02,
                            "Baixa volatilidade detectada"
                        )
            
            self._log_parameter_changes(before_changes)
            
            if not self.observe_only:
                # Salvar parametros aprendidos
                await self._save_learned_parameters(trade)
            
            # Salvar analise do trade
            await self._save_trade_analysis(trade)
            
            self._maybe_snapshot()
            logger.info("Aprendizado concluido e salvo")
            
        except Exception as e:
            logger.error(f"Erro ao aprender com trade: {e}")
    
    async def _save_learned_parameters(self, trigger_trade: Dict):
        """Salvar parametros ajustados no MongoDB"""
        try:
            learning_record = {
                'type': 'parameters',
                'parameters': self.adjustable_params.copy(),
                'metrics': self.performance_metrics.copy(),
                'total_adjustments': self.performance_metrics.get('total_trades', 0),
                'trigger_trade': {
                    'symbol': trigger_trade.get('symbol'),
                    'pnl': trigger_trade.get('pnl'),
                    'roe': trigger_trade.get('roe')
                },
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Inserir novo registro (mantem historico)
            await self.db.learning_data.insert_one(learning_record)
            
            logger.info("Parametros aprendidos salvos no MongoDB")
            
        except Exception as e:
            logger.error(f"Erro ao salvar parametros: {e}")
    
    async def _save_trade_analysis(self, trade: Dict):
        """Salvar analise detalhada do trade"""
        try:
            pnl = trade.get('pnl', 0)
            roe = trade.get('roe', 0)
            
            # CORRIGIDO: Adicionar campo 'won' e 'ml_score' para o endpoint usar
            analysis = {
                'type': 'trade_analysis',
                'trade_id': trade.get('_id'),
                'symbol': trade.get('symbol'),
                'side': trade.get('side'),
                'pnl': pnl,
                'roe': roe,
                'won': pnl > 0,  # CAMPO ESSENCIAL para calcular win_rate
                'ml_score': trade.get('confidence_score', 0.0),  # Score ML usado na entrada
                'confidence_score': trade.get('confidence_score', 0.0),  # Compatibilidade
                'entry_price': trade.get('entry_price'),
                'exit_price': trade.get('exit_price'),
                'duration_seconds': self._calculate_trade_duration(trade),
                'lessons_learned': self._extract_lessons(trade),
                'timestamp': datetime.now(timezone.utc).isoformat(),  # CORRIGIDO: era 'analyzed_at'
                'analyzed_at': datetime.now(timezone.utc).isoformat()
            }
            
            await self.db.learning_data.insert_one(analysis)
            logger.debug(f"Análise salva: {trade.get('symbol')} - Won={pnl > 0} - ML Score={trade.get('confidence_score', 0.0):.2f}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar analise: {e}")
    
    def _calculate_trade_duration(self, trade: Dict) -> int:
        """Calcular duracao do trade em segundos"""
        try:
            opened = datetime.fromisoformat(trade['opened_at'].replace('Z', '+00:00'))
            closed = datetime.fromisoformat(trade['closed_at'].replace('Z', '+00:00'))
            duration = (closed - opened).total_seconds()
            return int(duration)
        except:
            return 0
    
    def _extract_lessons(self, trade: Dict) -> Dict:
        """Extrair licoes do trade"""
        lessons = {}
        
        pnl = trade.get('pnl', 0)
        roe = trade.get('roe', 0)
        
        # Licao sobre resultado
        if pnl > 0:
            lessons['result'] = 'Vencedor'
            if roe > 10:
                lessons['quality'] = 'Excelente trade'
            elif roe > 5:
                lessons['quality'] = 'Bom trade'
            else:
                lessons['quality'] = 'Trade fraco'
        else:
            lessons['result'] = 'Perdedor'
            if abs(roe) > 5:
                lessons['quality'] = 'Perda grande - revisar estrategia'
            else:
                lessons['quality'] = 'Perda aceitavel - stop loss funcionou'
        
        # Licao sobre duracao
        duration = self._calculate_trade_duration(trade)
        if duration < 300:  # Menos de 5 minutos
            lessons['timing'] = 'Trade muito rapido'
        elif duration > 3600:  # Mais de 1 hora
            lessons['timing'] = 'Trade demorado - considerar TP mais proximo'
        else:
            lessons['timing'] = 'Duracao adequada'
        
        return lessons
    
    async def get_learning_stats(self) -> Dict:
        """Retornar estatisticas de aprendizado"""
        return {
            'parameters': self.adjustable_params,
            'metrics': self.performance_metrics,
            'total_learning_records': await self.db.learning_data.count_documents({'type': 'bot_parameters'}),
            'total_analyses': await self.db.learning_data.count_documents({'type': 'trade_analysis'})
        }
