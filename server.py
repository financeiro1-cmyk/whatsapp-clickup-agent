import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "")

    print(f"[WhatsApp] {sender}: {incoming_msg}")

    resp = MessagingResponse()
    resp.message(f"Recebido: \"{incoming_msg}\". (próximo passo: interpretar e criar no ClickUp)")
    return str(resp)


if __name__ == "__main__":
    app.run(port=5000, debug=True)
