# Stato del progetto

Aggiornato il 25 ottobre 2026. Base letta: main `ca98d64ba03e654aa184c67e99428bfb2ea9a9cd` (PR #2 già integrata). Questa revisione introduce R1 sul branch `feat/r1-paper`; verificare sempre HEAD/CI effettivi.

## Implementato

- Backend Python 3.12/FastAPI e frontend React/TypeScript dark, sette sezioni, WebSocket push, grafico osservato, ordini/posizioni, rischio e diagnostica.
- Feed pubblico OKX EEA, discovery FUTURES/xperp senza swap hardcoded, size/precision lineari validate, clock sync, heartbeat/reconnect/stale, trade aggregati, funding opzionale. Fixture offline esplicita.
- Broker PAPER: fee/slippage configurati, partial fills, limiti, stop simulati; target long/short/flat, riduzioni, reverse in due fasi, client ID idempotenti.
- Risk engine indipendente: cap tecnico 5x/configurato 1x, budget trade 0,5%, daily loss/drawdown, costi, margine e blocco su persistenza/ordine/feed incerti. Kill switch UI e ReferenceStrategy opt-in, OFF al riavvio.
- PostgreSQL/Alembic: market/system e ledger PAPER/LIVE separati con CHECK e privilegi minimi; transazioni, checkpoint, startup reconciliation e storico durabile.
- START_PAPER.bat + wizard riprendibile, UPDATE_PAPER.bat, start/stop/health/doctor/verify, task al logon opzionale, backup e restore separato non distruttivo. Nessun prerequisito LLM.
- CI Linux/Windows, PostgreSQL reale, restore, controlli Python e frontend, browser desktop/mobile. Workflow release con ZIP comprensivo di UI compilata e SHA-256, eseguito solo dopo i check su main.

## Test e prove disponibili in questa revisione

- Localmente: ruff, mypy, 23 test Python unitari, TypeScript, 2 test Vitest e build Vite. Browser desktop e mobile verificati con backend di test esplicitamente in memoria; PostgreSQL reale verificato in CI Linux con bootstrap/privilegi e restore completo. Il run [40212619378](https://github.com/MatCuns/BTC-Trading-OS/actions/runs/40212619378) sul commit 2bf973149d4dd7f8b0874d097a387704e5789397 ha superato Linux/Windows con PostgreSQL, restore e browser desktop/mobile; il wizard Windows è stato eseguito in PowerShell 5.1 con configurazione esistente e senza aprire il browser. Le successive correzioni di guardia devono mantenere verde la CI dello SHA finale prima del merge.
- Probe pubblico reale: endpoint time e discovery OKX EEA rispondono 200/code 0. Trovato BTC-USD_UM_XPERP-310404, ctVal 0.0001 BTC, scadenza 4 aprile 2031. Un successivo smoke del connettore ha ricevuto una quote WebSocket reale (offset -173ms, lag puntuale 268ms); un altro probe ha avuto timeout. Non dichiarata affidabilità continuativa.
- Nessuna chiave, ordine reale, modifica di conto o attivazione LIVE.

## Non verificato / limiti espliciti

- Server Windows di Matteo, setup completo con installer e consensi OS, volumi/cluster PostgreSQL reali, backup fisico, GPU/CPU/RAM: **NOT TESTED**. Un runner Windows non è il server.
- Disponibilità dello strumento sul conto e demo, stop/margine/reduce-only effettivi exchange: NOT TESTED. Demo è una utility separata, non selezionabile dalla UI R1.
- Funding incompleto se API non disponibile o durante downtime; no modello di liquidazione/coda/market impact. Fee ipotizzate, nessuna valutazione di rendimento della strategia.
- data_root applicativo non trasferisce un cluster PostgreSQL esistente. Recovery unattended senza logon, gate LIVE e intelligence sono R3/R2.
- Release installata sul server: **non confermata**.

## Prossima azione per Matteo

Dopo pubblicazione della release verificata: scaricare lo ZIP PAPER ed eseguire START_PAPER.bat sul server. [Guida](START_HERE.md) e [collaudo](ACCEPTANCE.md). Nessuna PR da approvare.

## Handoff

PR [#3](https://github.com/MatCuns/BTC-Trading-OS/pull/3), branch feat/r1-paper; primo commit implementativo 5342c2e9f37b6e3a169bbd1f4e2be74afcd7455d; base nota ca98d64; codice/docs/test nella stessa revisione. In caso di CI fallita, correggere sul branch e verificare lo SHA finale prima del merge. Nessun tag PAPER finché i gate software disponibili non passano; collaudo server distinto. R2 non avviata. Vedere CHANGELOG, ARCHITECTURE, OPERATIONS e OKX_COMPATIBILITY.
