import os, re, json, hashlib, threading
import telebot
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8579468852"))
ECOCASH_NUMBER = "0775713879"
ECOCASH_NAME = "Danil"

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

# --- SEPARATE ZOL vs ECONET FOLDERS ---
VPN_FILE_MAP = {
    "ZOL": ["zol vpn", "zol"], "HA Tunnel Plus ZOL": ["ha zol"], "HTTP Custom ZOL": ["http zol", "hc zol"], "STARK ZOL": ["stark zol"],
    "ECO": ["eco vpn", "econet"], "HA Tunnel Plus": ["ha tunnel plus", "hat"], "HTTP Custom": ["http custom", "hc"], "EHI": ["ehi"], "NPV": ["npv"], "STARK": ["stark"], "DARK": ["dark"], "TLS": ["tls"], "SocksIP": ["socksip"], "NETMOD": ["netmod"], "FAMILY": ["family"]
}

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
            if vpn_lower.split()[0] in f.lower() or any(k in f.lower() for k in VPN_FILE_MAP.get(vpn_type, [vpn_lower])):
                if is_zol and "zol" in f.lower(): return os.path.join(folder, f).replace("\\","/")
                if not is_zol and "zol" not in f.lower(): return os.path.join(folder, f).replace("\\","/")
                if "family" in vpn_lower: return os.path.join(folder, f).replace("\\","/")
    # fallback
    for fp in get_files():
        if vpn_lower.split()[0] in os.path.basename(fp).lower():
            if is_zol and "zol" in fp.lower(): return fp
            if not is_zol: return fp
    return None

def deliver(user_id, vpn_type, txn_id, amount, username=""):
    ht = harare_time()
    if not txn_id.startswith("MANUAL"): used_hashes.add(hashlib.sha256(txn_id.encode()).hexdigest()[:20])
    try:
        files = get_files()
        if not files:
            bot.send_message(user_id, f"❌ No configs - Contact /support {ECOCASH_NUMBER}")
            return
        if "FAMILY" in vpn_type.upper():
            bot.send_message(user_id, f"📦 Family Pack - Sending {len(files)} files ZOL+ECONET...")
            for fp in files:
                with open(fp,'rb') as doc: bot.send_document(user_id, doc, caption=f"✅ {os.path.basename(fp)} - $2")
        else:
            fp = find_file_for_vpn(vpn_type)
            if fp and os.path.exists(fp):
                with open(fp,'rb') as doc:
                    folder = "ZOL" if "zol" in fp.lower() else "ECONET"
                    bot.send_document(user_id, doc, caption=f"✅ {vpn_type} - {folder} - $2 - {ht['date_str']} {txn_id}")
                bot.send_message(user_id, f"💚 APPROVED\n✅ {vpn_type}\n📁 {folder} - {os.path.basename(fp)}\n💰 ${amount}\n💳 {ECOCASH_NUMBER}\n🧾 {txn_id}\n📅 {ht['full']}\n\n📥 File from {folder} folder!\n/help")
            else:
                bot.send_message(ADMIN_ID, f"⚠️ No file for {vpn_type}")
                bot.send_message(user_id, f"❌ File missing - Contact /support")
        pending_choice.pop(user_id,None); pending_approval.pop(str(user_id),None)
        sales_log.append({"user":user_id,"username":username,"vpn":vpn_type,"txn":txn_id,"date":ht['date_str'],"amount":amount}); save()
    except Exception as e:
        bot.send_message(ADMIN_ID, f"Error {e}")

def validate_sms(text):
    if not (text.startswith("Cashin Confirmation:") or text.startswith("Transfer Confirmation:")): return False, "Not EcoCash SMS", None, None
    if "approval code:" not in text.lower(): return False, "No Approval Code", None, None
    m = re.search(r'USD\s*\$?\s*(\d+\.?\d*)', text.upper())
    if not m: return False, "No USD", None, None
    amount = float(m.group(1))
    if amount < 1.99: return False, f"${amount} < $2", None, None
    mc = re.search(r'(?:CI|PP)\d{6}\.\d{3,4}(?:\.T\d+)?', text.upper())
    txn = mc.group(0) if mc else "NOCODE"
    if text.startswith("Transfer Confirmation:"):
        if "danil" not in text.lower() and "tafadzwa" not in text.lower() and "zinatsa" not in text.lower(): return False, f"Not to {ECOCASH_NUMBER}", None, None
    return True, "Valid", txn, amount

def menu_main(chat_id):
    markup=InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("📡 ZOL - $2", callback_data="cat_ZOL"))
    markup.add(InlineKeyboardButton("🌐 ECONET - $2", callback_data="cat_ECONET"))
    markup.add(InlineKeyboardButton("🔥 ALL 12 - $2 BEST", callback_data="cat_ALL"))
    bot.send_message(chat_id, f"🚀 CHOOSE NETWORK - $2\n💳 {ECOCASH_NUMBER} {ECOCASH_NAME}\n\n📡 ZOL\n🌐 ECONET\n🔥 ALL", reply_markup=markup)

def menu_zol(chat_id):
    markup=InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("📡 ZOL VPN - $2", callback_data="buy_ZOL"))
    markup.add(InlineKeyboardButton("📡 HA Tunnel ZOL - $2", callback_data="buy_HA Tunnel Plus ZOL"))
    markup.add(InlineKeyboardButton("📡 HTTP Custom ZOL - $2", callback_data="buy_HTTP Custom ZOL"))
    markup.add(InlineKeyboardButton("📡 Stark ZOL - $2", callback_data="buy_STARK ZOL"))
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="cat_BACK"))
    bot.send_message(chat_id, f"📡 ZOL - ALL $2\n💳 {ECOCASH_NUMBER}", reply_markup=markup)

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
    bot.send_message(chat_id, f"🌐 ECONET - ALL $2\n💳 {ECOCASH_NUMBER}", reply_markup=markup)

def menu_all(chat_id):
    markup=InlineKeyboardMarkup(row_width=1)
    for n in ["HA Tunnel Plus","HTTP Custom","EHI","NPV","STARK","DARK","TLS","SocksIP","NETMOD","ZOL","ECO"]:
        markup.add(InlineKeyboardButton(f"{n} - $2", callback_data=f"buy_{n}"))
    markup.add(InlineKeyboardButton("🔥 Family ALL 12 - $2 BEST", callback_data="buy_FAMILY"))
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="cat_BACK"))
    bot.send_message(chat_id, f"🔥 ALL 12 - $2\n💳 {ECOCASH_NUMBER}", reply_markup=markup)

@app.route('/')
def home(): return f"LIVE {harare_time()['full']} Sales {len(sales_log)}"

@bot.message_handler(commands=['start'])
def cmd_start(m):
    bot.send_message(m.chat.id, f"🚀 Welcome REO VPN\n💳 {ECOCASH_NUMBER} {ECOCASH_NAME}\n📡 /zol ZOL $2\n🌐 /econet ECONET $2\n🛒 /buy Choose")
    menu_main(m.chat.id)

@bot.message_handler(commands=['buy'])
def cmd_buy(m): menu_main(m.chat.id)
@bot.message_handler(commands=['zol'])
def cmd_zol(m): menu_zol(m.chat.id)
@bot.message_handler(commands=['econet','eco'])
def cmd_econet(m): menu_econet(m.chat.id)
@bot.message_handler(commands=['price'])
def cmd_price(m): bot.send_message(m.chat.id, f"💰 Price {ECOCASH_NUMBER}\n\n📡 ZOL $2: ZOL, HA ZOL, HTTP ZOL, Stark ZOL\n🌐 ECONET $2: ECO, HA, HTTP, EHI, NPV, Dark, TLS, SocksIP, NetMod\n🔥 Family ALL 12 $2\n/buy /zol /econet")
@bot.message_handler(commands=['proof'])
def cmd_proof(m): bot.send_message(m.chat.id, f"✅ Proofs Total {len(sales_log)} to {ECOCASH_NUMBER}\n/buy")
@bot.message_handler(commands=['trial'])
def cmd_trial(m): bot.send_message(m.chat.id, "🎁 Money back - Family $2 test - /buy")
@bot.message_handler(commands=['refer'])
def cmd_refer(m): bot.send_message(m.chat.id, f"👥 Refer $0.50 https://t.me/reo_products_bot")
@bot.message_handler(commands=['support'])
def cmd_support(m): bot.send_message(m.chat.id, f"📞 Support {ECOCASH_NAME} {ECOCASH_NUMBER}")
@bot.message_handler(commands=['help'])
def cmd_help(m): bot.send_message(m.chat.id, f"📲 1 /buy or /zol or /econet\n2 Pick $2\n3 Pay {ECOCASH_NUMBER} *153#\n4 Forward SMS\n5 Danil approves")
@bot.message_handler(commands=['about'])
def cmd_about(m): bot.send_message(m.chat.id, f"⭐ REO 500+ Customers {ECOCASH_NUMBER}")
@bot.message_handler(commands=['myvpn'])
def cmd_myvpn(m):
    my=[s for s in sales_log if s['user']==m.from_user.id]
    if not my: bot.send_message(m.chat.id, "❌ No purchases /buy"); return
    last=my[-1]; deliver(m.from_user.id, last['vpn'], last['txn'], last['amount'], "")
@bot.message_handler(commands=['status'])
def cmd_status(m):
    if m.from_user.id in pending_choice: bot.send_message(m.chat.id, f"⏳ Waiting {pending_choice[m.from_user.id]}")
    elif str(m.from_user.id) in pending_approval: bot.send_message(m.chat.id, f"⏳ Waiting approval")
    else: bot.send_message(m.chat.id, "✅ No pending /buy")

@bot.message_handler(commands=['pending'])
def cmd_pending(m):
    if m.from_user.id!=ADMIN_ID: bot.send_message(m.chat.id, "❌ Admin only"); return
    if not pending_approval: bot.send_message(m.chat.id, "✅ No pending"); return
    msg=f"⏳ Pending {len(pending_approval)}\n"
    for uid,data in pending_approval.items(): msg+=f"{uid} {data['vpn']} {data['txn']}\n/give {uid} {data['vpn']}\n\n"
    bot.send_message(m.chat.id, msg[:4000])

@bot.message_handler(commands=['give'])
def cmd_give(m):
    if m.from_user.id!=ADMIN_ID: bot.send_message(m.chat.id, "❌ Admin only"); return
    try:
        _, uid, *vpn = m.text.split(); uid=int(uid); vpn=" ".join(vpn)
        if "family" in vpn.lower(): vpn="FAMILY"
        deliver(uid, vpn, "MANUAL", 2.00, "admin"); bot.send_message(m.chat.id, f"✅ Gave {vpn} to {uid}")
    except: bot.send_message(m.chat.id, "Usage: /give USERID VPN")

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    if c.data=="cat_ZOL": menu_zol(c.message.chat.id)
    elif c.data=="cat_ECONET": menu_econet(c.message.chat.id)
    elif c.data=="cat_ALL": menu_all(c.message.chat.id)
    elif c.data=="cat_BACK": menu_main(c.message.chat.id)
    elif c.data.startswith("buy_"):
        vpn=c.data.replace("buy_",""); pending_choice[c.from_user.id]=vpn
        bot.send_message(c.message.chat.id, f"💰 Order {vpn} $2 to {ECOCASH_NUMBER}\nPay $2 via *153# then forward SMS\nFile from {'ZOL' if 'zol' in vpn.lower() else 'ECONET'} folder")
    elif c.data.startswith("approve_") or c.data.startswith("ap_"):
        if c.from_user.id!=ADMIN_ID: return
        uid=int(c.data.split("_")[1]); data=pending_approval.get(str(uid))
        if data: deliver(uid, data['vpn'], data['txn'], data['amount'], ""); bot.edit_message_text(f"✅ APPROVED {uid}", c.message.chat.id, c.message.message_id)
    elif c.data.startswith("reject_") or c.data.startswith("rj_"):
        if c.from_user.id!=ADMIN_ID: return
        uid=int(c.data.split("_")[1]); pending_approval.pop(str(uid),None); pending_choice.pop(uid,None); save()
        bot.edit_message_text(f"❌ REJECTED {uid}", c.message.chat.id, c.message.message_id)

@bot.message_handler(content_types=['text'])
def handle_sms(m):
    if m.text.startswith("/"): return
    if m.from_user.id not in pending_choice: bot.send_message(m.chat.id, "👋 /buy /zol /econet"); return
    valid, reason, txn, amount = validate_sms(m.text)
    if not valid: bot.send_message(m.chat.id, f"❌ {reason}"); return
    h=hashlib.sha256(txn.encode()).hexdigest()[:20]
    if h in used_hashes: bot.send_message(m.chat.id, f"🚫 Used {txn}"); return
    pending_approval[str(m.from_user.id)]={"vpn":pending_choice[m.from_user.id],"txn":txn,"amount":amount,"username":m.from_user.username or ""}; save()
    bot.send_message(m.chat.id, f"✅ SMS Received ${amount} {txn} {pending_choice[m.from_user.id]}\n⏳ Waiting Danil")
    markup=InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("✅ APPROVE", callback_data=f"approve_{m.from_user.id}"), InlineKeyboardButton("❌ REJECT", callback_data=f"reject_{m.from_user.id}"))
    bot.send_message(ADMIN_ID, f"🔔 NEW {m.from_user.id} {pending_choice[m.from_user.id]} ${amount} {txn}\n{m.text}", reply_markup=markup)

def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
if __name__=="__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.infinity_polling()
