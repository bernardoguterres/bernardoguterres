# Hi, I'm Bernardo 👋
**CS @ King's College London** · **MSc Data Science & ML @ UCL (incoming)** · Building at the intersection of quantitative finance and machine learning

I build end-to-end systems — from research and backtesting through to live execution and monitoring. Currently focused on algorithmic trading infrastructure, applied ML, and explainable AI in regulated finance.

---

### What I'm building

| Project | Description |
|---|---|
| [**AlphaLab**](https://github.com/bernardoguterres/AlphaLab) | Desktop backtesting platform — 8 strategies, 50+ indicators, walk-forward validation, Monte Carlo simulation. React/TypeScript + Flask + Tauri (Rust), under 10MB, 233 passing tests |
| [**AlphaLive**](https://github.com/bernardoguterres/AlphaLive) | 24/7 live execution engine on Railway. Consumes AlphaLab strategies, trades via Alpaca, production-grade risk management (circuit breakers, kill switch, trailing stops), real-time FastAPI/WebSocket dashboard. Pre-execution gate runs DeepLOB + AlphaSignal concurrently via asyncio.gather before every order |
| [**AlphaSignal**](https://github.com/bernardoguterres/AlphaSignal) | Financial RAG system — ingests SEC EDGAR filings & news, hybrid BM25 + FAISS dense retrieval, cross-encoder reranking, sentiment extraction. 7 REST API endpoints, 89% test coverage |
| [**DeepLOB**](https://github.com/bernardoguterres/DeepLOB) | PyTorch CNN+Inception+LSTM reimplementation of DeepLOB (Zhang et al. 2019). Trained on FI-2010, macro F1 0.78 at k=5. Integrated Gradients + SHAP explainability. FastAPI inference server deployed as an execution timing filter in AlphaLive |
| [**xai-dr-finance**](https://github.com/bernardoguterres/xai-dr-finance) | XAI framework for dimensionality reduction in regulated finance. Bridges the "discrete logic gap" — converts continuous SHAP attributions into EBA/ECB/SR 11-7 compliant IF-THEN rules. 8,867 lines, 6 DR methods, 5 XAI techniques, 16 modules. Pending publication |
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
![Rust](https://img.shields.io/badge/Rust-0a0a0a?style=flat-square&logo=rust&logoColor=3b82f6)

---

📍 London · [Portfolio](https://bernardoguterres.github.io/portfolio/) · [LinkedIn](https://linkedin.com/in/bernardoguterres) · bernardomloguterres@gmail.com
