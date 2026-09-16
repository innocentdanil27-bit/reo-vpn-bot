import os, re, json, threading
import telebot
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8579468852"))
ECOCASH_NUMBER = "0775713879"
ZOL_HOST = os.environ.get("ZOL_HOST", "172.64.145.202")
ECONET_HOST = os.environ.get("ECONET_HOST", "vpsbible.com")
VPN_HOST = os.environ.get("VPN_HOST", "172.64.145.202")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
pending_choice = {}
pending_approval = {}
used_hashes = set()
sales_log = []

def harare_time():
    now = datetime.now(timezone.utc) + timedelta(hours=2)
    return {"day": now.strftime("%A"), "date": now.strftime("%d/%m/%Y %H:%M")}

# === LEGIT FILE CREATOR - ADDED, NOT REPLACING OLD ===
def make_working_config(vpn_name, host, network):
    """Creates EHI, NPV, TXT, HA.json, HC - legit file writer"""
    os.makedirs(f"configs/{network.lower()}", exist_ok=True)
    sni = "zol.co.zw" if network == "ZOL" else "www.econet.co.zw"
    if "vpsbible" in host.lower():
        sni = "vpsbible.com"
    folder = f"configs/{network.lower()}"
    safe_name = vpn_name.replace(" ", "_")

    # EHI
    with open(f"{folder}/{safe_name}.ehi", 'w', encoding='utf-8') as f:
        f.write(f"[ehi]\nhost={host}\nport=443\nsni={sni}\nnetwork={network}\nname={vpn_name}\ncontact={ECOCASH_NUMBER}\n")
    # NPV
    with open(f"{folder}/{safe_name}.npv", 'w', encoding='utf-8') as f:
        json.dump({"host": host, "port": 443, "sni": sni, "network": network, "name": vpn_name}, f, indent=2)
    # TXT
    with open(f"{folder}/{safe_name}.txt", 'w', encoding='utf-8') as f:
        f.write(f"VPN: {vpn_name}\nHost: {host}\nSNI: {sni}\nNetwork: {network}\nContact: {ECOCASH_NUMBER}\n")
    # HA Tunnel JSON
    with open(f"{folder}/{safe_name}_HA.json", 'w', encoding='utf-8') as f:
        json.dump({"host": host, "port": "443", "sni": sni, "network": network}, f, indent=2)
    # HC
    with open(f"{folder}/{safe_name}.hc", 'w', encoding='utf-8') as f:
        f.write(f"host={host}\nport=443\nsni={sni}\nnetwork={network}\n")

    print(f"BOT MADE {vpn_name} with {host} for {network}")
    return f"{folder}/{safe_name}.ehi"

def bot_make_files_itself():
    # AUTO RUN ON START - creates files without you changing anything
    make_working_config("ZOL", ZOL_HOST, "ZOL")
    make_working_config("EHI_ZOL", ZOL_HOST, "ZOL")
    make_working_config("NPV_ZOL", ZOL_HOST, "ZOL")
    make_working_config("HA_Tunnel_Plus_ZOL", ZOL_HOST, "ZOL")
    make_working_config("HTTP_Custom_ZOL", ZOL_HOST, "ZOL")
    make_working_config("ECO", ECONET_HOST, "ECONET")
    make_working_config("EHI_SUNDAY", ECONET_HOST, "ECONET")
    make_working_config("NPV_SUNDAY", ECONET_HOST, "ECONET")
    make_working_config("HA_Tunnel_Plus_SUNDAY", ECONET_HOST, "ECONET")

bot_make_files_itself()

def get_files():
    files = []
    for folder in ["configs/zol", "configs/econet"]:
        if os.path.exists(folder):
            for f in os.listdir(folder):
                files.append(os.path.join(folder, f))
    return files

def find_file(vpn):
    folder = "configs/zol" if "zol" in vpn.lower() else "configs/econet"
    if os.path.exists(folder):
        safe = vpn.replace(" ", "_").lower()
        for f in os.listdir(folder):
            if safe in f.lower() or vpn.split()[0].lower() in f.lower():
                return os.path.join(folder, f)
        if os.listdir(folder):
            return os.path.join(folder, os.listdir(folder)[0])
    return None

def deliver(uid, vpn, txn, amt):
    try:
        fp = find_file(vpn)
        host_used = ZOL_HOST if "zol" in vpn.lower() else ECONET_HOST
        if fp:
            with open(fp, 'rb') as d:
                bot.send_document(uid, d, caption=f"✅ {vpn} WORKING Host {host_used}")
            bot.send_message(uid, f"💚 APPROVED {vpn}\n🏠 {host_used}\n🤖 Bot made file & stays!")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"Deliver error {e}")

def validate_sms(text):
    if not (text.startswith("Cashin") or text.startswith("Transfer")):
        return False, "Not EcoCash", None, None
    m = re.search(r'USD\s*\$?\s*(\d+\.?\d*)', text.upper())
    if not m or float(m.group(1)) < 1.99:
        return False, "Less than $2", None, None
    mc = re.search(r'(?:CI|PP)\d{6}', text.upper())
    return True, "Valid", mc.group(0) if mc else "NOCODE", float(m.group(1))

@app.route('/')
def home():
    return f"LIVE ZOL:{ZOL_HOST} ECONET:{ECONET_HOST} Files:{len(get_files())}"

# === ALL OLD COMMANDS - KEPT LEGIT ===
@bot.message_handler(commands=['start', 'buy', 'zol', 'econet', 'price', 'help', 'pending', 'listfiles', 'files', 'stats', 'sales'])
def old_commands(m):
    day = harare_time()["day"]
    if m.text.startswith('/start'):
        bot.send_message(m.chat.id, f"🚀 REO VPN BOT\n📡 ZOL {ZOL_HOST} DAILY TODAY ✅\n🌐 ECONET {ECONET_HOST} SUNDAY Create TODAY ✅\n📅 {day}\n📁 {len(get_files())} files\n/buy /zol /econet\n💳 {ECOCASH_NUMBER}")
        return
    if m.text.startswith('/price'):
        bot.send_message(m.chat.id, f"💰 $2\n📡 ZOL {ZOL_HOST} Daily\n🌐 ECONET {ECONET_HOST} Sunday Create TODAY\n💳 {ECOCASH_NUMBER}"); return
    if m.text.startswith('/help'):
        bot.send_message(m.chat.id, "1 /zol or /econet\n2 Pick $2\n3 Pay to 0775713879 *153#\n4 Forward SMS\n5 Admin approve\n6 Get file"); return
    if m.text.startswith('/pending'):
        if m.from_user.id!= ADMIN_ID: return
        txt = "\n".join([f"{k}:{v}" for k,v in pending_choice.items()]) or "No pending"
        bot.send_message(m.chat.id, txt); return
    if m.text.startswith('/listfiles') or m.text.startswith('/files'):
        if m.from_user.id!= ADMIN_ID: return
        bot.send_message(m.chat.id, "\n".join(get_files())[:4000]); return
    if m.text.startswith('/stats') or m.text.startswith('/sales'):
        if m.from_user.id!= ADMIN_ID: return
        bot.send_message(m.chat.id, f"Files {len(get_files())} Pending {len(pending_choice)}"); return

    markup = InlineKeyboardMarkup(row_width=1)
    if m.text.startswith('/zol'):
        for v in ["ZOL", "EHI ZOL", "NPV ZOL", "HA Tunnel Plus ZOL", "HTTP Custom ZOL"]:
            markup.add(InlineKeyboardButton(f"📡 {v} $2 {ZOL_HOST}", callback_data=f"buy_{v}"))
        bot.send_message(m.chat.id, f"📡 ZOL DAILY {ZOL_HOST}", reply_markup=markup); return
    if m.text.startswith('/econet'):
        for v in ["EHI SUNDAY", "NPV SUNDAY", "HA Tunnel Plus SUNDAY", "ECO"]:
            markup.add(InlineKeyboardButton(f"🌐 {v} $2 {ECONET_HOST}", callback_data=f"buy_{v}"))
        bot.send_message(m.chat.id, f"🌐 ECONET {ECONET_HOST} Create TODAY", reply_markup=markup); return

    markup.add(InlineKeyboardButton(f"📡 ZOL $2 {ZOL_HOST} DAILY", callback_data="cat_ZOL"))
    markup.add(InlineKeyboardButton(f"🌐 ECONET $2 {ECONET_HOST} SUNDAY", callback_data="cat_ECONET"))
    bot.send_message(m.chat.id, f"CHOOSE $2 💳 {ECOCASH_NUMBER}", reply_markup=markup)

# === ADDED COMMANDS - LEGIT, DOES NOT REMOVE OLD ===
@bot.message_handler(commands=['makefile'])
def makefile_cmd(m):
    if m.from_user.id!= ADMIN_ID: return
    try:
        # Legit parse: /makefile EHI 172.64.145.202 OR /makefile EHI_ZOL 172.64.145.202
        _, name, host = m.text.split(maxsplit=2)
        net = "ZOL" if ("zol" in name.lower() or "172.64" in host) else "ECONET"
        make_working_config(name, host, net)
        bot.send_message(m.chat.id, f"✅ MADE {name} {host} in configs/{net.lower()}/ -.ehi.npv.txt")
    except:
        bot.send_message(m.chat.id, f"Usage: /makefile NAME HOST\nEx: /makefile EHI {ZOL_HOST}")

@bot.message_handler(commands=['makezol'])
def makezol_cmd(m):
    if m.from_user.id!= ADMIN_ID: return
    try:
        _, name, host = m.text.split(maxsplit=2)
        if host == "default": host = ZOL_HOST
        make_working_config(name, host, "ZOL")
        bot.send_message(m.chat.id, f"✅ ZOL DAILY MADE {name} {host}")
    except:
        bot.send_message(m.chat.id, "Usage: /makezol NAME HOST\nEx: /makezol EHI 172.64.145.202")

@bot.message_handler(commands=['makeeconet'])
def makeeconet_cmd(m):
    if m.from_user.id!= ADMIN_ID: return
    try:
        _, name, host = m.text.split(maxsplit=2)
        if host == "default": host = ECONET_HOST
        make_working_config(name, host, "ECONET")
        bot.send_message(m.chat.id, f"✅ ECONET SUNDAY MADE {name} {host} - Create TODAY")
    except:
        bot.send_message(m.chat.id, "Usage: /makeeconet NAME HOST\nEx: /makeeconet EHI vpsbible.com")

@bot.message_handler(commands=['sethost', 'set_zol_host', 'set_econet_host'])
def sethost_cmd(m):
    if m.from_user.id!= ADMIN_ID: return
    try:
        parts = m.text.split()
        if len(parts) == 3:
            net, host = parts[1], parts[2]
            global ZOL_HOST, ECONET_HOST
            if net.lower() == "zol": ZOL_HOST = host
            else: ECONET_HOST = host
            bot_make_files_itself()
            bot.send_message(m.chat.id, f"✅ {net} {host} Remade {len(get_files())} files")
        else:
            bot.send_message(m.chat.id, f"ZOL {ZOL_HOST} ECONET {ECONET_HOST}")
    except:
        bot.send_message(m.chat.id, f"Current ZOL {ZOL_HOST} ECONET {ECONET_HOST}")

@bot.message_handler(commands=['give', 'sendfile'])
def give_cmd(m):
    if m.from_user.id!= ADMIN_ID: return
    try:
        # /give USERID VPN_NAME_WITH_SPACES
        parts = m.text.split(maxsplit=2)
        uid = int(parts[1]); vpn = parts[2]
        deliver(uid, vpn, "GIVE", 2)
        bot.send_message(m.chat.id, f"✅ Sent {vpn} to {uid}")
    except:
        bot.send_message(m.chat.id, "Usage: /give USERID VPN_NAME")

@bot.callback_query_handler(func=lambda c: True)
def callback_handler(c):
    if c.data.startswith("buy_"):
        vpn = c.data.replace("buy_", "")
        pending_choice[c.from_user.id] = vpn
        host_used = ZOL_HOST if "zol" in vpn.lower() else ECONET_HOST
        bot.send_message(c.message.chat.id, f"💰 {vpn} $2 to {ECOCASH_NUMBER}\n🏠 {host_used}\nPay *153# forward SMS")
    elif c.data.startswith("cat_"):
        markup = InlineKeyboardMarkup(row_width=1)
        if "ZOL" in c.data:
            for v in ["ZOL", "EHI ZOL", "NPV ZOL", "HA Tunnel Plus ZOL"]:
                markup.add(InlineKeyboardButton(f"{v} $2 {ZOL_HOST}", callback_data=f"buy_{v}"))
        else:
            for v in ["EHI SUNDAY", "NPV SUNDAY", "ECO"]:
                markup.add(InlineKeyboardButton(f"{v} $2 {ECONET_HOST}", callback_data=f"buy_{v}"))
        bot.send_message(c.message.chat.id, "Choose:", reply_markup=markup)
    elif c.data.startswith("approve_"):
        if c.from_user.id!= ADMIN_ID: return
        uid = int(c.data.split("_")[1])
        vpn = pending_choice.get(uid, "ECO")
        deliver(uid, vpn, "APPROVED", 2)
        if uid in pending_choice: del pending_choice[uid]
        bot.edit_message_text(f"✅ APPROVED {vpn}", c.message.chat.id, c.message.message_id)

@bot.message_handler(content_types=['text'])
def sms_handler(m):
    if m.text.startswith("/"): return
    if m.from_user.id not in pending_choice:
        bot.send_message(m.chat.id, "Use /buy"); return
    valid, reason, txn, amt = validate_sms(m.text)
    if not valid:
        bot.send_message(m.chat.id, f"❌ {reason}"); return
    bot.send_message(m.chat.id, f"✅ Valid ${amt} {txn} Waiting admin")
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ APPROVE", callback_data=f"approve_{m.from_user.id}"))
    bot.send_message(ADMIN_ID, f"🔔 {m.from_user.id} {pending_choice[m.from_user.id]} ${amt} {txn}\n{m.text[:500]}", reply_markup=markup)

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.infinity_polling()
