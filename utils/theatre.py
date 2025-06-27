from datetime import datetime
import csv
import os
import ast

class Theatre:
    def __init__(self, login_instance):
        self.login = login_instance
        self.movie_list = {
            1: {"name": "Baahubali 2", "price": 200},
            2: {"name": "Pushpa", "price": 200},
            3: {"name": "Kal Ho Na Ho", "price": 200},
            4: {"name": "War 2", "price": 200},
            5: {"name": "Inception", "price": 200},
            6: {"name": "50 First Dates", "price": 200},
        }
        self.movie_timings = ["9:30", "12:30", "4:00", "7:30", "11:30"]
        
        self.hall_data = {}
        self.n = None
        self.available_rows = None
        self.available_cols = None
        self.col = None
        self.booking_history = []
        
        self.seats(3)
        self._load_booking_history()

    def seats(self, n):
        self.n = n
        self.col = [i for i in range(n)]
        self.available_rows = [chr(65 + i) for i in range(n)]
        self.available_cols = [str(i) for i in range(n)]
        
        self.hall_data = {
            movie_id: {
                'timings': {
                    time: {  
                        'alpha_dict': {row: [0]*self.n for row in self.available_rows},
                        'booked_seats': {},
                        'ticket_count': self.n * self.n
                    } for time in self.movie_timings
                }
            } for movie_id in self.movie_list
        }

    def _load_booking_history(self):
        if not os.path.exists(self.login.file2):
            return

        reverse_movie_map = {movie_data["name"]: movie_id 
                            for movie_id, movie_data in self.movie_list.items()}

        try:
            with open(self.login.file2, 'r') as f:
                reader = csv.reader(f)
                next(reader)  
                
                DATE = 0
                USERNAME = 1
                UID = 2
                SHOW_TIMING = 3
                NO_OF_SEATS = 4
                SEAT_NUMBERS = 5
                MOVIE_NAME = 6
                TOTAL_PRICE = 7
                TICKET_STATUS = 8

                for row in reader:
                    if len(row) <= TICKET_STATUS: 
                        continue
                    
                    try:
                        movie_name = row[MOVIE_NAME]
                        seats_str = row[SEAT_NUMBERS]
                        status = row[TICKET_STATUS].lower()
                        username = row[USERNAME]
                        uid = row[UID]
                        show_timing = row[SHOW_TIMING]
                        price = int(row[TOTAL_PRICE]) if row[TOTAL_PRICE].isdigit() else None
                        
                        if status != 'booked':
                            continue
                            
                        if movie_name not in reverse_movie_map:
                            continue
                        movie_id = reverse_movie_map[movie_name]
                        
                        if show_timing not in self.movie_timings:
                            continue
                            
                        try:
                            seat_list = ast.literal_eval(seats_str) if seats_str.startswith('[') else [seats_str]
                        except:
                            seat_list = [seats_str]
                        
                        for seat in seat_list:
                            row_char = seat[0].upper()
                            col_str = seat[1:] if len(seat) > 1 else seat
                            
                            if (row_char not in self.available_rows or 
                                not col_str.isdigit() or 
                                int(col_str) not in self.col):
                                continue
                                
                            col_index = int(col_str)
                            
                            timing_data = self.hall_data[movie_id]['timings'][show_timing]
                            
                            if timing_data['alpha_dict'][row_char][col_index] == 'X':
                                continue
                                
                            timing_data['alpha_dict'][row_char][col_index] = 'X'
                            timing_data['ticket_count'] -= 1
                            timing_data['booked_seats'][seat] = [
                                username,
                                movie_id,
                                seat,
                                show_timing,
                                uid,
                                price if price is not None else self.movie_list[movie_id]['price']
                            ]
                            
                    except (ValueError, SyntaxError, IndexError, KeyError) as e:
                        print(f"Skipping invalid booking record: {e}")
                        continue

        except Exception as e:
            print(f"Error loading booking history: {e}")

    def display_seats(self):
        print("\nAvailable Movies:")
        for key, val in self.movie_list.items():
            print(f"{key}. {val['name']}")

        try:
            movie_id = int(input("Enter the serial number of the movie to view its seating: "))
            if movie_id not in self.movie_list:
                print("Invalid movie number.")
                return

            print(f"\n--- Seating for '{self.movie_list[movie_id]['name']} ---")
            for timing, data in self.hall_data[movie_id]['timings'].items():
                print(f"\n{timing} Show:")
                print("  ", " ".join(str(col) for col in self.col))
                for row_label, seats in data['alpha_dict'].items():
                    print(f"{row_label}:", " ".join(str(seat) if seat != 0 else '.' for seat in seats))

        except ValueError:
            print("Please enter a valid number.")

    def _display_movie_seats(self, movie_id):
        """Display the current seating arrangement for a specific movie"""
        print(f"\n--- Seating for '{self.movie_list[movie_id]['name']}' ---")
        hall = self.hall_data[movie_id]
        print("  ", " ".join(str(col) for col in self.col)) 
        
        for row_label, seats in hall['alpha_dict'].items():
            print(f"{row_label}:", " ".join(str(seat) if seat != 0 else '.' for seat in seats)) 

    def update_booking_csv(self, name, uid, show_time, seats, movie_id, status, total_price=None):
        try:
            if total_price is None:
                total_price = self.movie_list[movie_id]["price"] * len(seats)
            
            if status.lower() == 'cancelled' and total_price > 0:
                total_price = -total_price

            row = [
                datetime.today().date(),
                name,
                uid,
                show_time,
                len(seats),
                seats,
                self.movie_list[movie_id]['name'],
                total_price,        
                status
            ]

            write_header = not os.path.exists(self.login.file2)
            
            with open(self.login.file2, 'a', newline='') as f:
                writer = csv.writer(f)
                if write_header:
                    writer.writerow([
                        'Date', 'UserName', 'UID', 'Show_Timing',
                        'No_of_Seats', 'Seat_Numbers', 'Movie_Name',
                        'Total_Price', 'Ticket_Status'
                    ])
                writer.writerow(row)
            
            self.booking_history.append(row)
            
        except Exception as e:
            print(f"Error updating booking records: {e}")
            raise

    def book_ticket(self):
        print("\nAvailable Movies:")
        for key, val in self.movie_list.items():
            print(f"{key}. {val['name']} ₹{val['price']}")

        while True:
            try:
                m = int(input("Enter the serial number of the movie: "))
                if m not in self.movie_list:
                    print("Please enter a valid movie serial number.")
                    continue
                break
            except ValueError:
                print("Please enter a number only.")

        show_time = self.get_movie_timing()
        if show_time is None:
            return

        timing_data = self.hall_data[m]['timings'][show_time]
        
        while True:
            try:
                n = input(f"Enter the number of seats you want to book for {show_time}: ")
                n = int(n)
                if n <= 0:
                    print("Please enter a positive number.")
                    continue
                if n > timing_data['ticket_count']:
                    print(f"There are only {timing_data['ticket_count']} seats left for this show.")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter a number only.")

        total_price = self.movie_list[m]["price"] * n
        
        balance = self.login.check_balance(self.login.current_user)
        print(f"\nYour current balance: ₹{balance}")
        print(f"Total booking amount: ₹{total_price}")
        
        if balance < total_price:
            print("\nInsufficient balance!")
            print(f"You need ₹{total_price - balance} more to book these tickets.")
            return

        user_name = None
        if os.path.exists(self.login.file2):
            with open(self.login.file2, 'r') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if len(row) >= 3 and row[2] == self.login.current_user:
                        user_name = row[1] 
                        break
        
        if not user_name:
            while True:
                user_name = input("Please enter your name for the booking: ").strip()
                if user_name:
                    print(f"Thank you, {user_name}!")
                    break
                print("Name cannot be empty. Please try again.")
        else:
            print(f"\nWelcome back, {user_name}!")

        booked = 0
        booked_seats_list = []
        selected_seats = set()  
        
        while booked < n:
            print(f"\n--- Seating for '{self.movie_list[m]['name']}' at {show_time} ---")
            print("  ", " ".join(str(col) for col in self.col)) 
            for row_label, seats in timing_data['alpha_dict'].items():
                print(f"{row_label}:", " ".join(str(seat) if seat != 0 else '.' for seat in seats))
            
            print("\nSeats marked 'X' are booked, '.' are available")
            print(f"Available rows: {self.available_rows}")
            print(f"Available columns: {self.available_cols}")

            try:
                row = input("Choose row: ").upper()
                colm = input("Choose column: ")
                
                if (row not in self.available_rows or 
                    not colm.isdigit() or 
                    int(colm) not in self.col):
                    print("\nInvalid selection. Please choose from available options.")
                    continue
                    
                seat_num = f"{row}{colm}"
                
                if seat_num in selected_seats:
                    print("You've already selected this seat in current booking. Choose another.")
                    continue
                    
                if timing_data['alpha_dict'][row][int(colm)] == 'X':
                    print("Seat already booked for this show time. Choose another.")
                    continue
                    
                selected_seats.add(seat_num)
                booked_seats_list.append(seat_num)
                booked += 1
                
            except ValueError:
                print("Invalid input. Please try again.")
                continue


        print(f"\nTOTAL AMOUNT: ₹{total_price} for {n} seat(s) at {show_time}")
        print(f"Selected Seats: {', '.join(booked_seats_list)}")
        print(f"Your current balance: ₹{balance}")
        
        while True:
            confirm = input("Confirm payment and book tickets? (y/n): ").lower()
            
            if confirm == 'y':
                try:
                    total_price = self.movie_list[m]["price"] * len(booked_seats_list)
                    new_balance = self.login.add_to_wallet(self.login.current_user, -total_price)
                    print(f"\n₹{total_price} deducted. New balance: ₹{new_balance}")
                    
                    for seat in booked_seats_list:
                        row_char = seat[0]
                        col_index = int(seat[1:])
                        timing_data['booked_seats'][seat] = [
                            user_name, 
                            m, 
                            seat, 
                            show_time, 
                            self.login.current_user,
                            self.movie_list[m]["price"]
                        ]
                        timing_data['alpha_dict'][row_char][col_index] = 'X'
                        timing_data['ticket_count'] -= 1
                    
                    self.update_booking_csv(
                        user_name, 
                        self.login.current_user, 
                        show_time, 
                        booked_seats_list, 
                        m, 
                        'booked',
                        total_price
                    )
                    print(f"\nBooking confirmed! Enjoy '{self.movie_list[m]['name']}' at {show_time}")
                    break
                    
                except Exception as e:
                    print(f"Payment failed: {e}")
                    print("Booking cancelled due to payment error")
                    break
            
            elif confirm == 'n':
                print("Booking cancelled. Seats released.")
                break
            
            else:
                print("Please enter 'y' or 'n'")


    def display_ticket_details(self):
        if not self.booking_history:
            print("No tickets booked yet.")
            return

        last_booking = self.booking_history[-1]
        print("\nLast Ticket Booked:")
        print(f"Date: {last_booking[0]} | Name: {last_booking[1]} | UID: {last_booking[2]}")
        print(f"Show Time: {last_booking[3]} | Seats: {last_booking[5]} ({last_booking[4]})")
        print(f"Movie: {last_booking[6]} | Price: ₹{last_booking[7]} | Status: {last_booking[8]}")


    def cancel_ticket(self):
        print("\n--- Your Booked Tickets ---")
        user_tickets = []
        
        for movie_id, movie_data in self.hall_data.items():
            for show_time, timing_data in movie_data['timings'].items():
                for seat, details in timing_data['booked_seats'].items():
                    if len(details) > 4 and details[4] == self.login.current_user:
                        user_tickets.append({
                            'movie_id': movie_id,
                            'movie': self.movie_list[movie_id]['name'],
                            'show_time': show_time,
                            'seat': seat,
                            'details': details
                        })
        
        if not user_tickets:
            print("You have no tickets booked.")
            return
        
        for i, ticket in enumerate(user_tickets, 1):
            print(f"{i}. {ticket['movie']} | Seat: {ticket['seat']} | Time: {ticket['show_time']}")

        try:
            choice = int(input("\nEnter the serial number of ticket to cancel (0 to exit): "))
            if choice == 0:
                return
            if choice < 1 or choice > len(user_tickets):
                print("Invalid selection.")
                return
                
            selected_ticket = user_tickets[choice-1]
            movie_id = selected_ticket['movie_id']
            show_time = selected_ticket['show_time']
            seat = selected_ticket['seat']
            
            timing_data = self.hall_data[movie_id]['timings'][show_time]
            booking_details = timing_data['booked_seats'][seat]
            
            row_char = seat[0]
            col_index = int(seat[1:])
            refund_amount = self.movie_list[movie_id]['price']
            
            timing_data['booked_seats'].pop(seat)
            timing_data['alpha_dict'][row_char][col_index] = 0
            timing_data['ticket_count'] += 1
                    
            new_balance = self.login.add_to_wallet(self.login.current_user, abs(refund_amount))
            print(f"\n{seat} cancelled successfully for '{self.movie_list[movie_id]['name']}' at {show_time}")
            print(f"₹{abs(refund_amount)} has been refunded to your wallet. New balance: ₹{new_balance}")
            
            self.update_booking_csv(
                booking_details[0], 
                self.login.current_user, 
                show_time, 
                [seat], 
                movie_id,
                'cancelled',
                -refund_amount 
            )
            
        except ValueError:
            print("Please enter a valid number.")


    def check_remaining_seats(self):
        print("\nRemaining Seats Per Movie:")
        print(f"{'Movie':<20} | {'Show Time':<10} | {'Available Seats'}")
        print("-" * 50)
        
        for movie_id, movie_data in self.movie_list.items():
            movie_name = movie_data['name']
            timing_data = self.hall_data[movie_id]['timings']
            
            for show_time, data in timing_data.items():
                print(f"{movie_name:<20} | {show_time:<10} | {data['ticket_count']}")
            print("-" * 50)


    def display_booked_details(self):
        all_booked_seats = []
        
        for movie_id, movie_data in self.hall_data.items():
            for show_time, timing_data in movie_data['timings'].items():
                for seat, details in timing_data['booked_seats'].items():
                    name = details[0]
                    movie_name = self.movie_list[movie_id]['name']
                    movie_price = self.movie_list[movie_id]['price']
                    all_booked_seats.append((
                        seat, 
                        name, 
                        movie_name, 
                        show_time, 
                        movie_price,
                        details[4] if len(details) > 4 else "N/A" 
                    ))
        
        all_booked_seats.sort(key=lambda x: (x[0][0], int(x[0][1:])))
        
        print("\nAll Booked Tickets:")
        print(f"{'Seat':<5} | {'User':<15} | {'Movie':<20} | {'Time':<8} | {'Price':<6} | {'UID'}")
        print("-" * 80)
        
        for seat, name, movie_name, timing, price, uid in all_booked_seats:
            print(f"{seat:<5} | {name:<15} | {movie_name:<20} | {timing:<8} | ₹{price:<4} | {uid}")


    def view_my_bookings(self):
        print("\n--- Your Booked Tickets ---")
        found = False
        
        if os.path.exists(self.login.file2):
            with open(self.login.file2, 'r') as f:
                reader = csv.reader(f)
                next(reader) 
                
                for row in reader:
                    if len(row) >= 9 and row[2] == self.login.current_user and row[8].lower() == 'booked':
                        print(f"Date: {row[0]} | Movie: {row[6]} | Seats: {row[5]} | Show: {row[3]} | Price: ₹{row[7]}")
                        found = True
        
        for movie_id, movie_data in self.hall_data.items():
            for show_time, timing_data in movie_data['timings'].items():
                for seat, details in timing_data['booked_seats'].items():
                    if len(details) > 4 and details[4] == self.login.current_user:
                        print(f"[Active] Movie: {self.movie_list[movie_id]['name']} | Seat: {seat} | Show: {show_time} | Price: ₹{self.movie_list[movie_id]['price']}")
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
        
    def view_history(self):
        if not os.path.exists(self.login.file2):
            print("No booking history available yet.")
            return
        
        print(f"BOOKING HISTORY FOR USER: {self.login.current_user} ")
        
        with open(self.login.file2, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            found = False
            
            print(f"{'Date':<12} | {'Action':<10} | {'Movie':<15} | {'Show':<8} | {'Seats':<15} | {'Price':<10} | {'Status'}")
            print("-"*90)
            
            for row in reader:
                if len(row) >= 8 and row[2] == self.login.current_user: 
                    date = row[0]
                    movie = row[6]
                    show_time = row[3]
                    seats = row[5]
                    price = row[7] if len(row) > 7 else "N/A" 
                    status = row[8] if len(row) > 8 else row[7]
                    
                    action = "Booked" if status.lower() == "booked" else "Cancelled"

                    print(f"{date:<12} | {movie:<15} | {show_time:<8} | {seats:<15} | ₹{price:<9} | {status}")
                    found = True
                    
            if not found:
                print("No history records found for this user.")
        
    def reset_seats(self):
        print("\nSelect reset option:")
        print("1. Reset seats for a specific movie")
        print("2. Reset all seats (all movies)")
        print("3. Cancel")
        
        while True:
            try:
                choice = int(input("Enter choice (1-3): "))
                if choice not in [1, 2, 3]:
                    print("Please enter 1, 2, or 3")
                    continue
                break
            except ValueError:
                print("Please enter a valid number")

        if choice == 3:
            print("Reset operation cancelled.")
            return

        if choice == 1:
            print("\nAvailable Movies:")
            for key, val in self.movie_list.items():
                print(f"{key}. {val}")
            
            while True:
                try:
                    movie_id = int(input("Enter movie number to reset: "))
                    if movie_id not in self.movie_list:
                        print("Invalid movie number")
                        continue
                    break
                except ValueError:
                    print("Please enter a valid number")

            confirm = input(f"\nWARNING: This will reset ALL seats for '{self.movie_list[movie_id]['name']}'. Continue? (y/n): ").lower()
            if confirm != 'y':
                print("Seat reset cancelled.")
                return

            alpha_dict = {}
            alpha_chr = 65 
            for _ in range(self.n):
                alpha_dict[chr(alpha_chr)] = [0 for _ in range(self.n)]
                alpha_chr += 1

            self.hall_data[movie_id] = {
                'alpha_dict': alpha_dict,
                'ticket_count': self.n * self.n,
                'booked_seats': {}
            }
            print(f"\nAll seats for '{self.movie_list[movie_id]['name']}' have been reset.")

        elif choice == 2:
            confirm = input("\nWARNING: This will reset ALL seats for ALL movies. Continue? (y/n): ").lower()
            if confirm != 'y':
                print("Full reset cancelled.")
                return

            for movie_id in self.hall_data:
                alpha_dict = {}
                alpha_chr = 65
                for _ in range(self.n):
                    alpha_dict[chr(alpha_chr)] = [0 for _ in range(self.n)]
                    alpha_chr += 1

                self.hall_data[movie_id] = {
                    'alpha_dict': alpha_dict,
                    'ticket_count': self.n * self.n,
                    'booked_seats': {}
                }
            print("\nAll seats for all movies have been reset.")

    
    def confirm_payment(self, movie_id, num_seats):
        movie = self.movie_list[movie_id]['name']
        total = movie["price"] * num_seats
        
        print(f"\nPayment Required: ₹{total} for {num_seats} seat(s)")
        print(f"Movie: {movie['name']} (₹{movie['price']} per seat)")
        
        while True:
            confirm = input("Confirm payment? (y/n): ").lower()
            if confirm == 'y':
                print("Payment confirmed! Booking your tickets...")
                return True
            elif confirm == 'n':
                print("Payment cancelled. Booking not completed.")
                return False
            else:
                print("Please enter 'y' or 'n'")