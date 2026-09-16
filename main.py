import os
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

VPN_PRODUCTS = {
    "hatunnel": {"name": "HA Tunnel Plus", "price": "2", "app": "HA Tunnel Plus", "desc": "30 Days Unlimited"},
    "httpcustom": {"name": "HTTP Custom", "price": "2", "app": "HTTP Custom", "desc": "30 Days Secure"},
    "injector": {"name": "HTTP Injector", "price": "2", "app": "HTTP Injector", "desc": "30 Days Premium"},
    "napsternet": {"name": "NapsternetV", "price": "2", "app": "NapsternetV", "desc": "30 Days V2Ray"},
    "stark": {"name": "Stark VPN", "price": "2.5", "app": "Stark VPN", "desc": "30 Days Premium"},
    "family": {"name": "Family Pack", "price": "5", "app": "Any App", "desc": "3 Devices"}
}

bot = telebot.TeleBot(BOT_TOKEN)
print("REO VPN LEGIT BOT STARTED")

def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    for k,v in VPN_PRODUCTS.items():
        kb.add(types.InlineKeyboardButton(f"{v['name']} - ${v['price']}", callback_data=f"buy_{k}"))
    kb.add(types.InlineKeyboardButton("📖 How To Use", callback_data="how"), types.InlineKeyboardButton("💬 Support", callback_data="support"))
    return kb

@bot.message_handler(commands=['start'])
def start(m):
    txt = "🔥 *REO LEGIT VPN STORE* 🔥\n\n✅ Legit • 30 Days • Fast\n\n*SELECT APP:*"
    bot.send_message(m.chat.id, txt, parse_mode="Markdown", reply_markup=main_menu())

@bot.message_handler(commands=['myid'])
def myid(m):
    bot.send_message(m.chat.id, f"ID: {m.from_user.id}")

@bot.message_handler(commands=['send'])
def admin_send(m):
    if m.from_user.id != ADMIN_ID: return
    try:
        _, uid, *rest = m.text.split()
        txt = " ".join(rest)
        bot.send_message(int(uid), f"🎉 *PAYMENT CONFIRMED!*\n\n{txt}", parse_mode="Markdown")
        bot.send_message(m.chat.id, f"✅ Sent to {uid}")
    except:
        bot.send_message(m.chat.id, "Usage: /send USER_ID config")

@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    d=call.data
    if d.startswith("buy_"):
        k=d.replace("buy_","")
        p=VPN_PRODUCTS[k]
        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(f"✅ I Paid ${p['price']}", callback_data=f"paid_{k}"))
        bot.send_message(call.message.chat.id, f"🛒 *{p['name']}* - ${p['price']}\nEcoCash: `{ECOCASH}`\nPay then click I Paid", parse_mode="Markdown", reply_markup=kb)
    elif d.startswith("paid_"):
        k=d.replace("paid_","")
        p=VPN_PRODUCTS[k]
        u=call.from_user
        bot.send_message(ADMIN_ID, f"🔔 NEW ORDER {p['name']} ${p['price']}\nUser: {u.first_name} @{u.username} ID:{u.id}\n/send {u.id} config")
        bot.send_message(call.message.chat.id, "✅ Noted! Admin will send config after verifying EcoCash.")
    elif d=="how":
        bot.send_message(call.message.chat.id, "1.Pay EcoCash 2.Click I Paid 3.Get config")
    elif d=="support":
        bot.send_message(call.message.chat.id, f"Support: EcoCash {ECOCASH}")

bot.infinity_polling()
