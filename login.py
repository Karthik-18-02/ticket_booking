import csv
import re
import ast
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
    
        self.hall_data = {}
        self.booking_history = []

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
                'ticket_count': n * n,
                'booked_seats': {}
            }

    def _load_booking_history(self):
        """Load booking history from CSV and update seat availability"""
        if not os.path.exists(self.login.file2):
            return

        reverse_movie_map = {movie_name: movie_id for movie_id, movie_name in self.movie_list.items()}
        current_status = {} 

        try:
            with open(self.login.file2, 'r') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if len(row) < 8:
                        continue
                    
                    date_str, username, uid, show_timing, _, seats_str, movie_name, status = row
                    
                    try:
                        seat_list = ast.literal_eval(seats_str)
                    except (ValueError, SyntaxError):
                        continue
                    
                    for seat in seat_list:
                        key = (movie_name, seat)
                        current_status[key] = (status, username, show_timing)
                        
            for (movie_name, seat), (status, username, show_timing) in current_status.items():
                if status == 'booked':
                    if movie_name in reverse_movie_map:
                        movie_id = reverse_movie_map[movie_name]
                        row_char = seat[0]
                        col_str = seat[1:]
                        
                        if (row_char in self.available_rows and 
                            col_str in self.available_cols and
                            movie_id in self.hall_data):
                            
                            col_index = int(col_str)
                            hall = self.hall_data[movie_id]
                            
                            if hall['alpha_dict'][row_char][col_index] == 0:
                                hall['alpha_dict'][row_char][col_index] = 'X'
                                hall['ticket_count'] -= 1
                                hall['booked_seats'][seat] = [username, movie_id, seat, show_timing, uid]
        except Exception as e:
            print(f"Error loading booking history: {e}")

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

        self.booking_history.append(row)

    def book_ticket(self):
        print("\nAvailable Movies:")
        for key, val in self.movie_list.items():
            print(f"{key}. {val}")

        while True:
            try:
                m = int(input("Enter the serial number of the movie: "))
                if m not in self.movie_list:
                    print("Please enter a valid movie serial number.")
                    continue
                break
            except ValueError:
                print("Please enter a number only.")

        while True:
            try:
                n = input("Enter the number of seats you want to book: ")
                n = int(n)
                if n <= 0:
                    print("Please enter a positive number.")
                    continue
                if n > self.hall_data[m]['ticket_count']:
                    print(f"There are only {self.hall_data[m]['ticket_count']} seats left for this show.")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter a number only.")

        user_booked_before = any(
            booking[2] == self.login.current_user 
            for booking in self.booking_history
        )

        if user_booked_before:
            user_name = next(
                (booking[1] for booking in self.booking_history 
                if booking[2] == self.login.current_user),
                self.login.current_user 
            )
            print(f"\nWelcome back, {user_name}!")
        else:
            user_name = input("Please enter your name for the booking: ")
            print(f"Thank you, {user_name}!")

        show_time = self.get_movie_timing()
        if show_time is None:
            return

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

            if self.hall_data[m]['alpha_dict'][row][int(colm)] == 'X':
                print("This seat is already booked for this movie. Choose another.")
                continue

            self.hall_data[m]['booked_seats'][seat_num] = [user_name, m, seat_num, show_time, self.login.current_user]
            self.hall_data[m]['alpha_dict'][row][int(colm)] = 'X'
            self.hall_data[m]['ticket_count'] -= 1
            booked_seats_list.append(seat_num)
            booked += 1
            print(f"Seat {seat_num} successfully booked for {user_name} in '{self.movie_list[m]}' at {show_time}.")

        self.update_booking_csv(user_name, self.login.current_user, show_time, booked_seats_list, m, 'booked')

    def display_ticket_details(self):
        if not self.booking_history:
            print("No tickets booked yet.")
            return

        last_booking = self.booking_history[-1]
        print("\nLast Ticket Booked:")
        print(f"Date: {last_booking[0]} | Name: {last_booking[1]} | UID: {last_booking[2]} | Show Time: {last_booking[3]}")
        print(f"No. of Seats: {last_booking[4]} | Seats: {last_booking[5]} | Movie: {last_booking[6]} | Status: {last_booking[7]}")

    def cancel_ticket(self):
        print("\nAvailable Movies:")
        for key, val in self.movie_list.items():
            print(f"{key}. {val}")
        
        try:
            movie_id = int(input("Enter the movie number: "))
            ticket_id = input("Enter your ticket id to cancel (e.g., A1): ").upper()
            
            if movie_id not in self.hall_data:
                print("Invalid movie number.")
                return
                
            hall = self.hall_data[movie_id]
            
            if ticket_id not in hall['booked_seats']:
                print("Ticket not found for this movie.")
                return
                
            booking_details = hall['booked_seats'][ticket_id]
            booked_user_id = booking_details[4] if len(booking_details) > 4 else booking_details[0]

            if booked_user_id != self.login.current_user:
                print("\nERROR: You can only cancel tickets you've booked yourself!")
                return
                
            row_char = ticket_id[0]
            col_index = int(ticket_id[1:])
            
            hall['booked_seats'].pop(ticket_id)
            hall['alpha_dict'][row_char][col_index] = 0
            hall['ticket_count'] += 1
            
            print(f"\n{ticket_id} cancelled successfully for '{self.movie_list[movie_id]}'")
            
            self.update_booking_csv(
                booking_details[0], 
                self.login.current_user, 
                booking_details[3], 
                [ticket_id], 
                movie_id, 
                'cancelled'
            )
        except ValueError:
            print("Please enter valid numbers.")


    def check_remaining_seats(self):
        for movie_id in self.movie_list:
            print(f"{self.movie_list[movie_id]}: {self.hall_data[movie_id]['ticket_count']}")

    def display_booked_details(self):
        all_booked_seats = []
        
        for movie_id, hall in self.hall_data.items():
            for seat, details in hall['booked_seats'].items():
                name = details[0]
                timing = details[3]  
                movie_name = self.movie_list[movie_id]
                all_booked_seats.append((seat, name, movie_name, timing))
        
        all_booked_seats.sort(key=lambda x: (x[0][0], int(x[0][1:])))
        
        for seat, name, movie_name, timing in all_booked_seats:
            print(f"{seat} → [{name}, {movie_name}, {timing}, {seat}]")

    def view_my_bookings(self):
        print("\n--- Your Booked Tickets ---")
        found = False
        
        for movie_id, hall in self.hall_data.items():
            for seat, details in hall['booked_seats'].items():
                user_id = details[4] if len(details) > 4 else details[0] 
                
                if user_id == self.login.current_user:
                    movie_name = self.movie_list[movie_id]
                    show_time = details[3] if len(details) > 3 else "Unknown"
                    print(f"Date: {datetime.today().date()} | Movie: {movie_name} | Seat: {seat} | Show: {show_time}")
                    found = True
                    
        if not found:
            print("You have no booked tickets.")

    def get_movie_timing(self):
        while True:
            try:
                print("\nAvailable Show Timings:")
                for i, timing in enumerate(self.movie_timings, 1):
                    print(f"{i}. {timing}")

                user_input = input("Select timing (1-{}): ".format(len(self.movie_timings)))
                
                if not user_input.strip():
                    print("Error: Input cannot be empty. Please try again.\n")
                    continue
                    
                if not user_input.isdigit():
                    print("Error: Please enter a number only.\n")
                    continue
                    
                timing_choice = int(user_input)
                
                if timing_choice < 1 or timing_choice > len(self.movie_timings):
                    print("Error: Please select a number between 1 and {}.\n".format(len(self.movie_timings)))
                    continue
                    
                return self.movie_timings[timing_choice - 1]
                
            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
                return None
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
                continue


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
                        t.seats(3)
                        t._load_booking_history()

                        while True:
                            print("\n--- Theatre Booking System ---")
                            print("1. Book Tickets")
                            print("2. Display Seats")
                            print("3. Cancel Ticket")
                            print("4. Show Ticket Details")
                            print("5. Check Remaining Seats")
                            print("6. Display Booked Seats")
                            print("7. View User Bookings")
                            print("8. Exit")

                            choice = input("Enter your choice (1-8): ")

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
                                print("Exiting the system. Thank you!")
                                return
                            
                            else:
                                print("Invalid choice. Please enter a number between 1 and 8.")
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

