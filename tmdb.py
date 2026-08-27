import requests
import streamlit as st

BASE_URL = "https://api.themoviedb.org/3"


def get_token():
    try:
        token = st.secrets["TMDB_API_TOKEN"]
        return str(token).strip() if token else None
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def _cached_tmdb_request(endpoint, params_tuple):
    token = get_token()
    if not token:
        return {"__error__": "TMDB API token is missing. Check Streamlit Secrets."}

    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json",
    }

    try:
        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            params=dict(params_tuple),
            timeout=15,
        )

        if response.status_code != 200:
            return {
                "__error__": (
                    f"TMDB API error {response.status_code}: "
                    f"{response.text[:300]}"
                )
            }

        return response.json()

    except requests.RequestException as exc:
        return {"__error__": f"Could not connect to TMDB: {exc}"}


def tmdb_request(endpoint, params=None):
    clean = params or {}
    params_tuple = tuple(sorted(clean.items()))
    data = _cached_tmdb_request(endpoint, params_tuple)

    if "__error__" in data:
        st.error(data["__error__"])
        return None

    return data


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
    return data.get("results", []) if data else []


def get_movie_details(tmdb_id):
    return tmdb_request(
        f"/movie/{tmdb_id}",
        {"append_to_response": "credits,videos,keywords"},
    )


def get_movie_recommendations(tmdb_id, page=1):
    data = tmdb_request(
        f"/movie/{tmdb_id}/recommendations",
        {"page": page},
    )
    return data.get("results", []) if data else []


def get_similar_movies(tmdb_id, page=1):
    data = tmdb_request(
        f"/movie/{tmdb_id}/similar",
        {"page": page},
    )
    return data.get("results", []) if data else []


def get_discover_movies(
    genres=None,
    year_from=None,
    year_to=None,
    min_rating=0,
    page=1,
    sort_by="popularity.desc",
    min_votes=100,
    keywords=None,
):
    params = {
        "sort_by": sort_by,
        "include_adult": False,
        "include_video": False,
        "page": page,
        "vote_count.gte": min_votes,
        "vote_average.gte": min_rating,
    }

    if genres:
        # Use | for OR, which is useful for quick taste-building.
        params["with_genres"] = "|".join(str(x) for x in genres)

    if keywords:
        params["with_keywords"] = "|".join(str(x) for x in keywords)

    if year_from:
        params["primary_release_date.gte"] = f"{year_from}-01-01"

    if year_to:
        params["primary_release_date.lte"] = f"{year_to}-12-31"

    data = tmdb_request("/discover/movie", params)
    return data.get("results", []) if data else []


def image_url(path, size="w500"):
    if not path:
        return None
    return f"https://image.tmdb.org/t/p/{size}{path}"
