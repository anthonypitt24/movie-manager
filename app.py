import streamlit as st

from database import (
    init_db,
    add_movie,
    get_movie_by_tmdb_id,
    add_to_watchlist,
    get_watchlist,
    get_watch_history,
    get_ratings,
    get_favourites,
    get_user_statistics,
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
    }

    .movie-title {
        font-size: 22px;
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
        return False

    try:

        add_movie(
            tmdb_id=details.get("id"),
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
                "cast"
            ),
            directors=details.get(
                "directors"
            ),
            keywords=details.get(
                "keywords"
            ),
        )

        return True

    except TypeError:

        # Compatibility with an older
        # database.py that doesn't yet
        # have the extra movie fields.

        try:

            add_movie(
                tmdb_id=details.get("id"),
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
            )

            return True

        except Exception as e:

            st.error(
                f"Could not save movie: {e}"
            )

            return False

    except Exception as e:

        st.error(
            f"Could not save movie: {e}"
        )

        return False


# ============================================================
# MOVIE CARD
# ============================================================

def display_movie(
    movie,
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

    st.markdown(
        f'<div class="movie-title">'
        f'{movie.get("title", "Unknown")}'
        f'</div>',
        unsafe_allow_html=True,
    )

    release = movie.get(
        "release_date",
        "",
    )

    if release:
        release = release[:4]

    if release:

        st.caption(
            f"📅 {release}"
        )

    tmdb_rating = movie.get(
        "vote_average"
    )

    if tmdb_rating:

        st.write(
            f"⭐ TMDB: {tmdb_rating:.1f}/10"
        )

    match = movie.get(
        "match_score"
    )

    if match is not None:

        st.markdown(
            f'<div class="match">🎯 '
            f'{match:.0f}% Match</div>',
            unsafe_allow_html=True,
        )

    overview = movie.get(
        "overview"
    )

    if overview:

        st.write(
            overview
        )

    reason = movie.get(
        "reason"
    )

    if not reason:

        reason = recommendation_reason(
            movie
        )

    if reason:

        st.caption(
            f"💡 {reason}"
        )

    tmdb_id = movie.get(
        "id"
    )

    if not tmdb_id:
        return

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "📋 Watchlist",
            key=f"{key_prefix}_wl_{tmdb_id}",
            use_container_width=True,
        ):

            details = get_movie_details(
                tmdb_id
            )

            if details:

                if save_movie(details):

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
            key=f"{key_prefix}_watched_{tmdb_id}",
            use_container_width=True,
        ):

            details = get_movie_details(
                tmdb_id
            )

            if details:

                if save_movie(details):

                    log_watched_movie(
                        [user],
                        tmdb_id,
                    )

                    st.success(
                        "Marked as watched."
                    )


# ============================================================
# TONIGHT
# ============================================================

if page == "🍿 Tonight":

    st.markdown(
        '<div class="title">'
        '🍿 What should we watch?'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        'Personalised recommendations based on '
        'your movie tastes.'
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
    # PERSONAL
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
                "I need a few highly-rated "
                "movies from you before I can "
                "make personalised recommendations."
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
                        key_prefix=f"personal_{index}",
                    )

    # ========================================================
    # BOTH
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
                "Once both of you have rated "
                "some movies, I'll find films "
                "that match you both."
            )

        else:

            st.subheader(
                "🍿 Best matches for Anthony + Kseniia"
            )

            cols = st.columns(4)

            for index, movie in enumerate(
                shared
            ):

                with cols[index % 4]:

                    display_movie(
                        movie,
                        key_prefix=f"shared_{index}",
                    )

    # ========================================================
    # SURPRISE
    # ========================================================

    with tab3:

        st.subheader(
            "🎲 Surprise Me"
        )

        st.write(
            "A film you probably wouldn't "
            "have searched for yourself."
        )

        if st.button(
            "🎲 Find Something",
            key="surprise_button",
        ):

            recommendations = (
                get_personal_recommendations(
                    user,
                    limit=12,
                )
            )

            if recommendations:

                movie = recommendations[0]

                display_movie(
                    movie,
                    key_prefix="surprise",
                )

            else:

                st.warning(
                    "I need some ratings first."
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
        key="main_movie_search",
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

            st.subheader(
                f"Search results for '{query}'"
            )

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

                    st.markdown(
                        f"### {movie.get('title', 'Unknown')}"
                    )

                    if movie.get(
                        "release_date"
                    ):

                        st.caption(
                            movie[
                                "release_date"
                            ][:4]
                        )

                    if movie.get(
                        "vote_average"
                    ):

                        st.write(
                            "⭐ "
                            f"{movie['vote_average']:.1f}/10"
                        )

                    if st.button(
                        "View",
                        key=f"search_view_{index}_{movie['id']}",
                        use_container_width=True,
                    ):

                        details = (
                            get_movie_details(
                                movie["id"]
                            )
                        )

                        if details:

                            st.session_state[
                                "selected_movie"
                            ] = details

                            st.rerun()

    # ========================================================
    # SELECTED MOVIE
    # ========================================================

    if (
        "selected_movie"
        in st.session_state
    ):

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

            if details.get(
                "overview"
            ):

                st.write(
                    details["overview"]
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

            st.caption(
                f"TMDB ID: {details.get('id')}"
            )

            col_a, col_b = st.columns(2)

            with col_a:

                if st.button(
                    "📋 Add to My Watchlist",
                    key="selected_watchlist",
                    use_container_width=True,
                ):

                    if save_movie(details):

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

                    if save_movie(details):

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

    # ========================================================
    # RATE A MOVIE
    # ========================================================

    st.subheader(
        "⭐ Rate a Movie"
    )

    st.write(
        "Search for the movie you want to rate."
    )

    rating_search = st.text_input(
        "Movie title",
        placeholder="e.g. Interstellar",
        key="rating_movie_search",
    )

    if rating_search:

        rating_results = search_movies(
            rating_search
        )

        if not rating_results:

            st.warning(
                "No movies found."
            )

        else:

            # ------------------------------------------------
            # BUILD FRIENDLY MOVIE NAMES
            # ------------------------------------------------

            movie_options = []

            for movie in rating_results[:12]:

                year = ""

                if movie.get(
                    "release_date"
                ):

                    year = (
                        movie[
                            "release_date"
                        ][:4]
                    )

                title = movie.get(
                    "title",
                    "Unknown",
                )

                if year:

                    label = (
                        f"{title} ({year})"
                    )

                else:

                    label = title

                movie_options.append(
                    (
                        label,
                        movie["id"],
                    )
                )

            selected_label = st.selectbox(
                "Choose the movie",
                [
                    option[0]
                    for option in movie_options
                ],
                key="rating_movie_select",
            )

            selected_id = dict(
                movie_options
            )[selected_label]

            # ------------------------------------------------
            # GET FULL DETAILS
            # ------------------------------------------------

            selected_details = (
                get_movie_details(
                    selected_id
                )
            )

            if selected_details:

                # Save it to database before
                # rating it.

                if save_movie(
                    selected_details
                ):

                    st.session_state[
                        "rating_movie"
                    ] = selected_details

            # ------------------------------------------------
            # SHOW SELECTED MOVIE
            # ------------------------------------------------

            if (
                "rating_movie"
                in st.session_state
            ):

                movie = st.session_state[
                    "rating_movie"
                ]

                st.markdown("---")

                col1, col2 = st.columns(
                    [1, 2]
                )

                with col1:

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

                with col2:

                    st.subheader(
                        movie.get(
                            "title",
                            "Movie",
                        )
                    )

                    release = movie.get(
                        "release_date"
                    )

                    if release:

                        st.caption(
                            f"📅 {release[:4]}"
                        )

                    if movie.get(
                        "vote_average"
                    ):

                        st.write(
                            f"⭐ TMDB "
                            f"{movie['vote_average']:.1f}/10"
                        )

                    if movie.get(
                        "runtime"
                    ):

                        st.write(
                            f"⏱️ "
                            f"{movie['runtime']} minutes"
                        )

                    if movie.get(
                        "overview"
                    ):

                        st.write(
                            movie["overview"]
                        )

                st.markdown("---")

                # ------------------------------------------------
                # RATING
                # ------------------------------------------------

                st.subheader(
                    "⭐ Your Rating"
                )

                rating = st.slider(
                    "How much did you like it?",
                    0.5,
                    5.0,
                    3.0,
                    0.5,
                    key="movie_rating_slider",
                )

                # Visual stars

                full_stars = int(
                    rating
                )

                stars = (
                    "⭐" * full_stars
                )

                st.markdown(
                    f"## {stars} {rating:.1f}/5"
                )

                review = st.text_area(
                    "Your review / notes",
                    placeholder=(
                        "What did you think? "
                        "What did you like or dislike?"
                    ),
                    key="movie_review",
                )

                favourite = st.checkbox(
                    "❤️ Add to Favourites",
                    key="movie_favourite",
                )

                if st.button(
                    "💾 Save My Rating",
                    key="save_movie_rating",
                    use_container_width=True,
                ):

                    try:

                        save_rating(
                            user,
                            int(
                                movie["id"]
                            ),
                            rating,
                            review or None,
                            favourite,
                        )

                        st.success(
                            f"⭐ {movie['title']} "
                            "rated successfully!"
                        )

                        # Clear selected rating
                        # so next movie can be chosen.

                        if (
                            "rating_movie"
                            in st.session_state
                        ):

                            del st.session_state[
                                "rating_movie"
                            ]

                    except Exception as e:

                        st.error(
                            f"Could not save rating: {e}"
                        )


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
        "🍿 Movies we're likely to both enjoy"
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
            "Rate some movies first. "
            "The more you rate, the better "
            "the recommendations become."
        )

    else:

        cols = st.columns(4)

        for index, movie in enumerate(
            recommendations
        ):

            with cols[index % 4]:

                display_movie(
                    movie,
                    key_prefix=f"both_{index}",
                )
