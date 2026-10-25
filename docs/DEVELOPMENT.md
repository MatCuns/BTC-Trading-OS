# Come sviluppare, aggiungere e rimuovere funzioni

## Riprendere una sessione
1. Aprire MatCuns/BTC-Trading-OS e verificare remote, branch e modifiche locali.
2. Leggere AGENTS.md, STATUS, ARCHITECTURE e CHANGELOG.
3. Controllare PR/commit effettivi e codice; il merge non prova che la release sia installata sul server.
4. Scegliere una modifica circoscritta, un branch e criteri di accettazione.

## Aggiungere una funzionalità
- Scrivere obiettivo osservabile e punto di integrazione (collector, strategia, broker, API o UI).
- Verificare dipendenze, licenze/costi dei feed e limiti hardware.
- Implementare backend, schema/migrazione, API e UI necessari alla funzione.
- Usare toggle disabilitato se sperimentale; nessuna attivazione LIVE implicita.
- Testare comportamento e failure mode significativi; aggiornare documentazione e PR.
- Consegnare comandi esatti per installazione e collaudo Windows.

## Rimuovere una funzionalità
- Individuare utilizzi in codice, UI, configurazione, task Windows, dipendenze e dati.
- Disabilitare e scollegare i consumatori prima di rimuovere il componente.
- Rimuovere codice morto, configurazioni obsolete, dipendenze e test ormai non validi.
- Preservare storico ordini, eventi e audit. Archiviazione o migrazioni distruttive richiedono un piano esplicito dell'utente.
- Nessuna rimozione dei controlli rischio come effetto collaterale.
- Verificare avvio, compatibilità configurazioni e possibilità di rollback.
- Annotare modifica incompatibile e istruzioni per l'utente.

## Cambiare una funzione esistente
Descrivere prima/dopo con un esempio concreto. Prevedere migrazione di config/dati e compatibilità con le posizioni eventualmente aperte. Testare regressioni rilevanti.

## Prompt breve per Astra
Repository: https://github.com/MatCuns/BTC-Trading-OS
Leggi AGENTS.md e docs/STATUS.md, verifica branch/codice e continua dallo stato reale.
Modifica richiesta: [aggiungere / modificare / rimuovere + comportamento atteso].
Implementa su branch dedicato, verifica i contratti interessati e aggiorna documentazione e handoff.
Consegna PR, test eseguiti, limitazioni, comandi server e rollback.
Non inviare ordini LIVE e non cancellare dati operativi.

## Qualità e rilascio
Nessuna CI esiste ancora: sarà creata in R1. Documentazione sola richiede revisione di coerenza/link, non test applicativi inventati.
Release di codice: eseguire i controlli pertinenti e registrare quelli non disponibili.
main resta stabile; una PR integrata non aggiorna il server automaticamente.
