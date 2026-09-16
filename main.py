def confirm_payment(text):
    upper=text.upper()
    lower=text.lower()
    if "confirmation" not in lower and "ecocash" not in lower:
        return False, "Not EcoCash", None, None, None
    amt_m=re.search(r'USD\s*\$?\s*(\d+\.?\d*)', upper)
    if not amt_m: return False, "No USD amount", None, None, None
    amount=float(amt_m.group(1))
    if amount < 2.0: return False, f"Amount USD {amount} < $2", None, None, None
    app_m=re.search(r'(CI\d{6}\.\d+\.T\d+|MP\d+|TXN[A-Z0-9]+)', upper)
    if not app_m: return False, "No Approval Code", None, None, None
    txn_id=app_m.group(1)
    if hash_txn(txn_id) in used_txns:
        return False, f"ALREADY USED {txn_id}", None, None, None
    
    # SECURED: TODAY ONLY - 2026 to 2030 - NO YESTERDAY!
    today = datetime.now().date()
    today_str = today.strftime('%d/%m/%Y')
    txn_date_str = today_str
    
    dm=re.search(r'CI(\d{2})(\d{2})(\d{2})', upper)
    if dm:
        y,mn,d=dm.groups()  # YY MM DD
        try:
            full_year=2000+int(y)
            # ONLY 2026-2030
            if full_year < 2026 or full_year > 2030:
                return False, f"❌ REJECTED {d}/{mn}/{full_year} - Only 2026-2030 allowed", f"{d}/{mn}/{full_year}", txn_id, amount
            txn_date_str=f"{d}/{mn}/{full_year}"
            dt=datetime.strptime(txn_date_str, '%d/%m/%Y').date()
            # TODAY ONLY - NO YESTERDAY!
            if dt != today:
                return False, f"❌ OLD DATE {txn_date_str} - Must be TODAY {today_str} ONLY! No yesterday!", txn_date_str, txn_id, amount
        except Exception as e:
            return False, f"❌ Invalid Date {txn_date_str}", txn_date_str, txn_id, amount
    else:
        # If no CI date, must still be today (we use today as date)
        pass
    
    return True, f"CONFIRMED USD {amount}", txn_date_str, txn_id, amount
