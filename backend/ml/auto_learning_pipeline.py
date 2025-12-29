"""
Pipeline de Aprendizado Automatico
Integra: Limpeza -> Coleta -> Dataset -> Treinamento -> Validacao
"""

import os
import sys
import logging
from datetime import datetime, timezone
from typing import Dict, Optional
import schedule
import time

# Adicionar path do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.data_cleaner import DataCleaner
from ml.data_collector import OHLCVCollector
from ml.dataset_generator import DatasetGenerator
from ml.model_trainer import ModelTrainer

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


class AutoLearningPipeline:
    """Pipeline automatico de aprendizado"""

    def __init__(
        self,
        days_history: int = 14,
        min_win_rate_improvement: float = 2.0,  # Minimo 2% melhoria para deploy
        min_pnl_improvement: float = 5.0,       # Minimo 5% PnL melhoria
        auto_deploy: bool = False               # Deploy automatico se melhorar
    ):
        self.days_history = days_history
        self.min_win_rate_improvement = min_win_rate_improvement
        self.min_pnl_improvement = min_pnl_improvement
        self.auto_deploy = auto_deploy

        self.last_run = None
        self.last_metrics = {}
        self.run_history = []

    def run_full_pipeline(self) -> Dict:
        """Executa pipeline completo"""

        logger.info("=" * 60)
        logger.info("PIPELINE DE APRENDIZADO AUTOMATICO")
        logger.info("=" * 60)

        start_time = datetime.now(timezone.utc)
        results = {
            'started_at': start_time.isoformat(),
            'steps': {}
        }

        try:
            # === PASSO 1: LIMPEZA ===
            logger.info("\n[PASSO 1/5] Limpando dados antigos...")
            results['steps']['cleanup'] = self._run_cleanup()

            # === PASSO 2: COLETA ===
            logger.info("\n[PASSO 2/5] Coletando dados OHLCV...")
            results['steps']['collection'] = self._run_collection()

            # === PASSO 3: GERACAO DATASET ===
            logger.info("\n[PASSO 3/5] Gerando dataset rotulado...")
            results['steps']['dataset'] = self._run_dataset_generation()

            # === PASSO 4: TREINAMENTO ===
            logger.info("\n[PASSO 4/5] Treinando modelo...")
            results['steps']['training'] = self._run_training()

            # === PASSO 5: VALIDACAO ===
            logger.info("\n[PASSO 5/5] Validando modelo...")
            results['steps']['validation'] = self._run_validation(results['steps']['training'])

            # Resultado final
            results['status'] = 'success'
            results['should_deploy'] = results['steps']['validation'].get('approved', False)

        except Exception as e:
            logger.error(f"Erro no pipeline: {e}")
            results['status'] = 'error'
            results['error'] = str(e)

        results['finished_at'] = datetime.now(timezone.utc).isoformat()
        results['duration_seconds'] = (datetime.now(timezone.utc) - start_time).total_seconds()

        self.last_run = start_time
        self.last_metrics = results.get('steps', {}).get('training', {})
        self.run_history.append(results)

        # Manter apenas ultimas 10 execucoes
        if len(self.run_history) > 10:
            self.run_history = self.run_history[-10:]

        self._print_summary(results)

        return results

    def _run_cleanup(self) -> Dict:
        """Executa limpeza de dados"""
        cleaner = DataCleaner()

        stats_before = cleaner.get_storage_stats()
        cleanup_results = cleaner.clean_all()
        orphan_results = cleaner.clean_orphaned_data()
        stats_after = cleaner.get_storage_stats()

        total_deleted = sum(r.get('deleted', 0) for r in cleanup_results if r.get('status') == 'cleaned')

        return {
            'total_deleted': total_deleted,
            'orphans_removed': orphan_results.get('orphans_removed', 0),
            'stats_before': stats_before,
            'stats_after': stats_after
        }

    def _run_collection(self) -> Dict:
        """Executa coleta de dados"""
        collector = OHLCVCollector(days_back=self.days_history)

        results = collector.collect_all()
        stats = collector.get_stats()

        collector.close()

        return {
            'total_candles': results['total_candles'],
            'symbols_collected': len(results['symbols']),
            'errors': len(results.get('errors', [])),
            'stats': stats
        }

    def _run_dataset_generation(self) -> Dict:
        """Executa geracao de dataset"""
        generator = DatasetGenerator()

        dataset = generator.generate_full_dataset(timeframe='15m')

        if dataset.empty:
            return {'error': 'Dataset vazio', 'samples': 0}

        generator.save_dataset(dataset, 'training_data')
        generator.close()

        return {
            'samples': len(dataset),
            'win_rate': dataset['is_win'].mean() * 100,
            'avg_pnl': dataset['pnl_pct'].mean(),
            'symbols': dataset['symbol'].nunique()
        }

    def _run_training(self) -> Dict:
        """Executa treinamento"""
        trainer = ModelTrainer()

        metrics = trainer.train(
            dataset_name='training_data',
            model_type='random_forest',
            test_size=0.2
        )

        if 'error' not in metrics:
            trainer.save_model('signal_filter')

        trainer.close()

        return metrics

    def _run_validation(self, training_metrics: Dict) -> Dict:
        """Valida se modelo deve ser deployado"""

        if 'error' in training_metrics:
            return {'approved': False, 'reason': 'Erro no treinamento'}

        win_rate_improvement = (
            training_metrics.get('win_rate_with_model', 0) -
            training_metrics.get('win_rate_without_model', 0)
        )

        pnl_improvement = training_metrics.get('pnl_improvement', 0)

        # Criterios de aprovacao
        checks = {
            'win_rate_improved': win_rate_improvement >= self.min_win_rate_improvement,
            'pnl_improved': pnl_improvement >= self.min_pnl_improvement,
            'min_samples': training_metrics.get('test_samples', 0) >= 100,
            'reasonable_accuracy': training_metrics.get('accuracy', 0) >= 0.52,
            'not_overfitting': training_metrics.get('accuracy', 0) <= 0.85
        }

        approved = all(checks.values())

        result = {
            'approved': approved,
            'checks': checks,
            'win_rate_improvement': win_rate_improvement,
            'pnl_improvement': pnl_improvement
        }

        if approved:
            result['reason'] = 'Modelo aprovado para deploy'
            if self.auto_deploy:
                result['auto_deployed'] = True
                logger.info("[Validation] Modelo deployado automaticamente!")
        else:
            failed_checks = [k for k, v in checks.items() if not v]
            result['reason'] = f"Falhou em: {', '.join(failed_checks)}"

        return result

    def _print_summary(self, results: Dict):
        """Imprime resumo do pipeline"""

        print("\n" + "=" * 60)
        print("RESUMO DO PIPELINE")
        print("=" * 60)

        steps = results.get('steps', {})

        # Limpeza
        cleanup = steps.get('cleanup', {})
        print(f"\n[Limpeza]")
        print(f"  Documentos removidos: {cleanup.get('total_deleted', 0)}")

        # Coleta
        collection = steps.get('collection', {})
        print(f"\n[Coleta]")
        print(f"  Velas coletadas: {collection.get('total_candles', 0)}")
        print(f"  Simbolos: {collection.get('symbols_collected', 0)}")

        # Dataset
        dataset = steps.get('dataset', {})
        print(f"\n[Dataset]")
        print(f"  Amostras: {dataset.get('samples', 0)}")
        print(f"  Win Rate base: {dataset.get('win_rate', 0):.1f}%")

        # Treinamento
        training = steps.get('training', {})
        if 'error' not in training:
            print(f"\n[Treinamento]")
            print(f"  Accuracy: {training.get('accuracy', 0):.2%}")
            print(f"  Win Rate SEM modelo: {training.get('win_rate_without_model', 0):.1f}%")
            print(f"  Win Rate COM modelo: {training.get('win_rate_with_model', 0):.1f}%")
            print(f"  PnL melhoria: {training.get('pnl_improvement', 0):.2f}%")

        # Validacao
        validation = steps.get('validation', {})
        print(f"\n[Validacao]")
        print(f"  Aprovado: {'SIM' if validation.get('approved') else 'NAO'}")
        print(f"  Motivo: {validation.get('reason', 'N/A')}")

        # Status final
        print("\n" + "-" * 60)
        print(f"Status: {results.get('status', 'unknown').upper()}")
        print(f"Duracao: {results.get('duration_seconds', 0):.1f} segundos")
        print("=" * 60)


def run_pipeline():
    """CLI para executar pipeline"""
    import argparse

    parser = argparse.ArgumentParser(description='Pipeline de Aprendizado Automatico')
    parser.add_argument('--days', type=int, default=14, help='Dias de historico')
    parser.add_argument('--auto-deploy', action='store_true', help='Deploy automatico')
    parser.add_argument('--schedule', type=int, help='Rodar a cada N horas')

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    pipeline = AutoLearningPipeline(
        days_history=args.days,
        auto_deploy=args.auto_deploy
    )

    if args.schedule:
        print(f"\nAgendado para rodar a cada {args.schedule} horas")
        print("Pressione Ctrl+C para parar\n")

        # Rodar imediatamente
        pipeline.run_full_pipeline()

        # Agendar proximas execucoes
        schedule.every(args.schedule).hours.do(pipeline.run_full_pipeline)

        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        pipeline.run_full_pipeline()


if __name__ == '__main__':
    run_pipeline()
