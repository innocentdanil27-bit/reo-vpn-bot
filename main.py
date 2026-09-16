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
    dm=re.search(r'CI(\d{2})(\d{2})(\d{2})
