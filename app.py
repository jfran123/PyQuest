from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "pyquest_secret_key"

# Create database if not exists
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Home Page
@app.route("/")
def home():
    return render_template("Index.html")

# Register
@app.route("/register", methods=["POST"])
def register():
    fullname = request.form["fullname"]
    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    try:
        c.execute("INSERT INTO users (fullname, email, password) VALUES (?, ?, ?)",
                  (fullname, email, password))
        conn.commit()
    except:
        return render_template("Register.html", error="Email already exists!")

    conn.close()
    return redirect("/")

# Login
@app.route("/login", methods=["POST","GET"])
def login():
    if request.method == "GET":
        return render_template("Login.html",error="")

    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    user = c.fetchone()
    conn.close()

    if user:
        session["user"] = user[1]
        return redirect("/dashboard")
    else:
        return render_template("Login.html", error="Invalid Email or Password")

# Dashboard
@app.route("/dashboard")
def dashboard():
    if "user" in session:
        return render_template("dashboard.html", name=session["user"],error="")
    return redirect("/")

# Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)