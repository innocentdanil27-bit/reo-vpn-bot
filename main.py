def confirm_payment(text):
    upper=text.upper()
    lower=text.lower()
    
    # 1. MUST BE REAL ECOCASH FORMAT - NOT TYPED
    if not text.startswith("Cashin Confirmation:"):
        return False, "Fake! Must start with 'Cashin Confirmation:'", None, None, None
    if "received from" not in lower:
        return False, "Fake! No 'received from'", None, None, None
    if "approval code:" not in lower:
        return False, "Fake! No Approval Code line", None, None, None
    if "new balance:" not in lower:
        return False, "Fake! No New Balance line", None, None, None
    if "transact using the super app" not in lower:
        return False, "Fake! Must have Super App line", None, None, None

    amt_m=re.search(r'USD\s*\$?\s*(\d+\.?\d*)', upper)
    if not amt_m: return False, "No USD amount", None, None, None
    amount=float(amt_m.group(1))
    if amount < 2.0: return False, f"Amount USD {amount} < $2", None, None, None
    
    # Strict CI format: CIYYMMDD.HHMM.T + numbers
    app_m=re.search(r'CI\d{6}\.\d{3,4}\.T\d{6,10}', upper)
    if not app_m: return False, "Invalid Approval Code Format", None, None, None
    txn_id=app_m.group(0)
    if hash_txn(txn_id) in used_txns:
        return False, f"ALREADY USED {txn_id}", None, None, None

    today = datetime.now().date()
    today_str = today.strftime('%d/%m/%Y')
    dm=re.search(r'CI(\d{2})(\d{2})(\d{2})', upper)
    if dm:
        y,mn,d=dm.groups()
        try:
            full_year=2000+int(y)
            if full_year < 2026 or full_year > 2030:
                return False, f"REJECTED {d}/{mn}/{full_year} - Only 2026-2030", f"{d}/{mn}/{full_year}", txn_id, amount
            txn_date_str=f"{d}/{mn}/{full_year}"
            dt=datetime.strptime(txn_date_str, '%d/%m/%Y').date()
            if dt != today:
                return False, f"OLD DATE {txn_date_str} - TODAY {today_str} ONLY! No yesterday!", txn_date_str, txn_id, amount
        except:
            return False, f"Invalid Date", None, None, None
    else:
        return False, "No CI date", None, None, None
    
    return True, f"CONFIRMED USD {amount}", txn_date_str, txn_id, amount

def send_file(uid, vtype, txn_id, txn_date, amount, username=""):
    files=get_files()
    used_txns.add(hash_txn(txn_id))
    try:
        if vtype=="FAMILY":
            for f in files:
                with open(f"configs/{f}",'rb') as doc:
                    bot.send_document(uid, doc, caption=f"✅ Family Pack $2\nTxn:{txn_id}\nDate:{txn_date}")
        else:
            if files:
                with open(f"configs/{files[0]}",'rb') as doc:
                    bot.send_document(uid, doc, caption=f"✅ {vtype} $2\nTxn:{txn_id}\nDate:{txn_date}")
        bot.send_message(uid, f"💚 USD {amount} CONFIRMED!\nTxn:{txn_id}\nDate:{txn_date}\nFile sent!")
        pending.pop(uid,None)
        transactions_log.append({"user":uid,"username":username,"app":vtype,"txn_id":txn_id,"txn_date":txn_date,"amount":amount,"confirm":datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        save_backup()
        # FIXED: Don't send NEW SALE to customer if customer is admin (testing)
        if uid != ADMIN_ID:
            bot.send_message(ADMIN_ID, f"🔔 NEW SALE $2!\n💰 USD {amount}\n📱 App: {vtype}\n👤 User: {uid} @{username}\n🧾 Txn: {txn_id}\n📅 Date: {txn_date}\n⏰ Now: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n💳 To: 0775713879\n✅ FILE SENT\n📊 Total: {len(transactions_log)}")
    except Exception as e:
        if uid != ADMIN_ID:
            bot.send_message(ADMIN_ID, f"Error {e}")
