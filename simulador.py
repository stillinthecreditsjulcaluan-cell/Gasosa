import streamlit as st

def init_simulator(start_cash):
    if "paper_cash" not in st.session_state:
        st.session_state.paper_cash=float(start_cash)
    if "paper_portfolio" not in st.session_state:
        st.session_state.paper_portfolio={}

def buy_sim(ticker, qty, price):
    total=qty*price
    if total>st.session_state.paper_cash:
        return False, "Saldo simulado insuficiente."
    positions=st.session_state.paper_portfolio
    old=positions.get(ticker, {"qty":0,"avg":0.0})
    new_qty=old["qty"]+qty
    new_avg=(old["qty"]*old["avg"]+qty*price)/new_qty
    positions[ticker]={"qty":new_qty,"avg":new_avg}
    st.session_state.paper_cash-=total
    return True, f"Compra simulada registrada: {qty} {ticker} a R$ {price:.2f}."

def sell_sim(ticker, qty, price):
    positions=st.session_state.paper_portfolio
    if ticker not in positions or qty>positions[ticker]["qty"]:
        return False, "Quantidade maior que a posição simulada disponível."
    positions[ticker]["qty"]-=qty
    st.session_state.paper_cash+=qty*price
    if positions[ticker]["qty"]==0:
        del positions[ticker]
    return True, f"Venda simulada registrada: {qty} {ticker} a R$ {price:.2f}."
