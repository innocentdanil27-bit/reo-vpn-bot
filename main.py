import telebot
from telebot import types

BOT_TOKEN = "8931751932:AAHrky1vnNFVztV-kYipcRFpOo9kO7aABJo"
ADMIN_ID = 8579468852

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(m):
    text1 = "What you get:\n• 30 Days Unlimited\n• All apps supported\n• Instant delivery after payment\n• 24/7 Support - 0775713879\n\n👇 Tap to start:"
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🛒 BUY VPN - $2", callback_data="buy"),
        types.InlineKeyboardButton("📖 How to Install VPN", callback_data="how"),
        types.InlineKeyboardButton("📞 Support", callback_data="sup")
    )
    bot.send_message(m.chat.id, text1, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    d = call.data
    if d == "buy":
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("NapsternetV", callback_data="vpn1"),
            types.InlineKeyboardButton("HTTP Custom", callback_data="vpn2"),
            types.InlineKeyboardButton("Dark Tunnel", callback_data="vpn3"),
            types.InlineKeyboardButton("TLS Tunnel", callback_data="vpn4"),
            types.InlineKeyboardButton("eHi Tunnel", callback_data="vpn5"),
            types.InlineKeyboardButton("Stark VPN", callback_data="vpn6"),
            types.InlineKeyboardButton("HA Tunnel", callback_data="vpn7")
        )
        bot.send_message(call.message.chat.id, "Choose VPN - $2:", reply_markup=kb)
    elif d == "how":
        text2 = "📖 HOW TO USE VPN - 3 Steps\n\n1️⃣ Buy: Click Buy VPN → Choose → Pay $2 to 0775713879 → Forward EcoCash SMS\n\n2️⃣ Install App:\n• NapsternetV - from PlayStore\n• HTTP Custom - from PlayStore\n• Dark Tunnel - from PlayStore\n\n3️⃣ Import File:\n   Open App → Tap + → Import Config → Select file I send you → TAP CONNECT\n\n✅ Done! Enjoy free net 🔥\n\nNeed help? 0775713879"
        bot.send_message(call.message.chat.id, text2)
    elif d == "sup":
        bot.send_message(call.message.chat.id, "Support: 0775713879")

print("ONLINE")
bot.infinity_polling()
