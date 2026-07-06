import os
import re
import difflib
import requests

from clickup_map import normalize, COMPANIES

CLICKUP_API_TOKEN = os.environ.get("CLICKUP_API_TOKEN")
CLICKUP_API_V3 = "https://api.clickup.com/api/v3"
WORKSPACE_ID = "9011628707"

DOCUMENT_REQUEST_KEYWORDS = [
    "manda", "mandar", "enviar", "envia", "preciso do", "preciso da",
    "busca", "buscar", "cade", "quero o", "quero a", "pode mandar",
    "me manda", "me envia",
]

DOC_INDEX = {
    "smart ventures": {"doc_id": "8cj52n3-21211", "page_id": "8cj52n3-3331"},
}

ROW_RE = re.compile(r"^\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|$", re.MULTILINE)
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def is_document_request(text_norm):
    return any(kw in text_norm for kw in DOCUMENT_REQUEST_KEYWORDS)


def _parse_table(markdown):
    rows = []
    for match in ROW_RE.finditer(markdown):
        desc, link_cell, date = match.groups()
        if not desc or desc.startswith("---") or normalize(desc) == "descricao":
            continue
        link_match = LINK_RE.search(link_cell)
        link = link_match.group(2) if link_match else link_cell.replace("<br>", "").strip()
        if not link:
            continue
        rows.append({"descricao": desc, "link": link, "data": date})
    return rows


def fetch_rows(doc_id, page_id):
    url = f"{CLICKUP_API_V3}/workspaces/{WORKSPACE_ID}/docs/{doc_id}/pages/{page_id}"
    r = requests.get(url, headers={"Authorization": CLICKUP_API_TOKEN}, params={"content_format": "text/md"}, timeout=15)
    r.raise_for_status()
    content = r.json().get("content", "")
    return _parse_table(content)


def _strip_known_phrases(text_norm, company_key):
    stripped = text_norm
    for alias in COMPANIES[company_key]["aliases"]:
        stripped = stripped.replace(alias, " ")
    for kw in DOCUMENT_REQUEST_KEYWORDS:
        stripped = stripped.replace(kw, " ")
    return stripped


def _word_similar(a, b):
    if a == b:
        return 1.0
    if len(a) < 3 or len(b) < 3:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def find_document(company_key, text_norm):
    entry = DOC_INDEX.get(company_key)
    if not entry:
        return {"ok": False, "reason": f"ainda não tenho um índice de documentos para {company_key}"}

    rows = fetch_rows(entry["doc_id"], entry["page_id"])

    core_query = _strip_known_phrases(text_norm, company_key)
    query_words = [w for w in core_query.split() if len(w) > 2]

    if not query_words:
        opcoes = ", ".join(r["descricao"] for r in rows)
        return {"ok": False, "reason": f"não entendi qual documento. Disponíveis: {opcoes}"}

    best, best_score = None, 0.0
    for row in rows:
        desc_words = [w for w in normalize(row["descricao"]).split() if len(w) > 2]
        score = 0.0
        for qw in query_words:
            match_ratio = max((_word_similar(qw, dw) for dw in desc_words), default=0.0)
            if match_ratio >= 0.8:
                score += match_ratio
        if score > best_score:
            best, best_score = row, score

    if not best or best_score < 0.8:
        opcoes = ", ".join(r["descricao"] for r in rows)
        return {"ok": False, "reason": f"não achei esse documento com confiança. Disponíveis: {opcoes}"}

    return {"ok": True, "descricao": best["descricao"], "link": best["link"]}
