from tkinter import *
from tkinter import messagebox
from random import choice, randint, shuffle
import pyperclip
import os
from cryptography.fernet import Fernet

# Import our database model and session from database.py
from database import Password, session

# Import authentication functions from auth.py
from auth import set_master_password, verify_master_password, master_password_exists

# ---------------------------- ENCRYPTION SETUP ------------------------------- #

# The file where the Fernet encryption key is stored locally
KEY_FILE = "secret.key"

def load_or_create_key():
    # If a key already exists, load it - we must use the same key every time
    # A different key would make all previously saved passwords unreadable
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    else:
        # First run - generate a new random key and save it
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        return key

# Load the key once at startup and create the Fernet instance
KEY = load_or_create_key()
fernet = Fernet(KEY)

def encrypt(password):
    # encode() converts string to bytes, Fernet encrypts it
    # decode() converts the result back to string for database storage
    return fernet.encrypt(password.encode()).decode()

def decrypt(token):
    # Reverse of encrypt - converts stored string back to readable password
    return fernet.decrypt(token.encode()).decode()

# ---------------------------- PASSWORD GENERATOR ------------------------------- #

def generate_password():
    letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
               'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
               'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
               'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    symbols = ['!', '#', '$', '%', '&', '(', ')', '*', '+']

    # Generate random counts of letters, symbols and numbers
    password_letters = [choice(letters) for _ in range(randint(8, 10))]
    password_symbols = [choice(symbols) for _ in range(randint(2, 4))]
    password_numbers = [choice(numbers) for _ in range(randint(2, 4))]

    # Combine all parts and shuffle so the order is unpredictable
    password_list = password_letters + password_symbols + password_numbers
    shuffle(password_list)

    password = "".join(password_list)

    # Display the generated password in the entry field
    pass_entry.delete(0, END)
    pass_entry.insert(0, password)

    # Copy to clipboard automatically for convenience
    pyperclip.copy(password)

# ---------------------------- SAVE PASSWORD ------------------------------- #

def save():
    website = website_entry.get()
    email = email_entry.get()
    password = pass_entry.get()

    # Validate that required fields are not empty before saving
    if len(website) == 0 or len(password) == 0:
        messagebox.showinfo(title="Oops", message="Please don't leave any fields empty")
    else:
        # Create a new database row with the password encrypted
        # We never store plain text passwords in the database
        new_entry = Password(
            website=website,
            email=email,
            password=encrypt(password)
        )
        # Add the new entry to the session and commit to save it permanently
        session.add(new_entry)
        session.commit()

        # Clear the fields and focus back to website entry for next entry
        website_entry.delete(0, 'end')
        pass_entry.delete(0, 'end')
        website_entry.focus()
        messagebox.showinfo(title="Success", message="Password saved successfully!")

# ---------------------------- FIND PASSWORD ------------------------------- #

def find_password():
    website = website_entry.get()

    # Query the database for the first entry matching the website name
    result = session.query(Password).filter_by(website=website).first()

    if result is None:
        messagebox.showinfo(title="Error", message="No details for the website exist")
    else:
        # Decrypt the password before displaying it to the user
        decrypted_password = decrypt(result.password)
        messagebox.showinfo(title=website, message=f"Email: {result.email}\nPassword: {decrypted_password}")

# ---------------------------- LOGIN SCREEN ------------------------------- #

def open_main_app():
    # Reveal the main window after successful authentication
    window.deiconify()

def login_screen():
    # Create a popup window for authentication
    login = Toplevel()
    login.title("Login")
    login.config(padx=30, pady=30)

    if master_password_exists():
        # Master password already set - ask user to enter it
        Label(login, text="Enter Master Password:").grid(row=0, column=0)
        password_entry = Entry(login, show="*", width=30)
        password_entry.grid(row=1, column=0, pady=5)

        def check_password():
            # verify_master_password() hashes the input and compares to stored hash
            if verify_master_password(password_entry.get()):
                login.destroy()
                open_main_app()
            else:
                messagebox.showerror("Error", "Wrong password!")

        Button(login, text="Login", command=check_password).grid(row=2, column=0, pady=5)

    else:
        # First run - no master password exists yet, ask user to create one
        Label(login, text="Create Master Password:").grid(row=0, column=0)
        password_entry = Entry(login, show="*", width=30)
        password_entry.grid(row=1, column=0, pady=5)

        def save_password():
            if len(password_entry.get()) < 6:
                messagebox.showwarning("Weak", "Password must be at least 6 characters")
            else:
                # Hash and store the master password securely using bcrypt
                set_master_password(password_entry.get())
                login.destroy()
                open_main_app()

        Button(login, text="Set Password", command=save_password).grid(row=2, column=0, pady=5)

# ---------------------------- UI SETUP ------------------------------- #

window = Tk()
window.title("Password Manager")
window.config(padx=50, pady=50)

# Hide the main window immediately - it will only show after successful login
window.withdraw()

canvas = Canvas(width=200, height=200)
logo_img = PhotoImage(file="logo.png")
canvas.create_image(100, 100, image=logo_img)
canvas.grid(row=0, column=1)

# Labels
website_label = Label(text="Website:")
website_label.grid(column=0, row=1)
email_label = Label(text="Email/Username:")
email_label.grid(column=0, row=2)
Pass_label = Label(text="Password:")
Pass_label.grid(column=0, row=3)

# Entry fields
website_entry = Entry(width=21)
website_entry.grid(column=1, row=1)
website_entry.focus()
email_entry = Entry(width=40)
email_entry.grid(column=1, row=2, columnspan=2)
email_entry.insert(0, "mymail@mail.com")
pass_entry = Entry(width=21)
pass_entry.grid(column=1, row=3)

# Buttons
pass_button = Button(text="Generate Password", command=generate_password)
pass_button.grid(column=2, row=3)
add_button = Button(text="Add", width=36, command=save)
add_button.grid(column=1, row=4, columnspan=2)
search_button = Button(text="Search", width=16, command=find_password)
search_button.grid(column=2, row=1)

# Show login screen before revealing the main app
login_screen()

window.mainloop()