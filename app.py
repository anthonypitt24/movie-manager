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
# PAGE
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
# MOVIE CARD
# ============================================================

def display_movie(movie):

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
        release = release[:4]

    if release:
        st.caption(
            f"📅 {release}"
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

    st.caption(
        f"💡 {reason}"
    )

    tmdb_id = movie.get(
        "id"
    )

    if tmdb_id:

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "📋 Watchlist",
                key=f"wl_{tmdb_id}",
            ):

                details = get_movie_details(
                    tmdb_id
                )

                if details:

                    save_movie(
                        details
                    )

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
                key=f"watched_{tmdb_id}",
            ):

                details = get_movie_details(
                    tmdb_id
                )

                if details:

                    save_movie(
                        details
                    )

                    log_watched_movie(
                        [user],
                        tmdb_id,
                    )

                    st.success(
                        "Marked as watched."
                    )


# ============================================================
# SAVE TMDB MOVIE
# ============================================================

def save_movie(details):

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

    # --------------------------------------------------------
    # PERSONAL
    # --------------------------------------------------------

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

                with cols[
                    index % 4
                ]:

                    display_movie(
                        movie
                    )

    # --------------------------------------------------------
    # BOTH
    # --------------------------------------------------------

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

                with cols[
                    index % 4
                ]:

                    display_movie(
                        movie
                    )

    # --------------------------------------------------------
    # SURPRISE
    # --------------------------------------------------------

    with tab3:

        st.subheader(
            "🎲 Surprise Me"
        )

        st.write(
            "A film you probably wouldn't "
            "have searched for yourself."
        )

        if st.button(
            "🎲 Find Something"
        ):

            recommendations = (
                get_personal_recommendations(
                    user,
                    limit=12,
                )
            )

            if recommendations:

                movie = recommendations[
                    0
                ]

                display_movie(
                    movie
                )

            else:

                st.warning(
                    "I need some ratings first."
                )


# ============================================================
# SEARCH
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

                with cols[
                    index % 4
                ]:

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
                        key=f"view_{movie['id']}",
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

            if st.button(
                "📋 Add to My Watchlist"
            ):

                save_movie(
                    details
                )

                add_to_watchlist(
                    user,
                    details["id"],
                )

                st.success(
                    "Added to your watchlist."
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

    tmdb_id = st.number_input(
        "TMDB Movie ID",
        min_value=1,
        step=1,
    )

    rating = st.slider(
        "Rating",
        0.5,
        5.0,
        3.0,
        0.5,
    )

    review = st.text_area(
        "Review"
    )

    favourite = st.checkbox(
        "❤️ Favourite"
    )

    if st.button(
        "Save Rating"
    ):

        movie = get_movie_by_tmdb_id(
            int(tmdb_id)
        )

        if not movie:

            st.error(
                "Find the movie using "
                "Movie Search first."
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
                "Rating saved."
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

            with cols[
                index % 4
            ]:

                display_movie(
                    movie
                )
