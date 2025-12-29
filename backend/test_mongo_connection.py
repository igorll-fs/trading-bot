"""
Teste de conexao MongoDB
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    print("=" * 50)
    print("TESTE DE CONEXAO MONGODB")
    print("=" * 50)

    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'trading_bot')

    print(f"\nURL: {mongo_url}")
    print(f"Database: {db_name}")

    # Tentar diferentes URLs
    urls_to_try = [
        mongo_url,
        'mongodb://localhost:27017',
        'mongodb://127.0.0.1:27017',
    ]

    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

    for url in urls_to_try:
        print(f"\nTentando: {url}")
        try:
            client = MongoClient(url, serverSelectionTimeoutMS=5000)
            # Forcar conexao
            client.admin.command('ping')
            print(f"  SUCESSO! Conectado em {url}")

            # Listar databases
            dbs = client.list_database_names()
            print(f"  Databases: {dbs}")

            # Verificar colecoes do trading_bot
            db = client[db_name]
            collections = db.list_collection_names()
            print(f"  Colecoes em '{db_name}': {collections}")

            # Contar documentos
            for col in collections:
                count = db[col].count_documents({})
                print(f"    - {col}: {count} docs")

            client.close()
            return url

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"  FALHOU: {e}")
        except Exception as e:
            print(f"  ERRO: {e}")

    print("\n" + "=" * 50)
    print("NENHUMA CONEXAO FUNCIONOU!")
    print("=" * 50)
    print("\nVerifique se o MongoDB esta rodando:")
    print("  1. Abra um terminal")
    print("  2. Execute: mongod")
    print("  3. Ou inicie o servico: net start MongoDB")

    return None


if __name__ == '__main__':
    working_url = test_connection()

    if working_url:
        print("\n" + "=" * 50)
        print("CONEXAO OK!")
        print("=" * 50)

        # Atualizar .env se necessario
        current_url = os.getenv('MONGO_URL', '')
        if working_url != current_url:
            print(f"\nSugestao: Atualize MONGO_URL no .env para:")
            print(f"  MONGO_URL={working_url}")
