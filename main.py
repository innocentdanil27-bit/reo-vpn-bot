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
    if "received from" not in lower: return False, "Fake SMS", None, None, None
    if "approval code:" not in lower: return False, "Missing Approval Code", None, None, None
    if "new balance:" not in lower: return False, "Missing New Balance", None, None, None
    if "transact using the super app" not in lower: return False, "Missing Super App line", None, None, None
    amt_m=re.search(r'USD\s*\$?\s*(\d+\.?\d*)', upper)
    if not amt_m: return False, "No USD amount", None, None, None
    amount=float(amt_m.group(1))
    if amount < 2.0: return False, f"USD {amount} < $2", None, None, None
    app_m=re.search(r'CI\d{6}\.\d{3,4}\.T\d{6,10}', upper)
    if not app_m: return False, "Invalid Code", None, None, None
    txn_id=app_m.group(0)
    if hash_txn(txn_id) in used_txns: return False, f"ALREADY USED {txn_id} - BLOCKED", None, None, None
    dm=re.search(r'CI(\d{2})(\d{2})(\d{2})', upper)
    if not dm: return False, "No CI date", None, None, None
    y,mn,d=dm.groups()
    try:
        yy=int(y); mm=int(mn); dd=int(d)
        full_year=2000+yy
        ht=get_harare_time()
        if full_year < 2026 or full_year > 2030: return False, f"OLD YEAR {full_year} - 2026-2030 only", f"{dd:02d}/{mm:02d}/{full_year}", txn_id, amount
        if mm < 1 or mm > 12: return False, f"Invalid month {mm}", f"{dd:02d}/{mm:02d}/{full_year}", txn_id, amount
        _, max_days = calendar.monthrange(full_year, mm)
        if dd < 1 or dd > max_days: return False, f"FAKE DATE {dd:02d}/{mm:02d}/{full_year} {calendar.month_name[mm]} has {max_days} days only!", f"{dd:02d}/{mm:02d}/{full_year}", txn_id, amount
        txn_date_obj = datetime(full_year, mm, dd).date()
        txn_date_str = txn_date_obj.strftime('%d/%m/%Y')
        if txn_date_obj!= ht["date"]: return False, f"OLD RECEIPT {txn_date_str} - TODAY {ht['date_str']} {ht['day_name']} ONLY!", txn_date_str, txn_id, amount
    except: return False, "Calendar error", None, None, None
    return True, f"CONFIRMED USD {amount} - {txn_date_str} {calendar.day_name[txn_date_obj.weekday()]}", txn_date_str, txn_id, amount

def send_file(uid, vtype, txn_id, txn_date, amount, username=""):
    files=get_files(); used_txns.add(hash_txn(txn_id))
    try:
        ht=get_harare_time()
        if vtype=="FAMILY":
            for f in files:
                with open(f"configs/{f}",'rb') as doc: bot.send_document(uid, doc, caption=f"✅ Family Pack $2 {txn_date} {ht['day_name']} {txn_id}")
        else:
            sent=False
            for f in files:
                if vtype.lower() in f.lower():
                    with open(f"configs/{f}",'rb') as doc: bot.send_document(uid, doc, caption=f"✅ {vtype} $2 {txn_date} {txn_id}")
                    sent=True; break
            if not sent and files:
                with open(f"configs/{files[0]}",'rb') as doc: bot.send_document(uid, doc, caption=f"✅ {vtype} $2 {txn_date}")
        bot.send_message(uid, f"💚 CONFIRMED!\n✅ {vtype}\n💰 ${amount}\n📅 {txn_date} {ht['day_name']} {ht['time_str']} CAT\n🧾 {txn_id}\n📥 File sent!\n🔄 /myvpn to redownload\n📞 /support for help")
        pending.pop(uid,None)
        transactions_log.append({"user":uid,"username":username,"app":vtype,"txn_id":txn_id,"txn_date":txn_date,"day":ht['day_name'],"time":ht['time_str'],"amount":amount})
        save_backup()
        if uid!= ADMIN_ID: bot.send_message(ADMIN_ID, f"🔔 SALE $2 {vtype} {uid} @{username} {txn_date} {ht['day_name']} {txn_id} Total {len(transactions_log)}")
    except Exception as e:
        if uid!= ADMIN_ID: bot.send_message(ADMIN_ID, f"Error {e}")

# ===== VPN MENU =====
def show_vpn_menu(chat_id):
    markup=InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("1️⃣ HA Tunnel Plus - $2 🔥 Popular", callback_data="buy_HA Tunnel Plus"))
    markup.add(InlineKeyboardButton("2️⃣ HTTP Custom - $2 ⚡ Fast", callback_data="buy_HTTP Custom"))
    markup.add(InlineKeyboardButton("3️⃣ HTTP Injector (EHI) - $2 💉", callback_data="buy_EHI"))
    markup.add(InlineKeyboardButton("4️⃣ NapsternetV (NPV) - $2 🚀", callback_data="buy_NPV"))
    markup.add(InlineKeyboardButton("5️⃣ Stark VPN - $2 🌟", callback_data="buy_STARK"))
    markup.add(InlineKeyboardButton("6️⃣ Dark Tunnel - $2 🌙", callback_data="buy_DARK"))
    markup.add(InlineKeyboardButton("7️⃣ TLS Tunnel - $2 🔒", callback_data="buy_TLS"))
    markup.add(InlineKeyboardButton("8️⃣ SocksIP Tunnel - $2 🧦 Gaming", callback_data="buy_SocksIP"))
    markup.add(InlineKeyboardButton("9️⃣ NetMod - $2 🛠️ Pro", callback_data="buy_NETMOD"))
    markup.add(InlineKeyboardButton("🔥 FAMILY PACK - ALL 9 VPNs - $2 BEST DEAL", callback_data="buy_FAMILY"))
    ht=get_harare_time()
    bot.send_message(chat_id, f"🚀 REO VPN - {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n⭐ 500+ Certified Customers\n📅 {ht['month_name']} {ht['year']} - Calendar Verified\n\nWE SELL:\n1 HA Tunnel Plus - Econet 100%\n2 HTTP Custom - Streaming\n3 HTTP Injector - Gaming\n4 NapsternetV - Fastest\n5 Stark VPN - 1 Click\n6 Dark Tunnel - No DC\n7 TLS Tunnel - Secure\n8 SocksIP - PUBG/CoD\n9 NetMod - Pro\n10 Family Pack ALL $2\n\n💳 EcoCash 0775713879 Danil\n📅 TODAY ONLY - Calendar checks day!", reply_markup=markup)

@app.route('/')
def home():
    ht=get_harare_time()
    return f"LIVE {ht['full']} - {len(transactions_log)} sales"

# ===== 8 COMMANDS - CERTIFIED ANSWERS =====

@bot.message_handler(commands=['start'])
def cmd_start(m):
    if m.from_user.id in blocked: bot.send_message(m.chat.id, "🚫 Blocked. Contact /support"); return
    ht=get_harare_time()
    bot.send_message(m.chat.id, f"👋 Welcome to REO VPN - Certified Shop!\n\n"
        f"📅 Today: {ht['day_name']} {ht['date_str']}\n"
        f"⏰ Time: {ht['time_str']} CAT Harare\n"
        f"📆 {ht['month_name']} {ht['year']} | Leap: {ht['is_leap']}\n\n"
        f"⭐ 500+ Happy Customers Certified\n"
        f"⚡ Instant Auto Delivery\n"
        f"🛡️ Money Back Guarantee\n"
        f"✅ Calendar Verified Payments\n\n"
        f"👇 Choose your VPN below - All $2:")
    show_vpn_menu(m.chat.id)

@bot.message_handler(commands=['buy'])
def cmd_buy(m):
    if m.from_user.id in blocked: bot.send_message(m.chat.id, "🚫 Blocked. Contact /support"); return
    ht=get_harare_time()
    bot.send_message(m.chat.id, f"🛒 REO SHOP - Ready to Buy - Certified!\n📅 {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\nPick your VPN - All $2 - Instant file:")
    show_vpn_menu(m.chat.id)

@bot.message_handler(commands=['price'])
def cmd_price(m):
    ht=get_harare_time()
    bot.send_message(m.chat.id, f"💰 REO CERTIFIED PRICE LIST\n"
        f"📅 {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n"
        f"📆 {ht['month_name']} {ht['year']} - {calendar.monthrange(ht['year'], ht['date'].month)[1]} days in month\n\n"
        f"✅ ALL VPNs $2 EACH - CERTIFIED PRICE:\n\n"
        f"1️⃣ HA Tunnel Plus - $2 🔥 BEST - 100% Econet, Streaming, Gaming\n"
        f"2️⃣ HTTP Custom - $2 ⚡ - Fast, Stable, No Buffer\n"
        f"3️⃣ HTTP Injector (EHI) - $2 - Classic, Gaming, PUBG\n"
        f"4️⃣ NapsternetV (NPV) - $2 🚀 - 2026 Fastest, New Protocol\n"
        f"5️⃣ Stark VPN Reloaded - $2 - Simple 1-Click Connect\n"
        f"6️⃣ Dark Tunnel - $2 - Unlimited, No Disconnect\n"
        f"7️⃣ TLS Tunnel - $2 - Secure, Encrypted\n"
        f"8️⃣ SocksIP Tunnel - $2 - Best for CoD, Free Fire\n"
        f"9️⃣ NetMod / SocksHttp - $2 - Pro Users, Custom\n"
        f"🔟 FAMILY PACK - ALL 9 VPNs - $2 🔥 - BEST DEAL, You get all files!\n\n"
        f"💳 Payment: EcoCash 0775713879 - Danil\n"
        f"⚡ Delivery: Instant after SMS verification\n"
        f"🛡️ Guarantee: Money back if not working\n"
        f"📦 Files:.hat,.hc,.ehi,.npv,.tls etc\n\n"
        f"👉 Type /buy to order now - Certified shop!")

@bot.message_handler(commands=['support'])
def cmd_support(m):
    ht=get_harare_time()
    bot.send_message(m.chat.id, f"📞 REO CERTIFIED SUPPORT - 24/7 ONLINE\n"
        f"📅 {ht['full']}\n\n"
        f"👤 Owner: Danil - Harare\n"
        f"📱 EcoCash: 0775713879\n"
        f"🤖 Bot: @reo_products_bot\n"
        f"⏰ Hours: 24/7 CAT (Harare Time)\n"
        f"📆 Today is {ht['day_name']} - We are open!\n\n"
        f"✅ CERTIFIED HELP:\n"
        f"• File not connecting? Send screenshot\n"
        f"• Payment not verified? Forward REAL EcoCash SMS\n"
        f"• Need setup guide? Type /help\n"
        f"• Want refund? We give money back guarantee\n\n"
        f"⚡ Response time: 2-5 minutes\n"
        f"💬 Just reply here - Danil will answer!\n\n"
        f"Type /buy to buy VPN $2")

@bot.message_handler(commands=['help'])
def cmd_help(m):
    ht=get_harare_time()
    bot.send_message(m.chat.id, f"📲 REO CERTIFIED BUYING GUIDE\n"
        f"📅 {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n"
        f"📆 {ht['month_name']} has {calendar.monthrange(ht['year'], ht['date'].month)[1]} days - Calendar verified\n\n"
        f"✅ 5 EASY STEPS TO GET VPN - CERTIFIED:\n\n"
        f"1️⃣ Type /buy - See all 10 VPNs\n"
        f"2️⃣ Tap your VPN (e.g HA Tunnel Plus)\n"
        f"3️⃣ Pay $2 to EcoCash 0775713879 - Name: Danil\n"
        f" • Dial *153# or use EcoCash App\n"
        f" • Send exactly $2.00\n"
        f"4️⃣ Forward REAL EcoCash SMS from EcoCash inbox to this bot.\n"
        f" SMS must look like:\n"
        f" Cashin Confirmation: USD $2.00 received from...\n"
        f" Approval Code: CI{ht['date'].strftime('%y%m%d')}.xxxx.Txxxxxx\n"
        f" New balance: USD $...\n"
        f" Transact using the Super App\n"
        f" • Must be TODAY {ht['date_str']} {ht['day_name']} - Yesterday rejected by calendar!\n"
        f" • Must be $2.00 - $1.50 rejected!\n"
        f"5️⃣ Bot checks calendar + day + time and sends file INSTANTLY ✅\n\n"
        f"❌ DON'T TYPE 'I paid' - Must forward SMS\n"
        f"❌ DON'T send screenshot - Forward text SMS\n"
        f"❌ DON'T use old receipt - Only TODAY allowed\n\n"
        f"✅ After payment you get:\n"
        f"• VPN config file (.hat,.hc etc)\n"
        f"• Setup instructions\n"
        f"• Support 24/7\n\n"
        f"Need help? /support - We are certified!")

@bot.message_handler(commands=['about'])
def cmd_about(m):
    ht=get_harare_time()
    bot.send_message(m.chat.id, f"⭐ ABOUT REO PRODUCTS - CERTIFIED SHOP\n"
        f"📅 Today: {ht['full']}\n"
        f"📆 Month: {ht['month_name']} {ht['year']} - {calendar.monthrange(ht['year'], ht['date'].month)[1]} days - Calendar library verified\n"
        f"🔄 Leap Year: {ht['is_leap']} - Feb has {29 if ht['is_leap'] else 28} days\n\n"
        f"✅ CERTIFIED BY 500+ CUSTOMERS:\n"
        f"• Serving since 2024 - Harare, Zimbabwe\n"
        f"• 500+ Happy Customers - Check reviews\n"
        f"• Instant Auto Delivery - No waiting for admin\n"
        f"• 100% Secure - Calendar verified payments, No reuse\n"
        f"• Money Back Guarantee - If VPN not working, we refund\n"
        f"• Works: Econet, TelOne, Liquid, NetOne\n"
        f"• Fast Servers - No buffering, Gaming supported\n\n"
        f"👤 Founder: Danil - Harare\n"
        f"🏆 Best VPN Seller in ZW 2026 - Certified\n"
        f"🛡️ Bot uses Python calendar.monthrange() to reject fake dates like Feb 31\n"
        f"⏰ Timezone: Harare CAT UTC+2 - Correct date for ZW\n\n"
        f"💰 All VPNs $2 - Family Pack $2 Best Deal!\n"
        f"Type /buy to join 500+ certified customers!")

@bot.message_handler(commands=['status'])
def cmd_status(m):
    ht=get_harare_time()
    if m.from_user.id in pending:
        bot.send_message(m.chat.id, f"⏳ PAYMENT PENDING - CERTIFIED CHECK\n"
            f"📅 Today: {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n"
            f"📱 Your Order: {pending[m.from_user.id]}\n"
            f"💰 Amount: $2.00\n"
            f"💳 Pay to: EcoCash 0775713879 - Danil\n"
            f"📆 Calendar: {ht['month_name']} {ht['year']} has {calendar.monthrange(ht['year'], ht['date'].month)[1]} days\n\n"
            f"After pay, forward REAL EcoCash SMS here.\n"
            f"Must be TODAY {ht['date_str']} - Yesterday rejected!\n"
            f"Bot will verify day {ht['day_name']} + date + time\n"
            f"Then send file instantly ✅\n\n"
            f"Need help? /help")
    else:
        bot.send_message(m.chat.id, f"✅ NO PENDING PAYMENT - CERTIFIED STATUS\n"
            f"📅 Today: {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n"
            f"📆 {ht['month_name']} {ht['year']} - Day {ht['date'].day} of {calendar.monthrange(ht['year'], ht['date'].month)[1]}\n\n"
            f"You haven't ordered yet or your payment was already confirmed and file sent.\n\n"
            f"✅ To buy new VPN: Type /buy\n"
            f"📦 To see your old purchases: Type /myvpn\n"
            f"📞 Need help? /support")

@bot.message_handler(commands=['myvpn'])
def cmd_myvpn(m):
    ht=get_harare_time()
    my=[t for t in transactions_log if t['user']==m.from_user.id]
    if not my:
        bot.send_message(m.chat.id, f"❌ NO PURCHASES YET - CERTIFIED SHOP\n"
            f"📅 Today: {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n\n"
            f"You haven't bought any VPN yet.\n\n"
            f"✅ CERTIFIED OFFER:\n"
            f"• All Single VPNs $2\n"
            f"• Family Pack ALL 9 VPNs $2 - BEST DEAL!\n"
            f"• Instant delivery\n"
            f"• Money back guarantee\n\n"
            f"Type /buy to buy your first VPN and join 500+ certified customers!")
        return
    last=my[-1]
    bot.send_message(m.chat.id, f"📦 YOUR CERTIFIED VPNs - {ht['day_name']} {ht['date_str']}\n"
        f"⏰ Now: {ht['time_str']} CAT\n\n"
        f"✅ Total Purchases: {len(my)} - Certified Customer!\n"
        f"📱 Last Purchase: {last['app']}\n"
        f"📅 Date: {last['txn_date']} {last.get('day','')}\n"
        f"⏰ Time: {last.get('time','')}\n"
        f"🧾 Txn: {last['txn_id']}\n\n"
        f"📥 Resending your last file now - Certified redownload service...\n"
        f"💡 Tip: Family Pack gives you ALL VPNs for $2!")
    files=get_files()
    for f in files:
        if last['app'].lower() in f.lower() or last['app']=="FAMILY":
            try:
                with open(f"configs/{f}",'rb') as doc: bot.send_document(m.chat.id, doc, caption=f"✅ {last['app']} - Certified Redownload {last['txn_date']}")
            except: pass
            if last['app']!="FAMILY": break

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    if c.data.startswith("buy_"):
        vtype=c.data.replace("buy_","")
        pending[c.from_user.id]=v
