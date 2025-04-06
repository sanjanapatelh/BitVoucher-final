# models.py
from datetime import datetime
from typing import Optional, Dict, Any

# First, we keep the dataclass models needed for the LNbits service
from dataclasses import dataclass

@dataclass
class Account:
    id: str
    user: str
    name: str
    adminkey: str
    inkey: str
    deleted: bool
    currency: str
    balance_msat: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    extra: Optional[Dict] = None


@dataclass
class Wallet:
    id: str
    user: str
    name: str
    adminkey: str
    inkey: str
    deleted: bool
    currency: str
    balance_msat: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    extra: Optional[Dict] = None


@dataclass
class WalletInfo:
    name: str
    balance: int


@dataclass
class Invoice:
    checking_id: str
    payment_hash: str
    wallet_id: str
    amount: int
    fee: int
    bolt11: str
    status: str
    memo: str
    expiry: datetime
    webhook: str
    webhook_status: int
    preimage: str
    tag: str
    extension: str
    time: datetime
    created_at: datetime
    updated_at: datetime
    extra: dict

# In a real application, these would be database models
# This is the original in-memory implementation with classes

class Recipient:
    def __init__(self, id, name, wallet_id, admin_key, invoice_key, daily_limit):
        self.id = id
        self.name = name
        self.wallet_id = wallet_id
        self.admin_key = admin_key
        self.invoice_key = invoice_key
        self.daily_limit = daily_limit
        self.created_at = datetime.now()
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "wallet_id": self.wallet_id,
            "admin_key": self.admin_key,
            "invoice_key": self.invoice_key,
            "daily_limit": self.daily_limit,
            "created_at": self.created_at
        }

class Vendor:
    def __init__(self, id, name, category):
        self.id = id
        self.name = name
        self.category = category
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category
        }

class Transaction:
    def __init__(self, id, recipient_id, vendor_id, amount, status="pending", transaction_type="payment", payment_hash=None):
        self.id = id
        self.recipient_id = recipient_id
        self.vendor_id = vendor_id
        self.amount = amount
        self.date = datetime.now()
        self.status = status
        self.type = transaction_type
        self.payment_hash = payment_hash
    
    def to_dict(self):
        return {
            "id": self.id,
            "recipient_id": self.recipient_id,
            "vendor_id": self.vendor_id,
            "amount": self.amount,
            "date": self.date,
            "status": self.status,
            "type": self.type,
            "payment_hash": self.payment_hash
        }