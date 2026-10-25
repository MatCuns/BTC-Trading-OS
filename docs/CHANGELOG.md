# Changelog

## 0.1.0-paper — 2026-10-25
- Implementato core PAPER, ledger PostgreSQL separati, rischio indipendente, feed OKX EEA con discovery e fixture esplicita.
- Aggiunti partial fills, fee/slippage, stop simulati, reverse durabile, idempotenza e riconciliazione al riavvio.
- Realizzata UI React con sette sezioni, grafici osservati, controlli PAPER, stato feed e diagnostica.
- Implementati wizard Windows riprendibile, launcher, script operativi, backup/restore isolato e aggiornamenti a tag PAPER espliciti.
- Aggiunti test Python/PostgreSQL, frontend/browser e CI Linux/Windows; release ZIP generata dopo i gate su main.
- LIVE disabilitato; AI e recovery unattended rimandati alle rispettive fasi. Collaudo sul server di Matteo non eseguito.

## Unreleased - 2026-10-25
- PR #1 già integrata in main; rimosse le istruzioni obsolete che chiedevano di approvarla.
- Nuova identità visiva BTC Quant OS, README di prodotto e concept del terminale chiaramente etichettato.
- START_HERE e tre prompt autosufficienti: nessun contratto comune da incollare separatamente.
- Mandato operativo autonomo: branch, test, PR e merge gestiti dall'agente dopo le verifiche.
- Requisito first_run/update per ridurre le operazioni manuali sul server; script ancora da implementare in R1.

### Preparazione precedente
- Aggiunti AGENTS.md e documenti STATUS, ARCHITECTURE, DEVELOPMENT e OPERATIONS.
- Documentato stato iniziale reale: nessuna applicazione o CI implementata.
- Definito flusso per aggiunta, modifica, rimozione e rilascio delle funzioni.
- README aggiornato con il punto di ingresso e le responsabilità.
- Nessun cambiamento a LICENSE. Nessun codice trading o accesso a fondi reali.

## Base iniziale
- main: fb7f89e46057f035c35e48a180264451ef0ce6f8.
- README minimo e licenza MIT.
