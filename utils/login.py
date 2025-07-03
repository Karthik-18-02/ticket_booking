import csv
import re
import os
from datetime import datetime

from utils.theatre import Theatre
from utils.admin import Admin

class Login:
    def __init__(self, file1='csvs/login_details.csv', file2='csvs/booking_details.csv'):
        self.file1 = file1
        self.file2 = file2
        self.current_user = None
        self.is_admin = False
        self.login_data = self.load_login_data()
        self.booking_data = self.load_booking_data()
        self.user_wallets = {}
        self.wallet_history_file = 'csvs/wallet_history.csv' 
        self._init_files()
        self._load_wallets() 
        self.login_size = len(self.login_data)
        self.booking_size = len(self.booking_data)
        self.user_names = {} 
        self._load_user_names()
        self._init_wallet_history_file() 

    def _init_wallet_history_file(self):
        """Initialize wallet history file with proper headers"""
        os.makedirs('csvs', exist_ok=True)
        headers = ['Date', 'Time', 'Username', 'Amount', 'Balance', 'Description']
        
        try:
            if os.path.exists(self.wallet_history_file):
                with open(self.wallet_history_file, 'r') as f:
                    first_line = f.readline().strip()
                
                if first_line != ','.join(headers):
                    try:
                        backup_name = f"{self.wallet_history_file}.bak"
                        if os.path.exists(backup_name):
                            os.remove(backup_name)
                        os.rename(self.wallet_history_file, backup_name)
                        print(f"Created backup of invalid wallet history: {backup_name}")
                    except PermissionError:
                        print("Warning: Could not create backup - file may be locked by another process")
        
            if not os.path.exists(self.wallet_history_file):
                with open(self.wallet_history_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    
        except Exception as e:
            print(f"Warning: Could not initialize wallet history file - {str(e)}")
            print("The system will try to create a new file when first transaction occurs")
                    
        except Exception as e:
            print(f"Warning: Could not initialize wallet history - {str(e)}")

    def _load_user_names(self):
        """Load user names from booking history"""
        if os.path.exists(self.file2):
            with open(self.file2, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('UserName') and row.get('UID'):
                        self.user_names[row['UID']] = row['UserName']

    def _load_wallets(self):
        self.user_wallets = {}  
        if os.path.exists(self.file1):
            with open(self.file1, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader, [])
                wallet_index = headers.index('WalletBalance') if 'WalletBalance' in headers else 2
                
                for row in reader:
                    if row: 
                        username = row[0]
                        try:
                            balance = int(row[wallet_index]) if len(row) > wallet_index else 1000
                            self.user_wallets[username] = balance
                        except (ValueError, IndexError):
                            self.user_wallets[username] = 1000

    def add_to_wallet(self, username, amount, description=""):
        """Add or deduct money from wallet and record transaction history"""
        try:
            # Validate username first
            if not username or not self.is_validate_mobile_number(username):
                print("Invalid username/mobile number")
                return self.check_balance(username)

            current_balance = self.check_balance(username)
            new_balance = current_balance + amount
            
            self.user_wallets[username] = new_balance
            
            wallet_file = 'csvs/user_wallets.csv'
            wallet_data = []
            fieldnames = ['Username', 'WalletBalance']
            
            if os.path.exists(wallet_file):
                with open(wallet_file, 'r') as f:
                    reader = csv.DictReader(f)
                    wallet_data = [row for row in reader if row.get('Username')]
            
            user_found = False
            for record in wallet_data:
                if record['Username'] == username:
                    record['WalletBalance'] = str(new_balance)
                    user_found = True
                    break
            
            if not user_found:
                wallet_data.append({'Username': username, 'WalletBalance': str(new_balance)})
            
            with open(wallet_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for record in wallet_data:
                    if not record.get('Username'):
                        continue
                    writer.writerow({
                        'Username': record['Username'],
                        'WalletBalance': record['WalletBalance']
                    })
            
            now = datetime.now()
            transaction = {
                'Date': now.strftime('%Y-%m-%d'),
                'Time': now.strftime('%H:%M:%S'),
                'Username': username,
                'Amount': amount,
                'Balance': new_balance,
                'Description': description
            }
            
            history_file = self.wallet_history_file
            file_exists = os.path.exists(history_file)
            with open(history_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=transaction.keys())
                if not file_exists or os.stat(history_file).st_size == 0:
                    writer.writeheader()
                writer.writerow(transaction)
            
            print(f"₹{abs(amount):.2f} {'added to' if amount > 0 else 'deducted from'} wallet successfully.")
            print(f"New balance: ₹{new_balance:.2f}")
            return new_balance
            
        except Exception as e:
            print(f"\nError processing transaction: {str(e)}")
            print("Your balance remains unchanged.")
            return current_balance
        

    def get_wallet_history(self, username):
        """Retrieve and display wallet history for the current user"""
        try:
            transactions = []
            if os.path.exists(self.wallet_history_file):
                with open(self.wallet_history_file, 'r') as f:
                    reader = csv.DictReader(f)
                    if not reader.fieldnames or 'Balance' not in reader.fieldnames:
                        print("\nWallet history format is invalid")
                        return
                        
                    transactions = [
                        {
                            'date': row['Date'],
                            'time': row['Time'],
                            'amount': float(row['Amount']),
                            'balance': float(row['Balance']) if 'Balance' in row else 0,
                            'description': row.get('Description', '')
                        }
                        for row in reader if row.get('Username') == username
                    ]
                    transactions.sort(key=lambda x: (x['date'], x['time']), reverse=True)
            
            if not transactions:
                print("\nNo wallet transactions found.")
                return

            print("\n" + "="*85)
            print(f"WALLET TRANSACTION HISTORY: {username}".center(85))
            print("="*85)
            print(f"{'Date':<12} | {'Time':<10} | {'Amount':<15} | {'Balance':<15} | {'Description'}")
            print("-"*85)
            
            for t in transactions:
                amount_str = f"+₹{t['amount']:,.2f}" if t['amount'] >= 0 else f"-₹{abs(t['amount']):,.2f}"
                print(f"{t['date']:<12} | {t['time']:<10} | {amount_str:<15} | ₹{t['balance']:<14} | {t['description']}")
            
            print("="*85)
            
        except Exception as e:
            print(f"\nError retrieving wallet history: {str(e)}")


    def check_balance(self, username):
        try:
            # if username in self.user_wallets:
            #     return self.user_wallets[username]
            
            wallet_file = 'csvs/user_wallets.csv'
            if os.path.exists(wallet_file):
                with open(wallet_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get('Username') == username:
                            try:
                                balance = float(row['WalletBalance'])
                                self.user_wallets[username] = balance
                                return balance
                            except (ValueError, KeyError):
                                continue
            
            self.user_wallets[username] = 1000
            return 1000
            
        except Exception as e:
            print(f"Error checking balance: {e}")
            return 1000
        
    def _init_files(self):
        if os.path.exists(self.file1):
            with open(self.file1, 'r') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if len(row) >= 2:
                        self.user_wallets[row[0]] = 1000

    def load_login_data(self):
        try:
            with open(self.file1, 'r') as csvfile:
                reader1 = csv.reader(csvfile)
                return list(reader1)
        except FileNotFoundError:
            return [['Username', 'Password']]

    def load_booking_data(self):
        try:
            with open(self.file2, 'r') as csvfile:
                reader2 = csv.reader(csvfile)
                return list(reader2)
        except FileNotFoundError:
            return [['Date', 'UserName', 'UID', 'Show_Timing', 'No_of_Seats', 'Seat_Numbers', 'Movie_Name', 'Ticket_Status']]

    def save_login_data(self):
        with open(self.file1, 'w', newline='') as csvfile:
            writer1 = csv.writer(csvfile)
            writer1.writerows(self.login_data)

    def save_booking_data(self):
        with open(self.file2, 'w', newline='') as csvfile:
            writer2 = csv.writer(csvfile)
            writer2.writerows(self.booking_data)

    def is_validate_mobile_number(self, mobile):
        pattern = r'^[6-9]\d{9}$'
        return bool(re.fullmatch(pattern, mobile))

    def is_valid_password(self, password):
        if len(password) < 8:
            return False, "Password must be at least 8 characters long."
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter."
        if not re.search(r"[0-9]", password):
            return False, "Password must contain at least one number."
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character."
        return True, ""

    def sign_up(self):
        print("\t\t ---- SIGN-UP ----")
        while True:
            username = input("Please enter your 10-digit mobile number: ")
            if self.is_validate_mobile_number(username):
                if any(user[0] == username for user in self.login_data[1:]):
                    print("User already exists.")
                else:
                    break
            else:
                print("Invalid mobile number. It must be 10 digits and start with 6, 7, 8, or 9.")

        while True:
            password = input("Enter your password: ")
            valid, message = self.is_valid_password(password)
            if valid:
                break
            print(message)

        self.login_data.append([username, password, "1000"])
        self.user_wallets[username] = 1000
        self.save_login_data()
        return "Account created successfully."

    def sign_in(self):
        print("\t\t ---- SIGN-IN ----")
        while True:
            username = input("Enter your mobile number: ")
            if username == "admin":
                password = input("Enter admin password: ")
                if password == "admin123":
                    print("Admin login successful")
                    self.current_user = "admin"
                    self.is_admin = True
                    theatre = Theatre(self)
                    theatre.current_user = username
                    admin = Admin(theatre)
                    admin.admin_menu()
                    return
                else:
                    print("Invalid admin credentials")
                    continue
            
            user = next((user for user in self.login_data[1:] if user[0] == username), None)
            if user:
                for i in range(3, 0, -1):
                    password = input("Enter your password: ")
                    if user[1] == password:
                        user_name = self._get_user_name(username)
                        if user_name:
                            print(f"\nWelcome back, {user_name}!")
                        else:
                            print("\nSigned in successfully")
                        
                        self.current_user = username
                        self.is_admin = False

                        theatre = Theatre(self)
                        
                        if self.is_admin:
                            admin = Admin(theatre)
                            admin.admin_menu()
                        else:
                            theatre.user_menu()
                        return
                    else:
                        print(f"Incorrect password. You have ({i-1}) attempts left")
                return
            else:
                print("User not found.")

    def _get_user_name(self, username):
        """Retrieve user's name from booking history"""
        if os.path.exists(self.file2):
            with open(self.file2, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('UID') == username and row.get('UserName'):
                        return row['UserName']
        return None
