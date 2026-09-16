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

def confirm_payment(text):
    upper=text.upper(); lower=text.lower()
    if not text.startswith("Cashin Confirmation:"): return False, "Fake! Forward REAL SMS", None, None, None
    if "received from" not in lower: return False, "Fake! No 'received from'", None, None, None
    if "approval code:" not in lower: return False, "Fake! No Approval Code", None, None, None
    if "new balance:" not in lower: return False, "Fake! No New Balance", None, None, None
    if "transact using the super app" not in lower: return False, "Fake! No Super App line", None, None, None
    amt_m=re.search(r'USD\s*\$?\s*(\d+\.?\d*)', upper)
    if not amt_m: return False, "No USD amount", None, None, None
    amount=float(amt_m.group(1))
    if amount < 2.0: return False, f"Amount USD {amount} < $2", None, None, None
    app_m=re.search(r'CI\d{6}\.\d{3,4}\.T\d{6,10}', upper)
    if not app_m: return False, "Invalid Code Format", None, None, None
    txn_id=app_m.group(0)
    if hash_txn(txn_id) in used_txns: return False, f"ALREADY USED {txn_id}", None, None, None
    today = datetime.now().date()
    today_str = today.strftime('%d/%m/%Y')
    dm=re.search(r'CI(\d{2})(\d{2})(\d{2})', upper)
    if dm:
        y,mn,d=dm.groups()
        try:
            full_year=2000+int(y)
            if full_year < 2026 or full_year > 2030: return False, f"OLD {d}/{mn}/{full_year} Only 2026-2030", f"{d}/{mn}/{full_year}", txn_id, amount
            txn_date_str=f"{d}/{mn}/{full_year}"
            dt=datetime.strptime(txn_date_str, '%d/%m/%Y').date()
            if dt!= today: return False, f"OLD {txn_date_str} - TODAY {today_str} ONLY!", txn_date_str, txn_id, amount
        except: return False, "Invalid Date", None, None, None
    else: return False, "No CI date", None, None, None
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
            sent=False
            for f in files:
                if vtype.lower() in f.lower() or f.split('.')[0].lower() in vtype.lower():
                    with open(f"configs/{f}",'rb') as doc:
                        bot.send_document(uid, doc, caption=f"✅ {vtype} $2\nTxn:{txn_id}\nDate:{txn_date}")
                    sent=True; break
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
        if uid!= ADMIN_ID: bot.send_message(ADMIN_ID, f"Error {e}")

def show_vpn_menu(chat_id):
    markup=InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("1. HA Tunnel Plus - $2", callback_data="buy_HA Tunnel Plus"))
    markup.add(InlineKeyboardButton("2. HTTP Custom - $2", callback_data="buy_HTTP Custom"))
    markup.add(InlineKeyboardButton("3. HTTP Injector (EHI) - $2", callback_data="buy_EHI"))
    markup.add(InlineKeyboardButton("4. NapsternetV (NPV) - $2", callback_data="buy_NPV"))
    markup.add(InlineKeyboardButton("5. Stark VPN - $2", callback_data="buy_STARK"))
    markup.add(InlineKeyboardButton("6. Dark Tunnel - $2", callback_data="buy_DARK"))
    markup.add(InlineKeyboardButton("7. TLS Tunnel - $2", callback_data="buy_TLS"))
    markup.add(InlineKeyboardButton("8. SocksIP Tunnel - $2", callback_data="buy_SocksIP
