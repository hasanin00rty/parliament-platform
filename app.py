from flask import Flask, render_template, request, redirect, session
from werkzeug.security import check_password_hash
import sqlite3
import os
import config
from flask import flash


app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# ---------- DATABASE ----------
def get_db():
    return sqlite3.connect(config.DATABASE)

def init_db():
    if not os.path.exists(config.DATABASE):
        db = get_db()
        c = db.cursor()
        c.execute("""
        CREATE TABLE content (
            id INTEGER PRIMARY KEY,
            title TEXT,
            description TEXT
        )
        """)
        c.execute("""
        INSERT INTO content (title, description)
        VALUES ('التشريع مسؤولية… لا امتياز',
                'منصة سياسية مستقلة تُعنى بالتشريع والرقابة والشفافية')
        """)
        db.commit()
        db.close()

init_db()

# ---------- ROUTES ----------
@app.route("/")
def home():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT title, description FROM content WHERE id=1")
    data = c.fetchone()
    db.close()
    return render_template("index.html", title=data[0], desc=data[1])

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/shadow-parliament")
def shadow_parliament():
    return render_template("shadow_parliament.html")

@app.route("/oversight")
def oversight():
    return render_template("oversight.html")

@app.route("/constitution")
def constitution():
    return render_template("constitution.html")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "logged_in" in session:
        if request.method == "POST":
            db = get_db()
            c = db.cursor()
            c.execute("""
            UPDATE content SET title=?, description=? WHERE id=1
            """, (request.form["title"], request.form["desc"]))
            db.commit()
            db.close()
            return redirect("/")
        return render_template("admin.html")

    if request.method == "POST":
        password = request.form["password"]
        if check_password_hash(config.ADMIN_PASSWORD_HASH, password):
            session["logged_in"] = True
            return redirect("/admin")

    return render_template("admin.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/propose", methods=["GET", "POST"])
def propose():
    if request.method == "POST":
        db = get_db()
        c = db.cursor()
        c.execute("""
        INSERT INTO proposals (title, category, description, governorate)
        VALUES (?, ?, ?, ?)
        """, (
            request.form["title"],
            request.form["category"],
            request.form["description"],
            request.form.get("governorate")
        ))
        db.commit()
        db.close()

        flash("تم إرسال المقترح بنجاح، شكرًا لتعاونكم 🤍")
        return redirect("/propose")

    return render_template("propose.html")


@app.route("/admin/proposals", methods=["GET", "POST"])
def admin_proposals():
    if "logged_in" not in session:
        return redirect("/admin")

    db = get_db()
    c = db.cursor()

    if request.method == "POST":
        c.execute(
            "UPDATE proposals SET status=? WHERE id=?",
            (request.form["status"], request.form["id"])
        )
        db.commit()

    c.execute("SELECT * FROM proposals ORDER BY created_at DESC")
    proposals = c.fetchall()
    db.close()

    return render_template("admin_proposals.html", proposals=proposals)
@app.route("/proposals")
def proposals():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT * FROM proposals WHERE status='approved' ORDER BY created_at DESC")
    data = c.fetchall()
    db.close()
    return render_template("proposals.html", proposals=data)

if __name__ == "__main__":
    app.run()

