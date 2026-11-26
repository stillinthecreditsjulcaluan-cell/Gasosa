import pandas as pd
import numpy as np

def enrich(df):
    x=df.copy(); close=x['close']
    x['SMA20']=close.rolling(20).mean(); x['SMA50']=close.rolling(50).mean()
    delta=close.diff(); gain=delta.clip(lower=0).rolling(14).mean(); loss=(-delta.clip(upper=0)).rolling(14).mean()
    rs=gain/loss.replace(0,np.nan); x['RSI14']=100-(100/(1+rs))
    ema12=close.ewm(span=12,adjust=False).mean(); ema26=close.ewm(span=26,adjust=False).mean()
    x['MACD']=ema12-ema26; x['MACD_signal']=x['MACD'].ewm(span=9,adjust=False).mean()
    x['vol_avg20']=x['volume'].rolling(20).mean() if 'volume' in x else np.nan
    x['vol_ratio']=x['volume']/x['vol_avg20'] if 'volume' in x else np.nan
    x['returns']=close.pct_change(); x['volatility20']=x['returns'].rolling(20).std()*100
    return x

def score_asset(ticker, df, quote):
    last=df.iloc[-1]; score=0; trend=0; momentum=0; volume=0; risk=0; notes=[]; cautions=[]
    if pd.notna(last.get('SMA20')) and last['close']>last['SMA20']:
        trend+=15; notes.append('Preço acima MM20')
    if pd.notna(last.get('SMA20')) and pd.notna(last.get('SMA50')) and last['SMA20']>last['SMA50']:
        trend+=20; notes.append('MM20 acima MM50')
    rsi=last.get('RSI14')
    if pd.notna(rsi) and 45<=rsi<=65: momentum+=15; notes.append('RSI em zona saudável')
    elif pd.notna(rsi) and 65<rsi<=70: momentum+=8; cautions.append('RSI próximo de sobrecompra')
    if pd.notna(last.get('MACD')) and pd.notna(last.get('MACD_signal')) and last['MACD']>last['MACD_signal']:
        momentum+=15; notes.append('MACD acima do sinal')
    vr=last.get('vol_ratio')
    if pd.notna(vr) and vr>=1.2: volume=20; notes.append('Volume 20%+ acima da média')
    elif pd.notna(vr) and vr>=1.0: volume=10; notes.append('Volume acima da média')
    vol=last.get('volatility20')
    if pd.notna(vol):
        if vol<=3: risk=15
        elif vol<=5: risk=10
        elif vol<=8: risk=5
        else: risk=0; cautions.append('Volatilidade elevada')
    if pd.notna(rsi) and rsi>70: risk=max(0,risk-5); cautions.append('RSI acima de 70: cuidado com esticamento')
    elif pd.notna(rsi) and rsi<30: cautions.append('RSI abaixo de 30: fraqueza, não é compra automática')
    score=trend+momentum+volume+risk
    if score>=75: label='Radar forte — investigar'
    elif score>=55: label='Radar moderado — observar'
    elif score>=35: label='Neutro — aguardar'
    else: label='Fraco — evitar perseguir'
    return {'Ticker':ticker,'Preço (R$)':round(float(last['close']),2),'Variação (%)':quote.get('regularMarketChangePercent'),'RSI14':round(float(rsi),1) if pd.notna(rsi) else None,'Score':score,'Tendência':trend,'Momentum':momentum,'Volume':volume,'Risco':risk,'Classificação':label,'Volume x média':round(float(vr),2) if pd.notna(vr) else None,'Critérios':'; '.join(notes) or 'Sem critérios positivos','Alertas':'; '.join(cautions) or 'Sem alerta técnico calculado'}
