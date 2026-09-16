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

# --- FILES ACCORDING TO NAMES - LEGIT MAP ---
VPN_FILE_MAP = {
    "ZOL": ["zol vpn", "zol main", "zol"],
    "HA Tunnel Plus ZOL": ["ha tunnel plus zol", "ha zol", "hat zol"],
    "HTTP Custom ZOL": ["http custom zol", "hc zol", "http zol"],
    "STARK ZOL": ["stark zol"],
    "FAMILY ZOL": ["family zol"],
    "ECO": ["eco vpn", "econet vpn", "eco"],
    "HA Tunnel Plus": ["ha tunnel plus", "ha_plus", "hat"],
    "HTTP Custom": ["http custom", "http_custom", "hc"],
    "EHI": ["ehi"],
    "NPV": ["npv", "napsternet"],
    "STARK": ["stark"],
    "DARK": ["dark"],
    "TLS": ["tls"],
    "SocksIP": ["socksip", "socks"],
    "NETMOD": ["netmod"],
    "FAMILY": ["family", "all 12"],
}

def get_files():
    if not os.path.exists("configs"): return []
    return [f for f in os.listdir("configs") if not f.startswith('.')]

def find_file_for_vpn(vpn_type):
    files = get_files()
    vpn_lower = vpn_type.lower().strip()
    for f in files:
        if vpn_lower == f.lower().split('.')[0].strip(): return f
    keywords = VPN_FILE_MAP.get(vpn_type, [vpn_lower])
    keywords = [k.lower() for k in keywords] + [vpn_lower]
    for f in files:
        fl = f.lower()
        for kw in keywords:
            if kw in fl: return f
    first = vpn_lower.split()[0]
    for f in files:
        if first in f.lower(): return f
    return None

def deliver(user_id, vpn_type, txn_id, amount, username=""):
    ht = harare_time()
    if not txn_id.startswith("MANUAL"): used_hashes.add(hashlib.sha256(txn_id.encode()).hexdigest()[:20])
    try:
        files = get_files()
        if not files:
            bot.send_message(user_id, f"❌ No configs - Contact /support {ECOCASH_NUMBER}")
            bot.send_message(ADMIN_ID, "⚠️ configs/ empty!"); return
        matched_file = None
        if "FAMILY" in vpn_type.upper():
            bot.send_message(user_id, f"📦 Family Pack ALL 12 - Sending {len(files)} files...")
            for f in files:
                with open(f"configs/{f}",'rb') as doc: bot.send_document(user_id, doc, caption=f"✅ {f} - Family $2 - {ht['date_str']}")
        else:
            matched_file = find_file_for_vpn(vpn_type)
            if matched_file:
                with open(f"configs/{matched_file}",'rb') as doc: bot.send_document(user_id, doc, caption=f"✅ {vpn_type} - $2 - {ht['date_str']} - {txn_id} To {ECOCASH_NUMBER}")
                bot.send_message(user_id, f"💚 APPROVED BY DANIL\n✅ VPN: {vpn_type}\n📄 File: {matched_file}\n💰 ${amount}\n💳 To: {ECOCASH_NUMBER} {ECOCASH_NAME}\n📅 {ht['full']}\n🧾 {txn_id}\n\n📥 Sent according to name!\n📲 /help\n🔄 /myvpn")
            else:
                with open(f"configs/{files[0]}",'rb') as doc: bot.send_document(user_id, doc, caption=f"✅ {vpn_type} - $2")
                bot.send_message(ADMIN_ID, f"⚠️ No file for {vpn_type} - Sent default {files[0]} - Rename file in configs/ to '{vpn_type}'")
        pending_choice.pop(user_id,None); pending_approval.pop(str(user_id),None)
        sales_log.append({"user":user_id,"username":username,"vpn":vpn_type,"file":matched_file or "ALL","txn":txn_id,"date":ht['date_str'],"amount":amount}); save()
        if user_id!=ADMIN_ID: bot.send_message(ADMIN_ID, f"✅ Sent {vpn_type} ({matched_file or 'ALL'}) to {user_id} @{username} {txn_id} ${amount} Total {len(sales_log)}")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Deliver error {vpn_type} to {user_id}: {e}")

def validate_sms(text):
    if not (text.startswith("Cashin Confirmation:") or text.startswith("Transfer Confirmation:")): return False, "Not EcoCash SMS", None, None
    if "approval code:" not in text.lower(): return False, "No Approval Code", None, None
    m = re.search(r'USD\s*\$?\s*(\d+\.?\d*)', text.upper())
    if not m: return False, "No USD amount", None, None
    amount = float(m.group(1))
    if amount < 1.99: return False, f"${amount} < $2", None, None
    mc = re.search(r'(?:CI|PP)\d{6}\.\d{3,4}(?:\.T\d+)?', text.upper())
    txn = mc.group(0) if mc else "NOCODE"
    if text.startswith("Transfer Confirmation:"):
        if "danil" not in text.lower() and "tafadzwa" not in text.lower() and "zinatsa" not in text.lower(): return False, f"Not to {ECOCASH_NUMBER}", None, None
    return True, "Valid", txn, amount

# MENUS
def menu_main(chat_id):
    markup=InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("📡 ZOL - $2", callback_data="cat_ZOL"))
    markup.add(InlineKeyboardButton("🌐 ECONET - $2", callback_data="cat_ECONET"))
    markup.add(InlineKeyboardButton("🔥 ALL 12 - $2 BEST", callback_data="cat_ALL"))
    ht=harare_time()
    bot.send_message(chat_id, f"🚀 CHOOSE NETWORK - $2\n📅 {ht['day']} {ht['date_str']} {ht['time_str']} CAT\n💳 {ECOCASH_NUMBER} {ECOCASH_NAME}\n\n📡 ZOL\n🌐 ECONET\n🔥 ALL\nTap:", reply_markup=markup)

def menu_zol(chat_id):
    markup=InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("📡 ZOL VPN - $2", callback_data="buy_ZOL"))
    markup.add(InlineKeyboardButton("📡 HA Tunnel ZOL - $2", callback_data="buy_HA Tunnel Plus ZOL"))
    markup.add(InlineKeyboardButton("📡 HTTP Custom ZOL - $2", callback_data="buy_HTTP Custom ZOL"))
    markup.add(InlineKeyboardButton("📡 Stark ZOL - $2", callback_data="buy_STARK ZOL"))
    markup.add(InlineKeyboardButton("📡 Family ZOL - $2", callback_data="buy_FAMILY ZOL"))
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="cat_BACK"))
    bot.send_message(chat_id, f"📡 ZOL - ALL $2\n💳 {ECOCASH_NUMBER}\nPick ZOL VPN:", reply_markup=markup)

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
    bot.send_message(chat_id, f"🌐 ECONET - ALL $2\n💳 {ECOCASH_NUMBER}\nPick ECONET VPN:", reply_markup=markup)

def menu_all(chat_id):
    markup=InlineKeyboardMarkup(row_width=1)
    for n in ["HA Tunnel Plus","HTTP Custom","EHI","NPV","STARK","DARK","TLS","SocksIP","NETMOD","ZOL","ECO"]:
        markup.add(InlineKeyboardButton(f"{n} - $2", callback_data=f"buy_{n}"))
    markup.add(InlineKeyboardButton("🔥 Family ALL 12 - $2 BEST", callback_data="buy_FAMILY"))
    markup.add(InlineKeyboardButton("🔙 Back", callback_data="cat_BACK"))
    bot.send_message(chat_id, f"🔥 ALL 12 VPNs - $2\n💳 {ECOCASH_NUMBER}\nZOL + ECONET:", reply_markup=markup)

@app.route('/')
def home(): return f"LIVE {harare_time()['full']} Sales {len(sales_log)} Pending {len(pending_approval)} Files {len(get_files())}"

# ===== ALL CUSTOMER COMMANDS - EVERY COMMAND RESPONDS =====
@bot.message_handler(commands=['start'])
def cmd_start(m):
    ht=harare_time()
    bot.send_message(m.chat.id, f"🚀 Welcome REO VPN - TRUE {ECOCASH_NUMBER}\n📅 {ht['full']}\n💳 {ECOCASH_NUMBER} {ECOCASH_NAME}\n⭐ 500+ Customers\n📡 /zol = ZOL $2\n🌐 /econet = ECONET $2\n🛒 /buy = Choose\n💰 /price = Price\n📦 /myvpn = My VPNs\n📞 /support = Help")
    menu_main(m.chat.id)

@bot.message_handler(commands=['buy'])
def cmd_buy(m): menu_main(m.chat.id)

@bot.message_handler(commands=['zol'])
def cmd_zol(m): menu_zol(m.chat.id)

@bot.message_handler(commands=['econet','eco'])
def cmd_econet(m): menu_econet(m.chat.id)

@bot.message_handler(commands=['price'])
def cmd_price(m):
    ht=harare_time()
    bot.send_message(m.chat.id, f"💰 Price List - {ht['date_str']}\n💳 TRUE {ECOCASH_NUMBER} {ECOCASH_NAME}\n\n📡 ZOL $2:\n• ZOL VPN $2\n• HA Tunnel ZOL $2\n• HTTP Custom ZOL $2\n• Stark ZOL $2\n\n🌐 ECONET $2:\n• ECONET VPN $2\n• HA Tunnel Plus $2\n• HTTP Custom $2\n• EHI $2\n• NPV $2\n• Dark $2\n• TLS $2\n• SocksIP $2\n• NetMod $2\n\n🔥 Family ALL 12 $2 BEST - SAVE $22\n👉 /buy /zol /econet")

@bot.message_handler(commands=['proof'])
def cmd_proof(m):
    ht=harare_time()
    recent=sales_log[-10:][::-1]
    txt=f"✅ Live Proofs {ht['date_str']} {ht['time_str']} CAT\nTotal {len(sales_log)} to {ECOCASH_NUMBER}\n\n"
    for s in recent: txt+=f"• {s['vpn']} {s['date']} ${s['amount']} ✅\n"
    bot.send_message(m.chat.id, txt+"\n/buy to order")

@bot.message_handler(commands=['trial'])
def cmd_trial(m): bot.send_message(m.chat.id, "🎁 No free trial but money back - Family Pack ALL 12 $2 test speed - /buy /zol /econet")

@bot.message_handler(commands=['refer'])
def cmd_refer(m): bot.send_message(m.chat.id, f"👥 Refer & earn $0.50\nShare https://t.me/reo_products_bot\nFriend pays $2 to {ECOCASH_NUMBER} you get $0.50\n4 friends = FREE\n/buy")

@bot.message_handler(commands=['support'])
def cmd_support(m): bot.send_message(m.chat.id, f"📞 Support 24/7\nOwner {ECOCASH_NAME}\nEcoCash {ECOCASH_NUMBER}\nDanil replies 1-5 mins\n/support")

@bot.message_handler(commands=['help'])
def cmd_help(m): bot.send_message(m.chat.id, f"📲 How to buy:\n1 /buy or /zol or /econet - Choose network\n2 Pick VPN $2\n3 Pay $2 to {ECOCASH_NUMBER} via *153#\n4 Forward REAL EcoCash SMS here\n5 Danil checks EcoCash app & APPROVES 1-5 mins\n6 Bot sends file according to name!\n/support")

@bot.message_handler(commands=['about'])
def cmd_about(m): bot.send_message(m.chat.id, f"⭐ About REO 500+ Customers\nSince 2024 Harare\n💳 {ECOCASH_NUMBER} {ECOCASH_NAME}\n📡 ZOL VPNs $2\n🌐 ECONET VPNs $2\n🔥 All 12 VPNs $2\n✅ Manual verification - 100% safe\n/buy")

@bot.message_handler(commands=['myvpn'])
def cmd_myvpn(m):
    my=[s for s in sales_log if s['user']==m.from_user.id]
    if not my: bot.send_message(m.chat.id, "❌ No purchases yet - /buy /zol /econet"); return
    last=my[-1]; bot.send_message(m.chat.id, f"📦 Your last: {last['vpn']} {last['date']} - Resending file according to name..."); deliver(m.from_user.id, last['vpn'], last['txn'], last['amount'], "")

@bot.message_handler(commands=['status'])
def cmd_status(m):
    if m.from_user.id in pending_choice: bot.send_message(m.chat.id, f"⏳ Waiting payment for {pending_choice[m.from_user.id]} - Pay to {ECOCASH_NUMBER}")
    elif str(m.from_user.id) in pending_approval: bot.send_message(m.chat.id, f"⏳ Waiting Danil approval - {pending_approval[str(m.from_user.id)]['vpn']} - 1-5 mins")
    else: bot.send_message(m.chat.id, "✅ No pending - /buy /zol /econet to order")

# ===== ADMIN ONLY - CUSTOMER NEVER SEES =====
@bot.message_handler(commands=['pending'])
def cmd_pending(m):
    if m.from_user.id!= ADMIN_ID: bot.send_message(m.chat.id, "❌ Admin only - /buy to order"); return
    if not pending_approval: bot.send_message(m.chat.id, "✅ No pending approvals"); return
    msg=f"⏳ PENDING {len(pending_approval)} - TRUE {ECOCASH_NUMBER}\n"
    for uid,data in pending_approval.items(): msg+=f"{uid} - {data['vpn']} - {data['txn']}\n/give {uid} {data['vpn']}\n\n"
    bot.send_message(m.chat.id, msg[:4000])

@bot.message_handler(commands=['give','approve','reject','block','clean_tafadzwa'])
def cmd_admin(m):
    if m.from_user.id!= ADMIN_ID: bot.send_message(m.chat.id, "❌ Admin only - /buy to order VPN $2"); return
    if m.text.startswith("/give"):
        try:
            _, uid, *vpn = m.text.split(); uid=int(uid); vpn=" ".join(vpn)
            if "family" in vpn.lower(): vpn="FAMILY"
            deliver(uid, vpn, "MANUAL", 2.00, "admin_give"); bot.send_message(m.chat.id, f"✅ Gave {vpn} to {uid} - File according to name: {find_file_for_vpn(vpn) or 'ALL'}")
        except Exception as e: bot.send_message(m.chat.id, f"Usage: /give USERID VPN_TYPE\nEx: /give 123 ZOL\n/give 123 EHI\nError: {e}")

# ONE CALLBACK HANDLER - ALL BUTTONS WORK
@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    if c.data=="cat_ZOL": menu_zol(c.message.chat.id)
    elif c.data=="cat_ECONET": menu_econet(c.message.chat.id)
    elif c.data=="cat_ALL": menu_all(c.message.chat.id)
    elif c.data=="cat_BACK": menu_main(c.message.chat.id)
    elif c.data.startswith("buy_"):
        vpn=c.data.replace("buy_",""); pending_choice[c.from_user.id]=vpn
        bot.send_message(c.message.chat.id, f"💰 Order: {vpn} - $2 to {ECOCASH_NUMBER} {ECOCASH_NAME}\n📅 {harare_time()['full']}\n\nPay $2 via *153# to {ECOCASH_NUMBER}\nThen forward EcoCash SMS here\n⏰ Danil approves 1-5 mins\nFile will be sent according to name: {vpn}")
    elif c.data.startswith("approve_") or c.data.startswith("ap_"):
        if c.from_user.id!=ADMIN_ID: return
        uid=int(c.data.split("_")[1]); data=pending_approval.get(str(uid))
        if not data: bot.send_message(c.message.chat.id, "No pending"); return
        deliver(uid, data['vpn'], data['txn'], data['amount'], data.get('username',"")); bot.edit_message_text(f"✅ APPROVED {uid} {data['vpn']} - File: {find_file_for_vpn(data['vpn'])}", c.message.chat.id, c.message.message_id)
    elif c.data.startswith("reject_") or c.data.startswith("rj_"):
        if c.from_user.id!=ADMIN_ID: return
        uid=int(c.data.split("_")[1]); pending_approval.pop(str(uid),None); pending_choice.pop(uid,None); save()
        bot.send_message(uid, f"❌ Rejected - Not TRUE payment to {ECOCASH_NUMBER}"); bot.edit_message_text(f"❌ REJECTED {uid}", c.message.chat.id, c.message.message_id)

@bot.message_handler(content_types=['text'])
def handle_sms(m):
    if m.text.startswith("/"): return
    if m.from_user.id not in pending_choice: bot.send_message(m.chat.id, "👋 /buy Choose ZOL or ECONET\n📡 /zol ZOL only\n🌐 /econet ECONET only\n💰 /price"); return
    valid, reason, txn, amount = validate_sms(m.text)
    if not valid: bot.send_message(m.chat.id, f"❌ {reason}\nMust be REAL EcoCash SMS $2 to {ECOCASH_NUMBER} {ECOCASH_NAME}"); return
    h=hashlib.sha256(txn.encode()).hexdigest()[:20]
    if h in used_hashes: bot.send_message(m.chat.id, f"🚫 Already used {txn}"); return
    pending_approval[str(m.from_user.id)]={"vpn":pending_choice[m.from_user.id],"txn":txn,"amount":amount,"username":m.from_user.username or ""}; save()
    ht=harare_time()
    bot.send_message(m.chat.id, f"✅ SMS Received - Waiting Manual Approval\n💰 ${amount} 🧾 {txn}\n📱 {pending_choice[m.from_user.id]}\n💳 To: {ECOCASH_NUMBER} {ECOCASH_NAME}\n📅 {ht['day']} {ht['date_str']} {ht['time_str']} CAT\n⏳ Danil checking EcoCash app... 1-5 mins\nQueue: {len(pending_approval)}")
    markup=InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("✅ APPROVE", callback_data=f"approve_{m.from_user.id}"), InlineKeyboardButton("❌ REJECT", callback_data=f"reject_{m.from_user.id}"))
    bot.send_message(ADMIN_ID, f"🔔 NEW PAYMENT - TRUE {ECOCASH_NUMBER}\n👤 {m.from_user.id} @{m.from_user.username or ''} {m.from_user.first_name}\n📱 {pending_choice[m.from_user.id]} -> File: {find_file_for_vpn(pending_choice[m.from_user.id])}\n💰 ${amount} 🧾 {txn}\n📅 {ht['full']}\n\nSMS:\n{m.text}\n\nCheck EcoCash ${amount} TRUE to {ECOCASH_NUMBER}? Tap APPROVE", reply_markup=markup)

def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
if __name__=="__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.infinity_polling()
