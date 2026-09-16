import os
from flask import Flask
import threading
app = Flask(__name__)
@app.route('/')
def home(): return "REO VPN BOT - Danil ALL $2 - AUTO SEND"
def run_web(): app.run(host="0.0.0.0", port=10000)
threading.Thread(target=run_web, daemon=True).start()

import telebot
from telebot import types
import glob

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8579468852
ECOCASH = "0775713879"
ECOCASH_NAME = "Danil"
PRICE = "$2"

VPN_PRODUCTS = {
    "hatunnel": {"name": "HA Tunnel Plus", "price": "$2"},
    "httpcustom": {"name": "HTTP Custom", "price": "$2"},
    "injector": {"name": "HTTP Injector", "price": "$2"},
    "napsternetv": {"name": "NapsternetV", "price": "$2"},
    "stark": {"name": "Stark VPN", "price": "$2"},
    "dark": {"name": "Dark Tunnel", "price": "$2"},
    "tls": {"name": "TLS Tunnel", "price": "$2"},
    "sockstunnel": {"name": "SocksIP Tunnel", "price": "$2"},
    "netmod": {"name": "NetMod / SocksHttp", "price": "$2"},
    "family": {"name": "Family Pack (All Apps)", "price": "$2"}
}

WELCOME_TEXT = """🔥 REO LEGIT VPN STORE 🔥
🇿🇼 Owner: Danil - Trusted 2024
💰 ALL VPNs $2 ONLY!

✅ 30 Days Unlimited
✅ Fast NetOne & ZOL & Econet
✅ INSTANT AUTO DELIVERY
✅ Support 24/7 - Danil

⭐ 500+ Happy Customers
🛡️ Money Back by Danil

👇 ALL $2 - PICK YOUR APP:"""

def get_product_text(product):
    p = VPN_PRODUCTS[product]
    return f"""🛒 ORDER: {p['name']} - $2

💰 PRICE: $2 USD ONLY
📱 EcoCash: {ECOCASH}
👤 Name: {ECOCASH_NAME}

📌 PAY $2 TO DANIL:
1. Send $2 to {ECOCASH}
2. Click I PAID $2
3. Get File INSTANTLY!

🛡️ Danil Guarantee
⚡ 30 Days Unlimited
📶 NetOne, ZOL, Econet"""

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(msg):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for key, p in VPN_PRODUCTS.items():
        markup.add(types.InlineKeyboardButton(f"{p['name']} - $2", callback_data=key))
    markup.row(
        types.InlineKeyboardButton("📖 How To Use", callback_data="howto"),
        types.InlineKeyboardButton("💬 Support Danil", callback_data="support")
    )
    bot.send_message(msg.chat.id, WELCOME_TEXT, reply_markup=markup)

@bot.callback_query_handler(func=lambda c: True)
def callback(call):
    if call.data in VPN_PRODUCTS:
        p = VPN_PRODUCTS[call.data]
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"✅ I Paid $2 to Danil", callback_data=f"paid_{call.data}"))
        markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="back"))
        bot.send_message(call.message.chat.id, get_product_text(call.data), reply_markup=markup)

    elif call.data.startswith("paid_"):
        prod_key = call.data.replace("paid_", "")
        p = VPN_PRODUCTS[prod_key]
        bot.send_message(call.message.chat.id, f"✅ $2 Payment to Danil OK!\n\n📦 Sending {p['name']}...\n⏳ Wait...")

        files = glob.glob(f"configs/*{prod_key}*") + glob.glob("configs/*.*")
        sent = 0
        for f in files:
            if os.path.isfile(f) and "placeholder" not in f.lower():
                try:
                    with open(f, 'rb') as doc:
                        bot.send_document(call.message.chat.id, doc, caption=f"🔥 {p['name']} - $2 Danil\n📶 NetOne | ZOL | Econet | 30 Days")
                        sent += 1
                    if prod_key!= "family": break
                except: pass
            if sent >= 5: break

        if sent == 0:
            bot.send_message(call.message.chat.id, f"⚠️ Config not uploaded.\nDanil will send {p['name']} manually in 2-5 mins.\nID: {call.from_user.id}")
        else:
            bot.send_message(call.message.chat.id, f"🎉 Done! $2 - Danil\n💬 Help? {ECOCASH}")

    elif call.data == "howto":
        bot.send_message(call.message.chat.id, "📚 BY DANIL - SETUP:\n1. Install app\n2. Import file we sent\n3. START\n\nNetOne, ZOL, Econet - $2")
    elif call.data == "support":
        bot.send_message(call.message.chat.id, f"💬 DANIL SUPPORT\n📱 {ECOCASH}\n👤 Danil\n💰 ALL $2\n⏰ 2-10 Mins reply")
    elif call.data == "back":
        start(call.message)

bot.infinity_polling()
