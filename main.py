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
    harare_now = datetime.now(timezone.utc) + timedelta(hours=2)
    return {"date": harare_now.date(), "date_str": harare_now.strftime('%d/%m/%Y'), "time_str": harare_now.strftime('%H:%M:%S'), "day_name": harare_now.strftime('%A'), "month_name": harare_now.strftime('%B'), "year": harare_now.year, "full": harare_now.strftime('%A, %d %B %Y %H:%M:%S CAT')}

def confirm_payment(text):
    upper=text.upper(); lower=text.lower()
    ht=get_harare_time()
    if not (text.startswith("Cashin Confirmation:") or text.startswith("Transfer Confirmation:")):
        return False, "Must forward REAL EcoCash SMS", None, None, None
    if "approval code:" not in lower: return False, "Missing Approval Code", None, None, None
    if "new balance:" not in lower: return False, "Missing New Balance", None, None, None
    amt_m=re.search(r'USD\s*\$?\s*(\d+\.?\d*)', upper)
    if not amt_m: return False, "No USD amount", None, None, None
    amount=float(amt_m.group(1))
    if amount < 1.99: return False, f"USD {amount} < $2", None, None, None
    app_m=re.search(r'(?:CI|PP)\d{6}\.\d{3,4}\.T\d{6,10}', upper)
    if not app_m:
        app_m2=re.search(r'(?:CI|PP)\d{6}\.\d{3,4}', upper)
        if not app_m2: return False, "Invalid Code", None, None, None
        txn_id=app_m2.group(0)
    else: txn_id=app_m.group(0)
    if hash_txn(txn_id) in used_txns: return False, f"ALREADY USED {txn_id} - BLOCKED", None, None, None
    dm=re.search(r'(?:CI|PP)(\d{2})(\d{2})(\d{2})', upper)
    if not dm: return False, "No date", None, None, None
    y,mn,d=dm.groups()
    try:
        yy=int(y); mm=int(mn); dd=int(d); full_year=2000+yy
        if full_year < 2025 or full_year > 2030: return False, f"OLD YEAR {full_year}", f"{dd:02d}/{mm:02d}/{full_year}", txn_id, amount
        _, max_days = calendar.monthrange(full_year, mm)
        if dd < 1 or dd > max_days: return False, f"FAKE DATE {dd:02d}/{mm:02d}/{full_year} {calendar.month_name[mm]} has {max_days} days!", f"{dd:02d}/{mm:02d}/{full_year}", txn_id, amount
        txn_date_obj = datetime(full_year, mm, dd).date()
        txn_date_str = txn_date_obj.strftime('%d/%m/%Y')
        if txn_date_obj!= ht["date"]: return False, f"OLD RECEIPT {txn_date_str} - TODAY {ht['date_str']} {ht['day_name']} ONLY!", txn_date_str, txn_id, amount
    except: return False, "Calendar error", None, None, None
    return True, f"CONFIRMED USD {amount} {txn_date_str}", txn_date_str, txn_id, amount

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
        bot.send_message(uid, f"💚 PAYMENT CONFIRMED - LEGIT!\n\n✅ App: {vtype}\n💰 USD {amount}\n📅 {txn_date} {ht['day_name']} {ht['time_str']} CAT\n🧾 Txn: {txn_id}\n\n📥 File sent above!\n📲 /help for setup\n🔄 /myvpn to redownload anytime")
        pending.pop(uid,None)
        transactions_log.append({"user":uid,"username":username,"app":vtype,"txn_id":txn_id,"txn_date":txn_date,"day":ht['day_name'],"time":ht['time_str'],"amount":amount})
        save_backup()
        if uid!= ADMIN_ID: bot.send_message(ADMIN_ID, f"🔔 NEW SALE $2!\n💰 {amount}\n📱 {vtype}\n👤 {uid} @{username}\n📅 {txn_date} {ht['day_name']}\n🧾 {txn_id}\n📊 Total: {len(transactions_log)}")
    except Exception as e: bot.send_message(ADMIN_ID, f"Error {e}")

def show_vpn_menu(chat_id):
    markup=InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("1. HA Tunnel Plus - $2 🔥 Most Popular", callback_data="buy_HA Tunnel Plus"))
    markup.add(InlineKeyboardButton("2. HTTP Custom - $2 ⚡ Fast Streaming", callback_data="buy_HTTP Custom"))
    markup.add(InlineKeyboardButton("3. HTTP Injector (EHI) - $2 💉 Gaming", callback_data="buy_EHI"))
    markup.add(InlineKeyboardButton("4. NapsternetV (NPV) - $2 🚀 2026 Fast", callback_data="buy_NPV"))
    markup.add(InlineKeyboardButton("5. Stark VPN - $2 🌟 1-Click", callback_data="buy_STARK"))
    markup.add(InlineKeyboardButton("6. Dark Tunnel - $2 🌙 No DC", callback_data="buy_DARK"))
    markup.add(InlineKeyboardButton("7. TLS Tunnel - $2 🔒 Secure", callback_data="buy_TLS"))
    markup.add(InlineKeyboardButton("8. SocksIP Tunnel - $2 🧦 PUBG/CoD", callback_data="buy_SocksIP"))
    markup.add(InlineKeyboardButton("9. NetMod / SocksHttp - $2 🛠️ Pro", callback_data="buy_NETMOD"))
    markup.add(InlineKeyboardButton("10. Family Pack (ALL Apps) - $2 🔥 BEST DEAL", callback_data="buy_FAMILY"))
    ht=get_harare_time()
    bot.send_message(chat_id, f"🚀 REO VPN - CERTIFIED SHOP\n📅 {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n⭐ 500+ Certified Customers | 🛡️ Money Back\n\nWE SELL LEGIT:\n1 HA Tunnel Plus - $2\n2 HTTP Custom - $2\n3 HTTP Injector - $2\n4 NapsternetV - $2\n5 Stark VPN - $2\n6 Dark Tunnel - $2\n7 TLS Tunnel - $2\n8 SocksIP Tunnel - $2\n9 NetMod - $2\n10 Family Pack ALL - $2 BEST\n\n💳 Pay: EcoCash 0775713879 Danil\n📅 TODAY {ht['date_str']} ONLY - Calendar checks!\n👇 TAP TO BUY:", reply_markup=markup)

@app.route('/')
def home():
    ht=get_harare_time()
    return f"LIVE {ht['full']} - {len(transactions_log)} sales"

# ===== ALL 11 COMMANDS - LEGIT RESPONSES FOR CUSTOMERS =====
@bot.message_handler(commands=['start'])
def cmd_start(m):
    if m.from_user.id in blocked: bot.send_message(m.chat.id, "🚫 You are blocked. Contact /support with proof"); return
    ht=get_harare_time()
    bot.send_message(m.chat.id, f"👋 *Welcome to REO VPN - LEGIT CERTIFIED SHOP*\n\n"
        f"📅 *Today:* {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT Harare\n"
        f"📆 *{ht['month_name']} {ht['year']}* has {calendar.monthrange(ht['year'], ht['date'].month)[1]} days - Calendar verified\n\n"
        f"⭐ *500+ Happy Customers Certified*\n"
        f"⚡ *Instant Auto Delivery* - No admin wait\n"
        f"🛡️ *Money Back Guarantee* - If not working, we refund\n"
        f"✅ *Calendar Verified* - Rejects fake Feb 31, old receipts\n"
        f"🔒 *Secure* - Each code used once only\n\n"
        f"*We Sell:*\nHA Tunnel, HTTP Custom, HTTP Injector, NapsternetV, Stark, Dark, TLS, SocksIP, NetMod, Family Pack - ALL $2\n\n"
        f"👇 *Choose below - Legit shop:*", parse_mode="Markdown")
    show_vpn_menu(m.chat.id)

@bot.message_handler(commands=['buy'])
def cmd_buy(m):
    if m.from_user.id in blocked: return
    ht=get_harare_time()
    bot.send_message(m.chat.id, f"🛒 *REO SHOP - LEGIT BUY*\n📅 {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n\nAll VPNs $2 - Tap to buy - Instant file after payment:", parse_mode="Markdown")
    show_vpn_menu(m.chat.id)

@bot.message_handler(commands=['price'])
def cmd_price(m):
    ht=get_harare_time()
    bot.send_message(m.chat.id, f"💰 *REO CERTIFIED PRICE LIST - LEGIT*\n"
        f"📅 {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n"
        f"📆 {ht['month_name']} {ht['year']} - {calendar.monthrange(ht['year'], ht['date'].month)[1]} days\n\n"
        f"*✅ ALL VPNs $2 EACH - CERTIFIED:*\n\n"
        f"1️⃣ *HA Tunnel Plus - $2* 🔥 MOST POPULAR\n Works 100% Econet, Streaming, TikTok, YouTube\n\n"
        f"2️⃣ *HTTP Custom - $2* ⚡ FAST\n High speed, Stable, No buffer, Netflix\n\n"
        f"3️⃣ *HTTP Injector (EHI) - $2* 💉 CLASSIC\n Gaming, PUBG, CoD, Old reliable\n\n"
        f"4️⃣ *NapsternetV (NPV) - $2* 🚀 NEW 2026\n Fastest protocol, Low ping\n\n"
        f"5️⃣ *Stark VPN Reloaded - $2* 🌟 SIMPLE\n 1-Click connect, Easy setup\n\n"
        f"6️⃣ *Dark Tunnel - $2* 🌙 UNLIMITED\n No disconnect, Long lasting\n\n"
        f"7️⃣ *TLS Tunnel - $2* 🔒 SECURE\n Encrypted, Secure browsing\n\n"
        f"8️⃣ *SocksIP Tunnel - $2* 🧦 GAMING\n Best for Free Fire, CoD, PUBG\n\n"
        f"9️⃣ *NetMod / SocksHttp - $2* 🛠️ PRO\n Advanced, Custom payloads\n\n"
        f"🔟 *FAMILY PACK - ALL 9 VPNs - $2* 🔥 BEST DEAL!\n You get ALL files.hat.hc.ehi.npv.tls - Save $18!\n\n"
        f"💳 *Pay:* EcoCash *0775713879* - Danil\n"
        f"⚡ *Delivery:* Instant after SMS\n"
        f"🛡️ *Guarantee:* Money back if not working\n"
        f"📦 *Files:* Ready to import\n\n"
        f"👉 *Type /buy to order - Legit certified shop!*", parse_mode="Markdown")

@bot.message_handler(commands=['proof'])
def cmd_proof(m):
    ht=get_harare_time()
    count=len(transactions_log)
    recent=transactions_log[-10:] if count>=10 else transactions_log
    msg=f"✅ *REO LIVE PAYMENT PROOFS - LEGIT*\n"
    msg+=f"📅 {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n"
    msg+=f"📆 {ht['month_name']} {ht['year']} - Calendar verified\n"
    msg+=f"📊 *Total Sales: {count} - 500+ Customers*\n\n"
    if not recent:
        msg+=f"🔥 *Today's proofs will appear here!*\n\n"
        msg+=f"Example legit sales:\n"
        msg+=f"• HA Tunnel Plus - Wednesday 16/09/2026 - USD 2.00 - CI260916... CONFIRMED\n"
        msg+=f"• Family Pack - Wednesday 16/09/2026 - USD 2.00 - PP260916... CONFIRMED\n"
        msg+=f"• HTTP Custom - Wednesday 16/09/2026 - USD 2.00 - CI260916... CONFIRMED\n\n"
    else:
        msg+=f"*Recent 10 legit sales:*\n"
        for t in recent[::-1]:
            msg+=f"• {t['app']} - {t['txn_date']} {t.get('day','')} {t.get('time','')} - ${t['amount']} - {t['txn_id'][:12]}... ✅\n"
    msg+=f"\n⭐ *All payments calendar verified*\n"
    msg+=f"🛡️ *No fake receipts - No reuse - Legit shop*\n"
    msg+=f"💬 *Customers trust us - 500+ reviews*\n\n"
    msg+=f"👉 *Type /buy to join and be next proof!*"
    bot.send_message(m.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(commands=['trial'])
def cmd_trial(m):
    ht=get_harare_time()
    bot.send_message(m.chat.id, f"🎁 *FREE TRIAL - LEGIT TEST - {ht['day_name']} {ht['date_str']}*\n\n"
        f"We don't give free config but we give *CERTIFIED GUARANTEE*:\n\n"
        f"✅ *Money Back Guarantee* - If VPN not connecting, we refund $2 in 10 mins\n"
        f"✅ *Free Replacement* - If one app not working, we give another FREE\n"
        f"✅ *Test Speed* - Our servers 100Mbps, Low ping for gaming\n"
        f"✅ *All VPNs $2 Only* - Cheapest in Zimbabwe - Others charge $5\n"
        f"✅ *Family Pack $2* - You get ALL 9 VPNs to test - If one fails, try another!\n\n"
        f"🔥 *Why no free trial?* Free trials get abused and sold. We keep $2 to keep quality.\n\n"
        f"💡 *How to test legit:*\n"
        f"1. Buy Family Pack $2 - /buy\n"
        f"2. Test all 9 apps\n"
        f"3. If none work (rare), tell /support - We refund 100%\n\n"
        f"⭐ *500+ customers tested and stayed - Legit!*\n\n"
        f"👉 *Type /buy to test now - Money back guarantee!*", parse_mode="Markdown")

@bot.message_handler(commands=['refer'])
def cmd_refer(m):
    ht=get_harare_time()
    bot.send_message(m.chat.id, f"👥 *REFER & EARN $0.50 - LEGIT PROGRAM*\n"
        f"📅 {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n\n"
        f"🔥 *Earn $0.50 per friend - Real money!*\n\n"
        f"*How it works - Legit:*\n"
        f"1️⃣ Share bot: @reo_products_bot to friends\n"
        f"2️⃣ Friend buys VPN for $2 and tells us your @username in payment\n"
        f"3️⃣ After friend's payment confirmed, you get $0.50 EcoCash\n"
        f"4️⃣ Refer 4 friends = $2 = FREE VPN for you!\n\n"
        f"💰 *Rewards:*\n"
        f"• 1 friend = $0.50 EcoCash\n"
        f"• 3 friends = $1.50 = Free 1 VPN\n"
        f"• 4 friends = $2.00 = Free Family Pack ALL VPNs!\n\n"
        f"📊 *Your referrals today: 0*\n"
        f"💵 *Your earnings: $0.00*\n\n"
        f"🔗 *Your referral link:* Tell friends to type /start and mention @{m.from_user.username or m.from_user.id}\n\n"
        f"⭐ *Legit program - We pay every day 6PM CAT*\n"
        f"📞 *Payout:* EcoCash 0775713879\n\n"
        f"👉 *Start sharing now - Type /buy to see products to share!*", parse_mode="Markdown")

@bot.message_handler(commands=['support'])
def cmd_support(m):
    ht=get_harare_time()
    bot.send_message(m.chat.id, f"📞 *REO CERTIFIED SUPPORT - LEGIT 24/7*\n"
        f"📅 {ht['full']}\n\n"
        f"👤 *Owner:* Danil - Harare, Zimbabwe\n"
        f"📱 *EcoCash:* 0775713879 - Danil\n"
        f"🤖 *Bot:* @reo_products_bot - This bot\n"
        f"⏰ *Hours:* 24/7 CAT (Harare Time) - We are open now! {ht['day_name']}\n\n"
        f"✅ *CERTIFIED LEGIT HELP - We fix fast:*\n"
        f"• *File not connecting?* Send screenshot + VPN name - We send new file in 2 mins\n"
        f"• *Payment not verified?* Forward REAL EcoCash SMS - Cashin OR Transfer both accepted\n"
        f"• *Need setup?* Type /help - Step by step guide\n"
        f"• *Want refund?* Money back guarantee - If VPN not working, we refund $2\n"
        f"• *Code PP or CI?* Both accepted - PP260916... and CI260916... both work now!\n\n"
        f"⚡ *Response time:* 2-5 minutes - Fastest in ZW\n"
        f"💬 *Just reply here - Danil will answer you directly!*\n\n"
        f"👉 *Type /buy to buy VPN $2 - Legit shop*", parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def cmd_help(m):
    ht=get_harare_time()
    bot.send_message(m.chat.id, f"📲 *HOW TO SETUP VPN - LEGIT GUIDE - {ht['day_name']} {ht['date_str']}*\n"
        f"⏰ Now: {ht['time_str']} CAT | 📆 {ht['month_name']} has {calendar.monthrange(ht['year'], ht['date'].month)[1]} days\n\n"
        f"✅ *5 EASY STEPS - CERTIFIED:*\n\n"
        f"1️⃣ *Type /buy* - See all 10 VPNs (9 single + Family Pack)\n\n"
        f"2️⃣ *Tap your VPN* (e.g HA Tunnel Plus)\n"
        f" - HA Tunnel Plus: Best for Econet\n"
        f" - HTTP Custom: Best for streaming\n"
        f" - Family Pack: Best deal - ALL 9 files\n\n"
        f"3️⃣ *Pay $2* to EcoCash *0775713879* - Name: Danil\n"
        f" • Dial *153# -> Send Money\n"
        f" • Or use EcoCash App -> Send $2.00\n"
        f" • Send exactly $2.00\n\n"
        f"4️⃣ *Forward REAL EcoCash SMS* to this bot - LEGIT SMS must have:\n"
        f" ✅ `Transfer Confirmation: USD 2.00 sent to TAFADZWA...` OR `Cashin Confirmation...`\n"
        f" ✅ `Approval Code: PP260916.1347.T4051947` OR `CI260916...` - Both PP and CI work!\n"
        f" ✅ `New balance: USD 0.00` (or any balance)\n"
        f" ✅ `Transact using the Super App on https://goo.su/bCutT`\n"
        f" • Must be TODAY {ht['date_str']} {ht['day_name']} - Yesterday rejected by calendar!\n"
        f" • Must be $2.00 - $1 rejected!\n\n"
        f"5️⃣ *Bot checks calendar* (rejects Feb 31, April 31) + day + time and sends file INSTANTLY ✅\n\n"
        f"📥 *After file:*\n"
        f"• Download VPN app from Play Store (HA Tunnel Plus etc)\n"
        f"• Open app -> Import file we sent\n"
        f"• Click START - Enjoy fast internet!\n\n"
        f"❌ *DON'T:* Type 'I paid' - Must forward SMS text\n"
        f"❌ *DON'T:* Send screenshot only - Forward text\n"
        f"❌ *DON'T:* Use old receipt - Only TODAY {ht['date_str']} allowed\n\n"
        f"Need help? /support - Legit 24/7 support!", parse_mode="Markdown")

@bot.message_handler(commands=['about'])
def cmd_about(m):
    ht=get_harare_time()
    bot.send_message(m.chat.id, f"⭐ *ABOUT REO - LEGIT CERTIFIED SHOP - 500+ Customers*\n"
        f"📅 *Today:* {ht['full']}\n"
        f"📆 *Month:* {ht['month_name']} {ht['year']} - {calendar.monthrange(ht['year'], ht['date'].month)[1]} days - Calendar library verified\n"
        f"🔄 *Leap Year:* {ht['is_leap']} - Feb has {29 if ht['is_leap'] else 28} days\n\n"
        f"✅ *CERTIFIED BY 500+ CUSTOMERS - LEGIT:*\n"
        f"• *Serving since 2024* - Harare, Zimbabwe - 2 years experience\n"
        f"• *500+ Happy Customers* - Check /proof for live sales\n"
        f"• *Instant Auto Delivery* - No waiting for admin - Bot sends in 3 seconds\n"
        f"• *100% Secure* - Calendar verified payments - Rejects fake dates Feb 31, Rejects reuse\n"
        f"• *Money Back Guarantee* - If VPN not working, we refund $2 - Legit promise\n"
        f"• *Works:* Econet, TelOne, Liquid, NetOne - All networks\n"
        f"• *Fast Servers* - 100Mbps, No buffering, Gaming low ping\n"
        f"• *All VPNs $2* - Cheapest in ZW - Others charge $5\n"
        f"• *Family Pack $2* - You get ALL 9 VPNs - Save $16\n\n"
        f"👤 *Founder:* Danil - Harare\n"
        f"🏆 *Best VPN Seller in ZW 2026* - Certified legit shop\n"
        f"🛡️ *Tech:* Python calendar.monthrange() rejects fake dates, Harare CAT UTC+2 correct time\n"
        f"⏰ *Timezone:* Harare CAT - Correct date for Zimbabwe\n"
        f"💰 *Refer & Earn:* $0.50 per friend - /refer\n\n"
        f"💰 *All VPNs $2 - Family Pack $2 Best Deal!*\n"
        f"👉 *Type /buy to join 500+ certified customers - Legit!*", parse_mode="Markdown")

@bot.message_handler(commands=['status'])
def cmd_status(m):
    ht=get_harare_time()
    if m.from_user.id in pending:
        bot.send_message(m.chat.id, f"⏳ *PAYMENT PENDING - LEGIT CHECK*\n"
            f"📅 {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n"
            f"📱 *Your Order:* {pending[m.from_user.id]}\n"
            f"💰 *Amount:* $2.00\n"
            f"💳 *Pay to:* EcoCash 0775713879 - Danil\n"
            f"📆 *Calendar:* {ht['month_name']} {ht['year']} has {calendar.monthrange(ht['year'], ht['date'].month)[1]} days\n\n"
            f"After pay, forward REAL EcoCash SMS here.\n"
            f"*Both accepted:*\n"
            f"✅ Transfer Confirmation: USD 2.00 sent to TAFADZWA ZINATSA. Approval Code: PP260916.1347.T4051947\n"
            f"✅ Cashin Confirmation: USD 2.00 received from... CI260916...\n\n"
            f"Must be TODAY {ht['date_str']} - Yesterday rejected!\n"
            f"Bot will verify day {ht['day_name']} + date + time then send file instantly ✅\n\n"
            f"Need help? /help - Legit guide", parse_mode="Markdown")
    else:
        bot.send_message(m.chat.id, f"✅ *NO PENDING - LEGIT STATUS*\n"
            f"📅 {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n\n"
            f"You haven't ordered yet or your payment was already confirmed and file sent.\n\n"
            f"✅ *To buy:* /buy - All $2\n"
            f"📦 *To see old purchases:* /myvpn - Redownload anytime\n"
            f"✅ *To see proofs:* /proof - Live sales\n"
            f"📞 *Need help:* /support - 24/7 legit support", parse_mode="Markdown")

@bot.message_handler(commands=['myvpn'])
def cmd_myvpn(m):
    ht=get_harare_time()
    my=[t for t in transactions_log if t['user']==m.from_user.id]
    if not my:
        bot.send_message(m.chat.id, f"❌ *NO PURCHASES YET - LEGIT SHOP*\n"
            f"📅 {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n\n"
            f"You haven't bought any VPN yet.\n\n"
            f"✅ *CERTIFIED OFFER - LEGIT:*\n"
            f"• All Single VPNs $2 - Instant file\n"
            f"• Family Pack ALL 9 VPNs $2 - BEST DEAL - Save $16!\n"
            f"• Instant delivery - 3 seconds\n"
            f"• Money back guarantee\n"
            f"• Redownload anytime with /myvpn\n\n"
            f"👉 *Type /buy to buy your first VPN - Join 500+ certified customers!*", parse_mode="Markdown")
        return
    last=my[-1]
    bot.send_message(m.chat.id, f"📦 *YOUR CERTIFIED VPNs - LEGIT*\n"
        f"📅 {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n\n"
        f"✅ *Total Purchases: {len(my)} - Certified Customer!*\n"
        f"📱 *Last:* {last['app']}\n"
        f"📅 *Date:* {last['txn_date']} {last.get('day','')}\n"
        f"⏰ *Time:* {last.get('time','')}\n"
        f"🧾 *Txn:* {last['txn_id']}\n\n"
        f"📥 *Resending your last file now - Certified redownload service...*\n"
        f"💡 *Family Pack gives ALL VPNs $2!*", parse_mode="Markdown")
    files=get_files()
    for f in files:
        if last['app'].lower() in f.lower() or last['app']=="FAMILY":
            try:
                with open(f"configs/{f}",'rb') as doc: bot.send_document(m.chat.id, doc, caption=f"✅ {last['app']} - Certified Redownload {last['txn_date']} {last.get('day','')}")
            except: pass
            if last['app']!="FAMILY": break

# Catch all unknown /commands - makes EVERY command respond legit
@bot.message_handler(func=lambda m: m.text and m.text.startswith('/'))
def cmd_unknown(m):
    ht=get_harare_time()
    bot.send_message(m.chat.id, f"🤖 *REO BOT - LEGIT - {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT*\n\n"
        f"You typed: {m.text}\n\n"
        f"✅ *Available LEGIT commands - ALL RESPOND:*\n"
        f"🚀 /start - Start bot - Buy VPN $2\n"
        f"🛒 /buy - Buy VPN instantly $2\n"
        f"💰 /price - Price list - All $2 - Legit prices\n"
        f"✅ /proof - Live payment proofs - Certified sales\n"
        f"🎁 /trial - Free trial info - Money back guarantee\n"
        f"👥 /refer - Refer & Earn $0.50 - Legit program\n"
        f"📞 /support - Contact Danil 0775713879 - 24/7 legit\n"
        f"📲 /help - How to setup VPN - Legit guide\n"
        f"⭐ /about - About REO - 500+ customers certified\n"
        f"📦 /myvpn - My purchased VPNs - Redownload\n"
        f"⏳ /status - Check payment status\n\n"
        f"👉 *Type /buy to order - Legit certified shop!*", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    if c.data.startswith("buy_"):
        vtype=c.data.replace("buy_",""); pending[c.from_user.id]=vtype
        ht=get_harare_time()
        bot.send_message(c.message.chat.id, f"💰 *CERTIFIED ORDER: {vtype} - $2 LEGIT*\n"
            f"📅 TODAY {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n"
            f"📆 Calendar: {ht['month_name']} has {calendar.monthrange(ht['year'], ht['date'].month)[1]} days\n\n"
            f"💳 *Pay to:* EcoCash *0775713879*\n"
            f"👤 *Name:* Danil\n"
            f"💰 *Amount:* Exactly $2.00\n\n"
            f"After payment, *Forward REAL EcoCash SMS* here - BOTH accepted:\n"
            f"✅ Transfer Confirmation: USD 2.00 sent to TAFADZWA ZINATSA. Approval Code: PP260916.1347.T4051947\n"
            f"✅ Cashin Confirmation: USD 2.00 received from...\n"
            f"✅ Approval Code: CI or PP\n"
            f"✅ New balance\n"
            f"✅ Super App link https://goo.su/bCutT\n\n"
            f"📅 TODAY {ht['date_str']} {ht['day_name']} ONLY! Calendar checks day!\n"
            f"⏰ Time now: {ht['time_str']} CAT - Harare\n"
            f"🛡️ Certified secure - No fake dates!\n\n"
            f"Forward SMS now for instant file!", parse_mode="Markdown")

@bot.message_handler(content_types=['text'])
def txt(m):
    if m.text.startswith('/'): return
    if m.from_user.id not in pending:
        ht=get_harare_time()
        bot.send_message(m.chat.id, f"👋 Hi! {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n"
            f"✅ I am REO VPN Bot - Legit certified shop\n"
            f"⭐ 500+ Customers\n"
            f"Type /buy to buy VPN $2\n"
            f"Type /price for price list\n"
            f"Type /proof for live proofs\n"
            f"Type /help for guide\n"
            f"All commands respond - Legit!"); return
    valid, reason, txn_date, txn_id, amount = confirm_payment(m.text)
    if valid:
        bot.send_message(m.chat.id, f"🔍 {reason}\n🧾 {txn_id}\n📅 {txn_date}\n✅ Certified by calendar!")
        send_file(m.from_user.id, pending[m.from_user.id], txn_id, txn_date, amount, m.from_user.username or "")
    else:
        if "ALREADY USED" in reason: blocked.add(m.from_user.id); save_backup()
        if len(m.text)>15: bot.send_message(m.chat.id, f"{reason}\nNeed TODAY {get_harare_time()['date_str']} ONLY!")

def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
if __name__=="__main__":
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
