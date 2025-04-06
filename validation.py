# validation.py
from datetime import datetime
from lightning import get_wallet_balance
from utils import calculate_spent_today

def validate_transaction(recipient_id, vendor_id, amount, recipients, vendors, transactions):
    """
    Validates a transaction based on:
    1. Vendor whitelist
    2. Daily spending limits
    3. Available balance
    4. Vendor category restrictions
    
    Args:
        recipient_id (str): ID of the recipient
        vendor_id (str): ID of the vendor
        amount (int): Transaction amount in satoshis
        recipients (dict): Dictionary of recipients
        vendors (dict): Dictionary of vendors
        transactions (list): List of past transactions
    
    Returns:
        tuple: (bool, str) indicating if transaction is valid and a message
    """
    print(f"Validating transaction: recipient={recipient_id}, vendor={vendor_id}, amount={amount}")
    
    # Check if vendor exists and is approved
    if vendor_id not in vendors:
        return False, "Vendor not approved for subsidy program"
    
    # Retrieve recipient information
    recipient = recipients.get(recipient_id)
    if not recipient:
        return False, "Recipient not found"
    
    # Validate vendor category
    vendor_category = vendors[vendor_id]["category"]
    allowed_categories = ["food", "medicine"]  # From config 
    if vendor_category not in allowed_categories:
        return False, f"Category '{vendor_category}' is not approved for subsidy"
    
    # Check daily spending limit
    try:
        # Calculate total spent today
        spent_today = calculate_spent_today(transactions, recipient_id)
        print(f"Spent today: {spent_today} sats, daily limit: {recipient.get('daily_limit', 10000)} sats")
        
        # Check if this transaction would exceed daily limit
        if spent_today + amount > recipient.get("daily_limit", 10000):  # Default 10000 sats
            return False, (
                f"Daily spending limit exceeded "
                f"(limit: {recipient['daily_limit']} sats, "
                f"already spent: {spent_today} sats)"
            )
    except Exception as e:
        print(f"Error checking daily limit: {str(e)}")
        return False, f"Error checking daily limit: {str(e)}"
    
    # Check wallet balance
    try:
        balance = get_wallet_balance(recipient["adminkey"])
        print(f"Wallet balance: {balance} sats, required: {amount} sats")
        
        if balance < amount:
            return False, (
                f"Insufficient balance "
                f"(balance: {balance} sats, "
                f"required: {amount} sats)"
            )
    except Exception as e:
        print(f"Error checking wallet balance: {str(e)}")
        return False, f"Error checking wallet balance: {str(e)}"
    
    # If all checks pass, transaction is valid
    return True, "Transaction validated successfully"