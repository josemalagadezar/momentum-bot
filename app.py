import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "momentum2024")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")

# In-memory leads storage
leads = []

# User session storage
sessions = {}

def send_message(recipient_id, message_text):
    url = f"https://graph.facebook.com/v18.0/me/messages"
    headers = {"Content-Type": "application/json"}
    params = {"access_token": PAGE_ACCESS_TOKEN}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    requests.post(url, headers=headers, params=params, json=data)

def send_buttons(recipient_id, text, buttons):
    url = f"https://graph.facebook.com/v18.0/me/messages"
    headers = {"Content-Type": "application/json"}
    params = {"access_token": PAGE_ACCESS_TOKEN}
    quick_replies = [{"content_type": "text", "title": b, "payload": b} for b in buttons]
    data = {
        "recipient": {"id": recipient_id},
        "message": {
            "text": text,
            "quick_replies": quick_replies
        }
    }
    requests.post(url, headers=headers, params=params, json=data)

def send_image(recipient_id, image_url):
    url = f"https://graph.facebook.com/v18.0/me/messages"
    headers = {"Content-Type": "application/json"}
    params = {"access_token": PAGE_ACCESS_TOKEN}
    data = {
        "recipient": {"id": recipient_id},
        "message": {
            "attachment": {
                "type": "image",
                "payload": {"url": image_url, "is_reusable": True}
            }
        }
    }
    requests.post(url, headers=headers, params=params, json=data)

def handle_message(sender_id, message_text):
    if sender_id not in sessions:
        sessions[sender_id] = {"step": 0, "data": {}}

    session = sessions[sender_id]
    step = session["step"]
    text = message_text.strip()

    if step == 0:
        send_message(sender_id, "😊 ¡Hola! Bienvenido a Reinvéntate 40+.\n\nSomos una comunidad de personas que buscan una nueva oportunidad para generar ingresos, aprender algo nuevo y rodearse de un ambiente positivo 🙌\n\nCuéntame, ¿cuál de estas opciones te interesa más?")
        send_buttons(sender_id, "Elige una opción:", [
            "💰 Generar ingresos extra",
            "🏠 Trabajar desde casa",
            "🚀 Emprender mi negocio",
            "💪 Mejorar mi bienestar"
        ])
        session["step"] = 1

    elif step == 1:
        session["data"]["interes"] = text
        send_buttons(sender_id, "¡Excelente! ¿Cuál es tu situación laboral actual?", [
            "✅ Trabajo tiempo completo",
            "🔧 Trabajo independiente",
            "❌ No trabajo actualmente",
            "🔎 Estoy buscando opciones"
        ])
        session["step"] = 2

    elif step == 2:
        session["data"]["situacion"] = text
        send_buttons(sender_id, "¿Buscas ingresos adicionales o un cambio más grande?", [
            "💵 Solo ingresos extra",
            "🔄 Un cambio importante",
            "🚀 Quiero emprender",
            "🤔 Estoy evaluando"
        ])
        session["step"] = 3

    elif step == 3:
        session["data"]["objetivo"] = text
        send_buttons(sender_id, "¿Cuánto tiempo podrías dedicarle?", [
            "⏱ 1 a 2 horas al día",
            "🕐 Medio tiempo",
            "🕐 Tiempo completo",
            "📊 Depende de la oportunidad"
        ])
        session["step"] = 4

    elif step == 4:
        session["data"]["tiempo"] = text
        send_message(sender_id, "Perfecto 🙌\n\nPor lo que me comentas, creo que esta oportunidad podría interesarte mucho.\n\nEstamos realizando reuniones presenciales donde explicamos:\n✅ Cómo generar ingresos\n✅ Cómo funciona el sistema\n✅ Cómo empezar desde cero\n✅ Trabajo en equipo y desarrollo personal\n\nLa asistencia es GRATUITA y sin compromiso.")
        send_buttons(sender_id, "¿Te gustaría asistir?", [
            "✅ Sí, quiero asistir",
            "📋 Quiero más información"
        ])
        session["step"] = 5

    elif step == 5:
        session["data"]["asistencia"] = text
        if "asistir" in text.lower() or "sí" in text.lower():
            send_message(sender_id, "¡Excelente decisión! 🎉 Aquí está tu invitación:")
            send_image(sender_id, "https://i.imgur.com/placeholder.jpg")  # Replace with real image URL
            send_message(sender_id, "🎟️ Seminario del Éxito\n📅 Sábado 16 de Mayo, 4:45 PM\n📍 Calle Sacramento 236, Surco Coworking de la Municipalidad\n✅ Entrada libre y sin compromiso")
        else:
            send_message(sender_id, "¡Con gusto te cuento más! Es un seminario gratuito donde conocerás cómo generar ingresos y ser parte de una comunidad que crece 🌟")
        send_message(sender_id, "Para separarte un lugar necesito algunos datos 😊\n\n¿Cuál es tu nombre completo?")
        session["step"] = 6

    elif step == 6:
        session["data"]["nombre"] = text
        send_message(sender_id, f"Mucho gusto, {text} 😊\n\n¿Cuántos años tienes?")
        session["step"] = 7

    elif step == 7:
        session["data"]["edad"] = text
        send_message(sender_id, "¿En qué distrito vives?")
        session["step"] = 8

    elif step == 8:
        session["data"]["distrito"] = text
        send_message(sender_id, "¿Cuál es tu número de WhatsApp? (con código de país, ej: +51 987 654 321)")
        session["step"] = 9

    elif step == 9:
        session["data"]["whatsapp"] = text
        leads.append({**session["data"]})
        nombre = session["data"].get("nombre", "")
        send_message(sender_id, f"✅ ¡Perfecto, {nombre}!\n\nTus datos han sido registrados. Uno de nuestros coordinadores te contactará por WhatsApp para confirmarte el horario.\n\n📍 Oficina en Surco\n🕒 Horarios flexibles\n🎯 Sin costo y sin compromiso\n\n¡Nos vemos pronto! 🚀")
        session["step"] = 10

    elif step == 10:
        send_message(sender_id, "¡Gracias por tu interés! 🌟 Recuerda que este puede ser el inicio de algo increíble. ¡Mucho ánimo! 💪\n\nSi tienes alguna pregunta adicional, escríbenos cuando quieras.")
        session["step"] = 0

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
    return "Momentum Bot activo ✅"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
