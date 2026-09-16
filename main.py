import os, telebot, re, hashlib, json, threading, calendar
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8579468852"))
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

ECOCASH_NUMBER = "0775713879"
ECOCASH_NAME_PUBLIC = "Danil"
ECOCASH_NAME_KEYWORDS = ["tafadzwa", "zinatsa", "danil"]

pending = {} # user_id -> vtype they want to buy
pending_approval = {} # user_id -> {vtype, sms_text, amount, txn_id, username, time}
blocked = set()
used_txns = set()
transactions_log = []
BACKUP_FILE = "transactions_backup.json"
if os.path.exists(BACKUP_FILE):
    try:
        with open(BACKUP_FILE,'r') as f:
            d=json.load(f); transactions_log=d.get("logs",[]); used_txns=set(d.get("used_txns",[])); pending_approval=d.get("pending_approval",{})
    except: pass

def save_backup():
    with open(BACKUP_FILE,'w') as f: json.dump({"logs":transactions_log,"used_txns":list(used_txns),"pending_approval":pending_approval},f)
def hash_txn(t): return hashlib.sha256(t.encode()).hexdigest()[:20]
def get_files():
    if not os.path.exists("configs"): return []
    return [f for f in os.listdir("configs") if not f.startswith('.')]
def get_harare_time():
    harare_now = datetime.now(timezone.utc) + timedelta(hours=2)
    return {"date": harare_now.date(), "date_str": harare_now.strftime('%d/%m/%Y'), "time_str": harare_now.strftime('%H:%M:%S'), "day_name": harare_now.strftime('%A'), "month_name": harare_now.strftime('%B'), "year": harare_now.year, "full": harare_now.strftime('%A, %d %B %Y %H:%M:%S CAT')}

def quick_check_sms(text):
    upper=text.upper(); lower=text.lower()
    ht=get_harare_time()
    if not (text.startswith("Cashin Confirmation:") or text.startswith("Transfer Confirmation:")):
        return False, "Not EcoCash SMS", None, None
    if "approval code:" not in lower: return False, "No Approval Code", None, None
    amt_m=re.search(r'USD\s*\$?\s*(\d+\.?\d*)', upper)
    if not amt_m: return False, "No USD amount", None, None
    amount=float(amt_m.group(1))
    if amount < 1.99: return False, f"Amount ${amount} < $2", None, None
    app_m=re.search(r'(?:CI|PP)\d{6}\.\d{3,4}\.T\d{6,10}', upper)
    if not app_m:
        app_m2=re.search(r'(?:CI|PP)\d{6}\.\d{3,4}', upper)
        txn_id=app_m2.group(0) if app_m2 else "NOCODE"
    else: txn_id=app_m.group(0)
    # Check true recipient
    if text.startswith("Transfer Confirmation:"):
        is_to_you = any(k in lower for k in ECOCASH_NAME_KEYWORDS)
        if not is_to_you:
            return False, f"NOT TO US - Sent to someone else, not to {ECOCASH_NUMBER}", None, None
    return True, f"Looks OK ${amount} {txn_id}", txn_id, amount

def send_file(uid, vtype, txn_id, txn_date, amount, username=""):
    files=get_files()
    try:
        if txn_id!= "MANUAL_GIVE":
            used_txns.add(hash_txn(txn_id))
        ht=get_harare_time()
        date_str = txn_date if txn_date else ht["date_str"]
        if vtype=="FAMILY":
            for f in files:
                with open(f"configs/{f}",'rb') as doc: bot.send_document(uid, doc, caption=f"✅ Family Pack $2 {date_str} {ht['day_name']} {txn_id}")
        else:
            sent=False
            for f in files:
                if vtype.lower() in f.lower():
                    with open(f"configs/{f}",'rb') as doc: bot.send_document(uid, doc, caption=f"✅ {vtype} $2 {date_str} {txn_id}")
                    sent=True; break
            if not sent and files:
                with open(f"configs/{files[0]}",'rb') as doc: bot.send_document(uid, doc, caption=f"✅ {vtype} $2 {date_str}")
        bot.send_message(uid, f"💚 PAYMENT APPROVED BY ADMIN!\n\n✅ App: {vtype}\n💰 USD {amount}\n💳 To: {ECOCASH_NUMBER} {ECOCASH_NAME_PUBLIC}\n📅 {date_str} {ht['day_name']} {ht['time_str']} CAT\n🧾 Txn: {txn_id}\n✅ Approved by Danil\n\n📥 File sent!\n📲 /help for setup\n🔄 /myvpn to redownload")
        pending.pop(uid,None)
        pending_approval.pop(str(uid),None)
        transactions_log.append({"user":uid,"username":username,"app":vtype,"txn_id":txn_id,"txn_date":date_str,"day":ht['day_name'],"time":ht['time_str'],"amount":amount,"paid_to_number":ECOCASH_NUMBER,"approved_by":"Danil manual","true_ecocash":True})
        save_backup()
        if uid!= ADMIN_ID: bot.send_message(ADMIN_ID, f"✅ SENT FILE to {uid} @{username}\n📱 {vtype}\n🧾 {txn_id}\n📊 Total: {len(transactions_log)}")
    except Exception as e: bot.send_message(ADMIN_ID, f"Error sending file {e}")

def show_vpn_menu(chat_id):
    markup=InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("1. HA Tunnel Plus - $2 🔥", callback_data="buy_HA Tunnel Plus"))
    markup.add(InlineKeyboardButton("2. HTTP Custom - $2 ⚡", callback_data="buy_HTTP Custom"))
    markup.add(InlineKeyboardButton("3. HTTP Injector (EHI) - $2 💉", callback_data="buy_EHI"))
    markup.add(InlineKeyboardButton("4. NapsternetV (NPV) - $2 🚀", callback_data="buy_NPV"))
    markup.add(InlineKeyboardButton("5. Stark VPN - $2 🌟", callback_data="buy_STARK"))
    markup.add(InlineKeyboardButton("6. Dark Tunnel - $2 🌙", callback_data="buy_DARK"))
    markup.add(InlineKeyboardButton("7. TLS Tunnel - $2 🔒", callback_data="buy_TLS"))
    markup.add(InlineKeyboardButton("8. SocksIP Tunnel - $2 🧦", callback_data="buy_SocksIP"))
    markup.add(InlineKeyboardButton("9. NetMod - $2 🛠️", callback_data="buy_NETMOD"))
    markup.add(InlineKeyboardButton("10. Family Pack ALL - $2 🔥 BEST", callback_data="buy_FAMILY"))
    ht=get_harare_time()
    bot.send_message(chat_id, f"🚀 REO VPN - MANUAL APPROVAL SHOP\n📅 {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n💳 Pay: {ECOCASH_NUMBER} {ECOCASH_NAME_PUBLIC}\nALL $2 - PICK VPN - Admin approves!", reply_markup=markup)

@app.route('/')
def home():
    ht=get_harare_time()
    return f"LIVE {ht['full']} - {len(transactions_log)} sales - {len(pending_approval)} pending manual approval"

# ===== ALL COMMANDS =====
@bot.message_handler(commands=['start','buy'])
def cmd_start(m):
    if m.from_user.id in blocked: bot.send_message(m.chat.id, f"🚫 Blocked /support {ECOCASH_NUMBER}"); return
    show_vpn_menu(m.chat.id)

@bot.message_handler(commands=['price'])
def cmd_price(m):
    ht=get_harare_time()
    bot.send_message(m.chat.id, f"💰 PRICE {ht['day_name']} {ht['date_str']} - TRUE to {ECOCASH_NUMBER}\nALL $2\n1 HA Tunnel $2\n2 HTTP Custom $2\n3 EHI $2\n4 NPV $2\n5 Stark $2\n6 Dark $2\n7 TLS $2\n8 SocksIP $2\n9 NetMod $2\n10 Family ALL $2 BEST\nPay {ECOCASH_NUMBER} {ECOCASH_NAME_PUBLIC}\nAdmin approves then file sent /buy", parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def cmd_help(m):
    ht=get_harare_time()
    bot.send_message(m.chat.id, f"📲 HOW TO BUY - MANUAL APPROVAL - {ht['day_name']} {ht['date_str']}\n💳 TRUE: {ECOCASH_NUMBER} {ECOCASH_NAME_PUBLIC}\n\n1 /buy - Pick VPN\n2 Pay $2 to {ECOCASH_NUMBER}\n3 Forward REAL EcoCash SMS here\n4 Bot sends SMS to Danil for manual check\n5 Danil checks EcoCash app - If TRUE $2 to {ECOCASH_NUMBER}, Danil taps APPROVE\n6 Bot sends file instantly!\n\n⏰ Wait 1-5 mins for admin approval\n/support if delay", parse_mode="Markdown")

@bot.message_handler(commands=['support','about','proof','trial','refer','status','myvpn'])
def cmd_others(m):
    ht=get_harare_time()
    if "/support" in m.text: bot.send_message(m.chat.id, f"📞 SUPPORT {ht['full']}\nOwner {ECOCASH_NAME_PUBLIC}\nTRUE EcoCash {ECOCASH_NUMBER}\n24/7 Manual approval\nSend proof then wait for approve")
    elif "/about" in m.text: bot.send_message(m.chat.id, f"⭐ REO 500+ Customers\nTRUE Number {ECOCASH_NUMBER}\nManual approval - 100% safe\nSince 2024 Harare\nAll $2 /buy")
    elif "/proof" in m.text:
        count=len(transactions_log); recent=transactions_log[-5:] if count>=5 else transactions_log
        msg=f"✅ TRUE PROOFS to {ECOCASH_NUMBER} {ht['day_name']} {ht['date_str']}\nTotal {count}\n"
        for t in recent[::-1]: msg+=f"• {t['app']} {t['txn_date']} ${t['amount']} ✅ APPROVED BY DANIL\n"
        msg+=f"\nAll manually approved TRUE to {ECOCASH_NUMBER}\n/buy"
        bot.send_message(m.chat.id, msg)
    elif "/trial" in m.text: bot.send_message(m.chat.id, f"🎁 No free trial but money back - Buy Family $2 to test all - Manual approval /buy")
    elif "/refer" in m.text: bot.send_message(m.chat.id, f"👥 Refer $0.50 per friend TRUE to {ECOCASH_NUMBER}\nShare @reo_products_bot\n/buy")
    elif "/status" in m.text:
        if m.from_user.id in pending: bot.send_message(m.chat.id, f"⏳ Waiting {pending[m.from_user.id]} Pay {ECOCASH_NUMBER} then forward SMS - Danil will approve")
        elif str(m.from_user.id) in pending_approval: bot.send_message(m.chat.id, f"⏳ Your proof sent to Danil for manual check - Wait 1-5 mins for APPROVE\nApp: {pending_approval[str(m.from_user.id)]['vtype']}")
        else: bot.send_message(m.chat.id, f"✅ No pending {ht['day_name']} /buy")
    elif "/myvpn" in m.text:
        my=[t for t in transactions_log if t['user']==m.from_user.id]
        if not my: bot.send_message(m.chat.id, f"❌ No purchases yet /buy"); return
        last=my[-1]; bot.send_message(m.chat.id, f"📦 Last {last['app']} {last['txn_date']} Resending..."); files=get_files()
        for f in files:
            if last['app'].lower() in f.lower() or last['app']=="FAMILY":
                with open(f"configs/{f}",'rb') as doc: bot.send_document(m.chat.id, doc)
                if last['app']!="FAMILY": break

# ===== ADMIN COMMANDS - MANUAL GIVE =====
@bot.message_handler(commands=['give','approve'])
def cmd_give(m):
    if m.from_user.id!= ADMIN_ID: bot.send_message(m.chat.id, "🚫 Admin only"); return
    ht=get_harare_time()
    try:
        parts=m.text.split()
        if len(parts) < 3:
            bot.send_message(m.chat.id, f"❌ Usage:\n/give USERID VPN_TYPE\nExample:\n/give 123456789 HA Tunnel Plus\n/give 123456789 FAMILY\n\nOr to approve pending:\n/approve USERID\n\nPending list: /pending")
            return
        uid=int(parts[1])
        vtype=" ".join(parts[2:]) if len(parts)>2 else pending.get(uid,"FAMILY")
        if "family" in vtype.lower(): vtype="FAMILY"
        send_file(uid, vtype, f"MANUAL_GIVE_{ht['date_str'].replace('/','')}_{uid}", ht["date_str"], 2.00, "manual_give")
        bot.send_message(m.chat.id, f"✅ MANUALLY GAVE {vtype} to {uid}\n📅 {ht['full']}\n💳 True to {ECOCASH_NUMBER}")
    except Exception as e: bot.send_message(m.chat.id, f"Error {e}\nUsage: /give USERID VPN_TYPE")

@bot.message_handler(commands=['pending','list_pending'])
def cmd_pending(m):
    if m.from_user.id!= ADMIN_ID: return
    ht=get_harare_time()
    if not pending_approval: bot.send_message(m.chat.id, f"✅ No pending - All approved {ht['date_str']} {ht['time_str']}"); return
    msg=f"⏳ PENDING MANUAL APPROVAL - {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n💳 True to {ECOCASH_NUMBER}\nTotal pending: {len(pending_approval)}\n\n"
    for uid_str, data in pending_approval.items():
        msg+=f"👤 {uid_str} @{data.get('username','')} - {data.get('vtype','?')} - ${data.get('amount','?')} - {data.get('txn_id','')} - {data.get('time','')}\nSMS: {data.get('sms_text','')[:80]}...\n/approve {uid_str} or /give {uid_str} {data.get('vtype','FAMILY')}\n\n"
    bot.send_message(m.chat.id, msg[:4000])

@bot.message_handler(commands=['reject','block'])
def cmd_reject(m):
    if m.from_user.id!= ADMIN_ID: return
    try:
        parts=m.text.split()
        uid=int(parts[1])
        reason=" ".join(parts[2:]) if len(parts)>2 else f"Not true payment to {ECOCASH_NUMBER}"
        pending_approval.pop(str(uid),None)
        pending.pop(uid,None)
        save_backup()
        bot.send_message(uid, f"❌ PAYMENT REJECTED by Admin Danil\nReason: {reason}\n\n💳 Must be TRUE $2 to {ECOCASH_NUMBER} {ECOCASH_NAME_PUBLIC}\n📲 Send correct SMS to {ECOCASH_NUMBER}\n/support")
        bot.send_message(m.chat.id, f"✅ Rejected {uid} Reason: {reason}")
    except Exception as e: bot.send_message(m.chat.id, f"Error {e} Usage: /reject USERID reason")

@bot.message_handler(commands=['clean_tafadzwa'])
def cmd_clean(m):
    if m.from_user.id!= ADMIN_ID: return
    REMOVE_CODE = "PP260916.1347.T4051947"
    h = hash_txn(REMOVE_CODE)
    if h in used_txns: used_txns.remove(h)
    global transactions_log
    transactions_log = [t for t in transactions_log if REMOVE_CODE not in t.get("txn_id","")]
    save_backup()
    bot.send_message(m.chat.id, f"✅ Cleaned {REMOVE_CODE}")

@bot.message_handler(func=lambda m: m.text and m.text.startswith('/'))
def cmd_unknown(m):
    if m.from_user.id == ADMIN_ID:
        bot.send_message(m.chat.id, f"🤖 ADMIN COMMANDS - TRUE {ECOCASH_NUMBER}\n\n👥 CUSTOMER COMMANDS:\n/start /buy /price /proof /help etc all work\n\n🔐 ADMIN MANUAL APPROVAL COMMANDS:\n/pending - List all pending manual approvals\n/give USERID VPN_TYPE - Manually give file\nExample: /give 123456789 HA Tunnel Plus\n/give 123456789 FAMILY\n/approve USERID - Approve pending user\n/reject USERID reason - Reject\n/block USERID - Block user\n/clean_tafadzwa - Clean old txn\n\nWhen customer sends SMS, you get buttons APPROVE/REJECT")
    else:
        bot.send_message(m.chat.id, f"🤖 REO BOT TRUE {ECOCASH_NUMBER} {get_harare_time()['date_str']}\n/buy /price /proof /help /support /myvpn /status")

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    ht=get_harare_time()
    if c.data.startswith("buy_"):
        vtype=c.data.replace("buy_",""); pending[c.from_user.id]=vtype
        bot.send_message(c.message.chat.id, f"💰 TRUE ORDER: {vtype} - $2 to {ECOCASH_NUMBER} {ECOCASH_NAME_PUBLIC}\n📅 TODAY {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n\n💳 Pay TRUE to: {ECOCASH_NUMBER}\n👤 Name: {ECOCASH_NAME_PUBLIC}\n💰 $2.00\n\nAfter pay, forward REAL EcoCash SMS here:\n✅ Transfer OR Cashin Confirmation\n✅ USD 2.00\n✅ Approval Code\n✅ New balance + Super App\n\nMust be TRUE to {ECOCASH_NUMBER}!\n\n⏰ After you forward SMS, Danil will manually check EcoCash app and APPROVE, then file sent instantly!\nWait 1-5 mins after forwarding!")
    elif c.data.startswith("approve_"):
        if c.from_user.id!= ADMIN_ID: bot.answer_callback_query(c.id, "Admin only"); return
        try:
            uid=int(c.data.split("_")[1])
            data=pending_approval.get(str(uid))
            if not data: bot.send_message(c.message.chat.id, f"❌ No pending for {uid}"); return
            vtype=data.get("vtype","FAMILY")
            txn_id=data.get("txn_id",f"MANUAL_{ht['date_str']}")
            amount=data.get("amount",2.00)
            username=data.get("username","")
            send_file(uid, vtype, txn_id, ht["date_str"], amount, username)
            bot.answer_callback_query(c.id, f"✅ Approved {uid} {vtype}")
            bot.edit_message_text(f"✅ APPROVED {uid} {vtype} {txn_id} TRUE to {ECOCASH_NUMBER} - {ht['time_str']}", c.message.chat.id, c.message.message_id)
        except Exception as e: bot.send_message(c.message.chat.id, f"Error approve {e}")
    elif c.data.startswith("reject_"):
        if c.from_user.id!= ADMIN_ID: return
        try:
            uid=int(c.data.split("_")[1])
            pending_approval.pop(str(uid),None)
            pending.pop(uid,None)
            save_backup()
            bot.send_message(uid, f"❌ Rejected by Admin - Not true payment to {ECOCASH_NUMBER} {ECOCASH_NAME_PUBLIC}\nMust pay TRUE $2 to {ECOCASH_NUMBER}\n/support")
            bot.answer_callback_query(c.id, f"❌ Rejected {uid}")
            bot.edit_message_text(f"❌ REJECTED {uid} - Not true to {ECOCASH_NUMBER}", c.message.chat.id, c.message.message_id)
        except Exception as e: bot.send_message(c.message.chat.id, f"Error {e}")

@bot.message_handler(content_types=['text'])
def txt(m):
    if m.text.startswith('/'): return
    uid=m.from_user.id
    if uid not in pending:
        bot.send_message(m.chat.id, f"👋 Hi! Type /buy to buy $2 TRUE to {ECOCASH_NUMBER}\nAll commands work - /help guide"); return

    valid, reason, txn_id, amount = quick_check_sms(m.text)
    ht=get_harare_time()
    if not valid:
        bot.send_message(m.chat.id, f"{reason}\n\nMust be:\n✅ REAL EcoCash SMS\n✅ USD 2.00\n✅ TRUE to {ECOCASH_NUMBER} {ECOCASH_NAME_PUBLIC}\n✅ Today {ht['date_str']}\n\nForward REAL SMS!")
        return

    # Check if already used
    if txn_id!= "NOCODE" and hash_txn(txn_id) in used_txns:
        bot.send_message(m.chat.id, f"🚫 ALREADY USED {txn_id} - Each code once! /support"); return

    # SAVE TO PENDING APPROVAL - MANUAL MODE
    pending_approval[str(uid)] = {
        "vtype": pending[uid],
        "sms_text": m.text[:500],
        "txn_id": txn_id,
        "amount": amount,
        "username": m.from_user.username or "",
        "time": ht["full"],
        "user_id": uid
    }
    save_backup()

    # Tell customer to wait
    bot.send_message(m.chat.id, f"✅ SMS RECEIVED - WAITING FOR ADMIN MANUAL APPROVAL\n\n💰 Amount: ${amount}\n🧾 Txn: {txn_id}\n📱 App: {pending[uid]}\n💳 To: {ECOCASH_NUMBER} {ECOCASH_NAME_PUBLIC}\n📅 {ht['day_name']} {ht['date_str']} {ht['time_str']} CAT\n\n⏳ Danil is checking EcoCash app now...\n⏰ Wait 1-5 mins - If TRUE $2 to {ECOCASH_NUMBER}, Danil will tap APPROVE and bot sends file instantly!\n\n📊 Your position in queue: {len(pending_approval)}\n/support if delay")

    # Send to ADMIN with APPROVE BUTTONS
    markup=InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton(f"✅ APPROVE {pending[uid]}", callback_data=f"approve_{uid}"),
               InlineKeyboardButton(f"❌ REJECT", callback_data=f"reject_{uid}"))
    admin_msg = f"🔔 NEW MANUAL APPROVAL NEEDED - TRUE CHECK {ECOCASH_NUMBER}\n\n👤 User: {uid} @{m.from_user.username or ''} {m.from_user.first_name}\n📱 Wants: {pending[uid]}\n💰 Amount: ${amount}\n🧾 Txn: {txn_id}\n📅 {ht['full']}\n💳 Should be TRUE to {ECOCASH_NUMBER} {ECOCASH_NAME_PUBLIC}\n\n📩 FULL SMS FROM CUSTOMER:\n{m.text}\n\n⚠️ CHECK YOUR ECOCASH APP NOW:\n• Open EcoCash App\n• Check if ${amount} received from this user?\n• Check if TRUE to {ECOCASH_NUMBER}?\n• If YES, tap APPROVE below - Bot sends file\n• If NO, tap REJECT\n\nPending: {len(pending_approval)}"
    bot.send_message(ADMIN_ID, admin_msg, reply_markup=markup)

def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
if __name__=="__main__":
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
