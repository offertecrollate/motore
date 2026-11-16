"""
Categorie di prodotto (per i filtri del sito), ricavate dal nome e dalla
categoria del negozio con parole chiave in italiano, tedesco, francese e inglese.
"""
CATEGORIES = [
    # id, nomi (it, de, fr), parole chiave
    ("smartphone", {"it": "Smartphone e tablet", "de": "Smartphones und Tablets", "fr": "Smartphones et tablettes"},
     ["smartphone", "iphone", "galaxy s", "galaxy a", "pixel", "handy", "telefon", "téléphone", "tablet", "ipad",
      "galaxy tab", "kindle", "e-reader", "smartwatch", "apple watch"]),
    ("informatica", {"it": "Informatica", "de": "Computer", "fr": "Informatique"},
     ["notebook", "laptop", "macbook", "pc ", "computer", "monitor", "ssd", "hard disk", "festplatte", "stampante",
      "drucker", "imprimante", "router", "mouse", "maus", "tastiera", "tastatur", "clavier", "grafikkarte", "gpu",
      "scheda video", "informatica", "informatique"]),
    ("tv_audio", {"it": "TV e audio", "de": "TV und Audio", "fr": "TV et audio"},
     ["tv", "televisore", "fernseher", "téléviseur", "soundbar", "cuffie", "kopfhörer", "casque", "airpods",
      "earbuds", "headphone", "lautsprecher", "speaker", "altoparlante", "enceinte", "wh-1000", "beamer",
      "proiettore", "audio"]),
    ("elettrodomestici", {"it": "Elettrodomestici e cucina", "de": "Haushalt und Küche", "fr": "Électroménager et cuisine"},
     ["aspirapolvere", "staubsauger", "aspirateur", "dyson", "roomba", "robot aspir", "lavatrice", "waschmaschine",
      "frigo", "kühlschrank", "macchina caffè", "kaffeevollautomat", "kaffeemaschine", "machine à café", "magnifica",
      "nespresso", "friggitrice", "airfryer", "heissluft", "forno", "mixer", "frullatore", "küchenmaschine", "bimby",
      "thermomix", "kenwood", "de'longhi", "delonghi", "elettrodomest", "haushalt", "électroménager"]),
    ("giochi", {"it": "Giochi e videogiochi", "de": "Spielzeug und Gaming", "fr": "Jeux et jeux vidéo"},
     ["lego", "playmobil", "gioco", "giocattol", "spielzeug", "jouet", "playstation", "ps5", "xbox", "nintendo",
      "switch", "videogioc", "gaming", "pokémon", "pokemon"]),
    ("casa", {"it": "Casa, giardino e fai da te", "de": "Haus, Garten und Werkzeug", "fr": "Maison, jardin et bricolage"},
     ["trapano", "bohrmaschine", "perceuse", "avvitatore", "akkuschrauber", "giardino", "garten", "jardin",
      "tagliaerba", "rasenmäher", "tondeuse", "lampada", "lampe", "leuchte", "materasso", "matratze", "mobili",
      "möbel", "meuble", "werkzeug", "utensil", "outil"]),
    ("sport", {"it": "Sport e tempo libero", "de": "Sport und Freizeit", "fr": "Sport et loisirs"},
     ["bici", "fahrrad", "vélo", "scarpe running", "laufschuh", "fitness", "tapis", "laufband", "zaino", "rucksack",
      "sac à dos", "tenda", "zelt", "sport"]),
    ("bellezza", {"it": "Salute e bellezza", "de": "Gesundheit und Beauty", "fr": "Santé et beauté"},
     ["rasoio", "rasierer", "rasoir", "spazzolino", "zahnbürste", "brosse à dents", "phon", "föhn", "sèche-cheveux",
      "piastra", "profumo", "parfum", "crema", "creme", "beauty", "bellezza", "beauté"]),
    ("moda", {"it": "Moda", "de": "Mode", "fr": "Mode"},
     ["scarpe", "schuhe", "chaussures", "giacca", "jacke", "veste", "jeans", "maglia", "shirt", "borsa", "tasche",
      "sac ", "orologio", "uhr", "montre", "moda", "mode"]),
]
OTHER = ("altro", {"it": "Altro", "de": "Weiteres", "fr": "Autres"})
# negozi per adulti: categoria a parte, mai in home, mai su Google, mai su Facebook (decisione di Giuseppe)
ADULT = ("adulti", {"it": "Adulti 18+", "de": "Erwachsene 18+", "fr": "Adultes 18+"})


def categorize(name: str, raw_category: str = "") -> str:
    text = f" {name} {raw_category or ''} ".lower()
    for cid, _, words in CATEGORIES:
        if any(w in text for w in words):
            return cid
    return OTHER[0]


def label(cid: str, lang: str) -> str:
    if cid == ADULT[0]:
        return ADULT[1].get(lang, ADULT[1]["it"])
    for c, names, _ in CATEGORIES:
        if c == cid:
            return names.get(lang, names["it"])
    return OTHER[1].get(lang, OTHER[1]["it"])


ORDER = [c[0] for c in CATEGORIES] + [OTHER[0]]
