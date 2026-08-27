import streamlit as st

from database import (
    init_db,
    add_movie,
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

    .movie-info {
        opacity: 0.75;
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
# SAVE TMDB MOVIE
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
        )
        if details.get("credits")
        else [],
        directors=[],
        keywords=details.get(
            "keywords",
            {}
        ).get(
            "keywords",
            []
        )
        if details.get("keywords")
        else [],
    )


# ============================================================
# MOVIE CARD
# ============================================================

def display_movie(
    movie,
    key_suffix="default",
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

    # --------------------------------------------------------
    # WATCHLIST
    # --------------------------------------------------------

    with col1:

        if st.button(
            "📋 Watchlist",
            key=f"wl_{tmdb_id}_{key_suffix}",
            use_container_width=True,
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

    # --------------------------------------------------------
    # WATCHED
    # --------------------------------------------------------

    with col2:

        if st.button(
            "🎬 Watched",
            key=f"watched_{tmdb_id}_{key_suffix}",
            use_container_width=True,
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
    # PERSONAL RECOMMENDATIONS
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

                with cols[
                    index % 4
                ]:

                    display_movie(
                        movie,
                        key_suffix=f"personal_{index}",
                    )

    # ========================================================
    # SHARED RECOMMENDATIONS
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

                with cols[
                    index % 4
                ]:

                    display_movie(
                        movie,
                        key_suffix=f"shared_{index}",
                    )

    # ========================================================
    # SURPRISE ME
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
            key="surprise_find_button",
        ):

            recommendations = (
                get_personal_recommendations(
                    user,
                    limit=12,
                )
            )

            if recommendations:

                movie = recommendations[0]

                st.session_state[
                    "surprise_movie"
                ] = movie

            else:

                st.warning(
                    "I need some ratings first."
                )

        if (
            "surprise_movie"
            in st.session_state
        ):

            display_movie(
                st.session_state[
                    "surprise_movie"
                ],
                key_suffix="surprise",
            )


# ============================================================
# FIND A MOVIE
# ============================================================

elif page == "🔎 Find a Movie":

    st.title(
        "🔎 Find a Movie"
    )

    st.write(
        "Search TMDB by movie title."
    )

    query = st.text_input(
        "Search for a film",
        placeholder="e.g. Interstellar",
        key="movie_search",
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
                "Search Results"
            )

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

                    st.markdown(
                        f"**{movie.get('title', 'Unknown')}**"
                    )

                    release = movie.get(
                        "release_date"
                    )

                    if release:

                        st.caption(
                            release[:4]
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
                        key=f"view_{movie['id']}_{index}",
                        use_container_width=True,
                    ):

                        details = (
                            get_movie_details(
                                movie["id"]
                            )
                        )

                        if details:

                            save_movie(
                                details
                            )

                            st.session_state[
                                "selected_movie"
                            ] = details

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

            col_a, col_b = st.columns(2)

            with col_a:

                if st.button(
                    "📋 Add to My Watchlist",
                    key="selected_add_watchlist",
                    use_container_width=True,
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

            with col_b:

                if st.button(
                    "🎬 Mark Watched",
                    key="selected_mark_watched",
                    use_container_width=True,
                ):

                    save_movie(
                        details
                    )

                    log_watched_movie(
                        [user],
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

    st.write(
        "Rate movies you've watched. "
        "Just search for the movie title — "
        "you don't need to know any TMDB or IMDb number."
    )

    # ========================================================
    # EXISTING RATINGS
    # ========================================================

    data = get_ratings(
        user
    )

    if data.empty:

        st.info(
            "You haven't rated anything yet."
        )

    else:

        st.subheader(
            "Your Ratings"
        )

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    # ========================================================
    # SEARCH FOR MOVIE TO RATE
    # ========================================================

    st.subheader(
        "🎬 Rate a Movie"
    )

    rating_search = st.text_input(
        "Search for the movie",
        placeholder="e.g. Interstellar, The Martian, Gladiator...",
        key="rating_movie_search",
    )

    selected_rating_movie = None

    if rating_search:

        rating_results = search_movies(
            rating_search
        )

        if not rating_results:

            st.warning(
                "No movies found. "
                "Try another title."
            )

        else:

            # ------------------------------------------------
            # Create readable labels
            # ------------------------------------------------

            movie_options = []

            for movie in rating_results[:10]:

                title = movie.get(
                    "title",
                    "Unknown",
                )

                release = movie.get(
                    "release_date",
                    ""
                )

                year = (
                    release[:4]
                    if release
                    else "Unknown year"
                )

                tmdb_rating = movie.get(
                    "vote_average"
                )

                if tmdb_rating:

                    label = (
                        f"{title} "
                        f"({year}) — "
                        f"⭐ {tmdb_rating:.1f}/10"
                    )

                else:

                    label = (
                        f"{title} "
                        f"({year})"
                    )

                movie_options.append(
                    (
                        label,
                        movie["id"],
                    )
                )

            # ------------------------------------------------
            # Movie selector
            # ------------------------------------------------

            selected_label = st.selectbox(
                "Choose the movie",
                [
                    option[0]
                    for option in movie_options
                ],
                key="rating_movie_selector",
            )

            selected_id = dict(
                movie_options
            )[selected_label]

            # ------------------------------------------------
            # Get full movie details
            # ------------------------------------------------

            selected_rating_movie = (
                get_movie_details(
                    selected_id
                )
            )

    # ========================================================
    # RATING FORM
    # ========================================================

    if selected_rating_movie:

        details = selected_rating_movie

        st.markdown("---")

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

            st.subheader(
                details.get(
                    "title",
                    "Movie",
                )
            )

            release = details.get(
                "release_date"
            )

            if release:

                st.caption(
                    f"📅 {release[:4]}"
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

            if details.get(
                "overview"
            ):

                st.write(
                    details[
                        "overview"
                    ]
                )

        st.markdown("---")

        st.subheader(
            "⭐ Your Rating"
        )

        rating = st.slider(
            "How much did you like it?",
            min_value=0.5,
            max_value=5.0,
            value=3.0,
            step=0.5,
            key=f"rating_value_{details['id']}",
        )

        # Show stars visually

        full_stars = int(
            rating
        )

        half_star = (
            rating - full_stars
            >= 0.5
        )

        stars = (
            "⭐" * full_stars
        )

        if half_star:
            stars += "½"

        st.markdown(
            f"### {stars}  {rating}/5"
        )

        review = st.text_area(
            "Your review / notes",
            placeholder=(
                "What did you think? "
                "What did you like or dislike?"
            ),
            key=f"review_{details['id']}",
        )

        favourite = st.checkbox(
            "❤️ Add to Favourites",
            key=f"favourite_{details['id']}",
        )

        if st.button(
            "💾 Save My Rating",
            key=f"save_rating_{details['id']}",
            use_container_width=True,
        ):

            save_movie(
                details
            )

            save_rating(
                user,
                details["id"],
                rating,
                review or None,
                favourite,
            )

            st.success(
                f"Saved your {rating}/5 rating "
                f"for {details['title']}."
            )

            st.info(
                "🧠 This rating will now help "
                "improve your future recommendations."
            )

    else:

        if not rating_search:

            st.info(
                "👆 Search for a movie above "
                "to start rating it."
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

    st.write(
        "These recommendations are based on "
        "both Anthony's and Kseniia's ratings."
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
                    movie,
                    key_suffix=f"both_{index}",
                )
