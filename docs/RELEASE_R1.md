R1 introduces the **BTC Quant OS internal PAPER terminal** for Windows x64. It does not enable real trading.

Download **BTC-Quant-OS-v0.1.0-paper.zip**, extract it, then double-click **START_PAPER.bat**. The compiled React UI is included. The wizard checks Python 3.12 and PostgreSQL, gives official installation steps where needed, preserves local configuration, creates a least-privilege runtime role and opens http://127.0.0.1:8765. No OKX API key, Docker, WSL, Node server or Ollama is required for the release ZIP.

Included: EEA public X-Perp discovery, live ticker/trade connector, internal broker with partial fills/fees/slippage, stops and independent risk gates, durable PostgreSQL ledgers, two-phase reverse, restart reconciliation, UI controls/observability, guided setup, update, backup and isolated restore drill.

Kill switch starts ON and reference strategy OFF. Fixture mode is explicitly synthetic. LIVE is disabled and has no API execution route. Demo adapter is a separately tested integration utility, not an operational UI mode.

Software gates: Linux and Windows PostgreSQL tests, PowerShell parsing and Windows process boot, full isolated restore, strict Python checks, React typecheck/unit/build and desktop/mobile browser tests. See the workflow attached to the release commit for actual output.

**Not tested on Matteo's Windows server:** full installer with its OS prompts, real disk locations/backup destination, continuous OKX WebSocket reliability, hardware load and extended forward trading. Public discovery does not prove account eligibility. Simulated fills do not reproduce queue position, liquidation or guaranteed stops; funding can be incomplete across downtime. No profitability is claimed.

[Start here](https://github.com/MatCuns/BTC-Trading-OS/blob/main/docs/START_HERE.md) · [Server guide](https://github.com/MatCuns/BTC-Trading-OS/blob/main/docs/OPERATIONS.md) · [Acceptance](https://github.com/MatCuns/BTC-Trading-OS/blob/main/docs/ACCEPTANCE.md) · [OKX compatibility](https://github.com/MatCuns/BTC-Trading-OS/blob/main/docs/OKX_COMPATIBILITY.md)
