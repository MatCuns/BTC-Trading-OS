# Operazioni sul server

Stato: istruzioni preliminari; script applicativi non ancora esistenti.

## Responsabilità di Matteo
Preparare OS, dischi e backup, installare Git/Python 3.12/Node LTS/PostgreSQL/Ollama, selezionare percorsi reali, custodire segreti locali e collaudare le release.
Clone canonico: https://github.com/MatCuns/BTC-Trading-OS.git
Percorso codice suggerito: C:\BTCQuantOS. Data root e backup root sono ancora da definire.

## Responsabilità di Astra durante R1
Produrre setup.ps1, configure.ps1, start.ps1, stop.ps1, doctor.ps1 e verify_release.ps1, istruzioni complete, migrazioni e build UI.
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
