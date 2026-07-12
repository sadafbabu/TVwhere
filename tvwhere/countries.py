"""Country and language playlists from iptv-org."""

IPTV_ORG_BASE = "https://iptv-org.github.io/iptv"

DEFAULT_COUNTRY = "global"

# Countries — alphabetical by name after "All"
COUNTRIES = [
    {"code": "global", "name": "All Countries", "url": f"{IPTV_ORG_BASE}/index.m3u", "kind": "all"},
    {"code": "af", "name": "Afghanistan", "url": f"{IPTV_ORG_BASE}/countries/af.m3u", "kind": "country"},
    {"code": "ar", "name": "Argentina", "url": f"{IPTV_ORG_BASE}/countries/ar.m3u", "kind": "country"},
    {"code": "au", "name": "Australia", "url": f"{IPTV_ORG_BASE}/countries/au.m3u", "kind": "country"},
    {"code": "at", "name": "Austria", "url": f"{IPTV_ORG_BASE}/countries/at.m3u", "kind": "country"},
    {"code": "bd", "name": "Bangladesh", "url": f"{IPTV_ORG_BASE}/countries/bd.m3u", "kind": "country"},
    {"code": "be", "name": "Belgium", "url": f"{IPTV_ORG_BASE}/countries/be.m3u", "kind": "country"},
    {"code": "br", "name": "Brazil", "url": f"{IPTV_ORG_BASE}/countries/br.m3u", "kind": "country"},
    {"code": "ca", "name": "Canada", "url": f"{IPTV_ORG_BASE}/countries/ca.m3u", "kind": "country"},
    {"code": "cn", "name": "China", "url": f"{IPTV_ORG_BASE}/countries/cn.m3u", "kind": "country"},
    {"code": "co", "name": "Colombia", "url": f"{IPTV_ORG_BASE}/countries/co.m3u", "kind": "country"},
    {"code": "cz", "name": "Czech Republic", "url": f"{IPTV_ORG_BASE}/countries/cz.m3u", "kind": "country"},
    {"code": "dk", "name": "Denmark", "url": f"{IPTV_ORG_BASE}/countries/dk.m3u", "kind": "country"},
    {"code": "eg", "name": "Egypt", "url": f"{IPTV_ORG_BASE}/countries/eg.m3u", "kind": "country"},
    {"code": "fi", "name": "Finland", "url": f"{IPTV_ORG_BASE}/countries/fi.m3u", "kind": "country"},
    {"code": "fr", "name": "France", "url": f"{IPTV_ORG_BASE}/countries/fr.m3u", "kind": "country"},
    {"code": "de", "name": "Germany", "url": f"{IPTV_ORG_BASE}/countries/de.m3u", "kind": "country"},
    {"code": "gr", "name": "Greece", "url": f"{IPTV_ORG_BASE}/countries/gr.m3u", "kind": "country"},
    {"code": "hk", "name": "Hong Kong", "url": f"{IPTV_ORG_BASE}/countries/hk.m3u", "kind": "country"},
    {"code": "hu", "name": "Hungary", "url": f"{IPTV_ORG_BASE}/countries/hu.m3u", "kind": "country"},
    {"code": "in", "name": "India", "url": f"{IPTV_ORG_BASE}/countries/in.m3u", "kind": "country"},
    {"code": "id", "name": "Indonesia", "url": f"{IPTV_ORG_BASE}/countries/id.m3u", "kind": "country"},
    {"code": "ir", "name": "Iran", "url": f"{IPTV_ORG_BASE}/countries/ir.m3u", "kind": "country"},
    {"code": "iq", "name": "Iraq", "url": f"{IPTV_ORG_BASE}/countries/iq.m3u", "kind": "country"},
    {"code": "il", "name": "Israel", "url": f"{IPTV_ORG_BASE}/countries/il.m3u", "kind": "country"},
    {"code": "it", "name": "Italy", "url": f"{IPTV_ORG_BASE}/countries/it.m3u", "kind": "country"},
    {"code": "jp", "name": "Japan", "url": f"{IPTV_ORG_BASE}/countries/jp.m3u", "kind": "country"},
    {"code": "ke", "name": "Kenya", "url": f"{IPTV_ORG_BASE}/countries/ke.m3u", "kind": "country"},
    {"code": "kr", "name": "South Korea", "url": f"{IPTV_ORG_BASE}/countries/kr.m3u", "kind": "country"},
    {"code": "my", "name": "Malaysia", "url": f"{IPTV_ORG_BASE}/countries/my.m3u", "kind": "country"},
    {"code": "mx", "name": "Mexico", "url": f"{IPTV_ORG_BASE}/countries/mx.m3u", "kind": "country"},
    {"code": "nl", "name": "Netherlands", "url": f"{IPTV_ORG_BASE}/countries/nl.m3u", "kind": "country"},
    {"code": "ng", "name": "Nigeria", "url": f"{IPTV_ORG_BASE}/countries/ng.m3u", "kind": "country"},
    {"code": "no", "name": "Norway", "url": f"{IPTV_ORG_BASE}/countries/no.m3u", "kind": "country"},
    {"code": "pk", "name": "Pakistan", "url": f"{IPTV_ORG_BASE}/countries/pk.m3u", "kind": "country"},
    {"code": "ph", "name": "Philippines", "url": f"{IPTV_ORG_BASE}/countries/ph.m3u", "kind": "country"},
    {"code": "pl", "name": "Poland", "url": f"{IPTV_ORG_BASE}/countries/pl.m3u", "kind": "country"},
    {"code": "pt", "name": "Portugal", "url": f"{IPTV_ORG_BASE}/countries/pt.m3u", "kind": "country"},
    {"code": "ro", "name": "Romania", "url": f"{IPTV_ORG_BASE}/countries/ro.m3u", "kind": "country"},
    {"code": "ru", "name": "Russia", "url": f"{IPTV_ORG_BASE}/countries/ru.m3u", "kind": "country"},
    {"code": "sa", "name": "Saudi Arabia", "url": f"{IPTV_ORG_BASE}/countries/sa.m3u", "kind": "country"},
    {"code": "sg", "name": "Singapore", "url": f"{IPTV_ORG_BASE}/countries/sg.m3u", "kind": "country"},
    {"code": "za", "name": "South Africa", "url": f"{IPTV_ORG_BASE}/countries/za.m3u", "kind": "country"},
    {"code": "es", "name": "Spain", "url": f"{IPTV_ORG_BASE}/countries/es.m3u", "kind": "country"},
    {"code": "se", "name": "Sweden", "url": f"{IPTV_ORG_BASE}/countries/se.m3u", "kind": "country"},
    {"code": "ch", "name": "Switzerland", "url": f"{IPTV_ORG_BASE}/countries/ch.m3u", "kind": "country"},
    {"code": "tw", "name": "Taiwan", "url": f"{IPTV_ORG_BASE}/countries/tw.m3u", "kind": "country"},
    {"code": "th", "name": "Thailand", "url": f"{IPTV_ORG_BASE}/countries/th.m3u", "kind": "country"},
    {"code": "tr", "name": "Turkey", "url": f"{IPTV_ORG_BASE}/countries/tr.m3u", "kind": "country"},
    {"code": "ae", "name": "UAE", "url": f"{IPTV_ORG_BASE}/countries/ae.m3u", "kind": "country"},
    {"code": "ua", "name": "Ukraine", "url": f"{IPTV_ORG_BASE}/countries/ua.m3u", "kind": "country"},
    {"code": "gb", "name": "United Kingdom", "url": f"{IPTV_ORG_BASE}/countries/gb.m3u", "kind": "country"},
    {"code": "us", "name": "United States", "url": f"{IPTV_ORG_BASE}/countries/us.m3u", "kind": "country"},
    {"code": "vn", "name": "Vietnam", "url": f"{IPTV_ORG_BASE}/countries/vn.m3u", "kind": "country"},
]

LANGUAGES = [
    {"code": "ben", "name": "Bengali", "url": f"{IPTV_ORG_BASE}/languages/ben.m3u", "kind": "language"},
    {"code": "hin", "name": "Hindi", "url": f"{IPTV_ORG_BASE}/languages/hin.m3u", "kind": "language"},
    {"code": "ara", "name": "Arabic", "url": f"{IPTV_ORG_BASE}/languages/ara.m3u", "kind": "language"},
    {"code": "eng", "name": "English", "url": f"{IPTV_ORG_BASE}/languages/eng.m3u", "kind": "language"},
    {"code": "spa", "name": "Spanish", "url": f"{IPTV_ORG_BASE}/languages/spa.m3u", "kind": "language"},
    {"code": "fra", "name": "French", "url": f"{IPTV_ORG_BASE}/languages/fra.m3u", "kind": "language"},
    {"code": "deu", "name": "German", "url": f"{IPTV_ORG_BASE}/languages/deu.m3u", "kind": "language"},
    {"code": "por", "name": "Portuguese", "url": f"{IPTV_ORG_BASE}/languages/por.m3u", "kind": "language"},
    {"code": "rus", "name": "Russian", "url": f"{IPTV_ORG_BASE}/languages/rus.m3u", "kind": "language"},
    {"code": "jpn", "name": "Japanese", "url": f"{IPTV_ORG_BASE}/languages/jpn.m3u", "kind": "language"},
    {"code": "kor", "name": "Korean", "url": f"{IPTV_ORG_BASE}/languages/kor.m3u", "kind": "language"},
    {"code": "zho", "name": "Chinese", "url": f"{IPTV_ORG_BASE}/languages/zho.m3u", "kind": "language"},
]

_ALL = COUNTRIES + LANGUAGES
_CODE_MAP = {c["code"]: c for c in _ALL}


def is_valid_code(code: str) -> bool:
    return code in _CODE_MAP


def list_countries() -> list:
    return [{"code": c["code"], "name": c["name"], "kind": c["kind"]} for c in COUNTRIES]


def list_languages() -> list:
    return [{"code": c["code"], "name": c["name"], "kind": "language"} for c in LANGUAGES]


def list_all_regions() -> dict:
    return {"countries": list_countries(), "languages": list_languages()}


def get_country(code: str) -> dict:
    return _CODE_MAP.get(code, _CODE_MAP[DEFAULT_COUNTRY])


def get_url(code: str) -> str:
    return get_country(code)["url"]


def get_name(code: str) -> str:
    return get_country(code)["name"]
