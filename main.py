# --- CUSTOMER COMMANDS - ONLY THESE SHOW TO CUSTOMERS ---
@bot.message_handler(commands=['start'])
def cmd_start(m):
    ht=harare_time()
    bot.send_message(m.chat.id, f"🚀 Welcome REO VPN\n📅 {ht['full']}\n💳 EcoCash: {ECOCASH_NUMBER} {ECOCASH_NAME}\n⭐ 500+ Customers\n\n📡 /zol = ZOL $2\n🌐 /econet = ECONET $2\n🛒 /buy = Choose network\n💰 /price = Price list\n📦 /myvpn = My VPNs", parse_mode="Markdown")
    menu_main(m.chat.id)

@bot.message_handler(commands=['buy'])
def cmd_buy(m): menu_main(m.chat.id)

@bot.message_handler(commands=['zol'])
def cmd_zol(m): menu_zol(m.chat.id)  # Customer only sees ZOL menu, NOT admin list

@bot.message_handler(commands=['econet','eco'])
def cmd_econet(m): menu_econet(m.chat.id)

@bot.message_handler(commands=['price'])
def cmd_price(m):
    ht=harare_time()
    bot.send_message(m.chat.id, f"💰 Price List {ht['date_str']}\n💳 {ECOCASH_NUMBER} {ECOCASH_NAME}\n\n📡 ZOL $2:\n• ZOL VPN $2\n• HA Tunnel ZOL $2\n• HTTP Custom ZOL $2\n• Stark ZOL $2\n\n🌐 ECONET $2:\n• ECONET VPN $2\n• HA Tunnel Plus $2\n• HTTP Custom $2\n• EHI $2\n• NPV $2\n• Dark $2\n• TLS $2\n• SocksIP $2\n• NetMod $2\n\n🔥 Family ALL 12 $2 BEST\n👉 /buy or /zol or /econet")

@bot.message_handler(commands=['proof'])
def cmd_proof(m):
    ht=harare_time()
    recent=sales_log[-10:][::-1]
    txt=f"✅ Proofs {ht['date_str']} {ht['time_str']} CAT\nTotal {len(sales_log)} paid to {ECOCASH_NUMBER}\n\n"
    for s in recent: txt+=f"• {s['vpn']} {s['date']} ${s['amount']} ✅\n"
    bot.send_message(m.chat.id, txt + "\n/buy")

@bot.message_handler(commands=['trial'])
def cmd_trial(m): bot.send_message(m.chat.id, "🎁 Free trial - Family Pack ALL 12 $2 test - Money back guarantee - /buy to test")

@bot.message_handler(commands=['refer'])
def cmd_refer(m): bot.send_message(m.chat.id, f"👥 Refer & earn $0.50\nShare: https://t.me/reo_products_bot\nFriend pays $2 to {ECOCASH_NUMBER} you get $0.50\n/buy")

@bot.message_handler(commands=['support'])
def cmd_support(m): bot.send_message(m.chat.id, f"📞 Support 24/7\nOwner {ECOCASH_NAME}\nEcoCash {ECOCASH_NUMBER}\nDanil replies 1-5 mins")

@bot.message_handler(commands=['help'])
def cmd_help(m): bot.send_message(m.chat.id, f"📲 How to buy:\n1 /buy or /zol or /econet\n2 Pick VPN $2\n3 Pay $2 to {ECOCASH_NUMBER} via *153#\n4 Forward EcoCash SMS here\n5 Danil approves 1-5 mins\n6 File sent!\n/support")

@bot.message_handler(commands=['about'])
def cmd_about(m): bot.send_message(m.chat.id, f"⭐ About REO - 500+ Customers\nSince 2024 Harare\n💳 {ECOCASH_NUMBER} {ECOCASH_NAME}\n📡 ZOL - $2\n🌐 ECONET - $2\nAll $2 /buy")

@bot.message_handler(commands=['myvpn'])
def cmd_myvpn(m):
    my=[s for s in sales_log if s['user']==m.from_user.id]
    if not my: bot.send_message(m.chat.id, "❌ No purchases yet - /buy /zol /econet to order"); return
    last=my[-1]; bot.send_message(m.chat.id, f"📦 Last: {last['vpn']} {last['date']} - Resending..."); deliver(m.from_user.id, last['vpn'], last['txn'], last['amount'], "")

@bot.message_handler(commands=['status'])
def cmd_status(m):
    if m.from_user.id in pending_choice: bot.send_message(m.chat.id, f"⏳ Waiting payment for {pending_choice[m.from_user.id]} - Pay to {ECOCASH_NUMBER}")
    elif str(m.from_user.id) in pending_approval: bot.send_message(m.chat.id, f"⏳ Waiting Danil approval - {pending_approval[str(m.from_user.id)]['vpn']} 1-5 mins")
    else: bot.send_message(m.chat.id, "✅ No pending orders - /buy /zol /econet")

# --- ADMIN ONLY - CUSTOMER WILL NEVER SEE THESE ---
@bot.message_handler(commands=['pending'])
def cmd_pending(m):
    if m.from_user.id != ADMIN_ID: 
        bot.send_message(m.chat.id, "❌ Admin only - /buy to order VPN $2"); return
    if not pending_approval: bot.send_message(m.chat.id, "✅ No pending approvals"); return
    msg=f"⏳ PENDING MANUAL - TRUE {ECOCASH_NUMBER}\nTotal {len(pending_approval)}\n\n"
    for uid,data in pending_approval.items(): msg+=f"{uid} - {data['vpn']} - {data['txn']}\n/give {uid} {data['vpn']}\n\n"
    bot.send_message(m.chat.id, msg[:4000])

@bot.message_handler(commands=['give','approve','reject','block','clean_tafadzwa'])
def cmd_admin(m):
    if m.from_user.id != ADMIN_ID:
        bot.send_message(m.chat.id, "❌ Admin only - /buy to order VPN $2"); return
    
    if m.text.startswith("/give"):
        try:
            _, uid, *vpn = m.text.split(); uid=int(uid); vpn=" ".join(vpn)
            if "family" in vpn.lower(): vpn="FAMILY"
            deliver(uid, vpn, "MANUAL", 2.00, "admin")
            bot.send_message(m.chat.id, f"✅ Gave {vpn} to {uid}")
        except: bot.send_message(m.chat.id, "Usage: /give USERID VPN_TYPE\nExample: /give 123456789 ZOL")

# --- UNKNOWN COMMAND - FIXED - CUSTOMER NEVER SEES ADMIN ---
@bot.message_handler(func=lambda m: m.text and m.text.startswith('/'))
def cmd_unknown(m):
    if m.from_user.id == ADMIN_ID:
        # Admin sees admin commands
        bot.send_message(m.chat.id, f"🔐 ADMIN - TRUE {ECOCASH_NUMBER}\n\nCUSTOMER: /start /buy /zol /econet /price /proof /myvpn\n\nADMIN: /pending - list pending\n/give USERID VPN_TYPE - give file\n\nCustomer sends SMS you get APPROVE/REJECT buttons")
    else:
        # Customer sees ONLY customer commands - NO admin!
        bot.send_message(m.chat.id, f"🤖 REO VPN - TRUE {ECOCASH_NUMBER} {ECOCASH_NAME}\n\n📡 /zol - ZOL $2\n🌐 /econet - ECONET $2\n🛒 /buy - Choose ZOL or ECONET\n💰 /price - Price list\n✅ /proof - Live proofs\n📦 /myvpn - My VPNs\n📞 /support - Contact Danil\n\n👉 Tap to order:")
        menu_main(m.chat.id)
