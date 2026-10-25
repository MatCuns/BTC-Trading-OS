# Compatibilità OKX EEA — R1

Verifica: **25 ottobre 2026**. Fonti ufficiali: [API EEA](https://my.okx.com/docs-v5/en/), [X-Perps Europe](https://www.okx.com/en-eu/x-perps).

## Evidenza pubblica e limiti

Richieste REST pubbliche dalla sessione cloud hanno risposto HTTP 200/code 0 per `/api/v5/public/time` e `/api/v5/public/instruments?instType=FUTURES`. Lo strumento BTC visibile era:

| Campo | Risposta osservata |
| --- | --- |
| instId | BTC-USD_UM_XPERP-310404 |
| instFamily | BTC-USD_UM_XPERP |
| instType / ruleType | FUTURES / xperp |
| state / ctType | live / linear |
| ctVal × ctMult | 0.0001 × 1 BTC per contratto |
| settleCcy | USD |
| tickSz / lotSz / minSz | 0.1 / 1 / 1 |
| expTime | 1933056000000 ms (4 aprile 2031, 08:00 UTC) |
| minNotional | Non presente: ipotesi PAPER configurata pari a 5 unità di settlement |

L'ID è **evidenza della discovery, non un default hardcoded**. Ogni avvio interroga l'API. Zero candidati: PAPER fermo con motivo esplicito; più candidati: selezione locale BTC_INSTRUMENT_ID. Nessuna sostituzione con BTC-USDT-SWAP. Fixture offline è una scelta esplicita con etichetta visibile.

Un secondo probe REST ha avuto timeout nella rete cloud: non è un test di affidabilità di OKX né del server Windows. Streaming pubblico continuo, latency, funding e stabilità della connessione sul server sono da collaudare. Test automatici verificano parsing, ping/pong, timeout, reconnect e blocco stale tramite mock deterministici.

**Disponibilità pubblica non significa abilitazione del conto.** Nessuna autenticazione, verifica di adeguatezza, ordine reale o modifica di account effettuata. Leva restituita dal metadata non sovrascrive i limiti applicativi.

## Endpoint e limiti

| Operazione | Endpoint / parametri | Rate limit documentato / uso R1 |
| --- | --- | --- |
| REST produzione e demo EEA | https://eea.okx.com | Nessun host globale sostitutivo |
| Discovery | GET /api/v5/public/instruments?instType=FUTURES | 20 richieste / 2s, IP + instType; polling solo a connessione |
| Clock | GET /api/v5/public/time | 10 / 2s per IP; differenza >2s blocca feed |
| Primo ticker | GET /api/v5/market/ticker?instId=... | 20 / 2s per IP; una richiesta a connessione |
| Streaming pubblico | wss://wseea.okx.com/ws/v5/public; tickers + trades | 3 connessioni/s per IP; subscribe/unsubscribe/login 480/ora per connessione; due canali per sessione |
| Funding opzionale | GET /api/v5/public/funding-rate-history?instId=... | 10 / 2s, IP + instId; R1 una richiesta/minuto |
| WS demo | wss://wseeapap.okx.com/ws/v5/public | Endpoint documentato; runtime R1 non selezionabile DEMO |
| Demo utility | GET account/instruments, account/balance, trade/order; POST trade/order | Solo su EEA + x-simulated-trading: 1; richieste di test mock, nessun ordine demo inviato |

REST seriale con pausa minima 250ms e timeout 10s; reconnect esponenziale con jitter e massimo 60s. Nessuna apertura di nuove posizioni su feed stale >10s. Il client invia il testo `ping` dopo 20s senza messaggi, attende fino a 5s per risposta e riconnette in caso di errore.

## DEMO / LIVE

OkxDemoAdapter firma richieste con SecretStr, ha allowlist dei percorsi e header demo obbligatorio. La utility place richiede environment OKX_DEMO e attestazione esplicita della verifica dello strumento sull'account; non è connessa alla UI né al ledger PAPER. L'attestazione non è un controllo live del conto: prima di estenderne l'uso va implementata la verifica autenticata end-to-end. Risposte di accettazione demo non sono prova di fill o benchmark di rendimento.

Margine `isolated`, reduceOnly e market order sono parametri dell'utility, verificati tramite mock. Supporto effettivo di stop, riduzione, modalità account e disponibilità del prodotto in demo **NOT TESTED**. Nessun fallback in LIVE. OkxLiveAdapter rifiuta sempre. Le fee conto non sono lette; default PAPER maker 2 bps, taker 5 bps, slippage 2 bps, dichiarati come ipotesi.
