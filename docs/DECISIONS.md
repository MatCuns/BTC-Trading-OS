# Decisioni R1

1. INTERNAL_PAPER è l'unico ambiente applicativo selezionabile. Demo è una utility separata testata con mock; LIVE è uno stub non abilitabile.
2. Un processo FastAPI + PostgreSQL; frontend compilato senza server Node persistente. Nessun Ollama prima di R2.
3. Decimal e contratti lineari BTC-valued; contratti inversi o metadata incerti sono bloccati. Nessuna scelta silenziosa di un altro prodotto.
4. Persistenza prima di pubblicare mutazioni: rollback memoria e blocco su commit ambiguo, riconciliazione esplicita al riavvio. PAPER senza exchange non ha fill esterni da riconciliare.
5. Il ruolo runtime non possiede schemi, non può DELETE né accedere a LIVE. La password amministrativa non è salvata; la password app è solo nella configurazione locale con ACL utente/SYSTEM.
6. Installer di prerequisiti attraverso fonti ufficiali e passi riprendibili, senza installazioni opache o accettazione silenziosa di contratti. Un PostgreSQL esistente non viene spostato, sostituito o duplicato.
7. data_root applicativo e data_directory del cluster PostgreSQL sono distinti ed espliciti. Un eventuale trasferimento di un cluster esistente richiede un intervento amministrativo separato dopo backup.
8. Kill switch reinserito e strategia OFF a ogni riavvio. Il task Windows R1 è al logon utente, con privilegi limitati; recovery veramente unattended e boot senza sessione restano R3.
9. Solo export/backup automatici, nessuna retention distruttiva implicita. Lo storico SQL rimane disponibile oltre le finestre limitate della UI.
10. Release software dopo CI verificata; collaudo sullo Xeon Windows, durata del feed e forward performance restano gate distinti e non vengono dichiarati superati dal merge.
