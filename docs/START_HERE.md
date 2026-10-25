# Parti da qui, Matteo

**Situazione attuale:** documentazione e presentazione del progetto sono disponibili su `main`. La PR #1 è già integrata. Il bot, la UI applicativa e gli script di installazione devono ancora essere costruiti.

## La tua prossima azione: un messaggio ad Astra

Seleziona il repository `MatCuns/BTC-Trading-OS` nell'ambiente di sviluppo e incolla:

```text
Lavora su https://github.com/MatCuns/BTC-Trading-OS.
Leggi AGENTS.md e docs/STATUS.md, poi esegui integralmente
docs/prompts/01_R1_PAPER.md.
Implementa, verifica e integra le modifiche in main autonomamente
secondo il mandato del prompt. Non lasciarmi PR da approvare.
Consegna una release PAPER e una procedura guidata per il server.
```

Non occorre allegare il PDF o copiare separatamente un contratto comune. I tre file dei prompt sono autosufficienti. Se Astra non riesce a leggerli, incolla il mega prompt integrale dal PDF. Non basta selezionare il nome del modello in una chat priva di ambiente di sviluppo: occorre accesso reale al repository e strumenti di modifica/esecuzione.

## Dopo la consegna R1

1. Astra gestisce codice, test, commit, PR e merge. Non devi premere Merge.
2. Se Astra opera soltanto in cloud, esegui sul server la procedura guidata che avrà realmente creato. `START_PAPER.bat` e `scripts/first_run.ps1` sono requisiti R1: **oggi non esistono**. Non provare a lanciarlo prima della consegna.
3. Scegli nel wizard i volumi reali; inserisci eventuali password solo localmente. Non devi modificare Python, SQL o React a mano.
4. Verifica che UI e PAPER funzionino sul server. Invia ad Astra il report redatto se qualcosa fallisce: è Astra a correggere.
5. Dopo il gate R1 usa il messaggio seguente con `02_R2_INTELLIGENCE.md`; dopo R2 usa `03_R3_OPERATIONS.md`.

```text
Leggi AGENTS.md e docs/STATUS.md nel repository MatCuns/BTC-Trading-OS.
Esegui integralmente docs/prompts/02_R2_INTELLIGENCE.md,
applica e integra autonomamente le modifiche dopo i controlli.
```

## Cosa resta inevitabilmente sul server

Scelta dei dischi senza cancellazioni automatiche, consenso Windows quando richiesto, credenziali locali e collaudi hardware. Un agente cloud non può premere pulsanti sul tuo PC senza un accesso separato. L'attivazione LIVE con denaro reale resta una decisione distinta, mai implicita nel merge.

## Per sapere sempre dove siamo

[docs/STATUS.md](STATUS.md) è il punto di ingresso. Ogni sessione deve aggiornarlo con implementato, verificato, non testato, blocchi e prossima azione. Il merge non prova che quella release sia già sul server.
