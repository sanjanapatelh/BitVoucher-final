# service.py
import requests
import json
from typing import Optional, Dict
from datetime import datetime

from models import Account, Wallet, WalletInfo, Invoice

class LNbits:
    """
    The class provides an example of basic operations with LNbits network.
    For other operations, refer to LNbits API reference: 
        https://demo.lnbits.com/docs
    """

    def __init__(self, url_base: str):
        self._URL_BASE = url_base.rstrip('/')  # Remove trailing slash if present

        self._API_V1_URL = f"{self._URL_BASE}/api/v1"

        self._ACCOUNTS_RESOURCE = f"{self._API_V1_URL}/account"
        self._WALLETS_RESOURCE = f"{self._API_V1_URL}/wallet"
        self._PAYMENTS_RESOURCE = f"{self._API_V1_URL}/payments"
        
        print(f"LNbits initialized with base URL: {self._URL_BASE}")
        print(f"API V1 URL: {self._API_V1_URL}")
        print(f"Accounts resource: {self._ACCOUNTS_RESOURCE}")
        print(f"Wallets resource: {self._WALLETS_RESOURCE}")
        print(f"Payments resource: {self._PAYMENTS_RESOURCE}")

    def create_account(self, name: str) -> Account:
        """
        Creates an LNbits account.

        Args:
            - name (str): the name of the account to be created

        Returns:
            - an Account object of the newly created account

        Raises:
            - an Exception if the operation did not succeed. 
                Check API reference & response body for details
        """
        print(f"Creating account with name: {name}")

        # Making the request
        response = requests.post(
            url=self._ACCOUNTS_RESOURCE,
            json={
                "name": name
            }
        )

        print(f"Create account response status: {response.status_code}")
        
        # Checking for errors
        if response.status_code != 200:
            error_message = f"Couldn't create an account.\n" \
                           f"Response status code: {response.status_code}\n" \
                           f"Response body: {response.text}"
            print(error_message)
            raise Exception(error_message)

        response_data = response.json()
        print(f"Account created successfully: {response_data}")
        
        # Converting a json dict into a model
        return Account(**response_data)
    
    def create_wallet(self, account_api_key: str, name: str) -> Wallet:
        """
        Creates an LNbits wallet.

        Args:
            - account_api_key (str): an API key of the account associated with the wallet
            - name (str): the name of the wallet to be created

        Returns:
            - a Wallet object of the newly created wallet

        Raises:
            - an Exception if the operation did not succeed. 
                Check API reference & response body for details
        """
        print(f"Creating wallet with name: {name} for account key: {account_api_key[:5]}...")

        # Making the request
        response = requests.post(
            url=self._WALLETS_RESOURCE,
            headers=self._get_header(account_api_key),
            json={
                "name": name
            }
        )

        print(f"Create wallet response status: {response.status_code}")
        
        # Checking for errors
        if response.status_code != 200:
            error_message = f"Couldn't create a wallet.\n" \
                           f"Response status code: {response.status_code}\n" \
                           f"Response body: {response.text}"
            print(error_message)
            raise Exception(error_message)

        response_data = response.json()
        print(f"Wallet created successfully: {response_data}")
        
        # Converting a json dict into a model
        return Wallet(**response_data)
    
    def get_wallet(self, wallet_key: str) -> Optional[WalletInfo]:
        """
        Fetches a wallet by its inkey or adminkey.

        Args:
            - wallet_key (str): the wallet's inkey or adminkey

        Returns:
            - a Wallet object
            - None if wallet does not exist

        Raises:
            - an Exception if the operation did not succeed. 
                Check API reference & response body for details
        """
        print(f"Getting wallet with key: {wallet_key[:5]}...")

        # Making the request
        response = requests.get(
            url=self._WALLETS_RESOURCE,
            headers=self._get_header(wallet_key)
        )

        print(f"Get wallet response status: {response.status_code}")
        
        # Wallet not found
        if response.status_code == 404: 
            print("Wallet not found")
            return None
        
        # Checking for errors
        if response.status_code != 200:
            error_message = f"Couldn't fetch the wallet.\n" \
                           f"Response status code: {response.status_code}\n" \
                           f"Response body: {response.text}"
            print(error_message)
            raise Exception(error_message)
        
        response_data = response.json()
        print(f"Wallet fetched successfully: {response_data}")
        
        # Converting a json dict into a model
        return WalletInfo(**response_data)
    
    def create_invoice(self, wallet_key: str, amount_sats: int, memo: str = "") -> Invoice:
        """
        Creates an invoice to be paid by another wallet.

        Args:
            - wallet_key (str): the wallet's inkey or adminkey
            - amount_sats (int): the amount in sats to be paid
            - memo (str, default ""): an arbitrary string to distinguish the payment among other

        Returns: 
            - an Invoice object

        Raises:
            - an Exception if the operation did not succeed. 
                Check API reference & response body for details
        """
        print(f"Creating invoice for amount: {amount_sats} sats, memo: {memo}, wallet key: {wallet_key[:5]}...")

        # Making the request with explicit out=False to create an invoice
        response = requests.post(
            url=self._PAYMENTS_RESOURCE,
            headers=self._get_header(wallet_key),
            json={
                "out": False,
                "amount": amount_sats,
                "memo": memo
            }
        )

        print(f"Create invoice response status: {response.status_code}")
        print(f"Create invoice response headers: {response.headers}")
        
        # Checking for errors
        if response.status_code != 201:
            error_message = f"Couldn't create an invoice.\n" \
                           f"Response status code: {response.status_code}\n" \
                           f"Response body: {response.text}"
            print(error_message)
            raise Exception(error_message)
        
        response_data = response.json()
        print(f"Invoice created successfully: {response_data}")
        
        # Handle datetime fields in the response
        if 'expiry' in response_data and isinstance(response_data['expiry'], str):
            response_data['expiry'] = datetime.fromisoformat(response_data['expiry'].replace('Z', '+00:00'))
        
        if 'time' in response_data and isinstance(response_data['time'], str):
            response_data['time'] = datetime.fromisoformat(response_data['time'].replace('Z', '+00:00'))
            
        if 'created_at' in response_data and isinstance(response_data['created_at'], str):
            response_data['created_at'] = datetime.fromisoformat(response_data['created_at'].replace('Z', '+00:00'))
            
        if 'updated_at' in response_data and isinstance(response_data['updated_at'], str):
            response_data['updated_at'] = datetime.fromisoformat(response_data['updated_at'].replace('Z', '+00:00'))
        
        # Ensure extra field is a dict
        if 'extra' not in response_data or response_data['extra'] is None:
            response_data['extra'] = {}
        
        # Converting a json dict into a model
        return Invoice(**response_data)
    
    def pay_invoice(self, wallet_adminkey: str, invoice: str) -> Invoice:
        """
        Pays an invoice.

        Args:
            - wallet_adminkey (str): the wallet's adminkey (inkey will NOT work)
            - invoice (str): the invoice to be paid

        Returns: 
            - an Invoice object

        Raises:
            - an Exception if the operation did not succeed. 
                Check API reference & response body for details
        """
        print(f"Paying invoice: {invoice[:20]}... with wallet key: {wallet_adminkey[:5]}...")

        # Making the request with explicit out=True to pay an invoice
        response = requests.post(
            url=self._PAYMENTS_RESOURCE,
            headers=self._get_header(wallet_adminkey),
            json={
                "out": True,
                "bolt11": invoice
            }
        )

        print(f"Pay invoice response status: {response.status_code}")
        
        # Checking for errors
        if response.status_code != 201 and response.status_code != 200:
            error_message = f"Couldn't pay the invoice.\n" \
                           f"Response status code: {response.status_code}\n" \
                           f"Response body: {response.text}"
            print(error_message)
            raise Exception(error_message)
        
        response_data = response.json()
        print(f"Invoice paid successfully: {response_data}")
        
        # Handle datetime fields in the response
        if 'expiry' in response_data and isinstance(response_data['expiry'], str):
            response_data['expiry'] = datetime.fromisoformat(response_data['expiry'].replace('Z', '+00:00'))
        
        if 'time' in response_data and isinstance(response_data['time'], str):
            response_data['time'] = datetime.fromisoformat(response_data['time'].replace('Z', '+00:00'))
            
        if 'created_at' in response_data and isinstance(response_data['created_at'], str):
            response_data['created_at'] = datetime.fromisoformat(response_data['created_at'].replace('Z', '+00:00'))
            
        if 'updated_at' in response_data and isinstance(response_data['updated_at'], str):
            response_data['updated_at'] = datetime.fromisoformat(response_data['updated_at'].replace('Z', '+00:00'))
            
        # Ensure extra field is a dict
        if 'extra' not in response_data or response_data['extra'] is None:
            response_data['extra'] = {}
        
        # Converting a json dict into a model
        return Invoice(**response_data)

    def _get_header(self, auth_key: str) -> Dict[str, str]:
        """
        Converts LNbits auth key into a header 
        that can be used for requests to LNbits API.

        Args:
            - auth_key (str): an auth key to be used in the header

        Returns:
            - a dict that contains the API key header with the auth_key in its value
        """
        return {
            "X-Api-Key": auth_key,
            "Content-type": "application/json"
        }