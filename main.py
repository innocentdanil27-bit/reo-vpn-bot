import os, re, json, hashlib, threading
import telebot
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8579468852"))
ECOCASH_NUMBER = "0775713879"
ECOCASH_NAME = "Danil"
VPN_HOST = os.environ.get("VPN_HOST", "38.54.91.12")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

pending_choice = {}
pending_approval = {}
used_hashes = set()
sales_log = []
BACKUP = "backup.json"

if os.path.exists(BACKUP):
    try:
        with open(BACKUP,'r') as f:
            d=json.load(f); sales_log=d.get("sales",[]); used_hashes=set(d.get("hashes",[])); pending_approval=d.get("pending",{})
    except: pass

def save():
    with open(BACKUP,'w') as f: json.dump({"sales":sales_log,"hashes":list(used_hashes),"pending":pending_approval}, f)

def harare_time():
    now = datetime.now(timezone.utc) + timedelta(hours=2)
    return {"date_str": now.strftime("%d/%m/%Y"), "time_str": now.strftime("%H:%M:%S"), "day": now.strftime("%A"), "full": now.strftime("%A, %d %B %Y %H:%M:%S CAT")}

# ===== BOT MAKES FILES ITSELF FROM HOST - STAYS WITH FILES =====
def bot_make_files_itself():
    os.makedirs("configs/zol", exist_ok=True)
    os.makedirs("configs/econet", exist_ok=True)
    zol_files = {
        f"configs/zol/ZOL VPN.txt": f"ZOL VPN Host:{VPN_HOST} Contact:{ECOCASH_NUMBER}",
        f"configs/zol/HA Tunnel Plus ZOL.txt": f"HA ZOL Host:{VPN_HOST} SNI:zol.co.zw {ECOCASH_NUMBER}",
        f"configs/zol/HTTP Custom ZOL.txt": f"HTTP ZOL Host:{VPN_HOST} sni=zol.co.zw {ECOCASH_NUMBER}",
        f"configs/zol/STARK ZOL.txt": f"STARK ZOL {VPN_HOST} {ECOCASH_NUMBER}"
    }
    econet_files = {
        f"configs/econet/ECO VPN.txt": f"ECO VPN Host:{VPN_HOST} Contact:{ECOCASH_NUMBER}",
        f"configs/econet/HA Tunnel Plus.txt": f"HA ECONET Host:{VPN_HOST} sni=econet.co.zw {ECOCASH_NUMBER}",
        f"configs/econet/HTTP Custom.txt": f"HTTP ECONET Host:{VPN_HOST} sni=econet.co.zw {ECOCASH_NUMBER}",
        f"configs/econet/EHI.txt": f"EHI {VPN_HOST} {ECOCASH_NUMBER}",
        f"configs/econet/NPV.txt": f"NPV {VPN_HOST} {ECOCASH_NUMBER}",
        f"configs/econet/DARK.txt": f"DARK {VPN_HOST} {ECOCASH_NUMBER}",
        f"configs/econet/TLS.txt": f"TLS {VPN_HOST} {ECOCASH_NUMBER}",
        f"configs/econet/SocksIP.txt": f"SocksIP {VPN_HOST} {ECOCASH_NUMBER}",
        f"configs/econet/NETMOD.txt": f"NETMOD {VPN_HOST} {ECOCASH_NUMBER}"
    }
    all_files = {**zol_files, **econet_files}
    for path, content in all_files.items():
        if not os.path.exists(path):
            with open(path,'w') as f: f.write(content + f"\nMade by bot {harare_time()['full']}")
    print(f"BOT MADE {len(all_files)} FILES FROM HOST {VPN_HOST} & STAYS")

bot_make_files_itself()

def get_files():
    files = []
    for folder in ["configs", "configs/zol", "configs/econet"]:
        if os.path.exists(folder):
            for f in os.listdir(folder):
                p = os.path.join(folder, f)
                if os.path.isfile(p) and not f.startswith('.'):
                    files.append(p.replace("\\","/"))
    return files

def find_file_for_vpn(vpn_type):
    vpn_lower = vpn_type.lower()
    is_zol = "zol" in vpn_lower
    search_order = ["configs/zol", "configs"] if is_zol else ["configs/econet", "configs"]
    for folder in search_order:
        if not os.path.exists(folder): continue
        for f in os.listdir(folder):
            if vpn_lower.split()[0] in f.lower():
                return os.path.join(folder, f).replace("\\","/")
    return None

def deliver(user_id, vpn_type, txn_id, amount, username=""):
    ht = harare_time()
    if not txn_id.startswith("MANUAL"): used_hashes.add(hashlib.sha256(txn_id.encode()).hexdigest()[:20])
    try:
        files = get_files()
        if "FAMILY" in vpn_type.upper():
            bot.send_message(user_id, f"📦 Family {len(files)} files - Bot made from {VPN_HOST} & stays!")
            for fp in files:
                with open(fp,'rb') as doc: bot.send_document(user_id, doc, caption=f"✅ {os.path.basename(fp)} - $2 - {VPN_HOST}")
        else:
            fp = find_file_for_vpn(vpn_type)
            if fp and os.path.exists(fp):
                with open(fp,'rb') as doc:
                    folder = "ZOL" if "zol" in fp.lower() else "ECONET"
                    bot.send_document(user_id, doc, caption=f"✅ {vpn_type} - {folder} - $2 - {txn_id} - Host {VPN_HOST}")
                bot.send_message(user_id, f"💚 APPROVED {vpn_type}\n📁 {folder}\n🏠 Host {VPN_HOST}\n🤖 Bot made & stayed with file!\n💰 ${amount} {txn_id}\n📅 {ht['full']}\n💳 {ECOCASH_NUMBER}\n/help")
            else:
                bot.send_message(user_id, f"❌ File missing - Contact /support")
        pending_choice.pop(user_id,None); pending_approval.pop(str(user_id),None)
        sales_log.append({"user":user_id,"username":username,"vpn":vpn_type,"txn":txn_id,"date":ht['date_str'],"amount":amount}); save()
    except Exception as e:
        bot.send_message(ADMIN_ID, f"Error {e}")

def validate_sms(text):
    if not (text.startswith("Cashin Confirmation:") or text.startswith("Transfer Confirmation:")): return False, "Not EcoCash SMS", None, None
    m = re.search(r'USD\s*\$?\s*(\d+\.?\d*)', text.upper())
    if not m: return False, "No USD", None, None
    amount = float(m.group(1))
    if amount < 1.99: return False, f"${amount} < $2", None, None
    mc = re.search(r'(?:CI|PP)\d{6}\.\d{3,4}', text.upper())
    txn = mc.group(0) if mc else "NOCODE"
    return True, "Valid", txn, amount

def menu_main(chat_id):
    markup=InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("📡 ZOL - $2", callback_data="cat_ZOL"))
    markup.add(InlineKeyboardButton("🌐 ECONET - $2", callback_data="cat_ECONET"))
    markup.add(InlineKeyboardButton("🔥 ALL 12 - $2 BEST", callback_data="cat_ALL"))
    bot.send_message(chat_id, f"🚀 CHOOSE $2\n💳 {ECOCASH_NUMBER}\n🏠 Host {VPN_HOST}\n🤖 Bot made {len(get_files())} files & stays\n📡 /zol ZOL\n🌐 /econet ECONET", reply_markup=markup)

def menu_zol(chat_id):
    markup=InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("📡 ZOL VPN - $2", callback_data="buy_ZOL"))
    markup.add(InlineKeyboardButton("📡 HA Tunnel ZOL - $2", callback_data="buy_HA Tunnel Plus ZOL"))
    markup.add(InlineKeyboardButton("📡 HTTP Custom ZOL - $2", callback_data="buy_HTTP Custom ZOL"))
    markup.add(InlineKeyboardButton("📡 Stark ZOL - $2", callback_data="buy_STARK ZOL"))
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="cat_BACK"))
    bot.send_message(chat_id, f"📡 ZOL - $2 - Bot made from {VPN_HOST}\n💳 {ECOCASH_NUMBER}", reply_markup=markup)

def menu_econet(chat_id):
    markup=InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🌐 ECONET VPN - $2", callback_data="buy_ECO"))
    markup.add(InlineKeyboardButton("🌐 HA Tunnel Plus - $2", callback_data="buy_HA Tunnel Plus"))
    markup.add(InlineKeyboardButton("🌐 HTTP Custom - $2", callback_data="buy_HTTP Custom"))
    markup.add(InlineKeyboardButton("🌐 EHI - $2", callback_data="buy_EHI"))
    markup.add(InlineKeyboardButton("🌐 NPV - $2", callback_data="buy_NPV"))
    markup.add(InlineKeyboardButton("🌐 Dark - $2", callback_data="buy_DARK"))
    markup.add(InlineKeyboardButton("🌐 TLS - $2", callback_data="buy_TLS"))
    markup.add(InlineKeyboardButton("🌐 SocksIP - $2", callback_data="buy_SocksIP"))
    markup.add(InlineKeyboardButton("🌐 NetMod - $2", callback_data="buy_NETMOD"))
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="cat_BACK"))
    bot.send_message(chat_id, f"🌐 ECONET - $2 - Bot made from {VPN_HOST}\n💳 {ECOCASH_NUMBER}", reply_markup=markup)

def menu_all(chat_id):
    markup=InlineKeyboardMarkup(row_width=1)
    for n in ["HA Tunnel Plus","HTTP Custom","EHI","NPV","STARK","DARK","TLS","SocksIP","NETMOD","ZOL","ECO"]:
        markup.add(InlineKeyboardButton(f"{n} - $2", callback_data=f"buy_{n}"))
    markup.add(InlineKeyboardButton("🔥 Family ALL 12 - $2 BEST", callback_data="buy_FAMILY"))
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="cat_BACK"))
    bot.send_message(chat_id, f"🔥 ALL 12 - $2 - Bot made {VPN_HOST}\n💳 {ECOCASH_NUMBER}", reply_markup=markup)

@app.route('/')
def home(): return f"LIVE {harare_time()['full']} Sales {len(sales_log)} Files {len(get_files())} Host {VPN_HOST}"

@bot.message_handler(commands=['start'])
def cmd_start(m):
    bot.send_message(m.chat.id, f"🚀 REO VPN\n💳 {ECOCASH_NUMBER}\n🏠 Host {VPN_HOST}\n🤖 Bot made {len(get_files())} files itself & stays!\n📡 /zol\n🌐 /econet\n🛒 /buy")
    menu_main(m.chat.id)

@bot.message_handler(commands=['buy'])
def cmd_buy(m): menu_main(m.chat.id)
@bot.message_handler(commands=['zol'])
def cmd_zol(m): menu_zol(m.chat.id)
@bot.message_handler(commands=['econet','eco'])
def cmd_econet(m): menu_econet(m.chat.id)
@bot.message_handler(commands=['price'])
def cmd_price(m): bot.send_message(m.chat.id, f"💰 $2 to {ECOCASH_NUMBER} Host {VPN_HOST} Files {len(get_files())} Bot made & stays /buy /zol /econet")
@bot.message_handler(commands=['help'])
def cmd_help(m): bot.send_message(m.chat.id, f"1 /buy /zol /econet\n2 Pick $2\n3 Pay {ECOCASH_NUMBER} *153#\n4 Forward SMS\n5 Danil approves - Bot sends file it made from {VPN_HOST} & stayed with!")
@bot.message_handler(commands=['support'])
def cmd_support(m): bot.send_message(m.chat.id, f"📞 {ECOCASH_NUMBER} {ECOCASH_NAME} Host {VPN_HOST} Files {len(get_files())}")
@bot.message_handler(commands=['about','proof','trial','refer','myvpn','status'])
def cmd_other(m):
    if m.text.startswith('/about'): bot.send_message(m.chat.id, f"⭐ REO 500+ {ECOCASH_NUMBER} Host {VPN_HOST}")
    elif m.text.startswith('/proof'): bot.send_message(m.chat.id, f"✅ Total {len(sales_log)} to {ECOCASH_NUMBER} Files {len(get_files())}")
    elif m.text.startswith('/trial'): bot.send_message(m.chat.id, "🎁 Family $2 test /buy")
    elif m.text.startswith('/refer'): bot.send_message(m.chat.id, f"👥 Refer $0.50 https://t.me/reo_products_bot")
    elif m.text.startswith('/myvpn'):
        my=[s for s in sales_log if s['user']==m.from_user.id]
        if not my: bot.send_message(m.chat.id, "❌ No purchases /buy"); return
        last=my[-1]; deliver(m.from_user.id, last['vpn'], last['txn'], last['amount'], "")
    elif m.text.startswith('/status'):
        if m.from_user.id in pending_choice: bot.send_message(m.chat.id, f"⏳ Waiting {pending_choice[m.from_user.id]}")
        else: bot.send_message(m.chat.id, f"✅ No pending /buy")

# ===== 3 NEW COMMANDS ONLY - AS YOU SAID - BOT MAKES FILE WITH HOST + SELECT NETWORK =====

@bot.message_handler(commands=['makefile'])
def cmd_makefile(m):
    if m.from_user.id!= ADMIN_ID:
        bot.send_message(m.chat.id, "❌ Admin only"); return
    try:
        parts = m.text.split()
        if len(parts) < 3:
            bot.send_message(m.chat.id, f"Usage:\n/makefile VPN_NAME HOST\n\nExample:\n/makefile EHI 38.54.91.12\n/makefile ZOL 38.54.91.12\n\nBot makes file itself from host & stays!\nCurrent: {VPN_HOST}")
            return
        vpn_name = parts[1]; host = parts[2]
        is_zol = "zol" in vpn_name.lower()
        folder = "configs/zol" if is_zol else "configs/econet"
        os.makedirs(folder, exist_ok=True)
        file_path = os.path.join(folder, f"{vpn_name}.txt")
        with open(file_path, 'w') as f:
            f.write(f"{vpn_name}\nHost:{host}\nSNI:{'zol.co.zw' if is_zol else 'econet.co.zw'}\nNetwork:{'ZOL' if is_zol else 'ECONET'}\nMade:{harare_time()['full']}\nContact:{ECOCASH_NUMBER}\nBot made & stays!")
        bot.send_message(m.chat.id, f"✅ Bot made!\n📁 {folder}/{vpn_name}.txt\n🏠 {host}\n🤖 Stays with file!\nCustomer /{'zol' if is_zol else 'econet'} gets it after approval!")
    except Exception as e:
        bot.send_message(m.chat.id, f"❌ {e}\nUsage: /makefile VPN_NAME HOST")

@bot.message_handler(commands=['makezol'])
def cmd_makezol(m):
    if m.from_user.id!= ADMIN_ID:
        bot.send_message(m.chat.id, "❌ Admin only"); return
    try:
        parts = m.text.split()
        if len(parts) < 3:
            bot.send_message(m.chat.id, "Usage:\n/makezol VPN_NAME HOST\nEx:\n/makezol ZOL 38.54.91.12\nMakes file in ZOL folder configs/zol/")
            return
        vpn_name = parts[1]; host = parts[2]
        os.makedirs("configs/zol", exist_ok=True)
        file_path = f"configs/zol/{vpn_name}.txt"
        with open(file_path, 'w') as f:
            f.write(f"ZOL {vpn_name}\nHost:{host}\nSNI:zol.co.zw\nNetwork:ZOL\nMade:{harare_time()['full']}\nContact:{ECOCASH_NUMBER}\nBot made & stays!")
        bot.send_message(m.chat.id, f"✅ ZOL File made!\n📁 configs/zol/{vpn_name}.txt\n🏠 {host}\n📡 ZOL\n🤖 Bot stays!\nCustomer /zol gets it after approval!")
    except Exception as e:
        bot.send_message(m.chat.id, f"❌ {e}")

@bot.message_handler(commands=['makeeconet'])
def cmd_makeeconet(m):
    if m.from_user.id!= ADMIN_ID:
        bot.send_message(m.chat.id, "❌ Admin only"); return
    try:
        parts = m.text.split()
        if len(parts) < 3:
            bot.send_message(m.chat.id, "Usage:\n/makeeconet VPN_NAME HOST\nEx:\n/makeeconet EHI 38.54.91.12\nMakes file in ECONET folder configs/econet/")
            return
        vpn_name = parts[1]; host = parts[2]
        os.makedirs("configs/econet", exist_ok=True)
        file_path = f"configs/econet/{vpn_name}.txt"
        with open(file_path, 'w') as f:
            f.write(f"ECONET {vpn_name}\nHost:{host}\nSNI:econet.co.zw\nNetwork:ECONET\nMade:{harare_time()['full']}\nContact:{ECOCASH_NUMBER}\nBot made & stays!")
        bot.send_message(m.chat.id, f"✅ ECONET File made!\n📁 configs/econet/{vpn_name}.txt\n🏠 {host}\n🌐 ECONET\n🤖 Bot stays!\nCustomer /econet gets it after approval!")
    except Exception as e:
        bot.send_message(m.chat.id, f"❌ {e}")

@bot.message_handler(commands=['pending','give','sethost'])
def admin(m):
    if m.from_user.id!=ADMIN_ID: bot.send_message(m.chat.id, "❌ Admin only"); return
    if m.text.startswith('/pending'):
        msg=f"⏳ Pending {len(pending_approval)} Files {len(get_files())} Host {VPN_HOST}\n"
        for uid,data in pending_approval.items(): msg+=f"{uid} {data['vpn']} {data['txn']}\n/give {uid} {data['vpn']}\n\n"
        bot.send_message(m.chat.id, msg[:4000])
    elif m.text.startswith('/give'):
        try:
            _, uid, *vpn = m.text.split(); uid=int(uid); vpn=" ".join(vpn)
            if "family" in vpn.lower(): vpn="FAMILY"
            deliver(uid, vpn, "MANUAL", 2.00, "admin"); bot.send_message(m.chat.id, f"✅ Gave {vpn} to {uid} from {VPN_HOST}")
        except: bot.send_message(m.chat.id, "Usage: /give USERID VPN")
    elif m.text.startswith('/sethost'):
        try:
            new_host = m.text.split()[1]
            global VPN_HOST; VPN_HOST = new_host
            bot_make_files_itself()
            bot.send_message(m.chat.id, f"✅ Host set {new_host} - Bot remade {len(get_files())} files & stays!")
        except: bot.send_message(m.chat.id, f"Current {VPN_HOST} Use: /sethost 1.2.3.4")

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    if c.data=="cat_ZOL": menu_zol(c.message.chat.id)
    elif c.data=="cat_ECONET": menu_econet(c.message.chat.id)
    elif c.data=="cat_ALL": menu_all(c.message.chat.id)
    elif c.data=="cat_BACK": menu_main(c.message.chat.id)
    elif c.data.startswith("buy_"):
        vpn=c.data.replace("buy_",""); pending_choice[c.from_user.id]=vpn
        bot.send_message(c.message.chat.id, f"💰 Order {vpn} $2 to {ECOCASH_NUMBER}\n🏠 Host {VPN_HOST}\n🤖 Bot made file & stays in {'zol' if 'zol' in vpn.lower() else 'econet'} folder!\nPay $2 *153# forward SMS\nI confirm & bot sends!")
    elif c.data.startswith("approve_"):
        if c.from_user.id!=ADMIN_ID: return
        uid=int(c.data.split("_")[1]); data=pending_approval.get(str(uid))
        if data: deliver(uid, data['vpn'], data['txn'], data['amount'], ""); bot.edit_message_text(f"✅ APPROVED {uid} - Bot sent file {VPN_HOST}", c.message.chat.id, c.message.message_id)
    elif c.data.startswith("reject_"):
        if c.from_user.id!=ADMIN_ID: return
        uid=int(c.data.split("_")[1]); pending_approval.pop(str(uid),None); pending_choice.pop(uid,None); save()
        bot.edit_message_text(f"❌ REJECTED {uid}", c.message.chat.id, c.message.message_id)

@bot.message_handler(content_types=['text'])
def handle_sms(m):
    if m.text.startswith("/"): return
    if m.from_user.id not in pending_choice: bot.send_message(m.chat.id, f"👋 /buy /zol /econet - Bot has {len(get_files())} files {VPN_HOST}"); return
    valid, reason, txn, amount = validate_sms(m.text)
    if not valid: bot.send_message(m.chat.id, f"❌ {reason}"); return
    h=hashlib.sha256(txn.encode()).hexdigest()[:20]
    if h in used_hashes: bot.send_message(m.chat.id, f"🚫 Used {txn}"); return
    pending_approval[str(m.from_user.id)]={"vpn":pending_choice[m.from_user.id],"txn":txn,"amount":amount,"username":m.from_user.username or ""}; save()
    bot.send_message(m.chat.id, f"✅ SMS ${amount} {txn} {pending_choice[m.from_user.id]}\n🏠 {VPN_HOST}\n🤖 Bot made & stays!\n⏳ Waiting Danil confirm!")
    markup=InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("✅ APPROVE SEND FILE", callback_data=f"approve_{m.from_user.id}"), InlineKeyboardButton("❌ REJECT", callback_data=f"reject_{m.from_user.id}"))
    bot.send_message(ADMIN_ID, f"🔔 NEW {m.from_user.id} {pending_choice[m.from_user.id]} ${amount} {txn}\n🏠 {VPN_HOST}\n🤖 Bot file ready - stays!\n{m.text}", reply_markup=markup)

def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
if __name__=="__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.infinity_polling()
