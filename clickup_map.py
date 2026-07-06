import unicodedata


def normalize(text):
    text = text.lower().strip()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    return text


COMPANIES = {
    "led": {
        "aliases": ["led"],
        "areas": {
            "comunicacao": {"aliases": ["comunicacao", "comunicaçao"], "list_id": "901113681285"},
            "obras": {"aliases": ["obras", "gerenciamento de obras"], "list_id": "901113286593"},
            "financeiro": {"aliases": ["financeiro"], "list_id": "901113745194"},
            "design": {"aliases": ["design", "criacao", "criação"], "list_id": "901113749447"},
        },
    },
    "smart ventures": {
        "aliases": ["smart ventures", "sv", "s ventures"],
        "areas": {
            "comunicacao": {"aliases": ["comunicacao", "comunicaçao"], "list_id": "901113663252"},
            "comercial": {"aliases": ["comercial"], "list_id": "901113663284"},
            "engenharia": {"aliases": ["engenharia"], "list_id": "901113663341"},
            "financeiro": {"aliases": ["financeiro"], "list_id": "901113745198"},
            "design": {"aliases": ["design", "criacao", "criação"], "list_id": "901113749450"},
        },
    },
    "speed tax": {
        "aliases": ["speed tax", "speed"],
        "areas": {
            "comunicacao": {"aliases": ["comunicacao", "comunicaçao"], "list_id": "901113393845"},
            "comercial": {"aliases": ["comercial"], "list_id": "901113680427"},
            "financeiro": {"aliases": ["financeiro"], "list_id": "901113745208"},
            "design": {"aliases": ["design", "criacao", "criação"], "list_id": "901113749458"},
        },
    },
    "smart trietment": {
        "aliases": ["smart trietment", "trietment", "treatment", "smart treatment"],
        "areas": {
            "comunicacao": {"aliases": ["comunicacao", "comunicaçao"], "list_id": "901113393839"},
            "financeiro": {"aliases": ["financeiro"], "list_id": "901113745210"},
            "comercial": {"aliases": ["comercial"], "list_id": "901113745215"},
            "design": {"aliases": ["design", "criacao", "criação"], "list_id": "901113749461"},
        },
    },
    "villa lisboa": {
        "aliases": ["villa lisboa", "vila lisboa", "v lisboa"],
        "areas": {
            "comunicacao": {"aliases": ["comunicacao", "comunicaçao"], "list_id": "901113393826"},
            "obras": {"aliases": ["obras", "gerenciamento de obras"], "list_id": "901111758473"},
            "comercial": {"aliases": ["comercial"], "list_id": "901111758683"},
            "financeiro": {"aliases": ["financeiro"], "list_id": "901111758693"},
            "design": {"aliases": ["design", "criacao", "criação"], "list_id": "901113749454"},
        },
    },
    "villa cachoeira": {
        "aliases": ["villa cachoeira", "vila cachoeira", "v cachoeira"],
        "areas": {
            "comunicacao": {"aliases": ["comunicacao", "comunicaçao"], "list_id": "901113694709"},
            "obras": {"aliases": ["obras", "gerenciamento de obras"], "list_id": "901111758982"},
            "arquitetura": {"aliases": ["arquitetura"], "list_id": "901111922757"},
            "comercial": {"aliases": ["comercial"], "list_id": "901111758962"},
            "financeiro": {"aliases": ["financeiro"], "list_id": "901111758984"},
            "design": {"aliases": ["design", "criacao", "criação"], "list_id": "901113749456"},
        },
    },
    "axle": {
        "aliases": ["axle"],
        "areas": {
            "comunicacao": {"aliases": ["comunicacao", "comunicaçao"], "list_id": "901112220523"},
            "customer success": {"aliases": ["customer success", "cs"], "list_id": "901112214985"},
            "comercial": {"aliases": ["comercial"], "list_id": "901112214997"},
            "financeiro": {"aliases": ["financeiro"], "list_id": "901112215004"},
            "design": {"aliases": ["design", "criacao", "criação"], "list_id": "901113749467"},
        },
    },
    "time sale": {
        "aliases": ["time sale", "timesale"],
        "areas": {
            "comunicacao": {"aliases": ["comunicacao", "comunicaçao"], "list_id": "901113393854"},
            "financeiro": {"aliases": ["financeiro"], "list_id": "901113745219"},
            "design": {"aliases": ["design", "criacao", "criação"], "list_id": "901113749462"},
        },
    },
}

URGENT_KEYWORDS = ["urgente", "urgencia", "urgência", "prioridade maxima", "emergencia", "emergência"]
HIGH_KEYWORDS = ["importante", "prioridade alta", "alta prioridade"]


def find_company(text_norm):
    candidates = []
    for key, data in COMPANIES.items():
        for alias in data["aliases"]:
            if alias in text_norm:
                candidates.append((len(alias), key))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def find_area(text_norm, company_key):
    areas = COMPANIES[company_key]["areas"]
    candidates = []
    for area_key, data in areas.items():
        for alias in data["aliases"]:
            if alias in text_norm:
                candidates.append((len(alias), area_key))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def detect_priority(text_norm):
    for kw in URGENT_KEYWORDS:
        if kw in text_norm:
            return "urgent"
    for kw in HIGH_KEYWORDS:
        if kw in text_norm:
            return "high"
    return "normal"


def resolve(raw_text):
    text_norm = normalize(raw_text)
    company_key = find_company(text_norm)
    if not company_key:
        return {"ok": False, "reason": "a empresa"}

    area_key = find_area(text_norm, company_key)
    if not area_key:
        areas_disponiveis = ", ".join(COMPANIES[company_key]["areas"].keys())
        return {"ok": False, "reason": f"a área (opções para {company_key}: {areas_disponiveis})"}

    return {
        "ok": True,
        "company": company_key,
        "area": area_key,
        "list_id": COMPANIES[company_key]["areas"][area_key]["list_id"],
        "priority": detect_priority(text_norm),
    }
