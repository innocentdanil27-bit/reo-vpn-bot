import os, telebot, time, re, hashlib, json
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
from datetime import datetime, timedelta

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8579468852"))
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

pending = {}
blocked = set()
used_txns = set()
transactions_log = []
BACKUP_FILE = "transactions_backup.json"

if os.path.exists(BACKUP_FILE):
    try:
        with open(BACKUP_FILE,'r') as f:
            d=json.load(f)
            transactions_log=d.get("logs",[])
            used_txns=set(d.get("used_txns",[]))
    except: pass

def save_backup():
    with open(BACKUP_FILE,'w') as f:
        json.dump({"logs":transactions_log,"used_txns":list(used_txns)},f)

def hash_txn(t): return hashlib.sha256(t.encode()).hexdigest()[:20]
def get_files():
    if not os.path.exists("configs"): return []
    return [f for f in os.listdir("configs") if not f.startswith('.')]

def confirm_payment(text):
    upper=text.upper()
    lower=text.lower()
    if "confirmation" not in lower and "ecocash" not in lower:
        return False, "Not EcoCash", None, None, None
    amt_m=re.search(r'USD\s*\$?\s*(\d+\.?\d*)', upper)
    if not amt_m: return False, "No USD amount", None, None, None
    amount=float(amt_m.group(1))
    if amount < 2.0: return False, f"Amount USD {amount} < $2", None, None, None
    app_m=re.search(r'(CI\d{6}\.\d+\.T\d+|MP\d+|TXN[A-Z0-9]+)', upper)
    if not app_m: return False, "No Approval Code", None, None, None
    txn_id=app_m.group(1)
    if hash_txn(txn_id) in used_txns:
        return False, f"ALREADY USED {txn_id}", None, None, None
    txn_date_str=datetime.now().strftime('%d/%m/%Y')
    dm=re.search(r'CI(\d{2})(\d{2})(\d{2})', upper)
    if dm:
        y,mn,d=dm.groups()
        try:
            full_year=2000+int(y)
            if full_year < 2026 or full_year > 2030:
                return False, f"OLD DATE {d}/{mn}/{full_year} - Only 2026-2030 allowed", f"{d}/{mn}/{full_year}", txn_id, amount
            txn_date_str=f"{d}/{mn}/{full_year}"
            dt=datetime.strptime(txn_date_str, '%d/%m/%Y')
            if abs((datetime.now()-dt).days) > 30:
                return False, f"OLD DATE {txn_date_str} - Must be recent", txn_date_str, txn_id, amount
        except: pass
    return True, f"CONFIRMED USD {amount}", txn_date_str, txn_id, amount

def send_file(uid, vtype, txn_id, txn_date, amount, username=""):
    files=get_files()
    used_txns.add(hash_txn(txn_id))
    try:
        if vtype=="FAMILY":
            for f in files:
                with open(f"configs/{f}",'rb') as doc:
                    bot.send_document(uid, doc, caption=f"✅ Family Pack $2\nTxn:{txn_id}\nDate:{txn_date}")
        else:
            if files:
                with open(f"configs/{files[0]}",'rb') as doc:
                    bot.send_document(uid, doc, caption=f"✅ {vtype} $2\nTxn:{txn_id}\nDate:{txn_date}")
        bot.send_message(uid, f"💚 USD {amount} CONFIRMED!\nTxn:{txn_id}\nDate:{txn_date}\nFile sent!")
        pending.pop(uid,None)
        transactions_log.append({"user":uid,"username":username,"app":vtype,"txn_id":txn_id,"txn_date":txn_date,"amount":amount,"confirm":datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        save_backup()
        bot.send_message(ADMIN_ID, f"🔔 NEW SALE $2!\n\n💰 USD {amount}\n📱 App: {vtype}\n👤 User: {uid} @{username}\n🧾 Txn: {txn_id}\n📅 Date: {txn_date}\n⏰ Now: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n💳 To: 0775713879\n✅ FILE SENT & BACKED UP\n📊 Total: {len(transactions_log)}")
        if len(transactions_log)%5==0:
            with open(BACKUP_FILE,'rb') as d:
                bot.send_document(ADMIN_ID, d, caption=f"💾 Backup {len(transactions_log)} sales")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"Error {e}")

@app.route('/')
def home(): return f"LIVE $2 Bot - {len(transactions_log)} sales - All VPNs - 2026-2030"

@bot.message_handler(commands=['start'])
def start(m):
    if m.from_user.id in blocked: return
    markup=InlineKeyboardMarkup(row_width=1)
    # ALL VPN APPS - $2
    markup.add(InlineKeyboardButton("HA Tunnel Plus - $2", callback_data="buy_HA"))
    markup.add(InlineKeyboardButton("HTTP Custom - $2", callback_data="buy_HC"))
    markup.add(InlineKeyboardButton("HTTP Injector - $2", callback_data="buy_EHI"))
    markup.add(InlineKeyboardButton("NapsternetV - $2", callback_data="buy_NPV"))
    markup.add(InlineKeyboardButton("Stark VPN - $2", callback_data="buy_STK"))
    markup.add(InlineKeyboardButton("Dark Tunnel - $2", callback_data="buy_DARK"))
    markup.add(InlineKeyboardButton("TLS Tunnel - $2", callback_data="buy_TLS"))
    markup.add(InlineKeyboardButton("SocksIP Tunnel - $2", callback_data="buy_SOCKS"))
    markup.add(InlineKeyboardButton("NetMod / SocksHttp - $2", callback_data="buy_NETMOD"))
    markup.add(InlineKeyboardButton("Family Pack (All Apps) - $2", callback_data="buy_FAMILY"))
    markup.row(InlineKeyboardButton("📖 How To Use", callback_data="howto"), InlineKeyboardButton("💬 Support Danil", callback_data="support"))
    bot.send_message(m.chat.id, "✅ INSTANT AUTO DELIVERY\n✅ Support 24/7 - Danil\n\n⭐ 500+ Happy Customers\n🛡️ Money Back by Danil\n\n👇 ALL $2 - PICK YOUR APP:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    if c.data.startswith("buy_"):
        pending[c.from_user.id]=c.data.replace("buy_","")
        bot.send_message(c.message.chat.id, f"💰 {c.data.replace('buy_','')} - $2\n💳 EcoCash: 0775713879\nName: Danil\n\nForward:\nCashin Confirmation: USD 2.00 received...\nApproval Code: CI260915...\nMust be TODAY {datetime.now().strftime('%d/%m/%Y')}")
    elif c.data=="howto":
        bot.send_message(c.message.chat.id, "📖 HOW TO USE\n\n1️⃣ Pick App $2\n2️⃣ Pay EcoCash 0775713879\n3️⃣ Forward SMS: Cashin Confirmation USD 2.00...\n4️⃣ Bot checks Date 2026-2030 + Amount $2 + Txn new\n5️⃣ File instantly!\n\n⚠️ No reuse! Must be recent!")
    elif c.data=="support":
        bot.send_message(c.message.chat.id, "💬 SUPPORT 24/7 - Danil\n\n📱 EcoCash: 0775713879\n👤 Danil\n🛡️ 500+ Happy Customers\n\nIf issue, forward SMS here!")
    if c.data.startswith("approve_"):
        if c.from_user.id!=ADMIN_ID: return
        _,uid,vtype=c.data.split("_",2)
        send_file(int(uid),vtype,f"MANUAL-{int(time.time())}",datetime.now().strftime('%d/%m/%Y'),2.00,"manual")

@bot.message_handler(content_types=['photo'])
def ph(m):
    if m.from_user.id not in pending: return
    vtype=pending[m.from_user.id]
    markup=InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ APPROVE", callback_data=f"approve_{m.from_user.id}_{vtype}"))
    bot.send_photo(ADMIN_ID, m.photo[-1].file_id, caption=f"📸 Check\nApp:{vtype}\nUser:{m.from_user.id} @{m.from_user.username}\nDate 2026-2030", reply_markup=markup)
    bot.send_message(m.chat.id, "Screenshot sent to Danil!")

@bot.message_handler(content_types=['text'])
def txt(m):
    uid=m.from_user.id
    username=m.from_user.username or ""
    if uid==ADMIN_ID and "/backup" in m.text:
        with open(BACKUP_FILE,'rb') as d: bot.send_document(ADMIN_ID, d); return
    if uid==ADMIN_ID and ("/myid" in m.text or "/id" == m.text.lower()):
        bot.send_message(ADMIN_ID, f"👑 ADMIN\n🆔 ID: {ADMIN_ID}\n👤 @{m.from_user.username}\n📊 Sales: {len(transactions_log)}"); return
    if uid not in pending: return
    if "i paid" in m.text.lower() and "confirmation" not in m.text.lower():
        bot.send_message(m.chat.id, "🚫 NO FILE! Forward EcoCash SMS with Approval Code!"); return
    valid, reason, txn_date, txn_id, amount = confirm_payment(m.text)
    if valid:
        bot.send_message(m.chat.id, f"🔍 {reason}\nTxn:{txn_id}\nDate:{txn_date}\n✅ $2 Confirmed! Sending file...")
        send_file(uid, pending[uid], txn_id, txn_date, amount, username)
    else:
        if "ALREADY USED" in reason:
            blocked.add(uid); save_backup()
            bot.send_message(m.chat.id, f"🚫 {reason} - BLOCKED!")
            bot.send_message(ADMIN_ID, f"🚨 Hacker reuse {uid} {txn_id}")
        elif len(m.text)>15:
            bot.send_message(m.chat.id, f"❌ {reason}\nNeed USD 2.00 + Approval Code + TODAY date 2026-2030")

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__=="__main__":
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
