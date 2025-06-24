import csv
import re
from utils.theatre import Theatre

class Login:
    def __init__(self, file1='csvs/login_details.csv', file2='csvs/booking_details.csv'):
        self.file1 = file1
        self.file2 = file2
        self.login_data = self.load_login_data()
        self.booking_data = self.load_booking_data()
        self.login_size = len(self.login_data)
        self.booking_size = len(self.booking_data)
        self.current_user = None

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

        self.login_data.append([username, password])
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
                            print("6. Display Booked Seats")
                            print("7. View Active Bookings")
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
                                t.display_booked_details()

                            elif choice == '7':
                                t.view_my_bookings()
                            
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