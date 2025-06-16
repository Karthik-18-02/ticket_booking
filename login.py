import csv
import re
from datetime import datetime

class Theatre:
    def __init__(self):
        self.movie_list = {
            1: "Baahubali 2",
            2: "Pushpa",
            3: "Kal Ho Na Ho",
            4: "War 2",
            5: "Inception",
            6: "50 First Dates",
        }
        self.movie_timings = ["9:30", "12:30", "4:00", "7:30", "11:30"]
        self.booked_seats = {}

    def seats(self, n):
        self.n = n
        self.col = [i for i in range(n)]
        self.alpha_dict = {}
        alpha_chr = 65

        self.ticket_count = n*n
        self.available_rows = [chr(alpha_chr + i) for i in range(n)]
        self.available_cols = [str(i) for i in range(n)]

        for _ in range(n):
            self.alpha_dict[chr(alpha_chr)] = [0 for _ in range(n)]
            alpha_chr += 1
    
    def display_seats(self):
        print("   ", self.col)
        for key, val in self.alpha_dict.items():
            print(key, ":", val)
    
    def book_ticket(self):
        print("""
            1. Baahubali 2
            2. Pushpa
            3. Kal Ho Na Ho
            4. War 2
            5. Inception
            6. 50 First Dates
        """)
        m = int(input("Enter the serial number of the movie: "))

        if m not in self.movie_list:
            return "PLease enter only the serial numbers of the movie given in the list"
        
        else:
            
            n = int(input("Enter the number of seats you want to book: "))

            if n > self.ticket_count:
                print(f"There are only {self.ticket_count} seats left for this show.")
                return

            booked = 0
            while booked < n:
                self.display_seats()
                print("""
                Seats marked as 'X' are reserved and cannot be booked.
                Seats marked as '0' are available.
                """)
                print("Available rows:", self.available_rows)
                print("Available columns:", self.available_cols)

                name = input("Enter your name: ")
                row = input("Choose your row from the given list: ").upper()
                colm = input("Choose your column from the given list: ")

                seat_num = row + colm

                if row not in self.available_rows or colm not in self.available_cols:
                    print("\n\t---- Please enter only the elements given in the list ----")
                    continue

                if seat_num in self.booked_seats:
                    print("This seat is already booked, please choose another seat.")
                    continue

                self.booked_seats[seat_num] = [name, m, seat_num]
                self.alpha_dict[row][int(colm)] = 'X'
                self.ticket_count -= 1
                booked += 1
                print(f"Seat {seat_num} successfully booked for {name}.\n")

    
    def display_ticket_details(self):
        ticket_id = input("Enter your ticket id: (Ex: A1, B2, C6)")
        if ticket_id in self.booked_seats:
            return self.booked_seats[ticket_id]
        else:
            return "Enter the ticket_id in correct format (Ex: A1, B2, C6)"
    
    def cancel_ticket(self):
        ticket_id = input("Enter your ticket id that you want to canecl: (Ex: A1, B2, C6)")
        if ticket_id in self.booked_seats:
            self.booked_seats.pop(ticket_id)
            self.alpha_dict[ticket_id[0]][int(ticket_id[1])] = 0
            self.ticket_count += 1
            print(f"{ticket_id} is successfully cancelled")
            return
        else:
            return "Your entered ticket number is not booked yet"
    
    def check_remaining_seats(self):
        return self.ticket_count
    
    def display_booked_details(self):
        return self.booked_seats

        
    
    def practice(self):
        print(self.available_rows)
        print(self.available_cols)

class Login:
    def __init__(self, file1='csvs/login_details.csv', file2='csvs/booking_details.csv'):
        self.file1 = file1
        self.file2 = file2
        self.login_data = self.load_login_data()
        self.booking_data = self.load_booking_data()
        self.login_size = len(self.login_data)
        self.booking_size = len(self.booking_data)


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
            return [['UserId', 'UserName', '[date, show_timing, no._of_seats, movie_name]']]

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
                for i in range(5, 0, -1):
                    password = input("Enter your password: ")
                    if user[1] == password:
                        print("Signed in succesfully")

                        t = Theatre()
                        t.seats(3)

                        while True:
                            print("\n--- Theatre Booking System ---")
                            print("1. Book Tickets")
                            print("2. Display Seats")
                            print("3. Cancel Ticket")
                            print("4. Show Ticket Details")
                            print("5. Check Remaining Seats")
                            print("6. Display Booked Seats")
                            print("7. Exit")

                            choice = input("Enter your choice (1-7): ")

                            if choice == '1':
                                t.book_ticket()

                            elif choice == '2':
                                t.display_seats()
                            elif choice == '3':
                                t.cancel_ticket()
                            elif choice == '4':
                                print(t.display_ticket_details())
                            elif choice == '5':
                                print(t.check_remaining_seats())
                            elif choice == '6':
                                print(t.display_booked_details())
                            elif choice == '7':
                                print("Exiting the system. Thank you!")
                                break
                            else:
                                print("Invalid choice. Please enter a number between 1 and 7.")

                        return
                    print(f"Incorrect password and you have ({i-1}) attempts left")
                return
            else:
                print("User not found.")
            
            if username == "":
                break

k = Login()
# print(k.sign_up())
# print(k.sign_in())

while True:
    print("\n--- Theatre Booking Login System ---")
    print("1. Sign-up")
    print("2. Sign-in")
    print("3. Exit")

    choice = input("Enter your choice (1-3): ")

    if choice == '1':
        print(k.sign_up())
    elif choice == '2':
        print(k.sign_in())
    elif choice == '3':
        print("Closing the Login portal. Thank You!")
        break
    else:
        print("Invalid choice. Please enter a number between 1 and 3.")

