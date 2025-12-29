import requests
import json

response = requests.get('http://127.0.0.1:8000/api/trades?limit=200')
trades = response.json()

sim = [t for t in trades if t.get('simulated') == True]
real = [t for t in trades if not t.get('simulated')]

print(f"Total trades retornados: {len(trades)}")
print(f"Com simulated=True: {len(sim)}")
print(f"Reais (sem simulated): {len(real)}")

if sim:
    print(f"\nExemplo trade simulado: {sim[0].get('symbol')} - price: {sim[0].get('entry_price')}")
if real:
    print(f"Exemplo trade real: {real[0].get('symbol')} - price: {real[0].get('entry_price')}")
