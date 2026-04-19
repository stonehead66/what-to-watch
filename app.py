import random

from cs50 import SQL
from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
from datetime import date

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///data/movies.db")

# Create recommendation parameters dict (rec_param)
@app.before_request
def init_rec_param():
    session.setdefault("rec_param", {
        "years": None,
        "rating": None,
        "genres": [],
        "languages": []
    })

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# app routes

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/actuality", methods=["GET", "POST"])
def actuality():
    if request.method == "GET":
        return render_template("actuality.html")

    years = request.form.get("years")
    session["rec_param"]["years"] = years

    return redirect(url_for("genres"))
    
@app.route("/genres", methods=["GET", "POST"])
def genres():
    if request.method == "GET":
        return render_template("genres.html")

    genres = request.form.getlist("genres")
    session["rec_param"]["genres"] = genres

    return redirect(url_for("languages"))
    
@app.route("/languages", methods=["GET", "POST"])
def languages():
    if request.method == "GET":
        return render_template("languages.html")
    
    languages = request.form.getlist("languages")
    session["rec_param"]["languages"] = languages

    return redirect(url_for("ratings"))

@app.route("/ratings", methods=["GET", "POST"])
def ratings():
    if request.method == "GET":
        return render_template("ratings.html")

    rating = request.form.get("rating")
    session["rec_param"]["rating"] = rating

    return redirect(url_for("result"))

@app.route("/result", methods=["GET", "POST"])
def result():
    params = session.get("rec_param", {})
    last = session.get("last_tconst")

    current_year = date.today().year
    min_year = current_year - int(params["years"] or 100)

    where, args = [], []

    where.append("m.startYear >= ?")
    args.append(min_year)

    where.append("m.averageRating >= ?")
    args.append(float(params.get("rating") or 0))

    if params["genres"] and "ALL" not in params["genres"]:
        ph = ", ".join(["?"] * len(params["genres"]))
        where.append(f"g.genre_red IN ({ph})")
        args.extend(params["genres"])

    if params["languages"] and "ALL" not in params["languages"]:
        ph = ", ".join(["?"] * len(params["languages"]))
        where.append(f"s.sp_languages_iso IN ({ph})")
        args.extend(params["languages"])

    if last:
        where.append("m.tconst != ?")
        args.append(last)

    query = f"""
    SELECT DISTINCT m.tconst, m.primaryTitle, m.startYear, m.averageRating, i.language_en
    FROM movies m
    JOIN genres g ON m.tconst = g.tconst
    JOIN spoken_languages s ON m.tconst = s.tconst
    JOIN langs_iso_639 i ON s.sp_languages_iso = i.iso_639_code
    WHERE {" AND ".join(where)}
    ORDER BY RANDOM()
    LIMIT 100
    """

    print("PARAMS:", params)
    print("WHERE:", where)
    print("ARGS:", args)
    rows = db.execute(query, *args)
    print("ROWS:", len(rows))
    recomm = random.choice(rows) if rows else None

    if recomm:
        session["last_tconst"] = recomm["tconst"]

    no_result = (recomm is None)

    return render_template("result.html", recomm=recomm, choices=rows, years=params["years"], genres=params["genres"], languages=params["languages"], rating=params["rating"], no_result=no_result)

if __name__ == "__main__":
    app.run()

