from flask import Flask, jsonify, render_template, request, redirect, session
import sqlite3
import os
from judge import run_code

app = Flask(__name__)
app.secret_key = "pyquest_secret_key"


# Create database if not exists
# def init_db():
#     conn = sqlite3.connect("database.db")
#     c = conn.cursor()
#     c.execute('''
#         CREATE TABLE IF NOT EXISTS users (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             fullname TEXT,
#             email TEXT UNIQUE,
#             password TEXT
#         )
#     ''')
#     conn.commit()
#     conn.close()

# init_db()

def db():
    return sqlite3.connect("database.db")

# Home Page
@app.route("/")
def home():
    return render_template("Index.html")

# REGISTER
@app.route("/register", methods=["POST"])
def register():

    fullname = request.form["fullname"]
    email = request.form["email"]
    password = request.form["password"]
    role = request.form["role"]

    conn = db()
    c = conn.cursor()

    try:

        c.execute(
            "INSERT INTO users(fullname,email,password,role) VALUES(?,?,?,?)",
            (fullname,email,password,role)
        )

        conn.commit()

    except:
        return render_template("Register.html", error="Email exists")

    conn.close()

    return redirect("/")

# Login
@app.route("/login", methods=["POST","GET"])
def login():
    if request.method == "GET":
        return render_template("Login.html",error="")

    email = request.form["email"]
    password = request.form["password"]

    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    user = c.fetchone()
    conn.close()

    if user:
        session["user"] = user[1]
        session["role"] = user[4]
        if user[4] == "admin":
            return redirect("/admin")

        elif user[4] == "teacher":
            return redirect("/teacher")
        else:
            return redirect("/dashboard")
    else:
        return render_template("Login.html", error="Invalid Email or Password")
# Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# Dashboard
@app.route("/dashboard")
def dashboard():
    if "user" in session:
        return render_template("dashboard.html", name=session["user"],error="")
    return redirect("/")

# Admin Dashboard
@app.route("/admin")
def admin():
    if "user" in session and session["user"].lower() == "admin":
        return render_template("admin.html", name=session["user"])
    return redirect("/")

# Teacher Dashboard
@app.route("/teacher")
def teacher():

    if "user" in session and session["role"] == "teacher":
        return render_template("teacher.html", name=session["user"])
    return redirect("/")
# Teacher Problems View
@app.route("/teacher/problems")
def teacher_problems():

    conn = db()
    c = conn.cursor()

    c.execute("SELECT * FROM problems")
    problems = c.fetchall()

    conn.close()

    return render_template("teacher_problems.html", problems=problems)

# Add Problem
@app.route("/add_problem", methods=["POST"])
def add_problem():

    title = request.form["title"]
    desc = request.form["description"]
    level = request.form["level"]
    inp = request.form["input"]
    out = request.form["output"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO problems(title,description,level) VALUES(?,?,?)",
        (title,desc,level)
    )

    pid = c.lastrowid

    c.execute(
        "INSERT INTO testcases(problem_id,input,expected_output) VALUES(?,?,?)",
        (pid,inp,out)
    )

    conn.commit()
    conn.close()

    return redirect("/teacher")


# PROBLEMS BY LEVEL
@app.route("/problems/<level>")
def problems(level):

    conn = db()
    c = conn.cursor()

    c.execute("SELECT * FROM problems WHERE level=?", (level,))
    problems = c.fetchall()

    conn.close()

    return render_template("problems.html", problems=problems, level=level)


# SINGLE PROBLEM
@app.route("/problem/<int:pid>")
def problem(pid):

    conn = db()
    c = conn.cursor()

    c.execute("SELECT * FROM problems WHERE id=?", (pid,))
    problem = c.fetchone()
    
    # get example test case
    c.execute(
        "SELECT input, expected_output FROM testcases WHERE problem_id=? LIMIT 1",
        (pid,)
    )

    example = c.fetchone()

    conn.close()

    return render_template("problem.html", problem=problem, example=example)

# # RUN CODE PREVIEW
# @app.route("/run", methods=["POST"])
# def run():

#     code = request.json["code"]

#     output = run_code(code)

#     return jsonify({"output": output})


# Submit Problem
@app.route("/submit/<int:pid>", methods=["POST"])
def submit(pid):

    if "user" not in session:
        return redirect("/")

    code = request.form["code"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT input, expected_output FROM testcases WHERE problem_id=?", (pid,))
    tests = c.fetchall()

    passed = 0

    for test in tests:

        inp = test[0]
        expected = test[1]

        output = run_code(code, inp)

        if output == expected:
            passed += 1

    if passed == len(tests):
        result = "Correct"
    else:
        result = "Wrong"

    conn.close()

    return render_template("result.html", result=result)



# Run Code
@app.route("/run", methods=["POST"])
def run():
    # print(request.form["code"])
    data = request.get_json()
    code = data["code"]
    input_data = data.get("input","")
    from judge import run_code

    output = run_code(code, input_data)

    return {"output": output}

# Leaderboard
@app.route("/leaderboard")
def leaderboard():

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT fullname, points FROM users ORDER BY points DESC")
    users = c.fetchall()

    conn.close()

    return render_template("leaderboard.html", users=users)

if __name__ == "__main__":
    app.run(debug=True)