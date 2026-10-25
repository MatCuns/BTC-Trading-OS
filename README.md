<p align="center">
  <img src="docs/assets/hero.svg" alt="BTC Quant OS — Local intelligence. Explicit risk. Every decision traceable." width="100%" />
</p>

<p align="center">
  <a href="docs/START_HERE.md"><strong>Start here</strong></a> ·
  <a href="docs/STATUS.md"><strong>Project status</strong></a> ·
  <a href="docs/ARCHITECTURE.md"><strong>Architecture</strong></a> ·
  <a href="docs/prompts/01_R1_PAPER.md"><strong>Build with Astra</strong></a>
</p>

<p align="center">
  <img alt="Stage: pre-implementation" src="https://img.shields.io/badge/stage-pre--implementation-ffb454?style=flat-square" />
  <img alt="Platform target: Windows" src="https://img.shields.io/badge/platform-Windows-56c7ff?style=flat-square" />
  <img alt="Initial mode: PAPER" src="https://img.shields.io/badge/initial_mode-PAPER-4fe0b6?style=flat-square" />
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-a6b7d0?style=flat-square" /></a>
</p>

# A complete operating environment for BTC research and execution

**BTC Quant OS** is a local-first platform being built to connect Bitcoin market data, systematic decisions, independent risk controls and quantitative analytics in one desktop trading terminal.

The target: a Windows server that collects data around the clock, trades in a realistic internal paper environment, explains each decision and remains observable through a React dashboard. Local AI structures news and events; deterministic code owns orders, accounting and risk.

> **Current state — repository foundation.** Documentation, development prompts and visual direction are available. The trading engine, application UI, installer and CI are **not implemented yet**. The terminal below is a design concept, not a running product or a performance report. [See the authoritative status →](docs/STATUS.md)

## The terminal we are building

<p align="center">
  <img src="docs/assets/terminal-concept.svg" alt="Concept of the planned BTC Quant OS terminal. Illustrative curves only; no real market data, orders or returns." width="100%" />
</p>

<sub>DESIGN CONCEPT · Illustrative layout and curves · Not an application screenshot · No measured performance</sub>

## One platform. Three separate responsibilities.

| Market & execution | Intelligence & research | Operations & visibility |
| :--- | :--- | :--- |
| OKX regional REST/WebSocket adapters | Macro, cross-asset and crypto context | React + TypeScript terminal |
| Internal paper broker on live prices | News and authorized social collectors | Orders, positions and decision audit |
| Long / short / flat target exposure | Local Ollama structured extraction | Equity, drawdown and cost analytics |
| Idempotent orders and reconciliation | Provenance, freshness and deduplication | Process, feed and backup health |
| Independent exposure and loss limits | Versioned scores and model evaluation | Windows startup and crash recovery |

*The table describes the planned scope. Availability is tracked in [STATUS](docs/STATUS.md), not implied by this overview.*

## The architecture

```mermaid
flowchart TD
    M["OKX market feeds"] --> C["Market collector"]
    N["Authorized news and macro sources"] --> I["Collectors and local Ollama"]
    C --> D["Deterministic decision engine"]
    I --> D
    D --> R["Independent risk engine"]
    R --> B["Environment-specific broker"]
    B --> P["PostgreSQL ledger and audit"]
    C --> P
    I --> P
    P --> U["FastAPI and React terminal"]
```

The LLM cannot issue orders, execute shell commands or access trading secrets. A slow intelligence queue must not delay protective position management. PAPER, DEMO and LIVE use separate execution and accounting contexts.

## From first simulation to evaluated live capability

| Milestone | What it delivers | Current state |
| :--- | :--- | :--- |
| **Foundation** | Repository identity, documentation, handoff and autonomous development instructions | Available |
| **R1 · Paper core** | Live public feed, internal broker, ledger, risk controls, first UI and guided Windows setup | Next to build |
| **R2 · Intelligence** | Local AI, collectors, event scoring, research views and complete analytics UI | Planned |
| **R3 · Operations** | Recovery, reconciliation, verified regional adapter and explicit live-readiness gates | Planned |

Development agents are authorized to implement, verify and merge their own requested changes. Passing applicable checks is required; a merge does not automatically deploy software to the server or activate real-money trading.

## Start building — one instruction

Open this repository in an Astra development environment and send:

```text
Lavora su https://github.com/MatCuns/BTC-Trading-OS.
Leggi AGENTS.md e docs/STATUS.md, poi esegui integralmente
docs/prompts/01_R1_PAPER.md.
Implementa, verifica e integra autonomamente le modifiche in main.
Non lasciarmi PR da approvare. Consegna la release PAPER e il wizard Windows.
```

**No PDF attachment or separate preamble is needed.** Each [master prompt](docs/prompts) is self-contained. Server-specific choices belong in the guided installer the agent will build, not in manual source-code edits. [Istruzioni complete per Matteo →](docs/START_HERE.md)

## Built around the hardware already available

| Component | Initial design target |
| :--- | :--- |
| Host | Windows x64 · Intel Xeon E3-1220 v3 · 16 GB DDR3 |
| Local model | Ollama `qwen3:1.7b` · one request at a time · short validated JSON |
| GPU | GTX 1050 Ti 4 GB · actual offload and latency to be measured |
| Storage | Existing 128 GB system SSD + mirrored HDD data volume |
| Stack | Python 3.12 · FastAPI · PostgreSQL · React · TypeScript |
| Access | Localhost dashboard through Chrome Remote Desktop |

No mandatory Docker, WSL, new GPU or paid social feed. The chosen model is a starting configuration to benchmark, not a promise of accuracy or latency.

## Engineering principles

- **Evidence before confidence.** Missing or stale data is visible. Probabilities are not presented as calibrated without out-of-sample evidence.
- **Costs belong in the ledger.** Fees, spread, simulated slippage and funding are accounted for explicitly.
- **Regional compatibility is a requirement.** The actual OKX account and instrument must be verified against official documentation. No silent substitution with a global perpetual contract.
- **Durable state before new exposure.** Unknown order state, failed persistence or critical stale feeds block new entries.
- **Autonomous development, explicit live activation.** Agents own code delivery. Capital deployment remains separate.

## Find the right document

| Question | Document |
| :--- | :--- |
| What do I do now? | [START_HERE](docs/START_HERE.md) |
| What is actually implemented? | [STATUS](docs/STATUS.md) |
| What should an agent read first? | [AGENTS](AGENTS.md) |
| How do the components connect? | [ARCHITECTURE](docs/ARCHITECTURE.md) |
| How do we add, change or remove features? | [DEVELOPMENT](docs/DEVELOPMENT.md) |
| How is the Windows server operated? | [OPERATIONS](docs/OPERATIONS.md) |
| Which full prompt comes next? | [R1](docs/prompts/01_R1_PAPER.md) · [R2](docs/prompts/02_R2_INTELLIGENCE.md) · [R3](docs/prompts/03_R3_OPERATIONS.md) |
| What changed? | [CHANGELOG](docs/CHANGELOG.md) |

<details>
<summary><strong>Execution environments and real-money scope</strong></summary>

**INTERNAL_PAPER** simulates execution against live market input, with explicit assumptions. **OKX_DEMO** tests supported exchange API behavior using demo credentials. **OKX_LIVE** is planned and remains disabled until account eligibility, instrument specifications, operations and forward evidence have been evaluated.

The technical exposure ceiling is 5×, with a lower initial default. This is an application limit, not a guarantee of product availability or a recommendation to use leverage. X-Perps have expiry and product-specific mechanics. Stop orders do not guarantee a maximum loss. No return, profitability or OKX certification is claimed.

</details>

---

<p align="center"><strong>LOCAL INTELLIGENCE · EXPLICIT RISK · TRACEABLE DECISIONS</strong><br/><sub>Created by Matteo Cunsolo · Independent project, not affiliated with OKX · MIT licensed</sub></p>
