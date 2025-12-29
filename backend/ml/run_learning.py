#!/usr/bin/env python3
"""
Script principal para rodar o sistema de aprendizado ML

Uso:
    python ml/run_learning.py              # Pipeline completo
    python ml/run_learning.py --collect    # Apenas coletar dados
    python ml/run_learning.py --train      # Apenas treinar
    python ml/run_learning.py --clean      # Apenas limpar dados antigos
    python ml/run_learning.py --status     # Ver status do sistema
"""

import os
import sys
import argparse
import logging

# Adicionar path do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def check_dependencies():
    """Verifica dependencias necessarias"""
    missing = []

    try:
        import sklearn
    except ImportError:
        missing.append('scikit-learn')

    try:
        import pandas
    except ImportError:
        missing.append('pandas')

    try:
        import numpy
    except ImportError:
        missing.append('numpy')

    try:
        import schedule
    except ImportError:
        missing.append('schedule')

    if missing:
        print("ERRO: Dependencias faltando!")
        print(f"Instale com: pip install {' '.join(missing)}")
        return False

    return True


def run_status():
    """Mostra status do sistema ML"""
    from pymongo import MongoClient

    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'trading_bot')
    client = MongoClient(mongo_url)
    db = client[db_name]

    print("\n" + "=" * 60)
    print("STATUS DO SISTEMA DE APRENDIZADO ML")
    print("=" * 60)

    # Dados OHLCV
    ohlcv_count = db.ohlcv_data.count_documents({})
    ohlcv_symbols = db.ohlcv_data.distinct('symbol')
    print(f"\n[Dados OHLCV]")
    print(f"  Total de velas: {ohlcv_count}")
    print(f"  Simbolos: {len(ohlcv_symbols)}")

    # Dataset de treinamento
    training_count = db.ml_training_data.count_documents({})
    print(f"\n[Dataset de Treinamento]")
    print(f"  Amostras: {training_count}")

    # Modelo
    model = db.ml_models.find_one({'name': 'signal_filter'})
    print(f"\n[Modelo ML]")
    if model:
        metrics = model.get('metrics', {})
        print(f"  Status: CARREGADO")
        print(f"  Accuracy: {metrics.get('accuracy', 0):.2%}")
        print(f"  Win Rate melhoria: {metrics.get('win_rate_with_model', 0) - metrics.get('win_rate_without_model', 0):.1f}%")
        print(f"  Treinado em: {metrics.get('trained_at', 'N/A')}")
    else:
        print(f"  Status: NAO TREINADO")

    # Trades
    trades_count = db.trades.count_documents({})
    print(f"\n[Trades Historicos]")
    print(f"  Total: {trades_count}")

    print("\n" + "=" * 60)

    client.close()


def run_collect(days: int = 14):
    """Coleta dados OHLCV"""
    from ml.data_collector import OHLCVCollector

    print("\n[COLETA DE DADOS]")
    collector = OHLCVCollector(days_back=days)
    results = collector.collect_all()
    collector.close()

    print(f"Coletadas {results['total_candles']} velas de {len(results['symbols'])} simbolos")


def run_clean():
    """Limpa dados antigos"""
    from ml.data_cleaner import DataCleaner

    print("\n[LIMPEZA DE DADOS]")
    cleaner = DataCleaner()
    results = cleaner.clean_all()

    total = sum(r.get('deleted', 0) for r in results if r.get('status') == 'cleaned')
    print(f"Removidos {total} documentos antigos")


def run_generate():
    """Gera dataset de treinamento"""
    from ml.dataset_generator import DatasetGenerator

    print("\n[GERACAO DE DATASET]")
    generator = DatasetGenerator()
    dataset = generator.generate_full_dataset()

    if not dataset.empty:
        generator.save_dataset(dataset)
        print(f"Dataset gerado: {len(dataset)} amostras")
        print(f"Win Rate base: {dataset['is_win'].mean()*100:.1f}%")
    else:
        print("ERRO: Dataset vazio!")

    generator.close()


def run_train():
    """Treina modelo"""
    from ml.model_trainer import ModelTrainer

    print("\n[TREINAMENTO]")
    trainer = ModelTrainer()
    metrics = trainer.train()

    if 'error' not in metrics:
        trainer.save_model('signal_filter')
        print(f"Modelo treinado com accuracy: {metrics['accuracy']:.2%}")
        print(f"Win Rate melhorou: {metrics.get('win_rate_with_model', 0) - metrics.get('win_rate_without_model', 0):.1f}%")
    else:
        print(f"ERRO: {metrics['error']}")

    trainer.close()


def run_full_pipeline(days: int = 14):
    """Executa pipeline completo"""
    from ml.auto_learning_pipeline import AutoLearningPipeline

    pipeline = AutoLearningPipeline(days_history=days)
    results = pipeline.run_full_pipeline()

    return results


def main():
    parser = argparse.ArgumentParser(description='Sistema de Aprendizado ML')
    parser.add_argument('--status', action='store_true', help='Mostrar status')
    parser.add_argument('--collect', action='store_true', help='Apenas coletar dados')
    parser.add_argument('--clean', action='store_true', help='Apenas limpar dados antigos')
    parser.add_argument('--generate', action='store_true', help='Apenas gerar dataset')
    parser.add_argument('--train', action='store_true', help='Apenas treinar modelo')
    parser.add_argument('--days', type=int, default=14, help='Dias de historico')
    parser.add_argument('--schedule', type=int, help='Rodar pipeline a cada N horas')

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    if not check_dependencies():
        sys.exit(1)

    if args.status:
        run_status()
    elif args.collect:
        run_collect(args.days)
    elif args.clean:
        run_clean()
    elif args.generate:
        run_generate()
    elif args.train:
        run_train()
    elif args.schedule:
        import schedule
        import time

        print(f"\nAgendado para rodar a cada {args.schedule} horas")
        print("Pressione Ctrl+C para parar\n")

        run_full_pipeline(args.days)
        schedule.every(args.schedule).hours.do(lambda: run_full_pipeline(args.days))

        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        # Pipeline completo
        run_full_pipeline(args.days)


if __name__ == '__main__':
    main()
