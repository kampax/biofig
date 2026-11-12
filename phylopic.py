"""Busqueda de siluetas de organismos en PhyloPic (api.phylopic.org), con cache local.

Solo se devuelven imagenes con licencias que permiten uso y modificacion sin restricciones
comerciales: CC0, Public Domain Mark, CC BY y CC BY-SA. Se excluyen NC y ND.
"""
import re
import unicodedata
from pathlib import Path

import httpx

API = "https://api.phylopic.org"
IMG = "https://images.phylopic.org/images"
CACHE = Path(__file__).parent / "data" / "phylopic"
CACHE.mkdir(parents=True, exist_ok=True)
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

# Nombres comunes (es / en, sin tildes) -> nombre cientifico del clado en PhyloPic
COMMON = {
    # mamiferos
    "zorro": "vulpes", "fox": "vulpes", "zorro rojo": "vulpes vulpes", "red fox": "vulpes vulpes",
    "lobo": "canis lupus", "wolf": "canis lupus", "perro": "canis familiaris", "dog": "canis familiaris",
    "coyote": "canis latrans", "chacal": "canis aureus", "jackal": "canis aureus",
    "conejo": "oryctolagus cuniculus", "rabbit": "oryctolagus cuniculus", "liebre": "lepus", "hare": "lepus",
    "raton": "mus musculus", "mouse": "mus musculus", "rata": "rattus", "rat": "rattus",
    "ardilla": "sciurus", "squirrel": "sciurus", "castor": "castor", "beaver": "castor",
    "ciervo": "cervus elaphus", "deer": "cervidae", "venado": "odocoileus", "corzo": "capreolus capreolus", "roe deer": "capreolus capreolus",
    "alce": "alces alces", "moose": "alces alces", "reno": "rangifer tarandus", "reindeer": "rangifer tarandus",
    "jabali": "sus scrofa", "wild boar": "sus scrofa", "cerdo": "sus scrofa domesticus", "pig": "sus scrofa domesticus",
    "vaca": "bos taurus", "cow": "bos taurus", "cattle": "bos taurus", "oveja": "ovis aries", "sheep": "ovis aries",
    "cabra": "capra hircus", "goat": "capra hircus", "cabra montes": "capra pyrenaica", "ibex": "capra ibex",
    "caballo": "equus caballus", "horse": "equus caballus", "cebra": "equus quagga", "zebra": "equus quagga",
    "oso": "ursus", "bear": "ursus", "oso pardo": "ursus arctos", "brown bear": "ursus arctos", "oso polar": "ursus maritimus", "polar bear": "ursus maritimus",
    "lince": "lynx", "lynx": "lynx", "lince iberico": "lynx pardinus", "iberian lynx": "lynx pardinus",
    "gato": "felis catus", "cat": "felis catus", "gato montes": "felis silvestris", "wildcat": "felis silvestris",
    "leon": "panthera leo", "lion": "panthera leo", "tigre": "panthera tigris", "tiger": "panthera tigris",
    "leopardo": "panthera pardus", "leopard": "panthera pardus", "jaguar": "panthera onca", "puma": "puma concolor",
    "guepardo": "acinonyx jubatus", "cheetah": "acinonyx jubatus", "hiena": "hyaenidae", "hyena": "hyaenidae",
    "tejon": "meles meles", "badger": "meles meles", "nutria": "lutra lutra", "otter": "lutra lutra",
    "comadreja": "mustela nivalis", "weasel": "mustela", "erizo": "erinaceus europaeus", "hedgehog": "erinaceus europaeus",
    "murcielago": "chiroptera", "bat": "chiroptera", "topo": "talpa", "mole": "talpa",
    "elefante": "loxodonta africana", "elephant": "loxodonta africana", "jirafa": "giraffa", "giraffe": "giraffa",
    "rinoceronte": "rhinocerotidae", "rhinoceros": "rhinocerotidae", "hipopotamo": "hippopotamus amphibius", "hippopotamus": "hippopotamus amphibius",
    "camello": "camelus", "camel": "camelus", "llama": "lama glama", "guanaco": "lama guanicoe", "vicuna": "vicugna vicugna",
    "mono": "primates", "monkey": "primates", "chimpance": "pan troglodytes", "chimpanzee": "pan troglodytes",
    "gorila": "gorilla", "gorilla": "gorilla", "humano": "homo sapiens", "human": "homo sapiens", "persona": "homo sapiens",
    "canguro": "macropus", "kangaroo": "macropus", "koala": "phascolarctos cinereus", "armadillo": "dasypodidae",
    "ballena": "balaenoptera", "whale": "cetacea", "ballena jorobada": "megaptera novaeangliae", "humpback whale": "megaptera novaeangliae",
    "delfin": "delphinidae", "dolphin": "delphinidae", "orca": "orcinus orca", "foca": "phocidae", "seal": "phocidae",
    "lobo marino": "otariidae", "sea lion": "otariidae", "morsa": "odobenus rosmarus", "walrus": "odobenus rosmarus",
    "bisonte": "bison", "bison": "bison", "carpincho": "hydrochoerus hydrochaeris", "capybara": "hydrochoerus hydrochaeris",
    # aves
    "ave": "aves", "aves": "aves", "bird": "aves", "pajaro": "passeriformes", "songbird": "passeriformes",
    "aguila": "aquila", "eagle": "aquila", "aguila real": "aquila chrysaetos", "golden eagle": "aquila chrysaetos",
    "halcon": "falco", "falcon": "falco", "gavilan": "accipiter", "hawk": "buteo", "ratonero": "buteo buteo", "buzzard": "buteo buteo",
    "buitre": "gyps", "vulture": "gyps", "condor": "vultur gryphus", "milano": "milvus", "kite": "milvus",
    "buho": "bubo", "owl": "strigiformes", "lechuza": "tyto alba", "barn owl": "tyto alba", "mochuelo": "athene noctua",
    "perdiz": "phasianidae", "partridge": "phasianidae", "codorniz": "coturnix coturnix", "quail": "coturnix coturnix",
    "gallina": "gallus gallus", "chicken": "gallus gallus", "pato": "anas platyrhynchos", "duck": "anatidae", "ganso": "anser", "goose": "anser",
    "cisne": "cygnus", "swan": "cygnus", "garza": "ardea", "heron": "ardea", "cigüena": "ciconia ciconia", "ciguena": "ciconia ciconia", "stork": "ciconia",
    "flamenco": "phoenicopterus", "flamingo": "phoenicopterus", "gaviota": "laridae", "gull": "laridae",
    "pinguino": "spheniscidae", "penguin": "spheniscidae", "paloma": "columba livia", "pigeon": "columba livia",
    "gorrion": "passer domesticus", "sparrow": "passer domesticus", "golondrina": "hirundo rustica", "swallow": "hirundo rustica",
    "cuervo": "corvus", "crow": "corvus", "raven": "corvus corax", "urraca": "pica pica", "magpie": "pica pica",
    "pajaro carpintero": "picidae", "woodpecker": "picidae", "colibri": "trochilidae", "hummingbird": "trochilidae",
    "loro": "psittaciformes", "parrot": "psittaciformes", "avestruz": "struthio camelus", "ostrich": "struthio camelus",
    "pelicano": "pelecanus", "pelican": "pelecanus", "martin pescador": "alcedo atthis", "kingfisher": "alcedo atthis",
    "petirrojo": "erithacus rubecula", "robin": "erithacus rubecula", "carbonero": "parus major",
    # reptiles / anfibios
    "serpiente": "serpentes", "snake": "serpentes", "vibora": "vipera", "viper": "vipera", "culebra": "colubridae",
    "lagarto": "lacertidae", "lizard": "squamata", "lagartija": "podarcis", "iguana": "iguana", "camaleon": "chamaeleonidae", "chameleon": "chamaeleonidae",
    "tortuga": "testudines", "turtle": "testudines", "tortuga marina": "cheloniidae", "sea turtle": "cheloniidae",
    "cocodrilo": "crocodylidae", "crocodile": "crocodylidae", "caiman": "caimaninae", "alligator": "alligator",
    "rana": "rana", "frog": "anura", "sapo": "bufo", "toad": "bufo", "salamandra": "salamandra", "salamander": "caudata", "triton": "triturus", "newt": "triturus",
    # peces
    "pez": "actinopterygii", "fish": "actinopterygii", "trucha": "salmo trutta", "trout": "salmo trutta", "salmon": "salmo salar",
    "atun": "thunnus", "tuna": "thunnus", "sardina": "sardina pilchardus", "sardine": "sardina pilchardus",
    "tiburon": "selachimorpha", "shark": "selachimorpha", "raya": "batoidea", "ray": "batoidea", "carpa": "cyprinus carpio", "carp": "cyprinus carpio",
    "anguila": "anguilla", "eel": "anguilla", "bacalao": "gadus morhua", "cod": "gadus morhua", "pez payaso": "amphiprion",
    # invertebrados
    "insecto": "insecta", "insect": "insecta", "saltamontes": "caelifera", "grasshopper": "caelifera", "langosta": "locusta migratoria", "locust": "locusta migratoria",
    "mariposa": "papilionoidea", "butterfly": "papilionoidea", "polilla": "lepidoptera", "moth": "lepidoptera", "oruga": "lepidoptera",
    "abeja": "apis mellifera", "bee": "apis mellifera", "abejorro": "bombus", "bumblebee": "bombus", "avispa": "vespidae", "wasp": "vespidae",
    "hormiga": "formicidae", "ant": "formicidae", "escarabajo": "coleoptera", "beetle": "coleoptera", "mariquita": "coccinellidae", "ladybug": "coccinellidae",
    "mosca": "diptera", "fly": "diptera", "mosquito": "culicidae", "libelula": "odonata", "dragonfly": "odonata",
    "pulgon": "aphididae", "aphid": "aphididae", "cucaracha": "blattodea", "cockroach": "blattodea", "termita": "isoptera", "termite": "isoptera",
    "arana": "araneae", "spider": "araneae", "escorpion": "scorpiones", "scorpion": "scorpiones", "garrapata": "ixodida", "tick": "ixodida", "acaro": "acari", "mite": "acari",
    "lombriz": "lumbricus terrestris", "earthworm": "lumbricus terrestris", "gusano": "annelida", "worm": "annelida", "nematodo": "nematoda", "nematode": "nematoda",
    "caracol": "gastropoda", "snail": "gastropoda", "babosa": "gastropoda", "slug": "gastropoda", "almeja": "bivalvia", "clam": "bivalvia", "mejillon": "mytilus", "mussel": "mytilus",
    "pulpo": "octopus", "octopus": "octopus", "calamar": "teuthida", "squid": "teuthida",
    "cangrejo": "brachyura", "crab": "brachyura", "camaron": "caridea", "shrimp": "caridea", "krill": "euphausiacea",
    "copepodo": "copepoda", "copepod": "copepoda", "zooplancton": "copepoda", "zooplankton": "copepoda", "dafnia": "daphnia", "daphnia": "daphnia",
    "medusa": "scyphozoa", "jellyfish": "scyphozoa", "coral": "anthozoa", "estrella de mar": "asteroidea", "starfish": "asteroidea", "erizo de mar": "echinoidea", "sea urchin": "echinoidea",
    "esponja": "porifera", "sponge": "porifera",
    # plantas, hongos y microorganismos
    "planta": "embryophyta", "plant": "embryophyta", "arbol": "spermatophyta", "tree": "spermatophyta",
    "encina": "quercus ilex", "holm oak": "quercus ilex", "roble": "quercus", "oak": "quercus", "alcornoque": "quercus suber", "cork oak": "quercus suber",
    "pino": "pinus", "pine": "pinus", "abeto": "abies", "fir": "abies", "haya": "fagus", "beech": "fagus", "abedul": "betula", "birch": "betula",
    "eucalipto": "eucalyptus", "eucalyptus": "eucalyptus", "olivo": "olea europaea", "olive": "olea europaea", "palmera": "arecaceae", "palm": "arecaceae",
    "pasto": "poaceae", "grass": "poaceae", "hierba": "poaceae", "trigo": "triticum", "wheat": "triticum", "maiz": "zea mays", "maize": "zea mays", "corn": "zea mays",
    "arroz": "oryza sativa", "rice": "oryza sativa", "girasol": "helianthus annuus", "sunflower": "helianthus annuus",
    "leguminosa": "fabaceae", "legume": "fabaceae", "trebol": "trifolium", "clover": "trifolium", "soja": "glycine max", "soybean": "glycine max",
    "cactus": "cactaceae", "helecho": "polypodiopsida", "fern": "polypodiopsida", "musgo": "bryophyta", "moss": "bryophyta",
    "arabidopsis": "arabidopsis thaliana", "tomate": "solanum lycopersicum", "tomato": "solanum lycopersicum",
    "alga": "chlorophyta", "algae": "chlorophyta", "kelp": "laminariales", "diatomea": "bacillariophyta", "diatom": "bacillariophyta",
    "fitoplancton": "bacillariophyta", "phytoplankton": "bacillariophyta",
    "hongo": "fungi", "fungus": "fungi", "seta": "agaricales", "mushroom": "agaricales", "levadura": "saccharomyces cerevisiae", "yeast": "saccharomyces cerevisiae",
    "liquen": "lecanoromycetes", "lichen": "lecanoromycetes",
}

LICENSES = [
    ("publicdomain/zero", "CC0"), ("publicdomain/mark", "Dominio público"),
    ("by-nc", None), ("by-nd", None),  # excluidas
    ("by-sa/4.0", "CC BY-SA 4.0"), ("by-sa/3.0", "CC BY-SA 3.0"),
    ("by/4.0", "CC BY 4.0"), ("by/3.0", "CC BY 3.0"), ("by/2.0", "CC BY 2.0"),
]

_build = None
_search_cache: dict[str, list] = {}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return re.sub(r"\s+", " ", "".join(c for c in s if not unicodedata.combining(c))).strip()


def common_to_taxon(q: str) -> str:
    n = _norm(q)
    if n in COMMON:
        return COMMON[n]
    for cand in (n[:-2] if n.endswith("es") else None, n[:-1] if n.endswith("s") else None):
        if cand and cand in COMMON:
            return COMMON[cand]
    return n


def license_label(href: str):
    for key, label in LICENSES:
        if key in href:
            return label
    return None


async def _get(client: httpx.AsyncClient, path: str, **params):
    global _build
    if _build is None:
        r = await client.get(f"{API}/nodes", params={"build": 1, "page": 0})
        _build = r.json().get("build")
    params["build"] = _build
    r = await client.get(f"{API}{path}", params=params)
    if r.status_code == 404:
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        if "Outdated" not in str(body.get("errors")):
            return {}  # sin resultados
        _build = body.get("build")  # PhyloPic actualizo su indice
        params["build"] = _build
        r = await client.get(f"{API}{path}", params=params)
        if r.status_code == 404:
            return {}
    r.raise_for_status()
    return r.json()


async def _find_node(client, taxon: str):
    """Busca el nodo por nombre exacto; si no, por autocompletado; si no, por el genero."""
    for name in (taxon, None, taxon.split()[0] if " " in taxon else None):
        if name is None:
            ac = await _get(client, "/autocomplete", query=taxon)
            name = (ac.get("matches") or [None])[0]
            if not name:
                continue
        res = await _get(client, "/nodes", filter_name=name, embed_items="true", embed_primaryImage="true", page=0)
        items = res.get("_embedded", {}).get("items", [])
        if items:
            return items[0]
    return None


def _to_icon(img: dict, node_title: str):
    links = img.get("_links", {})
    lic = license_label(links.get("license", {}).get("href", ""))
    vec = links.get("vectorFile")
    if not lic or not vec:
        return None
    try:
        w, h = (float(x) for x in vec.get("sizes", "1x1").split("x"))
    except ValueError:
        w = h = 1.0
    return {
        "id": f"pp:{img['uuid']}",
        "name": links.get("specificNode", {}).get("title") or node_title,
        "src": f"/phylopic/{img['uuid']}.svg",
        "category": f"PhyloPic · {node_title}",
        "groups": ["ecologia"],
        "author": img.get("attribution") or "Anónimo",
        "license": lic,
        "source": "PhyloPic",
        "aspect": round(w / h, 4) if h else 1.0,
        "silhouette": True,
    }


async def search(query: str, limit: int = 12) -> list[dict]:
    """Devuelve iconos (mismo formato que la biblioteca local) para un nombre comun o cientifico."""
    taxon = common_to_taxon(query)
    if not taxon or len(taxon) < 3:
        return []
    if taxon in _search_cache:
        return _search_cache[taxon][:limit]
    out, seen = [], set()
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        node = await _find_node(client, taxon)
        for _level in range(3):  # si el taxon no tiene imagenes, subir al grupo padre
            if not node:
                break
            node_title = node["names"][0][0].get("text", taxon) if node.get("names") else taxon
            imgs = await _get(client, "/images", filter_clade=node["uuid"], embed_items="true", page=0)
            primary = node.get("_embedded", {}).get("primaryImage")
            for img in ([primary] if primary else []) + imgs.get("_embedded", {}).get("items", []):
                ic = _to_icon(img, node_title)
                if ic and ic["id"] not in seen:
                    seen.add(ic["id"])
                    out.append(ic)
            if out:
                break
            parent = node.get("_links", {}).get("parentNode")
            if not parent:
                break
            node = await _get(client, parent["href"].split("?")[0], embed_primaryImage="true")

    # Primero la especie exacta pedida, despues otras del mismo genero, despues el resto (orden estable)
    def rank(ic):
        name = _norm(ic["name"])
        if name == taxon or name.startswith(taxon + " "):
            return 0
        return 1 if name.split(" ")[0] == taxon.split(" ")[0] else 2
    out.sort(key=rank)
    _search_cache[taxon] = out
    return out[:limit]


async def svg_path(uuid: str) -> Path | None:
    if not UUID_RE.match(uuid):
        return None
    p = CACHE / f"{uuid}.svg"
    if not p.exists():
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            r = await client.get(f"{IMG}/{uuid}/vector.svg")
            if r.status_code != 200 or b"<svg" not in r.content[:2000]:
                return None
            p.write_bytes(r.content)
    return p
