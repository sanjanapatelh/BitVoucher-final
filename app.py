# app.py initialization section - replace this at the top of app.py
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
import requests
import json
import os
from datetime import datetime

# Import our modules
from validation import validate_transaction
from lightning import create_invoice, pay_invoice, get_wallet_balance
from utils import calculate_spent_today, generate_id

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key")  # Use environment variable

# LNBits API Configuration
LNBITS_URL = os.getenv("LNBITS_URL", "http://localhost:5001")
ADMIN_KEY = os.getenv("ADMIN_KEY", "9bca41d2b0f540f08393cde5dd13b178")  # Your admin key

# Add this code after the configuration to validate the setup
if not ADMIN_KEY:
    print("WARNING: ADMIN_KEY environment variable is not set. Using default key.")

# Test the connection and print detailed info
try:
    print(f"Testing connection to LNbits with admin key: {ADMIN_KEY[:5]}...")
    
    # Make a direct API call to check the wallet
    response = requests.get(
        f"{LNBITS_URL}/api/v1/wallet",
        headers={"X-Api-Key": ADMIN_KEY, "Content-type": "application/json"}
    )
    
    if response.status_code == 200:
        wallet_data = response.json()
        balance_msat = wallet_data.get("balance", 0)
        balance_sat = balance_msat // 1000
        
        print(f"Successfully connected to LNbits wallet")
        print(f"Wallet name: {wallet_data.get('name', 'Unknown')}")
        print(f"Balance: {balance_sat} sats ({balance_msat} msats)")
    else:
        print(f"Failed to connect to LNbits wallet: Status code {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Failed to connect to LNbits wallet: {str(e)}")

# Import LNbits service class after initializing configuration
from service import LNbits
lnbits_client = None  # Will be initialized when needed

# Persistent storage for recipients and vendors
recipients = {}
vendors = {}
transactions = []

# Routes
@app.route('/')
def index():
    """Home page route"""
    return render_template('index.html')

# Admin Routes
@app.route('/admin')
@app.route('/admin')
def admin_dashboard():
    """Admin dashboard route with wallet balances"""
    
    # Fetch balance for all recipients
    recipient_balances = {}
    for recipient_id, recipient in recipients.items():
        try:
            if 'adminkey' in recipient:
                # Try to get balance from LNbits
                balance = get_wallet_balance(recipient['adminkey'])
                recipient_balances[recipient_id] = balance
        except Exception as e:
            print(f"Error getting balance for recipient {recipient_id}: {str(e)}")
            # Calculate from transactions as fallback
            deposits = sum(t["amount"] for t in transactions 
                        if t["recipient_id"] == recipient_id 
                        and t["type"] == "deposit" 
                        and t["status"] == "complete")
            
            payments = sum(t["amount"] for t in transactions 
                         if t["recipient_id"] == recipient_id 
                         and t["type"] == "payment" 
                         and t["status"] == "complete")
            
            recipient_balances[recipient_id] = deposits - payments
    
    # Fetch balance for all vendors
    vendor_balances = {}
    for vendor_id, vendor in vendors.items():
        try:
            if 'adminkey' in vendor:
                # Try to get balance from LNbits
                balance = get_wallet_balance(vendor['adminkey'])
                vendor_balances[vendor_id] = balance
        except Exception as e:
            print(f"Error getting balance for vendor {vendor_id}: {str(e)}")
            # For vendors, we can estimate based on received payments
            received = sum(t["amount"] for t in transactions 
                         if t["vendor_id"] == vendor_id 
                         and t["type"] == "payment" 
                         and t["status"] == "complete")
            
            vendor_balances[vendor_id] = received
    
    return render_template('admin/dashboard.html', 
                          recipients=recipients,
                          recipient_balances=recipient_balances,
                          vendors=vendors,
                          vendor_balances=vendor_balances,
                          transactions=transactions)


@app.route('/admin/add_recipient', methods=['GET', 'POST'])
def add_recipient():
    if request.method == 'POST':
        try:
            # Create a new account for the recipient using LNbits service
            recipient_name = request.form['name']
            daily_limit = int(request.form['daily_limit'])
            
            # Import LNbits module properly - this ensures lnbits_client is defined
            from service import LNbits
            
            # Create or reuse the global lnbits_client
            global lnbits_client
            if not lnbits_client:
                lnbits_client = LNbits(LNBITS_URL)
            
            # Create LNbits account
            account = lnbits_client.create_account(name=f"Subsidy-{recipient_name}")
            
            # Create wallet for the account
            wallet = lnbits_client.create_wallet(
                account_api_key=account.adminkey,
                name=f"{recipient_name}-wallet"
            )
            
            # Store recipient info
            recipient_id = generate_id("R")
            recipients[recipient_id] = {
                "name": recipient_name,
                "wallet_id": wallet.id,
                "adminkey": wallet.adminkey,
                "inkey": wallet.inkey,
                "daily_limit": daily_limit,
                "created_at": datetime.now()
            }
            
            flash(f'Recipient {recipient_name} added successfully')
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            flash(f'Error creating account: {str(e)}')
    
    return render_template('admin/add_recipient.html')


# Replace the fund_recipient function in app.py with this updated version

@app.route('/admin/fund_recipient/<recipient_id>', methods=['GET', 'POST'])
def fund_recipient(recipient_id):
    # Ensure the recipient exists
    if recipient_id not in recipients:
        flash('Recipient not found')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        try:
            amount = int(request.form['amount'])
            recipient = recipients.get(recipient_id)
        
            if not recipient:
                flash('Recipient not found')
                return redirect(url_for('admin_dashboard'))
            
            # Use the global ADMIN_KEY to get the admin wallet balance
            admin_balance = get_wallet_balance(ADMIN_KEY)
            
            print(f"Admin wallet balance: {admin_balance} sats")
            
            if admin_balance < amount:
                flash(f'Insufficient balance in admin wallet. Current balance: {admin_balance} sats, Requested: {amount} sats')
                return redirect(url_for('fund_recipient', recipient_id=recipient_id))
            
            # Create an invoice for funding from the recipient's wallet
            inkey = recipient['inkey']
            
            print(f"Creating invoice with inkey: {inkey}, amount: {amount}")
            
            # Create the invoice
            invoice = create_invoice(
                wallet_key=inkey,
                amount=amount, 
                memo=f"Subsidy funding for {recipient['name']}"
            )
            
            if not invoice or 'payment_request' not in invoice:
                raise Exception(f"Failed to create invoice: {invoice}")
            
            print(f"Created invoice: {invoice}")
            
            # Automatically pay the invoice using the admin wallet
            payment = pay_invoice(
                wallet_adminkey=ADMIN_KEY,
                payment_request=invoice["payment_request"]
            )
            
            if not payment or 'payment_hash' not in payment:
                raise Exception(f"Failed to pay invoice: {payment}")
            
            print(f"Payment successful: {payment}")
            
            # Record the transaction as complete
            transaction_id = generate_id("T")
            transactions.append({
                "id": transaction_id,
                "recipient_id": recipient_id,
                "vendor_id": "admin",
                "amount": amount,
                "date": datetime.now(),
                "status": "complete",
                "type": "deposit",
                "payment_hash": payment["payment_hash"]
            })
            
            flash(f'Recipient {recipient["name"]} funded successfully with {amount} sats')
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            import traceback
            print(f"Error funding recipient: {str(e)}")
            print(traceback.format_exc())
            flash(f'Error funding recipient: {str(e)}')
    
    # GET request - display the form
    recipient = recipients.get(recipient_id)
    
    # Get admin wallet balance for display
    admin_balance = get_wallet_balance(ADMIN_KEY)
    
    return render_template('admin/fund_recipient.html', 
                          recipient_id=recipient_id, 
                          recipients=recipients, 
                          recipient=recipient,
                          admin_balance=admin_balance)

@app.route('/admin/vendors')
def vendor_list():
    return render_template('admin/vendors.html', vendors=vendors)

@app.route('/admin/add_vendor', methods=['GET', 'POST'])
def add_vendor():
    if request.method == 'POST':
        try:
            # Create a new account for the vendor
            vendor_name = request.form['name']
            vendor_category = request.form['category']
            
            # Create LNbits account
            account = lnbits_client.create_account(name=f"Vendor-{vendor_name}")
            
            # Create wallet for the vendor
            wallet = lnbits_client.create_wallet(
                account_api_key=account.adminkey,
                name=f"{vendor_name}-wallet"
            )
            
            # Store vendor info
            vendor_id = generate_id("V")
            vendors[vendor_id] = {
                "name": vendor_name,
                "category": vendor_category,
                "wallet_id": wallet.id,
                "adminkey": wallet.adminkey,
                "inkey": wallet.inkey
            }
            
            flash('Vendor added successfully')
            return redirect(url_for('vendor_list'))
            
        except Exception as e:
            flash(f'Error creating vendor: {str(e)}')
    
    return render_template('admin/add_vendor.html')

# Recipient Routes
@app.route('/recipient_list')
def recipient_list():
    """Route to display all recipients"""
    return render_template('recipient/list.html', 
                          recipients=recipients)

@app.route('/recipient/<recipient_id>')
def recipient_dashboard(recipient_id):
    # Ensure the recipient exists
    if recipient_id not in recipients:
        flash('Recipient not found')
        return redirect(url_for('index'))
    
    try:
        recipient = recipients[recipient_id]
        
        # Check if recipient has the required keys
        if 'adminkey' not in recipient:
            flash('Recipient wallet not properly configured')
            return redirect(url_for('index'))
        
        # Get recipient's wallet balance
        try:
            # Try to get the balance from LNbits
            balance = get_wallet_balance(recipient['adminkey'])
            print(f"Got wallet balance for {recipient['name']}: {balance} sats")
        except Exception as e:
            print(f"Error getting wallet balance: {str(e)}")
            
            # Fall back to calculating balance from transactions
            deposits = sum(t["amount"] for t in transactions 
                        if t["recipient_id"] == recipient_id 
                        and t["type"] == "deposit" 
                        and t["status"] == "complete")
            
            payments = sum(t["amount"] for t in transactions 
                         if t["recipient_id"] == recipient_id 
                         and t["type"] == "payment" 
                         and t["status"] == "complete")
            
            balance = deposits - payments
            print(f"Calculated balance from transactions: {balance} sats")
        
        # Get recipient's transactions
        recipient_transactions = [t for t in transactions if t["recipient_id"] == recipient_id]
        
        return render_template('recipient/dashboard.html',
                              recipients=recipients,  # Pass full recipients dict
                              recipient_id=recipient_id,
                              balance=balance,
                              transactions=recipient_transactions,
                              vendors=vendors)
    except Exception as e:
        import traceback
        print(f"Error in recipient dashboard: {str(e)}")
        print(traceback.format_exc())
        flash(f'Error getting wallet info: {str(e)}')
        return redirect(url_for('index'))


@app.route('/recipient/<recipient_id>/pay', methods=['GET', 'POST'])
def make_payment(recipient_id):
    recipient = recipients.get(recipient_id)
    if not recipient:
        flash('Recipient not found')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            vendor_id = request.form['vendor_id']
            amount = int(request.form['amount'])
            
            # Validate payment
            valid, message = validate_transaction(
                recipient_id, vendor_id, amount, 
                recipients, vendors, transactions
            )
            
            if not valid:
                flash(message)
                return redirect(url_for('make_payment', recipient_id=recipient_id))
            
            try:
                # Find the vendor's invoice key
                vendor = vendors[vendor_id]
                
                # Create an invoice from the vendor
                vendor_invoice = create_invoice(
                    wallet_key=vendor['inkey'], 
                    amount=amount, 
                    memo=f"Payment from {recipient['name']}"
                )
                
                if not vendor_invoice:
                    raise Exception("Failed to create vendor invoice")
                
                # AUTOMATIC PAYMENT: Pay the invoice directly instead of just displaying it
                payment = pay_invoice(
                    wallet_adminkey=recipient['adminkey'],
                    payment_request=vendor_invoice["payment_request"]
                )
                
                if not payment or 'payment_hash' not in payment:
                    raise Exception(f"Failed to pay invoice: {payment}")
                
                print(f"Payment successful: {payment}")
                
                # Record the transaction as complete
                transaction_id = generate_id("T")
                transactions.append({
                    "id": transaction_id,
                    "recipient_id": recipient_id,
                    "vendor_id": vendor_id,
                    "amount": amount,
                    "date": datetime.now(),
                    "status": "complete",  # Mark as complete since we paid it
                    "type": "payment",
                    "payment_hash": payment["payment_hash"]
                })
                
                # Redirect to dashboard with success message
                flash(f'Payment of {amount} sats to {vendor["name"]} completed successfully')
                return redirect(url_for('recipient_dashboard', recipient_id=recipient_id))
                
            except Exception as e:
                import traceback
                print(f"Error processing vendor payment: {str(e)}")
                print(traceback.format_exc())
                flash(f'Error processing vendor payment: {str(e)}')
                
        except Exception as e:
            import traceback
            print(f"Error processing payment: {str(e)}")
            print(traceback.format_exc())
            flash(f'Error processing payment: {str(e)}')
        
    return render_template('recipient/payment.html', 
                          recipient_id=recipient_id,
                          vendors=vendors)

# Vendor Routes
@app.route('/vendor/generate_invoice', methods=['GET', 'POST'])
def vendor_generate_invoice():
    if request.method == 'POST':
        vendor_id = request.form['vendor_id']
        recipient_id = request.form['recipient_id']
        amount = int(request.form['amount'])
        
        # Validate the transaction
        valid, message = validate_transaction(
            recipient_id, vendor_id, amount, 
            recipients, vendors, transactions
        )
        
        if not valid:
            flash(message)
            return redirect(url_for('vendor_generate_invoice'))
        
        try:
            # Get the vendor's LNbits wallet
            vendor = vendors[vendor_id]
            
            # Create invoice
            invoice = create_invoice(
                wallet_key=vendor['inkey'], 
                amount=amount, 
                memo=f"Payment from recipient {recipient_id}"
            )
            
            if not invoice:
                raise Exception("Failed to create invoice")
            
            # Record the transaction
            transaction_id = generate_id("T")
            transactions.append({
                "id": transaction_id,
                "recipient_id": recipient_id,
                "vendor_id": vendor_id,
                "amount": amount,
                "date": datetime.now(),
                "status": "pending",
                "type": "payment",
                "payment_hash": invoice["payment_hash"]
            })
            
            return render_template('vendor/invoice.html', 
                                 invoice=invoice, 
                                 recipient_id=recipient_id,
                                 vendor_id=vendor_id)
        except Exception as e:
            flash(f'Error generating invoice: {str(e)}')
    
    return render_template('vendor/generate_invoice.html', 
                          vendors=vendors, 
                          recipients=recipients)

# API Routes (for integration with payment systems)
@app.route('/api/validate_payment', methods=['POST'])
def api_validate_payment():
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400
    
    recipient_id = data.get('recipient_id')
    vendor_id = data.get('vendor_id')
    amount = data.get('amount')
    
    if not all([recipient_id, vendor_id, amount]):
        return jsonify({"success": False, "message": "Missing required fields"}), 400
    
    # Validate the payment
    valid, message = validate_transaction(
        recipient_id, vendor_id, int(amount), 
        recipients, vendors, transactions
    )
    
    return jsonify({
        "success": valid,
        "message": message
    })

@app.route('/api/record_transaction', methods=['POST'])
def api_record_transaction():
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400
    
    recipient_id = data.get('recipient_id')
    vendor_id = data.get('vendor_id')
    amount = data.get('amount')
    payment_hash = data.get('payment_hash')
    
    if not all([recipient_id, vendor_id, amount, payment_hash]):
        return jsonify({"success": False, "message": "Missing required fields"}), 400
    
    # Record the transaction
    transaction_id = generate_id("T")
    transactions.append({
        "id": transaction_id,
        "recipient_id": recipient_id,
        "vendor_id": vendor_id,
        "amount": int(amount),
        "date": datetime.now(),
        "status": "complete",
        "type": "payment",
        "payment_hash": payment_hash
    })
    
    return jsonify({
        "success": True,
        "transaction_id": transaction_id
    })

@app.route('/vendor/<vendor_id>')
def vendor_dashboard(vendor_id):
    """Route to display vendor dashboard"""
    # Ensure the vendor exists
    if vendor_id not in vendors:
        flash('Vendor not found')
        return redirect(url_for('index'))
    
    try:
        vendor = vendors[vendor_id]
        
        # Check if vendor has the required keys
        if 'adminkey' not in vendor:
            flash('Vendor wallet not properly configured')
            return redirect(url_for('index'))
        
        # Get vendor's wallet balance
        try:
            # Try to get the balance from LNbits
            balance = get_wallet_balance(vendor['adminkey'])
            print(f"Got wallet balance for {vendor['name']}: {balance} sats")
        except Exception as e:
            print(f"Error getting wallet balance: {str(e)}")
            
            # Fall back to calculating balance from transactions
            received = sum(t["amount"] for t in transactions 
                         if t["vendor_id"] == vendor_id 
                         and t["type"] == "payment" 
                         and t["status"] == "complete")
            
            balance = received
            print(f"Calculated balance from transactions: {balance} sats")
        
        # Get vendor's transactions
        vendor_transactions = [t for t in transactions if t["vendor_id"] == vendor_id]
        
        return render_template('vendor/dashboard.html',
                              vendor=vendor,
                              vendor_id=vendor_id,
                              balance=balance,
                              vendor_transactions=vendor_transactions,
                              recipients=recipients)
    except Exception as e:
        import traceback
        print(f"Error in vendor dashboard: {str(e)}")
        print(traceback.format_exc())
        flash(f'Error getting wallet info: {str(e)}')
        return redirect(url_for('index'))


# Main entry point
if __name__ == '__main__':
    app.run(
        debug=os.getenv("DEBUG", "True").lower() in ["true", "1", "t"],
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080"))
    )