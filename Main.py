import os, threading, random
import telebot
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8579468852"))

# YOUR REAL HOSTS - REMEMBERED
ZOL_HOST = "172.64.145.202" # ZOL host
ECONET_HOST = "vpsbible.com" # ECONET host

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

user_host = {}
user_type = {}

def cat_time():
    return (datetime.now(timezone.utc)+timedelta(hours=2)).strftime("%d/%m/%Y %H:%M CAT")

@app.route('/')
def home(): return f"LIVE ZOL:{ZOL_HOST} ECONET:{ECONET_HOST} {cat_time()}"

@bot.message_handler(commands=['start'])
def h_start(m):
    mk=InlineKeyboardMarkup(row_width=2)
    mk.add(InlineKeyboardButton(f"📡 ZOL {ZOL_HOST}", callback_data="gen_ZOL"))
    mk.add(InlineKeyboardButton(f"🌐 ECONET {ECONET_HOST}", callback_data="gen_ECONET"))
    mk.add(InlineKeyboardButton("⚙️ Create Host", callback_data="create_FAMILY"))
    bot.send_message(m.chat.id, f"🚀 REO SERVER GEN\n{cat_time()}\n\nZOL Host: {ZOL_HOST}\nECONET Host: {ECONET_HOST}\n\n/gen /create /host /status", reply_markup=mk)

@bot.message_handler(commands=['gen','server'])
def h_gen(m):
    mk=InlineKeyboardMarkup(row_width=1)
    mk.add(InlineKeyboardButton(f"📡 ZOL Host {ZOL_HOST}", callback_data="gen_ZOL"))
    mk.add(InlineKeyboardButton(f"🌐 ECONET Host {ECONET_HOST}", callback_data="gen_ECONET"))
    mk.add(InlineKeyboardButton("🔥 Family BOTH Hosts", callback_data="gen_FAMILY"))
    bot.send_message(m.chat.id, f"⚙️ SELECT:\nZOL = {ZOL_HOST}\nECONET = {ECONET_HOST}", reply_markup=mk)

@bot.message_handler(commands=['create','create_host'])
def h_create(m):
    mk=InlineKeyboardMarkup(row_width=1)
    mk.add(InlineKeyboardButton(f"Create ZOL Host {ZOL_HOST}", callback_data="create_ZOL"))
    mk.add(InlineKeyboardButton(f"Create ECONET Host {ECONET_HOST}", callback_data="create_ECONET"))
    mk.add(InlineKeyboardButton("Create Random Host", callback_data="create_RANDOM"))
    bot.send_message(m.chat.id, f"⚙️ CREATE HOST\nZOL: {ZOL_HOST}\nECONET: {ECONET_HOST}\nPick:", reply_markup=mk)

@bot.message_handler(commands=['host'])
def h_host(m):
    try:
        host = m.text.split()[1]
        user_host[m.from_user.id] = host
        bot.send_message(m.chat.id, f"✅ Custom host set: {host}\n/gen to generate")
    except:
        bot.send_message(m.chat.id, f"YOUR PRESET HOSTS:\nZOL: {ZOL_HOST}\nECONET: {ECONET_HOST}\n\nUsage:\n/host {ZOL_HOST}\n/host {ECONET_HOST}\n/host 104.21.1.1\n/create to use preset")

@bot.message_handler(commands=['status'])
def h_status(m):
    h=user_host.get(m.from_user.id, f"Default ZOL:{ZOL_HOST} ECONET:{ECONET_HOST}")
    bot.send_message(m.chat.id, f"📊 STATUS {cat_time()}\nZOL Host: {ZOL_HOST}\nECONET Host: {ECONET_HOST}\nYour current: {h}")

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    vpn_type = c.data.replace("gen_","").replace("create_","")

    # CHOOSE HOST BASED ON TYPE
    if "ZOL" in vpn_type.upper():
        host = ZOL_HOST
    elif "ECONET" in vpn_type.upper():
        host = ECONET_HOST
    else:
        host = f"{ZOL_HOST} + {ECONET_HOST}" if vpn_type=="FAMILY" else ECONET_HOST

    if c.data.startswith("create_"):
        if "RANDOM" in vpn_type:
            host = f"104.21.{random.randint(1,255)}"
        user_host[c.from_user.id] = host
        bot.send_message(c.message.chat.id, f"✅ HOST CREATED\n📦 {vpn_type}\n🌐 {host}\n{cat_time()}\n\n/gen to generate file with this host")
        return

    # GEN
    if c.data.startswith("gen_"):
        user_host[c.from_user.id] = host
        user_type[c.from_user.id] = vpn_type
        # Generate config file
        file_name = f"{vpn_type}_{host.replace('.','_')}.txt"
        content = f"""REO VPN SERVER
Type: {vpn_type}
ZOL Host: {ZOL_HOST}
ECONET Host: {ECONET_HOST}
Selected Host: {host}
Port: 443
SNI: {host}
Payload: GET / HTTP/1.1
Host: {host}

Generated: {cat_time()}
For HA Tunnel: Use {host} as SNI/Host
For EHI: SSH Host {host} Port 443
For NPV: Host {host}
"""
        with open(file_name,"w") as f: f.write(content)
        bot.send_message(c.message.chat.id, f"✅ SERVER GENERATED\n📦 {vpn_type}\n🌐 Host: {host}\nZOL: {ZOL_HOST}\nECONET: {ECONET_HOST}\n📅 {cat_time()}")
        with open(file_name,"rb") as f:
            bot.send_document(c.message.chat.id, f, caption=f"{vpn_type} {host}")

@bot.message_handler(content_types=['text'])
def txt_h(m):
    if m.text.startswith("/"): return
    if "." in m.text and len(m.text)<60 and " " not in m.text:
        user_host[m.from_user.id]=m.text.strip()
        bot.send_message(m.chat.id, f"✅ Custom host saved: {m.text}\n/gen to generate")

def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
if __name__=="__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.infinity_polling()
