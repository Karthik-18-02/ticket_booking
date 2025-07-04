from datetime import datetime
import csv
import os
import ast
import uuid

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
        self.booking_fields = ['BookingID','Date','Time','UserName','UID','ScreenID','Show_Timing','Seat_Numbers','Movie_Name','Movie_ID','Total_Price','Ticket_Status','Cancellation_Date']


    def _init_wallet_history_file(self):
        if not os.path.exists(self.wallet_history_file):
            with open(self.wallet_history_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'Time', 'Username', 'Amount', 'Description'])


    def _init_seat_tracker(self):
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
                return
                
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
                        seat_status = []
                        for s in seats:
                            if s == 'X':
                                seat_status.append('X')
                            else:
                                try:
                                    seat_status.append(int(s))
                                except ValueError:
                                    seat_status.append(0)
                        
                        timing_data = self.hall_data[screen_id]['seating'][show_time]
                        timing_data['alpha_dict'][row_char] = seat_status
                        
                        available = sum(1 for s in seat_status if s == 0)
                        timing_data['ticket_count'] = available
                        
                        booked_seats = sum(1 for s in seat_status if s == 'X')
                        self.hall_data[screen_id]['seating'][show_time]['ticket_count'] = (
                            self.hall_data[screen_id]['dimensions']['rows'] * 
                            self.hall_data[screen_id]['dimensions']['cols'] - 
                            booked_seats
                        )
        except Exception as e:
            print(f"[Warning] Could not load hall data: {str(e)}")

    def _load_movies(self):
        self.movie_list = {}
        movies_file = 'csvs/movies.csv'
        
        if os.path.exists(movies_file):
            with open(movies_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('IsActive', '').lower() == 'yes':
                        movie_id = int(row['MovieID'])
                        self.movie_list[movie_id] = {
                            "name": row['Title'],
                            "price": float(row['Price']),
                            "screen_id": row['ScreenID'],
                        }

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
                        
                        timings = row.get('Timings', '').split(';') if 'Timings' in row else []
                        if not timings and 'ShowTimes' in row:
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
        """Load booking history from file and reconstruct all active bookings"""
        if not os.path.exists(self.login.file2):
            return

        with open(self.login.file2, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if len(row) < 9:
                    continue
                    
                self.booking_history.append(row)
                
                if row.get('Ticket_Status', '').lower() != 'booked':
                    continue
                    
                screen_id = row.get('ScreenID')
                show_time = row.get('Show_Timing')
                seats_str = row.get('Seat_Numbers', '[]')
                user_id = row.get('UID')
                movie_name = row.get('Movie_Name')
                
                try:
                    seats = ast.literal_eval(seats_str) if seats_str.startswith('[') else [seats_str]
                except:
                    continue
                    
                if screen_id not in self.hall_data:
                    screen_info = self._get_screen_info(screen_id)
                    if screen_info:
                        rows = int(screen_info['Rows'])
                        cols = int(screen_info['Columns'])
                        self._init_screen_seating(screen_id, rows, cols, [show_time])
                    
                if (screen_id not in self.hall_data or 
                    show_time not in self.hall_data[screen_id]['seating']):
                    continue
                    
                timing_data = self.hall_data[screen_id]['seating'][show_time]
                
                movie_id = None
                for mid, movie in self.movie_list.items():
                    if movie['name'] == movie_name:
                        movie_id = mid
                        break
                
                if not movie_id:
                    continue
                    
                for seat in seats:
                    try:
                        row_char = seat[0].upper()
                        col_str = seat[1:]
                        col_index = timing_data['available_cols'].index(col_str)
                        
                        timing_data['alpha_dict'][row_char][col_index] = 'X'
                        timing_data['ticket_count'] -= 1
                        
                        timing_data['booked_seats'][seat] = {
                            'user_name': row.get('UserName'),
                            'movie_id': movie_id,
                            'seat': seat,
                            'show_time': show_time,
                            'user_id': user_id,
                            'price_paid': float(row.get('Total_Price', 0)) / len(seats),
                            'screen_id': screen_id,
                            'booking_date': row.get('Date')
                        }
                    except (ValueError, IndexError):
                        continue

    def _get_screen_info(self, screen_id):
        """Get screen info from screens.csv"""
        screens_file = 'csvs/screens.csv'
        if os.path.exists(screens_file):
            with open(screens_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('ScreenID') == screen_id:
                        return row
        return None


    def seats(self, screen_id, rows, cols):
        self.available_rows = [chr(65 + i) for i in range(rows)]
        self.available_cols = [str(i) for i in range(cols)]
        
        if screen_id not in self.hall_data:
            self.hall_data[screen_id] = {
                'dimensions': {'rows': rows, 'cols': cols},
                'seating': {}
            }
        
        timings = []
        if screen_id in self.screens:
            timings = self.screens[screen_id].get('timings', [])
        
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
            screen_id = self.movie_list[movie_id]['screen_id']
            
            booking_record = {
                'BookingID': str(uuid.uuid4()),
                'Date': datetime.today().strftime('%Y-%m-%d'),
                'Time': datetime.today().strftime('%H:%M:%S'),
                'UserName': name,
                'UID': uid,
                'ScreenID': screen_id,
                'Show_Timing': show_time,
                'Seat_Numbers': str(seats),
                'Movie_Name': movie_name,
                'Movie_ID': movie_id,
                'Total_Price': total_price,
                'Ticket_Status': status,
                'Cancellation_Date': '' if status.lower() != 'cancelled' else datetime.today().strftime('%Y-%m-%d')
            }

            user_file = f'csvs/bookings/{uid}_bookings.csv'
            os.makedirs('csvs/bookings', exist_ok=True)
            file_exists = os.path.exists(user_file)
            with open(user_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.booking_fields)
                if not file_exists or f.tell() == 0:
                    writer.writeheader()
                writer.writerow(booking_record)

            main_file = self.login.file2
            file_exists = os.path.exists(main_file)
            with open(main_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.booking_fields)
                if not file_exists or f.tell() == 0:
                    writer.writeheader()
                writer.writerow(booking_record)

            self.booking_history.append(booking_record)

        except Exception as e:
            print(f"Error updating booking records: {str(e)}")
            raise

    def book_ticket(self):
        print("\nAvailable Movies:")
        sorted_movies = sorted(self.movie_list.items(), key=lambda x: x[0])
        
        for movie_id, movie_data in sorted_movies:
            if not all(key in movie_data for key in ['name', 'price', 'screen_id']):
                print(f"Warning: Skipping invalid movie entry (ID: {movie_id})")
                continue
            print(f"{movie_id}. {movie_data['name']} ₹{movie_data['price']} (Screen: {movie_data['screen_id']})")

        while True:
            try:
                movie_id = int(input("Enter the serial number of the movie: "))
                if movie_id not in self.movie_list:
                    print("Please enter a valid movie serial number.")
                    continue
                break
            except ValueError:
                print("Please enter a number only.")
        
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
        user_bookings = []
        user_file = f'csvs/bookings/{self.login.current_user}_bookings.csv'
        
        if not os.path.exists(user_file):
            print("\nYou have no active bookings to cancel.")
            return
        
        with open(user_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Ticket_Status'].lower() == 'booked':
                    try:
                        seats = ast.literal_eval(row['Seat_Numbers']) if row['Seat_Numbers'].startswith('[') else [row['Seat_Numbers']]
                        user_bookings.append({
                            'booking_id': row['BookingID'],
                            'date': row['Date'],
                            'movie': row['Movie_Name'],
                            'movie_id': int(row['Movie_ID']),
                            'screen': row['ScreenID'],
                            'time': row['Show_Timing'],
                            'seats': seats,
                            'price': float(row['Total_Price']),
                            'status': row['Ticket_Status'],
                            'booking_date': row.get('Date')
                        })
                    except Exception as e:
                        print(f"Error processing booking {row.get('BookingID', 'unknown')}: {str(e)}")
                        continue

        if not user_bookings:
            print("\nYou have no active bookings to cancel.")
            return
        
        user_bookings.sort(key=lambda x: x.get('booking_date', ''), reverse=True)

        print("\nYour Active Bookings:")
        print("=" * 130)
        print(f"{'#':<3} | {'Booking ID':<12} | {'Movie':<25} | {'Screen':<8} | {'Date':<12} | {'Time':<8} | "
            f"{'Seats':<20} | {'Price':<10}")
        print("-" * 130)
        
        for i, booking in enumerate(user_bookings, 1):
            seats_str = ', '.join(booking['seats'][:3])
            if len(booking['seats']) > 3:
                seats_str += f" (+{len(booking['seats'])-3} more)"
                
            print(f"{i:<3} | {booking['booking_id'][:12]:<12} | {booking['movie'][:24]:<25} | "
                f"{booking['screen']:<8} | {booking['date']:<12} | {booking['time']:<8} | "
                f"{seats_str:<20} | ₹{booking['price']:<9.2f}")

        try:
            choice = input("\nEnter booking number to cancel (0 to return): ").strip()
            if choice == '0':
                return
                
            choice = int(choice)
            if not 1 <= choice <= len(user_bookings):
                print("Invalid selection. Please enter a valid number.")
                return
                
            selected = user_bookings[choice-1]
            self._process_cancellation(selected)

        except ValueError:
            print("Invalid input. Please enter a number.")

    def _process_cancellation(self, booking):
        confirm = input(f"\nConfirm cancellation of booking {booking['booking_id']} for {booking['movie']}? (y/n): ").lower()
        if confirm != 'y':
            print("Cancellation aborted.")
            return

        screen_id = booking['screen']
        show_time = booking['time']
        
        if screen_id in self.hall_data and show_time in self.hall_data[screen_id]['seating']:
            timing_data = self.hall_data[screen_id]['seating'][show_time]
            for seat in booking['seats']:
                try:
                    row_char = seat[0].upper()
                    col_str = seat[1:]
                    col_index = timing_data['available_cols'].index(col_str)
                    if timing_data['alpha_dict'][row_char][col_index] == 'X':
                        timing_data['alpha_dict'][row_char][col_index] = 0
                        timing_data['ticket_count'] += 1
                        timing_data['booked_seats'].pop(seat, None)
                except (ValueError, KeyError):
                    print(f"Warning: Could not free seat {seat}")

        refund_amount = booking['price']
        new_balance = self.login.add_to_wallet(
            self.login.current_user,
            refund_amount,
            description=f"Refund for {booking['movie']}"
        )

        try:
            user_file = f'csvs/bookings/{self.login.current_user}_bookings.csv'
            if os.path.exists(user_file):
                temp_file = f'{user_file}.tmp'
                with open(user_file, 'r') as infile, open(temp_file, 'w', newline='') as outfile:
                    reader = csv.DictReader(infile)
                    writer = csv.DictWriter(outfile, fieldnames=self.booking_fields)
                    writer.writeheader()
                    for row in reader:
                        if row['BookingID'] == booking['booking_id']:
                            row.update({
                                'Ticket_Status': 'cancelled',
                                'Cancellation_Date': datetime.today().strftime('%Y-%m-%d')
                            })
                        writer.writerow(row)
                os.replace(temp_file, user_file)

            main_file = self.login.file2
            if os.path.exists(main_file):
                temp_file = f'{main_file}.tmp'
                with open(main_file, 'r') as infile, open(temp_file, 'w', newline='') as outfile:
                    reader = csv.DictReader(infile)
                    writer = csv.DictWriter(outfile, fieldnames=self.booking_fields)
                    writer.writeheader()
                    for row in reader:
                        if row['BookingID'] == booking['booking_id']:
                            row.update({
                                'Ticket_Status': 'cancelled',
                                'Cancellation_Date': datetime.today().strftime('%Y-%m-%d')
                            })
                        writer.writerow(row)
                os.replace(temp_file, main_file)

            print("\n" + "="*60)
            print("CANCELLATION COMPLETED".center(60))
            print("="*60)
            print(f"{'Movie:':<15} {booking['movie']}")
            print(f"{'Screen:':<15} {booking['screen']}")
            print(f"{'Time:':<15} {booking['time']}")
            print(f"{'Seats:':<15} {', '.join(booking['seats'])}")
            print(f"{'Refund:':<15} ₹{refund_amount:.2f}")
            print(f"{'New Balance:':<15} ₹{new_balance:.2f}")
            print("="*60)

            self.save_hall_data()

        except Exception as e:
            # print(f"\nError during cancellation update: {str(e)}")
            if 'temp_file' in locals() and os.path.exists(temp_file):
                os.remove(temp_file)


    def view_ticket_details(self):
        """Display booked tickets in serialized order with detailed view option"""
        try:
            user_file = f'csvs/bookings/{self.login.current_user}_bookings.csv'
            
            if not os.path.exists(user_file):
                print("\nNo booked tickets found.")
                return
                
            bookings = []
            with open(user_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Ticket_Status'].lower() == 'booked':
                        try:
                            bookings.append({
                                'booking_id': row['BookingID'],
                                'date': row['Date'],
                                'time': row['Time'],
                                'movie': row['Movie_Name'],
                                'screen': row['ScreenID'],
                                'show_time': row['Show_Timing'],
                                'seats': ast.literal_eval(row['Seat_Numbers']) if row['Seat_Numbers'].startswith('[') else [row['Seat_Numbers']],
                                'price': float(row['Total_Price']),
                                'movie_id': row['Movie_ID']
                            })
                        except Exception as e:
                            print(f"Error processing booking {row.get('BookingID', 'unknown')}: {str(e)}")
                            continue

            if not bookings:
                print("\nNo active bookings found.")
                return

            bookings.sort(key=lambda x: (x['date'], x['time']), reverse=True)

            print("\n" + "="*120)
            print(f"YOUR BOOKED TICKETS".center(120))
            print("="*120)
            print(f"{'#':<3} | {'Booking ID':<12} | {'Movie':<25} | {'Screen':<8} | {'Date':<12} | {'Time':<8} | "
                f"{'Seats':<20} | {'Price':<10}")
            print("-"*120)
            
            for i, booking in enumerate(bookings, 1):
                seats_str = ', '.join(booking['seats'][:3])
                if len(booking['seats']) > 3:
                    seats_str += f" (+{len(booking['seats'])-3} more)"
                    
                print(f"{i:<3} | {booking['booking_id'][:12]:<12} | {booking['movie'][:24]:<25} | "
                    f"{booking['screen']:<8} | {booking['date']:<12} | {booking['show_time']:<8} | "
                    f"{seats_str:<20} | ₹{booking['price']:<9.2f}")

            while True:
                try:
                    choice = input("\nEnter ticket number to view details (0 to return): ").strip()
                    if choice == '0':
                        return
                        
                    choice = int(choice)
                    if not 1 <= choice <= len(bookings):
                        print("Invalid selection. Please enter a valid number.")
                        continue
                        
                    selected = bookings[choice-1]
                    self._display_ticket_details(selected)
                    break
                    
                except ValueError:
                    print("Invalid input. Please enter a number.")

        except Exception as e:
            print(f"\nError viewing ticket details: {str(e)}")


    def _display_ticket_details(self, booking):
        movie_data = self.movie_list.get(int(booking['movie_id']), {})
        
        print("\n" + "="*60)
        print("TICKET DETAILS".center(60))
        print("="*60)
        print(f"{'Booking ID:':<15} {booking['booking_id']}")
        print(f"{'Movie:':<15} {booking['movie']}")
        print(f"{'Screen:':<15} {booking['screen']}")
        print(f"{'Show Date:':<15} {booking['date']}")
        print(f"{'Show Time:':<15} {booking['show_time']}")
        print(f"{'Booked On:':<15} {booking['date']} at {booking['time']}")
        print(f"{'Seats:':<15} {', '.join(booking['seats'])}")
        print(f"{'Total Price:':<15} ₹{booking['price']:.2f}")
        
        if 'screen' in booking and 'show_time' in booking:
            screen_id = booking['screen']
            show_time = booking['show_time']
            
            if screen_id in self.hall_data and show_time in self.hall_data[screen_id]['seating']:
                print("\nSeat Map:")
                timing_data = self.hall_data[screen_id]['seating'][show_time]
                print("   ", " ".join(f"{col:>2}" for col in timing_data['available_cols']))
                
                user_seats = set(booking['seats'])
                
                for row_label in timing_data['available_rows']:
                    seats = timing_data['alpha_dict'][row_label]
                    seat_display = []
                    for col_idx, seat in enumerate(seats):
                        seat_pos = f"{row_label}{timing_data['available_cols'][col_idx]}"
                        if seat_pos in user_seats:
                            seat_display.append(' O')
                        elif seat == 'X':
                            seat_display.append(' X')
                        else:
                            seat_display.append(' .')
                    print(f"{row_label}:", " ".join(seat_display))
        
        print("="*60)
        input("\nPress Enter to return to the menu...")


    def check_remaining_seats(self):
        seats_data = []
        
        print("\n" + "="*75)
        print("AVAILABLE SEATS".center(75))
        print("="*75)
        print(f"{'Screen':<8} | {'Movie':<25} | {'Time':<8} | {'Available':<10} | {'Capacity':<10}")
        print("-"*75)
        
        try:
            self._load_hall_data()
            
            for screen_id in sorted(self.hall_data.keys()):
                if not screen_id.startswith('SC'):
                    continue
                    
                screen_info = self.hall_data[screen_id]
                rows = screen_info['dimensions']['rows']
                cols = screen_info['dimensions']['cols']
                total_capacity = rows * cols
                
                current_movies = [
                    movie for movie in self.movie_list.values() 
                    if movie['screen_id'] == screen_id
                ]
                
                for show_time, timing_data in screen_info['seating'].items():
                    available_seats = 0
                    for row in timing_data['alpha_dict'].values():
                        available_seats += row.count(0)
                    
                    timing_data['ticket_count'] = available_seats
                    
                    movie_name = "No movie assigned"
                    for movie in current_movies:
                        movie_name = movie['name']
                        break
                        
                    seats_data.append({
                        'screen_id': screen_id,
                        'movie': movie_name,
                        'show_time': show_time,
                        'available_seats': available_seats,
                        'total_capacity': total_capacity,
                        'seat_map': timing_data['alpha_dict']
                    })
                    
                    print(f"{screen_id:<8} | {movie_name[:24]:<25} | {show_time:<8} | "
                        f"{available_seats:<10} | {total_capacity:<10}")
            
            print("="*75)
            return seats_data
            
        except Exception as e:
            print(f"\nError checking seat availability: {str(e)}")
            return []

    def _print_seats_info(self, seats_info):
        print("\n" + "="*75)
        print("AVAILABLE SEATS".center(75))
        print("="*75)
        print(f"{'Screen':<8} | {'Movie':<25} | {'Time':<8} | {'Available':<10} | {'Capacity':<10}")
        print("-"*75)
        
        for info in seats_info:
            print(f"{info['screen_id']:<8} | {info['movie_name'][:24]:<25} | "
                f"{info['show_time']:<8} | {info['available_seats']:<10} | "
                f"{info['total_capacity']:<10}")
        
        print("="*75)
        


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
        try:
            user_file = f'csvs/bookings/{self.login.current_user}_bookings.csv'
            
            if not os.path.exists(user_file):
                print("\nNo booking history found.")
                return
                
            print("\n" + "="*120)
            print(f"BOOKING HISTORY FOR: {self.login.current_user}".center(120))
            print("="*120)
            
            with open(user_file, 'r') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    print("\nNo valid booking records found.")
                    return
                    
                print(f"\n{'Booking ID':<12} | {'Date':<12} | {'Movie':<25} | {'Screen':<8} | {'Time':<8} | "
                    f"{'Seats':<20} | {'Price':<10} | {'Status':<12} | {'Cancelled On':<12}")
                print("-"*120)
                
                for row in reader:
                    try:
                        seats = ast.literal_eval(row['Seat_Numbers']) if row['Seat_Numbers'].startswith('[') else [row['Seat_Numbers']]
                        seats_display = ', '.join(seats) if isinstance(seats, list) else row['Seat_Numbers']
                        
                        print(f"{row['BookingID'][:12]:<12} | {row['Date']:<12} | {row['Movie_Name'][:24]:<25} | "
                            f"{row['ScreenID']:<8} | {row['Show_Timing']:<8} | {seats_display[:19]:<20} | "
                            f"₹{float(row['Total_Price']):<9.2f} | {row['Ticket_Status'].capitalize():<12} | "
                            f"{row.get('Cancellation_Date', '-'):<12}")
                    except Exception as e:
                        print(f"\nError processing record: {str(e)}")
                        continue
                        
            print("="*120)
            
        except Exception as e:
            print(f"\nError viewing history: {str(e)}")

    def _process_booking_row(self, row):
        seats = row.get('Seat_Numbers', 'N/A')
        if seats.startswith('[') and seats.endswith(']'):
            try:
                seats = ', '.join(ast.literal_eval(seats))
            except:
                pass
        
        return {
            'date': row.get('Date', 'Unknown'),
            'movie': row.get('Movie_Name', 'Unknown'),
            'screen': row.get('ScreenID', 'N/A'),
            'time': row.get('Show_Timing', 'Unknown'),
            'seats': seats,
            'price': float(row.get('Total_Price', 0)) if str(row.get('Total_Price', '0')).replace('.','',1).isdigit() else 0,
            'status': row.get('Ticket_Status', 'Unknown'),
            'original_row': row
        }

    def _print_no_history_message(self):
        print("\n" + "="*60)
        print("No booking history available yet.".center(60))
        print("="*60)

    def _print_history_header(self):
        print("\n" + "="*100)
        print(f"{'BOOKING HISTORY':^100}")
        print("="*100)
        print(f"{'Date':<12} | {'Action':<8} | {'Movie':<20} | {'Screen':<6} | {'Time':<8} | "
            f"{'Seats':<12} | {'Amount':<10} | {'Status'}")
        print("-"*100)

    def _print_history_footer(self):
        print("="*100)
        print("End of History".center(100))
        print("="*100)


    def record_wallet_transaction(self, username, amount, description=""):
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
            print("9. View Ticket Details")
            print("10. Exit")

            choice = input("Enter your choice (1-10): ")

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
                self.view_ticket_details() 
            elif choice == '10':
                print("Exiting the system. Thank you!")
                return
            else:
                print("Invalid choice. Please enter a number between 1 and 10.")