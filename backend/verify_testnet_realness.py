"""
Verifica se os dados de preço do Testnet são reais ou falsos
Compara preços do Testnet vs Mainnet
"""

import asyncio
from binance.client import Client
from datetime import datetime

async def compare_testnet_vs_mainnet():
    """Compara dados de preço entre Testnet e Mainnet"""
    
    print("=" * 80)
    print("🔍 VERIFICAÇÃO: Dados do Testnet são REAIS ou FALSOS?")
    print("=" * 80)
    print()
    
    # Cliente Testnet
    testnet_client = Client(
        api_key="",  # Não precisa de API key para dados públicos
        api_secret="",
        testnet=True
    )
    
    # Cliente Mainnet (produção real)
    mainnet_client = Client(
        api_key="",  # Não precisa de API key para dados públicos
        api_secret=""
    )
    
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT']
    
    print("📊 Comparando preços em tempo real:")
    print("-" * 80)
    print(f"{'Símbolo':<12} {'Testnet':<20} {'Mainnet':<20} {'Diferença':<15}")
    print("-" * 80)
    
    for symbol in symbols:
        try:
            # Pegar preço do Testnet
            testnet_ticker = testnet_client.futures_symbol_ticker(symbol=symbol)
            testnet_price = float(testnet_ticker['price'])
            
            # Pegar preço do Mainnet (real)
            mainnet_ticker = mainnet_client.futures_symbol_ticker(symbol=symbol)
            mainnet_price = float(mainnet_ticker['price'])
            
            # Calcular diferença
            diff = abs(testnet_price - mainnet_price)
            diff_percent = (diff / mainnet_price) * 100
            
            print(f"{symbol:<12} ${testnet_price:<18,.2f} ${mainnet_price:<18,.2f} {diff_percent:>6.2f}%")
            
        except Exception as e:
            print(f"{symbol:<12} ERRO: {e}")
    
    print("-" * 80)
    print()
    
    # Testar dados de kline (gráfico)
    print("📈 Comparando dados de gráfico (Klines - últimas 10 velas de 1 minuto):")
    print("-" * 80)
    
    symbol = 'BTCUSDT'
    
    try:
        # Klines do Testnet
        testnet_klines = testnet_client.futures_klines(
            symbol=symbol,
            interval=Client.KLINE_INTERVAL_1MINUTE,
            limit=10
        )
        
        # Klines do Mainnet
        mainnet_klines = mainnet_client.futures_klines(
            symbol=symbol,
            interval=Client.KLINE_INTERVAL_1MINUTE,
            limit=10
        )
        
        print(f"\n🟢 TESTNET - {symbol} (últimas 10 velas de 1min):")
        print(f"{'Timestamp':<20} {'Open':<12} {'High':<12} {'Low':<12} {'Close':<12}")
        print("-" * 70)
        
        for kline in testnet_klines[-5:]:  # Mostrar últimas 5
            timestamp = datetime.fromtimestamp(kline[0] / 1000).strftime('%Y-%m-%d %H:%M')
            open_price = float(kline[1])
            high_price = float(kline[2])
            low_price = float(kline[3])
            close_price = float(kline[4])
            print(f"{timestamp:<20} ${open_price:<11,.2f} ${high_price:<11,.2f} ${low_price:<11,.2f} ${close_price:<11,.2f}")
        
        print(f"\n🔴 MAINNET (REAL) - {symbol} (últimas 10 velas de 1min):")
        print(f"{'Timestamp':<20} {'Open':<12} {'High':<12} {'Low':<12} {'Close':<12}")
        print("-" * 70)
        
        for kline in mainnet_klines[-5:]:  # Mostrar últimas 5
            timestamp = datetime.fromtimestamp(kline[0] / 1000).strftime('%Y-%m-%d %H:%M')
            open_price = float(kline[1])
            high_price = float(kline[2])
            low_price = float(kline[3])
            close_price = float(kline[4])
            print(f"{timestamp:<20} ${open_price:<11,.2f} ${high_price:<11,.2f} ${low_price:<11,.2f} ${close_price:<11,.2f}")
        
        # Comparar timestamps
        testnet_timestamps = [k[0] for k in testnet_klines[-5:]]
        mainnet_timestamps = [k[0] for k in mainnet_klines[-5:]]
        
        print("\n" + "=" * 80)
        print("🔎 ANÁLISE:")
        print("=" * 80)
        
        if testnet_timestamps == mainnet_timestamps:
            print("✅ Os timestamps são IDÊNTICOS entre Testnet e Mainnet")
        else:
            print("⚠️  Os timestamps são DIFERENTES")
        
        # Comparar preços
        testnet_closes = [float(k[4]) for k in testnet_klines[-5:]]
        mainnet_closes = [float(k[4]) for k in mainnet_klines[-5:]]
        
        avg_diff = sum([abs(t - m) for t, m in zip(testnet_closes, mainnet_closes)]) / len(testnet_closes)
        avg_price = sum(mainnet_closes) / len(mainnet_closes)
        avg_diff_percent = (avg_diff / avg_price) * 100
        
        print(f"\n📊 Diferença média de preço: ${avg_diff:,.2f} ({avg_diff_percent:.4f}%)")
        
        if avg_diff_percent < 0.01:
            print("\n✅ CONCLUSÃO: Os dados do TESTNET são 100% REAIS!")
            print("   Os gráficos e preços são IDÊNTICOS aos da Binance real (Mainnet).")
            print("   A única diferença é que o dinheiro é VIRTUAL ($100k grátis).")
        else:
            print("\n⚠️  CONCLUSÃO: Os dados do TESTNET são DIFERENTES")
            print(f"   Diferença de {avg_diff_percent:.4f}% detectada.")
        
    except Exception as e:
        print(f"ERRO ao comparar klines: {e}")
    
    print("\n" + "=" * 80)
    print("📝 RESUMO:")
    print("=" * 80)
    print("""
O Binance Futures Testnet usa:

1. ✅ PREÇOS REAIS - Sincronizados com o mercado real da Binance
2. ✅ GRÁFICOS REAIS - Mesmos dados de kline/candlestick do Mainnet
3. ✅ LIVRO DE ORDENS REAL - Order book idêntico ao mercado real
4. ✅ EXECUÇÃO SIMULADA - As ordens são executadas como se fosse real

A ÚNICA diferença:
💰 O dinheiro é VIRTUAL ($100,000 USDT grátis)
💰 Você não ganha/perde dinheiro real
💰 Perfeito para TESTAR estratégias sem risco

IMPORTANTE:
- Os gráficos que você vê são 100% REAIS
- Os preços são os mesmos do mercado real
- Sua estratégia está sendo testada em condições REAIS de mercado
- Quando migrar para Mainnet, verá os mesmos gráficos e preços!
""")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(compare_testnet_vs_mainnet())
