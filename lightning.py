# lightning.py
import requests
import json
import os
from typing import Optional, Dict, Any

# LNBits API Configuration
LNBITS_URL = os.getenv("LNBITS_URL", "http://localhost:5001")

def create_invoice(wallet_key: str, amount: int, memo: str = "") -> Optional[Dict[str, Any]]:
    """
    Creates a Lightning invoice using LNbits
    
    Args:
        wallet_key (str): The wallet's inkey
        amount (int): Amount in satoshis
        memo (str, optional): Description for the invoice
        
    Returns:
        Optional[Dict]: Invoice data or None if failed
    """
    try:
        # Print debug info
        print(f"Creating invoice with wallet_key: {wallet_key[:5] if wallet_key else 'None'}..., amount: {amount}, memo: {memo}")
        
        # Make a direct API call to create an invoice
        url = f"{LNBITS_URL}/api/v1/payments"
        headers = {
            "X-Api-Key": wallet_key,
            "Content-type": "application/json"
        }
        data = {
            "out": False,
            "amount": amount,
            "memo": memo
        }
        
        print(f"Sending request to: {url}")
        print(f"Request data: {data}")
        
        response = requests.post(url, headers=headers, json=data)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 201 or response.status_code == 200:
            invoice_data = response.json()
            print(f"Raw invoice data: {invoice_data}")
            
            # The key for the BOLT11 invoice could be different depending on the API version
            # Check multiple possible keys
            payment_request = None
            for key in ['payment_request', 'bolt11', 'pay_req']:
                if key in invoice_data and invoice_data[key]:
                    payment_request = invoice_data[key]
                    break
            
            if not payment_request:
                print("ERROR: No payment request/bolt11 found in invoice data!")
                print(f"Available keys: {list(invoice_data.keys())}")
                return None
            
            # Convert to our standardized format
            result = {
                "payment_hash": invoice_data.get("payment_hash", ""),
                "payment_request": payment_request,  # Use the found payment request
                "checking_id": invoice_data.get("checking_id", ""),
                "amount": amount,
                "memo": memo,
                "created_at": invoice_data.get("time", "")
            }
            
            print(f"Formatted invoice data: {result}")
            return result
        else:
            print(f"Error from LNbits API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        import traceback
        print(f"Exception creating invoice: {str(e)}")
        print(traceback.format_exc())
        return None()

def pay_invoice(wallet_adminkey: str, payment_request: str) -> Optional[Dict[str, Any]]:
    """
    Pays a Lightning invoice using LNbits
    
    Args:
        wallet_adminkey (str): The wallet's adminkey
        payment_request (str): The BOLT11 invoice to pay
        
    Returns:
        Optional[Dict]: Payment data or None if failed
    """
    try:
        # Print debug info
        print(f"Paying invoice with wallet_adminkey: {wallet_adminkey[:5] if wallet_adminkey else 'None'}..., payment_request: {payment_request[:20] if payment_request else 'None'}...")
        
        # Make a direct API call to pay an invoice
        url = f"{LNBITS_URL}/api/v1/payments"
        headers = {
            "X-Api-Key": wallet_adminkey,
            "Content-type": "application/json"
        }
        data = {
            "out": True,
            "bolt11": payment_request
        }
        
        print(f"Sending request to: {url}")
        print(f"Request data: {data}")
        
        response = requests.post(url, headers=headers, json=data)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 201 or response.status_code == 200:
            payment_data = response.json()
            print(f"Raw payment data: {payment_data}")
            
            # Convert to our standardized format
            result = {
                "payment_hash": payment_data.get("payment_hash", ""),
                "checking_id": payment_data.get("checking_id", ""),
                "amount": payment_data.get("amount", 0),
                "fee": payment_data.get("fee", 0),
                "status": payment_data.get("status", "")
            }
            
            print(f"Formatted payment data: {result}")
            return result
        else:
            print(f"Error from LNbits API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        import traceback
        print(f"Exception paying invoice: {str(e)}")
        print(traceback.format_exc())
        return None

def get_wallet_balance(wallet_key: str) -> int:
    """
    Gets the current balance of a wallet
    
    Args:
        wallet_key (str): The wallet's adminkey
        
    Returns:
        int: Wallet balance in satoshis (0 if error)
    """
    try:
        # Print debug info
        print(f"Getting wallet balance for key: {wallet_key[:5] if wallet_key else 'None'}...")
        
        # Make a direct API call to LNbits to get the wallet balance
        url = f"{LNBITS_URL}/api/v1/wallet"
        headers = {
            "X-Api-Key": wallet_key,
            "Content-type": "application/json"
        }
        
        print(f"Making direct API call to: {url}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            wallet_data = response.json()
            print(f"Raw wallet data: {wallet_data}")
            
            # Get balance in millisatoshis and convert to satoshis
            balance_msat = wallet_data.get("balance", 0)
            balance_sat = balance_msat // 1000
            
            print(f"Wallet balance: {balance_sat} sats (from {balance_msat} msats)")
            return balance_sat
        else:
            print(f"Error response from LNbits: Status {response.status_code}, Content: {response.text}")
            return 0
        
    except Exception as e:
        import traceback
        print(f"Exception getting balance: {str(e)}")
        print(traceback.format_exc())
        return 0

def get_wallet_transactions(wallet_key: str) -> list:
    """
    Gets transaction history for a wallet
    
    Args:
        wallet_key (str): The wallet's adminkey
        
    Returns:
        list: List of transactions
    """
    try:
        # Print debug info
        print(f"Getting transactions for wallet key: {wallet_key[:5] if wallet_key else 'None'}...")
        
        # Fetch transactions directly from LNbits API
        url = f"{LNBITS_URL}/api/v1/payments"
        headers = {
            "X-Api-Key": wallet_key,
            "Content-type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # Return parsed JSON of transactions
            transactions = response.json()
            print(f"Got {len(transactions)} transactions")
            return transactions
        else:
            print(f"Error getting transactions: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        import traceback
        print(f"Exception getting transactions: {str(e)}")
        print(traceback.format_exc())
        return []