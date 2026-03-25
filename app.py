from flask import Flask,flash, jsonify, render_template, request, redirect, session
import sqlite3
from judge import run_code

app = Flask(__name__)
app.secret_key = "pyquest_secret_key"

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
            (fullname.lower(),email.lower(),password,role)
        )

        conn.commit()
        flash("User registered successfully!", "success")
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
    c.execute("SELECT * FROM users WHERE email=? OR fullname=? AND password=?", (email.lower(), email.lower(), password))
    user = c.fetchone()
    conn.close()

    if user:
        session["user"] = user[1]
        session["role"] = user[4]
        session["user_id"] = user[0]
        if user[4] == "admin":
            return redirect("/admin")

        elif user[4] == "teacher":
            return redirect("/teacher")
        else:
            flash('You were successfully logged in', 'success')
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
    admin_name = session["user"].capitalize()
    if "user" in session and session["role"].lower() == "admin":
        return render_template("admin.html", name=admin_name)
    return redirect("/")
# Admin Users View
@app.route("/admin/users")
def admin_users():

    if session["role"] != "admin":
        return "Unauthorized"

    conn = db()
    c = conn.cursor()

    c.execute("SELECT id,fullname,role FROM users")
    users = c.fetchall()

    conn.close()

    return render_template("admin_users.html", users=users)
# Admin Update UserRole
@app.route("/admin/update_role/<int:uid>", methods=["POST"])
def update_role(uid):

    if session["role"] != "admin":
        return "Unauthorized"

    new_role = request.form["role"]

    conn = db()
    c = conn.cursor()

    c.execute(
    "UPDATE users SET role=? WHERE id=?",
    (new_role, uid)
    )

    conn.commit()
    conn.close()
    flash("User role updated successfully!", "success")
    return redirect("/admin/users")

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

    c.execute("SELECT * FROM problems WHERE teacher_id=?", (session["user"],))
    problems = c.fetchall()

    conn.close()

    return render_template("teacher_problems.html", problems=problems)

# TeacherAdd Problem
@app.route("/add_problem", methods=["POST"])
def add_problem():

    title = request.form["title"]
    desc = request.form["description"]
    level = request.form["level"]
    inp = request.form["input"]
    out = request.form["output"]

    conn = db()
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
    flash("Problem added successfully!", "success")
    return redirect("/teacher")
# Teacher Manage Problems
@app.route("/manage_problems")
def manage_problems():
    conn = db()
    c = conn.cursor()

    c.execute("SELECT * FROM problems WHERE teacher_id=?", (session["user_id"],))
    problems = c.fetchall()

    conn.close()

    return render_template("manage_problem.html", problems=problems)
# Teacher View/Edit Problem
@app.route("/teacher/edit_problem/<int:pid>", methods=["POST"])
def edit_problem(pid):

    title = request.form["title"]
    desc = request.form["description"]
    level = request.form["level"]
    inp = request.form["input"]
    out = request.form["output"]

    conn = db()
    c = conn.cursor()

    c.execute(
        "UPDATE problems SET title=?, description=?, level=? WHERE id=?",
        (title,desc,level,pid)
    )

    c.execute(
        "UPDATE testcases SET input=?, expected_output=? WHERE problem_id=?",
        (inp,out,pid)
    )

    conn.commit()
    conn.close()

    return redirect("/manage_problems")
# Teacher Edit Problem
@app.route("/teacher/update_problem/<int:id>", methods=["POST"])
def update_problem(id):

    if session.get("role") != "teacher":
        return redirect("/login")

    title = request.form["title"]
    description = request.form["description"]
    level = request.form["difficulty"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    UPDATE problems
    SET title=?, description=?, level=?
    WHERE id=? AND teacher_id=?
    """, (title, description, level, id, session["user_id"]))

    conn.commit()
    flash("Problem updated successfully!", "success")
    conn.close()

    return redirect("/manage_problems")
# Teacher Delete Problem
@app.route("/teacher/delete_problem/<int:id>")
def delete_problem(id):

    if session.get("role") != "teacher":
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    DELETE FROM problems
    WHERE id=? AND teacher_id=?
    """, (id, session["user_id"]))

    conn.commit()
    flash("Problem deleted successfully!", "success")
    conn.close()

    return redirect("/manage_problems")
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
    c.execute("select level from problems where id=?", (pid,))
    level = c.fetchone()[0]
    point=0
    match level:
        case 0:
            point = 10
        case 1:
            point = 20
        case 2:
            point = 30
        case _:
            point = 0
    
    passed = 0

    for test in tests:

        inp = test[0]
        expected = test[1]

        output = run_code(code, inp)

        if output == expected:
            passed += 1

    if passed == len(tests):
        result = "Correct"
        c.execute(
            "UPDATE users SET points = points + {0} WHERE email=?", (point, session["user"])
        )
    else:
        result = "Wrong"
    # Save submission
    c.execute(
        "INSERT INTO submissions(user,problem_id,code,result) VALUES(?,?,?,?)",
        (session["user"], pid, code, result)
    )
    conn.commit()
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

    conn = db()
    c = conn.cursor()

    c.execute("SELECT fullname, points FROM users where role='student' ORDER BY points DESC")
    users = c.fetchall()

    conn.close()

    return render_template("leaderboard.html", users=users)
# Student Progress Page
@app.route("/progress")
def progress():

    if "user" not in session:
        return redirect("/")

    conn = db()
    c = conn.cursor()

    # total submissions
    c.execute(
        "SELECT COUNT(*) FROM submissions WHERE user=?",
        (session["user"],)
    )
    total_submissions = c.fetchone()[0]

    # solved problems
    c.execute(
        "SELECT COUNT(DISTINCT problem_id) FROM submissions WHERE user=? AND result='Correct'",
        (session["user"],)
    )
    solved = c.fetchone()[0]

    # total problems
    c.execute("SELECT COUNT(*) FROM problems")
    total_problems = c.fetchone()[0]

    success_rate = 0
    if total_submissions > 0:
        success_rate = round((solved / total_submissions) * 100, 2)

    # solved list
    c.execute("""
        SELECT problems.title
        FROM submissions
        JOIN problems ON submissions.problem_id = problems.id
        WHERE submissions.user=? AND submissions.result='Correct'
        GROUP BY problems.title
    """, (session["user"],))

    solved_list = c.fetchall()

    conn.close()

    return render_template(
        "progress.html",
        solved=solved,
        total_problems=total_problems,
        total_submissions=total_submissions,
        success_rate=success_rate,
        solved_list=solved_list
    )

if __name__ == "__main__":
    app.run(debug=True)