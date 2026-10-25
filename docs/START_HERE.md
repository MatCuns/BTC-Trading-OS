# Matteo: inizia da qui

R1 ora contiene l'app PAPER, la dashboard e la procedura Windows. Non devi approvare PR, scrivere codice o fornire chiavi OKX.

**Sul server Windows: scarica ed estrai [lo ZIP della release PAPER](https://github.com/MatCuns/BTC-Trading-OS/releases/tag/v0.1.0-paper), poi fai doppio clic su `START_PAPER.bat`.**

Il wizard rileva Python/PostgreSQL e, se mancano, ti indica il link ufficiale e il singolo passo da completare. Riapri lo stesso BAT dopo l'installazione. Scegli localmente le cartelle dati/backup e inserisci la password PostgreSQL nascosta. Nessuna password va inviata qui.

Con lo ZIP pronto non serve Node.js; è necessario solo per compilare un checkout del codice sorgente. Non servono Docker, WSL, Ollama o un nuovo PC.

La UI si apre su http://127.0.0.1:8765 con **PAPER**, **LIVE DISABLED**, kill switch inserito e strategia OFF. Puoi vedere il mercato prima di abilitare le simulazioni. Se scegli fixture, i dati sono sintetici e indicati come tali.

I dettagli su prerequisiti, cartelle, errori, avvio/stop, update e backup sono in [OPERATIONS](OPERATIONS.md). Il collaudo del tuo server è ancora da eseguire: segui [ACCEPTANCE](ACCEPTANCE.md). Il merge del codice non installa l'app sul tuo PC.

Per lo sviluppo successivo, un agente deve leggere [STATUS](STATUS.md) e solo dopo valutare il [prompt R2](prompts/02_R2_INTELLIGENCE.md). Non rieseguire R1 da zero e non passare a LIVE.
