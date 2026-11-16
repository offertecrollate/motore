import json, os, sys
from datetime import datetime
sys.path.insert(0, '.')
from engine import categories as cats
G="https://static01.galaxus.com/productimages/"
E="https://www.euronics.it/dw/image/v2/BFPN_PRD/on/demandware.static/-/Sites-catalog_euronics_master/default/"
EU="https://www.euronics.it/"
CH=[
("Tineco S9 Artist Steam Pro (aspira + lava)",469,699,"Galaxus","https://www.galaxus.ch/it/s2/product/tineco-s9-artist-steam-pro-saugen-wischen-nassreiniger-66678544",G+"6/5/2/8/9/8/6/0/4/8/7/7/9/8/0/6/4/3/01a1308d-1b50-7033-bb71-bcf80d89fafb_720.jpeg"),
("Ooni Koda 16 forno per pizza a gas",449,599,"Galaxus","https://www.galaxus.ch/it/s4/product/ooni-koda-16-forno-per-pizza-a-gas-forno-per-pizza-13293128",G+"1/2/4/1/7/9/2/2/2/4/5/9/5/9/3/6/3/3/6/01a13053-da2b-7239-876a-54198cf1ac75_720.jpeg"),
("Bowflex Max Trainer M6 ellittica",999,1399,"Galaxus","https://www.galaxus.ch/it/s3/product/bowflex-max-trainer-m6-ellittica-11949458",G+"3/4/3/7/8/0/5/5/1/5/5/7/0/4/0/4/8/4/5/01a0ce4d-32fc-7956-91a1-e4f9be5efca4_720.jpeg"),
("Purelei calendario dell'Avvento oro rosa",135,165,"Galaxus","https://www.galaxus.ch/it/s14/product/purelei-adventskalender-rosegoldversion-adventskalender-76112157",G+"7/4/5/2/1/5/3/3/1/0/9/1/4/4/3/4/1/8/8/01a11fbf-5943-77f7-a27d-9c6df451a537_720.jpeg"),
("The Watch Book Rolex (libro, copertina rigida)",59,82.90,"Galaxus","https://www.galaxus.ch/it/s18/product/the-watch-book-rolex-tedesco-copertina-rigida-gisbert-l-brunner-libri-professionali-59049086",G+"4/4/4/5/7/9/0/0/6/2/0/9/0/1/9/2/4/4/3/01a132e4-93c0-7ba3-b9f2-d046b215e032_720.jpeg"),
("Jack & Jones Blusimon t-shirt (M)",29,44.90,"Galaxus","https://www.galaxus.ch/fr/s8/product/jack-jones-blusimon-m-t-shirt-71361017",G+"9/1/3/0/0/1/7/3/4/9/9/4/8/3/6/8/9/3/9/019f1d6b-93db-7c50-adbc-c65dce49a0fa_720.jpeg"),
("Sony Bravia 5 K-55XR5 TV 55\" Mini-LED 4K",699,899,"Digitec","https://www.digitec.ch/fr/s1/product/sony-k-55xr5-55-bravia-5-mini-led-4k-2025-tv-57260738",G+"5/7/8/2/7/3/8/3/3/7/5/2/9/6/9/1/5/4/4/019914df-2658-7777-9911-18b06e90f64e_720.jpeg"),
("Xiaomi Poco F8 Ultra 512 GB smartphone 5G",689,815,"Digitec","https://www.digitec.ch/fr/s1/product/xiaomi-poco-f8-ultra-512-go-bleu-jean-690-double-sim-5g-telephone-portable-65395694",G+"7/9/9/1/1/8/7/2/6/0/3/9/7/2/0/7/1/0/8/01a02974-2a0b-7f04-8571-8fb310cfe298_720.jpeg"),
("Samsung Galaxy Tab A11+ tablet 11\" 256 GB",199,259,"Digitec","https://www.digitec.ch/de/s1/product/samsung-galaxy-tab-a11-nur-wlan-11-256-gb-gray-tablet-62588272",G+"5/6/5/5/9/5/7/7/0/9/5/4/8/8/1/1/0/2/7/019aa10c-9a69-7310-bbce-a663b789ed2f_720.jpeg"),
("Samsung Galaxy Watch 8 Classic 46 mm smartwatch",199,279,"Digitec","https://www.digitec.ch/de/s1/product/samsung-galaxy-watch-8-classic-46-mm-edelstahl-schwarz-silber-ohne-sim-smartwatch-59757709",G+"9/0/3/5/7/9/8/7/4/7/1/6/1/7/1/5/6/6/4/0197eec7-ed0c-70e8-8a80-28ca61e5684f_720.jpeg"),
("Acer Predator Aethon 303 tastiera gaming",39,67,"Digitec","https://www.digitec.ch/de/s1/product/acer-predator-aethon-303-ch-kabelgebunden-tastatur-58832017",G+"4/8/4/2/2/3/5/3/0/7/0/9/8/4/1/6/4/6/1/01a07c50-3a99-73a3-9f80-33f2fb2cbb43_720.jpeg"),
("Anker Prime powerbank 27650 mAh 250 W",99,129,"Digitec","https://www.digitec.ch/de/s1/product/anker-prime-27650-mah-250-w-9954-wh-powerbank-40773021",G+"4/8/3/7/5/9/8/8/2/3/9/9/0/3/6/1/7/3/4/d6111992-19ea-4948-872a-1fd969756faa_cropped.jpg_720.jpeg"),
("Arlo Ultra 3 kit 3 telecamere 4K + pannello solare",379,450,"Digitec","https://www.digitec.ch/de/s1/product/arlo-ultra-3-ueberwachungskamera-3er-set-solarmodul-3840-x-2160-pixels-netzwerkkamera-64348843",G+"5/4/8/2/7/5/4/4/7/1/6/3/2/2/4/6/6/1/8/01a0d417-f03c-7b58-becf-e0d26ba1292d_720.jpeg"),
("Arlo Ultra 3 telecamera 4K + SmartHub",139,178,"Digitec","https://www.digitec.ch/de/s1/product/arlo-ultra-3-ueberwachungskamera-smarthub-3840-x-2160-pixels-netzwerkkamera-64672733",G+"8/4/0/6/7/8/5/1/4/2/2/9/8/0/9/9/5/3/8/01a0d430-fb5d-7ab3-b9ed-16b7256fa44e_720.jpeg"),
("NordVPN Plus 24 mesi, 10 dispositivi",49.90,139.90,"Digitec","https://www.digitec.ch/en/s1/product/nordvpn-plus-1-user-10-devicesusers-24-months-software-68560515",G+"2/5/3/2/6/5/0/6/7/9/6/2/9/9/4/3/3/7/6/019d0950-8596-7060-8fe7-4bd4945cf08a_720.jpeg"),
("Bici indoor HAMMER Speed Race SR",599,1390,"DayDeal","https://daydeal.ch/de/deal/indoor-bike-hammer-speed-race-sr-9477","https://images.daydeal.ch/files/572x520/DD4-0-Hauptbild-bike-6adb5ec93b121.png"),
("Robot lavavetri Dreame C1 Station S con pad e detergente",299,489,"DayDeal","https://daydeal.ch/de/deal/fensterputzroboter-set-dreame-c1-station-s-mit-pads-und-reinigungsmittel-9422","https://images.daydeal.ch/files/572x520/DD4-0-Hauptbild-sauger-6ac4fc5abdcef.jpg"),
("Vino bianco Compleo Cuvée Blanc 2025, 6 x 0,75 l",87.95,125.70,"DayDeal","https://daydeal.ch/de/deal/weisswein-6x-0-75-l-compleo-cuvee-blanc-2025-9511","https://images.daydeal.ch/files/572x520/DD4-Hauptbild-6ae839dcb16eb.jpg"),
("Detergente WC in schiuma Bellaria 3 x 700 ml",29.90,41.70,"DayDeal","https://daydeal.ch/de/deal/wc-reiniger-schaum-bellaria-3-700-ml-9255","https://images.daydeal.ch/files/572x520/DD3-Hauptbild-6a902c5579315.png"),
("Kit cura auto Motorex Franjo von Allmen Winter Kit",44,59.90,"DayDeal","https://daydeal.ch/de/deal/autopflege-set-motorex-franjo-von-allmen-winter-kit-9426","https://images.daydeal.ch/files/572x520/DD4-Hauptbild-6ad761479ca86.jpg"),
("Musicbox per bambini wobie Box blu",109,139,"DayDeal","https://daydeal.ch/de/deal/musikbox-fur-kinder-wobie-box-blau-9445","https://images.daydeal.ch/files/572x520/DD4-Hauptbild-6ad0882434e4c.jpg"),
("PC gaming Erazer Tank X15 (MD340129)",1999,2499,"DayDeal","https://daydeal.ch/de/deal/gaming-pc-erazer-tank-x15-md340129-9424","https://images.daydeal.ch/files/560x509/DD4-6acde2abeaa0e.jpg"),
]
def e(path, img): return EU+path, E+img+"?sw=600&q=90&strip=false"
IT=[
("Apple iPhone 14 Pro Max 512GB Nero Siderale",499,1699,*e("telefonia/smartphone-e-cellulari/iphone/apple---iphone-14-pro-max-512gb-nero-siderale/222008819.html","dw1dabc5e9/hi-res/222008819.jpg")),
("Apple MacBook Pro 16\" M2 Pro 512GB Argento",1099.90,3099,*e("informatica/mac/macbook/apple---macbook-pro-16-m2-pro-core%3A-12-cpu-19-gpu-512gb-argento/232000440.html","dwcc7c9bad/hi-res/232000440.jpg")),
("Apple Mac mini i5 512GB (2020) Space Grey",499.90,1359,*e("informatica/pc-desktop/desktop/apple---mac-mini-i5-512gb-mxng2t-a-%282020%29-space-grey/202005165.html","dw7cedab09/hi-res/202005165.jpg")),
("HUNE caricatore Fast Charge NOMADE-20CL",1.99,9.99,*e("telefonia/accessori/caricabatterie/hune---caricatore-fast-charge-nomade-20cl-verde-foresta/242013588.html","dwd83eacdd/hi-res/242013588.jpg")),
("HUNE cavo di ricarica 3 in 1 HIEDRA",1.99,7.99,*e("telefonia/accessori/cavi---adattatori/hune---cavo-3-in-1-per-ricarica-hiedra-3in1-verde-foresta/242013586.html","dw512ae92a/hi-res/242013586.jpg")),
("Hoover aspirapolvere a traino Breeze BR31PET",49.99,109.99,*e("elettrodomestici/pulizia--stiro-e-cucito/aspirapolvere-a-traino/hoover---aspirapolvere-a-traino-breeze-br31pet-nero/162016409.html","dw89e2df6f/hi-res/162016409.jpg")),
("Samsung Clear View Cover Galaxy Note 10",29.90,62.99,*e("telefonia/accessori/custodie/samsung---clear-view-cover-black-galaxy-note-10-nero/192010521.html","dw52b02574/hi-res/192010521.jpg")),
("Microsoft Ocean Plastic Mouse",9.99,19.90,*e("informatica/accessori-pc/mouse/microsoft---ocean-plastic-mouse/212012594.html","dw85596969/hi-res/212012594.jpg")),
("Lenovo notebook IdeaPad 3 15ADA05",399.90,697,*e("informatica/computer-portatili/notebook/lenovo---notebook-ip-3-15ada05-81w1018hix-platinum-grey/202012515.html","dw4e7bd22f/hi-res/202012515.jpg")),
("Candy lavatrice CSO 496TWM6/1-S 9 kg Classe A",279.99,479.99,*e("elettrodomestici/grandi-elettrodomestici/lavatrici/lavatrici-standard/candy---lavatrice-cso-496twm6-1-s-9-kg-classe-a-bianco/242001444.html","dw410116f5/hi-res/242001444.jpg")),
("Candy lavatrice slim RP4 476BWMBC/1-S 7 kg Classe A",299.99,499.99,*e("elettrodomestici/grandi-elettrodomestici/lavatrici-slim/candy---lavatrice-rp4-476bwmbc-1-s-7-kg-classe-a-bianco/252003440.html","dwe730e886/hi-res/252003440.jpg")),
("Apple Watch Series 7 GPS+Cellular 41mm acciaio",499.90,808,*e("telefonia/wearable/apple-watch/apple---watch-series-7-gpscellular-41mm-acciaio-maglia-milanese-grafite/212012809.html","dw4fac8beb/hi-res/212012809.jpg")),
("Namco Sand Land PS5",9.99,15.90,*e("gaming/playstation-5/giochi-sony-ps5/namco---sand-land-ps5/242000433.html","dwd66c4d3a/hi-res/242000433.jpg")),
("Dyson scopa elettrica V15 Detect Submarine",599,949,*e("elettrodomestici/pulizia--stiro-e-cucito/scope-elettriche/dyson---scopa-elettrica-v15-detect-submarine-yellow-nickel/262006541.html","dw1b39a6e4/hi-res/262006541.jpg")),
("Acer notebook Aspire 15.6\" A315-24P",399.90,610,*e("informatica/computer-portatili/notebook/acer---notebook-aspire-15.6-pollici-a315-24p-r2km-silver/222011974.html","dw62a8f593/hi-res/222011974.jpg")),
("Candy lavatrice CSO6106TWMB6/1-S 10 kg Classe A",329.99,499.99,*e("elettrodomestici/grandi-elettrodomestici/lavatrici/lavatrici-standard/candy---lavatrice-cso6106twmb6-1-s-10-kg-classe-a-bianco/242001377.html","dw3d4bbec0/hi-res/242001377.jpg")),
("Apple Watch Series 9 GPS 45mm Blu Tempesta",349.90,469,*e("telefonia/wearable/apple-watch/apple---watch-series-9-gps-cassa-45mm---s-m-blu-tempesta/232011464.html","dw6d4a2e94/hi-res/232011464.jpg")),
("Cellularline fascia da braccio per smartphone",9.99,13.49,*e("tv-e-audio/cuffie-e-auricolari/cuffie/cellularline---fascia-da-braccio-con-meccanismo-rotante-nero/182005751.html","dw6cccde58/hi-res/182005751.jpg")),
("EA FIFA 22 PS5",14.99,19.90,*e("gaming/playstation-5/giochi-sony-ps5/electronic-arts---fifa-22-ps5/212009226.html","dw96cf076c/hi-res/212009226.jpg")),
("Strong range extender Wi-Fi 6 AX1800",54.99,69.90,*e("informatica/reti-e-connettivita/adattatori-networking/strong---range-extender-repeaterax1800/242010709.html","dw9075b97e/hi-res/242010709.jpg")),
("Strong kit Powerline Wi-Fi 600 duo mini",39.99,49.90,*e("informatica/accessori-pc/varie-informatica/strong---powerline-kit-2-pezzi-compatti-powerlwf600duomini-bianco/232013537.html","dw2fd441aa/hi-res/232013537.jpg")),
("Apple iPhone Air 1TB Celeste",1199,1499,*e("telefonia/smartphone-e-cellulari/iphone/apple---iphone-air-1tb-celeste/252011564.html","dwecf92f1a/hi-res/252011564.jpg")),
("Candy lavatrice BP 413BL8-S 13 kg Classe A",399.99,499,*e("elettrodomestici/grandi-elettrodomestici/lavatrici/lavatrici-standard/candy---lavatrice-bp-413bl8-s-13kg-classe-a-bianco/252015620.html","dw669cf2a8/hi-res/252015620.jpg")),
("Apple MacBook Air 13\" M3 256GB Argento",1099.90,1349,*e("informatica/mac/macbook/apple---macbook-air-13---m3-core-8-cpu-core-8-gpu-256gb-argento/242003106.html","dw7500fa04/hi-res/242003106.jpg")),
("Wacom tavoletta grafica Intuos Pro Medium",369.90,444,*e("informatica/accessori-pc/tavolette-grafiche/wacom---intuos-pro-medium-nero/172008403.html","dw4fb2ad2f/hi-res/172008403.jpg")),
("MSI notebook gaming Cyborg 15 B13WEKG",999.99,1199,*e("informatica/computer-portatili/notebook-gaming/msi---notebook-cyborg-15-b13wekg-1093it-translucent-black/262002146.html","dwb1ef6766/hi-res/262002146.jpg")),
("Apple iPad Air 10.9\" Wi-Fi + Cellular 64GB",699.90,829,*e("informatica/tablet-ed-ebook-reader/ipad/apple---ipad-air-10.9---wi-fi-cellular-64gb-grigio-siderale/222002827.html","dw3fb3055c/hi-res/222002827.jpg")),
("Whirlpool asciugatrice 9 kg Classe A",599.99,699.99,*e("elettrodomestici/grandi-elettrodomestici/asciugatrici/whirlpool---asciugatrice-c-wd-96m-wbs-it-9kg-classe-a-bianco/252012543.html","dw29d1e5b9/hi-res/252012543.jpg")),
("Dyson piastra asciugacapelli Airstrait",349,399,*e("elettrodomestici/bellezza--salute--benessere/piastre/dyson---piastra-asciugacapelli-airstrait-rosa/252010178.html","dwd632a626/hi-res/252010178.jpg")),
("Hisense frigorifero 4 porte 485 l inox",699.99,799.99,*e("elettrodomestici/grandi-elettrodomestici/frigoriferi/hisense---frigorifero-4-porte-rf632n4wie1-classee-485lt-inox/232008506.html","dw9b96bfb8/hi-res/232008506.jpg")),
("Lenovo IdeaPad Slim 3 15,3\" Intel Core 7 16GB",699.99,799,*e("informatica/computer-portatili/notebook/lenovo---notebook-ideapad-slim-3-nb-15-3---ips3-15iwc11-luna-grey/262009047.html","dw01e66662/hi-res/262009047.jpg")),
("Apple AirPods 5 con custodia di ricarica wireless",149,169,*e("tv-e-audio/cuffie-e-auricolari/apple-airpods/apple---airpods-5-con-custodia-di-ricarica-wireless-bianco/262010748.html","dw4ed84d68/hi-res/262010748.jpg")),
]
now=datetime.now().isoformat(timespec="minutes")
def build(rows, cur, shop_default=None):
    out=[]
    for i,r in enumerate(rows):
        if shop_default: name,pr,ref,url,img=r; shop=shop_default
        else: name,pr,ref,shop,url,img=r
        pct=round((1-pr/ref)*100,1)
        out.append({"key":f"manual:{shop.lower()}:{i}:{abs(hash(url))%10**8}","source":"manuale",
            "category":cats.categorize(name,""),"name":name,"price":pr,"ref":ref,"pct":pct,"level":"offerta",
            "shop":shop,"url":url,"image":img,"currency":cur,"at":now,"history":[]})
    return sorted(out,key=lambda x:-x["pct"])
os.makedirs("site/ch",exist_ok=True); os.makedirs("site/it",exist_ok=True)
json.dump(build(CH,"CHF"),open("site/ch/deals.json","w"),ensure_ascii=False,indent=1)
json.dump(build(IT,"EUR","Euronics"),open("site/it/deals.json","w"),ensure_ascii=False,indent=1)
print(len(CH),len(IT))
