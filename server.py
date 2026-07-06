import os
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

import clickup_map
import document_index

load_dotenv()

app = Flask(__name__)

CLICKUP_API_TOKEN = os.environ.get("CLICKUP_API_TOKEN")
CLICKUP_API_BASE = "https://api.clickup.com/api/v2"


def make_title(text, max_len=75):
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "..."


def create_clickup_task(list_id, name, description, priority):
    url = f"{CLICKUP_API_BASE}/list/{list_id}/task"
    headers = {"Authorization": CLICKUP_API_TOKEN, "Content-Type": "application/json"}
    payload = {
        "name": name,
        "markdown_description": description + "\n\n_Criado via WhatsApp (ClickUp IA)_",
        "priority": {"urgent": 1, "high": 2, "normal": 3, "low": 4}[priority],
    }
    r = requests.post(url, json=payload, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()


@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "")

    print(f"[WhatsApp] {sender}: {incoming_msg}")

    resp = MessagingResponse()

    if not incoming_msg:
        resp.message("Não recebi nenhum texto. Manda a demanda descrevendo empresa + área + o que precisa.")
        return str(resp)

    text_norm = clickup_map.normalize(incoming_msg)
    company_key = clickup_map.find_company(text_norm)

    if company_key and document_index.is_document_request(text_norm):
        doc_result = document_index.find_document(company_key, text_norm)
        if doc_result["ok"]:
            resp.message(f"{doc_result['descricao']}:\n{doc_result['link']}")
        else:
            resp.message(f"Não consegui enviar o documento: {doc_result['reason']}")
        return str(resp)

    result = clickup_map.resolve(incoming_msg)

    if not result["ok"]:
        resp.message(
            f"Não consegui identificar {result['reason']}. "
            f"Manda de novo citando a empresa e a área, ex: \"Villa Lisboa financeiro: ...\""
        )
        return str(resp)

    try:
        task = create_clickup_task(
            list_id=result["list_id"],
            name=make_title(incoming_msg),
            description=incoming_msg,
            priority=result["priority"],
        )
        task_url = task.get("url", "")
        resp.message(
            f"Tarefa criada em {result['company'].title()} > {result['area'].title()}.\n{task_url}"
        )
    except Exception as e:
        print(f"[ERRO ao criar tarefa] {e}")
        resp.message("Identifiquei a empresa e área, mas houve um erro ao criar a tarefa no ClickUp. Já registrei o log pra investigar.")

    return str(resp)


if __name__ == "__main__":
    app.run(port=5000, debug=True)
