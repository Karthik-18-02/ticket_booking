import csv
import re
from datetime import datetime
import os

class Theatre:
    def __init__(self, login_instance):
        self.login = login_instance
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
        self.hall_data = {}

    def seats(self, n):
        self.n = n
        self.col = [i for i in range(n)]
        self.available_rows = [chr(65 + i) for i in range(n)]
        self.available_cols = [str(i) for i in range(n)]

        for movie_id in self.movie_list:
            alpha_dict = {}
            alpha_chr = 65
            for _ in range(n):
                alpha_dict[chr(alpha_chr)] = [0 for _ in range(n)]
                alpha_chr += 1
            self.hall_data[movie_id] = {
                'alpha_dict': alpha_dict,
                'ticket_count': n * n
            }

    def display_seats(self):
        print("\nAvailable Movies:")
        for key, val in self.movie_list.items():
            print(f"{key}. {val}")

        try:
            movie_id = int(input("Enter the serial number of the movie to view its seating: "))
            if movie_id not in self.movie_list:
                print("Invalid movie number.")
                return

            print(f"\n--- Seating for '{self.movie_list[movie_id]}' ---")
            hall = self.hall_data[movie_id]
            print("   ", self.col)
            for key, val in hall['alpha_dict'].items():
                print(key, ":", val)
        except ValueError:
            print("Please enter a valid number.")

    def _display_movie_seats(self, movie_id):
        print(f"\n--- Seating for '{self.movie_list[movie_id]}' ---")
        hall = self.hall_data[movie_id]
        print("   ", self.col)
        for key, val in hall['alpha_dict'].items():
            print(key, ":", val)

    def update_booking_csv(self, name, uid, show_time, seats, movie_id, status):
        row = [datetime.today().date(), name, uid, show_time, len(seats), seats, self.movie_list[movie_id], status]

        if not os.path.exists(self.login.file2):
            with open(self.login.file2, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'UserName', 'UID', 'Show_Timing', 'No_of_Seats', 'Seat_Numbers', 'Movie_Name', 'Ticket_Status'])

        with open(self.login.file2, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def book_ticket(self):
        print("\nAvailable Movies:")
        for key, val in self.movie_list.items():
            print(f"{key}. {val}")

        m = int(input("Enter the serial number of the movie: "))

        if m not in self.movie_list:
            print("Please enter a valid movie serial number.")
            return

        n = int(input("Enter the number of seats you want to book: "))

        if n > self.hall_data[m]['ticket_count']:
            print(f"There are only {self.hall_data[m]['ticket_count']} seats left for this show.")
            return

        name = input("Enter your name: ")
        booked = 0
        booked_seats_list = []
        while booked < n:
            self._display_movie_seats(m)
            print("""
            Seats marked as 'X' are reserved and cannot be booked.
            Seats marked as '0' are available.
            """)
            print("Available rows:", self.available_rows)
            print("Available columns:", self.available_cols)

            row = input("Choose your row from the given list: ").upper()
            colm = input("Choose your column from the given list: ")
            seat_num = f"{row}{colm}"

            if row not in self.available_rows or colm not in self.available_cols:
                print("\n\t---- Please enter only the elements given in the list ----")
                continue

            if (m, seat_num) in self.booked_seats:
                print("This seat is already booked for this movie. Choose another.")
                continue

            self.booked_seats[(m, seat_num)] = [name, m, seat_num]
            self.hall_data[m]['alpha_dict'][row][int(colm)] = 'X'
            self.hall_data[m]['ticket_count'] -= 1
            booked_seats_list.append(seat_num)
            booked += 1
            print(f"Seat {seat_num} successfully booked for {name} in '{self.movie_list[m]}'.")

        self.update_booking_csv(name, self.login.current_user, self.movie_timings[0], booked_seats_list, m, 'booked')

    def display_ticket_details(self):
        for key, val in self.movie_list.items():
            print(f"{key}. {val}")
        movie_id = int(input("Enter the movie number: "))
        ticket_id = input("Enter your ticket id (e.g., A1): ")
        key = (movie_id, ticket_id)
        if key in self.booked_seats:
            return self.booked_seats[key]
        else:
            return "Ticket not found. Please enter correct movie number and ticket id."

    def cancel_ticket(self):
        for key, val in self.movie_list.items():
            print(f"{key}. {val}")
        movie_id = int(input("Enter the movie number: "))
        ticket_id = input("Enter your ticket id to cancel (e.g., A1): ")
        key = (movie_id, ticket_id)
        if key in self.booked_seats:
            name = self.booked_seats[key][0]
            self.booked_seats.pop(key)
            self.hall_data[movie_id]['alpha_dict'][ticket_id[0]][int(ticket_id[1])] = 0
            self.hall_data[movie_id]['ticket_count'] += 1
            print(f"{ticket_id} cancelled successfully for '{self.movie_list[movie_id]}'")
            self.update_booking_csv(name, self.login.current_user, self.movie_timings[0], [ticket_id], movie_id, 'cancelled')
        else:
            print("Ticket not found for this movie.")

    def check_remaining_seats(self):
        for movie_id in self.movie_list:
            print(f"{self.movie_list[movie_id]}: {self.hall_data[movie_id]['ticket_count']}")

    def display_booked_details(self):
        for key, value in self.booked_seats.items():
            movie_id, seat = key
            print(f"Movie: {self.movie_list[movie_id]}, Seat: {seat}, Name: {value[0]}")


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
                for i in range(5, 0, -1):
                    password = input("Enter your password: ")
                    if user[1] == password:
                        print("Signed in successfully")
                        self.current_user = username

                        t = Theatre(self)
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
                                t.check_remaining_seats()

                            elif choice == '6':
                                t.display_booked_details()

                            elif choice == '7':
                                print("Exiting the system. Thank you!")
                                return

                            else:
                                print("Invalid choice. Please enter a number between 1 and 7.")
                    else:
                        print(f"Incorrect password and you have ({i-1}) attempts left")
                return
            else:
                print("User not found.")

            if username == "":
                break

k = Login()


while True:
    print("\n--- Theatre Booking Login System ---")
    print("1. Sign-up")
    print("2. Sign-in")
    print("3. Exit")

    choice = input("Enter your choice (1-3): ")

    if choice == '1':
        print(k.sign_up())
    elif choice == '2':
        k.sign_in()
    elif choice == '3':
        print("Closing the Login portal. Thank You!")
        break
    else:
        print("Invalid choice. Please enter a number between 1 and 3.")

