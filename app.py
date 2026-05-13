import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "momentum2024")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")

leads = []
sessions = {}

def send_message(recipient_id, message_text):
    url = "https://graph.facebook.com/v18.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    requests.post(url, params=params, json=data)

def send_buttons(recipient_id, text, buttons):
    url = "https://graph.facebook.com/v18.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    quick_replies = [{"content_type": "text", "title": b, "payload": b} for b in buttons]
    data = {
        "recipient": {"id": recipient_id},
        "message": {
            "text": text,
            "quick_replies": quick_replies
        }
    }
    requests.post(url, params=params, json=data)

def handle_message(sender_id, message_text):
    if sender_id not in sessions:
        sessions[sender_id] = {"step": 0, "data": {}}

    session = sessions[sender_id]
    step = session["step"]
    text = message_text.strip()

    # Detect no interest at any step except data collection
    no_interest_keywords = ["no me interesa", "no gracias", "no quiero", "salir", "adios", "adiós", "cancelar"]
    if any(kw in text.lower() for kw in no_interest_keywords) and step not in [3, 4, 5, 6]:
        send_message(sender_id,
            "😊 ¡No te preocupes!\n\nGracias por visitar nuestra página 🙌 Si más adelante deseas recibir información, estaremos felices de ayudarte.\n\n¡Muchos éxitos! 🚀"
        )
        sessions[sender_id] = {"step": 0, "data": {}}
        return

    # STEP 0 — Start / any message triggers welcome
    if step == 0:
        send_buttons(sender_id,
            "😊 ¡Hola! Gracias por escribirnos.\n\nMiles de personas hoy están buscando nuevas formas de generar ingresos, crecer y mejorar su calidad de vida 🙌\n\nCuéntame… ¿Qué fue lo que más te llamó la atención?",
            ["💰 Más ingresos", "🏠 Desde casa", "🚀 Emprender", "💪 Bienestar", "👀 Solo miraba"]
        )
        session["step"] = 1

    # STEP 1 — Interest selection
    elif step == 1:
        if "solo miraba" in text.lower():
            send_message(sender_id,
                "😊 ¡No te preocupes!\n\nGracias por visitar nuestra página 🙌 Si más adelante deseas recibir información, estaremos felices de ayudarte.\n\n¡Muchos éxitos! 🚀"
            )
            sessions[sender_id] = {"step": 0, "data": {}}
            return
        session["data"]["interes"] = text
        send_buttons(sender_id,
            "Excelente 🙌\n\nMuchas personas llegan aquí porque sienten que quieren un cambio, ganar más o simplemente conocer nuevas oportunidades.\n\n¿Cuál de estas opciones se parece más a ti?",
            ["💼 Tengo trabajo", "🔎 Busco algo", "🚀 Quiero crecer", "📈 Aprender más", "⏰ Tengo tiempo"]
        )
        session["step"] = 2

    # STEP 2 — Profile selection
    elif step == 2:
        session["data"]["situacion"] = text
        send_message(sender_id,
            "Perfecto 👍\n\nJustamente estamos compartiendo información con personas que quieren crecer y conocer algo diferente 🙌\n\nEn nuestras reuniones podrás conocer:\n✅ Cómo empiezan las personas desde cero\n✅ Historias reales\n✅ Cómo generar ingresos adicionales\n✅ El sistema de apoyo y capacitación\n\nY lo mejor… no necesitas experiencia previa 😊\n\nPara ayudarte con la información completa y enviarte tu invitación, necesito registrarte 👇\n\n¿Cuál es tu nombre completo?"
        )
        session["step"] = 3

    # STEP 3 — Name
    elif step == 3:
        session["data"]["nombre"] = text
        send_message(sender_id, "1️⃣ ¿Cuántos años tienes?")
        session["step"] = 4

    # STEP 4 — Age
    elif step == 4:
        session["data"]["edad"] = text
        send_message(sender_id, "2️⃣ ¿En qué distrito vives?")
        session["step"] = 5

    # STEP 5 — District
    elif step == 5:
        session["data"]["distrito"] = text
        send_message(sender_id, "3️⃣ ¿Cuál es tu número de WhatsApp? (ej: +51 987 654 321)")
        session["step"] = 6

    # STEP 6 — WhatsApp
    elif step == 6:
        session["data"]["whatsapp"] = text
        nombre = session["data"].get("nombre", "")
        leads.append({**session["data"]})
        send_message(sender_id,
            f"🔥 Excelente, {nombre}.\n\nTu registro quedó realizado correctamente 🙌\n\nEn breve, uno de nuestros asesores se comunicará contigo por WhatsApp para enviarte la invitación oficial y ayudarte con todos los detalles del evento 📍\n\nAhí podrás confirmar:\n✅ Horario\n✅ Ubicación\n✅ Asistencia\n✅ Y cualquier consulta que tengas\n\n📲 Te recomendamos estar atento a tu WhatsApp porque normalmente los cupos se completan rápido 🚀"
        )
        sessions[sender_id] = {"step": 0, "data": {}}

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                sender_id = event["sender"]["id"]
                if "message" in event:
                    msg = event["message"]
                    text = msg.get("text", "")
                    if text:
                        handle_message(sender_id, text)
                elif "postback" in event:
                    handle_message(sender_id, event["postback"]["payload"])
    return jsonify({"status": "ok"})

@app.route("/leads", methods=["GET"])
def get_leads():
    return jsonify(leads)

@app.route("/", methods=["GET"])
def home():
    return "Bot activo ✅"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
