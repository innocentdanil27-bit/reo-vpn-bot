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
referral_numbers = {}
referral_names = {}
referral_photos = {}

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
    bot.send_message(cid, f"📡 ZOL $2 Menu\n💳 {ECOCASH_NUMBER}", reply_markup=mk)

def econet_menu(cid):
    mk=InlineKeyboardMarkup(row_width=1)
    for v in ["EHI","NPV","SocksIP","NetMod","HA Tunnel Plus","FAMILY"]:
        mk.add(InlineKeyboardButton(f"🌐 {v} $2", callback_data=f"buy_{v}"))
    bot.send_message(cid, f"🌐 ECONET $2 Menu\n💳 {ECOCASH_NUMBER}", reply_markup=mk)

def deliver(uid, vpn, txn):
    try:
        bot.send_message(uid, f"✅ {vpn} APPROVED $2\nTxn: {txn}\nFile sent!")
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
def home(): return f"LIVE {now_cat()}"

@bot.message_handler(commands=['start'])
def h_start(m):
    if m.from_user.id in blocked: bot.send_message(m.chat.id,"🚫 Blocked"); return
    bot.send_message(m.chat.id, f"🚀 REO VPN {now_cat()}\n💳 {ECOCASH_NUMBER} {ECOCASH_NAME}\n/start /buy /zol /econet /price /proof /help /myvpn /status /support /about /trial /refer")
    main_menu(m.chat.id)

@bot.message_handler(commands=['buy'])
def h_buy(m):
    if m.from_user.id in blocked: return
    bot.send_message(m.chat.id, "🛒 BUY $2 - Choose:"); main_menu(m.chat.id)

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
    bot.send_message(m.chat.id, f"💰 PRICE {now_cat()}\n💳 {ECOCASH_NUMBER}\n📡 ZOL $2: ZOL, HA ZOL, HTTP ZOL, Stark ZOL\n🌐 ECONET $2: EHI, NPV, SocksIP, NetMod, HA Tunnel Plus\n🔥 Family ALL 12 $2")

@bot.message_handler(commands=['proof'])
def h_proof(m):
    if not sales_log: bot.send_message(m.chat.id, f"✅ PROOFS {now_cat()}\nNo proofs yet"); return
    txt=f"✅ PROOFS {now_cat()}\n"
    for s in sales_log[-10:][::-1]: txt+=f"• {s['vpn']} {s['date']} ✅\n"
    bot.send_message(m.chat.id, txt)

@bot.message_handler(commands=['help'])
def h_help(m):
    bot.send_message(m.chat.id, f"📲 HELP\n1 /buy 2 Pick $2 3 Pay to {ECOCASH_NUMBER} *153# 4 Forward SMS 5 Wait 1-5 mins")

@bot.message_handler(commands=['myvpn'])
def h_myvpn(m):
    bot.send_message(m.chat.id, f"📦 MYVPN {now_cat()}\nLast: {pending_choice.get(m.from_user.id,'None')}")

@bot.message_handler(commands=['status'])
def h_status(m):
    if m.from_user.id in pending_choice: bot.send_message(m.chat.id, f"⏳ Waiting payment for {pending_choice[m.from_user.id]}")
    elif str(m.from_user.id) in pending_approval: bot.send_message(m.chat.id, "⏳ Waiting admin approval")
    else: bot.send_message(m.chat.id, f"✅ No pending - {now_cat()}")

@bot.message_handler(commands=['support'])
def h_support(m):
    bot.send_message(m.chat.id, f"📞 SUPPORT 24/7\n{ECOCASH_NAME} {ECOCASH_NUMBER}")

@bot.message_handler(commands=['about'])
def h_about(m):
    bot.send_message(m.chat.id, f"⭐ ABOUT REO 500+ Customers\n💳 {ECOCASH_NUMBER}")

@bot.message_handler(commands=['trial'])
def h_trial(m):
    bot.send_message(m.chat.id, f"🎁 TRIAL Free test\n/buy - {ECOCASH_NUMBER}")

@bot.message_handler(commands=['refer'])
def h_refer(m):
    bot.send_message(m.chat.id, "👥 REFER & EARN $0.50\n1. Share https://t.me/reo_products_bot to 5 DIFFERENT groups\n2. Screenshots MUST show @reo_products_bot\n3. /mynumber 077xxxxxxx\n4. /myname YOUR NAME\n5. Send 5 DIFFERENT screenshots\n⚠️ <5 = $0.00")

@bot.message_handler(commands=['mynumber'])
def h_mynumber(m):
    try:
        num=m.text.split()[1].strip()
        referral_numbers[m.from_user.id]=num
        bot.send_message(m.chat.id,f"✅ Number saved: {num}\nNow /myname YOUR NAME")
    except: bot.send_message(m.chat.id,"❌ Usage: /mynumber 077xxxxxxx")

@bot.message_handler(commands=['myname'])
def h_myname(m):
    try:
        name=m.text.replace("/myname","").strip()
        referral_names[m.from_user.id]=name
        bot.send_message(m.chat.id,f"✅ Name saved: {name}")
    except: bot.send_message(m.chat.id,"❌ Usage: /myname YOUR NAME")

@bot.message_handler(content_types=['photo'])
def h_ref_photo(m):
    uid=m.from_user.id
    if uid in blocked: return
    file_uid=m.photo[-1].file_unique_id
    file_id=m.photo[-1].file_id
    lst=referral_photos.get(uid,[])
    if file_uid in lst: bot.send_message(m.chat.id,"❌ Same screenshot! Send DIFFERENT one."); return
    lst.append(file_uid); referral_photos[uid]=lst
    count=len(lst)
    try: bot.send_photo(ADMIN_ID, file_id, caption=f"📸 {count}/5 from {uid} @{m.from_user.username} Check @reo_products_bot")
    except: pass
    if count<5: bot.send_message(m.chat.id,f"📸 {count}/5 received. Send {5-count} more. Must show @reo_products_bot")
    elif count==5:
        num=referral_numbers.get(uid); name=referral_names.get(uid)
        if not num or not name:
            bot.send_message(m.chat.id,"✅ 5/5! Now send /mynumber and /myname")
            bot.send_message(ADMIN_ID,f"👥 VERIFY {uid} missing details")
        else:
            bot.send_message(m.chat.id,f"✅ Done! {num} {name} Admin will send $0.50")
            bot.send_message(ADMIN_ID,f"👥 READY TO PAY {uid}\n📱 {num}\n👤 {name}\n/refpay {uid}\n/refreject {uid}")
    else: bot.send_message(m.chat.id,"Wait for admin")

@bot.message_handler(commands=['refpay'])
def h_refpay(m):
    if m.from_user.id!=ADMIN_ID: return
    try:
        uid=int(m.text.split()[1]); num=referral_numbers.get(uid,"unknown"); name=referral_names.get(uid,"unknown")
        bot.send_message(m.chat.id,f"✅ Pay $0.50 to {num} ({name}) ID:{uid} via *153#")
        try: bot.send_message(uid,f"✅ Approved! $0.50 to {num} ({name})")
        except: pass
        if uid in referral_photos: del referral_photos[uid]
    except: bot.send_message(m.chat.id,"Usage: /refpay USERID")

@bot.message_handler(commands=['refreject'])
def h_refreject(m):
    if m.from_user.id!=ADMIN_ID: return
    try:
        uid=int(m.text.split()[1])
        if uid in referral_photos: del referral_photos[uid]
        bot.send_message(m.chat.id,f"❌ Rejected {uid}")
        try: bot.send_message(uid,"❌ Referral rejected: need 5 DIFFERENT screenshots showing @reo_products_bot")
        except: pass
    except: bot.send_message(m.chat.id,"Usage: /refreject USERID")

@bot.message_handler(commands=['admin'])
def h_admin(m):
    if m.from_user.id!=ADMIN_ID: bot.send_message(m.chat.id,"❌ Admin only"); return
    bot.send_message(m.chat.id, f"🤖 ADMIN\n/pending /give /approve /reject /block /refpay /refreject")

@bot.message_handler(commands=['pending'])
def h_pending(m):
    if m.from_user.id!=ADMIN_ID: return
    if not pending_approval: bot.send_message(m.chat.id,f"✅ No pending - {now_cat()}"); return
    msg=f"⏳ PENDING {len(pending_approval)}\n"
    for uid,d in pending_approval.items(): msg+=f"👤 {uid} {d['vpn']} {d['txn']}\n/give {uid} {d['vpn']}\n"
    bot.send_message(m.chat.id,msg[:3900])

@bot.message_handler(commands=['give'])
def h_give(m):
    if m.from_user.id!=ADMIN_ID: return
    try:
        _,uid,*vpn=m.text.split(); vpn=" ".join(vpn); uid=int(uid)
        if vpn.upper()=="FAMILY": vpn="Family ALL 12"
        deliver(uid,vpn,"MANUAL_GIVE")
        if str(uid) in pending_approval: del pending_approval[str(uid)]
        if uid in pending_choice: del pending_choice[uid]
        bot.send_message(m.chat.id,f"✅ GAVE {vpn} to {uid}")
    except Exception as e: bot.send_message(m.chat.id,f"❌ /give USERID VPN\n{e}")

@bot.message_handler(commands=['approve'])
def h_approve(m):
    if m.from_user.id!=ADMIN_ID: return
    try:
        uid=int(m.text.split()[1]); d=pending_approval[str(uid)]
        deliver(uid,d['vpn'],d['txn']); used_txn.add(d['txn'])
        del pending_approval[str(uid)]
        bot.send_message(m.chat.id,f"✅ APPROVED {uid}")
    except: bot.send_message(m.chat.id,"❌ /approve USERID")

@bot.message_handler(commands=['reject'])
def h_reject(m):
    if m.from_user.id!=ADMIN_ID: return
    try:
        parts=m.text.split(); uid=parts[1]; reason=" ".join(parts[2:]) if len(parts)>2 else "No reason"
        if uid in pending_approval: del pending_approval[uid]
        bot.send_message(m.chat.id,f"❌ REJECTED {uid}")
    except: bot.send_message(m.chat.id,"❌ /reject USERID reason")

@bot.message_handler(commands=['block'])
def h_block(m):
    if m.from_user.id!=ADMIN_ID: return
    try:
        uid=int(m.text.split()[1]); blocked.add(uid)
        bot.send_message(m.chat.id,f"🚫 BLOCKED {uid}")
    except: bot.send_message(m.chat.id,"❌ /block USERID")

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    if c.data.startswith("buy_"):
        pending_choice[c.from_user.id]=c.data.replace("buy_","")
        bot.send_message(c.message.chat.id,f"💰 {pending_choice[c.from_user.id]} $2 to {ECOCASH_NUMBER} *153#\nForward SMS here")
    elif c.data.startswith("cat_"):
        (zol_menu if "ZOL" in c.data else econet_menu)(c.message.chat.id)

@bot.message_handler(content_types=['text'])
def sms(m):
    if m.text.startswith("/"): return
    if m.from_user.id in blocked: return
    if m.from_user.id not in pending_choice: bot.send_message(m.chat.id,"🛒 First /buy"); return
    ok,reason,txn=check_sms(m.text)
    if not ok: bot.send_message(m.chat.id,f"❌ {reason}"); return
    pending_approval[str(m.from_user.id)]={"vpn":pending_choice[m.from_user.id],"txn":txn}
    bot.send_message(m.chat.id,f"✅ SMS {txn} received. Wait 1-5 mins")
    mk=InlineKeyboardMarkup(); mk.add(InlineKeyboardButton("✅ APPROVE",callback_data=f"approve_{m.from_user.id}"))
    bot.send_message(ADMIN_ID,f"🔔 NEW PAY {m.from_user.id} {txn}",reply_markup=mk)

def set_commands():
    try:
        cmds=[BotCommand("start","Start"),BotCommand("buy","Buy"),BotCommand("zol","ZOL"),BotCommand("econet","ECONET"),BotCommand("eco","ECO"),BotCommand("price","Price"),BotCommand("proof","Proofs"),BotCommand("help","Help"),BotCommand("myvpn","My VPN"),BotCommand("status","Status"),BotCommand("support","Support"),BotCommand("about","About"),BotCommand("trial","Trial"),BotCommand("refer","Refer"),BotCommand("mynumber","Number"),BotCommand("myname","Name"),BotCommand("admin","Admin"),BotCommand("pending","Pending")]
        bot.set_my_commands(cmds)
    except: pass

def run_flask(): app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
if __name__=="__main__":
    threading.Thread(target=run_flask,daemon=True).start()
    set_commands()
    bot.infinity_polling()
