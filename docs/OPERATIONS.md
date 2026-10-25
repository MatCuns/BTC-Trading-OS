# Operazioni sul server

Stato: istruzioni preliminari; script applicativi non ancora esistenti.

## Responsabilità di Matteo
Avviare sul server il wizard consegnato da R1, indicare i volumi reali, fornire eventuali consensi Windows e custodire i segreti locali. Il wizard deve ridurre le installazioni/configurazioni manuali. Se Astra ha accesso diretto autorizzato al server può eseguire i passaggi reversibili; senza tale accesso Matteo avvia la procedura e comunica il report redatto.
Clone canonico: https://github.com/MatCuns/BTC-Trading-OS.git
Percorso codice suggerito: C:\BTCQuantOS. Data root e backup root sono ancora da definire.

## Responsabilità di Astra durante R1
Produrre START_PAPER.bat come launcher a doppio clic per first_run.ps1, ingresso unico, update.ps1 per gli aggiornamenti, oltre a setup/configure/start/stop/doctor/verify_release come componenti interni documentati. first_run rileva prerequisiti, gestisce versioni/dipendenze ufficiali, selezione data/backup root, PostgreSQL a privilegi minimi, build/migrazioni, smoke test e UI PAPER senza chiavi OKX. Nessuna formattazione o sovrascrittura di istanze DB. R2 aggiunge Ollama e benchmark. Gestire interruzione/ripresa e rollback. Oggi questi script non esistono ancora.
Non chiedere all'utente di eseguire script che non sono ancora nel repository.
Specificare prerequisiti, parametri, output attesi, ambiente e rollback.
Nessuna porta pubblica o runner CI con chiavi di trading sul server.

## Aggiornamenti dopo R1
Leggere note release -> backup verificato -> fermare app -> scaricare commit/tag approvato -> installare dipendenze/build -> migrazioni -> collaudo -> avvio.
Non automatizzare deploy LIVE in seguito a un push.
Conservare il commit installato localmente e comunicarlo per la diagnosi.
Il rollback codice non annulla automaticamente migrazioni del database.
Restore prima su database separato; riconciliare con exchange prima di riprendere operatività reale.

## Segreti e diagnostica
Chiavi API e password mai su GitHub o in chat. Usare configuratore locale; in R3 adottare secret store Windows con ACL.
Diagnostica redatta: versione, commit, stato servizi, timestamp, errori privi di token/password e risultati dei check.


L’agente integra le proprie PR dopo i controlli, senza interventi GitHub di Matteo. Per iniziare lo sviluppo non è richiesto un setup Windows già completato.
