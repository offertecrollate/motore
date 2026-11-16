"""Frase simpatica sul prodotto, da mettere nelle prime righe del post (attira l'occhio).

Si sceglie in base a parole chiave nel nome; a parità di prodotto esce sempre la stessa frase.
Per un'offerta scelta a mano si può forzare con deal.extra["hook"].
"""
import hashlib
import re

HOOKS_IT = [
    # accessori prima dei prodotti: "borsa per notebook" è una borsa, "controller per smartphone" è un controller
    (("custodia", "sleeve", "borsa"), ["Il tuo notebook protetto e sempre a portata di mano 💼",
                                      "Ufficio, università o viaggio: il notebook viaggia comodo 💼"]),
    (("zaino", "trolley", "valigia"), ["Porta tutto con te, con stile e senza pensieri 🎒"]),
    (("controller", "gamepad"), ["Prendi il controllo della partita 🎮",
                                 "Trasforma il telefono in una console: si gioca ovunque 🎮"]),
    (("mouse",), ["Clic rapidi e mira perfetta: il mouse giusto per vincere ogni partita 🖱️",
                  "Il tuo setup da gaming merita un upgrade, e a questo prezzo è un attimo 🎮"]),
    (("cuffie", "headset", "auricolari"), ["Immergiti nel gioco: senti ogni passo prima degli altri 🎧",
                                           "Le cuffie che aspettavi, a un prezzo che non si vede spesso 🎧"]),
    (("tastiera", "keyboard"), ["Bellissima tastiera gaming: ogni tasto una soddisfazione ⌨️",
                                "Scrivere e giocare non è mai stato così bello ⌨️"]),
    (("notebook", "portatile", "laptop", "aspire", "swift", "chromebook"),
     ["Finalmente un portatile da portare ovunque, senza svuotare il portafoglio 💻",
      "Studio, lavoro e serie TV: il notebook che fa tutto 💻"]),
    (("monitor",), ["Più fluido e più veloce: il monitor che cambia il modo di giocare 🖥️",
                    "Uno schermo così sulla scrivania fa tutta la differenza 🖥️"]),
    (("router", "wi-fi", "wifi", "mesh"), ["Addio zone morte: Wi-Fi veloce in ogni stanza della casa 📶",
                                           "Internet a tutta velocità, dal salotto alla camera 📶"]),
    (("tablet", "ipad", "iconia"), ["Il tablet giusto per divano, viaggi e videochiamate 📱"]),
    (("smartphone", "iphone", "galaxy", "telefono"), ["Il telefono nuovo che aspettavi, a un prezzo crollato 📱"]),
    (("sedia",), ["La tua schiena ti ringrazierà: comodità da vero gamer 🪑"]),
    (("proiettore", "projector"), ["Il cinema arriva in salotto: popcorn pronti? 🍿"]),
    (("tv", "televisore", "oled", "qled"), ["Serate film e partite su un grande schermo, a un prezzo piccolo 📺"]),
    (("grill", "piastra", "plancha", "griglia"),
     ["Grigliate perfette anche in casa: carne, verdure e pesce come al ristorante 🔥"]),
    (("teglia", "backblech", "blech"), ["Teglia antiaderente: dolci e arrosti si staccano da soli 🍰"]),
    (("pirofil", "gratin"), ["Lasagne, parmigiane e gratin: la pirofila giusta per ogni ricetta 🧀"]),
    (("friggitrice", "air fryer"), ["Fritto croccante senza olio: la cena è servita in un attimo 🍟"]),
    (("caffè", "caffe", "espresso", "coffee"), ["Il caffè come al bar, ogni mattina a casa tua ☕"]),
    (("aspirapolvere", "robot", "lavapavimenti"), ["La casa pulita senza fatica: ci pensa lui 🧹"]),
    (("orologio", "smartwatch", "watch"), ["Stile e tecnologia al polso, a un prezzo che sorprende ⌚"]),
    (("lavatrice", "asciugatrice", "frigorifero", "lavastoviglie", "forno"),
     ["Un grande elettrodomestico a un prezzo davvero piccolo 🏠"]),
]
DEFAULT_IT = ["Un'occasione da non lasciarsi scappare 👀",
              "Un prezzo così non si vede tutti i giorni ⚡",
              "Corri a vederlo prima che il prezzo torni su ⏳"]


def hook(name: str, key: str = "", lang: str = "it") -> str:
    if lang != "it":
        return ""
    low = name.lower()
    pick = int(hashlib.md5((key or name).encode()).hexdigest(), 16)
    for words, phrases in HOOKS_IT:
        if any((re.search(rf"\b{re.escape(w)}\b", low) if len(w) <= 3 else w in low) for w in words):
            return phrases[pick % len(phrases)]
    return DEFAULT_IT[pick % len(DEFAULT_IT)]
