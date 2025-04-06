A Lightning Network application for managing Bitcoin subsidies / Bitcoin voucher .
Overview
This application helps administrators distribute Bitcoin subsidies to recipients, who can then spend them at approved vendors. 
All transactions use the Lightning Network for instant payments.

Features:
1.Create and manage recipients with daily spending limits
2.Fund recipient wallets using Lightning payments
3.Register approved vendors by category (food, medicine, etc.)
4.Track all transactions and wallet balances
5.Simple interfaces for admins, recipients, and vendors

Set up: 
1. run using shell script ./run.sh -> the admin key details are given through this

How It Works
1. Admins create recipient accounts, set spending limits, and add funds. 
2. Admins create allowed vendors.
3. Recipients view their balance and make payments to approved vendors
4. Vendors can generate invoices and receive payments.
