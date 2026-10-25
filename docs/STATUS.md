# Stato del progetto

Aggiornato il 25 ottobre 2026. Base letta: main `ca98d64ba03e654aa184c67e99428bfb2ea9a9cd` (PR #2 già integrata). R1 implementata e verificata; consegna tramite PR [#3](https://github.com/MatCuns/BTC-Trading-OS/pull/3), branch `feat/r1-paper`. Controllare HEAD reale: il riferimento di test seguente identifica il codice verificato senza inventare lo SHA di questa revisione documentale.

## Implementato

- Backend Python 3.12/FastAPI e frontend React/TypeScript dark, sette sezioni, WebSocket push, grafico osservato, ordini/posizioni, rischio e diagnostica.
- Feed pubblico OKX EEA, discovery FUTURES/xperp senza swap hardcoded, size/precision lineari validate, clock sync, heartbeat/reconnect/stale, trade aggregati, funding opzionale. Fixture offline esplicita.
- Broker PAPER: fee/slippage configurati, partial fills, limiti, stop simulati; target long/short/flat, riduzioni, reverse in due fasi, client ID idempotenti.
- Risk engine indipendente: cap tecnico 5x/configurato 1x, budget trade 0,5%, daily loss/drawdown, costi, margine e blocco su persistenza/ordine/feed incerti. Kill switch UI e ReferenceStrategy opt-in, OFF al riavvio.
- PostgreSQL/Alembic: market/system e ledger PAPER/LIVE separati con CHECK e privilegi minimi; transazioni, checkpoint, startup reconciliation e storico durabile.
- START_PAPER.bat + wizard riprendibile, UPDATE_PAPER.bat, start/stop/health/doctor/verify, task al logon opzionale, backup e restore separato non distruttivo. Nessun prerequisito LLM.
- CI Linux/Windows, PostgreSQL reale, restore, controlli Python e frontend, browser desktop/mobile. Workflow release con ZIP comprensivo di UI compilata e SHA-256, eseguito solo dopo i check su main.

## Test e prove disponibili in questa revisione

- Localmente: ruff, mypy, **23 test Python unitari**, TypeScript, **2 test Vitest**, build Vite e **2 test browser desktop/mobile** con backend di test esplicitamente in memoria. Due integrazioni PostgreSQL sono escluse solo dal test locale senza DB.
- **CI PASS** sul codice `0992cd48ee719a72b83a79841df03012ee2b9b26`: [run 40213022097](https://github.com/MatCuns/BTC-Trading-OS/actions/runs/40213022097). **25 test Python su Linux/PostgreSQL 16 e 25 su Windows/PostgreSQL 17**, bootstrap riprendibile, privilegi minimi, backup con ruolo applicativo e restore completo isolato. Ruff/format/mypy PASS; 2 Vitest e 2 browser desktop/mobile con PostgreSQL reale PASS.
- **Windows runner PASS:** parsing di tutti gli script e first_run con configurazione esistente in **PowerShell 5.1**, installazione dipendenze/build UI, start/health/verify/stop; browser non aperto nel test. Nessun task permanente o installer OS eseguito in CI. Il percorso con scelte interattive e consensi installer sul server reale resta NOT TESTED.
- Probe pubblico reale: endpoint time e discovery OKX EEA rispondono 200/code 0. Trovato BTC-USD_UM_XPERP-310404, ctVal 0.0001 BTC, scadenza 4 aprile 2031. Un successivo smoke del connettore ha ricevuto una quote WebSocket reale (offset -173ms, lag puntuale 268ms); un altro probe ha avuto timeout. Non dichiarata affidabilità continuativa.
- Nessuna chiave, ordine reale, modifica di conto o attivazione LIVE.

## Non verificato / limiti espliciti

- Server Windows di Matteo, setup completo con installer e consensi OS, volumi/cluster PostgreSQL reali, backup fisico, GPU/CPU/RAM: **NOT TESTED**. Un runner Windows non è il server.
- Disponibilità dello strumento sul conto e demo, stop/margine/reduce-only effettivi exchange: NOT TESTED. Demo è una utility separata, non selezionabile dalla UI R1.
- Funding incompleto se API non disponibile o durante downtime; no modello di liquidazione/coda/market impact. Fee ipotizzate, nessuna valutazione di rendimento della strategia.
- data_root applicativo non trasferisce un cluster PostgreSQL esistente. Recovery unattended senza logon, gate LIVE e intelligence sono R3/R2.
- Release installata sul server: **non confermata**.

## Prossima azione per Matteo

Scaricare lo ZIP dalla release `v0.1.0-paper` ed eseguire START_PAPER.bat sul server. Il workflow pubblica il tag/asset soltanto dopo i check su main; se la pubblicazione non è ancora conclusa, controllare la pagina Actions senza ricostruire R1. [Guida](START_HERE.md) e [collaudo](ACCEPTANCE.md). Nessuna PR da approvare.

## Handoff

PR [#3](https://github.com/MatCuns/BTC-Trading-OS/pull/3), branch feat/r1-paper; ultimo commit applicativo verificato `0992cd48ee719a72b83a79841df03012ee2b9b26`, base main ca98d64. Questa revisione finale aggiorna solo la registrazione delle evidenze. L'agente verifica nuovamente HEAD e integra la propria PR dopo la CI finale; pubblicazione automatica dello ZIP dopo i gate su main. Installazione sul server non confermata. R2 non avviata. Vedere CHANGELOG, ARCHITECTURE, OPERATIONS e OKX_COMPATIBILITY.
