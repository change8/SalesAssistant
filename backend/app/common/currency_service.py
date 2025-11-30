import re
import requests
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.app.common.models import ExchangeRate
from backend.app.core.database import SessionLocal

# Cache rates in memory briefly to avoid DB hits on every row
_RATE_CACHE = {}
_LAST_CACHE_UPDATE = None

def update_exchange_rates(db: Session):
    """Fetch latest rates from API and update DB."""
    try:
        # Using a free API (e.g., exchangerate-api.com or similar)
        # Base: CNY. If API doesn't support Base CNY for free, fetch USD and convert.
        # frankfurter.app is free and supports base.
        response = requests.get("https://api.frankfurter.app/latest?from=CNY")
        if response.status_code == 200:
            data = response.json()
            rates = data.get("rates", {})
            
            # Update DB
            # Note: Frankfurter gives rates FROM CNY. So 1 CNY = X USD.
            # We want to convert TO CNY. So we need rate X Foreign = 1 CNY?
            # No, usually we have Foreign Amount, want CNY.
            # If 1 CNY = 0.14 USD, then 1 USD = 1/0.14 CNY.
            # Let's store the rate TO CNY.
            
            for currency, rate_from_cny in rates.items():
                if rate_from_cny == 0: continue
                rate_to_cny = 1 / rate_from_cny
                
                db_rate = db.get(ExchangeRate, currency)
                if not db_rate:
                    db_rate = ExchangeRate(currency_code=currency)
                    db.add(db_rate)
                
                db_rate.rate_to_cny = rate_to_cny
                db_rate.updated_at = datetime.now()
            
            # Also ensure USD is there (Frankfurter might not have all, but usually does)
            # Add CNY itself
            cny_rate = db.get(ExchangeRate, "CNY")
            if not cny_rate:
                cny_rate = ExchangeRate(currency_code="CNY", rate_to_cny=1.0, updated_at=datetime.now())
                db.add(cny_rate)
            else:
                cny_rate.rate_to_cny = 1.0
                cny_rate.updated_at = datetime.now()
                
            db.commit()
            print("Exchange rates updated successfully.")
    except Exception as e:
        print(f"Failed to update exchange rates: {e}")

def get_rate(currency: str) -> float:
    """Get rate to convert Currency -> CNY."""
    global _RATE_CACHE, _LAST_CACHE_UPDATE
    
    # Refresh cache if empty or old (e.g. 1 hour)
    if not _RATE_CACHE or not _LAST_CACHE_UPDATE or datetime.now() - _LAST_CACHE_UPDATE > timedelta(hours=1):
        with SessionLocal() as db:
            rates = db.query(ExchangeRate).all()
            if not rates:
                # Try update if empty
                update_exchange_rates(db)
                rates = db.query(ExchangeRate).all()
            
            _RATE_CACHE = {r.currency_code: r.rate_to_cny for r in rates}
            _LAST_CACHE_UPDATE = datetime.now()
    
    return _RATE_CACHE.get(currency.upper(), 1.0) # Default 1.0 if not found

def convert_and_format(amount_str: str) -> str:
    """
    Parse amount string, convert to CNY if needed, and format.
    Input: "美元 5000.00" or "中国人民币 1000"
    Output: "¥ 1,000.00" or "$ 5,000.00 (¥ 35,000.00)"
    """
    if not amount_str:
        return "-"
        
    # 1. Parse Currency and Amount
    # Common prefixes in this dataset: "中国人民币", "美元", "日元", "欧元"
    # Regex to separate non-digits from digits
    match = re.match(r"^([^\d\s]+)\s*([\d,.]+)", amount_str.strip())
    if not match:
        return amount_str # Return as is if parse fails
        
    currency_name = match.group(1).strip()
    amount_val_str = match.group(2).replace(',', '')
    
    try:
        amount = float(amount_val_str)
    except:
        return amount_str
        
    # 2. Map Currency Name to Code & Symbol
    currency_map = {
        "中国人民币": {"code": "CNY", "symbol": "¥"},
        "人民币": {"code": "CNY", "symbol": "¥"},
        "美元": {"code": "USD", "symbol": "$"},
        "日元": {"code": "JPY", "symbol": "JP¥"}, # Or just 日元 symbol? User said "日元或其他币种保持现在的中文币种名"
        "欧元": {"code": "EUR", "symbol": "€"},
        "英镑": {"code": "GBP", "symbol": "£"},
    }
    
    info = currency_map.get(currency_name)
    
    # User rule: "中国人民币换成¥ ，美元换成$，日元或其他币种保持现在的中文币种名显示"
    if info:
        display_symbol = info["symbol"]
        code = info["code"]
    else:
        display_symbol = currency_name # Keep original name
        # Try to guess code? If unknown, assume 1:1 or skip conversion
        code = None

    # Format original amount
    formatted_original = f"{display_symbol} {amount:,.2f}"
    
    # 3. Convert if not CNY
    if code and code != "CNY":
        rate = get_rate(code)
        cny_amount = amount * rate
        formatted_cny = f"¥ {cny_amount:,.2f}"
        return f"{formatted_original}（{formatted_cny}）"
    
    return formatted_original
