import pandas as pd

def enrich(df):
    x=df.copy()
    close=x["close"]
    x["SMA20"]=close.rolling(20).mean()
    x["SMA50"]=close.rolling(50).mean()
    delta=close.diff()
    gain=delta.clip(lower=0).rolling(14).mean()
    loss=(-delta.clip(upper=0)).rolling(14).mean()
    rs=gain/loss.replace(0, float("nan"))
    x["RSI14"]=100-(100/(1+rs))
    ema12=close.ewm(span=12, adjust=False).mean()
    ema26=close.ewm(span=26, adjust=False).mean()
    x["MACD"]=ema12-ema26
    x["MACD_signal"]=x["MACD"].ewm(span=9, adjust=False).mean()
    x["vol_avg20"]=x["volume"].rolling(20).mean() if "volume" in x else float("nan")
    return x

def score_asset(ticker, df, quote):
    last=df.iloc[-1]
    prev=df.iloc[-2] if len(df)>1 else last
    score=0
    notes=[]
    if pd.notna(last.get("SMA20")) and last["close"]>last["SMA20"]:
        score+=1; notes.append("acima da MM20")
    if pd.notna(last.get("SMA50")) and last["close"]>last["SMA50"]:
        score+=1; notes.append("acima da MM50")
    if pd.notna(last.get("RSI14")) and 50<=last["RSI14"]<=70:
        score+=1; notes.append("RSI em faixa positiva")
    if pd.notna(last.get("MACD")) and pd.notna(last.get("MACD_signal")) and last["MACD"]>last["MACD_signal"]:
        score+=1; notes.append("MACD acima do sinal")
    if "volume" in df and pd.notna(last.get("vol_avg20")) and pd.notna(last.get("volume")) and last["vol_avg20"]>0 and last["volume"]>last["vol_avg20"]:
        score+=1; notes.append("volume acima da média")
    label="Observar"
    if score>=4: label="Condições técnicas positivas"
    elif score<=1: label="Condições fracas"
    return {
        "Ticker": ticker,
        "Preço (R$)": round(float(last["close"]),2),
        "Variação (%)": quote.get("regularMarketChangePercent"),
        "RSI14": round(float(last["RSI14"]),1) if pd.notna(last["RSI14"]) else None,
        "Score": score,
        "Classificação": label,
        "Critérios": "; ".join(notes) if notes else "Sem critérios positivos detectados"
    }
