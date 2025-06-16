class Theatre:
    def seats(self, n):
        self.n = n
        self.col = [i for i in range(n)]
        self.alpha_dict = {}
        self.booked_seats = {}
        alpha_chr = 65

        self.ticket_count = n*n
        self.available_rows = [chr(alpha_chr + i) for i in range(n)]
        self.available_cols = [str(i) for i in range(n)]

        for _ in range(n):
            self.alpha_dict[chr(alpha_chr)] = [0 for _ in range(n)]
            alpha_chr += 1
        
        return 
    
    def display_seats(self):
        print("   ", self.col)
        for key, val in self.alpha_dict.items():
            print(key, ":", val)

        return
    
    def book_ticket(self, movie='OK JAANU'):
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

            self.booked_seats[seat_num] = [name, movie, seat_num]
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
        


k = Theatre()
k.seats(3)

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
        k.book_ticket()
    elif choice == '2':
        k.display_seats()
    elif choice == '3':
        k.cancel_ticket()
    elif choice == '4':
        print(k.display_ticket_details())
    elif choice == '5':
        print(k.check_remaining_seats())
    elif choice == '6':
        print(k.display_booked_details())
    elif choice == '7':
        print("Exiting the system. Thank you!")
        break
    else:
        print("Invalid choice. Please enter a number between 1 and 7.")
