# 💰 DeFi Yield Aggregator

> Real-time DeFi yield aggregator — compare APY/APR from Aave V3, Compound, Curve & Uniswap V3 with Telegram alerts.

![Python](https://img.shields.io/badge/Python-3.12+-blue?style=flat-square&logo=python)
![DeFi Llama](https://img.shields.io/badge/DeFi_Llama-API-purple?style=flat-square)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=flat-square&logo=telegram)
![Ethereum](https://img.shields.io/badge/Ethereum-Mainnet-627EEA?style=flat-square&logo=ethereum)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 🔍 What is Yield Aggregation?

DeFi yield aggregation compares interest rates and returns across multiple decentralized finance protocols, helping investors find the best opportunities without manually checking each platform.

This bot aggregates real-time APY data from:
- 🏦 **Aave V3** — lending & borrowing rates
- 🏦 **Compound** — supply & borrow APY
- 🌊 **Curve** — liquidity pool APY + CRV rewards
- 🦄 **Uniswap V3** — LP fee APY

---

## ✨ Features

- 💰 **Best Yield Rankings** — top opportunities sorted by APY
- 💵 **Stablecoin Filter** — show only USDC, USDT, DAI yields
- 🏦 **Protocol Filter** — filter by specific protocol
- 📊 **Market Overview** — avg, highest, lowest APY summary
- 🔔 **APY Spike Alerts** — get notified when APY > 20%
- 🤖 **Telegram Bot** — 8 interactive commands
- 🔄 **Auto Cache** — 10 minute cache to avoid rate limits

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install requests
```

### 2. Set environment variables

```powershell
# Windows PowerShell
$env:TELEGRAM_TOKEN    = "your_telegram_bot_token"
$env:TELEGRAM_CHAT_ID  = "your_chat_id"
```

```bash
# Linux / Mac
export TELEGRAM_TOKEN="your_telegram_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### 3. Run as Telegram Bot

```bash
python defi_yield_aggregator.py
```

### 4. Quick Scan (one-time)

```bash
python defi_yield_aggregator.py scan
```

---

## 🤖 Telegram Commands

| Command | Description |
|---------|-------------|
| `/yield` | Best yield opportunities (top 10) |
| `/yield_stable` | Stablecoin yields only |
| `/yield_aave` | Aave V3 rates |
| `/yield_compound` | Compound rates |
| `/yield_curve` | Curve pool APY |
| `/yield_uni` | Uniswap V3 LP APY |
| `/yield_summary` | Market overview |
| `/yield_alert on/off` | Toggle APY spike alerts |

---

## 📊 Sample Output

```
💰 BEST YIELD OPPORTUNITIES
━━━━━━━━━━━━━━━━━━━━━━

1. Aave V3 — USDC
   💰 APY: 8.24% 🟢 | TVL: $1.2B

2. Curve — USDT/USDC/DAI
   💰 APY: 6.81% 🟡 | TVL: $892M

3. Compound V3 — USDC
   💰 APY: 5.43% 🟢 | TVL: $654M

4. Uniswap V3 — ETH/USDC
   💰 APY: 12.3% 🟡 | TVL: $234M

🟢 LOW risk  🟡 MEDIUM risk
⏰ 2026-05-24 14:00
```

---

## 🏗️ Architecture

```
defi_yield_aggregator.py
├── AaveClient          → Aave V3 API + DeFi Llama fallback
├── CompoundClient      → Compound via DeFi Llama
├── CurveClient         → Curve API + DeFi Llama fallback
├── UniswapClient       → Uniswap V3 via DeFi Llama
├── YieldAggregator     → Core engine (aggregate + rank + filter)
│   ├── get_all_yields()     → fetch all protocols
│   ├── get_best_yields()    → top N by APY
│   ├── get_stable_yields()  → stablecoin only
│   ├── get_by_protocol()    → filter by protocol
│   ├── detect_apy_spikes()  → find unusually high APY
│   └── get_summary()        → market overview stats
└── YieldBot            → Telegram bot with 8 commands
```

---

## 📡 Data Sources

| Source | Usage |
|--------|-------|
| [DeFi Llama Yields API](https://yields.llama.fi) | Primary — all protocols |
| [Aave API](https://aave-api-v2.aave.com) | Aave V3 detailed rates |
| [Curve API](https://api.curve.fi) | Curve pool APY + CRV rewards |

All data is fetched in real-time with 10-minute caching to avoid rate limits.

---

## ⚠️ Risk Disclaimer

| Risk Level | Description |
|-----------|-------------|
| 🟢 LOW | Lending protocols (Aave, Compound) — audited, battle-tested |
| 🟡 MEDIUM | Liquidity pools (Curve, Uniswap) — impermanent loss risk |
| 🔴 HIGH | New/unaudited protocols — DYOR |

> **Always do your own research before depositing funds into any DeFi protocol.**

---

## 🔧 Requirements

```
requests>=2.28.0
```

No Web3.py required — uses REST APIs only!

---

## 👤 Author

**Rizal** — [@rizalcodes](https://github.com/rizalcodes)

> Building Web3 tools with Python 🐍⛓️

---

## 📄 License

MIT License — free to use, modify, and distribute.
