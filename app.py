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

    # Detect "not interested" at any point
    no_interest_keywords = ["no me interesa", "no gracias", "no quiero", "solo estaba viendo", "adiós", "adios", "no", "salir"]
    if any(kw in text.lower() for kw in no_interest_keywords) and step not in [6, 7, 8, 9]:
        send_message(sender_id, "😊 ¡No te preocupes! Gracias por visitarnos 🙌 Si en algún momento deseas más información, aquí estaremos. ¡Éxitos! 🚀")
        sessions[sender_id] = {"step": 0, "data": {}}
        return

    if step == 0:
        send_buttons(sender_id,
            "😊 ¡Hola! Gracias por escribirnos.\n\nVimos tu interés en la información que estamos compartiendo y queremos conocerte un poco más 🙌\n\nCuéntame… ¿Qué fue lo que más llamó tu atención?",
            [
                "💰 Generar ingresos",
                "🏠 Trabajar desde casa",
                "🚀 Emprender",
                "💪 Bienestar y desarrollo",
                "🤔 Quiero información",
                "❌ Solo estaba viendo"
            ]
        )
        session["step"] = 1

    elif step == 1:
        if "solo estaba viendo" in text.lower():
            send_message(sender_id, "😊 ¡No te preocupes! Gracias por visitarnos 🙌 Si en algún momento deseas más información, aquí estaremos. ¡Éxitos! 🚀")
            sessions[sender_id] = {"step": 0, "data": {}}
            return
        session["data"]["interes"] = text
        send_buttons(sender_id,
            "Excelente 🙌\n\nMuchas personas llegan aquí buscando un cambio, ingresos extra o simplemente una nueva oportunidad.\n\n¿Cuál de estas opciones se parece más a tu situación actual?",
            [
                "💼 Tengo trabajo pero quiero mejorar",
                "🔎 Estoy buscando una oportunidad",
                "🏠 Tengo tiempo disponible",
                "🚀 Quiero crecer económicamente",
                "📈 Quiero aprender algo nuevo"
            ]
        )
        session["step"] = 2

    elif step == 2:
        session["data"]["situacion"] = text
        send_message(sender_id,
            "Perfecto 👍\n\nPor lo que me comentas, creemos que esta información puede aportarte muchísimo valor.\n\nEstamos seleccionando personas para participar en nuestras reuniones informativas y capacitaciones presenciales 🙌\n\nAhí podrás conocer:\n✅ Cómo funciona el sistema\n✅ Cómo empiezan las personas desde cero\n✅ Historias reales de resultados\n✅ Cómo generar ingresos adicionales\n\nPara enviarte la información completa y ayudarte con tu acceso, necesito registrarte 😊\n\n¿Cuál es tu nombre completo?"
        )
        session["step"] = 3

    elif step == 3:
        session["data"]["nombre"] = text
        send_message(sender_id, "¿Cuántos años tienes?")
        session["step"] = 4

    elif step == 4:
        session["data"]["edad"] = text
        send_message(sender_id, "¿En qué distrito vives?")
        session["step"] = 5

    elif step == 5:
        session["data"]["distrito"] = text
        send_message(sender_id, "¿Cuál es tu número de WhatsApp? (con código de país, ej: +51 987 654 321)")
        session["step"] = 6

    elif step == 6:
        session["data"]["whatsapp"] = text
        nombre = session["data"].get("nombre", "")
        leads.append({**session["data"]})
        send_message(sender_id,
            f"✅ Perfecto, {nombre}. Ya registramos tus datos 🙌\n\nEn breve, un asesor de nuestro equipo se pondrá en contacto contigo por WhatsApp para enviarte la invitación oficial con todos los detalles del evento 📍\n\nAhí también podrá ayudarte con:\n✅ Ubicación exacta\n✅ Horario\n✅ Confirmación de asistencia\n✅ Cualquier duda que tengas\n\nTe recomendamos estar atento a tu WhatsApp porque los cupos suelen llenarse rápido 🚀"
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
