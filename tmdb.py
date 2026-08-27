import requests
import streamlit as st

BASE_URL = "https://api.themoviedb.org/3"


# ============================================================
# TOKEN
# ============================================================

def get_token():

    try:
        token = st.secrets["TMDB_API_TOKEN"]

        if not token:
            return None

        return str(token).strip()

    except Exception:
        return None


# ============================================================
# REQUEST
# ============================================================

@st.cache_data(ttl=300, show_spinner=False)
def tmdb_request(endpoint, params=None):

    token = get_token()

    if not token:
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json",
    }

    try:

        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            params=params or {},
            timeout=15,
        )

        if response.status_code != 200:
            return None

        return response.json()

    except requests.RequestException:
        return None


# ============================================================
# SEARCH
# ============================================================

def search_movies(query, page=1):

    if not query or not query.strip():
        return []

    data = tmdb_request(
        "/search/movie",
        {
            "query": query.strip(),
            "page": page,
            "include_adult": False,
        },
    )

    if not data:
        return []

    return data.get("results", [])


# ============================================================
# MOVIE DETAILS
# ============================================================

def get_movie_details(tmdb_id):

    return tmdb_request(
        f"/movie/{tmdb_id}",
        {
            "append_to_response":
                "credits,videos,keywords"
        },
    )


# ============================================================
# RECOMMENDATIONS
# ============================================================

def get_movie_recommendations(
    tmdb_id,
    page=1,
):

    data = tmdb_request(
        f"/movie/{tmdb_id}/recommendations",
        {
            "page": page,
        },
    )

    if not data:
        return []

    return data.get("results", [])


# ============================================================
# SIMILAR MOVIES
# ============================================================

def get_similar_movies(
    tmdb_id,
    page=1,
):

    data = tmdb_request(
        f"/movie/{tmdb_id}/similar",
        {
            "page": page,
        },
    )

    if not data:
        return []

    return data.get("results", [])


# ============================================================
# DISCOVER
# ============================================================

def get_discover_movies(
    genres=None,
    year_from=None,
    year_to=None,
    min_rating=0,
    page=1,
    sort_by="popularity.desc",
    min_vote_count=100,
):

    params = {
        "sort_by": sort_by,
        "include_adult": False,
        "include_video": False,
        "page": page,
        "vote_count.gte": min_vote_count,
        "vote_average.gte": min_rating,
    }

    if genres:

        params["with_genres"] = "|".join(
            str(x)
            for x in genres
        )

    if year_from:

        params[
            "primary_release_date.gte"
        ] = f"{year_from}-01-01"

    if year_to:

        params[
            "primary_release_date.lte"
        ] = f"{year_to}-12-31"

    data = tmdb_request(
        "/discover/movie",
        params,
    )

    if not data:
        return []

    return data.get("results", [])


# ============================================================
# GENRE LIST
# ============================================================

def get_movie_genres():

    data = tmdb_request(
        "/genre/movie/list",
        {
            "language": "en-GB"
        },
    )

    if not data:
        return []

    return data.get("genres", [])


# ============================================================
# TRENDING
# ============================================================

def get_trending_movies():

    data = tmdb_request(
        "/trending/movie/week"
    )

    if not data:
        return []

    return data.get(
        "results",
        []
    )


# ============================================================
# IMAGE
# ============================================================

def image_url(
    path,
    size="w500",
):

    if not path:
        return None

    return (
        f"https://image.tmdb.org/t/p/"
        f"{size}{path}"
    )
