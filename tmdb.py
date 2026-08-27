import requests
import streamlit as st

BASE_URL = "https://api.themoviedb.org/3"


def get_token():
    """
    Get the TMDB API token from Streamlit secrets.
    """

    try:
        return st.secrets["TMDB_API_TOKEN"]
    except Exception:
        return None


def tmdb_request(endpoint, params=None):
    """
    Make a request to TMDB.
    """

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

        response.raise_for_status()

        return response.json()

    except requests.RequestException:
        return None


def search_movies(query, page=1):
    """
    Search TMDB for movies.
    """

    if not query.strip():
        return []

    data = tmdb_request(
        "/search/movie",
        {
            "query": query,
            "page": page,
            "include_adult": False,
        },
    )

    if not data:
        return []

    return data.get("results", [])


def get_movie_details(tmdb_id):
    """
    Get detailed information about a movie.
    """

    return tmdb_request(
        f"/movie/{tmdb_id}",
        {
            "append_to_response":
                "credits,videos,keywords"
        },
    )


def get_movie_recommendations(tmdb_id, page=1):
    """
    Get movies TMDB recommends based on another movie.
    """

    data = tmdb_request(
        f"/movie/{tmdb_id}/recommendations",
        {
            "page": page,
        },
    )

    if not data:
        return []

    return data.get("results", [])


def get_similar_movies(tmdb_id, page=1):
    """
    Get movies similar to another movie.
    """

    data = tmdb_request(
        f"/movie/{tmdb_id}/similar",
        {
            "page": page,
        },
    )

    if not data:
        return []

    return data.get("results", [])


def get_discover_movies(
    genres=None,
    year_from=None,
    year_to=None,
    min_rating=0,
    page=1,
):
    """
    Discover movies using TMDB filters.
    """

    params = {
        "sort_by": "popularity.desc",
        "include_adult": False,
        "include_video": False,
        "page": page,
        "vote_count.gte": 100,
        "vote_average.gte": min_rating,
    }

    if genres:
        params["with_genres"] = ",".join(
            str(x) for x in genres
        )

    if year_from:
        params["primary_release_date.gte"] = (
            f"{year_from}-01-01"
        )

    if year_to:
        params["primary_release_date.lte"] = (
            f"{year_to}-12-31"
        )

    data = tmdb_request(
        "/discover/movie",
        params,
    )

    if not data:
        return []

    return data.get("results", [])


def image_url(path, size="w500"):
    """
    Convert a TMDB poster path into a full image URL.
    """

    if not path:
        return None

    return f"https://image.tmdb.org/t/p/{size}{path}"
