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
        self.ticket_count = n * n
        alpha_chr = 65
        for _ in range(n):
            self.alpha_dict[chr(alpha_chr)] = ["_" for _ in range(n)]
            alpha_chr += 1

    def display_seats(self):
        print("\n   ", self.col)
        for key, val in self.alpha_dict.items():
            print(key, ":", val)

    def book_ticket(self, mobile_number):
        username = input("\nEnter your name: ")

        movie = None
        while movie is None:
            print("\nChoose a movie:")
            for key, value in self.movie_list.items():
                print(f"{key}. {value}")
            
            try:
                choice = int(input("Enter the serial number of the movie (or type '0' to exit): "))
                
                if choice == 0:
                    return "Exiting booking system..."
                elif choice in self.movie_list:
                    movie = self.movie_list[choice]
                else:
                    print("\nInvalid selection. Please enter a valid serial number.")
            
            except ValueError:
                print("\nInvalid input. Please enter a number.")


        show_time = None
        while show_time is None:
            print("\nAvailable show timings:", self.movie_timings)
            timing = input("Select a timing: ")
            if timing in self.movie_timings:
                show_time = timing
            else:
                print("\nInvalid timing. Choose from the list.")

        seats_to_book = 0
        while True:
            try:
                seats_to_book = int(input("Enter the number of seats to book: "))
                if seats_to_book <= 0 or seats_to_book > self.ticket_count:
                    print(f"\nInvalid number. Only {self.ticket_count} seats left.")
                else:
                    break
            except ValueError:
                print("\nEnter a valid number.")

        selected_seats = []
        for _ in range(seats_to_book):
            while True:
                self.display_seats()
                row = input("\nEnter row letter: ").upper()
                colm = input("Enter column number: ")
                seat_num = row + colm

                if row not in self.alpha_dict or not colm.isdigit() or int(colm) >= self.n:
                    print("\nInvalid seat selection. Try again.")
                    continue
                if seat_num in self.booked_seats:
                    print("\nSeat already booked. Choose another.")
                    continue

                self.booked_seats[seat_num] = [username, movie, show_time, seat_num, "booked"]
                self.alpha_dict[row][int(colm)] = "X"
                selected_seats.append(seat_num)
                self.ticket_count -= 1
                break

        booking_date = datetime.now().strftime("%Y-%m-%d")
        try:
            with open("csvs/booking_details.csv", "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(
                    [booking_date, username, mobile_number, show_time, seats_to_book, selected_seats, movie, "booked"]
                )
        except Exception as e:
            print(f"Error writing to CSV: {e}")

        print(f"\nBooking successful! Movie: {movie}, Time: {show_time}, Seats: {selected_seats}")

    def display_ticket_details(self):
        ticket_id = input("Enter your ticket ID (Ex: A1, B2, C6): ")
        if ticket_id in self.booked_seats:
            print(f"\nTicket Details: {self.booked_seats[ticket_id]}")
        else:
            print("Invalid ticket ID format or ticket not found.")

    def cancel_ticket(self, mobile_number):
        ticket_id = input("\nEnter ticket ID to cancel (Ex: A1, B2, C6): ")
        if ticket_id in self.booked_seats:
            original_booking = self.booked_seats.pop(ticket_id)
            self.alpha_dict[ticket_id[0]][int(ticket_id[1])] = "_"
            self.ticket_count += 1

            booking_date = datetime.now().strftime("%Y-%m-%d")

            with open("csvs/booking_details.csv", "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(
                    [booking_date, original_booking[0], mobile_number, original_booking[2], 
                    1, ticket_id, original_booking[1], "cancelled"]
                )

            print(f"\nTicket {ticket_id} has been successfully cancelled.")
        else:
            print("Invalid ticket ID or ticket was not booked.")


    def check_remaining_seats(self):
        print(f"\nTotal remaining seats: {self.ticket_count}")

    def display_booked_seats(self):
        print("\nBooked Seats:")
        for ticket_id, details in self.booked_seats.items():
            print(f"Ticket ID: {ticket_id} → {details}")

class Login:
    def __init__(self):
        self.file1 = "csvs/login_details.csv"
        self.login_data = self.load_login_data()

    def load_login_data(self):
        try:
            with open(self.file1, "r") as csvfile:
                return list(csv.reader(csvfile))
        except FileNotFoundError:
            return [["Mobile Number", "Password"]]

    def save_login_data(self):
        with open(self.file1, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(self.login_data)

    def is_valid_mobile_number(self, mobile):
        return bool(re.fullmatch(r"^[6-9]\d{9}$", mobile))

    def sign_up(self):
        print("\n---- SIGN-UP ----")
        while True:
            mobile = input("Enter mobile number: ")
            if self.is_valid_mobile_number(mobile):
                if any(user[0] == mobile for user in self.login_data[1:]):
                    print("User already exists.")
                else:
                    break
            else:
                print("Invalid mobile number format.")

        password = input("Enter password (Min 8 chars, 1 uppercase, 1 digit, 1 special char): ")
        self.login_data.append([mobile, password])
        self.save_login_data()
        print("Account created successfully!")

    def sign_in(self):
        print("\n---- SIGN-IN ----")
        while True:
            mobile = input("Enter mobile number: ")
            user = next((user for user in self.login_data[1:] if user[0] == mobile), None)
            if user:
                for i in range(3, 0, -1):
                    password = input("Enter password: ")
                    if user[1] == password:
                        print("\nSigned in successfully!")
                        theatre = Theatre()
                        theatre.seats(3)

                        while True:
                            print("\n--- Booking Options ---")
                            print("1. Book Ticket")
                            print("2. Display Seats")
                            print("3. Cancel Ticket")
                            print("4. Show Ticket Details")
                            print("5. Check Remaining Seats")
                            print("6. Display Booked Seats")
                            print("7. Exit")

                            choice = input("Enter your choice: ")
                            if choice == "1":
                                theatre.book_ticket(mobile)
                            elif choice == "2":
                                theatre.display_seats()
                            elif choice == "3":
                                theatre.cancel_ticket(mobile)
                            elif choice == "4":
                                theatre.display_ticket_details()
                            elif choice == "5":
                                theatre.check_remaining_seats()
                            elif choice == "6":
                                theatre.display_booked_seats()
                            elif choice == "7":
                                print("Exiting system. Thank you!")
                                return
                            else:
                                print("Invalid choice.")
                    print(f"Wrong password! {i-1} attempts left.")
                return
            print("User not found.")

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
        print(k.sign_in())
    elif choice == '3':
        print("Closing the Login portal. Thank You!")
        break
    else:
        print("Invalid choice. Please enter a number between 1 and 3.")
