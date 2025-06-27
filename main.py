import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.login import Login

def main():
    print("Welcome to Theater Booking System")
    login_system = Login()
    
    while True:
        print("\n1. Sign-up\n2. Sign-in\n3. Exit")
        choice = input("Enter choice: ")
        
        if choice == '1':
            print(login_system.sign_up())
        elif choice == '2':
            login_system.sign_in()
        elif choice == '3':
            print("Thank you for using our system!")
            break
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()

# screen(dynamic), payment(wallet), admin