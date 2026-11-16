# Motore errori di prezzo (Svizzera + Italia)

Un solo motore che ogni giorno:
1. **raccoglie i prezzi** dai feed delle piattaforme di affiliazione (Awin, Tradedoubler) e da Amazon.it / Amazon.de;
2. **salva lo storico** in un file SQLite (`prezzi.db`);
3. **trova i ribassi**: confronta il prezzo di oggi con la mediana degli ultimi 30 giorni
   (da −30% = offerta, da −60% = errore di prezzo; soglie nel config);
4. **pubblica** le offerte di ogni paese sul suo canale:
   - **Svizzera → WhatsApp**: negozi svizzeri + Amazon.it, Amazon.de, Amazon.fr (spediscono in Svizzera)
   - **Italia → Telegram**: offerte italiane
5. **aggiorna il sito**: pagina iniziale con un'immagine in alto (`site/assets/hero.jpg`, da creare)
   e sotto due bandiere grandi 🇮🇹 / 🇨🇭.
   - 🇮🇹 porta alle offerte solo per l'Italia (in italiano)
   - 🇨🇭 porta alle offerte per la Svizzera (italiano, tedesco, francese)
   Ogni parte è divisa in sezioni per categoria di negozio; ogni prodotto ha il link
   e il grafico dell'andamento del prezzo (ultimi 90 giorni, `site.chart_days`).

Ogni paese (`ch`, `it`) ha fonti, regole e canali propri in `countries:`; lingue e
sezioni del sito per ogni paese sono in `site.countries:` dentro `config.yaml`.

## Provarlo subito (senza account)

```bash
pip install -r requirements.txt
python demo.py          # simula 30 giorni di prezzi e un errore di prezzo
python -m pytest tests  # test del rilevatore
```
Il sito di prova si apre da `demo_out/site/index.html`.

## Uso reale

```bash
cp config.example.yaml config.yaml   # metti URL dei feed, tag Amazon, token dei canali
python -m engine.run --country ch --dry-run   # stampa i post senza pubblicare
python -m engine.run --country ch             # pubblica davvero
```

Sul server (es. Oracle Cloud Free Tier), con cron, 3 volte al giorno:
```
0 8,13,19 * * * cd /home/ubuntu/errori-prezzo && python3 -m engine.run --country ch
5 8,13,19 * * * cd /home/ubuntu/errori-prezzo && python3 -m engine.run --country it
```

## Fonti
| Fonte | Cosa serve |
|---|---|
| Awin (MediaMarkt CH e altri .ch) | iscrizione ad Awin, approvazione del negozio, URL del feed prodotti |
| Tradedoubler (Galaxus) | approvazione; chiedere a Galaxus se pagano su galaxus.ch / digitec.ch |
| Amazon.it / Amazon.de / Amazon.fr | iscrizioni separate, ognuna col suo tag; i prezzi per ora da un CSV (`data/amazon_de.csv`, …) |

I feed contengono già i link con il tuo codice affiliato: niente scraping.

## Canali
- **WhatsApp**: l'API ufficiale Meta non pubblica sui canali. Si usa **WAHA** (gratis, installato sul server, non ufficiale).
  Usa un numero dedicato al canale, non il tuo personale.
- **Telegram**: bot ufficiale (BotFather), il bot deve essere amministratore del canale.
- **Facebook** (pronto nel codice, non attivo nel config): pagina + token pagina dalla Graph API di Meta.

## Storico prezzi
Gratis: il motore salva ogni giorno i prezzi; farlo partire **prima** di aprire il sito,
così i grafici hanno già mesi di storico.
Opzionale (a pagamento, spento): `keepa:` nel config importa lo storico Amazon passato
dei prodotti nuovi (`engine/keepa_backfill.py`).

## Ancora da fare
- prezzi Amazon automatici (al momento entrano da CSV)
- Instagram
- canale premium (dopo 1000 iscritti)
- pagina singola per ogni offerta sul sito, per Google
