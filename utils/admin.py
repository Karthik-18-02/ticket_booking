import csv
import os
from datetime import datetime
from utils.theatre import Theatre

class Admin:
    def __init__(self, theatre_instance):
        self.theatre = theatre_instance
        self.screens_file = 'csvs/screens.csv'
        self.movies_file = 'csvs/movies.csv'
        self._initialize_files()

    def _initialize_files(self):
        os.makedirs('csvs', exist_ok=True)

        if not os.path.exists(self.movies_file):
            with open(self.movies_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['MovieID', 'Title', 'ScreenID', 'Price', 'IsActive'])

        screens_file = self.screens_file
        try:
            needs_recreation = False
            if os.path.exists(screens_file):
                try:
                    with open(screens_file, 'r') as f:
                        reader = csv.reader(f)
                        headers = next(reader, [])
                        if not all(h in headers for h in ['ScreenID', 'Rows', 'Columns', 'Status', 'Timings']):
                            needs_recreation = True
                except Exception as e:
                    print(f"Warning: Error reading screens file - {str(e)}")
                    needs_recreation = True
            
            if needs_recreation or not os.path.exists(screens_file):
                if os.path.exists(screens_file):
                    backup_name = f"{screens_file}.{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
                    try:
                        os.replace(screens_file, backup_name)
                        print(f"Created backup: {backup_name}")
                    except Exception as e:
                        print(f"Warning: Could not create backup - {str(e)}")
                        try:
                            os.remove(screens_file)
                        except:
                            pass
                
                with open(screens_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['ScreenID', 'Rows', 'Columns', 'LastMaintenance', 'Status', 'Timings'])
                    writer.writerow(['SC1', 10, 10, datetime.now().strftime('%Y-%m-%d'), 'Active', '09:30;12:30;16:00;19:30;23:30'])
        
        except Exception as e:
            print(f"Critical error initializing screens file: {str(e)}")
            raise
        
        if not os.path.exists(self.movies_file):
            with open(self.movies_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['MovieID', 'Title', 'ScreenID', 'Price', 'IsActive'])

    def _validate_time_format(self, time_str):
        try:
            time_obj = datetime.strptime(time_str, '%H:%M')
            return time_obj.strftime('%H:%M')
        except ValueError:
            return False

    def _validate_time_sequence(self, times):
        try:
            time_objs = [datetime.strptime(t, '%H:%M') for t in times]
            return all(time_objs[i] < time_objs[i+1] for i in range(len(time_objs)-1))
        except Exception:
            return False

    def add_screen(self):
        print("\n--- Add New Screen ---")
        
        screen_id = None
        while not screen_id:
            screen_id = input("Enter screen ID: ").strip()
            if not screen_id:
                print("Screen ID cannot be empty")

        while True:
            try:
                rows = int(input("Number of rows: "))
                if rows <= 3 or rows >= 26:
                    print("Rows should be greater than 2 and less than 27")
                else:
                    break
            
            except ValueError:
                print("Please enter a number only between 2 and 27")

        while True:
            try:
                cols = int(input("Number of columns per row: "))
                if cols is not int:
                    print("Please enter a number between 2 and 27")
                if cols <= 3 or cols >= 26:
                    print("Columns per row should be greater than 2 and less than 27")
                else:
                    break
            except ValueError:
                print("Please enter a number only between 2 adn 27")
        
        show_timings = []
        print("\nEnter show timings in 24-hour format (HH:MM). Press Enter when finished.")

        while True:
            timing = input(f"Enter timing {len(show_timings)+1} (or press Enter to finish): ").strip()
            
            if not timing:
                if len(show_timings) == 0:
                    print("At least one show timing is required!")
                    continue
                break
                
            if not self._validate_time_format(timing):
                print("Invalid time format. Please use HH:MM (24-hour format)")
                continue
                
            if timing in show_timings:
                print("This timing already exists!")
                continue
                
            new_time = datetime.strptime(timing, '%H:%M')
            
            if show_timings:
                last_time = datetime.strptime(show_timings[-1], '%H:%M')
                if new_time <= last_time:
                    print("New timing must be after the previous one!")
                    continue
            
            show_timings.append(timing)
        
        timings_str = ';'.join(show_timings)
        
        with open(self.screens_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                screen_id,
                rows,
                cols,
                datetime.now().strftime('%Y-%m-%d'),
                'Active',
                timings_str
            ])
        
        self._init_screen_seating(screen_id, rows, cols, show_timings)
        self.theatre.save_hall_data() 
        
        print(f"\nScreen {screen_id} added successfully with {rows}x{cols} seating")
        print(f"Show timings: {', '.join(show_timings)}")


    def remove_screen(self):
        print("\n--- Remove Screen ---")
        self.view_screens()
        
        available_screens = []
        if os.path.exists(self.screens_file):
            with open(self.screens_file, 'r') as f:
                reader = csv.DictReader(f)
                available_screens = [row['ScreenID'] for row in reader if row]
        
        if not available_screens:
            print("No screens available to remove.")
            return
        
        while True:
            screen_id = input("Enter screen ID to remove (or 'q' to cancel): ").strip().upper()
            
            if screen_id.lower() == 'q':
                print("Operation cancelled.")
                return
            
            if screen_id not in available_screens:
                print(f"Invalid screen ID. Please choose from: {', '.join(available_screens)}")
                continue
            
            break
        
        confirm = input(f"WARNING: This will permanently remove screen {screen_id} and all its data. Continue? (y/n): ").lower()
        if confirm != 'y':
            print("Screen removal cancelled.")
            return
        
        try:
            refunded_bookings = []
            
            screens = []
            with open(self.screens_file, 'r') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for row in reader:
                    if row['ScreenID'] == screen_id:
                        row['Status'] = 'Inactive'
                        row['LastMaintenance'] = datetime.now().strftime('%Y-%m-%d')
                    screens.append(row)
            
            with open(self.screens_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(screens)
            
            movies = []
            if os.path.exists(self.movies_file):
                with open(self.movies_file, 'r') as f:
                    reader = csv.DictReader(f)
                    fieldnames = reader.fieldnames
                    for row in reader:
                        if row['ScreenID'] == screen_id:
                            row['IsActive'] = 'No'
                        movies.append(row)
                
                with open(self.movies_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(movies)
            
            if screen_id in self.theatre.hall_data:
                del self.theatre.hall_data[screen_id]
                self.theatre.save_hall_data()
            
            self.theatre.movie_list = {k:v for k,v in self.theatre.movie_list.items() if v['screen_id'] != screen_id}
            
            if screen_id in self.theatre.screens:
                del self.theatre.screens[screen_id]
            
            print(f"\nScreen {screen_id} and all the data realted to it have been removed successfully.")
        
        except Exception as e:
            print(f"\nError removing screen: {str(e)}")


    def _init_screen_seating(self, screen_id, rows, cols, timings):
        available_rows = [chr(65 + i) for i in range(rows)]
        available_cols = [str(i) for i in range(cols)]
        
        if screen_id not in self.theatre.hall_data:
            self.theatre.hall_data[screen_id] = {
                'dimensions': {'rows': rows, 'cols': cols},
                'seating': {}
            }
        
        for time in timings:
            alpha_dict = {row: [0]*cols for row in available_rows}
            booked_seats = {}
            
            initial_booked = 0
            for row in alpha_dict.values():
                initial_booked += row.count('X')
            
            self.theatre.hall_data[screen_id]['seating'][time] = {
                'alpha_dict': alpha_dict,
                'booked_seats': booked_seats,
                'ticket_count': rows * cols - initial_booked,
                'available_rows': available_rows,
                'available_cols': available_cols
            }

    def view_screens(self, show_all=False):
        print("\n--- Theatre Screens ---")
        if show_all:
            print("[Showing ALL screens including inactive]\n")
        else:
            print("[Showing only ACTIVE screens]\n")
        
        screens = []
        try:
            if os.path.exists(self.screens_file):
                with open(self.screens_file, 'r') as f:
                    reader = csv.DictReader(f)
                    if reader.fieldnames:
                        screens = [
                            row for row in reader 
                            if row and (show_all or row.get('Status', '').lower() == 'active')
                        ]
            
            active_movies = {}
            if os.path.exists(self.movies_file):
                with open(self.movies_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get('IsActive', '').lower() == 'yes':
                            active_movies[row['ScreenID']] = row['Title']
        
        except Exception as e:
            print(f"Error reading data: {str(e)}")
            return
        
        if not screens:
            print("No screens available" if show_all else "No active screens available")
            return
        
        headers = [
            'Screen', 'Rows', 'Cols', 'Status', 
            'Movie', 'Last Maintenance', 'Show Times'
        ]
        col_widths = [8, 5, 5, 12, 20, 15, 60]
        
        header_row = " | ".join(
            f"{header:<{width}}" 
            for header, width in zip(headers, col_widths)
        )
        print(header_row)
        print("-" * (sum(col_widths) + len(headers)*3 - 1))
        
        for screen in screens:
            screen_id = screen.get('ScreenID', 'N/A')
            rows = screen.get('Rows', '?')
            cols = screen.get('Columns', '?')
            status = screen.get('Status', 'Unknown')
            movie = active_movies.get(screen_id, 'None')
            
            maintenance_date = screen.get('LastMaintenance', '')
            if maintenance_date:
                try:
                    date_obj = datetime.strptime(maintenance_date, '%Y-%m-%d')
                    maintenance_date = date_obj.strftime('%d-%m-%Y')
                except ValueError:
                    pass
            
            timings = screen.get('Timings', '')
            if not timings and 'ShowTimes' in screen:
                timings = screen['ShowTimes']
            if timings:
                timings = ', '.join(timings.split(';'))
            
            print(
                f"{screen_id:<8} | {rows:<5} | {cols:<5} | "
                f"{status:<12} | {movie[:19]:<20} | "
                f"{maintenance_date:<15} | {timings[:50]:<50}"
            )

    
    def display_seats(self):
        print("\nAvailable Movies:")
        for key, val in self.theatre.movie_list.items():
            print(f"{key}. {val['name']} (Screen: {val['screen_id']})")

        try:
            movie_id = int(input("Enter the serial number of the movie to view its seating: "))
            if movie_id not in self.theatre.movie_list:
                print("Invalid movie number.")
                return

            movie_data = self.theatre.movie_list[movie_id]
            screen_id = movie_data['screen_id']
            
            if screen_id not in self.theatre.hall_data:
                print(f"Screen {screen_id} not found.")
                return

            print(f"\n--- Seating for '{movie_data['name']}' ---")
            
            for show_time, timing_data in self.theatre.hall_data[screen_id]['seating'].items():
                print(f"\n{show_time} Show:")
                print("  ", " ".join(f"{col:>2}" for col in timing_data['available_cols']))
                
                for row_label in timing_data['available_rows']:
                    seats = timing_data['alpha_dict'][row_label]
                    print(f"{row_label}:", " ".join(' X' if seat == 'X' else ' .' for seat in seats))

        except ValueError:
            print("Please enter a valid number.")


    def add_movie(self):
        print("\n--- Add New Movie ---")
        
        while True:
            title = input("Movie title: ").strip()
            if not title:
                print("Error: Movie title cannot be empty.")
                continue
            
            if len(title) > 100:
                print("Error: Title too long (max 100 characters).")
                continue
                
            if os.path.exists(self.movies_file):
                with open(self.movies_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['Title'].lower() == title.lower() and row['IsActive'].lower() == 'yes':
                            print(f"Error: Active movie '{row['Title']}' already exists (ID: {row['MovieID']}).")
                            print("Please deactivate the existing movie first or choose a different title.")
                            return
            break
        
        while True:
            price_input = input("Ticket price: ").strip()
            try:
                price = float(price_input)
                if price <= 0:
                    print("Error: Price must be greater than 0.")
                    continue
                if price > 1000:
                    print("Warning: Price seems unusually high. Confirm? (y/n): ")
                    if input().lower() != 'y':
                        continue
                break
            except ValueError:
                print("Error: Please enter a valid number for the price.")
        
        active_screens = []
        if os.path.exists(self.screens_file):
            with open(self.screens_file, 'r') as f:
                reader = csv.DictReader(f)
                active_screens = [
                    row['ScreenID'] for row in reader 
                    if row and row.get('Status', '').lower() == 'active'
                ]
        
        if not active_screens:
            print("Error: No active screens available to assign movie.")
            return
        
        while True:
            self.view_screens()
            screen_id = input("Assign to screen ID: ").strip().upper()
            
            if not screen_id:
                print("Error: Screen ID cannot be empty.")
                continue
                
            if screen_id not in active_screens:
                print(f"Error: Invalid screen ID. Please choose from active screens: {', '.join(active_screens)}")
                continue
                
            with open(self.screens_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['ScreenID'] == screen_id and row.get('Status', '').lower() == 'maintenance':
                        print(f"Error: Screen {screen_id} is under maintenance and cannot be assigned movies.")
                        return
            break
        
        updated_movies = []
        if os.path.exists(self.movies_file):
            with open(self.movies_file, 'r') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for row in reader:
                    if row['ScreenID'] == screen_id and row['IsActive'].lower() == 'yes':
                        row['IsActive'] = 'No'
                        print(f"Deactivated previous movie: {row['Title']} (ID: {row['MovieID']})")
                    updated_movies.append(row)
            
            with open(self.movies_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(updated_movies)
        
        new_id = 1
        if updated_movies:
            existing_ids = [int(row['MovieID']) for row in updated_movies if row['MovieID'].isdigit()]
            new_id = max(existing_ids) + 1 if existing_ids else 1
        
        try:
            with open(self.movies_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    new_id,
                    title,
                    screen_id,
                    price,
                    'Yes'
                ])
            
            self.theatre.movie_list[new_id] = {
                'name': title,
                'price': price,
                'screen_id': screen_id
            }
            
            print(f"\nSuccessfully added movie:")
            print(f"ID: {new_id}")
            print(f"Title: {title}")
            print(f"Screen: {screen_id}")
            print(f"Price: ₹{price:.2f}")
            
        except Exception as e:
            print(f"\nError saving movie: {str(e)}")
            print("Please try again or check system permissions.")


    def remove_movie(self):
        print("\n--- Remove Movie ---")
        self.list_movies()
        
        try:
            movie_id = int(input("Enter Movie ID to remove (or 0 to cancel): "))
            if movie_id == 0:
                print("Operation cancelled.")
                return
                
            movie_exists = False
            movie_active = False
            screen_id = None
            
            with open(self.movies_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if int(row['MovieID']) == movie_id:
                        movie_exists = True
                        if row.get('IsActive', '').lower() == 'yes':
                            movie_active = True
                            screen_id = row['ScreenID']
                        break
            
            if not movie_exists:
                print(f"Error: Movie ID {movie_id} not found.")
                return
                
            if not movie_active:
                print(f"Error: Movie ID {movie_id} is already inactive.")
                return
                
            screen_active = False
            with open(self.screens_file, 'r') as f:
                screen_reader = csv.DictReader(f)
                for screen in screen_reader:
                    if screen['ScreenID'] == screen_id and screen.get('Status', '').lower() == 'active':
                        screen_active = True
                        break
            
            if not screen_active:
                print(f"Error: Screen {screen_id} for this movie is not active.")
                return
                
            confirm = input(f"Are you sure you want to deactivate Movie ID {movie_id}? (y/n): ").lower()
            if confirm != 'y':
                print("Operation cancelled.")
                return
                
            movies = []
            with open(self.movies_file, 'r') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for row in reader:
                    if int(row['MovieID']) == movie_id:
                        row['IsActive'] = 'No'
                        print(f"Deactivating: {row['Title']} (Screen: {row['ScreenID']})")
                    movies.append(row)
            
            with open(self.movies_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(movies)
            
            if movie_id in self.theatre.movie_list:
                del self.theatre.movie_list[movie_id]
                print(f"Movie ID {movie_id} has been deactivated from memory.")
            else:
                print(f"Note: Movie ID {movie_id} was not found in the current session's active movies.")
                
        except ValueError:
            print("Invalid input. Please enter a numeric Movie ID.")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

    def list_movies(self):
        print("\n--- Current Movies ---")
        try:
            if not os.path.exists(self.movies_file):
                print("No movies found")
                return
                
            with open(self.movies_file, 'r') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    print("No movies available")
                    return
                    
                has_movies = False
                for row in reader:
                    if row and row.get('IsActive', 'yes').lower() == 'yes':
                        print(f"\nID: {row.get('MovieID', 'N/A')} | {row.get('Title', 'Untitled')}")
                        print(f"Screen: {row.get('ScreenID', 'N/A')} | Price: ₹{row.get('Price', '0')}")
                        has_movies = True
                        
                if not has_movies:
                    print("No active movies found")
                    
        except Exception as e:
            print(f"Error listing movies: {str(e)}")

    def screen_maintenance(self):
        self.view_screens()
        
        available_screens = []
        if os.path.exists(self.screens_file):
            with open(self.screens_file, 'r') as f:
                reader = csv.DictReader(f)
                available_screens = [row['ScreenID'] for row in reader if row]
        
        if not available_screens:
            print("No screens available for maintenance.")
            return
        
        while True:
            screen_id = input("Enter screen ID for maintenance (or 'q' to quit): ").strip()
            
            if screen_id.lower() == 'q':
                return
            
            if screen_id not in available_screens:
                print(f"Invalid screen ID. Please choose from: {', '.join(available_screens)}")
                continue
            
            break
        
        screens = []
        status_changed = False
        new_status = None
        
        with open(self.screens_file, 'r') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for screen in reader:
                if screen['ScreenID'] == screen_id:
                    if screen['Status'].lower() == 'active':
                        screen['Status'] = 'Maintenance'
                        screen['LastMaintenance'] = datetime.now().strftime('%Y-%m-%d')
                        new_status = 'Maintenance'
                    else:
                        screen['Status'] = 'Active'
                        new_status = 'Active'
                    status_changed = True
                screens.append(screen)
        
        if status_changed:
            # Update screens.csv
            with open(self.screens_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(screens)
            
            # Update movies.csv if putting screen into maintenance
            if new_status == 'Maintenance':
                movies = []
                movies_updated = False
                if os.path.exists(self.movies_file):
                    with open(self.movies_file, 'r') as f:
                        reader = csv.DictReader(f)
                        fieldnames = reader.fieldnames
                        for row in reader:
                            if row['ScreenID'] == screen_id and row['IsActive'].lower() == 'yes':
                                row['IsActive'] = 'No'
                                print(f"Deactivating movie: {row['Title']} (MovieID: {row['MovieID']})")
                                movies_updated = True
                            movies.append(row)
                    
                    if movies_updated:
                        with open(self.movies_file, 'w', newline='') as f:
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(movies)
                        
                        # Update theatre.movie_list in memory
                        movies_to_remove = [
                            movie_id for movie_id, movie_data in self.theatre.movie_list.items() 
                            if movie_data['screen_id'] == screen_id
                        ]
                        for movie_id in movies_to_remove:
                            del self.theatre.movie_list[movie_id]
            
            print(f"\nScreen {screen_id} status changed to {new_status}.")
            if new_status == 'Maintenance':
                print("All movies on this screen have been deactivated.")
        else:
            print(f"Screen {screen_id} not found or status unchanged.")


    def reset_seats(self):
        print("\n=== SEAT RESET OPTIONS ===")
        print("1. Reset seats for specific show timing")
        print("2. Reset all timings for a screen")
        print("3. Reset all screens (full reset)")
        print("4. Cancel")
        
        while True:
            choice = input("Enter your choice (1-4): ")
            
            if choice == '1':
                self._reset_specific_timing()
                break
            elif choice == '2':
                self._reset_all_timings_for_screen()
                break
            elif choice == '3':
                self._reset_all_screens()
                break
            elif choice == '4':
                print("Seat reset cancelled.")
                break
            else:
                print("Invalid choice. Please try again.")

    def _reset_specific_timing(self):
        """Reset seats for a specific show timing"""
        print("\nAvailable Screens and Movies:")
        
        screens = self._get_active_screens()
        screen_movies = {}
        
        for movie_id, movie_data in self.theatre.movie_list.items():
            screen_id = movie_data['screen_id']
            if screen_id in screens:
                screen_movies[screen_id] = movie_data['name']
        
        for i, screen_id in enumerate(screens, 1):
            movie_name = screen_movies.get(screen_id, "No movie assigned")
            print(f"{i}. Screen {screen_id} - {movie_name}")
        
        screen_idx = self._get_valid_input("\nSelect screen: ", 1, len(screens)) - 1
        screen_id = screens[screen_idx]
        
        print("\nAvailable Show Timings:")
        for i, timing in enumerate(self.theatre.movie_timings, 1):
            print(f"{i}. {timing}")
        
        timing_idx = self._get_valid_input("Select timing: ", 1, len(self.theatre.movie_timings)) - 1
        timing = self.theatre.movie_timings[timing_idx]
        
        confirm = input(f"\nConfirm reset seats for Screen {screen_id} at {timing}? (y/n): ").lower()
        if confirm == 'y':
            self._do_reset(screen_id, timing)
            self.theatre.save_hall_data()
            print(f"Seats reset for Screen {screen_id} at {timing}")
        else:
            print("Reset cancelled.")

    def _reset_all_timings_for_screen(self):
        """Reset all timings for a selected screen"""
        print("\nAvailable Screens and Movies:")
        
        screens = self._get_active_screens()
        screen_movies = {}
        
        for movie_id, movie_data in self.theatre.movie_list.items():
            screen_id = movie_data['screen_id']
            if screen_id in screens:
                screen_movies[screen_id] = movie_data['name']
        
        for i, screen_id in enumerate(screens, 1):
            movie_name = screen_movies.get(screen_id, "No movie assigned")
            print(f"{i}. Screen {screen_id} - {movie_name}")
        
        screen_idx = self._get_valid_input("\nSelect screen: ", 1, len(screens)) - 1
        screen_id = screens[screen_idx]
        
        current_movie = screen_movies.get(screen_id, "no current movie")
        
        confirm = input(f"\nConfirm reset ALL timings for Screen {screen_id} ({current_movie})? (y/n): ").lower()
        if confirm == 'y':
            for timing in self.theatre.movie_timings:
                self._do_reset(screen_id, timing)
            self.theatre.save_hall_data()
            print(f"All timings reset for Screen {screen_id} ({current_movie})")
        else:
            print("Reset cancelled.")

    def _reset_all_screens(self):
        """Reset all screens and all timings"""
        confirm = input("\nWARNING: This will reset ALL seats in ALL screens. Continue? (y/n): ").lower()
        if confirm == 'y':
            for screen_id in self._get_active_screens():
                for timing in self.theatre.movie_timings:
                    self._do_reset(screen_id, timing)
            self.theatre.save_hall_data()
            print("All screens and timings have been reset.")
        else:
            print("Full reset cancelled.")

    def _do_reset(self, screen_id, timing):
        """Actual seat reset implementation"""
        if screen_id in self.theatre.hall_data and timing in self.theatre.hall_data[screen_id]['seating']:
            rows = self.theatre.hall_data[screen_id]['dimensions']['rows']
            cols = self.theatre.hall_data[screen_id]['dimensions']['cols']
            
            timing_data = self.theatre.hall_data[screen_id]['seating'][timing]
            timing_data['alpha_dict'] = {chr(65 + i): [0]*cols for i in range(rows)}
            timing_data['booked_seats'] = {}
            timing_data['ticket_count'] = rows * cols

    def _get_active_screens(self):
        """Get list of active screens"""
        screens = []
        if os.path.exists(self.screens_file):
            with open(self.screens_file, 'r') as f:
                reader = csv.DictReader(f)
                screens = [row['ScreenID'] for row in reader if row.get('Status', '').lower() == 'active']
        return screens

    def _get_valid_input(self, prompt, min_val, max_val):
        """Get validated numeric input"""
        while True:
            try:
                val = int(input(prompt))
                if min_val <= val <= max_val:
                    return val
                print(f"Please enter a number between {min_val} and {max_val}")
            except ValueError:
                print("Please enter a valid number.")


    def admin_menu(self):
        while True:
            print("\n=== ADMIN MENU ===")
            print("1. Add New Screen")
            print("2. Remove Existing Screen")
            print("3. View All Screens")
            print("4. Display Seats")
            print("5. Add New Movie")
            print("6. Remove Movie")
            print("7. List All Movies")
            print("8. Screen Maintenance")
            print("9. Reset Seats")
            print("10. Exit Admin Panel")
            
            choice = input("Enter your choice (1-10): ")
            
            if choice == '1':
                self.add_screen()
            elif choice == '2':
                self.remove_screen()
            elif choice == '3':
                self.view_screens()
            elif choice == '4':
                self.display_seats()
            elif choice == '5':
                self.add_movie()
            elif choice == '6':
                self.remove_movie()
            elif choice == '7':
                self.list_movies()
            elif choice == '8':
                self.screen_maintenance()
            elif choice == '9':
                self.reset_seats()
            elif choice == '10':
                print("Exiting admin panel...")
                break
            else:
                print("Invalid choice. Please try again.")