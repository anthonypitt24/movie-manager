import streamlit as st
import pandas as pd

from database import (
    init_db,
    get_all_users,
    get_user_statistics,
    get_watchlist,
    get_watch_history,
    get_ratings,
    get_favourites,
    get_shared_watched_movies,
    get_movie_by_tmdb_id,
    add_movie,
    add_to_watchlist,
    remove_from_watchlist,
    save_rating,
    set_favourite,
    set_movie_status,
    log_watched_movie,
    save_user_profile,
    get_user_profile,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Movie Manager",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# INITIALISE DATABASE
# ============================================================

init_db()


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 0;
    }

    .subtitle {
        font-size: 18px;
        opacity: 0.7;
        margin-bottom: 30px;
    }

    .movie-card {
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(128,128,128,0.25);
        margin-bottom: 15px;
    }

    .stat-card {
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(128,128,128,0.25);
        text-align: center;
    }

    .stat-number {
        font-size: 32px;
        font-weight: 800;
    }

    .stat-label {
        opacity: 0.7;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🎬 Movie Manager")

st.sidebar.markdown("---")

user = st.sidebar.selectbox(
    "Who's using the app?",
    ["Anthony", "Kseniia"],
)


st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "🔎 Movie Search",
        "📋 My Watchlist",
        "🎬 Watched",
        "⭐ My Ratings",
        "❤️ My Favourites",
        "👥 Our Movies",
        "👤 My Profile",
    ],
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_value(value, default=""):
    if value is None:
        return default
    return value


def rating_display(rating):
    if rating is None:
        return "Not rated"

    return f"{float(rating):.1f}/5"


# ============================================================
# HOME
# ============================================================

if page == "🏠 Home":

    st.markdown(
        '<div class="main-title">🎬 Movie Manager</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="subtitle">Welcome, {user}</div>',
        unsafe_allow_html=True,
    )

    stats = get_user_statistics(user)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "🎬 Watched",
            stats["watched"],
        )

    with col2:
        st.metric(
            "📋 Watchlist",
            stats["watchlist"],
        )

    with col3:
        st.metric(
            "⭐ Rated",
            stats["rated"],
        )

    with col4:
        st.metric(
            "❤️ Favourites",
            stats["favourites"],
        )

    with col5:
        average = stats["average_rating"]

        if average is None:
            average = "—"

        st.metric(
            "⭐ Average",
            average,
        )

    st.markdown("---")

    st.subheader("📋 Your Watchlist")

    watchlist = get_watchlist(user)

    if watchlist.empty:

        st.info(
            "Your watchlist is empty. "
            "Use Movie Search to add some films."
        )

    else:

        st.dataframe(
            watchlist,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    st.subheader("🎬 Recently Watched")

    history = get_watch_history(
        user,
        limit=10,
    )

    if history.empty:

        st.info(
            "You haven't recorded any films yet."
        )

    else:

        st.dataframe(
            history,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# MOVIE SEARCH
# ============================================================

elif page == "🔎 Movie Search":

    st.title("🔎 Movie Search")

    st.info(
        "TMDB search will be connected here next. "
        "For now you can manually add a movie using its TMDB ID."
    )

    st.markdown("---")

    st.subheader("➕ Add Movie")

    with st.form("add_movie_form"):

        tmdb_id = st.number_input(
            "TMDB Movie ID",
            min_value=1,
            step=1,
        )

        title = st.text_input(
            "Movie title"
        )

        original_title = st.text_input(
            "Original title"
        )

        overview = st.text_area(
            "Overview"
        )

        release_date = st.text_input(
            "Release date",
            placeholder="2026-01-01",
        )

        runtime = st.number_input(
            "Runtime (minutes)",
            min_value=0,
            max_value=500,
            value=0,
        )

        vote_average = st.number_input(
            "TMDB rating",
            min_value=0.0,
            max_value=10.0,
            value=0.0,
            step=0.1,
        )

        poster_path = st.text_input(
            "Poster path / URL"
        )

        backdrop_path = st.text_input(
            "Backdrop path / URL"
        )

        trailer_url = st.text_input(
            "Trailer URL"
        )

        submitted = st.form_submit_button(
            "Add Movie"
        )

        if submitted:

            if not title.strip():

                st.error(
                    "Please enter a movie title."
                )

            else:

                movie_id = add_movie(
                    tmdb_id=int(tmdb_id),
                    title=title.strip(),
                    original_title=original_title.strip()
                    or None,
                    overview=overview.strip()
                    or None,
                    release_date=release_date.strip()
                    or None,
                    runtime=int(runtime)
                    if runtime > 0
                    else None,
                    vote_average=float(vote_average)
                    if vote_average > 0
                    else None,
                    poster_path=poster_path.strip()
                    or None,
                    backdrop_path=backdrop_path.strip()
                    or None,
                    trailer_url=trailer_url.strip()
                    or None,
                )

                st.success(
                    f"Movie added successfully. "
                    f"Database ID: {movie_id}"
                )


# ============================================================
# WATCHLIST
# ============================================================

elif page == "📋 My Watchlist":

    st.title(
        f"📋 {user}'s Watchlist"
    )

    watchlist = get_watchlist(user)

    if watchlist.empty:

        st.info(
            "Your watchlist is empty."
        )

    else:

        st.dataframe(
            watchlist,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    st.subheader("➕ Add to Watchlist")

    with st.form("watchlist_form"):

        tmdb_id = st.number_input(
            "TMDB Movie ID",
            min_value=1,
            step=1,
        )

        priority = st.slider(
            "Priority",
            min_value=1,
            max_value=5,
            value=3,
        )

        notes = st.text_area(
            "Notes"
        )

        submitted = st.form_submit_button(
            "Add to Watchlist"
        )

        if submitted:

            movie = get_movie_by_tmdb_id(
                int(tmdb_id)
            )

            if not movie:

                st.error(
                    "That movie isn't in the database yet."
                )

            else:

                add_to_watchlist(
                    user,
                    int(tmdb_id),
                    priority,
                    notes or None,
                )

                st.success(
                    f"{movie['title']} added to "
                    f"{user}'s watchlist."
                )

                st.rerun()


# ============================================================
# WATCHED
# ============================================================

elif page == "🎬 Watched":

    st.title(
        f"🎬 {user}'s Watched Movies"
    )

    history = get_watch_history(
        user,
        limit=100,
    )

    if history.empty:

        st.info(
            "No watched movies have been recorded yet."
        )

    else:

        st.dataframe(
            history,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    st.subheader("➕ Record a Movie")

    with st.form("watched_form"):

        tmdb_id = st.number_input(
            "TMDB Movie ID",
            min_value=1,
            step=1,
        )

        viewers = st.multiselect(
            "Who watched it?",
            [
                "Anthony",
                "Kseniia",
            ],
            default=[user],
        )

        viewing_type = st.selectbox(
            "Viewing type",
            [
                "watched",
                "rewatch",
            ],
        )

        notes = st.text_area(
            "Notes"
        )

        submitted = st.form_submit_button(
            "Record Movie"
        )

        if submitted:

            if not viewers:

                st.error(
                    "Select at least one viewer."
                )

            else:

                movie = get_movie_by_tmdb_id(
                    int(tmdb_id)
                )

                if not movie:

                    st.error(
                        "That movie isn't in the database yet."
                    )

                else:

                    log_watched_movie(
                        viewers,
                        int(tmdb_id),
                        viewing_type=viewing_type,
                        notes=notes or None,
                    )

                    st.success(
                        f"{movie['title']} recorded."
                    )

                    st.rerun()


# ============================================================
# RATINGS
# ============================================================

elif page == "⭐ My Ratings":

    st.title(
        f"⭐ {user}'s Ratings"
    )

    ratings = get_ratings(user)

    if ratings.empty:

        st.info(
            "You haven't rated any movies yet."
        )

    else:

        st.dataframe(
            ratings,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    st.subheader("⭐ Rate a Movie")

    with st.form("rating_form"):

        tmdb_id = st.number_input(
            "TMDB Movie ID",
            min_value=1,
            step=1,
        )

        rating = st.slider(
            "Your rating",
            min_value=0.5,
            max_value=5.0,
            value=3.0,
            step=0.5,
        )

        review = st.text_area(
            "Review / notes"
        )

        favourite = st.checkbox(
            "❤️ Add to favourites"
        )

        submitted = st.form_submit_button(
            "Save Rating"
        )

        if submitted:

            movie = get_movie_by_tmdb_id(
                int(tmdb_id)
            )

            if not movie:

                st.error(
                    "That movie isn't in the database yet."
                )

            else:

                save_rating(
                    user,
                    int(tmdb_id),
                    rating,
                    review or None,
                    favourite,
                )

                st.success(
                    f"{movie['title']} rated "
                    f"{rating:.1f}/5."
                )

                st.rerun()


# ============================================================
# FAVOURITES
# ============================================================

elif page == "❤️ My Favourites":

    st.title(
        f"❤️ {user}'s Favourite Movies"
    )

    favourites = get_favourites(user)

    if favourites.empty:

        st.info(
            "You don't have any favourites yet."
        )

    else:

        st.dataframe(
            favourites,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# OUR MOVIES
# ============================================================

elif page == "👥 Our Movies":

    st.title("👥 Anthony & Kseniia")

    st.write(
        "Movies that both of you have watched."
    )

    shared = get_shared_watched_movies()

    if shared.empty:

        st.info(
            "There aren't any shared watched movies yet."
        )

    else:

        st.dataframe(
            shared,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    st.subheader("📊 Your Statistics")

    col1, col2 = st.columns(2)

    anthony_stats = get_user_statistics(
        "Anthony"
    )

    kseniia_stats = get_user_statistics(
        "Kseniia"
    )

    with col1:

        st.markdown("### 👤 Anthony")

        st.metric(
            "Watched",
            anthony_stats["watched"],
        )

        st.metric(
            "Watchlist",
            anthony_stats["watchlist"],
        )

        average = anthony_stats["average_rating"]

        st.metric(
            "Average rating",
            average if average else "—",
        )

    with col2:

        st.markdown("### 👤 Kseniia")

        st.metric(
            "Watched",
            kseniia_stats["watched"],
        )

        st.metric(
            "Watchlist",
            kseniia_stats["watchlist"],
        )

        average = kseniia_stats["average_rating"]

        st.metric(
            "Average rating",
            average if average else "—",
        )


# ============================================================
# PROFILE
# ============================================================

elif page == "👤 My Profile":

    st.title(
        f"👤 {user}'s Movie Profile"
    )

    profile = get_user_profile(user)

    if profile:

        st.success(
            "You already have a movie profile."
        )

    else:

        st.info(
            "Let's create your movie preferences."
        )

        profile = {}


    pacing_options = [
        "Slow",
        "Medium",
        "Fast",
        "Very Fast",
        "No preference",
    ]

    tone_options = [
        "Funny",
        "Dark",
        "Serious",
        "Emotional",
        "Feel-good",
        "Suspenseful",
        "Action-packed",
        "Romantic",
        "Mind-bending",
        "Family-friendly",
    ]

    runtime_options = [
        "Under 90 minutes",
        "90–120 minutes",
        "120–150 minutes",
        "150+ minutes",
        "No preference",
    ]

    current_pacing = (
        profile.get("pacing")
        if profile
        else None
    )

    if current_pacing not in pacing_options:
        current_pacing = "No preference"

    current_tones = (
        profile.get("tones", [])
        if profile
        else []
    )

    current_runtime = (
        profile.get("runtime")
        if profile
        else None
    )

    if current_runtime not in runtime_options:
        current_runtime = "No preference"


    with st.form("profile_form"):

        pacing = st.selectbox(
            "Preferred pacing",
            pacing_options,
            index=pacing_options.index(
                current_pacing
            ),
        )

        tones = st.multiselect(
            "Favourite movie tones",
            tone_options,
            default=[
                tone
                for tone in current_tones
                if tone in tone_options
            ],
        )

        runtime = st.selectbox(
            "Preferred runtime",
            runtime_options,
            index=runtime_options.index(
                current_runtime
            ),
        )

        decades = st.multiselect(
            "Favourite decades",
            [
                "1970s",
                "1980s",
                "1990s",
                "2000s",
                "2010s",
                "2020s",
            ],
            default=(
                profile.get("decades", [])
                if profile
                else []
            ),
        )

        certificates = st.multiselect(
            "Preferred certificates",
            [
                "U",
                "PG",
                "12",
                "12A",
                "15",
                "18",
            ],
            default=(
                profile.get(
                    "certificates",
                    []
                )
                if profile
                else []
            ),
        )

        favourite_actors = st.text_input(
            "Favourite actors",
            value=", ".join(
                profile.get(
                    "favourite_actors",
                    []
                )
                if profile
                else []
            ),
        )

        favourite_directors = st.text_input(
            "Favourite directors",
            value=", ".join(
                profile.get(
                    "favourite_directors",
                    []
                )
                if profile
                else []
            ),
        )

        disliked_actors = st.text_input(
            "Actors you dislike",
            value=", ".join(
                profile.get(
                    "disliked_actors",
                    []
                )
                if profile
                else []
            ),
        )

        disliked_directors = st.text_input(
            "Directors you dislike",
            value=", ".join(
                profile.get(
                    "disliked_directors",
                    []
                )
                if profile
                else []
            ),
        )

        submitted = st.form_submit_button(
            "💾 Save Profile"
        )

        if submitted:

            def split_names(value):
                return [
                    x.strip()
                    for x in value.split(",")
                    if x.strip()
                ]

            save_user_profile(
                user_name=user,
                pacing=pacing,
                tones=tones,
                decades=decades,
                certificates=certificates,
                runtime=runtime,
                favourite_actors=
                    split_names(
                        favourite_actors
                    ),
                favourite_directors=
                    split_names(
                        favourite_directors
                    ),
                disliked_actors=
                    split_names(
                        disliked_actors
                    ),
                disliked_directors=
                    split_names(
                        disliked_directors
                    ),
            )

            st.success(
                f"{user}'s profile saved."
            )

            st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.sidebar.markdown("---")

st.sidebar.caption(
    "🎬 Movie Manager"
)

st.sidebar.caption(
    "Database foundation v2.0"
)
