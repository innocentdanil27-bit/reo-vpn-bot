import os, telebot, time, re, hashlib, json
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
from datetime import datetime

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

# ===== ULTRA SECURE CHECK =====
def confirm_payment(text):
    upper=text.upper()
    lower=text.lower()
    if not text.startswith("Cashin Confirmation:"):
        return False, "Fake! Must forward REAL SMS", None, None, None
    if "received from" not in lower:
        return False, "Fake! No 'received from'", None, None, None
    if "approval code:" not in lower:
        return False, "Fake! No Approval Code", None, None, None
    if "new balance:" not in lower:
        return False, "Fake! No New Balance", None, None, None
    if "transact using the super app" not in lower:
        return False, "Fake! No Super App line", None, None, None

    amt_m=re.search(r'USD\s*\$?\s*(\d+\.?\d*)', upper)
    if not amt_m: return False, "No USD amount", None, None, None
    amount=float(amt_m.group(1))
    if amount < 2.0: return False, f"Amount USD {amount} < $2", None, None, None

    app_m=re.search(r'CI\d{6}\.\d{3,4}\.T\d{6,10}', upper)
    if not app_m: return False, "Invalid Code Format", None, None, None
    txn_id=app_m.group(0)
    if hash_txn(txn_id) in used_txns:
        return False, f"ALREADY USED {txn_id}", None, None, None

    today = datetime.now().date()
    today_str = today.strftime('%d/%m/%Y')
    dm=re.search(r'CI(\d{2})(\d{2})(\d{2})', upper)
    if dm:
        y,mn,d=dm.groups()
        try:
            full_year=2000+int(y)
            if full_year < 2026 or full_year > 2030:
                return False, f"OLD {d}/{mn}/{full_year} Only 2026-2030", f"{d}/{mn}/{full_year}", txn_id, amount
            txn_date_str=f"{d}/{mn}/{full_year}"
            dt=datetime.strptime(txn_date_str, '%d/%m/%Y').date()
            if dt!= today:
                return False, f"OLD {txn_date_str} - TODAY {today_str} ONLY!", txn_date_str, txn_id, amount
        except:
            return False, "Invalid Date", None, None, None
    else:
        return False, "No CI date", None, None, None
    return True, f"CONFIRMED USD {amount}", txn_date_str, txn_id, amount

def send_file(uid, vtype, txn_id, txn_date, amount, username=""):
    files=get_files()
    used_txns.add(hash_txn(txn_id))
    try:
        # SEND CORRECT FILE BASED ON VPN TYPE
        if vtype=="FAMILY":
            for f in files:
                with open(f"configs/{f}",'rb') as doc:
                    bot.send_document(uid, doc, caption=f"✅ Family Pack $2\nTxn:{txn_id}\nDate:{txn_date}")
        else:
            # Try find file matching vtype, else send first
            sent=False
            for f in files:
                if vtype.lower() in f.lower():
                    with open(f"configs/{f}",'rb') as doc:
                        bot.send_document(uid, doc, caption=f"✅ {vtype} $2\nTxn:{txn_id}\nDate:{txn_date}")
                    sent=True
                    break
            if not sent and files:
                with open(f"configs/{files[0]}",'rb') as doc:
                    bot.send_document(uid, doc, caption=f"✅ {vtype} $2\nTxn:{txn_id}\nDate:{txn_date}")

        bot.send_message(uid, f"💚 USD {amount} CONFIRMED!\n✅ {vtype}\nTxn:{txn_id}\nDate:{txn_date}\nFile sent! Enjoy!")
        pending.pop(uid,None)
        transactions_log.append({"user":uid,"username":username,"app":vtype,"txn_id":txn_id,"txn_date":txn_date,"amount":amount,"confirm":datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        save_backup()
        if uid!= ADMIN_ID:
            bot.send_message(ADMIN_ID, f"🔔 NEW SALE $2!\n💰 USD {amount}\n📱 App: {vtype}\n👤 {uid} @{username}\n🧾 {txn_id}\n📅 {txn_date}\n📊 Total: {len(transactions_log)}")
    except Exception as e:
        if uid!= ADMIN_ID:
            bot.send_message(ADMIN_ID, f"Error {e}")

@app.route('/')
def home(): return f"LIVE - {len(transactions_log)} sales - ALL VPNs $2"

@bot.message_handler(commands=['start'])
def start_cmd(m):
    if m.from_user.id in blocked: return
    markup=InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("1. HA Tunnel Plus - $2", callback_data="buy_HA Tunnel Plus"))
    markup.add(InlineKeyboardButton("2. HTTP Custom - $2", callback_data="buy_HTTP Custom"))
    markup.add(InlineKeyboardButton("3. HTTP Injector (EHI) - $2", callback_data="buy_EHI"))
    markup.add(InlineKeyboardButton("4. NapsternetV (NPV) - $2", callback_data="buy_NPV"))
    markup.add(InlineKeyboardButton("5. Stark VPN - $2", callback_data="buy_STARK"))
    markup.add(InlineKeyboardButton("6. Dark Tunnel - $2", callback_data="buy_DARK"))
    markup.add(InlineKeyboardButton("7. TLS Tunnel - $2", callback_data="buy_TLS"))
    markup.add(InlineKeyboardButton("8. SocksIP Tunnel - $2", callback_data="buy_SocksIP"))
    markup.add(InlineKeyboardButton("9. NetMod / SocksHttp - $2", callback_data="buy_NETMOD"))
    markup.add(InlineKeyboardButton("10. Family Pack (All Apps) - $2 🔥", callback_data="buy_FAMILY"))
    bot.send_message(m.chat.id, "✅ REO VPN BOT - INSTANT AUTO DELIVERY\n✅ Support 24/7 - Danil\n⭐ 500+ Happy Customers\n🛡️ Money Back Guarantee\n\n👇 ALL $2 - PICK YOUR VPN:\n\n💳 Pay: EcoCash 0775713879 - Danil\n📅 TODAY ONLY - No Yesterday!\nForward REAL EcoCash SMS after pay", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    if c.data.startswith("buy_"):
        pending[c.from_user.id]=c.data.replace("buy_","")
        bot.send_message(c.message.chat.id, f"💰 {c.data.replace('buy_','')} - $2\n💳 EcoCash: 0775713879\nName: Danil\n\nAfter pay, Forward REAL SMS:\nCashin Confirmation: USD 2.00 received from...\nApproval Code: CI{datetime.now().strftime('%y%m%d')}...\nNew balance: USD...\nTransact using the Super App...\n\nMust be TODAY {datetime.now().strftime('%d/%m/%Y')} ONLY!")
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
    bot.send_photo(ADMIN_ID, m.photo[-1].file_id, caption=f"📸 Check\nApp:{vtype}\nUser:{m.from_user.id} @{m.from_user.username}", reply_markup=markup)
    bot.send_message(m.chat.id, "Screenshot sent to Danil for manual check!")

@bot.message_handler(content_types=['text'])
def txt(m):
    uid=m.from_user.id
    username=m.from_user.username or ""
    if uid not in pending: return
    if "i paid" in m.text.lower() and "confirmation" not in m.text.lower():
        bot.send_message(m.chat.id, "🚫 Forward REAL EcoCash SMS with Approval Code! Not 'I paid'"); return
    valid, reason, txn_date, txn_id, amount = confirm_payment(m.text)
    if valid:
        bot.send_message(m.chat.id, f"🔍 {reason}\nTxn:{txn_id}\nDate:{txn_date}\n✅ $2 Confirmed!")
        send_file(uid, pending[uid], txn_id, txn_date, amount, username)
    else:
        if "ALREADY USED" in reason:
            blocked.add(uid); save_backup()
            bot.send_message(m.chat.id, f"🚫 {reason} - BLOCKED!")
            if uid!= ADMIN_ID:
                bot.send_message(ADMIN_ID, f"🚨 Hacker reuse {uid} {txn_id}")
        elif len(m.text)>15:
            bot.send_message(m.chat.id, f"❌ {reason}\nNeed REAL EcoCash SMS + USD 2.00 + TODAY {datetime.now().strftime('%d/%m/%Y')} ONLY!")

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__=="__main__":
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
