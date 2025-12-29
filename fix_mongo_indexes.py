"""Script para corrigir índices conflitantes do MongoDB"""
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017')
db = client['trading_bot']

print('Removendo índice conflitante...')
try:
    db.learning_data.drop_index('learning_type_timestamp')
    print('✓ Índice removido com sucesso')
except Exception as e:
    print(f'Info: {e}')

print('\nListando índices atuais:')
for idx in db.learning_data.list_indexes():
    print(f'  - {idx["name"]}')

client.close()
print('\nPronto! Agora reinicie o servidor.')
