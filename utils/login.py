import csv
import re
import os

from utils.theatre import Theatre

class Login:
    def __init__(self, file1='csvs/login_details.csv', file2='csvs/booking_details.csv'):
        self.file1 = file1
        self.file2 = file2
        self.current_user = None
        self.login_data = self.load_login_data()
        self.booking_data = self.load_booking_data()
        self.user_wallets = {}
        self._init_files()
        self._load_wallets() 
        self.login_size = len(self.login_data)
        self.booking_size = len(self.booking_data)

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

    def check_balance(self, username):
        # print(self.user_wallets)
        if username in self.user_wallets:
            return self.user_wallets[username]
        
        try:
            with open(self.file1, 'r') as f:
                reader = csv.reader(f)
                headers = next(reader, [])
                wallet_index = headers.index('WalletBalance') if 'WalletBalance' in headers else 2
                
                for row in reader:
                    if row and row[0] == username:
                        try:
                            balance = int(row[wallet_index]) if len(row) > wallet_index else 1000
                            self.user_wallets[username] = balance
                            return balance
                        except (ValueError, IndexError):
                            break
        except Exception as e:
            print(f"Error checking balance: {e}")
        
        self.user_wallets[username] = 1000
        return 1000

    def add_to_wallet(self, username, amount):
        try:
            current_balance = self.check_balance(username)
            new_balance = current_balance + amount
            
            self.user_wallets[username] = new_balance
            
            temp_file = self.file1 + '.tmp'
            updated = False
            headers = ['Username', 'Password', 'WalletBalance']
            
            with open(self.file1, 'r') as infile, open(temp_file, 'w', newline='') as outfile:
                reader = csv.reader(infile)
                writer = csv.writer(outfile)
                
                try:
                    file_headers = next(reader)
                    writer.writerow(file_headers)
                    wallet_index = file_headers.index('WalletBalance') if 'WalletBalance' in file_headers else 2
                except StopIteration:
                    writer.writerow(headers)
                    wallet_index = 2
                
                for row in reader:
                    if row and row[0] == username:
                        while len(row) <= wallet_index:
                            row.append('')
                        row[wallet_index] = str(new_balance)
                        updated = True
                    writer.writerow(row)
                
                if not updated:
                    new_row = [username, '', str(new_balance)]
                    while len(new_row) <= wallet_index:
                        new_row.append('')
                    new_row[wallet_index] = str(new_balance)
                    writer.writerow(new_row)
            
            os.replace(temp_file, self.file1)
            return new_balance
            
        except Exception as e:
            print(f"Error updating wallet: {e}")
            self.user_wallets[username] = current_balance
            return current_balance
        
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
            user = next((user for user in self.login_data[1:] if user[0] == username), None)
            if user:
                for i in range(3, 0, -1):
                    password = input("Enter your password: ")
                    if user[1] == password:
                        print("Signed in successfully")
                        self.current_user = username

                        l = Login()
                        t = Theatre(self)
                        # t.seats(3)
                        # t._load_booking_history()

                        while True:
                            print("\n--- Theatre Booking System ---")
                            print("1. Book Tickets")
                            print("2. Display Seats")
                            print("3. Cancel Ticket")
                            print("4. Show Ticket Details")
                            print("5. Check Remaining Seats")
                            print("6. Check Balance")
                            print("7. Add Money to Wallet")
                            print("8. View User History")
                            print("9. Reset Seats")
                            print("10. Exit")

                            choice = input("Enter your choice (1-10): ")

                            if choice == '1':
                                t.book_ticket()

                            elif choice == '2':
                                t.display_seats()

                            elif choice == '3':
                                t.cancel_ticket()

                            elif choice == '4':
                                t.display_ticket_details()

                            elif choice == '5':
                                t.check_remaining_seats()

                            elif choice == '6':
                                # t.display_booked_details()
                                balance = l.check_balance(self.current_user)
                                print(f"\nYour current balance: ₹{balance}")

                            elif choice == '7':
                                # t.view_my_bookings()
                                amount = int(input("Enter amount to add: ₹"))
                                new_balance = l.add_to_wallet(l.current_user, amount)
                                print(f"₹{amount} added successfully. New balance: ₹{new_balance}")
                            
                            elif choice == '8':  
                                t.view_history()

                            elif choice == '9':
                                t.reset_seats()

                            elif choice == '10':
                                print("Exiting the system. Thank you!")
                                return
                            
                            else:
                                print("Invalid choice. Please enter a number between 1 and 10.")
                    else:
                        print(f"Incorrect password and you have ({i-1}) attempts left")
                return
            else:
                print("User not found.")

            if username == "":
                break