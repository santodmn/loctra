# Location Share - Render

Pagina di condivisione posizione con consenso esplicito del browser, pronta per Render.

## Deploy

1. Crea un repository GitHub.
2. Carica nella root tutti i file di questa cartella, inclusi `.python-version` e `render.yaml`.
3. Su Render scegli **New + → Blueprint**.
4. Collega il repository.
5. Conferma il servizio definito in `render.yaml`.
6. Apri l'URL HTTPS assegnato da Render.

## Test

- `GET /health` deve rispondere con `{"ok":true}`.
- Apri la home da telefono.
- Premi **Condividi posizione**.
- Il browser deve mostrare la richiesta di autorizzazione.
- Dopo il consenso, nei Logs di Render appariranno `NUOVA POSIZIONE`, il link Google Maps e la precisione stimata.

## Note

- Il servizio usa Python 3.13 per evitare cambiamenti automatici del runtime.
- Gunicorn ascolta esplicitamente su `0.0.0.0:$PORT`, come richiesto/raccomandato per i Web Service Render.
- `locations.jsonl` è solo una copia temporanea: il filesystem standard di Render non va considerato persistente.
- La posizione viene inviata soltanto dopo l'azione dell'utente e il consenso nel popup del browser.
