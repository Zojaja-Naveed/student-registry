import time
import pymysql
from flask import Flask, request, redirect, render_template_string

def secret(name):
    with open(f"/run/secrets/{name}") as f:
        return f.read().strip()

def get_conn():
    return pymysql.connect(
        host="db",
        user=secret("db_user"),
        password=secret("db_password"),
        database=secret("db_name"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )

def init_db():
    for _ in range(20):
        try:
            conn = get_conn()
            with conn.cursor() as c:
                c.execute("""CREATE TABLE IF NOT EXISTS students (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    reg_no VARCHAR(30) NOT NULL,
                    department VARCHAR(50) NOT NULL)""")
            conn.close()
            return
        except Exception as e:
            print("Waiting for database...", e)
            time.sleep(3)

init_db()
app = Flask(__name__)

PAGE = """
<!doctype html>
<title>Student Registry</title>
<body style="font-family:Arial;max-width:700px;margin:40px auto">
<h1>Student Registry</h1>
<p>Deployed with Docker Compose on AWS EC2</p>
<form method="POST" action="/add">
  <input name="name" placeholder="Name" required>
  <input name="reg_no" placeholder="Reg No" required>
  <input name="department" placeholder="Department" required>
  <button>Add Student</button>
</form>
<hr>
<table border="1" cellpadding="8" style="border-collapse:collapse;width:100%">
  <tr><th>ID</th><th>Name</th><th>Reg No</th><th>Department</th><th></th></tr>
  {% for s in students %}
  <tr>
    <td>{{ s.id }}</td><td>{{ s.name }}</td><td>{{ s.reg_no }}</td><td>{{ s.department }}</td>
    <td><form method="POST" action="/delete/{{ s.id }}"><button>Delete</button></form></td>
  </tr>
  {% endfor %}
</table>
</body>
"""

@app.route("/")
def index():
    conn = get_conn()
    with conn.cursor() as c:
        c.execute("SELECT * FROM students ORDER BY id DESC")
        rows = c.fetchall()
    conn.close()
    return render_template_string(PAGE, students=rows)

@app.route("/add", methods=["POST"])
def add():
    conn = get_conn()
    with conn.cursor() as c:
        c.execute("INSERT INTO students(name, reg_no, department) VALUES(%s,%s,%s)",
                  (request.form["name"], request.form["reg_no"], request.form["department"]))
    conn.close()
    return redirect("/")

@app.route("/delete/<int:sid>", methods=["POST"])
def delete(sid):
    conn = get_conn()
    with conn.cursor() as c:
        c.execute("DELETE FROM students WHERE id=%s", (sid,))
    conn.close()
    return redirect("/")