import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dados import get_history, get_quote
from indicadores import enrich, score_asset
from simulador import init_simulator, buy_sim, sell_sim

st.set_page_config(page_title="Gasosa | Radar B3", page_icon="⛽", layout="wide")
st.title("⛽ GASOSA — Radar B3")
st.caption("Protótipo experimental • Dados de mercado podem ter atraso • Nenhuma ordem real é executada")

with st.sidebar:
    st.header("Configurações")
    token = st.text_input("Token brapi (opcional)", type="password", help="Deixe vazio para tentar os tickers liberados sem token. Não compartilhe seu token.")
    watchlist_text = st.text_area("Ativos monitorados (separados por vírgula)", "PETR4, VALE3, ITUB4, BBAS3, B3SA3, MGLU3, WEGE3, ABEV3, PRIO3, SUZB3")
    tickers = [t.strip().upper() for t in watchlist_text.split(",") if t.strip()]
    period = st.selectbox("Histórico", ["3mo", "1mo", "6mo", "1y"], index=0)
    cash = st.number_input("Saldo simulado inicial (R$)", min_value=0.0, value=1000.0, step=100.0)
    refresh = st.button("Atualizar radar", type="primary")

# For simplicity, refresh is a normal rerun; API data is fetched on app load.
headers_token = token.strip() or None

@st.cache_data(ttl=600, show_spinner=False)
def cached_history(ticker, period, api_token):
    return get_history(ticker, period=period, token=api_token)

@st.cache_data(ttl=600, show_spinner=False)
def cached_quote(ticker, api_token):
    return get_quote(ticker, token=api_token)

st.info("A classificação é uma triagem técnica experimental, não uma recomendação de investimento. Valide dados, custos, liquidez e risco.")
rows=[]
histories={}
errors=[]
with st.spinner("Consultando ativos e calculando indicadores..."):
    for ticker in tickers:
        try:
            df = cached_history(ticker, period, headers_token)
            if df is None or df.empty:
                raise ValueError("Histórico vazio")
            enriched = enrich(df)
            histories[ticker] = enriched
            quote = cached_quote(ticker, headers_token)
            rows.append(score_asset(ticker, enriched, quote))
        except Exception as e:
            errors.append(f"{ticker}: {e}")

if rows:
    ranking = pd.DataFrame(rows).sort_values("Score", ascending=False)
    st.subheader("Ranking do radar")
    st.dataframe(ranking, use_container_width=True, hide_index=True)
    st.caption("Score é uma métrica heurística do protótipo. Não representa probabilidade de lucro.")
else:
    st.warning("Não foi possível carregar dados. Verifique internet, tickers ou token da API.")

if errors:
    with st.expander(f"Erros de consulta ({len(errors)})"):
        for err in errors:
            st.write(err)

if histories:
    st.subheader("Análise individual")
    selected = st.selectbox("Escolha um ativo", list(histories.keys()))
    df = histories[selected].dropna(subset=["close"]).copy()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["close"], name="Fechamento", line=dict(width=2)))
    if "SMA20" in df:
        fig.add_trace(go.Scatter(x=df["date"], y=df["SMA20"], name="MM20"))
    if "SMA50" in df:
        fig.add_trace(go.Scatter(x=df["date"], y=df["SMA50"], name="MM50"))
    fig.update_layout(height=420, xaxis_title="Data", yaxis_title="Preço (R$)", template="plotly_dark", legend_title="Série")
    st.plotly_chart(fig, use_container_width=True)
    last = df.iloc[-1]
    c1,c2,c3 = st.columns(3)
    c1.metric("Último fechamento", f"R$ {last['close']:.2f}")
    c2.metric("RSI 14", f"{last['RSI14']:.1f}" if pd.notna(last["RSI14"]) else "—")
    c3.metric("MM20", f"R$ {last['SMA20']:.2f}" if pd.notna(last["SMA20"]) else "—")
    rsi_fig = go.Figure(go.Scatter(x=df["date"], y=df["RSI14"], name="RSI 14"))
    rsi_fig.add_hline(y=70, line_dash="dash")
    rsi_fig.add_hline(y=30, line_dash="dash")
    rsi_fig.update_layout(height=250, yaxis_range=[0,100], template="plotly_dark")
    st.plotly_chart(rsi_fig, use_container_width=True)

st.divider()
st.subheader("Simulador de operações (fictício)")
init_simulator(cash)
portfolio = st.session_state.paper_portfolio
cash_balance = st.session_state.paper_cash
st.write(f"**Saldo simulado:** R$ {cash_balance:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
with st.expander("Registrar compra simulada"):
    buy_ticker = st.selectbox("Ativo para compra", tickers, key="buy_ticker")
    buy_qty = st.number_input("Quantidade", min_value=1, step=1, key="buy_qty")
    if st.button("Simular compra"):
        price = histories.get(buy_ticker, pd.DataFrame()).iloc[-1]["close"] if buy_ticker in histories else None
        if price:
            ok, msg = buy_sim(buy_ticker, int(buy_qty), float(price))
            (st.success if ok else st.error)(msg)
        else:
            st.error("Preço não disponível para este ativo.")
with st.expander("Registrar venda simulada"):
    sell_ticker = st.selectbox("Ativo para venda", list(portfolio.keys()) or tickers, key="sell_ticker")
    sell_qty = st.number_input("Quantidade para venda", min_value=1, step=1, key="sell_qty")
    if st.button("Simular venda"):
        price = histories.get(sell_ticker, pd.DataFrame()).iloc[-1]["close"] if sell_ticker in histories else None
        if price:
            ok, msg = sell_sim(sell_ticker, int(sell_qty), float(price))
            (st.success if ok else st.error)(msg)
        else:
            st.error("Preço não disponível para este ativo.")
if portfolio:
    st.write("**Posições fictícias**")
    st.dataframe(pd.DataFrame([{"Ativo": k, "Quantidade": v["qty"], "Preço médio (R$)": v["avg"]} for k,v in portfolio.items()]), use_container_width=True, hide_index=True)
else:
    st.caption("Ainda não há posições simuladas.")
