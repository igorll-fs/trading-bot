"""
Rotas de Machine Learning / Sistema de Aprendizado.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["Learning"])


def create_learning_router(db, get_bot_func):
    """Factory function para criar router com dependências injetadas."""
    
    @router.get("/learning/stats")
    async def get_learning_stats():
        """Retorna estatísticas e parâmetros de machine learning."""
        try:
            bot = await get_bot_func(db)
            
            # CORRIGIDO: Buscar parâmetros do último registro ordenado por timestamp
            params_doc = await db.learning_data.find_one(
                {'type': 'parameters'},
                sort=[('timestamp', -1)]
            )
            
            # Análises de trades (projeção otimizada)
            analyses = await db.learning_data.find(
                {'type': 'trade_analysis'},
                {"_id": 0, "won": 1, "ml_score": 1, "timestamp": 1, "symbol": 1, "adjustments": 1}
            ).sort('timestamp', -1).limit(100).to_list(100)
            
            # Calcular estatísticas dos parâmetros
            if not params_doc:
                params = {
                    'min_confidence_score': 0.6,
                    'stop_loss_multiplier': 1.0,
                    'take_profit_multiplier': 1.0,
                    'position_size_multiplier': 1.0,
                    'total_adjustments': 0
                }
            else:
                # CORRIGIDO: Buscar dentro de 'parameters' sub-dict
                saved_params = params_doc.get('parameters', {})
                params = {
                    'min_confidence_score': saved_params.get('min_confidence_score', 0.6),
                    'stop_loss_multiplier': saved_params.get('stop_loss_multiplier', 1.0),
                    'take_profit_multiplier': saved_params.get('take_profit_multiplier', 1.0),
                    'position_size_multiplier': saved_params.get('position_size_multiplier', 1.0),
                    'total_adjustments': params_doc.get('total_adjustments', 0),
                    'last_updated': params_doc.get('timestamp', 'Never')
                }
            
            # Calcular win rate das análises (CORRIGIDO: usar campo 'won')
            if analyses:
                total_analyzed = len(analyses)
                winners = len([a for a in analyses if a.get('won', False)])  # CORRIGIDO
                win_rate = (winners / total_analyzed * 100) if total_analyzed > 0 else 0
                
                # Média dos scores de confiança (CORRIGIDO: usar 'ml_score')
                scores = [a.get('ml_score', 0) for a in analyses if a.get('ml_score', 0) > 0]
                avg_confidence = sum(scores) / len(scores) if scores else 0
                
                # Histórico de ajustes
                adjustments_history = [
                    {
                        'timestamp': a.get('timestamp'),
                        'symbol': a.get('symbol'),
                        'adjustments': a.get('adjustments', [])
                    }
                    for a in analyses
                    if a.get('adjustments')
                ]
            else:
                total_analyzed = 0
                win_rate = 0
                avg_confidence = 0
                adjustments_history = []
            
            return {
                'status': 'success',
                'current_parameters': params,
                'statistics': {
                    'total_analyzed_trades': total_analyzed,
                    'win_rate': round(win_rate, 2),
                    'average_confidence_score': round(avg_confidence, 3),
                    'total_parameter_adjustments': params['total_adjustments']
                },
                'recent_adjustments': adjustments_history[:10],
                'is_learning': bot.is_running
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return router
