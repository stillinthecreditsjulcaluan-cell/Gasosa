import requests
import pandas as pd

BASE="https://brapi.dev/api"

def _headers(token):
    return {"Authorization": f"Bearer {token}"} if token else {}

def get_history(ticker, period="3mo", token=None):
    url=f"{BASE}/quote/{ticker}"
    response=requests.get(url, params={"range":period, "interval":"1d"}, headers=_headers(token), timeout=20)
    response.raise_for_status()
    payload=response.json()
    results=payload.get("results", [])
    if not results:
        raise ValueError("API não retornou histórico para esse ativo")
    history=results[0].get("historicalDataPrice", [])
    df=pd.DataFrame(history)
    if df.empty:
        raise ValueError("Histórico indisponível ou não autorizado pelo plano da API")
    df["date"]=pd.to_datetime(df["date"], unit="s", errors="coerce")
    df=df.sort_values("date").reset_index(drop=True)
    for col in ["open","high","low","close","volume","adjustedClose"]:
        if col in df.columns:
            df[col]=pd.to_numeric(df[col], errors="coerce")
    if "close" not in df.columns and "adjustedClose" in df.columns:
        df["close"]=df["adjustedClose"]
    return df

def get_quote(ticker, token=None):
    url=f"{BASE}/quote/{ticker}"
    response=requests.get(url, headers=_headers(token), timeout=20)
    response.raise_for_status()
    results=response.json().get("results", [])
    if not results:
        raise ValueError("Cotação não retornada")
    return results[0]
