# Stato del progetto

Ultimo aggiornamento: 25 ottobre 2026.
Questo è il punto di ingresso per riprendere lo sviluppo. Si riferisce al branch che lo contiene; verificare sempre branch e commit aperti.

## Situazione verificata
- Base ispezionata: main, commit fb7f89e46057f035c35e48a180264451ef0ce6f8.
- Su quella base esistevano soltanto README.md e LICENSE (MIT).
- Questo aggiornamento aggiunge documentazione di coordinamento e istruzioni agenti.
- Nessun codice applicativo, schema DB, UI, script Windows o pipeline CI è stato implementato.
- Nessuna release installabile e nessun test di trading eseguito.
- Setup e prestazioni del server dell'utente: non verificati.
- Disponibilità del prodotto e abilitazione del conto OKX: non verificate.
- Modalità LIVE: non implementata e non attivata.

## Roadmap
| Release | Risultato | Stato |
| --- | --- | --- |
| R1 | Feed OKX, broker PAPER, ledger PostgreSQL, rischio e prima UI | Da implementare |
| R2 | Collector, Ollama, scoring e analytics/UI completa | Pianificata |
| R3 | Recupero, avvio automatico, adapter verificato e gate LIVE | Pianificata |

## Prossima azione
1. Integrare la PR di documentazione in main.
2. Matteo prepara Windows, percorsi dati, PostgreSQL, Ollama e checkout locale secondo il manuale.
3. Astra esegue il Prompt A sul repository canonico, dopo aver letto AGENTS.md.
4. Creare docs/OKX_COMPATIBILITY.md e script completi per setup/collaudo durante R1.

## Blocchi e informazioni mancanti
Percorso dati/backup reale, versione e supporto Windows, versioni installate, regione/abilitazione OKX, esito benchmark Ollama. Non inserire credenziali qui.

## Handoff da aggiornare in ogni sessione
- Branch e PR di lavoro: indicare il branch corrente e il link della PR.
- Ultimo commit noto: indicare SHA disponibile, non inventare il commit che contiene questo testo.
- Implementato: elenco breve con percorsi.
- Test eseguiti: comandi, ambiente, esiti.
- Non testato: controlli Windows/exchange ancora da eseguire.
- Problemi aperti: sintomo e prossimo controllo.
- Prossima azione concreta: un'attività eseguibile.
- Release installata sul server: ignota finché Matteo non la conferma; non dedurla dal merge.
