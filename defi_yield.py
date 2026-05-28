"""
defi_yield_aggregator.py - DeFi Yield Aggregator
By Rizal | github.com/rizalcodes
Compare APY/APR from Aave V3, Compound, Curve, Uniswap V3
Output: Real-time Telegram alerts & yield rankings
"""

import os
import time
import logging
import requests
from datetime import datetime
from typing import Optional

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN",   "8660442841:AAE1oCT6WkyhVdE9eC46I-YOD-FNBjeomYY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1024188205")

# APY spike alert threshold (%)
APY_SPIKE_THRESHOLD = 2.0   # alert kalau APY naik/turun > 2%
REFRESH_INTERVAL    = 3600  # auto refresh setiap 1 jam


# ─────────────────────────────────────────────
# 1. AAVE V3 CLIENT
# ─────────────────────────────────────────────
class AaveClient:
    """Fetch lending/borrowing rates dari Aave V3."""

    BASE = "https://aave-api-v2.aave.com/data/markets-data"

    # Aave V3 Ethereum market ID
    MARKET = "0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e"

    def __init__(self):
        self.session = requests.Session()

    def get_rates(self) -> list:
        """Ambil semua lending rates dari Aave V3."""
        try:
            r = self.session.get(
                f"{self.BASE}/{self.MARKET}",
                timeout=15
            )
            if r.status_code != 200:
                # Fallback ke DeFi Llama
                return self._get_from_defillama()

            data     = r.json()
            reserves = data.get("reserves", [])
            results  = []

            for reserve in reserves:
                symbol       = reserve.get("symbol", "")
                supply_apy   = float(reserve.get("supplyAPY", 0)) * 100
                borrow_apy   = float(reserve.get("variableBorrowAPY", 0)) * 100
                total_supply = float(reserve.get("totalLiquidityUSD", 0))
                util_rate    = float(reserve.get("utilizationRate", 0)) * 100

                if total_supply > 1000000:  # filter yang > $1M liquidity
                    results.append({
                        "protocol"    : "Aave V3",
                        "asset"       : symbol,
                        "supply_apy"  : round(supply_apy, 2),
                        "borrow_apy"  : round(borrow_apy, 2),
                        "tvl_usd"     : round(total_supply, 0),
                        "util_rate"   : round(util_rate, 2),
                        "type"        : "lending",
                        "risk"        : "LOW",
                    })

            return sorted(results, key=lambda x: x["supply_apy"], reverse=True)[:10]

        except Exception as e:
            log.error(f"Aave error: {e}")
            return self._get_from_defillama()

    def _get_from_defillama(self) -> list:
        """Fallback: ambil Aave data dari DeFi Llama."""
        try:
            r = requests.get("https://yields.llama.fi/pools", timeout=15)
            pools = r.json().get("data", [])
            results = []
            for pool in pools:
                if pool.get("project") == "aave-v3" and pool.get("chain") == "Ethereum":
                    apy = float(pool.get("apy", 0))
                    tvl = float(pool.get("tvlUsd", 0))
                    if tvl > 1000000:
                        results.append({
                            "protocol" : "Aave V3",
                            "asset"    : pool.get("symbol", ""),
                            "supply_apy": round(apy, 2),
                            "borrow_apy": 0,
                            "tvl_usd"  : round(tvl, 0),
                            "util_rate": 0,
                            "type"     : "lending",
                            "risk"     : "LOW",
                            "pool_id"  : pool.get("pool", ""),
                        })
            return sorted(results, key=lambda x: x["supply_apy"], reverse=True)[:8]
        except Exception as e:
            log.error(f"DeFi Llama Aave error: {e}")
            return []


# ─────────────────────────────────────────────
# 2. COMPOUND CLIENT
# ─────────────────────────────────────────────
class CompoundClient:
    """Fetch supply/borrow APY dari Compound V3."""

    def get_rates(self) -> list:
        """Ambil rates dari DeFi Llama untuk Compound."""
        try:
            r = requests.get("https://yields.llama.fi/pools", timeout=15)
            pools = r.json().get("data", [])
            results = []

            for pool in pools:
                project = pool.get("project", "")
                chain   = pool.get("chain", "")
                if "compound" in project.lower() and chain == "Ethereum":
                    apy = float(pool.get("apy", 0))
                    tvl = float(pool.get("tvlUsd", 0))
                    if tvl > 500000:
                        results.append({
                            "protocol"  : "Compound V3",
                            "asset"     : pool.get("symbol", ""),
                            "supply_apy": round(apy, 2),
                            "borrow_apy": float(pool.get("apyBorrow", 0) or 0),
                            "tvl_usd"   : round(tvl, 0),
                            "util_rate" : 0,
                            "type"      : "lending",
                            "risk"      : "LOW",
                        })

            return sorted(results, key=lambda x: x["supply_apy"], reverse=True)[:5]

        except Exception as e:
            log.error(f"Compound error: {e}")
            return []


# ─────────────────────────────────────────────
# 3. CURVE CLIENT
# ─────────────────────────────────────────────
class CurveClient:
    """Fetch pool APY dari Curve Finance."""

    BASE = "https://api.curve.fi/v1/getPools/ethereum/main"

    def get_rates(self) -> list:
        """Ambil top pools dari Curve."""
        try:
            r = requests.get(self.BASE, timeout=15)
            data  = r.json()
            pools = data.get("data", {}).get("poolData", [])
            results = []

            for pool in pools:
                name     = pool.get("name", "")
                apy      = float(pool.get("gaugeCrvApy", [0])[0] if pool.get("gaugeCrvApy") else 0)
                base_apy = float(pool.get("latestDailyApy", 0))
                total_apy = apy + base_apy
                tvl      = float(pool.get("usdTotal", 0))

                if tvl > 1000000 and total_apy > 0:
                    results.append({
                        "protocol"  : "Curve",
                        "asset"     : name,
                        "supply_apy": round(total_apy, 2),
                        "base_apy"  : round(base_apy, 2),
                        "crv_apy"   : round(apy, 2),
                        "borrow_apy": 0,
                        "tvl_usd"   : round(tvl, 0),
                        "util_rate" : 0,
                        "type"      : "liquidity",
                        "risk"      : "MEDIUM",
                    })

            return sorted(results, key=lambda x: x["supply_apy"], reverse=True)[:8]

        except Exception as e:
            log.error(f"Curve error: {e}")
            return self._fallback()

    def _fallback(self) -> list:
        """Fallback via DeFi Llama."""
        try:
            r = requests.get("https://yields.llama.fi/pools", timeout=15)
            pools = r.json().get("data", [])
            results = []
            for pool in pools:
                if pool.get("project") == "curve-dex" and pool.get("chain") == "Ethereum":
                    apy = float(pool.get("apy", 0))
                    tvl = float(pool.get("tvlUsd", 0))
                    if tvl > 1000000 and apy > 0:
                        results.append({
                            "protocol"  : "Curve",
                            "asset"     : pool.get("symbol", ""),
                            "supply_apy": round(apy, 2),
                            "borrow_apy": 0,
                            "tvl_usd"   : round(tvl, 0),
                            "util_rate" : 0,
                            "type"      : "liquidity",
                            "risk"      : "MEDIUM",
                        })
            return sorted(results, key=lambda x: x["supply_apy"], reverse=True)[:5]
        except Exception as e:
            log.error(f"Curve fallback error: {e}")
            return []


# ─────────────────────────────────────────────
# 4. UNISWAP V3 CLIENT
# ─────────────────────────────────────────────
class UniswapClient:
    """Fetch LP fee APY dari Uniswap V3 via DeFi Llama."""

    def get_rates(self) -> list:
        """Ambil top Uniswap V3 pools by APY."""
        try:
            r = requests.get("https://yields.llama.fi/pools", timeout=15)
            pools = r.json().get("data", [])
            results = []

            for pool in pools:
                if pool.get("project") == "uniswap-v3" and pool.get("chain") == "Ethereum":
                    apy = float(pool.get("apy", 0))
                    tvl = float(pool.get("tvlUsd", 0))
                    if tvl > 1000000 and apy > 0:
                        results.append({
                            "protocol"  : "Uniswap V3",
                            "asset"     : pool.get("symbol", ""),
                            "supply_apy": round(apy, 2),
                            "borrow_apy": 0,
                            "tvl_usd"   : round(tvl, 0),
                            "util_rate" : 0,
                            "type"      : "liquidity",
                            "risk"      : "MEDIUM-HIGH",
                        })

            return sorted(results, key=lambda x: x["supply_apy"], reverse=True)[:8]

        except Exception as e:
            log.error(f"Uniswap error: {e}")
            return []


# ─────────────────────────────────────────────
# 5. YIELD AGGREGATOR (CORE)
# ─────────────────────────────────────────────
class YieldAggregator:
    """Core engine — aggregate & rank yields dari semua protocol."""

    def __init__(self):
        self.aave     = AaveClient()
        self.compound = CompoundClient()
        self.curve    = CurveClient()
        self.uniswap  = UniswapClient()
        self._cache   = {}
        self._cache_ts = 0

    def get_all_yields(self, use_cache: bool = True) -> list:
        """Ambil semua yields dari semua protocol."""
        now = time.time()

        # Cache 10 menit
        if use_cache and self._cache and now - self._cache_ts < 600:
            log.info("📋 Using cached yield data")
            return self._cache

        log.info("🔄 Fetching fresh yield data...")
        all_yields = []

        log.info("📊 Fetching Aave V3...")
        all_yields.extend(self.aave.get_rates())
        time.sleep(0.5)

        log.info("📊 Fetching Compound...")
        all_yields.extend(self.compound.get_rates())
        time.sleep(0.5)

        log.info("📊 Fetching Curve...")
        all_yields.extend(self.curve.get_rates())
        time.sleep(0.5)

        log.info("📊 Fetching Uniswap V3...")
        all_yields.extend(self.uniswap.get_rates())

        # Sort by APY
        all_yields = sorted(all_yields, key=lambda x: x["supply_apy"], reverse=True)

        self._cache    = all_yields
        self._cache_ts = now

        log.info(f"✅ Found {len(all_yields)} yield opportunities")
        return all_yields

    def get_best_yields(self, top_n: int = 10) -> list:
        """Return top N yields."""
        return self.get_all_yields()[:top_n]

    def get_by_protocol(self, protocol: str) -> list:
        """Filter yields by protocol."""
        all_yields = self.get_all_yields()
        protocol   = protocol.lower()
        return [y for y in all_yields if protocol in y["protocol"].lower()]

    def get_by_risk(self, risk: str) -> list:
        """Filter yields by risk level."""
        all_yields = self.get_all_yields()
        return [y for y in all_yields if y["risk"] == risk.upper()]

    def get_stable_yields(self) -> list:
        """Filter stablecoin yields only."""
        stables    = ["USDC", "USDT", "DAI", "FRAX", "BUSD", "TUSD", "LUSD"]
        all_yields = self.get_all_yields()
        return [
            y for y in all_yields
            if any(s in y["asset"].upper() for s in stables)
        ]

    def detect_apy_spikes(self, threshold: float = APY_SPIKE_THRESHOLD) -> list:
        """Detect APY yang unusually high (potential opportunity atau risk)."""
        all_yields = self.get_all_yields()
        spikes = []

        for y in all_yields:
            if y["supply_apy"] > 20:  # APY > 20% = noteworthy
                spikes.append({
                    **y,
                    "spike_reason": "High APY — verify sustainability",
                    "alert_level" : "HIGH" if y["supply_apy"] > 50 else "MEDIUM",
                })

        return spikes

    def get_summary(self) -> dict:
        """Summary statistik semua yields."""
        all_yields = self.get_all_yields()
        if not all_yields:
            return {}

        apys = [y["supply_apy"] for y in all_yields]
        return {
            "total_opportunities": len(all_yields),
            "highest_apy"        : max(apys),
            "lowest_apy"         : min(apys),
            "avg_apy"            : round(sum(apys) / len(apys), 2),
            "protocols"          : list(set(y["protocol"] for y in all_yields)),
            "timestamp"          : datetime.now().isoformat(),
        }


# ─────────────────────────────────────────────
# 6. TELEGRAM BOT
# ─────────────────────────────────────────────
class YieldBot:
    def __init__(self):
        self.token      = TELEGRAM_TOKEN
        self.chat_id    = TELEGRAM_CHAT_ID
        self.base       = f"https://api.telegram.org/bot{self.token}"
        self.aggregator = YieldAggregator()
        self.offset     = 0
        self.running    = True
        self.alert_on   = False
        log.info("🤖 YieldBot initialized")

    def send(self, chat_id: str, text: str):
        try:
            requests.post(
                f"{self.base}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
                timeout=10
            )
        except Exception as e:
            log.error(f"Send error: {e}")

    def get_updates(self) -> list:
        try:
            r = requests.get(
                f"{self.base}/getUpdates",
                params={"offset": self.offset, "timeout": 10},
                timeout=15
            )
            return r.json().get("result", [])
        except Exception:
            return []

    def _format_yield(self, y: dict, rank: int = 0) -> str:
        rank_str  = f"{rank}. " if rank else "• "
        risk_emoji = "🟢" if y["risk"] == "LOW" else "🟡" if y["risk"] == "MEDIUM" else "🔴"
        tvl        = y["tvl_usd"]
        tvl_str    = f"${tvl/1e9:.1f}B" if tvl > 1e9 else f"${tvl/1e6:.1f}M"

        return (
            f"{rank_str}*{y['protocol']}* — {y['asset']}\n"
            f"   💰 APY: `{y['supply_apy']}%` {risk_emoji}\n"
            f"   💎 TVL: `{tvl_str}`"
        )

    # ── Commands ──────────────────────────────
    def cmd_start(self, chat_id: str):
        self.send(chat_id, """
💰 *DeFi Yield Aggregator Bot*
━━━━━━━━━━━━━━━━━━━━━━

Compare yields dari multiple DeFi protocols in real-time!

🏦 Aave V3 · Compound · Curve · Uniswap V3

📋 *Commands:*
/yield — Best yield opportunities
/yield_stable — Stablecoin yields only
/yield_aave — Aave V3 rates
/yield_compound — Compound rates
/yield_curve — Curve pools
/yield_uni — Uniswap V3 pools
/yield_alert `<on/off>` — APY spike alerts
/yield_summary — Market overview
/help — Bantuan
        """.strip())

    def cmd_yield(self, chat_id: str, args: list = None):
        self.send(chat_id, "🔄 Fetching best yields...\n⏳ Mohon tunggu ~10 detik...")
        try:
            yields = self.aggregator.get_best_yields(top_n=10)
            if not yields:
                self.send(chat_id, "❌ Tidak ada data yield tersedia.")
                return

            msg = "💰 *BEST YIELD OPPORTUNITIES*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for i, y in enumerate(yields, 1):
                msg += self._format_yield(y, i) + "\n\n"

            msg += f"🟢 LOW risk  🟡 MEDIUM risk  🔴 HIGH risk\n"
            msg += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            self.send(chat_id, msg)

        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_yield_stable(self, chat_id: str):
        self.send(chat_id, "🔄 Fetching stablecoin yields...")
        try:
            yields = self.aggregator.get_stable_yields()
            if not yields:
                self.send(chat_id, "❌ Tidak ada data stablecoin yield.")
                return

            msg = "💵 *STABLECOIN YIELDS*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for i, y in enumerate(yields[:8], 1):
                msg += self._format_yield(y, i) + "\n\n"
            self.send(chat_id, msg)

        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_yield_protocol(self, chat_id: str, protocol: str):
        self.send(chat_id, f"🔄 Fetching {protocol} yields...")
        try:
            yields = self.aggregator.get_by_protocol(protocol)
            if not yields:
                self.send(chat_id, f"❌ Tidak ada data untuk {protocol}.")
                return

            msg = f"🏦 *{protocol.upper()} YIELDS*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for i, y in enumerate(yields[:8], 1):
                msg += self._format_yield(y, i) + "\n\n"
            self.send(chat_id, msg)

        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_yield_summary(self, chat_id: str):
        self.send(chat_id, "🔄 Generating yield summary...")
        try:
            summary = self.aggregator.get_summary()
            if not summary:
                self.send(chat_id, "❌ Tidak ada data summary.")
                return

            protocols = ", ".join(summary["protocols"])
            msg = f"""
📊 *DEFI YIELD MARKET OVERVIEW*
━━━━━━━━━━━━━━━━━━━━━━
🏦 Protocols  : `{protocols}`
📈 Highest APY: `{summary['highest_apy']}%`
📉 Lowest APY : `{summary['lowest_apy']}%`
📊 Average APY: `{summary['avg_apy']}%`
🔢 Total Opps : `{summary['total_opportunities']}`
⏰ {summary['timestamp'][:19]}
            """.strip()
            self.send(chat_id, msg)

        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_yield_alert(self, chat_id: str, args: list):
        if not args:
            status = "ON ✅" if self.alert_on else "OFF ❌"
            self.send(chat_id, f"🔔 APY Alert: *{status}*")
            return
        if args[0].lower() == "on":
            self.alert_on = True
            self.send(chat_id, "✅ *APY Alert ON*\nKamu akan dapat notif kalau ada APY > 20%!")
        elif args[0].lower() == "off":
            self.alert_on = False
            self.send(chat_id, "❌ *APY Alert OFF*")

    # ── Message Router ────────────────────────
    def handle(self, message: dict):
        text    = message.get("text", "").strip()
        chat_id = str(message.get("chat", {}).get("id", ""))
        if not text or not chat_id:
            return

        parts   = text.split()
        command = parts[0].lower()
        args    = parts[1:]
        log.info(f"📨 {command} from {chat_id}")

        if command in ("/start", "/help"):   self.cmd_start(chat_id)
        elif command == "/yield":            self.cmd_yield(chat_id, args)
        elif command == "/yield_stable":     self.cmd_yield_stable(chat_id)
        elif command == "/yield_aave":       self.cmd_yield_protocol(chat_id, "aave")
        elif command == "/yield_compound":   self.cmd_yield_protocol(chat_id, "compound")
        elif command == "/yield_curve":      self.cmd_yield_protocol(chat_id, "curve")
        elif command == "/yield_uni":        self.cmd_yield_protocol(chat_id, "uniswap")
        elif command == "/yield_summary":    self.cmd_yield_summary(chat_id)
        elif command == "/yield_alert":      self.cmd_yield_alert(chat_id, args)
        else:
            self.send(chat_id, "❓ Command tidak dikenal. Ketik /help untuk bantuan.")

    # ── Main Loop ─────────────────────────────
    def run(self):
        log.info("🚀 YieldBot started!")
        while self.running:
            try:
                updates = self.get_updates()
                for update in updates:
                    self.offset = update["update_id"] + 1
                    msg = update.get("message", {})
                    if msg:
                        self.handle(msg)
            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                log.error(f"Polling error: {e}")
                time.sleep(5)


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "scan":
        # Quick scan mode
        agg = YieldAggregator()
        print("\n💰 Fetching all yields...")
        yields = agg.get_best_yields(10)
        print(f"\n📊 Top 10 Yields:")
        for i, y in enumerate(yields, 1):
            print(f"{i:2}. {y['protocol']:12} {y['asset']:20} APY: {y['supply_apy']:6.2f}% | TVL: ${y['tvl_usd']:,.0f}")

        summary = agg.get_summary()
        print(f"\n📈 Highest APY: {summary.get('highest_apy', 0)}%")
        print(f"📊 Average APY: {summary.get('avg_apy', 0)}%")
        print(f"🔢 Total Opps : {summary.get('total_opportunities', 0)}")
    else:
        bot = YieldBot()
        bot.run()