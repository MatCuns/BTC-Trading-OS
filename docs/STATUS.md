# Stato del progetto

Ultimo aggiornamento: 25 ottobre 2026. Riferimento iniziale di questa revisione: `main` a `7fa3d0192901c741c81a166a67d0872e9e57486f` (PR #1 già integrata). Questo file descrive il branch che lo contiene: controllare sempre HEAD reale.

## In una frase

**Preparazione del repository completata; sviluppo applicativo R1 da avviare con Astra.**

## Disponibile

- README di prodotto, asset grafici e mockup concettuale del terminale.
- AGENTS.md: mandato autonomo per modifiche, test, PR e merge delle modifiche autorizzate.
- START_HERE: una sola istruzione per iniziare, senza allegare il PDF.
- Tre mega prompt autosufficienti in docs/prompts.
- Guide di architettura prevista, sviluppo, operazioni e cronologia.

## Non ancora implementato

Codice applicativo, feed OKX, broker PAPER, schema DB, UI funzionante, Ollama integrato, script first_run/update, CI, release installabili e modalità LIVE. Il mockup nel README non è un'app eseguibile.

## Roadmap e gate

| Fase | Risultato da ottenere | Stato |
| --- | --- | --- |
| Preparazione repo | Identità, documenti, prompt e continuità | Completata nel branch di questa revisione |
| R1 | Feed pubblico, PAPER, PostgreSQL, rischio, UI e wizard | Da implementare |
| R2 | Collector, Ollama, score, analytics e UI completa | Pianificata |
| R3 | Recupero/boot, adapter regionale verificato e gate LIVE | Pianificata |

## Prossima azione concreta

Matteo seleziona il repository nell'ambiente Astra e usa il messaggio in [START_HERE](START_HERE.md). Astra legge ed esegue [Prompt A](prompts/01_R1_PAPER.md), costruisce R1 e integra la propria PR dopo i controlli. Nessuna operazione manuale su PR #1: è già stata integrata.

## Verifiche e limiti

- Verificati: contenuto iniziale del repository, merge PR #1, accesso GitHub nella sessione che prepara questi documenti.
- In questa revisione: controllo di coerenza/link dei documenti e rendering degli asset; nessun test applicativo esistente.
- Non verificati: setup Windows, percorsi dati/backup, versioni locali, benchmark GPU/LLM, prodotto/abilitazione del conto OKX.
- Release installata sul server: ignota. Non dedurla da main.
- LIVE: non implementato e mai attivato.

## Handoff obbligatorio per ogni sessione

Branch/PR e ultimo commit noto; file implementati; comandi di test con ambiente/esito; controlli non eseguiti; problemi aperti; prossima azione; release installata sul server se confermata. Non inventare lo SHA del commit che sta ancora per essere creato.
