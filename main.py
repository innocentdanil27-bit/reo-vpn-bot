import telebotimport os
from flask import Flask
import threading
app = Flask(__name__)
@app.route('/')
def home(): return "REO VPN BOT IS ALIVE!"
def run_web(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
threading.Thread(target=run_web, daemon=True).start()

import telebot
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8579468852
ECOCASH = "0775713879"

# --- LEGIT VPN PRODUCTS YOU SELL ---
VPN_PRODUCTS = {
    "hatunnel": {
        "name": "HA Tunnel Plus",
        "price": "2",
        "app": "HA Tunnel Plus",
        "desc": "30 Days • Unlimited • Fast • 1 Device"
    },
    "httpcustom": {
        "name": "HTTP Custom",
        "price": "2",
        "app": "HTTP Custom",
        "desc": "30 Days • Secure SSH • All Networks"
    },
    "injector": {
        "name": "HTTP Injector",
        "price": "2",
        "app": "HTTP Injector",
        "desc": "30 Days • Premium Servers"
    },
    "napsternet": {
        "name": "NapsternetV",
        "price": "2",
        "app": "NapsternetV",
        "desc": "30 Days • V2Ray • Fast"
    },
    "stark": {
        "name": "Stark VPN Reloaded",
        "price": "2.5",
        "app": "Stark VPN",
        "desc": "30 Days • Premium"
    },
    "family": {
        "name": "Family Pack - 3 Devices",
        "price": "5",
        "app": "Any App",
        "desc": "30 Days • 3 Devices • Any VPN App"
    }
}

bot = telebot.TeleBot(BOT_TOKEN)
print("REO VPN LEGIT BOT STARTED")

def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    for key, v in VPN_PRODUCTS.items():
        kb.add(types.InlineKeyboardButton(f"{v['name']} - ${v['price']}", callback_data=f"buy_{key}"))
    kb.add(
        types.InlineKeyboardButton("📖 How To Use", callback_data="how"),
        types.InlineKeyboardButton("💰 Price List", callback_data="pricelist"),
        types.InlineKeyboardButton("💬 Support", callback_data="support")
    )
    return kb

@bot.message_handler(commands=['start'])
def start(m):
    txt = (
        "🔥 *REO LEGIT VPN STORE* 🔥\n\n"
        "✅ 100% Legit VPN Service\n"
        "✅ 30 Days Unlimited\n"
        "✅ Fast & Secure Servers\n"
        "✅ Support All Apps\n\n"
        "*SELECT YOUR VPN APP:*"
    )
    bot.send_message(m.chat.id, txt, parse_mode="Markdown", reply_markup=main_menu())

@bot.message_handler(commands=['help', 'price', 'products', 'buy'])
def help_cmd(m):
    txt = "💰 *PACKAGES:*\n\n"
    for v in VPN_PRODUCTS.values():
        txt += f"• {v['name']} ({v['app']}) - ${v['price']}\n {v['desc']}\n\n"
    txt += f"Pay EcoCash: `{ECOCASH}`\nThen click Buy!"
    bot.send_message(m.chat.id, txt, parse_mode="Markdown", reply_markup=main_menu())

@bot.message_handler(commands=['myid'])
def myid(m):
    bot.send_message(m.chat.id, f"Your ID: `{m.from_user.id}`")

# ADMIN COMMAND: /send USER_ID config text or file link
@bot.message_handler(commands=['send'])
def admin_send(m):
    if m.from_user.id!= ADMIN_ID: return
    try:
        _, uid, *msg = m.text.split()
        text = " ".join(msg) if msg else "Here is your VPN config!"
        bot.send_message(int(uid), f"🎉 *PAYMENT CONFIRMED!*\n\n{text}\n\nThanks for choosing REO VPN!", parse_mode="Markdown")
        bot.send_message(m.chat.id, f"✅ Sent to {uid}")
    except:
        bot.send_message(m.chat.id, "Usage: /send USER_ID Your config details or link")

@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    d = call.data
    if d.startswith("buy_"):
        key = d.replace("buy_", "")
        p = VPN_PRODUCTS.get(key)
        if not p: return
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton(f"✅ I Paid ${p['price']}", callback_data=f"paid_{key}"),
            types.InlineKeyboardButton("⬅️ Back", callback_data="back")
        )
        bot.send_message(call.message.chat.id,
            f"🛒 *{p['name']}*\n\nApp: *{p['app']}*\nPrice: *${p['price']}*\n{p['desc']}\n\n"
            f"*PAYMENT:*\nEcoCash: `{ECOCASH}`\n\n"
            f"After paying click *I Paid* 👇",
            parse_mode="Markdown", reply_markup=kb)
    elif d.startswith("paid_"):
        key = d.replace("paid_", "")
        p = VPN_PRODUCTS[key]
        u = call.from_user
        # Notify admin
        bot.send_message(ADMIN_ID,
            f"🔔 *NEW ORDER*\n\nVPN: {p['name']
from telebot import types

BOT_TOKEN = "8931751932:AAHrky1vnNFVztV-kYipcRFpOo9kO7aABJo"
ADMIN_ID = 8579468852

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(m):
    text1 = "What you get:\n• 30 Days Unlimited\n• All apps supported\n• Instant delivery after payment\n• 24/7 Support - 0775713879\n\n👇 Tap to start:"
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🛒 BUY VPN - $2", callback_data="buy"),
        types.InlineKeyboardButton("📖 How to Install VPN", callback_data="how"),
        types.InlineKeyboardButton("📞 Support", callback_data="sup")
    )
    bot.send_message(m.chat.id, text1, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    d = call.data
    if d == "buy":
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("NapsternetV", callback_data="vpn1"),
            types.InlineKeyboardButton("HTTP Custom", callback_data="vpn2"),
            types.InlineKeyboardButton("Dark Tunnel", callback_data="vpn3"),
            types.InlineKeyboardButton("TLS Tunnel", callback_data="vpn4"),
            types.InlineKeyboardButton("eHi Tunnel", callback_data="vpn5"),
            types.InlineKeyboardButton("Stark VPN", callback_data="vpn6"),
            types.InlineKeyboardButton("HA Tunnel", callback_data="vpn7")
        )
        bot.send_message(call.message.chat.id, "Choose VPN - $2:", reply_markup=kb)
    elif d == "how":
        text2 = "📖 HOW TO USE VPN - 3 Steps\n\n1️⃣ Buy: Click Buy VPN → Choose → Pay $2 to 0775713879 → Forward EcoCash SMS\n\n2️⃣ Install App:\n• NapsternetV - from PlayStore\n• HTTP Custom - from PlayStore\n• Dark Tunnel - from PlayStore\n\n3️⃣ Import File:\n   Open App → Tap + → Import Config → Select file I send you → TAP 

