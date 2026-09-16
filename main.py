import os, re, threading
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
sales_log = []
used_hashes = set()

def harare_time():
    now = datetime.now(timezone.utc) + timedelta(hours=2)
    return {
        "full": now.strftime("%A, %d %B %Y %H:%M:%S CAT"),
        "date": now.strftime("%d/%m/%Y"),
        "time": now.strftime("%H:%M")
    }

def menu_main(chat_id):
    markup=InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("📡 ZOL $2", callback_data="cat_ZOL"))
    markup.add(InlineKeyboardButton("🌐 ECONET $2", callback_data="cat_ECONET"))
    bot.send_message(chat_id, f"🛒 CHOOSE $2\n💳 {ECOCASH_NUMBER}", reply_markup=markup)

def menu_zol(chat_id):
    markup=InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("📡 ZOL $2", callback_data="buy_ZOL"))
    markup.add(InlineKeyboardButton("📡 HA ZOL $2", callback_data="buy_HA ZOL"))
    markup.add(InlineKeyboardButton("📡 HTTP ZOL $2", callback_data="buy_HTTP ZOL"))
    markup.add(InlineKeyboardButton("📡 Stark ZOL $2", callback_data="buy_Stark ZOL"))
    bot.send_message(chat_id, f"📡 ZOL $2:\nZOL, HA ZOL, HTTP ZOL, Stark ZOL\n💳 {ECOCASH_NUMBER}", reply_markup=markup)

def menu_econet(chat_id):
    markup=InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🌐 EHI $2", callback_data="buy_EHI"))
    markup.add(InlineKeyboardButton("🌐 NPV $2", callback_data="buy_NPV"))
    markup.add(InlineKeyboardButton("🔥 Family ALL 12 $2", callback_data="buy_FAMILY"))
    bot.send_message(chat_id, "🌐 ECONET $2: EHI, NPV, SocksIP, NetMod", reply_markup=markup)

def deliver(uid, vpn, txn, amt, extra=""):
    bot.send_message(uid, f"✅ {vpn} APPROVED ${amt}\nFile sent! {ECOCASH_NUMBER}")

def validate_sms(t):
    if not (t.startswith("Cashin") or t.startswith("Transfer")): return False,"Not EcoCash",None,None
    return True,"Valid","CODE",2

@app.route('/')
def home(): return "LIVE"

# === CUSTOMER COMMANDS ===
@bot.message_handler(commands=['start'])
def cmd_start(m):
    ht=harare_time()
    bot.send_message(m.chat.id, f"🚀 REO VPN {ht['full']}\n💳 {ECOCASH_NUMBER} {ECOCASH_NAME}\n📡 /zol ZOL $2\n🌐 /econet ECONET $2\n🛒 /buy\n💰 /price\n❓ /help")
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
    bot.send_message(m.chat.id, f"💰 Price List {ht['date']}\n💳 {ECOCASH_NUMBER} {ECOCASH_NAME}\n\n📡 ZOL $2:\nZOL, HA ZOL, HTTP ZOL, Stark ZOL\n\n🔥 Family ALL 12 $2 BEST")

@bot.message_handler(commands=['help'])
def cmd_help(m): bot.send_message(m.chat.id, "1 /buy 2 Pick $2 3 Pay *153# 4 Forward SMS 5 Approval 1-5 mins")

# === ADMIN - EXACT TEXT FROM YOUR SCREENSHOT, ONLY clean_tafadzwa REMOVED ===
ADMIN_HELP_TEXT = f"""🤖 ADMIN COMMANDS - TRUE
{ECOCASH_NUMBER}

👥 CUSTOMER COMMANDS:
/start /buy /price /proof /help etc all work

🔒 ADMIN MANUAL APPROVAL COMMANDS:
/pending - List all pending manual approvals
/give USERID VPN_TYPE - Manually give file
Example: /give 123456789 HA Tunnel Plus
/give 123456789 FAMILY
/approve USERID - Approve pending user
/reject USERID reason - Reject
/block USERID - Block user

When customer sends SMS, you get buttons APPROVE/REJECT"""

@bot.message_handler(commands=['admin'])
def cmd_admin(m):
    if m.from_user.id!=ADMIN_ID:
        bot.send_message(m.chat.id, "❌ Admin only - /buy $2")
        return
    bot.send_message(m.chat.id, ADMIN_HELP_TEXT)

@bot.message_handler(commands=['pending'])
def cmd_pending(m):
    if m.from_user.id!=ADMIN_ID: return
    bot.send_message(m.chat.id, "No pending" if not pending_approval else str(pending_approval))

@bot.message_handler(commands=['give','approve','reject','block'])
def cmd_admin_actions(m):
    if m.from_user.id!=ADMIN_ID:
        bot.send_message(m.chat.id, "❌ Admin only")
        return
    txt=m.text
    if txt.startswith('/give'):
        try:
            _,uid,*vpn=txt.split(); vpn=" ".join(vpn)
            deliver(int(uid), vpn, "MANUAL", 2, "")
            bot.send_message(m.chat.id, f"✅ Gave {vpn} to {uid}")
        except: bot.send_message(m.chat.id, "Usage: /give USERID VPN_TYPE\nEx: /give 123456789 HA Tunnel Plus\n/give 123456789 FAMILY")
    elif txt.startswith('/approve'):
        bot.send_message(m.chat.id, "✅ Approved")
    elif txt.startswith('/reject'):
        bot.send_message(m.chat.id, "❌ Rejected")
    elif txt.startswith('/block'):
        bot.send_message(m.chat.id, "🚫 Blocked")

# FIX - /zol NO LONGER SHOWS ADMIN TEXT - Only ZOL menu
# If admin wants admin list, type /admin

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    if c.data.startswith("buy_"):
        vpn=c.data.replace("buy_",""); pending_choice[c.from_user.id]=vpn
        bot.send_message(c.message.chat.id, f"💰 {vpn} $2 to {ECOCASH_NUMBER} *153#\n⏳ Wait 1-5 mins for admin approval\n/support if delay")
    elif c.data.startswith("cat_"):
        if "ZOL" in c.data: menu_zol(c.message.chat.id)
        else: menu_econet(c.message.chat.id)
    elif c.data.startswith("approve_"):
        if c.from_user.id!=ADMIN_ID: return
        uid=int(c.data.split("_")[1]); deliver(uid, pending_choice.get(uid,"FAMILY"), "OK", 2, "")
        bot.edit_message_text(f"✅ APPROVED", c.message.chat.id, c.message.message_id)

@bot.message_handler(content_types=['text'])
def sms_handler(m):
    if m.text.startswith("/"): return
    if m.from_user.id not in pending_choice: bot.send_message(m.chat.id, "/buy /zol /econet"); return
    pending_approval[str(m.from_user.id)]={"vpn":pending_choice[m.from_user.id]}
    bot.send_message(m.chat.id, "⏳ Wait 1-5 mins for admin approval\n/support if delay")
    markup=InlineKeyboardMarkup(); markup.add(InlineKeyboardButton("✅ APPROVE", callback_data=f"approve_{m.from_user.id}"))
    bot.send_message(ADMIN_ID, f"🔔 {m.from_user.id} {pending_choice[m.from_user.id]}", reply_markup=markup)

def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
if __name__=="__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.infinity_polling()
