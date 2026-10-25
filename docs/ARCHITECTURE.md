# Architettura prevista

Stato: proposta, nessun componente applicativo ancora realizzato.

## Runtime sul server Windows
- Backend Python/FastAPI: collector di mercato, strategia, broker, risk engine, API e UI compilata.
- PostgreSQL locale: dati di mercato, intelligence e ledger separati PAPER/LIVE.
- Ollama locale: qwen3:1.7b iniziale, una richiesta per volta, 2048 token iniziali; benchmark da eseguire.
- Worker intelligence se necessario: coda bounded, collector autorizzati e JSON validato.
- React/TypeScript: build statica servita da FastAPI, nessun Node persistente necessario in produzione.

## Flussi
OKX pubblico -> collector -> rischio/strategia -> broker PAPER -> ledger -> UI.
News/fonti -> collector -> Ollama -> evento validato -> score -> strategia.
Il broker LIVE sarà separato e disabilitato fino ai gate R3 e alla decisione dell'utente.

## Dati e confini
Codice e documentazione su GitHub; database, modelli, segreti e log sul server.
DB su HDD ridondanti; backup su destinazione separata, con restore verificato.
Dashboard e servizi locali su loopback; accesso tramite Chrome Remote Desktop.
Repo pubblico: nessun dato di conto o segreto deve essere versionato.

## Contratti da definire in R1
BrokerAdapter, eventi di mercato, ledger idempotente, stati ordini e riconciliazione, API UI, limiti rischio.
Convalidare specifiche e strumenti OKX SEE nelle docs regionali: gli X-Perps sono contratti con scadenza.

Aggiornare questo file quando il codice realizza o cambia questa proposta.

