from tkinter import *
from tkinter import messagebox
from random import choice, randint, shuffle
import pyperclip
from database import Password, session
import os
from cryptography.fernet import Fernet

# ---------------------------- ENCRYPTION SETUP ------------------------------- #
KEY_FILE = "secret.key"

def load_or_create_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        return key

KEY = load_or_create_key()
fernet = Fernet(KEY)

def encrypt(password):
    return fernet.encrypt(password.encode()).decode()

def decrypt(token):
    return fernet.decrypt(token.encode()).decode()

# ---------------------------- PASSWORD GENERATOR ------------------------------- #
def generate_password():
    letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    symbols = ['!', '#', '$', '%', '&', '(', ')', '*', '+']

    password_letters = [choice(letters) for _ in range(randint(8, 10))]
    password_symbols = [choice(symbols) for _ in range(randint(2, 4))]
    password_numbers = [choice(numbers) for _ in range(randint(2, 4))]

    password_list = password_letters + password_symbols + password_numbers
    shuffle(password_list)

    password = "".join(password_list)
    pass_entry.delete(0, END)
    pass_entry.insert(0, password)
    pyperclip.copy(password)

# ---------------------------- SAVE PASSWORD ------------------------------- #
def save():
    website = website_entry.get()
    email = email_entry.get()
    password = pass_entry.get()

    if len(website) == 0 or len(password) == 0:
        messagebox.showinfo(title="Oops", message="Please don't leave any fields empty")
    else:
        new_entry = Password(
            website=website,
            email=email,
            password=encrypt(password)
        )
        session.add(new_entry)
        session.commit()
        website_entry.delete(0, 'end')
        pass_entry.delete(0, 'end')
        website_entry.focus()
        messagebox.showinfo(title="Success", message="Password saved successfully!")


# ---------------------------- FIND PASSWORD ------------------------------- #
def find_password():
    website = website_entry.get()
    result = session.query(Password).filter_by(website=website).first()

    if result is None:
        messagebox.showinfo(title="Error", message="No details for the website exist")
    else:
        decrypted_password = decrypt(result.password)
        messagebox.showinfo(title=website, message=f"Email: {result.email}\nPassword: {decrypted_password}")

# ---------------------------- UI SETUP ------------------------------- #
window = Tk()
window.title("Password Manager")
window.config(padx=50, pady=50)

canvas = Canvas(width=200, height=200)
logo_img = PhotoImage(file="logo.png")
canvas.create_image(100, 100, image=logo_img)
canvas.grid(row=0,column=1)

# labels
website_label = Label(text="Website:")
website_label.grid(column=0, row=1)
email_label = Label(text="Email/Username:")
email_label.grid(column=0, row=2)
Pass_label = Label(text="Password:")
Pass_label.grid(column=0, row=3)

# entries
website_entry = Entry(width=21)
website_entry.grid(column=1, row=1)
website_entry.focus()
email_entry = Entry(width=40)
email_entry.grid(column=1, row=2, columnspan=2)
email_entry.insert(0, "mymail@mail.com")
pass_entry = Entry(width=21)
pass_entry.grid(column=1, row=3)

# buttons
pass_button = Button(text="Generate Password", command=generate_password)
pass_button.grid(column=2, row=3)
add_button = Button(text="Add", width=36, command=save)
add_button.grid(column=1, row=4, columnspan=2)
search_button = Button(text="Search", width=16, command=find_password)
search_button.grid(column=2, row=1)
window.mainloop()