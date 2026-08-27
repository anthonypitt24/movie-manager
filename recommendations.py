from database import (
    get_user,
    get_ratings,
    get_watchlist,
    get_watch_history,
)

from tmdb import (
    get_movie_recommendations,
    get_similar_movies,
    get_movie_details,
)


# ============================================================
# HELPERS
# ============================================================

def normalise(value, minimum, maximum):
    if value is None:
        return 0

    if maximum == minimum:
        return 0

    return (value - minimum) / (
        maximum - minimum
    )


def movie_id_from_row(row):
    return int(row["TMDB_ID"])


# ============================================================
# USER TASTE PROFILE
# ============================================================

def build_taste_profile(user_name):

    ratings = get_ratings(user_name)

    profile = {
        "liked_movies": [],
        "disliked_movies": [],
        "average_rating": None,
    }

    if ratings.empty:
        return profile

    average = ratings["Rating"].mean()

    profile["average_rating"] = float(
        average
    )

    liked = ratings[
        ratings["Rating"] >= 4
    ]

    disliked = ratings[
        ratings["Rating"] <= 2
    ]

    profile["liked_movies"] = [
        int(x)
        for x in liked["TMDB_ID"].tolist()
    ]

    profile["disliked_movies"] = [
        int(x)
        for x in disliked["TMDB_ID"].tolist()
    ]

    return profile


# ============================================================
# GET SEED MOVIES
# ============================================================

def get_seed_movies(user_name, maximum=8):

    ratings = get_ratings(user_name)

    if ratings.empty:
        return []

    ratings = ratings.sort_values(
        "Rating",
        ascending=False,
    )

    seeds = []

    for _, row in ratings.iterrows():

        rating = float(row["Rating"])

        if rating >= 4:

            seeds.append(
                int(row["TMDB_ID"])
            )

        if len(seeds) >= maximum:
            break

    return seeds


# ============================================================
# GET WATCHED IDS
# ============================================================

def get_watched_ids(user_name):

    history = get_watch_history(
        user_name,
        limit=1000,
    )

    if history.empty:
        return set()

    return {
        int(x)
        for x in history["TMDB_ID"].tolist()
    }


# ============================================================
# GET WATCHLIST IDS
# ============================================================

def get_watchlist_ids(user_name):

    watchlist = get_watchlist(
        user_name
    )

    if watchlist.empty:
        return set()

    return {
        int(x)
        for x in watchlist["TMDB_ID"].tolist()
    }


# ============================================================
# BUILD CANDIDATES
# ============================================================

def build_candidates(
    user_name,
    maximum_seeds=8,
):

    seeds = get_seed_movies(
        user_name,
        maximum_seeds,
    )

    candidates = {}

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
            candidates[
                movie["id"]
            ] = movie

        for movie in similar:
            candidates[
                movie["id"]
            ] = movie

    watched = get_watched_ids(
        user_name
    )

    watchlist = get_watchlist_ids(
        user_name
    )

    # Don't recommend something
    # they've already watched.
    # Don't duplicate their watchlist.

    filtered = []

    for movie in candidates.values():

        movie_id = movie.get("id")

        if movie_id in watched:
            continue

        if movie_id in watchlist:
            continue

        filtered.append(movie)

    return filtered


# ============================================================
# MOVIE SCORE
# ============================================================

def score_movie(
    movie,
    liked_genres=None,
    disliked_genres=None,
    favourite_actors=None,
    favourite_directors=None,
):

    liked_genres = liked_genres or []
    disliked_genres = disliked_genres or []

    favourite_actors = favourite_actors or []
    favourite_directors = favourite_directors or []

    score = 50.0

    tmdb_rating = movie.get(
        "vote_average",
        0,
    )

    popularity = movie.get(
        "popularity",
        0,
    )

    # --------------------------------------------------------
    # TMDB quality
    # --------------------------------------------------------

    if tmdb_rating >= 8:
        score += 15

    elif tmdb_rating >= 7:
        score += 10

    elif tmdb_rating >= 6:
        score += 5

    # --------------------------------------------------------
    # Popularity
    # --------------------------------------------------------

    if popularity >= 100:
        score += 5

    elif popularity >= 50:
        score += 3

    # --------------------------------------------------------
    # Genres
    # --------------------------------------------------------

    movie_genres = set(
        movie.get("genre_ids", [])
    )

    for genre in liked_genres:

        if genre in movie_genres:
            score += 8

    for genre in disliked_genres:

        if genre in movie_genres:
            score -= 15

    # --------------------------------------------------------
    # Keep score sensible
    # --------------------------------------------------------

    return round(
        max(
            0,
            min(
                100,
                score,
            ),
        ),
        1,
    )


# ============================================================
# PERSONAL RECOMMENDATIONS
# ============================================================

def get_personal_recommendations(
    user_name,
    limit=12,
):

    candidates = build_candidates(
        user_name
    )

    results = []

    for movie in candidates:

        score = score_movie(
            movie
        )

        movie = dict(movie)

        movie[
            "match_score"
        ] = score

        movie[
            "match_for"
        ] = user_name

        results.append(movie)

    results.sort(
        key=lambda x: (
            x["match_score"],
            x.get(
                "vote_average",
                0
            ),
        ),
        reverse=True,
    )

    return results[:limit]


# ============================================================
# SHARED RECOMMENDATIONS
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

        base_score = score_movie(
            movie
        )

        # Shared recommendation gets
        # a small boost because it came
        # from the tastes of both users.

        if (
            movie_id in {
                x["id"]
                for x in candidates_one
            }
            and
            movie_id in {
                x["id"]
                for x in candidates_two
            }
        ):

            base_score += 12

        movie = dict(movie)

        movie[
            "match_score"
        ] = round(
            min(
                100,
                base_score,
            ),
            1,
        )

        movie[
            "match_for"
        ] = (
            f"{user_one} + "
            f"{user_two}"
        )

        results.append(movie)

    results.sort(
        key=lambda x: (
            x["match_score"],
            x.get(
                "vote_average",
                0
            ),
        ),
        reverse=True,
    )

    return results[:limit]


# ============================================================
# RECOMMENDATION REASON
# ============================================================

def recommendation_reason(movie):

    reasons = []

    rating = movie.get(
        "vote_average"
    )

    if rating and rating >= 8:
        reasons.append(
            "Highly rated on TMDB"
        )

    elif rating and rating >= 7:
        reasons.append(
            "Strong TMDB rating"
        )

    if movie.get(
        "popularity",
        0
    ) >= 100:

        reasons.append(
            "Popular with viewers"
        )

    if not reasons:

        reasons.append(
            "Similar to films you've enjoyed"
        )

    return " • ".join(
        reasons[:3]
    )
