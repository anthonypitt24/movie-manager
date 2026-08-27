import requests
import streamlit as st

BASE_URL = "https://api.themoviedb.org/3"


def get_token():

    try:
        token = st.secrets["TMDB_API_TOKEN"]

        if not token:
            return None

        return str(token).strip()

    except Exception:
        return None


def tmdb_request(endpoint, params=None):

    token = get_token()

    if not token:
        st.error(
            "TMDB API token is missing. "
            "Check Streamlit Secrets."
        )
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

            st.error(
                f"TMDB API error "
                f"{response.status_code}: "
                f"{response.text[:500]}"
            )

            return None

        return response.json()

    except requests.RequestException as e:

        st.error(
            f"Could not connect to TMDB: {e}"
        )

        return None


def search_movies(query, page=1):

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

    return data.get(
        "results",
        []
    )


def get_movie_details(tmdb_id):

    return tmdb_request(
        f"/movie/{tmdb_id}",
        {
            "append_to_response":
                "credits,videos,keywords"
        },
    )


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

    return data.get(
        "results",
        []
    )


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

    return data.get(
        "results",
        []
    )


def get_discover_movies(
    genres=None,
    year_from=None,
    year_to=None,
    min_rating=0,
    page=1,
):

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

    return data.get(
        "results",
        []
    )


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
