# utils.py
import json
import hashlib
from datetime import datetime, time

def generate_id(prefix=""):
    """Generate a unique ID with optional prefix"""
    timestamp = str(datetime.now().timestamp())
    hash_obj = hashlib.sha256(timestamp.encode())
    return f"{prefix}{hash_obj.hexdigest()[:8]}"

def get_today_range():
    """Get datetime range for today"""
    today = datetime.now().date()
    return datetime.combine(today, time.min), datetime.combine(today, time.max)

def calculate_spent_today(transactions, recipient_id):
    """Calculate how much a recipient has spent today"""
    today_start, today_end = get_today_range()
    
    print(f"Calculating spent today for recipient {recipient_id}")
    print(f"Today range: {today_start} to {today_end}")
    print(f"Number of transactions: {len(transactions)}")
    
    # Filter transactions that are:
    # 1. For this recipient
    # 2. Happened today
    # 3. Are complete
    # 4. Are payments (not deposits)
    today_transactions = []
    
    for t in transactions:
        # Debug info
        print(f"Checking transaction: {t['id']}")
        
        # Check recipient ID
        if t["recipient_id"] != recipient_id:
            print(f"  Skip: Different recipient ({t['recipient_id']})")
            continue
        
        # Check date - handle both string and datetime objects
        tx_date = t["date"]
        if isinstance(tx_date, str):
            try:
                tx_date = datetime.fromisoformat(tx_date.replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Try another common format
                    tx_date = datetime.strptime(tx_date, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    print(f"  Skip: Invalid date format ({tx_date})")
                    continue
        
        if not (today_start <= tx_date <= today_end):
            print(f"  Skip: Not today ({tx_date})")
            continue
        
        # Check status and type
        if t["status"] != "complete":
            print(f"  Skip: Status not complete ({t['status']})")
            continue
            
        if t["type"] != "payment":
            print(f"  Skip: Not a payment ({t['type']})")
            continue
        
        # This transaction passes all filters
        print(f"  Include: {t['id']} - {t['amount']} sats")
        today_transactions.append(t)
    
    # Sum the amounts of filtered transactions
    total_spent = sum(t["amount"] for t in today_transactions)
    print(f"Total spent today: {total_spent} sats")
    return total_spent

def load_data(filename):
    """Load data from JSON file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(data, filename):
    """Save data to JSON file"""
    with open(filename, 'w') as f:
        json.dump(data, f, default=str)

def format_datetime(dt):
    """Format datetime for display"""
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def format_sats(amount):
    """Format satoshis with commas for readability"""
    return f"{amount:,}"