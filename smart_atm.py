
import tkinter as tk
from tkinter import messagebox, simpledialog
import sqlite3
from datetime import datetime
from urllib.parse import urlencode

import qrcode
import pyttsx3
from PIL import ImageTk


# ==================================================
# CONFIGURATION
# ==================================================

DB_FILE = "smart_atm_multi.db"
INITIAL_BALANCE = 10000.0

UPI_ID = "7387915058@ybl"
PAYEE_NAME = "Vaishnavi"

LANG = "English"
FAILED_ATTEMPTS = 0

CURRENT_ACCOUNT = None
CURRENT_NAME = None
BALANCE = 0.0


# ==================================================
# FIVE DEMO ACCOUNTS
# ==================================================

INITIAL_ACCOUNTS = [
    ("1001", "Rajukar Sir", "1234", 10000.0),
    ("1002", "Vaishanvi Mam", "2345", 15000.0),
    ("1003", "Ranjana", "3456", 20000.0),
    ("1004", "Vinita", "4567", 25000.0),
    ("1005", "Rajeshree", "5678", 30000.0)
]


# ==================================================
# LANGUAGE TEXT
# ==================================================

TEXT = {
    "English": {
        "welcome": "Welcome to Smart ATM",
        "menu": "ATM MENU",
        "balance": "Check Balance",
        "deposit": "Deposit Money",
        "withdraw": "Withdraw Money",
        "statement": "Mini Statement",
        "qr": "My UPI QR - Receive Payment",
        "change_pin": "Change PIN",
        "exit": "Logout",
        "pin": "Enter your PIN",
        "account": "Enter your account number",
        "wrong_pin": "Incorrect account number or PIN",
        "blocked": "ATM access blocked after 3 attempts",
        "amount": "Enter amount in rupees",
        "success": "Transaction successful",
        "insufficient": "Insufficient balance",
        "invalid": "Enter a valid amount",
        "new_pin": "Enter new 4-digit PIN",
        "confirm_pin": "Confirm new PIN",
        "pin_changed": "PIN changed successfully",
        "qr_title": "Scan to Pay",
        "back": "Back to Menu",
        "no_transactions": "No transactions yet",
        "payment_note": "Scan with any compatible UPI app",
        "fraud": "Maximum withdrawal is ₹5000",
        "welcome_user": "Welcome"
    },

    "Hindi": {
        "welcome": "Smart ATM mein aapka swagat hai",
        "menu": "ATM MENU",
        "balance": "Balance dekhein",
        "deposit": "Paise jama karein",
        "withdraw": "Paise nikalein",
        "statement": "Mini Statement",
        "qr": "Mera UPI QR - Payment prapt karein",
        "change_pin": "PIN badlein",
        "exit": "Logout",
        "pin": "Apna PIN daalein",
        "account": "Account number daalein",
        "wrong_pin": "Galat account number ya PIN",
        "blocked": "3 galat prayason ke baad access block",
        "amount": "Rakam daalein",
        "success": "Transaction safal",
        "insufficient": "Pariyapt balance nahi hai",
        "invalid": "Sahi rakam daalein",
        "new_pin": "Naya 4-digit PIN daalein",
        "confirm_pin": "Naya PIN dobara daalein",
        "pin_changed": "PIN safalta se badal gaya",
        "qr_title": "Payment ke liye scan karein",
        "back": "Menu par wapas",
        "no_transactions": "Abhi koi transaction nahi",
        "payment_note": "Compatible UPI app se scan karein",
        "fraud": "Maximum withdrawal ₹5000 hai",
        "welcome_user": "Swagat hai"
    },

    "Marathi": {
        "welcome": "Smart ATM madhye aaple swagat aahe",
        "menu": "ATM MENU",
        "balance": "Shillak paha",
        "deposit": "Paise jama kara",
        "withdraw": "Paise kadha",
        "statement": "Mini Statement",
        "qr": "Maza UPI QR - Payment milava",
        "change_pin": "PIN badla",
        "exit": "Logout",
        "pin": "Aapla PIN taka",
        "account": "Account number taka",
        "wrong_pin": "Chukicha account number kiwa PIN",
        "blocked": "3 chukichya prayatnannantar access block",
        "amount": "Rakkam taka",
        "success": "Transaction yashasvi",
        "insufficient": "Pureshi shillak nahi",
        "invalid": "Yogya rakkam taka",
        "new_pin": "Nava 4-digit PIN taka",
        "confirm_pin": "Nava PIN punha taka",
        "pin_changed": "PIN yashasviritya badalla",
        "qr_title": "Payment sathi scan kara",
        "back": "Menu var parat",
        "no_transactions": "Ajun transaction nahi",
        "payment_note": "Compatible UPI app ne scan kara",
        "fraud": "Maximum withdrawal ₹5000 aahe",
        "welcome_user": "Swagat aahe"
    }
}


def msg(key):
    return TEXT[LANG][key]


# ==================================================
# VOICE ASSISTANCE
# ==================================================

try:
    voice = pyttsx3.init()
    voice.setProperty("rate", 150)
except Exception:
    voice = None


def speak(text):
    if voice:
        try:
            voice.say(text)
            voice.runAndWait()
        except Exception:
            pass


# ==================================================
# DATABASE
# ==================================================

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS accounts (
    account_no TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    pin TEXT NOT NULL,
    balance REAL NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_no TEXT NOT NULL,
    type TEXT NOT NULL,
    amount REAL NOT NULL,
    date TEXT NOT NULL
)
""")

# Add accounts only if they do not already exist.
# Existing balances and changed PINs will be preserved.
cursor.executemany("""
INSERT OR IGNORE INTO accounts
(account_no, name, pin, balance)
VALUES (?, ?, ?, ?)
""", INITIAL_ACCOUNTS)

conn.commit()


def save_transaction(kind, amount):
    date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    cursor.execute("""
        INSERT INTO transactions
        (account_no, type, amount, date)
        VALUES (?, ?, ?, ?)
    """, (CURRENT_ACCOUNT, kind, amount, date))

    conn.commit()


def update_balance():
    cursor.execute("""
        UPDATE accounts
        SET balance = ?
        WHERE account_no = ?
    """, (BALANCE, CURRENT_ACCOUNT))

    conn.commit()


# ==================================================
# GUI
# ==================================================

root = tk.Tk()
root.title("Smart Accessible ATM")
root.geometry("600x700")
root.configure(bg="#102A43")
root.resizable(False, False)


def clear_screen():
    for widget in root.winfo_children():
        widget.destroy()


def title(text):
    tk.Label(
        root,
        text=text,
        font=("Arial", 21, "bold"),
        bg="#102A43",
        fg="white",
        wraplength=550
    ).pack(pady=20)


def make_button(text, command):
    tk.Button(
        root,
        text=text,
        command=command,
        font=("Arial", 13, "bold"),
        width=32,
        height=2,
        bg="#2F80ED",
        fg="white",
        activebackground="#1366D6",
        cursor="hand2"
    ).pack(pady=6)


def show_account_info():
    tk.Label(
        root,
        text=f"{CURRENT_NAME} | Account: {CURRENT_ACCOUNT}",
        font=("Arial", 12),
        bg="#102A43",
        fg="white"
    ).pack(pady=5)


# ==================================================
# BALANCE
# ==================================================

def check_balance():
    clear_screen()
    title(msg("balance"))
    show_account_info()

    tk.Label(
        root,
        text=f"₹ {BALANCE:,.2f}",
        font=("Arial", 30, "bold"),
        bg="#102A43",
        fg="#00E676"
    ).pack(pady=40)

    speak(f"Your balance is {BALANCE} rupees")
    make_button(msg("back"), show_menu)


# ==================================================
# DEPOSIT
# ==================================================

def deposit():
    global BALANCE

    amount = simpledialog.askfloat(
        msg("deposit"),
        msg("amount"),
        minvalue=0.01,
        parent=root
    )

    if amount is None:
        return

    if amount <= 0:
        messagebox.showerror("ATM", msg("invalid"))
        return

    BALANCE += amount
    update_balance()
    save_transaction("Deposit", amount)

    messagebox.showinfo(
        "ATM",
        f"{msg('success')}\n"
        f"Deposited: ₹{amount:,.2f}\n"
        f"New balance: ₹{BALANCE:,.2f}"
    )

    speak(msg("success"))
    show_menu()


# ==================================================
# WITHDRAW
# ==================================================

def withdraw():
    global BALANCE

    amount = simpledialog.askfloat(
        msg("withdraw"),
        msg("amount"),
        minvalue=0.01,
        parent=root
    )

    if amount is None:
        return

    if amount <= 0:
        messagebox.showerror("ATM", msg("invalid"))
        return

    if amount > 5000:
        messagebox.showwarning("Security", msg("fraud"))
        speak(msg("fraud"))
        return

    if amount > BALANCE:
        messagebox.showerror("ATM", msg("insufficient"))
        return

    BALANCE -= amount
    update_balance()
    save_transaction("Withdrawal", amount)

    messagebox.showinfo(
        "ATM",
        f"{msg('success')}\n"
        f"Withdrawn: ₹{amount:,.2f}\n"
        f"New balance: ₹{BALANCE:,.2f}"
    )

    speak(msg("success"))
    show_menu()


# ==================================================
# MINI STATEMENT
# ==================================================

def mini_statement():
    clear_screen()
    title(msg("statement"))
    show_account_info()

    cursor.execute("""
        SELECT type, amount, date
        FROM transactions
        WHERE account_no = ?
        ORDER BY id DESC
        LIMIT 5
    """, (CURRENT_ACCOUNT,))

    rows = cursor.fetchall()

    if not rows:
        tk.Label(
            root,
            text=msg("no_transactions"),
            font=("Arial", 13),
            bg="#102A43",
            fg="white"
        ).pack(pady=20)

    for kind, amount, date in rows:
        tk.Label(
            root,
            text=f"{kind}: ₹{amount:,.2f}\n{date}",
            font=("Arial", 12),
            bg="#102A43",
            fg="white"
        ).pack(pady=8)

    make_button(msg("back"), show_menu)


# ==================================================
# UPI QR PAYMENT
# ==================================================

def qr_payment():
    amount = simpledialog.askfloat(
        "UPI Payment",
        "Enter payment amount (₹):",
        minvalue=1,
        parent=root
    )

    if amount is None:
        return

    if amount <= 0:
        messagebox.showerror("Error", msg("invalid"))
        return

    payment_data = {
        "pa": UPI_ID,
        "pn": PAYEE_NAME,
        "am": f"{amount:.2f}",
        "cu": "INR",
        "tn": "Smart ATM Demo Payment"
    }

    upi_link = "upi://pay?" + urlencode(payment_data)
    qr_image = qrcode.make(upi_link)

    clear_screen()
    title(msg("qr_title"))
    show_account_info()

    photo = ImageTk.PhotoImage(qr_image)
    qr_label = tk.Label(root, image=photo, bg="#102A43")
    qr_label.image = photo
    qr_label.pack(pady=15)

    tk.Label(
        root,
        text=f"Pay ₹{amount:,.2f}",
        font=("Arial", 20, "bold"),
        bg="#102A43",
        fg="#00E676"
    ).pack(pady=8)

    tk.Label(
        root,
        text=UPI_ID,
        font=("Arial", 13),
        bg="#102A43",
        fg="white"
    ).pack(pady=5)

    tk.Label(
        root,
        text=msg("payment_note"),
        font=("Arial", 11),
        bg="#102A43",
        fg="white"
    ).pack(pady=5)

    speak(msg("qr_title"))
    make_button(msg("back"), show_menu)


# ==================================================
# CHANGE PIN
# ==================================================

def change_pin():
    new_pin = simpledialog.askstring(
        "Change PIN",
        msg("new_pin"),
        show="*",
        parent=root
    )

    if new_pin is None:
        return

    if not new_pin.isdigit() or len(new_pin) != 4:
        messagebox.showerror(
            "Error",
            "PIN must contain exactly 4 digits"
        )
        return

    confirm_pin = simpledialog.askstring(
        "Change PIN",
        msg("confirm_pin"),
        show="*",
        parent=root
    )

    if confirm_pin is None:
        return

    if new_pin != confirm_pin:
        messagebox.showerror("Error", "PINs do not match")
        return

    cursor.execute("""
        UPDATE accounts
        SET pin = ?
        WHERE account_no = ?
    """, (new_pin, CURRENT_ACCOUNT))

    conn.commit()
    messagebox.showinfo("ATM", msg("pin_changed"))


# ==================================================
# LOGOUT
# ==================================================

def logout():
    global CURRENT_ACCOUNT, CURRENT_NAME, BALANCE

    CURRENT_ACCOUNT = None
    CURRENT_NAME = None
    BALANCE = 0.0

    language_screen()


# ==================================================
# ATM MENU
# ==================================================

def show_menu():
    clear_screen()
    title(msg("menu"))
    show_account_info()
    speak(msg("menu"))

    make_button(msg("balance"), check_balance)
    make_button(msg("deposit"), deposit)
    make_button(msg("withdraw"), withdraw)
    make_button(msg("statement"), mini_statement)
    make_button(msg("qr"), qr_payment)
    make_button(msg("change_pin"), change_pin)
    make_button(msg("exit"), logout)


# ==================================================
# LOGIN
# ==================================================

def login():
    global FAILED_ATTEMPTS
    global CURRENT_ACCOUNT, CURRENT_NAME, BALANCE

    FAILED_ATTEMPTS = 0

    while FAILED_ATTEMPTS < 3:
        account_no = simpledialog.askstring(
            "ATM Login",
            msg("account"),
            parent=root
        )

        if account_no is None:
            language_screen()
            return

        entered_pin = simpledialog.askstring(
            "ATM Login",
            msg("pin"),
            show="*",
            parent=root
        )

        if entered_pin is None:
            language_screen()
            return

        cursor.execute("""
            SELECT account_no, name, balance
            FROM accounts
            WHERE account_no = ? AND pin = ?
        """, (account_no.strip(), entered_pin))

        account = cursor.fetchone()

        if account:
            CURRENT_ACCOUNT = account[0]
            CURRENT_NAME = account[1]
            BALANCE = account[2]

            messagebox.showinfo(
                msg("welcome_user"),
                f"{msg('welcome_user')}, {CURRENT_NAME}!"
            )

            show_menu()
            return

        FAILED_ATTEMPTS += 1

        messagebox.showerror(
            "ATM",
            f"{msg('wrong_pin')}\n"
            f"Attempts remaining: {3 - FAILED_ATTEMPTS}"
        )

    messagebox.showerror("ATM", msg("blocked"))
    language_screen()


# ==================================================
# LANGUAGE SELECTION
# ==================================================

def select_language(language):
    global LANG
    LANG = language

    clear_screen()
    title(msg("welcome"))
    speak(msg("welcome"))

    make_button("Continue", login)


def language_screen():
    clear_screen()
    title("Select Language / भाषा / भाषा निवडा")

    make_button("English", lambda: select_language("English"))
    make_button("Hindi", lambda: select_language("Hindi"))
    make_button("Marathi", lambda: select_language("Marathi"))


# ==================================================
# START APPLICATION
# ==================================================

def on_close():
    conn.close()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_close)

language_screen()
root.mainloop()
