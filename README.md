# Hi, I'm Bernardo 👋
**CS @ King's College London** · **MSc Data Science & ML @ UCL (incoming)** · Building at the intersection of quantitative finance and machine learning

I build end-to-end systems - from research and backtesting through to live execution and monitoring. Currently focused on algorithmic trading infrastructure, applied ML, and explainable AI in regulated finance.

---

### What I'm building

| Project | Description |
|---|---|
| [**AlphaLab**](https://github.com/bernardoguterres/AlphaLab) | Web backtesting platform - 8 strategies, walk-forward validation, Monte Carlo simulation, Greenblatt Magic Formula screener. React/TypeScript + Flask, Railway-deployable, optional Tauri desktop build. 320 tests (91% coverage) |
| [**AlphaLive**](https://github.com/bernardoguterres/AlphaLive) | 24/7 live execution engine on Railway. Consumes AlphaLab strategies, trades via Alpaca with idempotent order placement, fractional sizing, and restart-safe persisted state reconciled against the broker. Multi-layer risk management (circuit breakers, kill switch, trailing stops), pre-execution sentiment gate via AlphaSignal, real-time FastAPI/WebSocket dashboard. Signal parity tests verify live signals match AlphaLab backtests bar-for-bar. 525 tests (91% coverage) |
| [**AlphaSignal**](https://github.com/bernardoguterres/AlphaSignal) | Financial RAG system - ingests SEC EDGAR filings & news, hybrid BM25 + FAISS dense retrieval, cross-encoder reranking, sentiment extraction. API-key-secured FastAPI service consumed by AlphaLive's execution gate. 157 tests (92% coverage) |
| [**xai-dr-finance**](https://github.com/bernardoguterres/xai-dr-finance) | XAI framework for dimensionality reduction in regulated finance. Bridges the "discrete logic gap" - converts continuous SHAP attributions into EBA/ECB/SR 11-7 compliant IF-THEN rules. 8,867 lines, 6 DR methods, 5 XAI techniques, 16 modules. Pending publication |
| [**nbaMVPPredictor**](https://github.com/bernardoguterres/nbaMVPPredictor) | ML ranking model (Ridge/RF/XGBoost) across 34 seasons, 52 engineered features, SHAP analysis, time-aware backtest with no data leakage |

---

### Stack

![Python](https://img.shields.io/badge/Python-0a0a0a?style=flat-square&logo=python&logoColor=3b82f6)
![TypeScript](https://img.shields.io/badge/TypeScript-0a0a0a?style=flat-square&logo=typescript&logoColor=3b82f6)
![React](https://img.shields.io/badge/React-0a0a0a?style=flat-square&logo=react&logoColor=3b82f6)
![Flask](https://img.shields.io/badge/Flask-0a0a0a?style=flat-square&logo=flask&logoColor=3b82f6)
![PyTorch](https://img.shields.io/badge/PyTorch-0a0a0a?style=flat-square&logo=pytorch&logoColor=3b82f6)
![FastAPI](https://img.shields.io/badge/FastAPI-0a0a0a?style=flat-square&logo=fastapi&logoColor=3b82f6)
![SQL](https://img.shields.io/badge/SQL-0a0a0a?style=flat-square&logo=postgresql&logoColor=3b82f6)
![scikit-learn](https://img.shields.io/badge/scikit--learn-0a0a0a?style=flat-square&logo=scikitlearn&logoColor=3b82f6)

---

📍 London · [Portfolio](https://bernardoguterres.github.io/portfolio/) · [LinkedIn](https://linkedin.com/in/bernardoguterres) · bernardomloguterres@gmail.com
