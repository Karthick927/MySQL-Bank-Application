import mysql.connector
import random
import sys
import getpass
from datetime import datetime

# --- Configuration (Update these credentials to match your MySQL setup) ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'YOUR_MYSQL_PASSWORD',
    'database': 'bank_db' 
}


# ------------------------------------------------------------------------

class Bank:
    """A console-based bank application using MySQL for data persistence."""

    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database

        print("Initializing Bank System...")
        self._ensure_database_and_table_exists()
        print("Initialization complete. Ready for transactions.")

    def _get_connection(self):
        """Establishes a connection to the database."""
        try:
            conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database  # Use the specific database name
            )
            return conn
        except mysql.connector.Error as err:
            print("-" * 40)
            print(f"Database Connection Error: {err.msg}")
            print("Please check your MySQL server status and DB_CONFIG settings.")
            print("-" * 40)
            return None

    def _ensure_database_and_table_exists(self):
        """Creates the database and the necessary table if they do not exist."""
        # Connect without specifying the database first
        try:
            conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            cursor = conn.cursor()

            # Create the database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            conn.database = self.database

            # Create the Accounts table
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS Accounts (
                acc_no BIGINT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                account_type VARCHAR(20) NOT NULL,
                balance DECIMAL(10, 2) NOT NULL DEFAULT 0.00
            );
            """
            cursor.execute(create_table_query)
            conn.commit()
            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            print(f"Setup Failed: {err.msg}")
            sys.exit(1) 

    def create_account(self):
        """CREATE operation: Adds a new account to the database."""
        name = input("Enter customer name: ")
        account_type = input("Enter account type (savings/current): ").lower()

        if account_type not in ["savings", "current", "saving"]:
            print(f"ERROR: Please enter either 'savings' or 'current', not '{account_type}'.")
            return

        try:
            initial_amount = float(input("Enter the initial amount to deposit (min 100): "))
            if initial_amount < 100:
                print("Minimum initial deposit is 100.")
                return
        except ValueError:
            print("Invalid amount. Please enter a number.")
            return

        conn = self._get_connection()
        if conn is None: return

        try:
            cursor = conn.cursor()
            # Generate a unique 10-digit account number (simple collision handling)
            new_acc_no = random.randint(1000000000, 9999999999)

            insert_query = """
            INSERT INTO Accounts (acc_no, name, account_type, balance)
            VALUES (%s, %s, %s, %s)
            """
            values = (new_acc_no, name, account_type, initial_amount)

            cursor.execute(insert_query, values)
            conn.commit()
            print("\n" + "=" * 25)
            print(f"Account created successfully for {name}!")
            print(f"Your Account Number: {new_acc_no}")
            print("=" * 25)

        except mysql.connector.Error as err:
            print(f"SQL Error: {err.msg}")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def deposit_money(self):
        """UPDATE operation: Adds funds to an existing account."""
        try:
            acc_no = int(input("Enter your account number: "))
            amount = float(input("Enter amount to deposit: "))
            if amount <= 0:
                print("Deposit amount must be positive.")
                return
        except ValueError:
            print("Invalid input. Please enter numbers.")
            return

        conn = self._get_connection()
        if conn is None: return

        try:
            cursor = conn.cursor()

            # Check if account exists and get current balance
            cursor.execute("SELECT balance FROM Accounts WHERE acc_no = %s", (acc_no,))
            result = cursor.fetchone()

            if result is None:
                print("ERROR: Account number not found.")
                return

            # Perform the update
            update_query = "UPDATE Accounts SET balance = balance + %s WHERE acc_no = %s"
            cursor.execute(update_query, (amount, acc_no))
            conn.commit()

            # Fetch the new balance
            cursor.execute("SELECT balance FROM Accounts WHERE acc_no = %s", (acc_no,))
            new_balance = cursor.fetchone()[0]

            print(f"\nDEPOSIT SUCCESSFUL! Amount: {amount:.2f}")
            print(f"New Balance: {new_balance:.2f}")

        except mysql.connector.Error as err:
            print(f"SQL Error: {err.msg}")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def withdraw_money(self):
        """UPDATE operation: Deducts funds from an existing account with validation."""
        try:
            acc_no = int(input("Enter your account number: "))
            amount = float(input("Enter amount to withdraw: "))
            if amount <= 0:
                print("Withdrawal amount must be positive.")
                return
        except ValueError:
            print("Invalid input. Please enter numbers.")
            return

        conn = self._get_connection()
        if conn is None: return

        try:
            cursor = conn.cursor()

            # 1. Check if account exists and if balance is sufficient
            cursor.execute("SELECT balance, name FROM Accounts WHERE acc_no = %s", (acc_no,))
            result = cursor.fetchone()

            if result is None:
                print("ERROR: Account number not found.")
                return

            current_balance = result[0]

            if current_balance < amount:
                print(f"INSUFFICIENT FUNDS. Current Balance: {current_balance:.2f}")
                return

            # 2. Perform the update (Withdrawal)
            update_query = "UPDATE Accounts SET balance = balance - %s WHERE acc_no = %s"
            cursor.execute(update_query, (amount, acc_no))
            conn.commit()

            # 3. Fetch the new balance
            cursor.execute("SELECT balance FROM Accounts WHERE acc_no = %s", (acc_no,))
            new_balance = cursor.fetchone()[0]

            print(f"\nWITHDRAWAL SUCCESSFUL! Amount: {amount:.2f}")
            print(f"Remaining Balance: {new_balance:.2f}")

        except mysql.connector.Error as err:
            print(f"SQL Error: {err.msg}")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def check_balance(self):
        """READ operation: Retrieves and displays the account balance."""
        try:
            acc_no = int(input("Enter your account number: "))
        except ValueError:
            print("Invalid account number.")
            return

        conn = self._get_connection()
        if conn is None: return

        try:
            cursor = conn.cursor()

            # SELECT query to retrieve specific account info
            cursor.execute("SELECT name, balance FROM Accounts WHERE acc_no = %s", (acc_no,))
            result = cursor.fetchone()

            if result is None:
                print("ERROR: Account number not found.")
                return

            name, balance = result
            print("\n" + "=" * 25)
            print(f"Account Holder: {name}")
            print(f"Current Balance: {balance:.2f}")
            print("=" * 25)

        except mysql.connector.Error as err:
            print(f"SQL Error: {err.msg}")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def view_all_accounts(self):
        """READ operation: Retrieves and displays all accounts."""
        conn = self._get_connection()
        if conn is None: return

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT acc_no, name, account_type, balance FROM Accounts")
            accounts = cursor.fetchall()

            if not accounts:
                print("\nNo accounts found in the database.")
                return

            print("\n--- All Bank Accounts ---")
            print(f"{'Account No':<15} {'Name':<20} {'Type':<10} {'Balance':>10}")
            print("-" * 55)
            for acc in accounts:
                acc_no, name, acc_type, balance = acc
                print(f"{acc_no:<15} {name:<20} {acc_type:<10} {balance:>10.2f}")
            print("-" * 55)

        except mysql.connector.Error as err:
            print(f"SQL Error: {err.msg}")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def main(self):
        """Main application loop."""
        print("=" * 40)
        print("\tWELCOME TO GEMINI BANKING SERVICE")
        print("=" * 40)

        while True:
            print("\n--- Menu ---")
            print("1. Create a new account")
            print("2. Deposit Money")
            print("3. Withdraw Money")
            print("4. Check Balance")
            print("5. View all accounts")
            print("6. Exit")
            print("=" * 15)

            try:
                choice = input("Enter your choice (1-6): ")

                if choice == '1':
                    self.create_account()
                elif choice == '2':
                    self.deposit_money()
                elif choice == '3':
                    self.withdraw_money()
                elif choice == '4':
                    self.check_balance()
                elif choice == '5':
                    self.view_all_accounts()
                elif choice == '6':
                    print("Exiting... Thank you for using Banking.")
                    break
                else:
                    print(f"ERROR: Please enter a valid choice (1-6), not '{choice}'.")

            except Exception as e:
                print(f"An unexpected error occurred: {e}")


if __name__ == '__main__':
    # Get the MySQL password securely at runtime
    db_password = getpass.getpass("Enter your MySQL Root/User Password: ")

    # Update the config with the runtime password
    DB_CONFIG['password'] = db_password

  
    app = Bank(**DB_CONFIG)
    app.main()
