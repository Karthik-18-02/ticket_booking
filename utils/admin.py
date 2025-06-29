import csv
import os
from datetime import datetime

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
                        if not all(h in headers for h in ['ScreenID', 'Rows', 'Columns', 'Status']):
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
                    writer.writerow(['ScreenID', 'Rows', 'Columns', 'LastMaintenance', 'Status'])
                    writer.writerow(['SC1', 10, 10, datetime.now().strftime('%Y-%m-%d'), 'Active'])
        
        except Exception as e:
            print(f"Critical error initializing screens file: {str(e)}")
            raise
        
        if not os.path.exists(self.movies_file):
            with open(self.movies_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['MovieID', 'Title', 'ScreenID', 'Price', 'IsActive'])

    def add_screen(self):
        print("\n--- Add New Screen ---")
        
        screen_id = input("Enter screen ID: ").strip()
        rows = int(input("Number of rows: "))
        cols = int(input("Number of columns per row: "))
        
        with open(self.screens_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                screen_id,
                rows,
                cols,
                datetime.now().strftime('%Y-%m-%d'),
                'Active'
            ])
        
        self.theatre.seats(rows) 
        
        print(f"\nScreen {screen_id} added successfully with {rows}x{cols} seating")


    def view_screens(self):
        print("\n--- Theatre Screens ---")
        screens = []
        
        try:
            # Load screens data
            if os.path.exists(self.screens_file):
                with open(self.screens_file, 'r') as f:
                    reader = csv.DictReader(f)
                    if reader.fieldnames:
                        screens = [row for row in reader if row]
            
            # Load movies data to find which movies are active on each screen
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
            print("No screens available")
            return
            
        print(f"\n{'Screen':<8} | {'Rows':<5} | {'Columns':<5} | {'Status':<12} | {'Movie':<20} | {'Last Maintenance'}")
        print("-"*70)
        
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
            
            print(f"{screen_id:<8} | {rows:<5} | {cols:<5} | {status:<12} | {movie[:19]:<20} | {maintenance_date}")


    def add_movie(self):
        print("\n--- Add New Movie ---")
        
        title = input("Movie title: ")
        price = float(input("Ticket price: "))
        
        self.view_screens()
        screen_id = input("Assign to screen ID: ")
        
        updated_movies = []
        if os.path.exists(self.movies_file):
            with open(self.movies_file, 'r') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for row in reader:
                    if row['ScreenID'] == screen_id and row['IsActive'].lower() == 'yes':
                        row['IsActive'] = 'No'
                        print(f"Deactivated previous movie: {row['Title']}")
                    updated_movies.append(row)
            
            with open(self.movies_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(updated_movies)
        
        new_id = len(updated_movies) + 1 if updated_movies else 1
        
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
        
        print(f"\nMovie '{title}' added successfully to Screen {screen_id}!")


    def remove_movie(self):
        print("\n--- Remove Movie ---")
        self.list_movies()
        
        movie_id = int(input("Enter Movie ID to remove: "))
        
        movies = []
        with open(self.movies_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if int(row['MovieID']) == movie_id:
                    row['IsActive'] = 'No'
                movies.append(row)
        
        with open(self.movies_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
            writer.writeheader()
            writer.writerows(movies)
        
        if movie_id in self.theatre.movie_list:
            del self.theatre.movie_list[movie_id]
        
        print(f"Movie ID {movie_id} has been deactivated.")

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
        screen_id = input("Enter screen ID for maintenance: ")
        
        screens = []
        with open(self.screens_file, 'r') as f:
            reader = csv.DictReader(f)
            for screen in reader:
                if screen['ScreenID'] == screen_id:
                    screen['Status'] = 'Maintenance'
                    screen['LastMaintenance'] = datetime.now().strftime('%Y-%m-%d')
                screens.append(screen)
        
        with open(self.screens_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
            writer.writeheader()
            writer.writerows(screens)
        
        print(f"Screen {screen_id} marked for maintenance.")


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
        
        # Get active screens and their movies
        screens = self._get_active_screens()
        screen_movies = {}
        
        # Build screen-movie mapping
        for movie_id, movie_data in self.theatre.movie_list.items():
            screen_id = movie_data['screen_id']
            if screen_id in screens:
                screen_movies[screen_id] = movie_data['name']
        
        # Display screens with their movies
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
        
        # Get active screens and their movies
        screens = self._get_active_screens()
        screen_movies = {}
        
        # Build screen-movie mapping
        for movie_id, movie_data in self.theatre.movie_list.items():
            screen_id = movie_data['screen_id']
            if screen_id in screens:
                screen_movies[screen_id] = movie_data['name']
        
        # Display screens with their movies
        for i, screen_id in enumerate(screens, 1):
            movie_name = screen_movies.get(screen_id, "No movie assigned")
            print(f"{i}. Screen {screen_id} - {movie_name}")
        
        screen_idx = self._get_valid_input("\nSelect screen: ", 1, len(screens)) - 1
        screen_id = screens[screen_idx]
        
        # Get the movie name for the confirmation message
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
            self.theatre.save_hall_data()  # Save the changes
            print("All screens and timings have been reset.")
        else:
            print("Full reset cancelled.")

    def _do_reset(self, screen_id, timing):
        """Actual seat reset implementation"""
        if screen_id in self.theatre.hall_data and timing in self.theatre.hall_data[screen_id]['seating']:
            # Get screen dimensions
            rows = self.theatre.hall_data[screen_id]['dimensions']['rows']
            cols = self.theatre.hall_data[screen_id]['dimensions']['cols']
            
            # Reset the seating data
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
            print("2. View All Screens")
            print("3. Add New Movie")
            print("4. Remove Movie")
            print("5. List All Movies")
            print("6. Screen Maintenance")
            print("7. Reset Seats")
            print("8. Exit Admin Panel")
            
            choice = input("Enter your choice (1-8): ")
            
            if choice == '1':
                self.add_screen()
            elif choice == '2':
                self.view_screens()
            elif choice == '3':
                self.add_movie()
            elif choice == '4':
                self.remove_movie()
            elif choice == '5':
                self.list_movies()
            elif choice == '6':
                self.screen_maintenance()
            elif choice == '7':
                self.reset_seats()
            elif choice == '8':
                print("Exiting admin panel...")
                break
            else:
                print("Invalid choice. Please try again.")