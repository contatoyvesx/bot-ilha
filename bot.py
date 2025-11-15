from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from openai import OpenAI
import requests
import os

app = FastAPI()

# ===============================
# VARIÁVEIS DE AMBIENTE
# ===============================
VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "minha_senha_verificacao")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")  # Token da página Meta
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")  # ID do telefone Meta
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


# ===============================
# 1) VERIFICAÇÃO DO WEBHOOK META
# ===============================
@app.get("/webhook")
async def verify_token(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200)

    return PlainTextResponse(content="Erro de verificação", status_code=403)


# ===============================
# 2) RECEBE AS MENSAGENS DO WHATSApp
# ===============================
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("📩 RECEBIDO:", data)

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        messages = value.get("messages")
        if not messages:
            return {"status": "ignored"}

        message = messages[0]
        from_number = message["from"]
        text = message.get("text", {}).get("body", "")

        if not text:
            send_message(from_number, "Envie uma mensagem de texto para continuar 😊")
            return {"status": "no_text"}

        # ===============================
        # 3) OPENAI - RESPOSTA DE IA
        # ===============================
        ai_response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Você é um assistente educado e direto. Responda em português.",
                },
                {"role": "user", "content": text},
            ],
        )

        reply = ai_response.choices[0].message.content.strip()

        # ===============================
        # 4) RESPONDE NO WHATSAPP
        # ===============================
        send_message(from_number, reply)

    except Exception as e:
        print("❌ ERRO NO WEBHOOK:", e)

    return {"status": "ok"}


# ===============================
# FUNÇÃO PARA ENVIAR MENSAGENS
# ===============================

def send_message(to: str, message: str):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }

    r = requests.post(url, headers=headers, json=payload)
    print("📤 ENVIANDO:", r.status_code, r.text)


# ===============================
# ROTA DE TESTE
# ===============================
@app.get("/")
async def root():
    return {"status": "running", "message": "Assistente WhatsApp OK!"}
