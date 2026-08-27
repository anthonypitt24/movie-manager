import streamlit as st

from database import (
    init_db,
    add_movie,
    add_to_watchlist,
    get_watchlist,
    get_watch_history,
    get_ratings,
    get_favourites,
    save_rating,
    log_watched_movie,
)

from tmdb import (
    search_movies,
    get_movie_details,
    image_url,
)

from recommendations import (
    get_personal_recommendations,
    get_shared_recommendations,
    recommendation_reason,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Movie Manager",
    page_icon="🎬",
    layout="wide",
)


# ============================================================
# DATABASE
# ============================================================

init_db()


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .title {
        font-size: 42px;
        font-weight: 800;
    }

    .subtitle {
        font-size: 19px;
        opacity: 0.7;
        margin-bottom: 25px;
    }

    .match {
        font-size: 24px;
        font-weight: 800;
        margin-top: 8px;
        margin-bottom: 8px;
    }

    .quick-title {
        text-align: center;
        font-size: 32px;
        font-weight: 800;
    }

    .quick-subtitle {
        text-align: center;
        opacity: 0.7;
        margin-bottom: 15px;
    }

    .quick-score {
        text-align: center;
        font-size: 20px;
        font-weight: 700;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🎬 Movie Manager")

user = st.sidebar.selectbox(
    "Your profile",
    [
        "Anthony",
        "Kseniia",
    ],
)

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Menu",
    [
        "🍿 Tonight",
        "🧠 Build My Profile",
        "🔎 Find a Movie",
        "📋 My Watchlist",
        "🎬 Watched",
        "⭐ My Ratings",
        "❤️ Favourites",
        "👥 Anthony + Kseniia",
    ],
)


# ============================================================
# SAVE MOVIE
# ============================================================

def save_movie(details):

    if not details:
        return

    add_movie(
        tmdb_id=details["id"],
        title=details.get(
            "title",
            "Unknown",
        ),
        original_title=details.get(
            "original_title"
        ),
        overview=details.get(
            "overview"
        ),
        release_date=details.get(
            "release_date"
        ),
        runtime=details.get(
            "runtime"
        ),
        vote_average=details.get(
            "vote_average"
        ),
        vote_count=details.get(
            "vote_count"
        ),
        poster_path=details.get(
            "poster_path"
        ),
        backdrop_path=details.get(
            "backdrop_path"
        ),
        genres=details.get(
            "genres"
        ),
        cast=details.get(
            "credits",
            {}
        ).get(
            "cast",
            []
        ),
        directors=[
            person
            for person in details.get(
                "credits",
                {}
            ).get(
                "crew",
                []
            )
            if person.get("job") == "Director"
        ],
        keywords=details.get(
            "keywords",
            {}
        ).get(
            "keywords",
            []
        ),
    )


# ============================================================
# MOVIE CARD
# ============================================================

def display_movie(
    movie,
    show_buttons=True,
    key_prefix="movie",
):

    poster = image_url(
        movie.get("poster_path")
    )

    if poster:

        st.image(
            poster,
            use_container_width=True,
        )

    st.subheader(
        movie.get(
            "title",
            "Unknown",
        )
    )

    release = movie.get(
        "release_date",
        ""
    )

    if release:

        st.caption(
            f"📅 {release[:4]}"
        )

    rating = movie.get(
        "vote_average"
    )

    if rating:

        st.write(
            f"⭐ TMDB: {rating:.1f}/10"
        )

    match = movie.get(
        "match_score"
    )

    if match is not None:

        st.markdown(
            f'<div class="match">'
            f'🎯 {match:.0f}% Match'
            f'</div>',
            unsafe_allow_html=True,
        )

    overview = movie.get(
        "overview"
    )

    if overview:

        st.write(
            overview
        )

    st.caption(
        "💡 "
        + recommendation_reason(movie)
    )

    if not show_buttons:
        return

    tmdb_id = movie.get("id")

    if not tmdb_id:
        return

    # --------------------------------------------------------
    # UNIQUE BUTTON KEYS
    # --------------------------------------------------------

    watchlist_key = (
        f"{key_prefix}_watchlist_"
        f"{tmdb_id}_{user}"
    )

    watched_key = (
        f"{key_prefix}_watched_"
        f"{tmdb_id}_{user}"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "📋 Watchlist",
            key=watchlist_key,
            use_container_width=True,
        ):

            details = get_movie_details(
                tmdb_id
            )

            if details:

                save_movie(details)

                add_to_watchlist(
                    user,
                    tmdb_id,
                )

                st.success(
                    "Added to watchlist."
                )

    with col2:

        if st.button(
            "🎬 Watched",
            key=watched_key,
            use_container_width=True,
        ):

            details = get_movie_details(
                tmdb_id
            )

            if details:

                save_movie(details)

                log_watched_movie(
                    user,
                    tmdb_id,
                )

                st.success(
                    "Marked as watched."
                )


# ============================================================
# BUILD MY PROFILE
# ============================================================

elif page == "🧠 Build My Profile":

    st.markdown(
        '<div class="title">'
        '🧠 Build My Profile'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        'Quickly rate films you already know. '
        'The more you rate, the smarter your '
        'recommendations become.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.info(
        f"🎯 Building {user}'s profile"
    )

    # --------------------------------------------------------
    # SESSION STATE
    # --------------------------------------------------------

    if "quick_movies" not in st.session_state:
        st.session_state["quick_movies"] = []

    if "quick_index" not in st.session_state:
        st.session_state["quick_index"] = 0

    if (
        "quick_started_user"
        not in st.session_state
        or
        st.session_state["quick_started_user"]
        != user
    ):

        st.session_state["quick_movies"] = []
        st.session_state["quick_index"] = 0
        st.session_state["quick_started_user"] = user

    # --------------------------------------------------------
    # GET MOVIES
    # --------------------------------------------------------

    if not st.session_state["quick_movies"]:

        with st.spinner(
            "Finding films for you..."
        ):

            movies = get_personal_recommendations(
                user,
                limit=30,
            )

        st.session_state["quick_movies"] = movies
        st.session_state["quick_index"] = 0

    movies = st.session_state["quick_movies"]

    index = st.session_state["quick_index"]

    # --------------------------------------------------------
    # FINISHED
    # --------------------------------------------------------

    if index >= len(movies):

        st.success(
            "🎉 Profile building session complete!"
        )

        st.write(
            "Your ratings have been saved. "
            "Your recommendations will now "
            "start adapting to your tastes."
        )

        if st.button(
            "🔄 Start Another Session",
            key="start_another_profile",
            use_container_width=True,
        ):

            st.session_state["quick_movies"] = []
            st.session_state["quick_index"] = 0

            st.rerun()

    else:

        movie = movies[index]

        poster = image_url(
            movie.get("poster_path"),
            "w780",
        )

        # ----------------------------------------------------
        # PROGRESS
        # ----------------------------------------------------

        progress = (
            index / len(movies)
            if len(movies) > 0
            else 0
        )

        st.progress(progress)

        st.markdown(
            f'<div class="quick-subtitle">'
            f'Film {index + 1} of {len(movies)}'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # MOVIE
        # ----------------------------------------------------

        col1, col2 = st.columns(
            [1, 1.5]
        )

        with col1:

            if poster:

                st.image(
                    poster,
                    use_container_width=True,
                )

        with col2:

            st.markdown(
                '<div class="quick-title">'
                +
                movie.get(
                    "title",
                    "Unknown"
                )
                +
                '</div>',
                unsafe_allow_html=True,
            )

            release = movie.get(
                "release_date",
                ""
            )

            if release:

                st.caption(
                    release[:4]
                )

            rating = movie.get(
                "vote_average"
            )

            if rating:

                st.write(
                    f"⭐ TMDB "
                    f"{rating:.1f}/10"
                )

            overview = movie.get(
                "overview"
            )

            if overview:

                st.write(
                    overview
                )

        st.markdown("---")

        st.markdown(
            '<div class="quick-title">'
            'How much do you like this film?'
            '</div>',
            unsafe_allow_html=True,
        )

        st.write("")

        # ----------------------------------------------------
        # RATING BUTTONS
        # ----------------------------------------------------

        cols = st.columns(5)

        choices = [
            ("😍", "Love", 5.0),
            ("🙂", "Like", 4.0),
            ("😐", "OK", 3.0),
            ("🙁", "Dislike", 2.0),
            ("😡", "Hate", 1.0),
        ]

        for column, choice in zip(
            cols,
            choices
        ):

            emoji, label, value = choice

            with column:

                if st.button(
                    f"{emoji} {label}",
                    key=(
                        f"quick_rating_"
                        f"{user}_"
                        f"{index}_"
                        f"{label}"
                    ),
                    use_container_width=True,
                ):

                    details = get_movie_details(
                        movie["id"]
                    )

                    if details:

                        save_movie(details)

                        save_rating(
                            user,
                            movie["id"],
                            value,
                            None,
                            value == 5.0,
                        )

                    st.session_state[
                        "quick_index"
                    ] += 1

                    st.rerun()

        # ----------------------------------------------------
        # NEVER SEEN
        # ----------------------------------------------------

        if st.button(
            "⏭️ I've never seen this — skip",
            key=(
                f"quick_skip_"
                f"{user}_"
                f"{index}"
            ),
            use_container_width=True,
        ):

            st.session_state[
                "quick_index"
            ] += 1

            st.rerun()

        st.markdown("---")

        st.caption(
            "💡 Tip: Don't overthink it. "
            "Your first instinct is usually "
            "more useful than trying to give "
            "the 'correct' rating."
        )


# ============================================================
# TONIGHT
# ============================================================

elif page == "🍿 Tonight":

    st.markdown(
        '<div class="title">'
        '🍿 What should we watch?'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        'Personalised recommendations based '
        'on what you actually enjoy.'
        '</div>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "👤 For Me",
            "👥 For Both of Us",
            "🎲 Surprise Me",
        ]
    )

    # ========================================================
    # FOR ME
    # ========================================================

    with tab1:

        recommendations = (
            get_personal_recommendations(
                user,
                limit=12,
            )
        )

        if not recommendations:

            st.info(
                "Build your profile using "
                "🧠 Build My Profile first."
            )

        else:

            st.subheader(
                f"🎯 Best matches for {user}"
            )

            cols = st.columns(4)

            for index, movie in enumerate(
                recommendations
            ):

                with cols[index % 4]:

                    display_movie(
                        movie,
                        key_prefix=(
                            f"tonight_personal_"
                            f"{user}_{index}"
                        ),
                    )

    # ========================================================
    # BOTH OF US
    # ========================================================

    with tab2:

        shared = (
            get_shared_recommendations(
                "Anthony",
                "Kseniia",
                limit=12,
            )
        )

        if not shared:

            st.info(
                "Both profiles need some "
                "ratings before I can calculate "
                "your shared taste."
            )

        else:

            st.subheader(
                "🍿 Best matches for both of you"
            )

            cols = st.columns(4)

            for index, movie in enumerate(
                shared
            ):

                with cols[index % 4]:

                    display_movie(
                        movie,
                        key_prefix=(
                            f"tonight_shared_"
                            f"{index}"
                        ),
                    )

    # ========================================================
    # SURPRISE ME
    # ========================================================

    with tab3:

        st.subheader(
            "🎲 Surprise Me"
        )

        if st.button(
            "🎲 Find Something",
            key="surprise_find",
            use_container_width=True,
        ):

            recommendations = (
                get_personal_recommendations(
                    user,
                    limit=12,
                )
            )

            if recommendations:

                display_movie(
                    recommendations[0],
                    key_prefix=(
                        f"surprise_{user}"
                    ),
                )

            else:

                st.warning(
                    "Build your profile first."
                )


# ============================================================
# FIND A MOVIE
# ============================================================

elif page == "🔎 Find a Movie":

    st.title(
        "🔎 Find a Movie"
    )

    query = st.text_input(
        "Search for a film",
        placeholder="e.g. Interstellar",
    )

    if query:

        results = search_movies(
            query
        )

        if not results:

            st.warning(
                "No movies found."
            )

        else:

            cols = st.columns(4)

            for index, movie in enumerate(
                results[:12]
            ):

                with cols[index % 4]:

                    poster = image_url(
                        movie.get(
                            "poster_path"
                        )
                    )

                    if poster:

                        st.image(
                            poster,
                            use_container_width=True,
                        )

                    st.subheader(
                        movie.get(
                            "title",
                            "Unknown",
                        )
                    )

                    release = movie.get(
                        "release_date",
                        ""
                    )

                    if release:

                        st.caption(
                            release[:4]
                        )

                    if movie.get(
                        "vote_average"
                    ):

                        st.write(
                            f"⭐ "
                            f"{movie['vote_average']:.1f}/10"
                        )

                    if st.button(
                        "View",
                        key=(
                            f"search_view_"
                            f"{movie['id']}"
                        ),
                        use_container_width=True,
                    ):

                        details = (
                            get_movie_details(
                                movie["id"]
                            )
                        )

                        if details:

                            save_movie(details)

                            st.session_state[
                                "selected_movie"
                            ] = details

    # --------------------------------------------------------
    # SELECTED MOVIE
    # --------------------------------------------------------

    if "selected_movie" in st.session_state:

        details = st.session_state[
            "selected_movie"
        ]

        st.markdown("---")

        st.title(
            details.get(
                "title",
                "Movie",
            )
        )

        col1, col2 = st.columns(
            [1, 2]
        )

        with col1:

            poster = image_url(
                details.get(
                    "poster_path"
                )
            )

            if poster:

                st.image(
                    poster,
                    use_container_width=True,
                )

        with col2:

            st.write(
                details.get(
                    "overview",
                    "",
                )
            )

            if details.get(
                "vote_average"
            ):

                st.write(
                    f"⭐ TMDB "
                    f"{details['vote_average']:.1f}/10"
                )

            if details.get(
                "runtime"
            ):

                st.write(
                    f"⏱️ "
                    f"{details['runtime']} minutes"
                )

            st.markdown("---")

            col_a, col_b = st.columns(2)

            with col_a:

                if st.button(
                    "📋 Add to My Watchlist",
                    key="selected_watchlist",
                    use_container_width=True,
                ):

                    save_movie(details)

                    add_to_watchlist(
                        user,
                        details["id"],
                    )

                    st.success(
                        "Added to your watchlist."
                    )

            with col_b:

                if st.button(
                    "🎬 Mark Watched",
                    key="selected_watched",
                    use_container_width=True,
                ):

                    save_movie(details)

                    log_watched_movie(
                        user,
                        details["id"],
                    )

                    st.success(
                        "Marked as watched."
                    )


# ============================================================
# WATCHLIST
# ============================================================

elif page == "📋 My Watchlist":

    st.title(
        f"📋 {user}'s Watchlist"
    )

    data = get_watchlist(
        user
    )

    if data.empty:

        st.info(
            "Your watchlist is empty."
        )

    else:

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# WATCHED
# ============================================================

elif page == "🎬 Watched":

    st.title(
        f"🎬 {user}'s Watched Movies"
    )

    data = get_watch_history(
        user,
        limit=100,
    )

    if data.empty:

        st.info(
            "Nothing recorded yet."
        )

    else:

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# RATINGS
# ============================================================

elif page == "⭐ My Ratings":

    st.title(
        f"⭐ {user}'s Ratings"
    )

    data = get_ratings(
        user
    )

    if data.empty:

        st.info(
            "You haven't rated anything yet."
        )

    else:

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    st.subheader(
        "⭐ Rate a Movie"
    )

    search = st.text_input(
        "Search for a movie to rate",
        placeholder="e.g. The Dark Knight",
    )

    selected_movie = None

    if search:

        results = search_movies(
            search
        )

        if results:

            options = {
                (
                    f"{m.get('title', 'Unknown')} "
                    f"({m.get('release_date', '')[:4]})"
                ):
                m["id"]
                for m in results[:10]
            }

            choice = st.selectbox(
                "Choose the movie",
                list(options.keys()),
            )

            if choice:

                selected_movie = (
                    get_movie_details(
                        options[choice]
                    )
                )

    rating = st.slider(
        "Rating",
        0.5,
        5.0,
        3.0,
        0.5,
    )

    review = st.text_area(
        "Review",
        placeholder="Optional",
    )

    favourite = st.checkbox(
        "❤️ Favourite"
    )

    if st.button(
        "Save Rating",
        key="manual_save_rating",
    ):

        if not selected_movie:

            st.error(
                "Search for and select "
                "a movie first."
            )

        else:

            save_movie(
                selected_movie
            )

            save_rating(
                user,
                selected_movie["id"],
                rating,
                review or None,
                favourite,
            )

            st.success(
                f"⭐ {selected_movie['title']} "
                f"rated {rating}/5"
            )

            st.rerun()


# ============================================================
# FAVOURITES
# ============================================================

elif page == "❤️ Favourites":

    st.title(
        f"❤️ {user}'s Favourites"
    )

    data = get_favourites(
        user
    )

    if data.empty:

        st.info(
            "No favourites yet."
        )

    else:

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# BOTH USERS
# ============================================================

elif page == "👥 Anthony + Kseniia":

    st.title(
        "👥 Anthony + Kseniia"
    )

    st.subheader(
        "🍿 Movies you're both likely to enjoy"
    )

    recommendations = (
        get_shared_recommendations(
            "Anthony",
            "Kseniia",
            limit=20,
        )
    )

    if not recommendations:

        st.info(
            "Build both profiles using "
            "🧠 Build My Profile."
        )

    else:

        cols = st.columns(4)

        for index, movie in enumerate(
            recommendations
        ):

            with cols[index % 4]:

                display_movie(
                    movie,
                    key_prefix=(
                        f"both_page_{index}"
                    ),
                )
