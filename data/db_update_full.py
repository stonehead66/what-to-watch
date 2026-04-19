# Update movies database with IMDb data
# fetch spoken languages for newly imported movies via TMDB API
# and store genres for newly imported movies in a separate genres table

import time
import sqlite3
from datetime import datetime

import pandas as pd
import requests

DB = "movies.db"

# TMDB
API_KEY = "ff9cb04c1de659c8145996f5099a4bd5"
BASE = "https://api.themoviedb.org/3"
PAUSE = 0.1
BATCH_COMMIT = 25

GENRE_RED_MAP = {
    "Sci-Fi": "Sci-Fi/Fantasy",
    "Fantasy": "Sci-Fi/Fantasy",
    "Comedy": "Comedy/Romance",
    "Romance": "Comedy/Romance",
    "Biography": "Biography/Documentary/Sport",
    "Documentary": "Biography/Documentary/Sport",
    "Sport": "Biography/Documentary/Sport",
    "Crime": "Crime/Thriller",
    "Thriller": "Crime/Thriller",
    "Action": "Action/Adventure/Western",
    "Adventure": "Action/Adventure/Western",
    "Western": "Action/Adventure/Western",
    "Animation": "Animation/Family",
    "Family": "Animation/Family",
    "Drama": "Drama",
    "Horror": "Horror/Mystery",
    "Mystery": "Horror/Mystery",
    "Music": "Music/Musical",
    "Musical": "Music/Musical",
}


def tmdb_get(url, params=None):
    params = dict(params or {})
    params["api_key"] = API_KEY

    for _ in range(4):
        try:
            response = requests.get(url, params=params, timeout=20)

            if response.status_code == 429:
                time.sleep(2)
                continue

            response.raise_for_status()
            return response.json()

        except requests.RequestException:
            time.sleep(1)

    return {}


def validate_new_movies_on_tmdb(con, df_new_movies):
    """
    Prüft neue Filme gegen TMDB.
    Nur bei TMDB gefundene Filme bleiben übrig.
    Nicht gefundene tconst werden aus der DB entfernt.
    Gibt zurück:
      - df_valid_new_movies
      - tmdb_map: {tconst: tmdb_id}
      - deleted_movies_count
    """
    cur = con.cursor()

    valid_indices = []
    tmdb_map = {}
    deleted_movies_count = 0

    for i, row in enumerate(df_new_movies.itertuples(), start=1):
        tconst = row.tconst

        data = tmdb_get(f"{BASE}/find/{tconst}", {"external_source": "imdb_id"})
        time.sleep(PAUSE)

        movie_results = data.get("movie_results") or []

        if not movie_results:
            cur.execute("DELETE FROM movies WHERE tconst = ?", (tconst,))
            if cur.rowcount:
                deleted_movies_count += 1

            cur.execute("DELETE FROM genres WHERE tconst = ?", (tconst,))
            cur.execute("DELETE FROM spoken_languages WHERE tconst = ?", (tconst,))
        else:
            tmdb_map[tconst] = movie_results[0]["id"]
            valid_indices.append(row.Index)

        if i % BATCH_COMMIT == 0:
            con.commit()

    con.commit()

    df_valid_new_movies = df_new_movies.loc[valid_indices].copy()
    return df_valid_new_movies, tmdb_map, deleted_movies_count


def fetch_spoken_languages_for_new_movies(con, tmdb_map):
    cur = con.cursor()
    inserted_language_rows = 0

    for i, (tconst, tmdb_id) in enumerate(tmdb_map.items(), start=1):
        cur.execute(
            "SELECT 1 FROM spoken_languages WHERE tconst = ? LIMIT 1",
            (tconst,)
        )
        if cur.fetchone():
            continue

        data = tmdb_get(f"{BASE}/movie/{tmdb_id}")
        time.sleep(PAUSE)

        langs = data.get("spoken_languages") or []

        for item in langs:
            code = item.get("iso_639_1")
            if code:
                cur.execute("""
                    INSERT OR IGNORE INTO spoken_languages (tconst, sp_languages_iso)
                    VALUES (?, ?)
                """, (tconst, code))
                inserted_language_rows += cur.rowcount

        if i % BATCH_COMMIT == 0:
            con.commit()

    con.commit()
    return inserted_language_rows


def insert_genres_for_new_movies(con, df_new_movies):
    cur = con.cursor()
    inserted_genre_rows = 0
    rows = []

    for _, row in df_new_movies.iterrows():
        tconst = row["tconst"]
        genres_value = row["genres"]

        if pd.isna(genres_value):
            continue

        for genre in str(genres_value).split(","):
            genre = genre.strip()
            if not genre:
                continue

            genre_red = GENRE_RED_MAP.get(genre)
            rows.append((tconst, genre, genre_red))

    if rows:
        cur.executemany("""
            INSERT OR IGNORE INTO genres (tconst, genre, genre_red)
            VALUES (?, ?, ?)
        """, rows)
        inserted_genre_rows = cur.rowcount
        con.commit()

    return inserted_genre_rows


def main():
    start_total = time.time()

    current_year = datetime.now().year
    min_year = current_year - 2

    con = sqlite3.connect(DB)
    cur = con.cursor()

    # ensure tables
    cur.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            tconst TEXT PRIMARY KEY,
            primaryTitle TEXT,
            startYear INTEGER,
            genres TEXT,
            averageRating REAL,
            numVotes INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS spoken_languages (
            tconst TEXT,
            sp_languages_iso TEXT,
            PRIMARY KEY (tconst, sp_languages_iso)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS genres (
            tconst TEXT,
            genre TEXT,
            genre_red TEXT,
            PRIMARY KEY (tconst, genre)
        )
    """)
    con.commit()

    # load data
    df_basics = pd.read_csv(
        "title.basics.tsv.gz",
        sep="\t",
        na_values=r"\N",
        usecols=["tconst", "titleType", "primaryTitle", "startYear", "genres", "isAdult"]
    )

    df_ratings = pd.read_csv(
        "title.ratings.tsv.gz",
        sep="\t",
        na_values=r"\N",
        usecols=["tconst", "averageRating", "numVotes"]
    )

    # filter
    df_basics = df_basics[
        (df_basics["titleType"] == "movie") &
        (df_basics["isAdult"] == 0) &
        (df_basics["startYear"] >= min_year)
    ]

    df_ratings = df_ratings[df_ratings["numVotes"] >= 500]

    df_movies = df_basics.merge(df_ratings, on="tconst", how="inner")

    # determine new movies
    source_ids = tuple(df_movies["tconst"].tolist())

    if source_ids:
        placeholders = ",".join("?" for _ in source_ids)
        cur.execute(f"SELECT tconst FROM movies WHERE tconst IN ({placeholders})", source_ids)
        existing_ids = {row[0] for row in cur.fetchall()}
    else:
        existing_ids = set()

    df_new_movies = df_movies[~df_movies["tconst"].isin(existing_ids)].copy()

    # neue Filme zuerst gegen TMDB validieren
    df_new_movies, tmdb_map, deleted_movies_count = validate_new_movies_on_tmdb(con, df_new_movies)

    valid_new_tconsts = set(df_new_movies["tconst"].tolist())

    # nur valide neue Filme in den finalen Import aufnehmen
    df_movies_final = pd.concat(
        [
            df_movies[df_movies["tconst"].isin(existing_ids)],
            df_new_movies
        ],
        ignore_index=True
    )

    new_count = len(df_new_movies)
    updated_count = len(df_movies_final) - new_count

    # upsert movies
    rows = list(
        df_movies_final[
            ["tconst", "primaryTitle", "startYear", "genres", "averageRating", "numVotes"]
        ].itertuples(index=False, name=None)
    )

    if rows:
        cur.executemany("""
            INSERT INTO movies (tconst, primaryTitle, startYear, genres, averageRating, numVotes)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(tconst) DO UPDATE SET
                primaryTitle = excluded.primaryTitle,
                startYear = excluded.startYear,
                genres = excluded.genres,
                averageRating = excluded.averageRating,
                numVotes = excluded.numVotes
        """, rows)
        con.commit()

    # insert genres for valid new movies only
    inserted_genre_rows = insert_genres_for_new_movies(con, df_new_movies)

    # fetch languages for valid new movies only
    inserted_language_rows = fetch_spoken_languages_for_new_movies(con, tmdb_map)

    # final count
    cur.execute("SELECT COUNT(*) FROM movies")
    total_movies = cur.fetchone()[0]

    con.close()

    print(f"Neue Filme: {new_count}")
    print(f"Aktualisiert: {updated_count}")
    print(f"Entfernt (nicht in TMDB gefunden): {deleted_movies_count}")
    print(f"Neue Genre-Eintraege: {inserted_genre_rows}")
    print(f"Neue Sprach-Eintraege: {inserted_language_rows}")
    print(f"Gesamt Filme: {total_movies}")
    print(f"Laufzeit: {time.time() - start_total:.2f}s")


if __name__ == "__main__":
    main()