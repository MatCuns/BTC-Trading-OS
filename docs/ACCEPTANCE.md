# Collaudo R1 — evidenze e gate

**Software R1: PASS** sul commit `0992cd48ee719a72b83a79841df03012ee2b9b26`, [CI 40213022097](https://github.com/MatCuns/BTC-Trading-OS/actions/runs/40213022097): 25 pytest su Linux e Windows, restore isolati, wizard con configurazione esistente in PowerShell 5.1, 2 Vitest e 2 browser desktop/mobile. Nessuna di queste prove è il collaudo del server di Matteo.

I test automatici sono definiti nella [CI](../.github/workflows/ci.yml). Gli esiti definitivi sono nel run collegato alla PR integrata; non confondere test su runner Windows con il server Xeon di Matteo.

| Criterio R1 | Verifica software | Sul server Windows di Matteo |
| --- | --- | --- |
| a. Boot Windows | Parsing PowerShell + processo start/health/stop su runner Windows | NOT TESTED: avviare START_PAPER.bat e completare wizard |
| b. Feed heartbeat/reconnect/stale | Mock ping/pong, timeout, backoff e quote stale | NOT TESTED: stabilità WS e connessione reale |
| c. Ordine -> fill -> fee -> PnL -> DB -> UI | pytest contabilità; PostgreSQL reale; Playwright browser | NOT TESTED: provare target PAPER 0,25x dopo feed valido |
| d. Cap, stop, daily loss, drawdown | Risk checks e gap-stop; rifiuto oltre 5x; budget/margine | NOT TESTED: leggere i parametri locali |
| e. Reverse e timeout | Close durabile prima di open; partial e timeout | NOT TESTED: provare reverse solo in PAPER |
| f. Restart mid-order | Residui cancellati, posizione mantenuta, kill ON | NOT TESTED: stop/start controllato |
| g. Segregazione PAPER/LIVE | API LIVE assente, stub rifiuta, CHECK SQL, privilegi ruolo | NOT TESTED: health live_enabled=false |
| h. Feed/DB interrotti | No nuove aperture, commit ambiguo, replay e riconciliazione | NOT TESTED: prova interruzione controllata in fixture |
| i. Nessuna chiave | Suite e browser funzionano senza chiavi OKX | NOT TESTED: nessuna chiave da inserire |
| j. Desktop/responsive | Playwright 1920x1080 e 390x844 + screenshot | NOT TESTED: leggibilità via Chrome Remote Desktop |
| k. CI | Linux/Windows PostgreSQL + restore + frontend build/browser | Consultare il run finale della PR |

## Sequenza consigliata sul server

1. Avvia wizard e UI; controlla data_directory PostgreSQL, destinazione backup e spazio libero.
2. Leggi `/api/health` o System: database e reconciled true, LIVE false. Attendi quote fresche con sorgente OKX; se rete assente usa fixture esplicita con app ferma.
3. In fixture, sblocca PAPER e invia target 0,25x, stop 0,01. Controlla Orders, Positions, saldo/fee e decision timeline. Le quote size possono produrre fill parziali: attendi o osserva timeout.
4. Invia target 0 per chiudere, quindi prova long -> short. La chiusura deve essere persistita prima della gamba opposta. Non modificare il DB manualmente per simulare fill.
5. Inserisci kill switch. Riavvia con stop/start: deve restare inserito e la strategia OFF. I fill già committati non devono duplicarsi.
6. Esegui backup e restore_check -Full. Conserva il report redatto e verifica il volume corretto. Non cancellare dati operativi.
7. Solo dopo, lascia il feed pubblico PAPER in osservazione e misura CPU/RAM, disco e disconnessioni. Nessuna performance di trading è validata da pochi ordini di prova.

Release installata e collaudo hardware: da registrare con versione, data e risultato locale. Nessun gate LIVE è soddisfatto da questi passi.
