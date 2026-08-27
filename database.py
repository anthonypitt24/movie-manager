# ============================================================
# MOVIE MANAGER DATABASE
# Version 2.0
#
# Database foundation for:
# - Anthony
# - Kseniia
# - Movies
# - Watchlists
# - Watch history
# - Ratings
# - Reviews
# - Favourites
# - Genres
# - Actors
# - Directors
# - Keywords
# - Personal taste profiles
# - Two-person recommendations
# ============================================================

import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, List, Dict, Any

import pandas as pd


# ============================================================
# SETTINGS
# ============================================================

DB_FILE = "movies.db"

DEFAULT_USERS = [
    "Anthony",
    "Kseniia",
]


# ============================================================
# DATABASE CONNECTION
# ============================================================

@contextmanager
def get_connection():
    """
    Safely open and close a SQLite connection.
    """

    conn = sqlite3.connect(
        DB_FILE,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 5000")

        yield conn

    finally:
        conn.close()


# ============================================================
# DATABASE INITIALISATION
# ============================================================

def init_db():
    """
    Create all database tables if they don't already exist.
    """

    with get_connection() as conn:

        cursor = conn.cursor()

        # ----------------------------------------------------
        # USERS
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ----------------------------------------------------
        # MOVIES
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                tmdb_id INTEGER NOT NULL UNIQUE,

                title TEXT NOT NULL,
                original_title TEXT,

                overview TEXT,

                release_date TEXT,

                runtime INTEGER,

                vote_average REAL,
                vote_count INTEGER,

                poster_path TEXT,
                backdrop_path TEXT,

                trailer_url TEXT,

                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ----------------------------------------------------
        # GENRES
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS genres (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                tmdb_id INTEGER NOT NULL UNIQUE,

                name TEXT NOT NULL UNIQUE
            )
        """)

        # ----------------------------------------------------
        # MOVIE / GENRE
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movie_genres (
                movie_id INTEGER NOT NULL,
                genre_id INTEGER NOT NULL,

                PRIMARY KEY (movie_id, genre_id),

                FOREIGN KEY (movie_id)
                    REFERENCES movies(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (genre_id)
                    REFERENCES genres(id)
                    ON DELETE CASCADE
            )
        """)

        # ----------------------------------------------------
        # PEOPLE
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                tmdb_id INTEGER NOT NULL UNIQUE,

                name TEXT NOT NULL,

                profile_path TEXT,

                known_for_department TEXT
            )
        """)

        # ----------------------------------------------------
        # MOVIE / PEOPLE
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movie_people (
                movie_id INTEGER NOT NULL,
                person_id INTEGER NOT NULL,

                role TEXT NOT NULL,

                character_name TEXT,

                PRIMARY KEY (movie_id, person_id, role),

                FOREIGN KEY (movie_id)
                    REFERENCES movies(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (person_id)
                    REFERENCES people(id)
                    ON DELETE CASCADE
            )
        """)

        # ----------------------------------------------------
        # KEYWORDS
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                tmdb_id INTEGER NOT NULL UNIQUE,

                name TEXT NOT NULL UNIQUE
            )
        """)

        # ----------------------------------------------------
        # MOVIE / KEYWORDS
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movie_keywords (
                movie_id INTEGER NOT NULL,
                keyword_id INTEGER NOT NULL,

                PRIMARY KEY (movie_id, keyword_id),

                FOREIGN KEY (movie_id)
                    REFERENCES movies(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (keyword_id)
                    REFERENCES keywords(id)
                    ON DELETE CASCADE
            )
        """)

        # ----------------------------------------------------
        # WATCHLIST
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,
                movie_id INTEGER NOT NULL,

                priority INTEGER DEFAULT 3,

                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                notes TEXT,

                UNIQUE(user_id, movie_id),

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (movie_id)
                    REFERENCES movies(id)
                    ON DELETE CASCADE
            )
        """)

        # ----------------------------------------------------
        # WATCH HISTORY
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watch_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                movie_id INTEGER NOT NULL,

                watched_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                viewing_type TEXT DEFAULT 'watched',

                notes TEXT,

                FOREIGN KEY (movie_id)
                    REFERENCES movies(id)
                    ON DELETE CASCADE
            )
        """)

        # ----------------------------------------------------
        # WATCH HISTORY USERS
        #
        # Allows:
        # Anthony
        # Kseniia
        # Anthony + Kseniia
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watch_history_users (
                watch_history_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,

                PRIMARY KEY (watch_history_id, user_id),

                FOREIGN KEY (watch_history_id)
                    REFERENCES watch_history(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)

        # ----------------------------------------------------
        # RATINGS
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,
                movie_id INTEGER NOT NULL,

                rating REAL NOT NULL,

                review TEXT,

                is_favourite INTEGER DEFAULT 0,

                date_rated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(user_id, movie_id),

                CHECK(rating >= 0.5 AND rating <= 5.0),

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (movie_id)
                    REFERENCES movies(id)
                    ON DELETE CASCADE
            )
        """)

        # ----------------------------------------------------
        # MOVIE STATUS
        #
        # want_to_watch
        # watching
        # watched
        # dropped
        # rewatch
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movie_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,
                movie_id INTEGER NOT NULL,

                status TEXT NOT NULL DEFAULT 'want_to_watch',

                date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                UNIQUE(user_id, movie_id),

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (movie_id)
                    REFERENCES movies(id)
                    ON DELETE CASCADE
            )
        """)

        # ----------------------------------------------------
        # USER PROFILES
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,

                pacing_pref TEXT,

                tone_tags TEXT,

                preferred_decades TEXT,

                preferred_certificates TEXT,

                preferred_runtime TEXT,

                favourite_actors TEXT,

                favourite_directors TEXT,

                disliked_actors TEXT,

                disliked_directors TEXT,

                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)

        # ----------------------------------------------------
        # USER FAVOURITE GENRES
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_favourite_genres (
                user_id INTEGER NOT NULL,
                genre_id INTEGER NOT NULL,

                PRIMARY KEY (user_id, genre_id),

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (genre_id)
                    REFERENCES genres(id)
                    ON DELETE CASCADE
            )
        """)

        # ----------------------------------------------------
        # USER EXCLUDED GENRES
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_excluded_genres (
                user_id INTEGER NOT NULL,
                genre_id INTEGER NOT NULL,

                PRIMARY KEY (user_id, genre_id),

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (genre_id)
                    REFERENCES genres(id)
                    ON DELETE CASCADE
            )
        """)

        # ----------------------------------------------------
        # SEARCH HISTORY
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER,

                search_term TEXT NOT NULL,

                search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE SET NULL
            )
        """)

        # ----------------------------------------------------
        # RECOMMENDATION HISTORY
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER,

                movie_id INTEGER NOT NULL,

                recommendation_score REAL,

                reason TEXT,

                date_recommended TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE SET NULL,

                FOREIGN KEY (movie_id)
                    REFERENCES movies(id)
                    ON DELETE CASCADE
            )
        """)

        # ----------------------------------------------------
        # INDEXES
        # ----------------------------------------------------

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_movies_tmdb
            ON movies(tmdb_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ratings_user
            ON ratings(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ratings_movie
            ON ratings(movie_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_watchlist_user
            ON watchlist(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status_user
            ON movie_status(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_movie
            ON watch_history(movie_id)
        """)

        # ----------------------------------------------------
        # DEFAULT USERS
        # ----------------------------------------------------

        for username in DEFAULT_USERS:

            cursor.execute("""
                INSERT OR IGNORE INTO users
                (username, display_name)
                VALUES (?, ?)
            """, (
                username,
                username
            ))

        conn.commit()


# ============================================================
# USER FUNCTIONS
# ============================================================

def get_user(user_name: str):

    with get_connection() as conn:

        return conn.execute("""
            SELECT *
            FROM users
            WHERE username = ?
        """, (
            user_name,
        )).fetchone()


def get_all_users() -> pd.DataFrame:

    with get_connection() as conn:

        return pd.read_sql_query("""
            SELECT
                id,
                username,
                display_name,
                date_created
            FROM users
            ORDER BY display_name
        """, conn)


# ============================================================
# MOVIE FUNCTIONS
# ============================================================

def add_movie(
    tmdb_id: int,
    title: str,
    original_title: Optional[str] = None,
    overview: Optional[str] = None,
    release_date: Optional[str] = None,
    runtime: Optional[int] = None,
    vote_average: Optional[float] = None,
    vote_count: Optional[int] = None,
    poster_path: Optional[str] = None,
    backdrop_path: Optional[str] = None,
    trailer_url: Optional[str] = None
):

    with get_connection() as conn:

        conn.execute("""
            INSERT INTO movies (
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
                trailer_url
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(tmdb_id)
            DO UPDATE SET

                title = excluded.title,
                original_title = excluded.original_title,
                overview = excluded.overview,
                release_date = excluded.release_date,
                runtime = excluded.runtime,
                vote_average = excluded.vote_average,
                vote_count = excluded.vote_count,
                poster_path = excluded.poster_path,
                backdrop_path = excluded.backdrop_path,
                trailer_url = excluded.trailer_url,

                last_updated = CURRENT_TIMESTAMP
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
            trailer_url
        ))

        conn.commit()

        row = conn.execute("""
            SELECT id
            FROM movies
            WHERE tmdb_id = ?
        """, (
            tmdb_id,
        )).fetchone()

        return row["id"]


def get_movie_by_tmdb_id(tmdb_id: int):

    with get_connection() as conn:

        return conn.execute("""
            SELECT *
            FROM movies
            WHERE tmdb_id = ?
        """, (
            tmdb_id,
        )).fetchone()


def get_movie(movie_id: int):

    with get_connection() as conn:

        return conn.execute("""
            SELECT *
            FROM movies
            WHERE id = ?
        """, (
            movie_id,
        )).fetchone()


# ============================================================
# GENRES
# ============================================================

def add_genre(
    tmdb_id: int,
    name: str
):

    with get_connection() as conn:

        conn.execute("""
            INSERT INTO genres (
                tmdb_id,
                name
            )

            VALUES (?, ?)

            ON CONFLICT(tmdb_id)
            DO UPDATE SET
                name = excluded.name
        """, (
            tmdb_id,
            name
        ))

        conn.commit()

        row = conn.execute("""
            SELECT id
            FROM genres
            WHERE tmdb_id = ?
        """, (
            tmdb_id,
        )).fetchone()

        return row["id"]


def attach_genre_to_movie(
    movie_id: int,
    genre_id: int
):

    with get_connection() as conn:

        conn.execute("""
            INSERT OR IGNORE INTO movie_genres
            (
                movie_id,
                genre_id
            )

            VALUES (?, ?)
        """, (
            movie_id,
            genre_id
        ))

        conn.commit()


# ============================================================
# PEOPLE
# ============================================================

def add_person(
    tmdb_id: int,
    name: str,
    profile_path: Optional[str] = None,
    known_for_department: Optional[str] = None
):

    with get_connection() as conn:

        conn.execute("""
            INSERT INTO people (
                tmdb_id,
                name,
                profile_path,
                known_for_department
            )

            VALUES (?, ?, ?, ?)

            ON CONFLICT(tmdb_id)
            DO UPDATE SET

                name = excluded.name,
                profile_path = excluded.profile_path,
                known_for_department =
                    excluded.known_for_department
        """, (
            tmdb_id,
            name,
            profile_path,
            known_for_department
        ))

        conn.commit()

        row = conn.execute("""
            SELECT id
            FROM people
            WHERE tmdb_id = ?
        """, (
            tmdb_id,
        )).fetchone()

        return row["id"]


def attach_person_to_movie(
    movie_id: int,
    person_id: int,
    role: str,
    character_name: Optional[str] = None
):

    with get_connection() as conn:

        conn.execute("""
            INSERT OR REPLACE INTO movie_people
            (
                movie_id,
                person_id,
                role,
                character_name
            )

            VALUES (?, ?, ?, ?)
        """, (
            movie_id,
            person_id,
            role,
            character_name
        ))

        conn.commit()


# ============================================================
# KEYWORDS
# ============================================================

def add_keyword(
    tmdb_id: int,
    name: str
):

    with get_connection() as conn:

        conn.execute("""
            INSERT INTO keywords (
                tmdb_id,
                name
            )

            VALUES (?, ?)

            ON CONFLICT(tmdb_id)
            DO UPDATE SET
                name = excluded.name
        """, (
            tmdb_id,
            name
        ))

        conn.commit()

        row = conn.execute("""
            SELECT id
            FROM keywords
            WHERE tmdb_id = ?
        """, (
            tmdb_id,
        )).fetchone()

        return row["id"]


def attach_keyword_to_movie(
    movie_id: int,
    keyword_id: int
):

    with get_connection() as conn:

        conn.execute("""
            INSERT OR IGNORE INTO movie_keywords
            (
                movie_id,
                keyword_id
            )

            VALUES (?, ?)
        """, (
            movie_id,
            keyword_id
        ))

        conn.commit()


# ============================================================
# WATCHLIST
# ============================================================

def add_to_watchlist(
    user_name: str,
    tmdb_id: int,
    priority: int = 3,
    notes: Optional[str] = None
):

    user = get_user(user_name)
    movie = get_movie_by_tmdb_id(tmdb_id)

    if not user:
        raise ValueError(
            f"User '{user_name}' does not exist."
        )

    if not movie:
        raise ValueError(
            f"Movie with TMDB ID {tmdb_id} "
            f"does not exist."
        )

    priority = max(
        1,
        min(5, int(priority))
    )

    with get_connection() as conn:

        conn.execute("""
            INSERT INTO watchlist (
                user_id,
                movie_id,
                priority,
                notes
            )

            VALUES (?, ?, ?, ?)

            ON CONFLICT(user_id, movie_id)
            DO UPDATE SET

                priority = excluded.priority,
                notes = excluded.notes
        """, (
            user["id"],
            movie["id"],
            priority,
            notes
        ))

        conn.commit()


def remove_from_watchlist(
    user_name: str,
    tmdb_id: int
):

    user = get_user(user_name)
    movie = get_movie_by_tmdb_id(tmdb_id)

    if not user or not movie:
        return

    with get_connection() as conn:

        conn.execute("""
            DELETE FROM watchlist

            WHERE user_id = ?
            AND movie_id = ?
        """, (
            user["id"],
            movie["id"]
        ))

        conn.commit()


def get_watchlist(
    user_name: Optional[str] = None
) -> pd.DataFrame:

    with get_connection() as conn:

        query = """
            SELECT

                u.display_name AS Viewer,

                m.tmdb_id AS TMDB_ID,

                m.title AS Title,

                m.release_date AS Release_Date,

                m.vote_average AS TMDB_Rating,

                w.priority AS Priority,

                w.notes AS Notes,

                w.added_date AS Added

            FROM watchlist w

            JOIN users u
                ON u.id = w.user_id

            JOIN movies m
                ON m.id = w.movie_id
        """

        params = []

        if user_name:

            query += """
                WHERE u.username = ?
            """

            params.append(user_name)

        query += """
            ORDER BY
                w.priority DESC,
                w.added_date DESC
        """

        return pd.read_sql_query(
            query,
            conn,
            params=params
        )


# ============================================================
# MOVIE STATUS
# ============================================================

VALID_STATUSES = {
    "want_to_watch",
    "watching",
    "watched",
    "dropped",
    "rewatch"
}


def set_movie_status(
    user_name: str,
    tmdb_id: int,
    status: str
):

    status = status.lower().strip()

    if status not in VALID_STATUSES:

        raise ValueError(
            f"Invalid status '{status}'. "
            f"Valid statuses: "
            f"{sorted(VALID_STATUSES)}"
        )

    user = get_user(user_name)
    movie = get_movie_by_tmdb_id(tmdb_id)

    if not user or not movie:
        raise ValueError(
            "User or movie not found."
        )

    with get_connection() as conn:

        conn.execute("""
            INSERT INTO movie_status (
                user_id,
                movie_id,
                status
            )

            VALUES (?, ?, ?)

            ON CONFLICT(user_id, movie_id)
            DO UPDATE SET

                status = excluded.status,
                date_updated = CURRENT_TIMESTAMP
        """, (
            user["id"],
            movie["id"],
            status
        ))

        conn.commit()


def get_movie_status(
    user_name: str,
    tmdb_id: int
):

    user = get_user(user_name)
    movie = get_movie_by_tmdb_id(tmdb_id)

    if not user or not movie:
        return None

    with get_connection() as conn:

        row = conn.execute("""
            SELECT status

            FROM movie_status

            WHERE user_id = ?
            AND movie_id = ?
        """, (
            user["id"],
            movie["id"]
        )).fetchone()

        if row:
            return row["status"]

        return None


# ============================================================
# WATCH HISTORY
# ============================================================

def log_watched_movie(
    viewers,
    tmdb_id: int,
    watched_date: Optional[str] = None,
    viewing_type: str = "watched",
    notes: Optional[str] = None
):
    """
    Log a movie being watched.

    Examples:

        log_watched_movie(
            "Anthony",
            123
        )

        log_watched_movie(
            ["Anthony", "Kseniia"],
            123
        )
    """

    if isinstance(viewers, str):
        viewers = [viewers]

    movie = get_movie_by_tmdb_id(tmdb_id)

    if not movie:
        raise ValueError(
            f"Movie with TMDB ID {tmdb_id} "
            f"does not exist."
        )

    if not watched_date:

        watched_date = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    with get_connection() as conn:

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO watch_history (
                movie_id,
                watched_date,
                viewing_type,
                notes
            )

            VALUES (?, ?, ?, ?)
        """, (
            movie["id"],
            watched_date,
            viewing_type,
            notes
        ))

        history_id = cursor.lastrowid

        for viewer in viewers:

            user = get_user(viewer)

            if not user:

                raise ValueError(
                    f"User '{viewer}' does not exist."
                )

            cursor.execute("""
                INSERT INTO watch_history_users
                (
                    watch_history_id,
                    user_id
                )

                VALUES (?, ?)
            """, (
                history_id,
                user["id"]
            ))

            # Automatically mark as watched
            cursor.execute("""
                INSERT INTO movie_status (
                    user_id,
                    movie_id,
                    status
                )

                VALUES (?, ?, 'watched')

                ON CONFLICT(user_id, movie_id)
                DO UPDATE SET

                    status = 'watched',

                    date_updated =
                        CURRENT_TIMESTAMP
            """, (
                user["id"],
                movie["id"]
            ))

            # Remove from watchlist
            cursor.execute("""
                DELETE FROM watchlist

                WHERE user_id = ?
                AND movie_id = ?
            """, (
                user["id"],
                movie["id"]
            ))

        conn.commit()

        return history_id


def get_watch_history(
    user_name: Optional[str] = None,
    limit: int = 50
) -> pd.DataFrame:

    limit = max(
        1,
        min(int(limit), 1000)
    )

    with get_connection() as conn:

        query = """
            SELECT

                wh.id AS Watch_ID,

                m.tmdb_id AS TMDB_ID,

                m.title AS Title,

                GROUP_CONCAT(
                    DISTINCT u.display_name
                ) AS Viewers,

                wh.viewing_type AS Type,

                wh.watched_date AS Watched,

                wh.notes AS Notes

            FROM watch_history wh

            JOIN movies m
                ON m.id = wh.movie_id

            JOIN watch_history_users whu
                ON whu.watch_history_id = wh.id

            JOIN users u
                ON u.id = whu.user_id
        """

        params = []

        if user_name:

            query += """
                WHERE wh.id IN (

                    SELECT
                        whu2.watch_history_id

                    FROM watch_history_users whu2

                    JOIN users u2
                        ON u2.id = whu2.user_id

                    WHERE u2.username = ?
                )
            """

            params.append(user_name)

        query += """
            GROUP BY wh.id

            ORDER BY wh.id DESC

            LIMIT ?
        """

        params.append(limit)

        return pd.read_sql_query(
            query,
            conn,
            params=params
        )


# ============================================================
# RATINGS
# ============================================================

def save_rating(
    user_name: str,
    tmdb_id: int,
    rating: float,
    review: Optional[str] = None,
    is_favourite: bool = False
):

    rating = float(rating)

    if rating < 0.5 or rating > 5.0:

        raise ValueError(
            "Rating must be between "
            "0.5 and 5.0."
        )

    user = get_user(user_name)
    movie = get_movie_by_tmdb_id(tmdb_id)

    if not user or not movie:

        raise ValueError(
            "User or movie not found."
        )

    with get_connection() as conn:

        conn.execute("""
            INSERT INTO ratings (
                user_id,
                movie_id,
                rating,
                review,
                is_favourite
            )

            VALUES (?, ?, ?, ?, ?)

            ON CONFLICT(user_id, movie_id)
            DO UPDATE SET

                rating = excluded.rating,

                review = excluded.review,

                is_favourite =
                    excluded.is_favourite,

                last_updated =
                    CURRENT_TIMESTAMP
        """, (
            user["id"],
            movie["id"],
            rating,
            review,
            int(is_favourite)
        ))

        conn.commit()


def get_user_rating(
    user_name: str,
    tmdb_id: int
):

    user = get_user(user_name)
    movie = get_movie_by_tmdb_id(tmdb_id)

    if not user or not movie:
        return None

    with get_connection() as conn:

        row = conn.execute("""
            SELECT

                rating,
                review,
                is_favourite

            FROM ratings

            WHERE user_id = ?
            AND movie_id = ?
        """, (
            user["id"],
            movie["id"]
        )).fetchone()

        if not row:
            return None

        return {
            "rating": row["rating"],
            "review": row["review"],
            "is_favourite":
                bool(row["is_favourite"])
        }


def get_ratings(
    user_name: Optional[str] = None
) -> pd.DataFrame:

    with get_connection() as conn:

        query = """
            SELECT

                u.display_name AS Viewer,

                m.tmdb_id AS TMDB_ID,

                m.title AS Title,

                r.rating AS Rating,

                r.review AS Review,

                r.is_favourite AS Favourite,

                r.date_rated AS Date_Rated

            FROM ratings r

            JOIN users u
                ON u.id = r.user_id

            JOIN movies m
                ON m.id = r.movie_id
        """

        params = []

        if user_name:

            query += """
                WHERE u.username = ?
            """

            params.append(user_name)

        query += """
            ORDER BY r.last_updated DESC
        """

        return pd.read_sql_query(
            query,
            conn,
            params=params
        )


# ============================================================
# FAVOURITES
# ============================================================

def set_favourite(
    user_name: str,
    tmdb_id: int,
    favourite: bool = True
):

    user = get_user(user_name)
    movie = get_movie_by_tmdb_id(tmdb_id)

    if not user or not movie:
        raise ValueError(
            "User or movie not found."
        )

    with get_connection() as conn:

        conn.execute("""
            UPDATE ratings

            SET

                is_favourite = ?,

                last_updated =
                    CURRENT_TIMESTAMP

            WHERE user_id = ?
            AND movie_id = ?
        """, (
            int(favourite),
            user["id"],
            movie["id"]
        ))

        conn.commit()


def get_favourites(
    user_name: str
) -> pd.DataFrame:

    with get_connection() as conn:

        return pd.read_sql_query("""
            SELECT

                m.tmdb_id AS TMDB_ID,

                m.title AS Title,

                r.rating AS Rating,

                r.review AS Review,

                m.poster_path AS Poster

            FROM ratings r

            JOIN users u
                ON u.id = r.user_id

            JOIN movies m
                ON m.id = r.movie_id

            WHERE u.username = ?

            AND r.is_favourite = 1

            ORDER BY r.rating DESC
        """, (
            conn,
            user_name
        ))


# ============================================================
# USER PROFILE
# ============================================================

def save_user_profile(
    user_name: str,
    pacing: Optional[str] = None,
    tones: Optional[List[str]] = None,
    decades: Optional[List[str]] = None,
    certificates: Optional[List[str]] = None,
    runtime: Optional[str] = None,
    favourite_actors: Optional[List[str]] = None,
    favourite_directors: Optional[List[str]] = None,
    disliked_actors: Optional[List[str]] = None,
    disliked_directors: Optional[List[str]] = None
):

    user = get_user(user_name)

    if not user:

        raise ValueError(
            f"User '{user_name}' does not exist."
        )

    with get_connection() as conn:

        conn.execute("""
            INSERT INTO user_profiles (

                user_id,

                pacing_pref,

                tone_tags,

                preferred_decades,

                preferred_certificates,

                preferred_runtime,

                favourite_actors,

                favourite_directors,

                disliked_actors,

                disliked_directors

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(user_id)
            DO UPDATE SET

                pacing_pref =
                    excluded.pacing_pref,

                tone_tags =
                    excluded.tone_tags,

                preferred_decades =
                    excluded.preferred_decades,

                preferred_certificates =
                    excluded.preferred_certificates,

                preferred_runtime =
                    excluded.preferred_runtime,

                favourite_actors =
                    excluded.favourite_actors,

                favourite_directors =
                    excluded.favourite_directors,

                disliked_actors =
                    excluded.disliked_actors,

                disliked_directors =
                    excluded.disliked_directors,

                last_updated =
                    CURRENT_TIMESTAMP
        """, (
            user["id"],
            pacing,
            json.dumps(tones or []),
            json.dumps(decades or []),
            json.dumps(certificates or []),
            runtime,
            json.dumps(favourite_actors or []),
            json.dumps(favourite_directors or []),
            json.dumps(disliked_actors or []),
            json.dumps(disliked_directors or [])
        ))

        conn.commit()


def get_user_profile(
    user_name: str
):

    user = get_user(user_name)

    if not user:
        return None

    with get_connection() as conn:

        row = conn.execute("""
            SELECT *

            FROM user_profiles

            WHERE user_id = ?
        """, (
            user["id"],
        )).fetchone()

        if not row:
            return None

        return {

            "pacing":
                row["pacing_pref"],

            "tones":
                json.loads(
                    row["tone_tags"] or "[]"
                ),

            "decades":
                json.loads(
                    row["preferred_decades"] or "[]"
                ),

            "certificates":
                json.loads(
                    row["preferred_certificates"] or "[]"
                ),

            "runtime":
                row["preferred_runtime"],

            "favourite_actors":
                json.loads(
                    row["favourite_actors"] or "[]"
                ),

            "favourite_directors":
                json.loads(
                    row["favourite_directors"] or "[]"
                ),

            "disliked_actors":
                json.loads(
                    row["disliked_actors"] or "[]"
                ),

            "disliked_directors":
                json.loads(
                    row["disliked_directors"] or "[]"
                )
        }


# ============================================================
# PROFILE GENRES
# ============================================================

def set_favourite_genres(
    user_name: str,
    genre_ids: List[int]
):

    user = get_user(user_name)

    if not user:
        raise ValueError(
            "User not found."
        )

    with get_connection() as conn:

        conn.execute("""
            DELETE FROM user_favourite_genres

            WHERE user_id = ?
        """, (
            user["id"],
        ))

        for genre_id in genre_ids:

            conn.execute("""
                INSERT OR IGNORE INTO
                user_favourite_genres
                (
                    user_id,
                    genre_id
                )

                VALUES (?, ?)
            """, (
                user["id"],
                genre_id
            ))

        conn.commit()


def set_excluded_genres(
    user_name: str,
    genre_ids: List[int]
):

    user = get_user(user_name)

    if not user:
        raise ValueError(
            "User not found."
        )

    with get_connection() as conn:

        conn.execute("""
            DELETE FROM user_excluded_genres

            WHERE user_id = ?
        """, (
            user["id"],
        ))

        for genre_id in genre_ids:

            conn.execute("""
                INSERT OR IGNORE INTO
                user_excluded_genres
                (
                    user_id,
                    genre_id
                )

                VALUES (?, ?)
            """, (
                user["id"],
                genre_id
            ))

        conn.commit()


# ============================================================
# SEARCH HISTORY
# ============================================================

def log_search(
    user_name: Optional[str],
    search_term: str
):

    user_id = None

    if user_name:

        user = get_user(user_name)

        if user:
            user_id = user["id"]

    with get_connection() as conn:

        conn.execute("""
            INSERT INTO search_history
            (
                user_id,
                search_term
            )

            VALUES (?, ?)
        """, (
            user_id,
            search_term
        ))

        conn.commit()


# ============================================================
# SHARED MOVIES
# ============================================================

def get_shared_watched_movies() -> pd.DataFrame:

    with get_connection() as conn:

        return pd.read_sql_query("""
            SELECT

                m.tmdb_id AS TMDB_ID,

                m.title AS Title,

                MAX(
                    CASE
                        WHEN u.username = 'Anthony'
                        THEN r.rating
                    END
                ) AS Anthony_Rating,

                MAX(
                    CASE
                        WHEN u.username = 'Kseniia'
                        THEN r.rating
                    END
                ) AS Kseniia_Rating

            FROM movies m

            JOIN watch_history wh
                ON wh.movie_id = m.id

            JOIN watch_history_users whu
                ON whu.watch_history_id = wh.id

            JOIN users u
                ON u.id = whu.user_id

            LEFT JOIN ratings r
                ON r.movie_id = m.id
                AND r.user_id = u.id

            WHERE u.username IN (
                'Anthony',
                'Kseniia'
            )

            GROUP BY
                m.id,
                m.tmdb_id,
                m.title

            HAVING COUNT(
                DISTINCT u.username
            ) = 2

            ORDER BY m.title
        """, conn)


# ============================================================
# COMPATIBILITY
# ============================================================

def calculate_movie_compatibility(
    tmdb_id: int
) -> Optional[float]:

    with get_connection() as conn:

        rows = conn.execute("""
            SELECT

                u.username,

                r.rating

            FROM ratings r

            JOIN users u
                ON u.id = r.user_id

            JOIN movies m
                ON m.id = r.movie_id

            WHERE m.tmdb_id = ?

            AND u.username IN (
                'Anthony',
                'Kseniia'
            )
        """, (
            tmdb_id,
        )).fetchall()

        ratings = {
            row["username"]:
                row["rating"]
            for row in rows
        }

        if "Anthony" not in ratings:
            return None

        if "Kseniia" not in ratings:
            return None

        difference = abs(
            ratings["Anthony"] -
            ratings["Kseniia"]
        )

        compatibility = (
            1 -
            (difference / 4.5)
        ) * 100

        return round(
            max(
                0,
                min(
                    100,
                    compatibility
                )
            ),
            1
        )


# ============================================================
# RECOMMENDATION HISTORY
# ============================================================

def save_recommendation(
    tmdb_id: int,
    score: float,
    reason: str,
    user_name: Optional[str] = None
):

    movie = get_movie_by_tmdb_id(tmdb_id)

    if not movie:
        raise ValueError(
            "Movie not found."
        )

    user_id = None

    if user_name:

        user = get_user(user_name)

        if user:
            user_id = user["id"]

    with get_connection() as conn:

        conn.execute("""
            INSERT INTO recommendation_history (
                user_id,
                movie_id,
                recommendation_score,
                reason
            )

            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            movie["id"],
            score,
            reason
        ))

        conn.commit()


# ============================================================
# MOVIE DASHBOARD
# ============================================================

def get_movie_dashboard(
    user_name: Optional[str] = None
) -> pd.DataFrame:

    with get_connection() as conn:

        if user_name:

            query = """
                SELECT

                    m.tmdb_id AS TMDB_ID,

                    m.title AS Title,

                    m.release_date AS Release_Date,

                    m.vote_average AS TMDB_Rating,

                    r.rating AS Personal_Rating,

                    r.is_favourite AS Favourite,

                    ms.status AS Status,

                    m.poster_path AS Poster

                FROM movies m

                LEFT JOIN ratings r

                    ON r.movie_id = m.id

                    AND r.user_id = (
                        SELECT id
                        FROM users
                        WHERE username = ?
                    )

                LEFT JOIN movie_status ms

                    ON ms.movie_id = m.id

                    AND ms.user_id = (
                        SELECT id
                        FROM users
                        WHERE username = ?
                    )

                ORDER BY m.title
            """

            params = [
                user_name,
                user_name
            ]

        else:

            query = """
                SELECT

                    m.tmdb_id AS TMDB_ID,

                    m.title AS Title,

                    m.release_date AS Release_Date,

                    m.vote_average AS TMDB_Rating,

                    m.poster_path AS Poster

                FROM movies m

                ORDER BY m.title
            """

            params = []

        return pd.read_sql_query(
            query,
            conn,
            params=params
        )


# ============================================================
# STATISTICS
# ============================================================

def get_user_statistics(
    user_name: str
) -> Dict[str, Any]:

    user = get_user(user_name)

    if not user:
        raise ValueError(
            "User not found."
        )

    with get_connection() as conn:

        watched = conn.execute("""
            SELECT COUNT(
                DISTINCT wh.movie_id
            )

            FROM watch_history wh

            JOIN watch_history_users whu
                ON whu.watch_history_id = wh.id

            WHERE whu.user_id = ?
        """, (
            user["id"],
        )).fetchone()[0]

        watchlist = conn.execute("""
            SELECT COUNT(*)

            FROM watchlist

            WHERE user_id = ?
        """, (
            user["id"],
        )).fetchone()[0]

        rated = conn.execute("""
            SELECT COUNT(*)

            FROM ratings

            WHERE user_id = ?
        """, (
            user["id"],
        )).fetchone()[0]

        favourites = conn.execute("""
            SELECT COUNT(*)

            FROM ratings

            WHERE user_id = ?

            AND is_favourite = 1
        """, (
            user["id"],
        )).fetchone()[0]

        average_rating = conn.execute("""
            SELECT AVG(rating)

            FROM ratings

            WHERE user_id = ?
        """, (
            user["id"],
        )).fetchone()[0]

        return {

            "watched":
                watched or 0,

            "watchlist":
                watchlist or 0,

            "rated":
                rated or 0,

            "favourites":
                favourites or 0,

            "average_rating":
                (
                    round(
                        average_rating,
                        2
                    )
                    if average_rating
                    is not None
                    else None
                )
        }


# ============================================================
# DATABASE BACKUP
# ============================================================

def backup_database(
    backup_file: str = "movies_backup.db"
):

    with get_connection() as source:

        destination = sqlite3.connect(
            backup_file
        )

        try:

            source.backup(
                destination
            )

        finally:

            destination.close()


# ============================================================
# DATABASE HEALTH CHECK
# ============================================================

def database_health_check() -> Dict[str, Any]:

    with get_connection() as conn:

        tables = conn.execute("""
            SELECT name

            FROM sqlite_master

            WHERE type = 'table'

            ORDER BY name
        """).fetchall()

        movie_count = conn.execute("""
            SELECT COUNT(*)
            FROM movies
        """).fetchone()[0]

        user_count = conn.execute("""
            SELECT COUNT(*)
            FROM users
        """).fetchone()[0]

        rating_count = conn.execute("""
            SELECT COUNT(*)
            FROM ratings
        """).fetchone()[0]

        watch_history_count = conn.execute("""
            SELECT COUNT(*)
            FROM watch_history
        """).fetchone()[0]

        return {

            "database":
                DB_FILE,

            "tables":
                [
                    row["name"]
                    for row in tables
                ],

            "users":
                user_count,

            "movies":
                movie_count,

            "ratings":
                rating_count,

            "watch_history":
                watch_history_count
        }


# ============================================================
# START DATABASE
# ============================================================

if __name__ == "__main__":

    init_db()

    print()
    print("=" * 60)
    print("MOVIE MANAGER DATABASE")
    print("=" * 60)

    health = database_health_check()

    print(
        f"Database: {health['database']}"
    )

    print(
        f"Users: {health['users']}"
    )

    print(
        f"Movies: {health['movies']}"
    )

    print(
        f"Ratings: {health['ratings']}"
    )

    print(
        f"Watch history: "
        f"{health['watch_history']}"
    )

    print()
    print("Users:")

    users = get_all_users()

    if users.empty:

        print("No users found.")

    else:

        for _, row in users.iterrows():

            print(
                f"  - {row['display_name']}"
            )

    print()
    print(
        "Database initialised successfully."
    )

    print("=" * 60)
