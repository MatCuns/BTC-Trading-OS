# Architettura R1 — INTERNAL_PAPER

Un processo Python 3.12/FastAPI gestisce feed, motore PAPER, rischio e API/WebSocket; PostgreSQL è il secondo servizio. React/TypeScript viene compilato e servito staticamente da FastAPI. Nessun Node persistente, Docker o WSL richiesto sul server. Ollama e intelligence restano R2.

## Confini e componenti

| File / componente | Responsabilità |
| --- | --- |
| `feed.py` | REST EEA, discovery FUTURES/xperp, ticker bid/ask, trade aggregati, funding pubblico opzionale, ping/pong e reconnect |
| `domain.py` | DTO tipizzati con environment_id, Decimal per quantità/prezzi/contabilità, metadata contratto |
| `engine.py` | Target, FLAT/HOLD/OPEN/REDUCE/REVERSE, riconciliazione, stop, kill switch e strategia di riferimento opt-in |
| `risk.py` | Gate indipendenti: freshness, persistenza, stato noto, cap tecnico 5x, cap configurato 1x, loss budget/costi/margine |
| `brokers.py` | Esecuzione interna parziale, fee, slippage, limiti; utility demo separata; stub LIVE che rifiuta sempre |
| `storage.py` | Transazioni PostgreSQL, versionamento ottimistico + advisory lock, ledger e audit idempotenti |
| `api.py` | Loopback, stato push, controlli PAPER, health, protezione origin/header per scritture locali |
| `scripts/*.ps1` | Setup riprendibile, start/stop con ownership PID, diagnostica redatta, backup e update esplicito |

## Dati

`market.event`: timestamp UTC dell'exchange e ingest_time, source, quality, payload_reference e hash deduplicato. Indice temporale per esportazione bulk. Il feed conserva quote validate; i contatori trade sono aggregati di sessione, non uno storico tick-by-tick completo.

`system.runtime`: checkpoint del motore INTERNAL_PAPER con versione. `paper` e `live` hanno account, orders, fills, positions, balances, snapshots, funding, requests e decisions separati. Vincoli CHECK sull'ambiente impediscono di usare etichette LIVE in tabelle PAPER. Chiavi uniche per client ID, fill e funding; FK fill -> order; snapshots includono conto, ultimo prezzo ed equity.

Il ruolo applicativo ha SELECT/INSERT/UPDATE nei soli schemi market/system/paper e SELECT su alembic_version. Non possiede schemi, non può DELETE/CREATE e non accede a live. L'amministratore viene usato localmente solo per bootstrap/migrazioni/restore separati, con password su stdin, mai nel repository. Nessuna migrazione distruttiva automatica.

Il runtime conserva 500 ordini completati + tutti i pending, 1.000 fill/request/funding e 500 decisioni; il DB conserva lo storico completo. Gli ID usciti dal checkpoint vengono ricercati nel ledger per mantenere l'idempotenza. Le scritture degli eventi immutabili vengono evitate con fingerprint in memoria. Checkpoint, conto, ordini e fill sono salvati nella stessa transazione. Il feed può essere registrato anche se il successivo checkpoint fallisce: nessuna esposizione viene resa disponibile senza commit del ledger.

## Esecuzione e guasti

Il target è esposizione nozionale/equity, firmata in [-5,+5]; default di configurazione 1x. Il budget pianificato 0,5% include stop e costi stimati e può imporre un target molto più basso. Il margine riserva anche i costi: il cap non è una promessa che un ordine a 5x sia ammissibile.

REVERSE: prima close reduce-only -> commit di fill e posizione piatta -> successivo tick e verifica -> open opposto. Timeout annulla il residuo e la seconda gamba. Un riavvio annulla residui PAPER, abbandona reverse pendenti, mantiene posizione/fill già persistiti, reinserisce kill switch e disabilita strategia.

Errori DB o commit ambiguo bloccano ogni nuovo ordine fino a un riavvio con riconciliazione. Feed stale blocca l'esecuzione senza vendite cieche. Stop/loss limit usano quote fresche e possono generare fill parziali o perdite oltre il livello previsto. Non sono stop garantiti. Il kill switch cancella entry e lascia le riduzioni protettive disponibili.

## Realismo e limiti

Solo contratti lineari con ctValCcy BTC e settle USD/USDC/USDT sono accettati; nessun cambio strumento con esposizione aperta. La valuta del ledger è quella di settlement, senza conversioni FX. MinNotional è un'ipotesi locale di 5 unità, dichiarata; non un vincolo OKX verificato. Fee maker/taker sono ipotesi configurate. Quote size limita il fill per tick; non si modella posizione in coda, impatto di mercato, liquidazione o ogni evento intratick. Funding applicato solo per eventi pubblici settled osservati dopo l'avvio; nessun backfill durante downtime. Esempi fixture sono sempre marcati sintetici.

ReferenceStrategy valuta ogni 60 secondi, dopo 60 osservazioni, medie 10/60 e volatilità; fallback FLAT. Nessuna efficacia finanziaria è stata misurata. LLM assente in R1 e nessun componente può abilitare LIVE.

## Storage e accesso

Dashboard solo 127.0.0.1:8765, accessibile attraverso il desktop remoto già scelto. data_root contiene log applicativi/esportazioni; backup_root è una destinazione esistente distinta. PostgreSQL mantiene il data_directory della sua istanza: il wizard lo mostra e non sposta cluster esistenti. Per una nuova installazione selezionare la cartella dati su HDD nell'installer ufficiale PostgreSQL. Ridondanza non sostituisce backup e prova di ripristino.
