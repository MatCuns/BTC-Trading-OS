# Procedura server — R1 PAPER

## Prima installazione: ingresso unico

1. Scarica l'asset **BTC-Quant-OS-v0.1.0-paper.zip** dalla [release PAPER](https://github.com/MatCuns/BTC-Trading-OS/releases/tag/v0.1.0-paper). Estrai tutto, per esempio in `C:\BTCQuantOS`; evita cartelle condivise. Non eseguire lo script dentro lo ZIP.
2. Fai doppio clic su **START_PAPER.bat**. Tieni aperta la finestra: se manca un prerequisito, indica un solo passo preciso con il link ufficiale. Eseguilo e riapri lo stesso BAT; i passaggi completati restano disponibili.
3. Indica due cartelle **già esistenti**, data_root e backup_root, preferibilmente su destinazioni fisiche diverse. Inserisci porta e amministratore PostgreSQL esistenti e la password localmente, nascosta. Il wizard crea un ruolo applicativo limitato e un database dedicato senza sovrascrivere omonimi.
4. Scegli **okx** per feed pubblico senza chiavi oppure **fixture** per simulazione sintetica offline. Si apre `http://127.0.0.1:8765`. Attendi il feed: solo dopo, se vuoi effettuare simulazioni, premi **Unlock PAPER execution**. Reference strategy resta OFF finché non attivi il toggle.

Non servono account/API key OKX per PAPER. Non è richiesta installazione preventiva per leggere il repository o sviluppare in cloud. Il wizard non installa Ollama, non espone servizi in rete, non formatta dischi e non rimuove Storj.

## Prerequisiti rilevati dal wizard

| Dipendenza | Fonte ufficiale / scelta |
| --- | --- |
| Windows x64 | Sistema esistente; nessuna modifica alla policy PowerShell globale |
| Python 3.12 x64 + launcher py | https://www.python.org/downloads/windows/ |
| PostgreSQL 16 o 17 | https://www.postgresql.org/download/windows/ ; includere command line tools, conservare password admin localmente |
| Node.js 22 LTS o 24 LTS | https://nodejs.org/en/download ; **solo checkout sorgente**. Lo ZIP release contiene già React compilato |
| Git | Solo per update di un checkout Git; non richiesto per avviare lo ZIP |

Gli installer ufficiali possono richiedere il consenso Windows. Il wizard non lo elude e non accetta contratti al posto tuo. Non assume winget. Se PostgreSQL è già presente, usa quell'istanza; non crearne una seconda. Per un'installazione PostgreSQL nuova seleziona nell'installer il data directory desiderato sul volume HDD.

**Percorsi:** data_root contiene log ed export applicativi. PostgreSQL conserva il `data_directory` della sua istanza, mostrato dal bootstrap; il wizard non trasferisce il cluster su un altro disco. Prima di affidarti allo storage ridondante, controlla che il cluster risieda davvero sul volume desiderato. backup_root non deve coincidere con data_root; due cartelle sullo stesso disco non costituiscono un backup separato.

## Ripresa dopo errore

Riapri START_PAPER.bat. `.runtime/setup-state.json` registra l'ultimo passo, `.env` esistente viene preservato. Un journal temporaneo locale protetto consente di completare un bootstrap interrotto dopo la creazione del ruolo/DB; la password amministrativa deve essere reinserita. Database/ruoli preesistenti senza questo journal sono rifiutati, mai sostituiti.

Non copiare `.env`, journal bootstrap o log grezzi in GitHub/chat. Se hai perso la configurazione di un database esistente, recuperala da un backup locale e verifica con l'amministratore; non cancellare il database per ripetere il wizard.

## Comandi operativi in ordine

Da PowerShell nella cartella estratta; ogni `-ExecutionPolicy Bypass` vale solo per il processo avviato:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\health.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_release.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\doctor.ps1
```

Salute attesa: environment INTERNAL_PAPER, live_enabled false, database true, reconciled true. KILL_SWITCH è normale al primo avvio. STALE_FEED deve sparire dopo la prima quote valida; in caso contrario vedere System/feed message. Nessuna apertura mentre i gate sono bloccati. Se il DB si interrompe, correggi il servizio/configurazione, ferma e riavvia l'app: non esiste un retry cieco di ordini.

Per fermare:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\stop.ps1
```

Il processo viene identificato tramite PID, percorso Python e command line; nessun kill indiscriminato. Al riavvio, ordini PAPER pendenti vengono cancellati, posizione già persistita mantenuta, kill switch ON e strategia OFF.

## Feed e impostazioni

Modifica localmente `.env` con app ferma. Esempi in `.env.example`. `BTC_FEED_MODE=fixture` è sempre sintetico ed etichettato; nessun fallback nascosto. In caso di più prodotti, usa `BTC_INSTRUMENT_ID` con l'ID indicato dalla discovery; non inserire uno swap come sostituto. Le modifiche a limiti/fee richiedono riavvio. La strategia si abilita dalla UI; il flag di ambiente non è un'autorizzazione a riprendere trading dopo un riavvio.

La quantità in tabella è in contratti, non BTC: nozionale = contratti × contract_btc × prezzo. Il capitale iniziale di 10.000 unità è simulato, senza versamenti. Il target predefinito 0,25x con stop 1% è solo un esempio PAPER. Riduci il target se il rischio rifiuta l'ordine; non allargare i limiti per far sparire l'errore.

## Backup e restore non distruttivo

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\backup.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\restore_check.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\restore_check.ps1 -Full
```

Il primo crea un dump PostgreSQL nei percorsi scelti. Il secondo verifica che l'archivio sia leggibile, **non** prova un restore completo. `-Full` richiede l'admin locale via stdin e ripristina solo in un **nuovo** DB `btc_restore_check_*`, controllando runtime e fill. Non sostituisce e non elimina database; il DB di prova rimane per revisione locale. La CI prova un restore completo su DB isolati Linux/Windows, distinto dal tuo disco/server.

Il dump applicativo include paper, system e market. Conserva a parte `.env` protetto: il dump non include credenziali, ruoli cluster o schemi LIVE. Restore operativo e riallineamento delle credenziali richiedono un piano separato. Per esportare eventi market oltre 30 giorni senza cancellarli: `.\.venv\Scripts\python.exe -m btc_os.cli archive`. Nessun pruning distruttivo automatico; sorvegliare spazio disco.

## Update e rollback

Su checkout Git: doppio clic UPDATE_PAPER.bat. Accetta solo un tag PAPER pubblicato, verifica origin e working tree pulito, effettua backup/check archivio, ferma app, seleziona il tag esatto, reinstalla dipendenze, ricompila la UI e verifica. Non si aggiorna a ogni push e non avvia LIVE. R1 usa solo migrazione 0001; upgrade di schema futuri richiedono uno step admin dedicato.

Su ZIP: estrai una nuova release in **nuova cartella**, conserva la vecchia, copia solo `.env` localmente e avvia il nuovo START_PAPER.bat dopo avere fermato la vecchia app. Non avviare due copie sullo stesso DB. Rollback: ferma la nuova versione, riapri START_PAPER.bat nella vecchia cartella. In Git lo script salva `.runtime/rollback-commit.txt` e ripristina il codice precedente se l'avvio fallisce; ripeti START_PAPER.bat per ricompilare. Un rollback codice non annulla migrazioni SQL e non ripristina automaticamente i dati.

## Avvio al logon e diagnosi

`install_tasks.ps1` crea, solo su invocazione esplicita, un task al logon dell'utente con privilegi limitati. Nessuna password amministrativa o task SYSTEM. Rollback: `install_tasks.ps1 -Remove`. Non eseguirlo durante i test. Il boot senza logon e recovery unattended completo appartengono a R3.

`doctor.ps1` produce `.runtime/doctor-redacted.json` con campi ammessi; `verify_release.ps1` esegue smoke DB e health. I log JSON ruotano in `data_root/logs`, massimo 5MB × 6 file; gli output di processo restano in `.runtime`. Non allegare log grezzi: invia solo doctor-redacted.json dopo averne letto il contenuto. Completa [ACCEPTANCE](ACCEPTANCE.md) prima di dichiarare collaudato il server.
