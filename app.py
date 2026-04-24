import random
import os

from cs50 import SQL
from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
from datetime import date

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "/home/stonehead66/flask_session"
Session(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure CS50 Library to use SQLite database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "data", "movies.db")
db = SQL(f"sqlite:///{db_path}")


@app.before_request
def init_rec_param():
    session.setdefault("rec_param", {
        "years": None,
        "rating": None,
        "genres": [],
        "languages": []
    })
    session.setdefault("shown_tconsts", [])
    session.setdefault("random_mode", False)


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


def reset_recommendation_state():
    session["shown_tconsts"] = []


# app routes

@app.route("/")
def index():
    reset_recommendation_state()
    session["random_mode"] = False
    return render_template("index.html")


@app.route("/random")
def random_shortcut():
    session["rec_param"] = {
        "years": 100,
        "rating": 0,
        "genres": ["ALL"],
        "languages": ["ALL"]
    }
    session["random_mode"] = True
    reset_recommendation_state()

    return redirect(url_for("result"))


@app.route("/actuality", methods=["GET", "POST"])
def actuality():
    if request.method == "GET":
        reset_recommendation_state()
        session["random_mode"] = False
        return render_template("actuality.html")

    params = session.get("rec_param", {})
    params["years"] = request.form.get("years")
    session["rec_param"] = params
    session["random_mode"] = False

    return redirect(url_for("genres"))


@app.route("/genres", methods=["GET", "POST"])
def genres():
    if request.method == "GET":
        return render_template("genres.html")

    params = session.get("rec_param", {})
    params["genres"] = request.form.getlist("genres")
    session["rec_param"] = params
    session["random_mode"] = False

    return redirect(url_for("languages"))


@app.route("/languages", methods=["GET", "POST"])
def languages():
    if request.method == "GET":
        return render_template("languages.html")

    params = session.get("rec_param", {})
    params["languages"] = request.form.getlist("languages")
    session["rec_param"] = params
    session["random_mode"] = False

    return redirect(url_for("ratings"))


@app.route("/ratings", methods=["GET", "POST"])
def ratings():
    if request.method == "GET":
        return render_template("ratings.html")

    params = session.get("rec_param", {})
    params["rating"] = request.form.get("rating")
    session["rec_param"] = params
    session["random_mode"] = False

    reset_recommendation_state()

    return redirect(url_for("result"))


@app.route("/result", methods=["GET"])
def result():
    params = session.get("rec_param", {})
    shown_tconsts = session.get("shown_tconsts", [])

    current_year = date.today().year
    min_year = current_year - int(params.get("years") or 100)

    where = []
    args = []

    where.append("m.startYear >= ?")
    args.append(min_year)

    where.append("m.averageRating >= ?")
    args.append(float(params.get("rating") or 0))

    if params.get("genres") and "ALL" not in params["genres"]:
        ph = ", ".join(["?"] * len(params["genres"]))
        where.append(f"g.genre_red IN ({ph})")
        args.extend(params["genres"])

    if params.get("languages") and "ALL" not in params["languages"]:
        ph = ", ".join(["?"] * len(params["languages"]))
        where.append(f"s.sp_languages_iso IN ({ph})")
        args.extend(params["languages"])

    if shown_tconsts:
        ph = ", ".join(["?"] * len(shown_tconsts))
        where.append(f"m.tconst NOT IN ({ph})")
        args.extend(shown_tconsts)

    query = f"""
    SELECT DISTINCT
        m.tconst,
        m.primaryTitle,
        m.startYear,
        m.averageRating,
        i.language_en
    FROM movies m
    JOIN genres g ON m.tconst = g.tconst
    JOIN spoken_languages s ON m.tconst = s.tconst
    JOIN langs_iso_639 i ON s.sp_languages_iso = i.iso_639_code
    WHERE {" AND ".join(where)}
    ORDER BY RANDOM()
    LIMIT 100
    """

    print("PARAMS:", params)
    print("SHOWN:", shown_tconsts)
    print("WHERE:", where)
    print("ARGS:", args)

    rows = db.execute(query, *args)
    print("ROWS:", len(rows))

    recomm = random.choice(rows) if rows else None

    if recomm:
        shown_tconsts.append(recomm["tconst"])
        session["shown_tconsts"] = shown_tconsts

    no_result = (recomm is None)

    return render_template(
        "result.html",
        recomm=recomm,
        choices=rows,
        years=params.get("years"),
        genres=params.get("genres"),
        languages=params.get("languages"),
        rating=params.get("rating"),
        no_result=no_result,
        random_mode=session.get("random_mode", False)
    )


if __name__ == "__main__":
    app.run()