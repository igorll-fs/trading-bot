"""
Limpeza Automatica de Dados Antigos
Remove dados obsoletos do MongoDB para manter performance
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List
from pymongo import MongoClient

logger = logging.getLogger(__name__)


class DataCleaner:
    """Limpa dados antigos automaticamente"""

    # Configuracoes de retencao (em dias)
    # None = NUNCA apagar (dados importantes)
    RETENTION_RULES = {
        'trades': None,            # NUNCA apagar - historico de trading importante
        'positions': None,         # NUNCA apagar - historico de posicoes
        'configs': None,           # NUNCA apagar - configuracoes
        'learning_data': 30,       # Dados de aprendizado antigo: 30 dias
        'advanced_learning': 30,   # ML avancado antigo: 30 dias
        'ohlcv_cache': 14,         # Cache de velas temporario: 14 dias
        'ohlcv_data': 30,          # Dados OHLCV para ML: 30 dias (recoletamos)
        'ml_training_data': 60,    # Datasets de treino: 60 dias
    }

    def __init__(self, mongo_url: str = None, db_name: str = None):
        self.mongo_url = mongo_url or os.getenv('MONGO_URL', 'mongodb://localhost:27017')
        self.db_name = db_name or os.getenv('DB_NAME', 'trading_bot')

    def _get_sync_client(self):
        return MongoClient(self.mongo_url)

    def _get_cutoff_date(self, days: int) -> datetime:
        return datetime.now(timezone.utc) - timedelta(days=days)

    def clean_collection(self, collection_name: str, date_field: str = 'timestamp') -> Dict:
        """Limpa uma colecao especifica baseado nas regras de retencao"""
        retention_days = self.RETENTION_RULES.get(collection_name)

        if retention_days is None:
            return {'collection': collection_name, 'status': 'skipped', 'reason': 'no retention rule'}

        cutoff = self._get_cutoff_date(retention_days)

        client = self._get_sync_client()
        try:
            db = client[self.db_name]
            collection = db[collection_name]

            # Contar antes
            total_before = collection.count_documents({})

            # Determinar campo de data correto
            if collection_name == 'trades':
                date_field = 'closed_at'
            elif collection_name in ['learning_data', 'advanced_learning', 'ml_training_data']:
                date_field = 'timestamp'
            elif collection_name == 'ohlcv_cache':
                date_field = 'cached_at'

            # Deletar documentos antigos
            result = collection.delete_many({
                date_field: {'$lt': cutoff}
            })

            deleted = result.deleted_count
            total_after = collection.count_documents({})

            logger.info(f"[Cleaner] {collection_name}: {deleted} documentos removidos ({total_before} -> {total_after})")

            return {
                'collection': collection_name,
                'status': 'cleaned',
                'deleted': deleted,
                'before': total_before,
                'after': total_after,
                'retention_days': retention_days,
                'cutoff_date': cutoff.isoformat()
            }

        except Exception as e:
            logger.error(f"[Cleaner] Erro ao limpar {collection_name}: {e}")
            return {'collection': collection_name, 'status': 'error', 'error': str(e)}
        finally:
            client.close()

    def clean_all(self) -> List[Dict]:
        """Limpa todas as colecoes com regras de retencao"""
        results = []

        logger.info("[Cleaner] Iniciando limpeza automatica...")

        for collection_name in self.RETENTION_RULES.keys():
            result = self.clean_collection(collection_name)
            results.append(result)

        # Resumo
        total_deleted = sum(r.get('deleted', 0) for r in results if r.get('status') == 'cleaned')
        logger.info(f"[Cleaner] Limpeza concluida. Total removido: {total_deleted} documentos")

        return results

    def clean_orphaned_data(self) -> Dict:
        """Remove dados orfaos (trades sem posicao correspondente, etc)"""
        client = self._get_sync_client()
        try:
            db = client[self.db_name]

            orphans_removed = 0

            # Remover learning_data de trades que nao existem mais
            trade_ids = set(str(t['_id']) for t in db.trades.find({}, {'_id': 1}))

            if trade_ids:
                result = db.learning_data.delete_many({
                    'type': 'trade_analysis',
                    'trade_id': {'$nin': list(trade_ids)}
                })
                orphans_removed += result.deleted_count

            logger.info(f"[Cleaner] Dados orfaos removidos: {orphans_removed}")

            return {'orphans_removed': orphans_removed}

        except Exception as e:
            logger.error(f"[Cleaner] Erro ao limpar dados orfaos: {e}")
            return {'error': str(e)}
        finally:
            client.close()

    def get_storage_stats(self) -> Dict:
        """Retorna estatisticas de armazenamento"""
        client = self._get_sync_client()
        try:
            db = client[self.db_name]

            stats = {}
            for collection_name in self.RETENTION_RULES.keys():
                try:
                    count = db[collection_name].count_documents({})
                    stats[collection_name] = {
                        'count': count,
                        'retention_days': self.RETENTION_RULES.get(collection_name)
                    }
                except:
                    stats[collection_name] = {'count': 0, 'error': 'collection not found'}

            return stats

        finally:
            client.close()


def run_cleanup():
    """Funcao para rodar limpeza via CLI"""
    logging.basicConfig(level=logging.INFO)

    cleaner = DataCleaner()

    print("\n" + "=" * 60)
    print("LIMPEZA AUTOMATICA DE DADOS")
    print("=" * 60)

    # Stats antes
    print("\nEstatisticas antes da limpeza:")
    stats = cleaner.get_storage_stats()
    for name, data in stats.items():
        print(f"  {name}: {data.get('count', 0)} documentos")

    # Limpar
    print("\nExecutando limpeza...")
    results = cleaner.clean_all()

    # Limpar orfaos
    print("\nLimpando dados orfaos...")
    orphan_result = cleaner.clean_orphaned_data()

    # Resumo
    print("\n" + "-" * 60)
    print("RESUMO:")
    for r in results:
        if r.get('status') == 'cleaned' and r.get('deleted', 0) > 0:
            print(f"  {r['collection']}: {r['deleted']} removidos")

    if orphan_result.get('orphans_removed', 0) > 0:
        print(f"  orfaos: {orphan_result['orphans_removed']} removidos")

    print("\nLimpeza concluida!")


if __name__ == '__main__':
    run_cleanup()
