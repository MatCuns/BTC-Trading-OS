# Istruzioni per gli agenti - BTC Trading OS

## Identità e contesto
- Repository canonico: https://github.com/MatCuns/BTC-Trading-OS
- Branch stabile: main. Prima di scrivere verificare origin e branch.
- Leggere prima docs/STATUS.md, poi docs/ARCHITECTURE.md e docs/CHANGELOG.md.
- Il codice e i test sono evidenza primaria: STATUS non sostituisce l'ispezione.
- Il repository è pubblico alla verifica del 25 ottobre 2026. Mai inserire segreti, log non redatti o dati di conto.

## Lavoro e consegna
- Usare un feature branch e una PR. L'utente autorizza l'agente a integrare automaticamente la propria PR dopo i controlli applicabili, senza chiedergli di premere Merge.
- Controllare HEAD e integrare solo lo SHA verificato. Non unire PR estranee, non aggirare check o protezioni, non abilitare auto-merge indiscriminato.
- Distinguere merge del codice e installazione sul server. Non attendere approvazione utente per il normale lavoro di sviluppo già autorizzato.
- I prompt completi sono in docs/prompts; l'ingresso per Matteo è docs/START_HERE.md.
- Preservare il lavoro esistente e LICENSE. Non sovrascrivere o cancellare modifiche umane.
- Implementare file reali e verificare le funzionalità interessate.
- Distinguere sempre implementato, testato in CI, verificato sul server Windows e pianificato.
- Aggiornare docs/STATUS.md e docs/CHANGELOG.md in ogni PR che cambia comportamento.
- Aggiornare ARCHITECTURE per cambi di componenti/dati; OPERATIONS per avvio, configurazione, dipendenze o deploy.
- Aggiornare docs/OKX_COMPATIBILITY.md quando cambia un adapter OKX; crearlo durante R1.
- Se la sessione termina a metà, registrare branch, riferimenti ai commit disponibili, test eseguiti, blocchi e prossima azione.
- Non inventare SHA autoreferenziali: usare il commit precedente noto e il link alla PR; annotare la revisione definitiva quando disponibile.
- Per aggiungere, rimuovere o modificare funzionalità seguire docs/DEVELOPMENT.md.
- Non cancellare questi documenti per fare pulizia: mantenerli brevi e aggiornati, evitando copie duplicate.

## Vincoli di progetto
Windows, Xeon E3-1220 v3, 16 GB DDR3, GTX 1050 Ti 4 GB, SSD sistema 128 GB, HDD ridondanti.
Python 3.12, FastAPI, PostgreSQL, React/TypeScript compilato, Ollama qwen3:1.7b come configurazione iniziale.
Nessun Docker/WSL o nuovo hardware obbligatorio. Percorsi dati configurabili.
PAPER interno su feed live prima di DEMO e LIVE. Nessun ordine LIVE durante lo sviluppo.
LLM asincrono senza accesso a broker, shell o segreti. Il rischio resta indipendente.

## Integrazione OKX
Verificare docs regionali e strumento effettivo: non assumere BTC-USDT-SWAP.
X-Perps ha scadenza; verificare tipo, metadata, contract size, tick/lot, fee e restrizioni del conto.
Nessuna sostituzione silenziosa del prodotto. Funzioni non supportate restano esplicite e bloccate.
Nessun test deve inviare ordini reali, modificare account reali o cancellare dati operativi.


## Identità visiva e stato reale
Preservare il marchio BTC Quant OS, gli asset in docs/assets e la struttura leggibile del README.
Il mockup del terminale è un concept, non screenshot di software funzionante. Non rimuovere questa distinzione finché la UI reale non è disponibile.
Non mostrare badge di CI verde, copertura o rendimenti inventati. Aggiornare status e release solo su evidenze.

## Procedura guidata come requisito R1
Creare scripts/first_run.ps1 e scripts/update.ps1; non affermare che esistano prima di averli implementati.
Gestire dipendenze ufficiali, percorsi, database e avvio in un percorso riprendibile. Nessun segreto in GitHub, nessuna formattazione o ordine LIVE.
Se l'agente lavora in cloud, non chiedere un setup Windows preventivo per poter cominciare a scrivere e verificare il codice.
