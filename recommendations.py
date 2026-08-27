import json

from database import (
    get_ratings,
    get_watchlist,
    get_watch_history,
    get_profile,
)

from tmdb import (
    get_movie_recommendations,
    get_similar_movies,
    get_movie_details,
    get_discover_movies,
)


# ============================================================
# STARTING TASTE PROFILES
# ============================================================

STARTING_PROFILES = {

    "Anthony": {
        "genres": [
            28,     # Action
            53,     # Thriller
            80,     # Crime
            9648,   # Mystery
            18,     # Drama
        ],

        "keywords": [
            "crime",
            "true crime",
            "investigation",
            "murder",
            "conspiracy",
            "psychological",
            "serial killer",
            "revenge",
            "detective",
        ],
    },

    "Kseniia": {
        "genres": [
            10749,  # Romance
            35,     # Comedy
            18,     # Drama
        ],

        "keywords": [
            "romance",
            "love",
            "relationship",
            "beautiful",
            "emotional",
            "chemistry",
            "seduction",
            "passion",
        ],
    },
}


# ============================================================
# HELPERS
# ============================================================

def safe_json(value):

    if not value:
        return []

    if isinstance(value, list):
        return value

    try:
        return json.loads(value)
    except Exception:
        return []


def get_watched_ids(username):

    history = get_watch_history(
        username,
        limit=5000,
    )

    if history.empty:
        return set()

    return {
        int(x)
        for x in history["TMDB_ID"].tolist()
    }


def get_watchlist_ids(username):

    watchlist = get_watchlist(username)

    if watchlist.empty:
        return set()

    return {
        int(x)
        for x in watchlist["TMDB_ID"].tolist()
    }


# ============================================================
# USER PROFILE
# ============================================================

def build_taste_profile(username):

    ratings = get_ratings(username)

    profile = {
        "genres": {},
        "liked_movies": [],
        "disliked_movies": [],
        "average_rating": None,
        "rating_count": 0,
    }

    if ratings.empty:
        return profile

    profile["rating_count"] = len(ratings)

    profile["average_rating"] = float(
        ratings["Rating"].mean()
    )

    for _, row in ratings.iterrows():

        movie_id = int(
            row["TMDB_ID"]
        )

        rating = float(
            row["Rating"]
        )

        if rating >= 4:

            profile[
                "liked_movies"
            ].append(movie_id)

        elif rating <= 2:

            profile[
                "disliked_movies"
            ].append(movie_id)

    return profile


# ============================================================
# SEED MOVIES
# ============================================================

def get_seed_movies(
    username,
    maximum=10,
):

    ratings = get_ratings(username)

    if ratings.empty:
        return []

    ratings = ratings.sort_values(
        "Rating",
        ascending=False,
    )

    seeds = []

    for _, row in ratings.iterrows():

        if float(row["Rating"]) >= 4:

            seeds.append(
                int(row["TMDB_ID"])
            )

        if len(seeds) >= maximum:
            break

    return seeds


# ============================================================
# STARTING PROFILE DISCOVERY
# ============================================================

def get_starting_genres(username):

    data = STARTING_PROFILES.get(
        username,
        {}
    )

    return data.get(
        "genres",
        []
    )


# ============================================================
# CANDIDATES
# ============================================================

def build_candidates(
    username,
    maximum_seeds=8,
):

    watched = get_watched_ids(
        username
    )

    watchlist = get_watchlist_ids(
        username
    )

    candidates = {}

    # --------------------------------------------------------
    # FROM RATINGS
    # --------------------------------------------------------

    seeds = get_seed_movies(
        username,
        maximum_seeds,
    )

    for seed in seeds:

        recommendations = (
            get_movie_recommendations(
                seed
            )
        )

        similar = get_similar_movies(
            seed
        )

        for movie in recommendations:

            if movie.get("id"):
                candidates[
                    movie["id"]
                ] = movie

        for movie in similar:

            if movie.get("id"):
                candidates[
                    movie["id"]
                ] = movie

    # --------------------------------------------------------
    # FROM STARTING PROFILE
    # --------------------------------------------------------

    if not candidates:

        genres = get_starting_genres(
            username
        )

        for genre in genres:

            movies = get_discover_movies(
                genres=[genre],
                min_rating=6.5,
                min_vote_count=250,
                sort_by="popularity.desc",
            )

            for movie in movies:

                if movie.get("id"):
                    candidates[
                        movie["id"]
                    ] = movie

    # --------------------------------------------------------
    # FILTER
    # --------------------------------------------------------

    results = []

    for movie in candidates.values():

        movie_id = movie.get("id")

        if not movie_id:
            continue

        if movie_id in watched:
            continue

        if movie_id in watchlist:
            continue

        results.append(movie)

    return results


# ============================================================
# SCORE
# ============================================================

def score_movie(
    movie,
    username=None,
):

    score = 50.0

    profile = STARTING_PROFILES.get(
        username,
        {}
    )

    preferred_genres = set(
        profile.get(
            "genres",
            []
        )
    )

    movie_genres = set(
        movie.get(
            "genre_ids",
            []
        )
    )

    # --------------------------------------------------------
    # STARTING PROFILE GENRES
    # --------------------------------------------------------

    matching_genres = (
        preferred_genres
        & movie_genres
    )

    score += len(
        matching_genres
    ) * 8

    # --------------------------------------------------------
    # TMDB QUALITY
    # --------------------------------------------------------

    tmdb_rating = float(
        movie.get(
            "vote_average",
            0
        ) or 0
    )

    if tmdb_rating >= 8.5:
        score += 15

    elif tmdb_rating >= 8:
        score += 12

    elif tmdb_rating >= 7:
        score += 8

    elif tmdb_rating >= 6:
        score += 3

    # --------------------------------------------------------
    # POPULARITY
    # --------------------------------------------------------

    popularity = float(
        movie.get(
            "popularity",
            0
        ) or 0
    )

    if popularity >= 200:
        score += 6

    elif popularity >= 100:
        score += 4

    elif popularity >= 50:
        score += 2

    # --------------------------------------------------------
    # PROFILE RATINGS
    # --------------------------------------------------------

    if username:

        ratings = get_ratings(
            username
        )

        if not ratings.empty:

            liked_genres = set()
            disliked_genres = set()

            for _, row in ratings.iterrows():

                rating = float(
                    row["Rating"]
                )

                genres = safe_json(
                    row.get("Genres")
                )

                if rating >= 4:

                    liked_genres.update(
                        genres
                    )

                elif rating <= 2:

                    disliked_genres.update(
                        genres
                    )

            for genre in movie_genres:

                if genre in liked_genres:
                    score += 6

                if genre in disliked_genres:
                    score -= 8

    return round(
        max(
            0,
            min(
                100,
                score
            )
        ),
        1,
    )


# ============================================================
# PERSONAL
# ============================================================

def get_personal_recommendations(
    username,
    limit=12,
):

    candidates = build_candidates(
        username
    )

    results = []

    for movie in candidates:

        movie = dict(movie)

        movie[
            "match_score"
        ] = score_movie(
            movie,
            username,
        )

        movie[
            "match_for"
        ] = username

        results.append(
            movie
        )

    results.sort(
        key=lambda x: (
            x.get(
                "match_score",
                0
            ),
            x.get(
                "vote_average",
                0
            ),
        ),
        reverse=True,
    )

    return results[:limit]


# ============================================================
# SHARED
# ============================================================

def get_shared_recommendations(
    user_one="Anthony",
    user_two="Kseniia",
    limit=12,
):

    candidates_one = build_candidates(
        user_one
    )

    candidates_two = build_candidates(
        user_two
    )

    combined = {}

    for movie in candidates_one:

        combined[
            movie["id"]
        ] = movie

    for movie in candidates_two:

        combined[
            movie["id"]
        ] = movie

    ids_one = {
        x["id"]
        for x in candidates_one
    }

    ids_two = {
        x["id"]
        for x in candidates_two
    }

    watched_one = get_watched_ids(
        user_one
    )

    watched_two = get_watched_ids(
        user_two
    )

    results = []

    for movie in combined.values():

        movie_id = movie["id"]

        if movie_id in watched_one:
            continue

        if movie_id in watched_two:
            continue

        score_one = score_movie(
            movie,
            user_one,
        )

        score_two = score_movie(
            movie,
            user_two,
        )

        # Both people's predicted
        # enjoyment matters.

        shared_score = (
            score_one * 0.5
            +
            score_two * 0.5
        )

        # Extra reward when both
        # recommendation engines
        # independently found it.

        if (
            movie_id in ids_one
            and movie_id in ids_two
        ):

            shared_score += 10

        movie = dict(movie)

        movie[
            "match_score"
        ] = round(
            min(
                100,
                shared_score
            ),
            1,
        )

        movie[
            "anthony_score"
        ] = score_one

        movie[
            "kseniia_score"
        ] = score_two

        movie[
            "match_for"
        ] = "Anthony + Kseniia"

        results.append(
            movie
        )

    results.sort(
        key=lambda x: (
            x[
                "match_score"
            ],
            x.get(
                "vote_average",
                0
            ),
        ),
        reverse=True,
    )

    return results[:limit]


# ============================================================
# REASON
# ============================================================

def recommendation_reason(movie):

    reasons = []

    rating = movie.get(
        "vote_average"
    )

    if rating:

        if rating >= 8:
            reasons.append(
                "Highly rated"
            )

        elif rating >= 7:
            reasons.append(
                "Strong reviews"
            )

    genres = movie.get(
        "genre_ids",
        []
    )

    if 28 in genres:
        reasons.append(
            "Action"
        )

    if 53 in genres:
        reasons.append(
            "Thriller"
        )

    if 80 in genres:
        reasons.append(
            "Crime"
        )

    if 10749 in genres:
        reasons.append(
            "Romance"
        )

    if 18 in genres:
        reasons.append(
            "Emotional drama"
        )

    if not reasons:

        reasons.append(
            "Matches your taste profile"
        )

    return " • ".join(
        reasons[:4]
    )
