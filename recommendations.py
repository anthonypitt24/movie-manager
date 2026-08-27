from collections import defaultdict

from database import (
    get_ratings,
    get_watchlist,
    get_watch_history,
    get_profile,
)
from tmdb import (
    get_movie_recommendations,
    get_similar_movies,
    get_discover_movies,
)


GENRES = {
    "Action": 28,
    "Adventure": 12,
    "Animation": 16,
    "Comedy": 35,
    "Crime": 80,
    "Documentary": 99,
    "Drama": 18,
    "Fantasy": 14,
    "Horror": 27,
    "Mystery": 9648,
    "Romance": 10749,
    "Science Fiction": 878,
    "Thriller": 53,
}


# These are deliberately used only to give the first profile session
# a strong starting point. After ratings exist, the user's own ratings
# increasingly take over.
TASTE_PRESETS = {
    "Anthony": {
        "genres": [28, 53, 80, 9648, 18, 878],
        "labels": [
            "🔥 Action",
            "⚡ Fast-paced",
            "🔪 Crime / True Crime",
            "😮 Thrillers",
            "🧠 Thought-provoking",
            "❤️ Emotive",
        ],
    },
    "Kseniia": {
        "genres": [10749, 18, 35, 53],
        "labels": [
            "💕 Romance",
            "✨ Beautiful",
            "🧠 Clever",
            "🔥 Mature / sensual",
            "😊 Feel-good",
            "❤️ Emotional",
        ],
    },
}


def _ids(values):
    return {int(x) for x in values if x is not None}


def get_seed_movies(user_name, maximum=8):
    ratings = get_ratings(user_name)
    if ratings.empty:
        return []

    ratings = ratings.sort_values("Rating", ascending=False)
    return [
        int(row["TMDB_ID"])
        for _, row in ratings.iterrows()
        if float(row["Rating"]) >= 4
    ][:maximum]


def get_watched_ids(user_name):
    history = get_watch_history(user_name, limit=5000)
    if history.empty:
        return set()
    return _ids(history["TMDB_ID"].tolist())


def get_watchlist_ids(user_name):
    watchlist = get_watchlist(user_name)
    if watchlist.empty:
        return set()
    return _ids(watchlist["TMDB_ID"].tolist())


def get_quick_profile_movies(user_name, limit=30):
    """
    Fast initial taste test.

    If the user has no ratings, pull films from their preset taste.
    If they already have ratings, mix preset discovery with films
    similar to their highly-rated films.
    """
    preset = TASTE_PRESETS.get(user_name, TASTE_PRESETS["Anthony"])
    candidates = {}

    # Broad genre discovery gives us a much better starting pool
    # than asking recommendations to recommend from zero ratings.
    for page in (1, 2):
        movies = get_discover_movies(
            genres=preset["genres"],
            page=page,
            sort_by="popularity.desc",
            min_rating=6.5,
            min_votes=250,
        )
        for movie in movies:
            if movie.get("id"):
                candidates[movie["id"]] = movie

    # Once the user has some ratings, add films related to things
    # they already love.
    for seed in get_seed_movies(user_name, maximum=5):
        for movie in get_movie_recommendations(seed):
            if movie.get("id"):
                candidates[movie["id"]] = movie
        for movie in get_similar_movies(seed):
            if movie.get("id"):
                candidates[movie["id"]] = movie

    watched = get_watched_ids(user_name)
    rated = _ids(get_rated_ids(user_name))

    filtered = [
        movie for movie in candidates.values()
        if movie.get("id") not in watched
        and movie.get("id") not in rated
    ]

    # Give the quick test a useful mixture rather than showing
    # 30 almost identical films.
    filtered.sort(
        key=lambda movie: (
            preset_score(movie, user_name),
            movie.get("vote_average", 0),
            movie.get("popularity", 0),
        ),
        reverse=True,
    )

    return filtered[:limit]


def get_rated_ids(user_name):
    ratings = get_ratings(user_name)
    if ratings.empty:
        return []
    return ratings["TMDB_ID"].tolist()


def _movie_genres(movie):
    ids = set(movie.get("genre_ids") or [])

    # Detailed TMDB responses use genres=[{"id":..., "name":...}]
    for item in movie.get("genres") or []:
        if isinstance(item, dict) and item.get("id"):
            ids.add(int(item["id"]))

    return ids


def preset_score(movie, user_name):
    preset = TASTE_PRESETS.get(user_name, TASTE_PRESETS["Anthony"])
    genres = _movie_genres(movie)
    matched = len(genres & set(preset["genres"]))

    score = 50 + matched * 10
    score += min(float(movie.get("vote_average") or 0) * 2, 20)
    score += min(float(movie.get("popularity") or 0) / 100, 10)

    return min(100, score)


def _rating_profile(user_name):
    ratings = get_ratings(user_name)
    if ratings.empty:
        return {
            "genre_likes": defaultdict(float),
            "genre_dislikes": defaultdict(float),
            "rated": {},
        }

    genre_likes = defaultdict(float)
    genre_dislikes = defaultdict(float)
    rated = {}

    # Ratings table does not contain genre IDs, so this function is
    # intentionally based on the movie data returned by the DB.
    # The recommendation engine below also uses the preset when
    # detailed metadata is unavailable.
    return {
        "genre_likes": genre_likes,
        "genre_dislikes": genre_dislikes,
        "rated": {
            int(row["TMDB_ID"]): float(row["Rating"])
            for _, row in ratings.iterrows()
        },
    }


def score_movie(movie, user_name=None, liked_genres=None, disliked_genres=None):
    liked_genres = set(liked_genres or [])
    disliked_genres = set(disliked_genres or [])

    if user_name:
        preset = TASTE_PRESETS.get(user_name, {})
        liked_genres |= set(preset.get("genres", []))

    movie_genres = _movie_genres(movie)

    score = 45.0

    # Personal genre fit.
    score += len(movie_genres & liked_genres) * 8
    score -= len(movie_genres & disliked_genres) * 15

    # TMDB quality.
    tmdb_rating = float(movie.get("vote_average") or 0)
    if tmdb_rating >= 8:
        score += 15
    elif tmdb_rating >= 7:
        score += 10
    elif tmdb_rating >= 6:
        score += 5

    # Popularity is useful, but deliberately capped so it doesn't
    # overpower personal taste.
    popularity = float(movie.get("popularity") or 0)
    score += min(8, popularity / 50)

    return round(max(0, min(100, score)), 1)


def build_candidates(user_name, maximum_seeds=8):
    seeds = get_seed_movies(user_name, maximum_seeds)
    candidates = {}

    # Add discovery based on the person's current taste preset.
    preset = TASTE_PRESETS.get(user_name, {})
    for movie in get_discover_movies(
        genres=preset.get("genres"),
        min_rating=6.5,
        min_votes=250,
        page=1,
    ):
        if movie.get("id"):
            candidates[movie["id"]] = movie

    # Add films related to actual liked films.
    for seed in seeds:
        for movie in get_movie_recommendations(seed):
            if movie.get("id"):
                candidates[movie["id"]] = movie
        for movie in get_similar_movies(seed):
            if movie.get("id"):
                candidates[movie["id"]] = movie

    watched = get_watched_ids(user_name)
    watchlist = get_watchlist_ids(user_name)
    rated = _ids(get_rated_ids(user_name))

    return [
        movie for movie in candidates.values()
        if movie.get("id") not in watched
        and movie.get("id") not in watchlist
        and movie.get("id") not in rated
    ]


def get_personal_recommendations(user_name, limit=12):
    candidates = build_candidates(user_name)
    results = []

    for movie in candidates:
        item = dict(movie)
        item["match_score"] = score_movie(movie, user_name=user_name)
        item["match_for"] = user_name
        results.append(item)

    results.sort(
        key=lambda x: (
            x["match_score"],
            x.get("vote_average", 0),
            x.get("popularity", 0),
        ),
        reverse=True,
    )
    return results[:limit]


def get_shared_recommendations(
    user_one="Anthony",
    user_two="Kseniia",
    limit=12,
):
    candidates_one = build_candidates(user_one)
    candidates_two = build_candidates(user_two)

    map_one = {m["id"]: m for m in candidates_one if m.get("id")}
    map_two = {m["id"]: m for m in candidates_two if m.get("id")}

    combined = dict(map_one)
    combined.update(map_two)

    watched = get_watched_ids(user_one) | get_watched_ids(user_two)
    results = []

    for movie_id, movie in combined.items():
        if movie_id in watched:
            continue

        score_one = score_movie(movie, user_name=user_one)
        score_two = score_movie(movie, user_name=user_two)

        # Geometric-ish compromise: favour films that score well
        # for both people rather than one person only.
        shared_score = (score_one * 0.45) + (score_two * 0.45)

        if movie_id in map_one and movie_id in map_two:
            shared_score += 10

        item = dict(movie)
        item["match_score"] = round(min(100, shared_score), 1)
        item["match_for"] = f"{user_one} + {user_two}"
        results.append(item)

    results.sort(
        key=lambda x: (
            x["match_score"],
            x.get("vote_average", 0),
        ),
        reverse=True,
    )
    return results[:limit]


def recommendation_reason(movie, user_name=None):
    reasons = []
    genres = _movie_genres(movie)

    if user_name:
        preset = TASTE_PRESETS.get(user_name, {})
        matched = genres & set(preset.get("genres", []))
        names = [
            name for name, genre_id in GENRES.items()
            if genre_id in matched
        ]
        if names:
            reasons.append("Fits your " + ", ".join(names[:2]) + " taste")

    rating = movie.get("vote_average")
    if rating and float(rating) >= 8:
        reasons.append("Highly rated on TMDB")
    elif rating and float(rating) >= 7:
        reasons.append("Strong TMDB rating")

    if not reasons:
        reasons.append("Similar to films you have enjoyed")

    return " • ".join(reasons[:3])
