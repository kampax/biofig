"""Selección curada de iconos de bibliotecas libres para BioFig.

- Fluent Emoji (Microsoft, licencia MIT): https://github.com/microsoft/fluentui-emoji  (estilo plano a color)
- Health Icons (Resolve to Save Lives, CC0): https://healthicons.org  (monocromos; se tiñen con color plano)

Cada entrada: "Nombre en Fluent|nombre en español". Se agrupan como las categorías de BioRender.
"""

FLUENT = {
    ("Laboratorio y objetos", ("laboratorio",)): """
Microscope|Microscopio; Test tube|Tubo de ensayo; Petri dish|Placa de Petri; Alembic|Alambique; Dna|ADN;
Microbe|Microbio; Syringe|Jeringa; Pill|Pastilla; Drop of blood|Gota de sangre; Adhesive bandage|Curita;
Stethoscope|Estetoscopio; X-ray|Radiografía; Thermometer|Termómetro; Balance scale|Balanza; Magnet|Imán;
Magnifying glass tilted left|Lupa; Telescope|Telescopio; Abacus|Ábaco; Straight ruler|Regla; Triangular ruler|Escuadra;
Scissors|Tijeras; Stopwatch|Cronómetro; Timer clock|Temporizador; Hourglass not done|Reloj de arena;
Alarm clock|Despertador; Clipboard|Portapapeles; Spiral notepad|Libreta; Notebook|Cuaderno; Memo|Nota;
Pencil|Lápiz; Pen|Bolígrafo; Card file box|Fichero; File folder|Carpeta; Books|Libros; Bookmark tabs|Marcadores;
Calendar|Calendario; Pushpin|Chinche; Round pushpin|Alfiler de mapa; Paperclip|Clip; Link|Eslabón;
Lab coat|Guardapolvo; Goggles|Gafas de seguridad; Gloves|Guantes; Safety vest|Chaleco de seguridad;
Fire extinguisher|Matafuegos; Toolbox|Caja de herramientas; Hammer|Martillo; Wrench|Llave inglesa;
Screwdriver|Destornillador; Hammer and wrench|Herramientas; Gear|Engranaje; Nut and bolt|Tuerca y tornillo;
Clamp|Prensa; Ladder|Escalera; Bucket|Balde; Broom|Escoba; Basket|Canasto; Package|Paquete; Jar|Frasco;
Battery|Batería; Electric plug|Enchufe; Light bulb|Lamparita; Flashlight|Linterna; Candle|Vela;
Laptop|Notebook (computadora); Desktop computer|Computadora; Keyboard|Teclado; Computer mouse|Mouse;
Printer|Impresora; Mobile phone|Celular; Camera|Cámara de fotos; Video camera|Videocámara; Film projector|Proyector;
Satellite antenna|Antena parabólica; Radio|Radio; Locked|Candado; Key|Llave; Bell|Campana;
Brain|Cerebro; Anatomical heart|Corazón anatómico; Lungs|Pulmones; Bone|Hueso; Tooth|Diente; Eye|Ojo;
Ear|Oreja; Biohazard|Riesgo biológico; Radioactive|Radiactivo; Bubbles|Burbujas; Ice|Hielo; Crutch|Muleta;
Bread|Pan; Cheese wedge|Queso; Egg|Huevo; Glass of milk|Vaso de leche; Honey pot|Miel; Canned food|Lata;
Cooked rice|Arroz cocido; Cut of meat|Carne; Butter|Manteca; Salt|Sal; Baby bottle|Mamadera""",
    ("Agricultura", ("agricultura", "ecologia")): """
Tractor|Tractor; Farmer|Productor rural; Seedling|Plántula; Sheaf of rice|Espiga de arroz; Ear of corn|Choclo / maíz;
Herb|Hierba; Four leaf clover|Trébol de cuatro hojas; Shamrock|Trébol; Sunflower|Girasol; Tulip|Tulipán;
Blossom|Flor; Hibiscus|Hibisco; Rose|Rosa; Cherry blossom|Flor de cerezo; Deciduous tree|Árbol caducifolio;
Evergreen tree|Árbol perenne; Palm tree|Palmera; Cactus|Cactus; Potted plant|Planta en maceta;
Brown mushroom|Hongo marrón; Mushroom|Hongo; Fallen leaf|Hoja caída; Leaf fluttering in wind|Hojas al viento;
Maple leaf|Hoja de arce; Cow|Vaca; Ox|Buey; Water buffalo|Búfalo; Pig|Cerdo; Boar|Jabalí; Ewe|Oveja; Ram|Carnero;
Goat|Cabra; Llama|Llama; Chicken|Gallina; Rooster|Gallo; Baby chick|Pollito; Hatching chick|Pollito naciendo;
Duck|Pato; Goose|Ganso; Turkey|Pavo; Horse|Caballo; Donkey|Burro; Rabbit|Conejo; Honeybee|Abeja;
Bug|Oruga; Worm|Lombriz; Snail|Caracol; Lady beetle|Vaquita de San Antonio; Ant|Hormiga; Cricket|Grillo;
Potato|Papa; Carrot|Zanahoria; Tomato|Tomate; Eggplant|Berenjena; Hot pepper|Ají; Bell pepper|Morrón;
Broccoli|Brócoli; Leafy green|Verdura de hoja; Cucumber|Pepino; Garlic|Ajo; Onion|Cebolla; Peanuts|Maní;
Chestnut|Castaña; Beans|Porotos; Pea pod|Arveja; Avocado|Palta; Red apple|Manzana roja; Green apple|Manzana verde;
Pear|Pera; Grapes|Uvas; Strawberry|Frutilla; Blueberries|Arándanos; Cherries|Cerezas; Peach|Durazno;
Lemon|Limón; Tangerine|Mandarina; Banana|Banana; Pineapple|Ananá; Mango|Mango; Melon|Melón;
Watermelon|Sandía; Coconut|Coco; Kiwi fruit|Kiwi; Olive|Aceituna; Ginger root|Jengibre; Roasted sweet potato|Batata;
Hut|Rancho; House with garden|Casa con huerta; Houses|Casas; Axe|Hacha; Hammer and pick|Pico y martillo;
Fuel pump|Surtidor de combustible; Droplet|Gota de agua""",
    ("Ambiente y ecología", ("ecologia",)): """
Mountain|Montaña; Snow-capped mountain|Montaña nevada; National park|Parque nacional; Desert|Desierto;
Desert island|Isla; Volcano|Volcán; Camping|Campamento; Sunrise over mountains|Amanecer en la montaña;
Sunrise|Amanecer; Water wave|Ola; Sun|Sol; Sun behind cloud|Sol y nubes; Sun behind rain cloud|Sol y lluvia;
Cloud|Nube; Cloud with rain|Nube con lluvia; Cloud with lightning|Tormenta eléctrica; Cloud with snow|Nevada;
Cloud with lightning and rain|Tormenta; Fog|Niebla; Tornado|Tornado; Cyclone|Ciclón; Rainbow|Arcoíris;
Snowflake|Copo de nieve; Fire|Fuego; Thermometer|Termómetro; Wind face|Viento; Rock|Roca; Wood|Madera;
Coral|Coral; Lotus|Loto; Nest with eggs|Nido con huevos; Empty nest|Nido; Feather|Pluma; Footprints|Huellas;
Paw prints|Huellas de animal; Fishing pole|Caña de pescar; Recycling symbol|Reciclaje; Wastebasket|Cesto de basura;
Factory|Fábrica; Seedling|Plántula""",
    ("Satélites y teledetección", ("satelite", "ecologia")): """
Satellite|Satélite; Satellite antenna|Antena satelital; Rocket|Cohete; Globe showing americas|Globo terráqueo (América);
Globe showing europe-africa|Globo terráqueo (Europa-África); Globe showing asia-australia|Globo terráqueo (Asia-Oceanía);
Globe with meridians|Globo con meridianos; World map|Mapa mundial; Compass|Brújula; Airplane|Avión;
Helicopter|Helicóptero; Telescope|Telescopio; Comet|Cometa; Crescent moon|Luna creciente; Full moon|Luna llena;
Milky way|Vía Láctea; Ringed planet|Planeta con anillos; Antenna bars|Señal; Camera with flash|Cámara con flash""",
    ("Gráficos y símbolos", ("graficos",)): """
Bar chart|Gráfico de barras; Chart increasing|Gráfico ascendente; Chart decreasing|Gráfico descendente;
Check mark button|Tilde (botón); Check mark|Tilde; Cross mark|Cruz; Cross mark button|Cruz (botón); Warning|Advertencia;
No entry|Prohibido el paso; Prohibited|Prohibido; Plus|Más; Minus|Menos; Multiply|Multiplicar; Divide|Dividir;
Heavy equals sign|Igual; Infinity|Infinito; Red question mark|Pregunta; Red exclamation mark|Exclamación;
Double exclamation mark|Doble exclamación; Recycling symbol|Reciclaje; Radioactive|Radiactivo; Biohazard|Riesgo biológico;
Atom symbol|Átomo; Female sign|Hembra; Male sign|Macho; Medical symbol|Símbolo médico; Up arrow|Flecha arriba;
Down arrow|Flecha abajo; Left arrow|Flecha izquierda; Right arrow|Flecha derecha; Up-down arrow|Flecha arriba-abajo;
Left-right arrow|Flecha izquierda-derecha; Clockwise vertical arrows|Flechas en ciclo;
Counterclockwise arrows button|Flechas antihorarias; Repeat button|Repetir; Information|Información;
High voltage|Alto voltaje; Light bulb|Idea; Star|Estrella; Glowing star|Estrella brillante; Sparkles|Destellos;
Bullseye|Diana; Hundred points|Cien puntos; Stopwatch|Cronómetro; Hourglass done|Reloj de arena;
Red circle|Círculo rojo; Blue circle|Círculo azul; Green circle|Círculo verde; Yellow circle|Círculo amarillo;
Orange circle|Círculo naranja; Purple circle|Círculo violeta; Black circle|Círculo negro; Green square|Cuadrado verde;
Red square|Cuadrado rojo; Blue square|Cuadrado azul""",
}

HEALTH = {  # carpeta de Health Icons -> (categoría, grupos, filtro de nombres o None para todos)
    "devices": ("Laboratorio y objetos", ("laboratorio",), None),
    "diagnostics": ("Laboratorio y objetos", ("laboratorio",), ("biopsy", "malaria-microscope", "mosquito-collection",
                                                                 "rdt-result", "rdt-result_neg", "rdt-result_positive")),
    "graphs": ("Gráficos y símbolos", ("graficos",), None),
    "symbols": ("Gráficos y símbolos", ("graficos",), ("alert", "alert-circle", "alert-triangle", "biomarker", "database",
                                                        "egg-cell", "electricity", "geo-location", "globe", "hazardous",
                                                        "heartbeat", "high-bars", "low-bars", "medium-bars", "lab-search",
                                                        "life-science", "magnifying-glass", "negative", "positive",
                                                        "artificial-intelligence", "bio-pharma", "cancel", "info", "yes",
                                                        "no", "network", "share", "thumbs-up", "thumbs-down")),
    "vehicles": ("Satélites y teledetección", ("satelite", "ecologia"), ("drone", "4x4", "helicopter", "small-plane",
                                                                       "machinery", "cross-country_motorcycle", "bike")),
}


def fluent_items():
    for (cat, groups), block in FLUENT.items():
        for entry in block.replace("\n", " ").split(";"):
            entry = entry.strip()
            if "|" in entry:
                en, es = (x.strip() for x in entry.split("|", 1))
                yield en, es, cat, list(groups)
