import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dados import get_history, get_quote
from indicadores import enrich, score_asset
from simulador import init_simulator, buy_sim, sell_sim

st.set_page_config(page_title='Gasosa | Radar B3',page_icon='⛽',layout='wide')
st.title('⛽ GASOSA — Radar B3 | v0.2')
st.caption('Triagem técnica experimental • Cotações podem ter atraso • Não executa ordens reais')
with st.sidebar:
    st.header('Configurações')
    token=st.text_input('Token brapi',type='password',help='Token privado; não compartilhe nem publique.')
    watchlist=st.text_area('Ativos (separados por vírgula)','PETR4, VALE3, ITUB4, BBAS3, B3SA3, MGLU3, WEGE3, ABEV3, PRIO3, SUZB3')
    tickers=list(dict.fromkeys(t.strip().upper() for t in watchlist.split(',') if t.strip()))
    period=st.selectbox('Histórico',['3mo','1mo','6mo','1y'],index=0)
    cash=st.number_input('Saldo inicial simulado (R$)',min_value=0.0,value=1000.0,step=100.0)
    refresh=st.button('Atualizar radar',type='primary')

@st.cache_data(ttl=600,show_spinner=False)
def cached_history(ticker,period,api_token): return get_history(ticker,period=period,token=api_token)
@st.cache_data(ttl=600,show_spinner=False)
def cached_quote(ticker,api_token): return get_quote(ticker,token=api_token)
rows=[]; histories={}; errors=[]
with st.spinner('Consultando dados e calculando motores...'):
    for ticker in tickers:
        try:
            df=cached_history(ticker,period,token.strip() or None)
            if df is None or df.empty: raise ValueError('Histórico vazio')
            enriched=enrich(df); histories[ticker]=enriched
            quote=cached_quote(ticker,token.strip() or None)
            rows.append(score_asset(ticker,enriched,quote))
        except Exception as e: errors.append(f'{ticker}: {e}')
if rows:
    ranking=pd.DataFrame(rows).sort_values('Score',ascending=False)
    st.subheader('Ranking de força técnica')
    st.dataframe(ranking[['Ticker','Preço (R$)','Variação (%)','RSI14','Score','Tendência','Momentum','Volume','Risco','Classificação']],use_container_width=True,hide_index=True)
    st.caption('Score 0–100 é uma pontuação heurística; não é probabilidade de lucro nem recomendação.')
    st.subheader('Radar de atenção')
    for _,r in ranking.iterrows():
        if r['Score']>=75: st.success(f"{r['Ticker']}: {r['Classificação']} — {r['Score']}/100")
        elif r['Score']>=55: st.info(f"{r['Ticker']}: {r['Classificação']} — {r['Score']}/100")
    with st.expander('Critérios e cautelas por ativo'):
        for _,r in ranking.iterrows():
            st.markdown(f"**{r['Ticker']} — {r['Score']}/100**")
            st.write('Critérios:',r['Critérios']); st.write('Alertas:',r['Alertas'])
else: st.warning('Sem dados retornados. Confira internet, ticker e token.')
if errors:
    with st.expander(f'Erros de consulta ({len(errors)})'):
        for e in errors: st.write(e)
if histories:
    st.subheader('Análise individual')
    selected=st.selectbox('Ativo',list(histories.keys())); df=histories[selected].dropna(subset=['close']).copy()
    fig=go.Figure(); fig.add_trace(go.Scatter(x=df.date,y=df.close,name='Fechamento',line=dict(width=2)))
    for col in ['SMA20','SMA50']:
        if col in df: fig.add_trace(go.Scatter(x=df.date,y=df[col],name=col))
    fig.update_layout(height=400,template='plotly_dark',yaxis_title='Preço (R$)'); st.plotly_chart(fig,use_container_width=True)
    last=df.iloc[-1]; a,b,c,d=st.columns(4)
    a.metric('Fechamento',f"R$ {last.close:.2f}"); b.metric('RSI14',f"{last.RSI14:.1f}" if pd.notna(last.RSI14) else '—'); c.metric('Vol. x média',f"{last.vol_ratio:.2f}x" if pd.notna(last.vol_ratio) else '—'); d.metric('Volatilidade 20d',f"{last.volatility20:.2f}%" if pd.notna(last.volatility20) else '—')
    rf=go.Figure(go.Scatter(x=df.date,y=df.RSI14,name='RSI14')); rf.add_hline(y=70,line_dash='dash'); rf.add_hline(y=30,line_dash='dash'); rf.update_layout(height=230,yaxis_range=[0,100],template='plotly_dark'); st.plotly_chart(rf,use_container_width=True)
    st.subheader('Componentes do score')
    if rows:
        rr=next((r for r in rows if r['Ticker']==selected),None)
        if rr: st.bar_chart(pd.Series({'Tendência':rr['Tendência'],'Momentum':rr['Momentum'],'Volume':rr['Volume'],'Risco':rr['Risco']}))
st.divider(); st.subheader('Simulador (operações fictícias)')
init_simulator(cash); portfolio=st.session_state.paper_portfolio; balance=st.session_state.paper_cash
st.write(f"**Saldo simulado:** R$ {balance:,.2f}".replace(',','X').replace('.',',').replace('X','.'))
with st.expander('Compra fictícia'):
    bt=st.selectbox('Ticker para compra',tickers,key='buy_ticker'); qty=st.number_input('Quantidade',min_value=1,step=1,key='buy_qty')
    if st.button('Simular compra'):
        price=histories[bt].iloc[-1].close if bt in histories else None
        if price: ok,msg=buy_sim(bt,int(qty),float(price)); (st.success if ok else st.error)(msg)
        else: st.error('Preço não disponível')
with st.expander('Venda fictícia'):
    stt=st.selectbox('Ticker para venda',list(portfolio.keys()) or tickers,key='sell_ticker'); sq=st.number_input('Quantidade para venda',min_value=1,step=1,key='sell_qty')
    if st.button('Simular venda'):
        price=histories[stt].iloc[-1].close if stt in histories else None
        if price: ok,msg=sell_sim(stt,int(sq),float(price)); (st.success if ok else st.error)(msg)
        else: st.error('Preço não disponível')
if portfolio: st.dataframe(pd.DataFrame([{'Ativo':k,'Quantidade':v['qty'],'Preço médio (R$)':v['avg']} for k,v in portfolio.items()]),use_container_width=True,hide_index=True)
else: st.caption('Nenhuma posição simulada ainda.')
