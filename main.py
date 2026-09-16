
import os
from flask import Flask
import threading
app = Flask(__name__)
@app.route('/')
def home(): return "REO VPN BOT IS ALIVE - Danil"
def run_web(): app.run(host="0.0.0.0", port=10000)
threading.Thread(target=run_web, daemon=True).start()

import telebot
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8579468852
ECOCASH = "0775713879"
ECOCASH_NAME = "Danil"

VPN_PRODUCTS = {
    "hatunnel": {"name": "HA Tunnel Plus", "price": "$2", "file": ".hat"},
    "httpcustom": {"name": "HTTP Custom", "price": "$2", "file": ".hc"},
    "injector": {"name": "HTTP Injector", "price": "$2", "file": ".ehi"},
    "napsternetv": {"name": "NapsternetV", "price": "$2", "file": ".nv"},
    "stark": {"name": "Stark VPN", "price": "$2.5", "file": ".sks"},
    "dark": {"name": "Dark Tunnel", "price": "$2", "file": ".dt"},
    "tls": {"name": "TLS Tunnel", "price": "$2", "file": ".tls"},
    "sockstunnel": {"name": "SocksIP Tunnel", "price": "$2", "file": ".sip"},
    "netmod": {"name": "NetMod / SocksHttp", "price": "$2", "file": ".nmd"},
    "family": {"name": "Family Pack (All Apps)", "price": "$5", "file": "All Files"}
}

WELCOME_TEXT = """🔥 REO LEGIT VPN STORE 🔥
🇿🇼 Trusted in Zimbabwe since 2024

✅ 30 Days Unlimited Data
✅ Fast NetOne & ZOL & Econet
✅ Instant Delivery After Payment
✅ Support 24/7 - Quick Reply

⭐ 500+ Happy Customers
💬 Reviews: @ReoVpnReviews
🛡️ Money Back Guarantee

👇 SELECT YOUR VPN APP:"""

def get_product_text(product):
    p = VPN_PRODUCTS[product]
    return f"""🛒 ORDER: {p['name']} - {p['price']}

💰 PRICE: {p['price']} USD (ZiG / EcoCash USD)
📱 EcoCash: {ECOCASH}
👤 Name: {ECOCASH_NAME}

📌 HOW TO PAY:
1. Send {p['price']} to {ECOCASH}
2. Click "I Paid" below
3. Wait 2-5 mins for verification
4. Receive your {p['file']} file instantly!

🛡️ 100% Money Back if not working
⚡ Unlimited for 30 Days
📶 Works Best On: NetOne, ZOL, Econet"""

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(msg):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("HA Tunnel Plus - $2", callback_data="hatunnel"),
        types.InlineKeyboardButton("HTTP Custom - $2", callback_data="httpcustom"),
        types.InlineKeyboardButton("HTTP Injector - $2", callback_data="injector"),
        types.InlineKeyboardButton("NapsternetV - $2", callback_data="napsternetv"),
        types.InlineKeyboardButton("Stark VPN - $2.5", callback_data="stark"),
        types.InlineKeyboardButton("Dark Tunnel - $2", callback_data="dark"),
        types.InlineKeyboardButton("TLS Tunnel - $2", callback_data="tls"),
        types.InlineKeyboardButton("SocksIP Tunnel - $2", callback_data="sockstunnel"),
        types.InlineKeyboardButton("NetMod - $2", callback_data="netmod"),
        types.InlineKeyboardButton("🔥 Family Pack - $5", callback_data="family")
    )
    markup.row(
        types.InlineKeyboardButton("📖 How To Use", callback_data="howto"),
        types.InlineKeyboardButton("💬 Support", callback_data="support")
    )
    bot.send_message(msg.chat.id, WELCOME_TEXT, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: True)
def callback(call):
    if call.data in VPN_PRODUCTS:
        p = VPN_PRODUCTS[call.data]
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"✅ I Paid {p['price']} - Verify Now", callback_data=f"paid_{call.data}"))
        markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="back"))
        bot.send_message(call.message.chat.id, get_product_text(call.data), reply_markup=markup)
    elif call.data.startswith("paid_"):
        prod = call.data.replace("paid_", "")
        bot.send_message(call.message.chat.id, f"✅ PAYMENT REQUEST RECEIVED!\n\nApp: {VPN_PRODUCTS[prod]['name']}\n\n⏳ Admin ({ECOCASH_NAME}) is verifying your EcoCash payment to {ECOCASH}...\nYou will get config in 2-5 mins.")
        bot.send_message(ADMIN_ID, f"🚨 NEW ORDER!\nUser: @{call.from_user.username} ({call.from_user.id})\nApp: {VPN_PRODUCTS[prod]['name']} - {VPN_PRODUCTS[prod]['price']}\nAction: /send {call.from_user.id}")
    elif call.data == "howto":
        bot.send_message(call.message.chat.id, "📚 HOW TO SETUP:\n1. Download app from Play Store\n2. You will receive config file\n3. Open App → Import → Select file\n4. Click START!\n\nWorks on: NetOne, ZOL, Econet")
    elif call.data == "support":
        bot.send_message(call.message.chat.id, f"💬 REO SUPPORT - 24/7\n\n📱 WhatsApp: {ECOCASH}\n👤 Name: {ECOCASH_NAME}\n⏰ Reply: 2-10 Mins\n🛡️ Guarantee: Works or Refund!")
    elif call.data == "back":
        start(call.message)

bot.infinity_polling()
