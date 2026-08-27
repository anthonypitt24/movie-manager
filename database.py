import sqlite3
import json
import pandas as pd
from contextlib import closing


# ============================================================
# DATABASE SETTINGS
# ============================================================

DB_FILE = "movies.db"


# ============================================================
# CONNECTION
# ============================================================

def get_connection():

    conn = sqlite3.connect(
        DB_FILE,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# DATABASE INITIALISATION
# ============================================================

def init_db():

    with closing(get_connection()) as conn:

        cursor = conn.cursor()

        # ----------------------------------------------------
        # MOVIES
        # ----------------------------------------------------

        cursor.execute("""
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

                date_added TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ----------------------------------------------------
        # DATABASE MIGRATION
        #
        # This makes the app safer if an older movies.db
        # already exists without the newer columns.
        # ----------------------------------------------------

        cursor.execute("""
            PRAGMA table_info(movies)
        """)

        existing_columns = {
            row["name"]
            for row in cursor.fetchall()
        }

        movie_columns = {
            "original_title": "TEXT",
            "overview": "TEXT",
            "release_date": "TEXT",
            "runtime": "INTEGER",
            "vote_average": "REAL",
            "vote_count": "INTEGER",
            "poster_path": "TEXT",
            "backdrop_path": "TEXT",
            "genres": "TEXT",
            "cast": "TEXT",
            "directors": "TEXT",
            "keywords": "TEXT",
            "date_added": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        }

        for column, definition in movie_columns.items():

            if column not in existing_columns:

                try:

                    cursor.execute(
                        f"""
                        ALTER TABLE movies
                        ADD COLUMN {column} {definition}
                        """
                    )

                except sqlite3.OperationalError:
                    pass

        # ----------------------------------------------------
        # USERS
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (

                username TEXT PRIMARY KEY,

                display_name TEXT NOT NULL,

                date_created TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ----------------------------------------------------
        # WATCHED
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watched (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                username TEXT NOT NULL,

                tmdb_id INTEGER NOT NULL,

                date_watched TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(username)
                    REFERENCES users(username),

                FOREIGN KEY(tmdb_id)
                    REFERENCES movies(tmdb_id),

                UNIQUE(username, tmdb_id)
            )
        """)

        # ----------------------------------------------------
        # RATINGS
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ratings (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                username TEXT NOT NULL,

                tmdb_id INTEGER NOT NULL,

                rating REAL NOT NULL,

                review TEXT,

                favourite INTEGER
                    DEFAULT 0,

                date_rated TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(username)
                    REFERENCES users(username),

                FOREIGN KEY(tmdb_id)
                    REFERENCES movies(tmdb_id),

                UNIQUE(username, tmdb_id)
            )
        """)

        # ----------------------------------------------------
        # WATCHLIST
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                username TEXT NOT NULL,

                tmdb_id INTEGER NOT NULL,

                date_added TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(username)
                    REFERENCES users(username),

                FOREIGN KEY(tmdb_id)
                    REFERENCES movies(tmdb_id),

                UNIQUE(username, tmdb_id)
            )
        """)

        # ----------------------------------------------------
        # USER PROFILES
        # ----------------------------------------------------

        cursor.execute("""
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

                last_updated TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(username)
                    REFERENCES users(username)
            )
        """)

        # ----------------------------------------------------
        # DEFAULT USERS
        # ----------------------------------------------------

        cursor.execute("""
            INSERT OR IGNORE INTO users
            (
                username,
                display_name
            )
            VALUES (?, ?)
        """, (
            "Anthony",
            "Anthony"
        ))

        cursor.execute("""
            INSERT OR IGNORE INTO users
            (
                username,
                display_name
            )
            VALUES (?, ?)
        """, (
            "Kseniia",
            "Kseniia"
        ))

        # ----------------------------------------------------
        # DEFAULT PROFILES
        # ----------------------------------------------------

        cursor.execute("""
            INSERT OR IGNORE INTO profiles
            (
                username
            )
            VALUES (?)
        """, (
            "Anthony",
        ))

        cursor.execute("""
            INSERT OR IGNORE INTO profiles
            (
                username
            )
            VALUES (?)
        """, (
            "Kseniia",
        ))

        conn.commit()


# ============================================================
# MOVIES
# ============================================================

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

    # --------------------------------------------------------
    # Convert lists/dictionaries to JSON
    # --------------------------------------------------------

    if isinstance(genres, (list, dict)):
        genres = json.dumps(
            genres,
            ensure_ascii=False
        )

    if isinstance(cast, (list, dict)):
        cast = json.dumps(
            cast,
            ensure_ascii=False
        )

    if isinstance(directors, (list, dict)):
        directors = json.dumps(
            directors,
            ensure_ascii=False
        )

    if isinstance(keywords, (list, dict)):
        keywords = json.dumps(
            keywords,
            ensure_ascii=False
        )

    # --------------------------------------------------------
    # Save movie
    # --------------------------------------------------------

    with closing(get_connection()) as conn:

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO movies
            (
                tmdb_id,
                title,
                original_title,
                overview,
                release_date,
                runtime,
                vote_average,
                vote_count,
                poster_path,
                backdrop_path,
                genres,
                cast,
                directors,
                keywords
            )

            VALUES
            (
                ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?
            )

            ON CONFLICT(tmdb_id)
            DO UPDATE SET

                title =
                    excluded.title,

                original_title =
                    excluded.original_title,

                overview =
                    excluded.overview,

                release_date =
                    excluded.release_date,

                runtime =
                    excluded.runtime,

                vote_average =
                    excluded.vote_average,

                vote_count =
                    excluded.vote_count,

                poster_path =
                    excluded.poster_path,

                backdrop_path =
                    excluded.backdrop_path,

                genres =
                    excluded.genres,

                cast =
                    excluded.cast,

                directors =
                    excluded.directors,

                keywords =
                    excluded.keywords
        """, (
            tmdb_id,
            title,
            original_title,
            overview,
            release_date,
            runtime,
            vote_average,
            vote_count,
            poster_path,
            backdrop_path,
            genres,
            cast,
            directors,
            keywords,
        ))

        conn.commit()


# ============================================================
# GET MOVIE BY TMDB ID
# ============================================================

def get_movie_by_tmdb_id(tmdb_id):

    with closing(get_connection()) as conn:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM movies
            WHERE tmdb_id = ?
        """, (
            int(tmdb_id),
        ))

        row = cursor.fetchone()

        if not row:
            return None

        return dict(row)


# ============================================================
# SEARCH MOVIES IN DATABASE BY TITLE
# ============================================================

def search_movies_by_title(
    title,
    limit=20,
):

    title = str(title).strip()

    if not title:
        return []

    try:
        limit = int(limit)
    except Exception:
        limit = 20

    limit = max(
        1,
        min(
            limit,
            100
        )
    )

    with closing(get_connection()) as conn:

        cursor = conn.cursor()

        cursor.execute(
            f"""
                SELECT *
                FROM movies

                WHERE title LIKE ?

                OR original_title LIKE ?

                ORDER BY
                    CASE
                        WHEN LOWER(title) = LOWER(?)
                        THEN 0
                        WHEN LOWER(title) LIKE LOWER(?)
                        THEN 1
                        ELSE 2
                    END,
                    title

                LIMIT {limit}
            """,
            (
                f"%{title}%",
                f"%{title}%",
                title,
                f"{title}%",
            )
        )

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]


# ============================================================
# GET MOVIE BY EXACT TITLE
# ============================================================

def get_movie_by_title(title):

    title = str(title).strip()

    if not title:
        return None

    with closing(get_connection()) as conn:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM movies

            WHERE LOWER(title) = LOWER(?)

            LIMIT 1
        """, (
            title,
        ))

        row = cursor.fetchone()

        if not row:
            return None

        return dict(row)


# ============================================================
# WATCHLIST
# ============================================================

def add_to_watchlist(
    username,
    tmdb_id,
):

    with closing(get_connection()) as conn:

        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO watchlist
            (
                username,
                tmdb_id
            )

            VALUES (?, ?)
        """, (
            username,
            tmdb_id,
        ))

        conn.commit()


def remove_from_watchlist(
    username,
    tmdb_id,
):

    with closing(get_connection()) as conn:

        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM watchlist

            WHERE username = ?

            AND tmdb_id = ?
        """, (
            username,
            tmdb_id,
        ))

        conn.commit()


def get_watchlist(username):

    with closing(get_connection()) as conn:

        return pd.read_sql_query("""
            SELECT

                w.tmdb_id AS "TMDB_ID",

                m.title AS "Title",

                m.release_date AS "Release Date",

                m.vote_average AS "TMDB Rating",

                w.date_added AS "Added"

            FROM watchlist w

            LEFT JOIN movies m
                ON m.tmdb_id = w.tmdb_id

            WHERE w.username = ?

            ORDER BY w.date_added DESC
        """, conn, params=(username,))


# ============================================================
# WATCHED
# ============================================================

def log_watched_movie(
    users,
    tmdb_id,
):

    if isinstance(users, str):

        users = [users]

    with closing(get_connection()) as conn:

        cursor = conn.cursor()

        for username in users:

            cursor.execute("""
                INSERT OR IGNORE INTO watched
                (
                    username,
                    tmdb_id
                )

                VALUES (?, ?)
            """, (
                username,
                tmdb_id,
            ))

        conn.commit()


def remove_watched_movie(
    username,
    tmdb_id,
):

    with closing(get_connection()) as conn:

        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM watched

            WHERE username = ?

            AND tmdb_id = ?
        """, (
            username,
            tmdb_id,
        ))

        conn.commit()


def get_watch_history(
    username,
    limit=100,
):

    try:

        limit = int(limit)

    except Exception:

        limit = 100

    limit = max(
        1,
        min(
            limit,
            5000
        )
    )

    with closing(get_connection()) as conn:

        return pd.read_sql_query(
            f"""
                SELECT

                    w.tmdb_id AS "TMDB_ID",

                    m.title AS "Title",

                    m.release_date AS "Release Date",

                    m.vote_average AS "TMDB Rating",

                    w.date_watched AS "Date Watched"

                FROM watched w

                LEFT JOIN movies m
                    ON m.tmdb_id = w.tmdb_id

                WHERE w.username = ?

                ORDER BY w.date_watched DESC

                LIMIT {limit}
            """,

            conn,

            params=(username,)
        )


# ============================================================
# RATINGS
# ============================================================

def save_rating(
    username,
    tmdb_id,
    rating,
    review=None,
    favourite=False,
):

    rating = float(rating)

    rating = max(
        0.5,
        min(
            5.0,
            rating
        )
    )

    favourite_value = (
        1
        if favourite
        else 0
    )

    with closing(get_connection()) as conn:

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO ratings
            (
                username,
                tmdb_id,
                rating,
                review,
                favourite
            )

            VALUES (?, ?, ?, ?, ?)

            ON CONFLICT(username, tmdb_id)

            DO UPDATE SET

                rating =
                    excluded.rating,

                review =
                    excluded.review,

                favourite =
                    excluded.favourite,

                date_rated =
                    CURRENT_TIMESTAMP
        """, (
            username,
            tmdb_id,
            rating,
            review,
            favourite_value,
        ))

        # ----------------------------------------------------
        # Rating a movie automatically means watched
        # ----------------------------------------------------

        cursor.execute("""
            INSERT OR IGNORE INTO watched
            (
                username,
                tmdb_id
            )

            VALUES (?, ?)
        """, (
            username,
            tmdb_id,
        ))

        conn.commit()


def get_ratings(username):

    with closing(get_connection()) as conn:

        return pd.read_sql_query("""
            SELECT

                r.tmdb_id AS "TMDB_ID",

                m.title AS "Title",

                r.rating AS "Rating",

                r.review AS "Review",

                r.favourite AS "Favourite",

                r.date_rated AS "Date Rated"

            FROM ratings r

            LEFT JOIN movies m
                ON m.tmdb_id = r.tmdb_id

            WHERE r.username = ?

            ORDER BY r.date_rated DESC
        """, conn, params=(username,))


# ============================================================
# FAVOURITES
# ============================================================

def get_favourites(username):

    with closing(get_connection()) as conn:

        return pd.read_sql_query("""
            SELECT

                r.tmdb_id AS "TMDB_ID",

                m.title AS "Title",

                r.rating AS "Rating",

                r.review AS "Review",

                r.date_rated AS "Date Added"

            FROM ratings r

            LEFT JOIN movies m
                ON m.tmdb_id = r.tmdb_id

            WHERE r.username = ?

            AND r.favourite = 1

            ORDER BY r.date_rated DESC
        """, conn, params=(username,))


def set_favourite(
    username,
    tmdb_id,
    favourite=True,
):

    with closing(get_connection()) as conn:

        cursor = conn.cursor()

        cursor.execute("""
            UPDATE ratings

            SET favourite = ?

            WHERE username = ?

            AND tmdb_id = ?
        """, (
            1 if favourite else 0,
            username,
            tmdb_id,
        ))

        conn.commit()


# ============================================================
# USER PROFILE
# ============================================================

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

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO profiles
            (
                username,
                favourite_genres,
                excluded_genres,
                favourite_actors,
                excluded_actors,
                favourite_directors,
                excluded_directors,
                pacing,
                tone,
                preferred_decades,
                min_runtime,
                max_runtime
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(username)

            DO UPDATE SET

                favourite_genres =
                    excluded.favourite_genres,

                excluded_genres =
                    excluded.excluded_genres,

                favourite_actors =
                    excluded.favourite_actors,

                excluded_actors =
                    excluded.excluded_actors,

                favourite_directors =
                    excluded.favourite_directors,

                excluded_directors =
                    excluded.excluded_directors,

                pacing =
                    excluded.pacing,

                tone =
                    excluded.tone,

                preferred_decades =
                    excluded.preferred_decades,

                min_runtime =
                    excluded.min_runtime,

                max_runtime =
                    excluded.max_runtime,

                last_updated =
                    CURRENT_TIMESTAMP
        """, (

            username,

            json.dumps(
                favourite_genres or [],
                ensure_ascii=False
            ),

            json.dumps(
                excluded_genres or [],
                ensure_ascii=False
            ),

            json.dumps(
                favourite_actors or [],
                ensure_ascii=False
            ),

            json.dumps(
                excluded_actors or [],
                ensure_ascii=False
            ),

            json.dumps(
                favourite_directors or [],
                ensure_ascii=False
            ),

            json.dumps(
                excluded_directors or [],
                ensure_ascii=False
            ),

            pacing,

            json.dumps(
                tone or [],
                ensure_ascii=False
            ),

            json.dumps(
                preferred_decades or [],
                ensure_ascii=False
            ),

            min_runtime,

            max_runtime,
        ))

        conn.commit()


def get_profile(username):

    with closing(get_connection()) as conn:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM profiles
            WHERE username = ?
        """, (
            username,
        ))

        row = cursor.fetchone()

        if not row:
            return None

        data = dict(row)

        json_fields = [
            "favourite_genres",
            "excluded_genres",
            "favourite_actors",
            "excluded_actors",
            "favourite_directors",
            "excluded_directors",
            "tone",
            "preferred_decades",
        ]

        for field in json_fields:

            try:

                data[field] = (
                    json.loads(data[field])
                    if data[field]
                    else []
                )

            except Exception:

                data[field] = []

        return data


# ============================================================
# OLD SURVEY COMPATIBILITY
# ============================================================

def save_profile_survey(
    user,
    fav_genres_ids,
    excl_genres_ids,
    pacing,
    tones,
):

    save_profile(
        username=user,
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
        "favorite_genres":
            profile.get(
                "favourite_genres",
                []
            ),

        "excluded_genres":
            profile.get(
                "excluded_genres",
                []
            ),

        "pacing_pref":
            profile.get(
                "pacing"
            ),

        "tone_tags":
            profile.get(
                "tone",
                []
            ),
    }


# ============================================================
# USER STATISTICS
# ============================================================

def get_user_statistics(username):

    with closing(get_connection()) as conn:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM watched
            WHERE username = ?
        """, (
            username,
        ))

        watched_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM watchlist
            WHERE username = ?
        """, (
            username,
        ))

        watchlist_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM ratings
            WHERE username = ?
        """, (
            username,
        ))

        ratings_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT AVG(rating)
            FROM ratings
            WHERE username = ?
        """, (
            username,
        ))

        average_rating = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM ratings
            WHERE username = ?

            AND favourite = 1
        """, (
            username,
        ))

        favourites_count = cursor.fetchone()[0]

        return {

            "watched":
                watched_count,

            "watchlist":
                watchlist_count,

            "ratings":
                ratings_count,

            "average_rating":
                round(
                    average_rating,
                    2
                )
                if average_rating is not None
                else None,

            "favourites":
                favourites_count,
        }


# ============================================================
# RECOMMENDATION DATA
# ============================================================

def get_liked_movie_ids(username):

    with closing(get_connection()) as conn:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT tmdb_id

            FROM ratings

            WHERE username = ?

            AND rating >= 4
        """, (
            username,
        ))

        return [
            row[0]
            for row in cursor.fetchall()
        ]


def get_disliked_movie_ids(username):

    with closing(get_connection()) as conn:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT tmdb_id

            FROM ratings

            WHERE username = ?

            AND rating <= 2
        """, (
            username,
        ))

        return [
            row[0]
            for row in cursor.fetchall()
        ]


def get_ratings_for_recommendation(username):

    with closing(get_connection()) as conn:

        return pd.read_sql_query("""
            SELECT

                r.tmdb_id AS "TMDB_ID",

                r.rating AS "Rating",

                m.title AS "Title",

                m.genres AS "Genres",

                m.cast AS "Cast",

                m.directors AS "Directors",

                m.keywords AS "Keywords",

                m.runtime AS "Runtime",

                m.release_date AS "Release Date"

            FROM ratings r

            LEFT JOIN movies m
                ON m.tmdb_id = r.tmdb_id

            WHERE r.username = ?

            ORDER BY r.rating DESC
        """, conn, params=(username,))


# ============================================================
# DATABASE HEALTH CHECK
# ============================================================

def database_summary():

    with closing(get_connection()) as conn:

        cursor = conn.cursor()

        tables = [
            "users",
            "movies",
            "watched",
            "ratings",
            "watchlist",
            "profiles",
        ]

        result = {}

        for table in tables:

            cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM {table}
                """
            )

            result[table] = (
                cursor.fetchone()[0]
            )

        return result


# ============================================================
# INITIALISE DATABASE
# ============================================================

init_db()
