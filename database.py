import sqlite3
import json
import pandas as pd
from contextlib import closing

DB_FILE = "movies.db"


def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _add_column_if_missing(conn, table, column, definition):
    columns = {
        row[1]
        for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    with closing(get_connection()) as conn:
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                tmdb_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                original_title TEXT,
                overview TEXT,
                release_date TEXT,
                runtime INTEGER,
                vote_average REAL,
                vote_count INTEGER,
                poster_path TEXT,
                backdrop_path TEXT,
                genres TEXT,
                cast TEXT,
                directors TEXT,
                keywords TEXT,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Upgrade older movies.db files safely.
        for column, definition in [
            ("original_title", "TEXT"),
            ("overview", "TEXT"),
            ("release_date", "TEXT"),
            ("runtime", "INTEGER"),
            ("vote_average", "REAL"),
            ("vote_count", "INTEGER"),
            ("poster_path", "TEXT"),
            ("backdrop_path", "TEXT"),
            ("genres", "TEXT"),
            ("cast", "TEXT"),
            ("directors", "TEXT"),
            ("keywords", "TEXT"),
            ("date_added", "TIMESTAMP"),
        ]:
            _add_column_if_missing(conn, "movies", column, definition)

        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS watched (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                tmdb_id INTEGER NOT NULL,
                date_watched TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(username) REFERENCES users(username),
                FOREIGN KEY(tmdb_id) REFERENCES movies(tmdb_id),
                UNIQUE(username, tmdb_id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                tmdb_id INTEGER NOT NULL,
                rating REAL NOT NULL,
                review TEXT,
                favourite INTEGER DEFAULT 0,
                date_rated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(username) REFERENCES users(username),
                FOREIGN KEY(tmdb_id) REFERENCES movies(tmdb_id),
                UNIQUE(username, tmdb_id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                tmdb_id INTEGER NOT NULL,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(username) REFERENCES users(username),
                FOREIGN KEY(tmdb_id) REFERENCES movies(tmdb_id),
                UNIQUE(username, tmdb_id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                username TEXT PRIMARY KEY,
                favourite_genres TEXT,
                excluded_genres TEXT,
                favourite_actors TEXT,
                excluded_actors TEXT,
                favourite_directors TEXT,
                excluded_directors TEXT,
                pacing TEXT,
                tone TEXT,
                preferred_decades TEXT,
                min_runtime INTEGER,
                max_runtime INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(username) REFERENCES users(username)
            )
        """)

        # Upgrade older profile tables.
        for column, definition in [
            ("favourite_genres", "TEXT"),
            ("excluded_genres", "TEXT"),
            ("favourite_actors", "TEXT"),
            ("excluded_actors", "TEXT"),
            ("favourite_directors", "TEXT"),
            ("excluded_directors", "TEXT"),
            ("pacing", "TEXT"),
            ("tone", "TEXT"),
            ("preferred_decades", "TEXT"),
            ("min_runtime", "INTEGER"),
            ("max_runtime", "INTEGER"),
            ("last_updated", "TIMESTAMP"),
        ]:
            _add_column_if_missing(conn, "profiles", column, definition)

        for username in ("Anthony", "Kseniia"):
            c.execute(
                "INSERT OR IGNORE INTO users(username, display_name) VALUES (?, ?)",
                (username, username),
            )
            c.execute(
                "INSERT OR IGNORE INTO profiles(username) VALUES (?)",
                (username,),
            )

        conn.commit()


def add_movie(
    tmdb_id,
    title,
    original_title=None,
    overview=None,
    release_date=None,
    runtime=None,
    vote_average=None,
    vote_count=None,
    poster_path=None,
    backdrop_path=None,
    genres=None,
    cast=None,
    directors=None,
    keywords=None,
):
    def serialise(value):
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        return value

    with closing(get_connection()) as conn:
        conn.execute("""
            INSERT INTO movies (
                tmdb_id, title, original_title, overview, release_date,
                runtime, vote_average, vote_count, poster_path,
                backdrop_path, genres, cast, directors, keywords
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(tmdb_id) DO UPDATE SET
                title=excluded.title,
                original_title=excluded.original_title,
                overview=excluded.overview,
                release_date=excluded.release_date,
                runtime=excluded.runtime,
                vote_average=excluded.vote_average,
                vote_count=excluded.vote_count,
                poster_path=excluded.poster_path,
                backdrop_path=excluded.backdrop_path,
                genres=excluded.genres,
                cast=excluded.cast,
                directors=excluded.directors,
                keywords=excluded.keywords
        """, (
            tmdb_id, title, original_title, overview, release_date,
            runtime, vote_average, vote_count, poster_path,
            backdrop_path, serialise(genres), serialise(cast),
            serialise(directors), serialise(keywords),
        ))
        conn.commit()


def get_movie_by_tmdb_id(tmdb_id):
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT * FROM movies WHERE tmdb_id = ?", (tmdb_id,)
        ).fetchone()
        return dict(row) if row else None


def add_to_watchlist(username, tmdb_id):
    with closing(get_connection()) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watchlist(username, tmdb_id) VALUES (?, ?)",
            (username, tmdb_id),
        )
        conn.commit()


def remove_from_watchlist(username, tmdb_id):
    with closing(get_connection()) as conn:
        conn.execute(
            "DELETE FROM watchlist WHERE username=? AND tmdb_id=?",
            (username, tmdb_id),
        )
        conn.commit()


def get_watchlist(username):
    with closing(get_connection()) as conn:
        return pd.read_sql_query("""
            SELECT w.tmdb_id AS "TMDB_ID",
                   m.title AS "Title",
                   m.release_date AS "Release Date",
                   m.vote_average AS "TMDB Rating",
                   w.date_added AS "Added"
            FROM watchlist w
            LEFT JOIN movies m ON m.tmdb_id=w.tmdb_id
            WHERE w.username=?
            ORDER BY w.date_added DESC
        """, conn, params=(username,))


def log_watched_movie(users, tmdb_id):
    if isinstance(users, str):
        users = [users]

    with closing(get_connection()) as conn:
        for username in users:
            conn.execute(
                "INSERT OR IGNORE INTO watched(username, tmdb_id) VALUES (?, ?)",
                (username, tmdb_id),
            )
        conn.commit()


def remove_watched_movie(username, tmdb_id):
    with closing(get_connection()) as conn:
        conn.execute(
            "DELETE FROM watched WHERE username=? AND tmdb_id=?",
            (username, tmdb_id),
        )
        conn.commit()


def get_watch_history(username, limit=100):
    try:
        limit = int(limit)
    except Exception:
        limit = 100
    limit = max(1, min(limit, 5000))

    with closing(get_connection()) as conn:
        return pd.read_sql_query(f"""
            SELECT w.tmdb_id AS "TMDB_ID",
                   m.title AS "Title",
                   m.release_date AS "Release Date",
                   m.vote_average AS "TMDB Rating",
                   w.date_watched AS "Date Watched"
            FROM watched w
            LEFT JOIN movies m ON m.tmdb_id=w.tmdb_id
            WHERE w.username=?
            ORDER BY w.date_watched DESC
            LIMIT {limit}
        """, conn, params=(username,))


def save_rating(username, tmdb_id, rating, review=None, favourite=False):
    rating = max(0.5, min(5.0, float(rating)))
    favourite_value = 1 if favourite else 0

    with closing(get_connection()) as conn:
        conn.execute("""
            INSERT INTO ratings(
                username, tmdb_id, rating, review, favourite
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(username, tmdb_id) DO UPDATE SET
                rating=excluded.rating,
                review=excluded.review,
                favourite=excluded.favourite,
                date_rated=CURRENT_TIMESTAMP
        """, (
            username, tmdb_id, rating, review, favourite_value
        ))

        conn.execute(
            "INSERT OR IGNORE INTO watched(username, tmdb_id) VALUES (?, ?)",
            (username, tmdb_id),
        )
        conn.commit()


def get_ratings(username):
    with closing(get_connection()) as conn:
        return pd.read_sql_query("""
            SELECT r.tmdb_id AS "TMDB_ID",
                   m.title AS "Title",
                   r.rating AS "Rating",
                   r.review AS "Review",
                   r.favourite AS "Favourite",
                   r.date_rated AS "Date Rated"
            FROM ratings r
            LEFT JOIN movies m ON m.tmdb_id=r.tmdb_id
            WHERE r.username=?
            ORDER BY r.date_rated DESC
        """, conn, params=(username,))


def get_favourites(username):
    with closing(get_connection()) as conn:
        return pd.read_sql_query("""
            SELECT r.tmdb_id AS "TMDB_ID",
                   m.title AS "Title",
                   r.rating AS "Rating",
                   r.review AS "Review",
                   r.date_rated AS "Date Added"
            FROM ratings r
            LEFT JOIN movies m ON m.tmdb_id=r.tmdb_id
            WHERE r.username=? AND r.favourite=1
            ORDER BY r.date_rated DESC
        """, conn, params=(username,))


def set_favourite(username, tmdb_id, favourite=True):
    with closing(get_connection()) as conn:
        conn.execute(
            "UPDATE ratings SET favourite=? WHERE username=? AND tmdb_id=?",
            (1 if favourite else 0, username, tmdb_id),
        )
        conn.commit()


def save_profile(
    username,
    favourite_genres=None,
    excluded_genres=None,
    favourite_actors=None,
    excluded_actors=None,
    favourite_directors=None,
    excluded_directors=None,
    pacing=None,
    tone=None,
    preferred_decades=None,
    min_runtime=None,
    max_runtime=None,
):
    with closing(get_connection()) as conn:
        conn.execute("""
            INSERT INTO profiles(
                username, favourite_genres, excluded_genres,
                favourite_actors, excluded_actors,
                favourite_directors, excluded_directors,
                pacing, tone, preferred_decades,
                min_runtime, max_runtime
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                favourite_genres=excluded.favourite_genres,
                excluded_genres=excluded.excluded_genres,
                favourite_actors=excluded.favourite_actors,
                excluded_actors=excluded.excluded_actors,
                favourite_directors=excluded.favourite_directors,
                excluded_directors=excluded.excluded_directors,
                pacing=excluded.pacing,
                tone=excluded.tone,
                preferred_decades=excluded.preferred_decades,
                min_runtime=excluded.min_runtime,
                max_runtime=excluded.max_runtime,
                last_updated=CURRENT_TIMESTAMP
        """, (
            username,
            json.dumps(favourite_genres or []),
            json.dumps(excluded_genres or []),
            json.dumps(favourite_actors or []),
            json.dumps(excluded_actors or []),
            json.dumps(favourite_directors or []),
            json.dumps(excluded_directors or []),
            pacing,
            json.dumps(tone or []),
            json.dumps(preferred_decades or []),
            min_runtime,
            max_runtime,
        ))
        conn.commit()


def get_profile(username):
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT * FROM profiles WHERE username=?", (username,)
        ).fetchone()

    if not row:
        return None

    data = dict(row)
    for field in (
        "favourite_genres", "excluded_genres",
        "favourite_actors", "excluded_actors",
        "favourite_directors", "excluded_directors",
        "tone", "preferred_decades",
    ):
        try:
            data[field] = json.loads(data[field]) if data[field] else []
        except Exception:
            data[field] = []
    return data


def save_profile_survey(user, fav_genres_ids, excl_genres_ids, pacing, tones):
    save_profile(
        user,
        favourite_genres=fav_genres_ids,
        excluded_genres=excl_genres_ids,
        pacing=pacing,
        tone=tones,
    )


def get_profile_survey(user):
    profile = get_profile(user)
    if not profile:
        return None
    return {
        "favorite_genres": profile.get("favourite_genres", []),
        "excluded_genres": profile.get("excluded_genres", []),
        "pacing_pref": profile.get("pacing"),
        "tone_tags": profile.get("tone", []),
    }


def get_user_statistics(username):
    with closing(get_connection()) as conn:
        watched = conn.execute(
            "SELECT COUNT(*) FROM watched WHERE username=?", (username,)
        ).fetchone()[0]
        watchlist = conn.execute(
            "SELECT COUNT(*) FROM watchlist WHERE username=?", (username,)
        ).fetchone()[0]
        ratings = conn.execute(
            "SELECT COUNT(*) FROM ratings WHERE username=?", (username,)
        ).fetchone()[0]
        average = conn.execute(
            "SELECT AVG(rating) FROM ratings WHERE username=?", (username,)
        ).fetchone()[0]
        favourites = conn.execute(
            "SELECT COUNT(*) FROM ratings WHERE username=? AND favourite=1",
            (username,),
        ).fetchone()[0]

    return {
        "watched": watched,
        "watchlist": watchlist,
        "ratings": ratings,
        "average_rating": round(average, 2) if average is not None else None,
        "favourites": favourites,
    }


def get_liked_movie_ids(username):
    with closing(get_connection()) as conn:
        return [
            row[0] for row in conn.execute(
                "SELECT tmdb_id FROM ratings WHERE username=? AND rating>=4",
                (username,),
            ).fetchall()
        ]


def get_disliked_movie_ids(username):
    with closing(get_connection()) as conn:
        return [
            row[0] for row in conn.execute(
                "SELECT tmdb_id FROM ratings WHERE username=? AND rating<=2",
                (username,),
            ).fetchall()
        ]


def get_ratings_for_recommendation(username):
    with closing(get_connection()) as conn:
        return pd.read_sql_query("""
            SELECT r.tmdb_id AS "TMDB_ID",
                   r.rating AS "Rating",
                   m.title AS "Title",
                   m.genres AS "Genres",
                   m.cast AS "Cast",
                   m.directors AS "Directors",
                   m.keywords AS "Keywords",
                   m.runtime AS "Runtime",
                   m.release_date AS "Release Date"
            FROM ratings r
            LEFT JOIN movies m ON m.tmdb_id=r.tmdb_id
            WHERE r.username=?
            ORDER BY r.rating DESC
        """, conn, params=(username,))


def database_summary():
    tables = ["users", "movies", "watched", "ratings", "watchlist", "profiles"]
    with closing(get_connection()) as conn:
        return {
            table: conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            for table in tables
        }


init_db()
