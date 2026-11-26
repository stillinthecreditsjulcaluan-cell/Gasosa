# Gasosa v0.1 — Radar B3

Protótipo experimental de análise técnica e simulação. Não executa ordens reais nem oferece garantia de resultado.

## Rodar localmente
1. Instale Python 3.10+.
2. No terminal, dentro desta pasta: `pip install -r requirements.txt`
3. Execute: `streamlit run app.py`

## Dados
O protótipo usa a API brapi. Alguns tickers podem exigir token e/ou plano específico. O token é digitado na interface e não é salvo pelo app.

## Limitações
- Dados podem ter atraso, limites e indisponibilidade.
- Score é heurístico e não representa probabilidade de lucro.
- Simulador é simples e não desconta corretagem, emolumentos, impostos, slippage ou proventos.
- Nenhuma ordem real é executada.
