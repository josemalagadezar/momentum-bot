import os
import requests
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "momentum2024")

# Token por página
PAGE_TOKENS = {
    "1071599096044735": os.environ.get("PAGE_ACCESS_TOKEN", ""),           # Momentum - Manuel
    "1147098975149726": os.environ.get("PAGE_ACCESS_TOKEN_REINVENTATE", ""), # Reinvéntate - Roberto
    "1161939380326544": os.environ.get("PAGE_ACCESS_TOKEN_IMPERIA", ""),     # Imperia - Rosa
}

# Nombre por página
PAGE_NAMES = {
    "1071599096044735": "Momentum Expansión",
    "1147098975149726": "Reinvéntate 40+",
    "1161939380326544": "Imperia Network",
}

SHEETS_URL = "https://script.google.com/macros/s/AKfycbxXQhVFrFBEx3vhcaGu2u-oCbG0xFmsmWmQAE96F1H3NRIamCob5ny4nV27fy7ieDDdZg/exec"

sessions = {}

def send_message(recipient_id, message_text, page_id):
    token = PAGE_TOKENS.get(str(page_id), "")
    url = "https://graph.facebook.com/v18.0/me/messages"
    params = {"access_token": token}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    requests.post(url, params=params, json=data)

def send_buttons(recipient_id, text, buttons, page_id):
    token = PAGE_TOKENS.get(str(page_id), "")
    url = "https://graph.facebook.com/v18.0/me/messages"
    params = {"access_token": token}
    quick_replies = [{"content_type": "text", "title": b, "payload": b} for b in buttons]
    data = {
        "recipient": {"id": recipient_id},
        "message": {
            "text": text,
            "quick_replies": quick_replies
        }
    }
    requests.post(url, params=params, json=data)

def save_to_sheets(lead_data):
    try:
        requests.post(SHEETS_URL, json=lead_data, timeout=10)
    except Exception as e:
        print(f"Error saving to sheets: {e}")

def handle_message(sender_id, message_text, page_id):
    if sender_id not in sessions:
        sessions[sender_id] = {"step": 0, "data": {}, "page_id": page_id}

    session = sessions[sender_id]
    step = session["step"]
    text = message_text.strip()
    pid = str(page_id)

    # Detect no interest
    no_interest_keywords = ["no me interesa", "no gracias", "no quiero", "salir", "adios", "adiós", "cancelar"]
    if any(kw in text.lower() for kw in no_interest_keywords) and step not in [3, 4, 5, 6]:
        send_message(sender_id,
            "😊 ¡No te preocupes!\n\nGracias por visitar nuestra página 🙌 Si más adelante deseas recibir información, estaremos felices de ayudarte.\n\n¡Muchos éxitos! 🚀",
            pid
        )
        sessions[sender_id] = {"step": 0, "data": {}, "page_id": pid}
        return

    if step == 0:
        send_buttons(sender_id,
            "😊 ¡Hola! Gracias por escribirnos.\n\nMiles de personas hoy están buscando nuevas formas de generar ingresos, crecer y mejorar su calidad de vida 🙌\n\nCuéntame… ¿Qué fue lo que más te llamó la atención?",
            ["💰 Más ingresos", "🏠 Desde casa", "🚀 Emprender", "💪 Bienestar", "👀 Solo miraba"],
            pid
        )
        session["step"] = 1

    elif step == 1:
        if "solo miraba" in text.lower():
            send_message(sender_id,
                "😊 ¡No te preocupes!\n\nGracias por visitar nuestra página 🙌 Si más adelante deseas recibir información, estaremos felices de ayudarte.\n\n¡Muchos éxitos! 🚀",
                pid
            )
            sessions[sender_id] = {"step": 0, "data": {}, "page_id": pid}
            return
        session["data"]["interes"] = text
        send_buttons(sender_id,
            "Excelente 🙌\n\nMuchas personas llegan aquí porque sienten que quieren un cambio, ganar más o simplemente conocer nuevas oportunidades.\n\n¿Cuál de estas opciones se parece más a ti?",
            ["💼 Tengo trabajo", "🔎 Busco algo", "🚀 Quiero crecer", "📈 Aprender más", "⏰ Tengo tiempo"],
            pid
        )
        session["step"] = 2

    elif step == 2:
        session["data"]["situacion"] = text
        send_message(sender_id,
            "Perfecto 👍\n\nJustamente estamos compartiendo información con personas que quieren crecer y conocer algo diferente 🙌\n\nEn nuestras reuniones podrás conocer:\n✅ Cómo empiezan las personas desde cero\n✅ Historias reales\n✅ Cómo generar ingresos adicionales\n✅ El sistema de apoyo y capacitación\n\nY lo mejor… no necesitas experiencia previa 😊\n\nPara ayudarte con la información completa y enviarte tu invitación, necesito registrarte 👇\n\n¿Cuál es tu nombre completo?",
            pid
        )
        session["step"] = 3

    elif step == 3:
        session["data"]["nombre"] = text
        send_message(sender_id, "1️⃣ ¿Cuántos años tienes?", pid)
        session["step"] = 4

    elif step == 4:
        session["data"]["edad"] = text
        send_message(sender_id, "2️⃣ ¿En qué distrito vives?", pid)
        session["step"] = 5

    elif step == 5:
        session["data"]["distrito"] = text
        send_message(sender_id, "3️⃣ ¿Cuál es tu número de WhatsApp? (ej: +51 987 654 321)", pid)
        session["step"] = 6

    elif step == 6:
        session["data"]["whatsapp"] = text
        nombre = session["data"].get("nombre", "")
        page_name = PAGE_NAMES.get(pid, "Página")

        save_to_sheets({
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "nombre": session["data"].get("nombre", ""),
            "edad": session["data"].get("edad", ""),
            "distrito": session["data"].get("distrito", ""),
            "whatsapp": session["data"].get("whatsapp", ""),
            "interes": session["data"].get("interes", ""),
            "situacion": session["data"].get("situacion", ""),
            "pagina": page_name
        })

        send_message(sender_id,
            f"🔥 Excelente, {nombre}.\n\nTu registro quedó realizado correctamente 🙌\n\nEn breve, uno de nuestros asesores se comunicará contigo por WhatsApp para enviarte la invitación oficial y ayudarte con todos los detalles del evento 📍\n\nAhí podrás confirmar:\n✅ Horario\n✅ Ubicación\n✅ Asistencia\n✅ Y cualquier consulta que tengas\n\n📲 Te recomendamos estar atento a tu WhatsApp porque normalmente los cupos se completan rápido 🚀",
            pid
        )
        sessions[sender_id] = {"step": 0, "data": {}, "page_id": pid}

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
            page_id = entry.get("id", "")
            for event in entry.get("messaging", []):
                sender_id = event["sender"]["id"]
                if "message" in event:
                    msg = event["message"]
                    text = msg.get("text", "")
                    if text:
                        handle_message(sender_id, text, page_id)
                elif "postback" in event:
                    handle_message(sender_id, event["postback"]["payload"], page_id)
    return jsonify({"status": "ok"})

@app.route("/", methods=["GET"])
def home():
    return "Bot activo ✅"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
