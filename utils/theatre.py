from datetime import datetime
import csv
import os
import ast

class Theatre:

    _seat_tracker = {} 

    def __init__(self, login_instance):
        self.login = login_instance
        self.hall_data = {}
        self.booking_history = []
        self.current_user = None
        self._load_movies()
        self._load_screens()
        self._load_booking_history()
        self._load_hall_data() 
        self._init_seat_tracker()
        self.wallet_history_file = 'csvs/wallet_history.csv'
        self._init_wallet_history_file()


    def _init_wallet_history_file(self):
        """Initialize wallet history file with headers if it doesn't exist"""
        if not os.path.exists(self.wallet_history_file):
            with open(self.wallet_history_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'Time', 'Username', 'Amount', 'Description'])


    def _init_seat_tracker(self):
        """Initialize seat availability tracker"""
        for screen_id, screen_data in self.hall_data.items():
            for show_time in self.hall_data[screen_id]['seating'].keys():
                key = (screen_id, show_time)
                if key not in self._seat_tracker:
                    rows = screen_data['dimensions']['rows']
                    cols = screen_data['dimensions']['cols']
                    self._seat_tracker[key] = rows * cols

    def save_hall_data(self):
        try:
            with open('csvs/hall_data.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ScreenID', 'ShowTime', 'Row', 'SeatStatus'])
                
                for screen_id, screen_data in self.hall_data.items():
                    for show_time, timing_data in screen_data['seating'].items():
                        for row, seats in timing_data['alpha_dict'].items():
                            writer.writerow([
                                screen_id,
                                show_time,
                                row,
                                ','.join(str(s) for s in seats)
                            ])
        except Exception as e:
            print(f"Error saving hall data: {str(e)}")

    def _load_hall_data(self):
        try:
            if not os.path.exists('csvs/hall_data.csv'):
                return  # File doesn't exist yet (first run)
                
            with open('csvs/hall_data.csv', 'r') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    return
                    
                for row in reader:
                    screen_id = row['ScreenID']
                    show_time = row['ShowTime']
                    row_char = row['Row']
                    seats = row['SeatStatus'].split(',')
                    
                    if screen_id in self.hall_data and show_time in self.hall_data[screen_id]['seating']:
                        self.hall_data[screen_id]['seating'][show_time]['alpha_dict'][row_char] = [
                            'X' if s == 'X' else 0 for s in seats
                        ]
                        
                        booked_seats = sum(1 for s in seats if s == 'X')
                        self.hall_data[screen_id]['seating'][show_time]['ticket_count'] = (
                            self.hall_data[screen_id]['dimensions']['rows'] * 
                            self.hall_data[screen_id]['dimensions']['cols'] - 
                            booked_seats
                        )
        except Exception as e:
            print(f"[Warning] Could not load hall data: {str(e)}")

    def _load_movies(self):
        """Load movies from admin configuration"""
        self.movie_list = {}
        movies_file = 'csvs/movies.csv'
        
        if os.path.exists(movies_file):
            print("\nDebug - Loading movies from file...")  # Debug line
            with open(movies_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    print(f"Debug - Found movie: {row}")  # Debug line
                    if row.get('IsActive', '').lower() == 'yes':
                        movie_id = int(row['MovieID'])
                        self.movie_list[movie_id] = {
                            "name": row['Title'],
                            "price": float(row['Price']),
                            "screen_id": row['ScreenID'],
                        }
            print(f"Debug - Loaded {len(self.movie_list)} movies")  # Debug line

    def _load_screens(self):
        self.screens = {}
        screens_file = 'csvs/screens.csv'
        
        if os.path.exists(screens_file):
            with open(screens_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('Status', '').lower() == 'active':
                        screen_id = row['ScreenID']
                        rows = int(row['Rows'])
                        cols = int(row['Columns'])
                        
                        # Load timings from the screen data (semicolon-separated)
                        timings = row.get('Timings', '').split(';') if 'Timings' in row else []
                        if not timings and 'ShowTimes' in row:  # Backward compatibility
                            timings = row['ShowTimes'].split(';')
                        
                        self.screens[screen_id] = {
                            "rows": rows,
                            "columns": cols,
                            "last_maintenance": row.get('LastMaintenance', ''),
                            "timings": timings
                        }
                        self._init_screen_seating(screen_id, rows, cols, timings)


    def _init_screen_seating(self, screen_id, rows, cols, timings):
        if screen_id not in self.hall_data:
            self.hall_data[screen_id] = {
                'dimensions': {'rows': rows, 'cols': cols},
                'seating': {}
            }
        
        available_rows = [chr(65 + i) for i in range(rows)]
        available_cols = [str(i) for i in range(cols)]
        
        for time in timings:
            if time not in self.hall_data[screen_id]['seating']:
                self.hall_data[screen_id]['seating'][time] = {
                    'alpha_dict': {row: [0]*cols for row in available_rows},
                    'booked_seats': {},
                    'ticket_count': rows * cols,
                    'available_rows': available_rows,
                    'available_cols': available_cols
                }

    def _load_booking_history(self):
        if not os.path.exists(self.login.file2):
            return

        with open(self.login.file2, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if len(row) < 9:
                    continue
                
                if row.get('Ticket_Status', '').lower() != 'booked':
                    continue
                    
                screen_id = row.get('ScreenID')
                show_time = row.get('Show_Timing')
                seats_str = row.get('Seat_Numbers', '[]')
                
                try:
                    seats = ast.literal_eval(seats_str) if seats_str.startswith('[') else [seats_str]
                except:
                    continue
                    
                if screen_id not in self.hall_data or show_time not in self.hall_data[screen_id]['seating']:
                    continue
                    
                timing_data = self.hall_data[screen_id]['seating'][show_time]
                
                for seat in seats:
                    try:
                        row_char = seat[0].upper()
                        col_str = seat[1:]
                        col_index = timing_data['available_cols'].index(col_str)
                        
                        timing_data['alpha_dict'][row_char][col_index] = 'X'
                        timing_data['ticket_count'] -= 1
                    except (ValueError, IndexError):
                        continue


    def seats(self, screen_id, rows, cols):
        """Initialize seating for a specific screen with dynamic timings"""
        self.available_rows = [chr(65 + i) for i in range(rows)]
        self.available_cols = [str(i) for i in range(cols)]
        
        # Get the timings for this screen
        if screen_id not in self.hall_data:
            self.hall_data[screen_id] = {
                'dimensions': {'rows': rows, 'cols': cols},
                'seating': {}
            }
        
        # Get timings from screen data (should be loaded already)
        timings = []
        if screen_id in self.screens:
            timings = self.screens[screen_id].get('timings', [])
        
        # Initialize seating for each timing
        for time in timings:
            if time not in self.hall_data[screen_id]['seating']:
                self.hall_data[screen_id]['seating'][time] = {
                    'alpha_dict': {row: [0]*cols for row in self.available_rows},
                    'booked_seats': {},
                    'ticket_count': rows * cols,
                    'available_rows': self.available_rows,
                    'available_cols': self.available_cols
                }

    def display_seats(self):
        print("\nAvailable Movies:")
        for key, val in self.movie_list.items():
            print(f"{key}. {val['name']} (Screen: {val['screen_id']})")

        try:
            movie_id = int(input("Enter the serial number of the movie to view its seating: "))
            if movie_id not in self.movie_list:
                print("Invalid movie number.")
                return

            movie_data = self.movie_list[movie_id]
            screen_id = movie_data['screen_id']
            
            if screen_id not in self.hall_data:
                print(f"Screen {screen_id} not found.")
                return

            print(f"\n--- Seating for '{movie_data['name']}' ---")
            
            for show_time, timing_data in self.hall_data[screen_id]['seating'].items():
                print(f"\n{show_time} Show:")
                print("  ", " ".join(f"{col:>2}" for col in timing_data['available_cols']))
                
                for row_label in timing_data['available_rows']:
                    seats = timing_data['alpha_dict'][row_label]
                    print(f"{row_label}:", " ".join(' X' if seat == 'X' else ' .' for seat in seats))

        except ValueError:
            print("Please enter a valid number.")


    def update_booking_csv(self, name, uid, show_time, seats, movie_id, status, total_price=None):
        try:
            movie_name = self.movie_list[movie_id]['name']
            screen_id = self.movie_list[movie_id].get('screen_id', 'SC1')
            
            booking_record = {
                'Date': datetime.today().strftime('%Y-%m-%d'),
                'UserName': name,
                'UID': uid,
                'ScreenID': screen_id,
                'Show_Timing': show_time,
                'Seat_Numbers': str(seats),
                'Movie_Name': movie_name,
                'Total_Price': round(total_price, 2),
                'Ticket_Status': status
            }

            file_exists = os.path.exists(self.login.file2)
            
            with open(self.login.file2, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=booking_record.keys())
                if not file_exists or f.tell() == 0:
                    writer.writeheader()
                writer.writerow(booking_record)
            
            self.booking_history.append(booking_record)
            
        except Exception as e:
            print(f"Error updating booking records: {str(e)}")
            raise

    def book_ticket(self):
        print("\nAvailable Movies:")
        print(f"Debug - Total movies in list: {len(self.movie_list)}")
        sorted_movies = sorted(self.movie_list.items(), key=lambda x: x[0])
        
        # First display all movies
        for movie_id, movie_data in sorted_movies:
            if not all(key in movie_data for key in ['name', 'price', 'screen_id']):
                print(f"Warning: Skipping invalid movie entry (ID: {movie_id})")
                continue
            print(f"{movie_id}. {movie_data['name']} ₹{movie_data['price']} (Screen: {movie_data['screen_id']})")

        # Then get user input
        while True:
            try:
                movie_id = int(input("Enter the serial number of the movie: "))
                if movie_id not in self.movie_list:
                    print("Please enter a valid movie serial number.")
                    continue
                break
            except ValueError:
                print("Please enter a number only.")
        
        # Rest of the method remains the same...
        movie_data = self.movie_list[movie_id]
        screen_id = movie_data['screen_id']

        if screen_id not in self.screens:
            print(f"Screen {screen_id} not found or inactive")
            return
        
        if screen_id not in self.hall_data:
            print(f"Error: Screen {screen_id} not found in hall data")
            return

        show_time = self.get_movie_timing(screen_id)
        if show_time is None:
            return

        timing_data = self.hall_data[screen_id]['seating'][show_time]
        available_rows = timing_data['available_rows']
        available_cols = timing_data['available_cols']
        
        actual_available = sum(
            seat == 0 
            for row in timing_data['alpha_dict'].values() 
            for seat in row
        )
        
        while True:
            try:
                n = input(f"Enter the number of seats you want to book for {show_time} (Available: {actual_available}): ")
                n = int(n)
                if n <= 0:
                    print("Please enter a positive number.")
                    continue
                if n > actual_available:
                    print(f"Only {actual_available} seats available for this show.")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter a number only.")

        total_price = movie_data["price"] * n
        
        balance = self.login.check_balance(self.login.current_user)
        print(f"\nYour current balance: ₹{balance}")
        print(f"Total booking amount: ₹{total_price}")
        
        if balance < total_price:
            print("\nInsufficient balance!")
            print(f"You need ₹{total_price - balance} more to book these tickets.")
            return

        user_name = self.login.user_names.get(self.login.current_user)
        if user_name:
            print(f"\nWelcome back, {user_name}!")
            print(f"Booking will be made under your name: {user_name}")
            use_same = input("Would you like to use this name? (y/n): ").lower()
            if use_same != 'y':
                user_name = input("Please enter your name for this booking: ").strip()
                while not user_name:
                    print("Name cannot be empty.")
                    user_name = input("Please enter your name for the booking: ").strip()
                self.login.user_names[self.login.current_user] = user_name
        else:
            user_name = input("Please enter your name for the booking: ").strip()
            while not user_name:
                print("Name cannot be empty.")
                user_name = input("Please enter your name for the booking: ").strip()
            self.login.user_names[self.login.current_user] = user_name

        booked = 0
        booked_seats_list = []
        selected_seats = set()
        
        while booked < n:
            print(f"\n--- Seating for '{movie_data['name']}' at {show_time} ---")
            print("   ", " ".join(f"{col:>2}" for col in available_cols))
            for row_label in available_rows:
                seats = timing_data['alpha_dict'][row_label]
                print(f"{row_label}:", " ".join(' X' if seat == 'X' else ' .' for seat in seats))
            
            print("\nSeats marked 'X' are booked, '.' are available")
            print(f"Available rows: {', '.join(available_rows)}")
            print(f"Available columns: {', '.join(available_cols)}")

            try:
                row = input("Choose row (letter): ").upper()
                col = input("Choose column (number): ")
                
                if row not in available_rows or col not in available_cols:
                    print("\nInvalid selection. Please choose from available options.")
                    continue
                    
                seat_num = f"{row}{col}"
                col_index = available_cols.index(col)
                
                if seat_num in selected_seats:
                    print("You've already selected this seat in current booking. Choose another.")
                    continue
                    
                if timing_data['alpha_dict'][row][col_index] == 'X':
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
                    new_balance = self.login.add_to_wallet(self.login.current_user, -total_price, description="Purchase")
                    print(f"\n₹{total_price} deducted. New balance: ₹{new_balance}")
                    
                    for seat in booked_seats_list:
                        row_char = seat[0].upper()
                        col_str = seat[1:]
                        col_index = available_cols.index(col_str)
                        
                        if timing_data['alpha_dict'][row_char][col_index] == 0:
                            timing_data['alpha_dict'][row_char][col_index] = 'X'
                            timing_data['ticket_count'] -= 1
                        
                        timing_data['booked_seats'][seat] = {
                            'user_name': user_name,
                            'movie_id': movie_id,
                            'seat': seat,
                            'show_time': show_time,
                            'user_id': self.login.current_user,
                            'price_paid': movie_data["price"],
                            'screen_id': screen_id
                        }
                    
                    self.update_booking_csv(
                        name=user_name,
                        uid=self.login.current_user,
                        show_time=show_time,
                        seats=booked_seats_list,
                        movie_id=movie_id,
                        status='booked',
                        total_price=total_price
                    )

                    self.booking_history.append({
                        'Date': datetime.today().strftime('%Y-%m-%d'),
                        'UserName': user_name,
                        'UID': self.login.current_user,
                        'ScreenID': screen_id,
                        'Show_Timing': show_time,
                        'Seat_Numbers': booked_seats_list,
                        'Movie_Name': movie_data['name'],
                        'Total_Price': total_price,
                        'Ticket_Status': 'booked'
                    })

                    self.save_hall_data() 

                    print("\n" + "="*50)
                    print("BOOKING CONFIRMED".center(50))
                    print("="*50)
                    print(f"{'Movie:':<15} {movie_data['name']}")
                    print(f"{'Screen:':<15} {screen_id}")
                    print(f"{'Time:':<15} {show_time}")
                    print(f"{'Seats:':<15} {', '.join(booked_seats_list)}")
                    print(f"{'Total Paid:':<15} ₹{total_price}")
                    print(f"{'New Balance:':<15} ₹{new_balance}")
                    print("="*50)
                    break
                    
                except Exception as e:
                    print(f"\nError processing booking: {str(e)}")
                    try:
                        self.login.add_to_wallet(self.login.current_user, total_price)
                        print("Booking failed. Full refund issued.")
                    except:
                        print("Critical error: Could not issue refund. Please contact support.")
                    break
            
            elif confirm == 'n':
                print("Booking cancelled. Seats released.")
                break
            
            else:
                print("Please enter 'y' or 'n'")


    def cancel_ticket(self):        
        user_tickets = []

        for screen_id, screen_data in self.hall_data.items():
            for show_time, timing_data in screen_data['seating'].items():
                for seat, details in timing_data['booked_seats'].items():
                    if isinstance(details, dict) and details.get('user_id') == self.login.current_user:
                        movie_id = details.get('movie_id')
                        if movie_id in self.movie_list:
                            user_tickets.append({
                                'screen_id': screen_id,
                                'movie_id': movie_id,
                                'movie': self.movie_list[movie_id]['name'],
                                'show_time': show_time,
                                'seat': seat,
                                'details': details,
                                'price_paid': details.get('price_paid', self.movie_list[movie_id]['price'])
                            })

        if not user_tickets:
            print("\nYou have no active bookings to cancel.")
            return

        print("\nYour Bookings:")
        print("-"*70)
        print(f"{'#':<3} | {'Movie':<20} | {'Screen':<6} | {'Time':<8} | {'Seat':<6} | {'Price':<8}")
        print("-"*70)
        for i, ticket in enumerate(user_tickets, 1):
            print(f"{i:<3} | {ticket['movie'][:19]:<20} | {ticket['screen_id']:<6} | "
                f"{ticket['show_time']:<8} | {ticket['seat']:<6} | ₹{ticket['price_paid']:<7}")

        try:
            choice = input("\nEnter ticket number to cancel (0 to return): ").strip()
            if choice == '0':
                return
                
            choice = int(choice)
            if not 1 <= choice <= len(user_tickets):
                print("Invalid selection. Please enter a valid ticket number.")
                return
                
            selected = user_tickets[choice-1]
            movie_id = selected['movie_id']
            show_time = selected['show_time']
            seat = selected['seat']
            screen_id = selected['screen_id']
            movie_name = selected['movie']
            details = selected['details']
            refund_amount = selected['price_paid']

            confirm = input(f"\nConfirm cancel seat {seat} for {movie_name} at {show_time}? (y/n): ").lower()
            if confirm != 'y':
                print("Cancellation aborted.")
                return

            timing_data = self.hall_data[screen_id]['seating'][show_time]
            available_cols = timing_data['available_cols']
            
            row_char = seat[0].upper()
            col_str = seat[1:]
            
            try:
                col_index = available_cols.index(col_str) 
                
                timing_data['alpha_dict'][row_char][col_index] = 0
                timing_data['ticket_count'] += 1
                timing_data['booked_seats'].pop(seat, None)

                new_balance = self.login.add_to_wallet(self.login.current_user, refund_amount)
                
                self.update_booking_csv(
                    name=details.get('user_name', self.login.current_user),
                    uid=self.login.current_user,
                    show_time=show_time,
                    seats=[seat],
                    movie_id=movie_id,
                    status='cancelled',
                    total_price=-refund_amount
                )

                self.save_hall_data()

                print("\n" + "="*50)
                print("CANCELLATION SUCCESSFUL".center(50))
                print("="*50)
                print(f"{'Movie:':<15} {movie_name}")
                print(f"{'Screen:':<15} {screen_id}")
                print(f"{'Time:':<15} {show_time}")
                print(f"{'Seat:':<15} {seat}")
                print(f"{'Refund Amount:':<15} ₹{refund_amount}")
                print(f"{'New Balance:':<15} ₹{new_balance}")
                print("="*50)

            except ValueError as e:
                print(f"\nError processing seat {seat}: {str(e)}")
                print("Please contact support for assistance.")

        except ValueError:
            print("Invalid input. Please enter a number.")

        except Exception as e:
            print(f"\nError cancelling ticket: {str(e)}")
            print("Please contact support for assistance.")


    def check_remaining_seats(self):
        print("\n" + "="*60)
        print("AVAILABLE SEATS".center(60))
        print("="*60)
        print(f"{'Screen':<8} | {'Movie':<25} | {'Time':<8} | {'Available':<10} | {'Capacity':<10}")
        print("-"*60)
        
        screen_ids = sorted(
            [sid for sid in self.hall_data.keys() if sid.startswith('SC')],
            key=lambda x: int(x[2:]) if x[2:].isdigit() else 0
        )
        
        for screen_id in screen_ids:
            screen_data = self.hall_data[screen_id]
            rows = screen_data['dimensions']['rows']
            cols = screen_data['dimensions']['cols']
            total_capacity = rows * cols
            
            screen_movies = {
                mid: data for mid, data in self.movie_list.items() 
                if data.get('screen_id') == screen_id
            }
            
            for movie_id, movie_data in screen_movies.items():
                movie_name = movie_data['name']
                
                for show_time in self.hall_data[screen_id]['seating'].keys():
                    available_seats = screen_data['seating'][show_time]['ticket_count']
                    
                    print(f"{screen_id:<8} | {movie_name[:24]:<25} | {show_time:<8} | {available_seats:<10} | {total_capacity:<10}")
        
        print("="*60)


    def get_movie_timing(self, screen_id):
        if screen_id not in self.hall_data:
            return None
            
        timings = list(self.hall_data[screen_id]['seating'].keys())

        if not timings:
            print("No show timings available for this screen")
            return None
        
        while True:
            try:
                print("\n" + "="*40)
                print("SELECT SHOW TIME".center(40))
                print("="*40)
                
                print("\nAvailable Show Timings:\n")
                for i, timing in enumerate(timings, 1):
                    print(f"  {i:>2}. {timing}")
                
                print("\n" + "-"*40)
                user_input = input(
                    f"Select timing (1-{len(timings)}, or '0' to cancel): "
                ).strip()
                
                if user_input == '0':
                    print("\nTiming selection cancelled.")
                    return None
                    
                if not user_input:
                    print("\nError: Please enter a selection.")
                    continue
                    
                if not user_input.isdigit():
                    print("\nError: Please enter a number only.")
                    continue
                    
                timing_choice = int(user_input)
                
                if not 1 <= timing_choice <= len(timings):
                    print(f"\nError: Please select between 1 and {len(timings)}")
                    continue
                    
                selected_time = timings[timing_choice - 1]
                print(f"\nSelected show time: {selected_time}")
                return selected_time
                
            except KeyboardInterrupt:
                print("\n\nOperation cancelled by user.")
                return None
            except Exception as e:
                print(f"\nAn error occurred: {str(e)}")
                print("Please try again.\n")
            

    def view_history(self):
        """Display booking history with enhanced formatting and details"""
        try:
            if not os.path.exists(self.login.file2):
                print("\n" + "="*60)
                print("No booking history available yet.".center(60))
                print("="*60)
                return
            
            print("\n" + "="*90)
            print(f"BOOKING HISTORY FOR: {self.login.current_user}".center(90))
            print("="*90)
            
            with open(self.login.file2, 'r') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    print("\nNo valid booking records found.")
                    return
                    
                date_field = 'Date' if 'Date' in reader.fieldnames else None
                movie_field = 'Movie_Name' if 'Movie_Name' in reader.fieldnames else 'Movie'
                show_field = 'Show_Timing' if 'Show_Timing' in reader.fieldnames else 'Show'
                seats_field = 'Seat_Numbers' if 'Seat_Numbers' in reader.fieldnames else 'Seats'
                price_field = 'Total_Price' if 'Total_Price' in reader.fieldnames else 'Price'
                status_field = 'Ticket_Status' if 'Ticket_Status' in reader.fieldnames else 'Status'
                screen_field = 'ScreenID' if 'ScreenID' in reader.fieldnames else None
                uid_field = 'UID' if 'UID' in reader.fieldnames else None
                
                found = False
                
                print(f"\n{'Date':<12} | {'Action':<8} | {'Movie':<20} | {'Screen':<6} | {'Time':<8} | "
                    f"{'Seats':<12} | {'Amount':<10} | {'Status'}")
                print("-"*90)
                
                for row in reader:
                    if uid_field and row.get(uid_field) != self.login.current_user:
                        continue
                        
                    date = row.get(date_field, 'Unknown')
                    movie = row.get(movie_field, 'Unknown')[:19]
                    show_time = row.get(show_field, 'Unknown')
                    seats = row.get(seats_field, 'N/A')
                    if seats.startswith('[') and seats.endswith(']'):
                        try:
                            seats = ', '.join(ast.literal_eval(seats))
                        except:
                            pass
                    price = float(row.get(price_field, 0)) if row.get(price_field, '').replace('.','',1).isdigit() else 0
                    status = row.get(status_field, 'Unknown')
                    screen = row.get(screen_field, 'N/A')
                    
                    action = "Booked" if status.lower() == "booked" else "Cancelled"
                    amount_display = f"₹{abs(price):.2f}"
                    
                    if status.lower() == "cancelled":
                        amount_display = f"(Refund) ₹{abs(price):.2f}"
                    
                    print(f"{date:<12} | {action:<8} | {movie:<20} | {screen:<6} | {show_time:<8} | "
                        f"{str(seats):<12} | {amount_display:<10} | {status.capitalize()}")
                    found = True
                    
                if not found:
                    print("\nNo booking history found for this user.")
                    
            print("\n" + "="*90)
            print("End of History".center(90))
            print("="*90)
            
        except Exception as e:
            print(f"\nError viewing history: {str(e)}")
            print("Please contact support if this error persists.")


    def record_wallet_transaction(self, username, amount, description=""):
        """Record a wallet transaction with timestamp"""
        try:
            now = datetime.now()
            with open(self.wallet_history_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    now.strftime('%Y-%m-%d'),
                    now.strftime('%H:%M:%S'),
                    username,
                    amount,
                    description
                ])
        except Exception as e:
            print(f"Error recording wallet transaction: {e}")

    def view_wallet_history(self):
        """Wrapper to call login's wallet history"""
        self.login.get_wallet_history(self.login.current_user)
    
    def _validate_time_format(self, time_str):
        try:
            datetime.strptime(time_str, '%H:%M')
            return True
        except ValueError:
            return False

    
    def user_menu(self):
        while True:
            print("\n--- Theatre Booking System ---")
            print("1. Book Tickets")
            print("2. Display Seats")
            print("3. Cancel Ticket")
            print("4. Check Remaining Seats")
            print("5. Check Balance")
            print("6. Add Money to Wallet")
            print("7. View Wallet History")
            print("8. View User History")
            print("9. Exit")

            choice = input("Enter your choice (1-9): ")

            if choice == '1':
                self.book_ticket()
            elif choice == '2':
                self.display_seats()
            elif choice == '3':
                self.cancel_ticket()
            elif choice == '4':
                self.check_remaining_seats()
            elif choice == '5':
                balance = self.login.check_balance(self.login.current_user)
                print(f"\nYour current balance: ₹{balance:.2f}")
            elif choice == '6':
                try:
                    amount = float(input("Enter amount to add: ₹"))
                    if amount > 0:
                        if not self.login.current_user:
                            print("Error: No user logged in")
                            continue
                            
                        new_balance = self.login.add_to_wallet(
                            username=self.login.current_user,
                            amount=amount,
                            description="Wallet top-up"
                        )
                    else:
                        print("Please enter a positive amount")
                except ValueError:
                    print("Please enter a valid amount")
            elif choice == '7':
                self.view_wallet_history()
            elif choice == '8':  
                self.view_history()
            elif choice == '9':
                print("Exiting the system. Thank you!")
                return
            else:
                print("Invalid choice. Please enter a number between 1 and 9.")