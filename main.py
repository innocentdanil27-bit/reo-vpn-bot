import os, telebot, re, hashlib, json, threading, calendar
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8579468852"))
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

pending = {}; blocked = set(); used_txns = set(); transactions_log = []
BACKUP_FILE = "transactions_backup.json"
if os.path.exists(BACKUP_FILE):
    try:
        with open(BACKUP_FILE,'r') as f:
            d=json.load(f); transactions_log=d.get("logs",[]); used_txns=set(d.get("used_txns",[]))
    except: pass

def save_backup():
    with open(BACKUP_FILE,'w') as f: json.dump({"logs":transactions_log,"used_txns":list(used_txns)},f)
def hash_txn(t): return hashlib.sha256(t.encode()).hexdigest()[:20]
def get_files():
    if not os.path.exists("configs"): return []
    return [f for f in os.listdir("configs") if not f.startswith('.')]
def get_harare_time():
    utc_now = datetime.now(timezone.utc)
    harare_now = utc_now + timedelta(hours=2)
    today = harare_now.date()
    return {
        "datetime": harare_now,
        "date": today,
        "date_str": today.strftime('%d/%m/%Y'),
        "time_str": harare_now.strftime('%H:%M:%S'),
        "day_name": harare_now.strftime('%A'),
        "month_name": harare_now.strftime('%B'),
        "year": today.year,
        "is_leap": calendar.isleap(today.year),
        "full": harare_now.strftime('%A, %d %B %Y %H:%M:%S CAT')
    }

def confirm_payment(text):
    upper=text.upper(); lower=text.lower()
    if not text.startswith("Cashin Confirmation:"): return False, "Must forward REAL EcoCash SMS", None, None, None
    if "received from" not in lower: return False, "Fake! Missing 'received from'", None, None, None
    if "approval code:" not in lower: return False, "Fake! Missing Approval Code", None, None, None
    if "new balance:" not in lower: return False, "Fake! Missing New Balance", None, None, None
    if "transact using the super app" not in lower: return False, "Fake! Missing Super App line", None, None, None
    amt_m=re.search(r'USD\s*\$?\s*(\d+\.?\d*)', upper)
    if not amt_m: return False, "No USD amount", None, None, None
    amount=float(amt_m.group(1))
    if amount < 2.0: return False, f"Amount USD {amount} < $2", None, None, None
    app_m=re.search(r'CI\d{6}\.\d{3,4}\.T\d{6,10}', upper)
    if not app_m: return False, "Invalid Code Format", None, None, None
    txn_id=app_m.group(0)
    if hash_txn(txn_id) in used_txns: return False, f"ALREADY USED {txn_id} - BLOCKED", None, None, None
    dm=re.search(r'CI(\d{2})(\d{2})(\d{2})', upper)
    if not dm: return False, "No CI date", None, None, None
    y,mn,d=dm.groups()
    try:
        yy=int(y); mm=int(mn); dd=int(d)
        full_year=2000+yy
        ht=get_harare_time()
        today=ht["date"]
        today_str=ht["date_str"]
        if full_year < 2026 or full_year > 2030: return False, f"OLD YEAR {dd:02d}/{mm:02d}/{full_year} - 2026-2030 ONLY!", f"{dd:02d}/{mm:02d}/{full_year}", txn_id, amount
        if mm < 1 or mm > 12: return False, f"INVALID MONTH {mm}", f"{dd:02d}/{mm:02d}/{full_year}", txn_id, amount
        first_wd, max_days = calendar.monthrange(full_year, mm)
        month_name = calendar.month_name[mm]
        first_day_name = calendar.day_name[first_wd]
        if dd < 1 or dd > max_days: return False, f"FAKE DATE! {dd:02d}/{mm:02d}/{full_year} {month_name} has only {max_days} days! Starts {first_day_name}!", f"{dd:02d}/{mm:02d}/{full_year}", txn_id, amount
        txn_date_obj = datetime(full_year, mm, dd).date()
        txn_date_str = txn_date_obj.strftime('%d/%m/%Y')
        txn_day_name = calendar.day_name[txn_date_obj.weekday()]
        if txn_date_obj!= today:
            if txn_date_obj < today: return False, f"OLD RECEIPT! {txn_day_name} {txn_date_str} - TODAY {ht['day_name']} {today_str} ONLY!", txn_date_str, txn_id, amount
            else: return False, f"FUTURE DATE! {txn_date_str} {txn_day_name} - Today {today_str}", txn_date_str, txn_id, amount
        time_match = re.search(r'(\d{1,2}):(\d{2})', text)
        sms_time = time_match.group(0) if time_match else "No time"
    except ValueError as ve: return False, f"CALENDAR ERROR: {ve}", None, None, None
    return True, f"CONFIRMED USD {amount} - {txn_day_name} {txn_date_str} - Calendar verified!", txn_date_str, txn_id, amount

def send_file(uid, vtype, txn_id, txn_date, amount, username=""):
    files=get_files(); used_txns.add(hash_txn(txn_id))
    try:
        ht=get_harare_time()
        if vtype=="FAMILY":
            for f in files:
                with open(f"configs/{f}",'rb') as doc: bot.send_document(uid, doc, caption=f"Family Pack $2 {txn_date} {ht['day_name']} {ht['time_str']} {txn_id}")
        else:
            sent=False
            for f in files:
                if vtype.lower() in f.lower():
                    with open(f"configs/{f}",'rb') as doc: bot.send_document(uid, doc, caption=f"{vtype} $2 {txn_date} {ht['day_name']} {ht['time_str']} {txn_id}")
                    sent=True; break
            if not sent and files:
                with open(f"configs/{files[0]}",'rb') as doc: bot.send_document(uid, doc, caption=f"{vtype} $2 {txn_date}")
        bot.send_message(uid, f"💚 PAYMENT CONFIRMED!\n✅ {vtype}\n💰 USD {amount}\n📅 {txn_date} {ht['day_name']}\n⏰ {ht['time_str']} CAT\n🧾 {txn_id}\n📥 File sent! /myvpn to redownload")
        pending.pop(uid,None)
        transactions_log.append({"user":uid,"username":username,"app":vtype,"txn_id":txn_id,"txn_date":txn_date,"day":ht['day_name'],"time":ht['time_str'],"full":ht['full'],"amount":amount})
        save_backup()
        if uid!= ADMIN_ID: bot.send_message(ADMIN_ID, f"NEW SALE $2! {vtype} {uid} @{username} {txn_date} {ht['day_name']} {ht['time_str']} {txn_id} Total {len(transactions_log)}")
    except Exception as e:
        if uid!= ADMIN_ID: bot.send_message(ADMIN_ID, f"Error {e}")

def show_vpn_menu(chat_id):
    markup=InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("1. HA Tunnel Plus - $2 🔥", callback_data="buy_HA Tunnel Plus"))
    markup.add(InlineKeyboardButton("2. HTTP Custom - $2 ⚡", callback_data="buy_HTTP Custom"))
    markup.add(InlineKeyboardButton("3. HTTP Injector (EHI) - $2", callback_data="buy_EHI"))
    markup.add(InlineKeyboardButton("4. NapsternetV (NPV) - $2 🚀", callback_data="buy_NPV"))
    markup.add(InlineKeyboardButton("5. Stark VPN - $2 🌟", callback_data="buy_STARK"))
    markup.add(InlineKeyboardButton("6. Dark Tunnel - $2 🌙", callback_data="buy_DARK"))
    markup.add(InlineKeyboardButton("7. TLS Tunnel - $2 🔒", callback_data="buy_TLS"))
    markup.add(InlineKeyboardButton("8. SocksIP Tunnel - $2 🧦", callback_data="buy_SocksIP"))
    markup.add(InlineKeyboardButton("9. NetMod / SocksHttp - $2 🛠️", callback_data="buy_NETMOD"))
    markup.add(InlineKeyboardButton("10. Family Pack (All Apps) - $2 🔥 BEST DEAL", callback_data="buy_FAMILY"))
    ht=get_harare_time()
    bot.send_message(chat_id, f"🚀 REO VPN BOT - {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n⭐ 500+ Customers | Calendar Verified\nWE ARE SELLING:\n1 HA Tunnel Plus\n2 HTTP Custom\n3 HTTP Injector\n4 NapsternetV\n5 Stark VPN\n6 Dark Tunnel\n7 TLS Tunnel\n8 SocksIP Tunnel\n9 NetMod\n10 Family Pack ALL $2\nPay: EcoCash 0775713879 Danil\nTODAY ONLY Calendar checks!", reply_markup=markup)

@app.route('/')
def home():
    ht=get_harare_time()
    return f"LIVE {ht['full']} - {len(transactions_log)} sales"

@bot.message_handler(commands=['start','buy'])
def cmd_start(m):
    if m.from_user.id in blocked: return
    show_vpn_menu(m.chat.id)

@bot.message_handler(commands=['price'])
def cmd_price(m):
    ht=get_harare_time()
    bot.send_message(m.chat.id, f"PRICE - {ht['day_name']} {ht['date_str']} {ht['time_str']}\nALL VPNs $2\n1 HA Tunnel Plus\n2 HTTP Custom\n3 HTTP Injector\n4 NapsternetV\n5 Stark VPN\n6 Dark Tunnel\n7 TLS Tunnel\n8 SocksIP Tunnel\n9 NetMod\n10 Family Pack ALL $2 BEST DEAL\nPay 0775713879 /buy")

@bot.message_handler(commands=['support'])
def cmd_support(m):
    ht=get_harare_time()
    bot.send_message(m.chat.id, f"SUPPORT\nDanil\n0775713879\n{ht['full']}\n24/7 CAT")

@bot.message_handler(commands=['help'])
def cmd_help(m):
    ht=get_harare_time()
    bot.send_message(m.chat.id, f"HOW TO BUY - {ht['day_name']} {ht['date_str']}\n1 /buy\n2 Pick VPN\n3 Pay $2 to 0775713879\n4 Forward REAL SMS\n5 File instant!\nMust be TODAY {ht['date_str']} {ht['day_name']}\nNow: {ht['time_str']} CAT")

@bot.message_handler(commands=['about'])
def cmd_about(m):
    ht=get_harare_time()
    bot.send_message(m.chat.id, f"ABOUT REO\nToday: {ht['full']}\nMonth {ht['month_name']} has {calendar.monthrange(ht['year'], ht['date'].month)[1]} days\nLeap: {ht['is_leap']}\n500+ Customers\nOwner Danil")

@bot.message_handler(commands=['status'])
def cmd_status(m):
    ht=get_harare_time()
    if m.from_user.id in pending: bot.send_message(m.chat.id, f"Waiting {pending[m.from_user.id]} {ht['day_name']} {ht['date_str']} {ht['time_str']} Pay $2 to 0775713879")
    else: bot.send_message(m.chat.id, f"No pending {ht['day_name']} {ht['date_str']} {ht['time_str']} /buy")

@bot.message_handler(commands=['myvpn'])
def cmd_myvpn(m):
    ht=get_harare_time()
    my=[t for t in transactions_log if t['user']==m.from_user.id]
    if not my: bot.send_message(m.chat.id, f"No purchases {ht['day_name']} {ht['date_str']} /buy"); return
    last=my[-1]; bot.send_message(m.chat.id, f"Last: {last['app']} {last['txn_date']} {last.get('day','')} {last.get('time','')} Now: {ht['time_str']} Resending...")
    files=get_files()
    for f in files:
        if last['app'].lower() in f.lower() or last['app']=="FAMILY":
            with open(f"configs/{f}",'rb') as doc: bot.send_document(m.chat.id, doc)
            if last['app']!="FAMILY": break

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    if c.data.startswith("buy_"):
        vtype=c.data.replace("buy_",""); pending[c.from_user.id]=vtype
        ht=get_harare_time()
        bot.send_message(c.message.chat.id, f"{vtype} - $2 0775713879 TODAY {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT Calendar checks! Forward REAL SMS!")

@bot.message_handler(content_types=['text'])
def txt(m):
    if m.text.startswith('/'): return
    if m.from_user.id not in pending: return
    valid, reason, txn_date, txn_id, amount = confirm_payment(m.text)
    if valid:
        bot.send_message(m.chat.id, f"{reason} {txn_id}")
        send_file(m.from_user.id, pending[m.from_user.id], txn_id, txn_date, amount, m.from_user.username or "")
    else:
        if "ALREADY USED" in reason: blocked.add(m.from_user.id); save_backup()
        if len(m.text)>15: bot.send_message(m.chat.id, f"{reason}")

def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
if __name__=="__main__":
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
