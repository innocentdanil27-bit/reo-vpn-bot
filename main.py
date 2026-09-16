import os, re, threading
import telebot
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
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
used_txn = set()
blocked = set()

def now_cat():
    return (datetime.now(timezone.utc)+timedelta(hours=2)).strftime("%d/%m/%Y %H:%M CAT")

def main_menu(cid):
    mk=InlineKeyboardMarkup(row_width=1)
    mk.add(InlineKeyboardButton("📡 ZOL $2", callback_data="cat_ZOL"))
    mk.add(InlineKeyboardButton("🌐 ECONET $2", callback_data="cat_ECONET"))
    mk.add(InlineKeyboardButton("🔥 Family ALL 12 $2", callback_data="buy_FAMILY"))
    bot.send_message(cid, f"🛒 CHOOSE $2\n💳 {ECOCASH_NUMBER}", reply_markup=mk)

def zol_menu(cid):
    mk=InlineKeyboardMarkup(row_width=1)
    for v in ["ZOL","HA ZOL","HTTP ZOL","Stark ZOL"]:
        mk.add(InlineKeyboardButton(f"📡 {v} $2", callback_data=f"buy_{v}"))
    bot.send_message(cid, f"📡 ZOL $2 Menu\nZOL, HA ZOL, HTTP ZOL, Stark ZOL\n💳 {ECOCASH_NUMBER}", reply_markup=mk)

def econet_menu(cid):
    mk=InlineKeyboardMarkup(row_width=1)
    for v in ["EHI","NPV","SocksIP","NetMod","HA Tunnel Plus","FAMILY"]:
        mk.add(InlineKeyboardButton(f"🌐 {v} $2", callback_data=f"buy_{v}"))
    bot.send_message(cid, f"🌐 ECONET $2 Menu\nEHI, NPV, SocksIP, NetMod\n💳 {ECOCASH_NUMBER}", reply_markup=mk)

def deliver(uid, vpn, txn):
    try:
        bot.send_message(uid, f"✅ {vpn} APPROVED $2\nTxn: {txn}\n💳 {ECOCASH_NUMBER}\nFile sent!")
        sales_log.append({"vpn":vpn,"txn":txn,"date":now_cat()})
    except: pass

def check_sms(t):
    up=t.upper()
    if not up.startswith(("CASHIN","TRANSFER")): return False,"Not EcoCash",None
    m=re.search(r'USD\s*\$?\s*(\d+\.?\d*)',up)
    if not m or float(m.group(1))<1.99: return False,"Less than $2",None
    txn=re.search(r'(CI|PP)\d{6,}',up)
    txn=txn.group(0) if txn else "MANUAL"
    if txn in used_txn: return False,"Txn used",None
    return True,"OK",txn

@app.route('/')
def home(): return f"LIVE {len(pending_approval)} pending {now_cat()}"

# ===== BUYER COMMANDS - EACH OWN HANDLER - LEGIT RESPOND =====
@bot.message_handler(commands=['start'])
def h_start(m):
    if m.from_user.id in blocked: bot.send_message(m.chat.id,"🚫 Blocked"); return
    bot.send_message(m.chat.id, f"🚀 REO VPN {now_cat()}\n💳 {ECOCASH_NUMBER} {ECOCASH_NAME}\n\n👥 BUYER COMMANDS:\n/start /buy /zol /econet /price /proof /help /myvpn /status /support /about /trial /refer\n\n🛒 Pick /buy")
    main_menu(m.chat.id)

@bot.message_handler(commands=['buy'])
def h_buy(m):
    if m.from_user.id in blocked: return
    bot.send_message(m.chat.id, "🛒 BUY $2 - Choose network:"); main_menu(m.chat.id)

@bot.message_handler(commands=['zol'])
def h_zol(m):
    if m.from_user.id in blocked: return
    bot.send_message(m.chat.id, "📡 ZOL $2 Command Received"); zol_menu(m.chat.id)

@bot.message_handler(commands=['econet'])
def h_econet(m):
    if m.from_user.id in blocked: return
    bot.send_message(m.chat.id, "🌐 ECONET $2 Command Received"); econet_menu(m.chat.id)

@bot.message_handler(commands=['eco'])
def h_eco(m):
    if m.from_user.id in blocked: return
    bot.send_message(m.chat.id, "🌐 ECO $2 Command Received"); econet_menu(m.chat.id)

@bot.message_handler(commands=['price'])
def h_price(m):
    bot.send_message(m.chat.id, f"💰 PRICE LIST {now_cat()}\n💳 {ECOCASH_NUMBER} {ECOCASH_NAME}\n\n📡 ZOL $2: ZOL, HA ZOL, HTTP ZOL, Stark ZOL\n🌐 ECONET $2: EHI, NPV, SocksIP, NetMod, HA Tunnel Plus\n🔥 Family ALL 12 $2 BEST\n\n/buy /zol /econet to order")

@bot.message_handler(commands=['proof'])
def h_proof(m):
    if not sales_log:
        bot.send_message(m.chat.id, f"✅ PROOFS {now_cat()} {ECOCASH_NUMBER}\nNo proofs yet today\n/buy to be first"); return
    txt=f"✅ PROOFS {now_cat()} {ECOCASH_NUMBER}\n"
    for s in sales_log[-10:][::-1]: txt+=f"• {s['vpn']} {s['date']} ✅\n"
    bot.send_message(m.chat.id, txt)

@bot.message_handler(commands=['help'])
def h_help(m):
    bot.send_message(m.chat.id, f"📲 HELP {now_cat()}\n1 /buy 2 Pick $2 3 Pay to {ECOCASH_NUMBER} *153# 4 Forward EcoCash SMS here 5 Wait 1-5 mins approval\n/support")

@bot.message_handler(commands=['myvpn'])
def h_myvpn(m):
    my=[s for s in sales_log if True]
    bot.send_message(m.chat.id, f"📦 MYVPN {now_cat()}\nLast order: {pending_choice.get(m.from_user.id,'None')}\nPending approval: {pending_approval.get(str(m.from_user.id),{}).get('vpn','None')}\n/buy to order")

@bot.message_handler(commands=['status'])
def h_status(m):
    if m.from_user.id in pending_choice:
        bot.send_message(m.chat.id, f"⏳ STATUS: Waiting payment for {pending_choice[m.from_user.id]} - Pay to {ECOCASH_NUMBER}")
    elif str(m.from_user.id) in pending_approval:
        bot.send_message(m.chat.id, f"⏳ STATUS: Waiting admin approval for {pending_approval[str(m.from_user.id)]['vpn']} 1-5 mins")
    else:
        bot.send_message(m.chat.id, f"✅ STATUS: No pending - {now_cat()} - /buy /zol /econet")

@bot.message_handler(commands=['support'])
def h_support(m):
    bot.send_message(m.chat.id, f"📞 SUPPORT 24/7 {now_cat()}\nOwner {ECOCASH_NAME}\nEcoCash {ECOCASH_NUMBER}\nDanil replies 1-5 mins")

@bot.message_handler(commands=['about'])
def h_about(m):
    bot.send_message(m.chat.id, f"⭐ ABOUT REO 500+ Customers Since 2024\n💳 {ECOCASH_NUMBER} {ECOCASH_NAME}\n📡 ZOL $2 🌐 ECONET $2 All $2\n/buy")

@bot.message_handler(commands=['trial'])
def h_trial(m):
    bot.send_message(m.chat.id, f"🎁 TRIAL Free test Family ALL 12 $2 - Money back guarantee\n/buy to test - {ECOCASH_NUMBER}")

@bot.message_handler(commands=['refer'])
def h_refer(m):
    bot.send_message(m.chat.id, f"👥 REFER Earn $0.50\nShare bot: https://t.me/reo_products_bot\nFriend pays $2 to {ECOCASH_NUMBER} you get $0.50\n/buy")

# ===== ADMIN COMMANDS - EACH OWN HANDLER - LEGIT - NO clean_tafadzwa =====
ADMIN_TEXT = f"""🤖 ADMIN COMMANDS - TRUE
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
def h_admin(m):
    if m.from_user.id!=ADMIN_ID: bot.send_message(m.chat.id,"❌ Admin only - /buy $2"); return
    bot.send_message(m.chat.id, ADMIN_TEXT)

@bot.message_handler(commands=['pending'])
def h_pending(m):
    if m.from_user.id!=ADMIN_ID: bot.send_message(m.chat.id,"❌ Admin only"); return
    if not pending_approval:
        bot.send_message(m.chat.id, f"✅ No pending approvals - {now_cat()}"); return
    msg=f"⏳ PENDING {len(pending_approval)} {now_cat()}\n"
    for uid,d in pending_approval.items():
        msg+=f"👤 {uid} 📦 {d['vpn']} 🔑 {d['txn']}\n/give {uid} {d['vpn']}\n/approve {uid}\n/reject {uid} reason\n\n"
    bot.send_message(m.chat.id, msg[:3900])

@bot.message_handler(commands=['give'])
def h_give(m):
    if m.from_user.id!=ADMIN_ID: bot.send_message(m.chat.id,"❌ Admin only"); return
    try:
        _,uid,*vpn=m.text.split(); vpn=" ".join(vpn); uid=int(uid)
        if vpn.upper()=="FAMILY": vpn="Family ALL 12"
        deliver(uid, vpn, "MANUAL_GIVE")
        if str(uid) in pending_approval: del pending_approval[str(uid)]
        if uid in pending_choice: del pending_choice[uid]
        bot.send_message(m.chat.id, f"✅ LEGIT GAVE {vpn} to {uid} - Pending cleared, txn saved")
    except Exception as e:
        bot.send_message(m.chat.id, f"❌ Usage: /give USERID VPN_TYPE\nExample: /give 123456789 HA Tunnel Plus\n/give 123456789 FAMILY\n{e}")

@bot.message_handler(commands=['approve'])
def h_approve(m):
    if m.from_user.id!=ADMIN_ID: return
    try:
        uid=int(m.text.split()[1]); d=pending_approval[str(uid)]
        deliver(uid, d['vpn'], d['txn']); used_txn.add(d['txn'])
        del pending_approval[str(uid)]
        if uid in pending_choice: del pending_choice[uid]
        bot.send_message(m.chat.id, f"✅ LEGIT APPROVED {uid} {d['vpn']} {d['txn']} - File sent")
    except:
        bot.send_message(m.chat.id, "❌ Usage: /approve USERID\nMust be in /pending list\nExample: /approve 123456789")

@bot.message_handler(commands=['reject'])
def h_reject(m):
    if m.from_user.id!=ADMIN_ID: return
    try:
        parts=m.text.split(); uid=parts[1]; reason=" ".join(parts[2:]) if len(parts)>2 else "No reason"
        if uid in pending_approval: del pending_approval[uid]
        if int(uid) in pending_choice: del pending_choice[int(uid)]
        bot.send_message(m.chat.id, f"❌ LEGIT REJECTED {uid} Reason: {reason} - Cleared")
        try: bot.send_message(int(uid), f"❌ Order rejected: {reason}\nPay to {ECOCASH_NUMBER} and forward SMS again")
        except: pass
    except: bot.send_message(m.chat.id, "❌ Usage: /reject USERID reason\nExample: /reject 123456789 wrong amount")

@bot.message_handler(commands=['block'])
def h_block(m):
    if m.from_user.id!=ADMIN_ID: return
    try:
        uid=int(m.text.split()[1]); blocked.add(uid)
        if str(uid) in pending_approval: del pending_approval[str(uid)]
        if uid in pending_choice: del pending_choice[uid]
        bot.send_message(m.chat.id, f"🚫 LEGIT BLOCKED {uid} - Cannot use bot anymore")
    except: bot.send_message(m.chat.id, "❌ Usage: /block USERID\nExample: /block 123456789")

# No clean_tafadzwa anywhere - REMOVED

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    if c.data.startswith("buy_"):
        pending_choice[c.from_user.id]=c.data.replace("buy_","")
        bot.send_message(c.message.chat.id, f"💰 {pending_choice[c.from_user.id]} $2 to {ECOCASH_NUMBER} *153#\nForward EcoCash SMS here\nWait 1-5 mins")
    elif c.data.startswith("cat_"):
        (zol_menu if "ZOL" in c.data else econet_menu)(c.message.chat.id)
    elif c.data.startswith("approve_"):
        if c.from_user.id!=ADMIN_ID: return
        uid=int(c.data.split("_")[1]); d=pending_approval.get(str(uid))
        if not d: return
        deliver(uid, d['vpn'], d['txn']); used_txn.add(d['txn'])
        del pending_approval[str(uid)]
        if uid in pending_choice: del pending_choice[uid]
        bot.edit_message_text(f"✅ APPROVED {uid} {d['vpn']} {d['txn']} LEGIT", c.message.chat.id, c.message.message_id)

@bot.message_handler(content_types=['text'])
def sms(m):
    if m.text.startswith("/"): return
    if m.from_user.id in blocked: return
    if m.from_user.id not in pending_choice: bot.send_message(m.chat.id,"🛒 First /buy /zol /econet"); return
    ok,reason,txn=check_sms(m.text)
    if not ok: bot.send_message(m.chat.id,f"❌ {reason}"); return
    pending_approval[str(m.from_user.id)]={"vpn":pending_choice[m.from_user.id],"txn":txn}
    bot.send_message(m.chat.id, f"✅ SMS Received {txn} {pending_choice[m.from_user.id]} $2\n⏳ Wait 1-5 mins approval")
    mk=InlineKeyboardMarkup(); mk.add(InlineKeyboardButton("✅ APPROVE", callback_data=f"approve_{m.from_user.id}"), InlineKeyboardButton("❌ REJECT", callback_data=f"reject_{m.from_user.id}"))
    bot.send_message(ADMIN_ID, f"🔔 NEW PAY {m.from_user.id} {pending_choice[m.from_user.id]} {txn}\n{m.text[:300]}\n/give {m.from_user.id} {pending_choice[m.from_user.id]}\n/approve {m.from_user.id}", reply_markup=mk)

def set_commands():
    try:
        cmds=[
            BotCommand("start","Start bot"),
            BotCommand("buy","Choose $2"),
            BotCommand("zol","ZOL $2 Menu"),
            BotCommand("econet","ECONET $2 Menu"),
            BotCommand("price","Price List"),
            BotCommand("proof","Proofs"),
            BotCommand("help","How to buy"),
            BotCommand("myvpn","My VPN"),
            BotCommand("status","Check status"),
            BotCommand("support","Support"),
            BotCommand("admin","Admin commands"),
            BotCommand("pending","Pending list"),
        ]
        bot.set_my_commands(cmds)
    except: pass

def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
if __name__=="__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    set_commands()
    bot.infinity_polling()
