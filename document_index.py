import os
import re
import requests

from clickup_map import normalize

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


def find_document(company_key, text_norm):
    entry = DOC_INDEX.get(company_key)
    if not entry:
        return {"ok": False, "reason": f"ainda não tenho um índice de documentos para {company_key}"}

    rows = fetch_rows(entry["doc_id"], entry["page_id"])

    query_words = set(w for w in text_norm.split() if len(w) > 2)
    best, best_score = None, 0
    for row in rows:
        desc_norm = normalize(row["descricao"])
        desc_words = set(desc_norm.split())
        score = len(query_words & desc_words)
        if desc_norm in text_norm:
            score += 3
        if score > best_score:
            best, best_score = row, score

    if not best or best_score == 0:
        opcoes = ", ".join(r["descricao"] for r in rows)
        return {"ok": False, "reason": f"não achei esse documento. Disponíveis: {opcoes}"}

    return {"ok": True, "descricao": best["descricao"], "link": best["link"]}
