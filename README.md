# BTC-Trading-OS

Piattaforma BTC quantitativa su server Windows. Progetto in fase iniziale: applicazione, UI e script devono ancora essere implementati.

## Da dove riprendere
Leggere prima [docs/STATUS.md](docs/STATUS.md): stato verificato, test, blocchi e prossima azione.
Gli agenti devono leggere anche [AGENTS.md](AGENTS.md).

- [Architettura prevista](docs/ARCHITECTURE.md)
- [Aggiungere, modificare o rimuovere funzioni](docs/DEVELOPMENT.md)
- [Operazioni e responsabilità sul server](docs/OPERATIONS.md)
- [Cronologia modifiche](docs/CHANGELOG.md)

## Sequenza
1. Matteo prepara server, dipendenze, percorsi e accessi.
2. Astra realizza R1: feed OKX, PAPER, PostgreSQL, rischio e UI.
3. Dopo collaudo Windows: R2 intelligence/Ollama e analytics.
4. R3 affidabilità e adapter LIVE verificato, lasciato disabilitato.

GitHub conserva il codice, non database o credenziali. Il merge non aggiorna automaticamente il server.
Il bot in PAPER e i risultati simulati non dimostrano redditività futura.

Licenza: [MIT](LICENSE).
