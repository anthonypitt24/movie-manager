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

from tmdb import search_movies, get_movie_details, image_url

from recommendations import (
    get_personal_recommendations,
    get_shared_recommendations,
    get_quick_profile_movies,
    recommendation_reason,
    TASTE_PRESETS,
)


st.set_page_config(
    page_title="Movie Manager",
    page_icon="🎬",
    layout="wide",
)

init_db()

st.markdown("""
<style>
.title {font-size:42px;font-weight:800;}
.subtitle {font-size:19px;opacity:.7;margin-bottom:25px;}
.match {font-size:24px;font-weight:800;}
.quick-title {text-align:center;font-size:32px;font-weight:800;}
.quick-subtitle {text-align:center;opacity:.7;margin-bottom:15px;}
.big-choice button {font-size:18px !important; min-height:70px;}
</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🎬 Movie Manager")

user = st.sidebar.selectbox(
    "Your profile",
    ["Anthony", "Kseniia"],
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
# HELPERS
# ============================================================

def save_movie(details):
    if not details:
        return

    credits = details.get("credits") or {}
    crew = credits.get("crew") or []

    directors = [
        person for person in crew
        if person.get("job") == "Director"
    ]

    keywords = (details.get("keywords") or {}).get("keywords", [])

    add_movie(
        tmdb_id=details["id"],
        title=details.get("title", "Unknown"),
        original_title=details.get("original_title"),
        overview=details.get("overview"),
        release_date=details.get("release_date"),
        runtime=details.get("runtime"),
        vote_average=details.get("vote_average"),
        vote_count=details.get("vote_count"),
        poster_path=details.get("poster_path"),
        backdrop_path=details.get("backdrop_path"),
        genres=details.get("genres") or [],
        cast=credits.get("cast") or [],
        directors=directors,
        keywords=keywords,
    )


def display_movie(movie, show_buttons=True, compact=False):
    poster = image_url(movie.get("poster_path"))

    if poster:
        st.image(poster, use_container_width=True)

    st.subheader(movie.get("title", "Unknown"))

    release = movie.get("release_date", "")
    if release:
        st.caption(f"📅 {release[:4]}")

    rating = movie.get("vote_average")
    if rating:
        st.write(f"⭐ TMDB: {float(rating):.1f}/10")

    match = movie.get("match_score")
    if match is not None:
        st.markdown(
            f'<div class="match">🎯 {match:.0f}% Match</div>',
            unsafe_allow_html=True,
        )

    if not compact and movie.get("overview"):
        st.write(movie["overview"])

    st.caption(
        "💡 " + recommendation_reason(movie, user)
    )

    if not show_buttons or not movie.get("id"):
        return

    tmdb_id = movie["id"]

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "📋 Watchlist",
            key=f"wl_{tmdb_id}_{user}",
            use_container_width=True,
        ):
            details = get_movie_details(tmdb_id)
            if details:
                save_movie(details)
                add_to_watchlist(user, tmdb_id)
                st.success("Added to watchlist.")

    with col2:
        if st.button(
            "🎬 Watched",
            key=f"watched_{tmdb_id}_{user}",
            use_container_width=True,
        ):
            details = get_movie_details(tmdb_id)
            if details:
                save_movie(details)
                log_watched_movie(user, tmdb_id)
                st.success("Marked as watched.")


# ============================================================
# BUILD PROFILE
# ============================================================

if page == "🧠 Build My Profile":

    st.markdown(
        '<div class="title">🧠 Build My Profile</div>',
        unsafe_allow_html=True,
    )

    preset = TASTE_PRESETS.get(user, TASTE_PRESETS["Anthony"])

    st.markdown(
        '<div class="subtitle">'
        'A fast taste test. No searching — just tell me what you think.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.info(
        f"🎯 Building {user}'s taste profile\n\n"
        + "  •  ".join(preset["labels"])
    )

    # New session whenever the selected user changes.
    if st.session_state.get("quick_user") != user:
        st.session_state.quick_user = user
        st.session_state.quick_movies = []
        st.session_state.quick_index = 0

    if not st.session_state.get("quick_movies"):
        with st.spinner("Finding a good mix of films..."):
            st.session_state.quick_movies = get_quick_profile_movies(
                user, limit=30
            )
            st.session_state.quick_index = 0

    movies = st.session_state.quick_movies
    index = st.session_state.quick_index

    if not movies:
        st.warning(
            "I couldn't find enough films from TMDB. "
            "Check that your TMDB API token is working."
        )

    elif index >= len(movies):
        st.success("🎉 Taste test complete!")
        st.write(
            f"{user}'s ratings have been saved. "
            "The recommendation engine can now use them."
        )

        if st.button("🔄 Do another taste test", use_container_width=True):
            st.session_state.quick_movies = []
            st.session_state.quick_index = 0
            st.rerun()

    else:
        movie = movies[index]

        st.progress((index + 1) / len(movies))
        st.markdown(
            f'<div class="quick-subtitle">'
            f'Film {index + 1} of {len(movies)}'
            f'</div>',
            unsafe_allow_html=True,
        )

        left, right = st.columns([1, 1.5])

        with left:
            poster = image_url(movie.get("poster_path"), "w780")
            if poster:
                st.image(poster, use_container_width=True)

        with right:
            st.markdown(
                f'<div class="quick-title">{movie.get("title", "Unknown")}</div>',
                unsafe_allow_html=True,
            )

            release = movie.get("release_date", "")
            if release:
                st.caption(release[:4])

            rating = movie.get("vote_average")
            if rating:
                st.write(f"⭐ TMDB {float(rating):.1f}/10")

            genres = movie.get("genre_ids") or []
            if genres:
                st.caption("🎬 " + " • ".join(
                    name for name, gid in {
                        "Action": 28, "Adventure": 12, "Comedy": 35,
                        "Crime": 80, "Drama": 18, "Fantasy": 14,
                        "Horror": 27, "Mystery": 9648,
                        "Romance": 10749, "Sci-Fi": 878,
                        "Thriller": 53
                    }.items() if gid in genres
                ))

            if movie.get("overview"):
                st.write(movie["overview"])

        st.markdown("---")

        st.markdown(
            '<div class="quick-title">How do you feel about this film?</div>',
            unsafe_allow_html=True,
        )

        choices = [
            ("😍", "LOVE IT", 5.0),
            ("🙂", "LIKE IT", 4.0),
            ("😐", "IT'S OK", 3.0),
            ("🙁", "DON'T LIKE", 2.0),
            ("😡", "HATE IT", 1.0),
        ]

        cols = st.columns(5)

        for col, (emoji, label, value) in zip(cols, choices):
            with col:
                if st.button(
                    f"{emoji}\n{label}",
                    key=f"taste_{user}_{index}_{value}",
                    use_container_width=True,
                ):
                    details = get_movie_details(movie["id"])

                    if details:
                        save_movie(details)
                        save_rating(
                            user,
                            movie["id"],
                            value,
                            None,
                            value == 5.0,
                        )

                    st.session_state.quick_index += 1
                    st.rerun()

        st.write("")

        if st.button(
            "⏭️ HAVEN'T SEEN IT — SKIP",
            key=f"skip_{user}_{index}",
            use_container_width=True,
        ):
            st.session_state.quick_index += 1
            st.rerun()

        st.caption(
            "💡 Don't overthink it. Your first reaction is the useful bit."
        )


# ============================================================
# TONIGHT
# ============================================================

elif page == "🍿 Tonight":

    st.markdown(
        '<div class="title">🍿 What should we watch?</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        'Personalised recommendations based on your tastes.'
        '</div>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(
        ["👤 For Me", "👥 For Both of Us", "🎲 Surprise Me"]
    )

    with tab1:
        recommendations = get_personal_recommendations(user, 12)

        if not recommendations:
            st.info("Use 🧠 Build My Profile first.")
        else:
            st.subheader(f"🎯 Best matches for {user}")
            cols = st.columns(4)
            for i, movie in enumerate(recommendations):
                with cols[i % 4]:
                    display_movie(movie)

    with tab2:
        shared = get_shared_recommendations("Anthony", "Kseniia", 12)

        if not shared:
            st.info("Build both profiles first.")
        else:
            st.subheader("🍿 Best matches for both of you")
            cols = st.columns(4)
            for i, movie in enumerate(shared):
                with cols[i % 4]:
                    display_movie(movie)

    with tab3:
        st.subheader("🎲 Surprise Me")

        if st.button("🎲 Find Something", use_container_width=True):
            recommendations = get_personal_recommendations(user, 12)

            if recommendations:
                st.session_state.surprise_movie = recommendations[0]

        if st.session_state.get("surprise_movie"):
            display_movie(st.session_state.surprise_movie)


# ============================================================
# SEARCH
# ============================================================

elif page == "🔎 Find a Movie":

    st.title("🔎 Find a Movie")

    query = st.text_input(
        "Search for a film",
        placeholder="e.g. Interstellar",
    )

    if query:
        results = search_movies(query)

        if not results:
            st.warning("No movies found.")
        else:
            cols = st.columns(4)

            for i, movie in enumerate(results[:12]):
                with cols[i % 4]:
                    poster = image_url(movie.get("poster_path"))
                    if poster:
                        st.image(poster, use_container_width=True)

                    st.subheader(movie.get("title", "Unknown"))

                    if movie.get("release_date"):
                        st.caption(movie["release_date"][:4])

                    if movie.get("vote_average"):
                        st.write(
                            f"⭐ {float(movie['vote_average']):.1f}/10"
                        )

                    if st.button(
                        "View",
                        key=f"view_{movie['id']}",
                        use_container_width=True,
                    ):
                        details = get_movie_details(movie["id"])
                        if details:
                            save_movie(details)
                            st.session_state.selected_movie = details

    if st.session_state.get("selected_movie"):
        details = st.session_state.selected_movie

        st.markdown("---")
        st.title(details.get("title", "Movie"))

        left, right = st.columns([1, 2])

        with left:
            poster = image_url(details.get("poster_path"))
            if poster:
                st.image(poster, use_container_width=True)

        with right:
            st.write(details.get("overview", ""))

            if details.get("vote_average"):
                st.write(
                    f"⭐ TMDB {float(details['vote_average']):.1f}/10"
                )

            if details.get("runtime"):
                st.write(f"⏱️ {details['runtime']} minutes")

            if st.button(
                "📋 Add to My Watchlist",
                use_container_width=True,
            ):
                save_movie(details)
                add_to_watchlist(user, details["id"])
                st.success("Added to your watchlist.")

            if st.button(
                "🎬 Mark as Watched",
                use_container_width=True,
            ):
                save_movie(details)
                log_watched_movie(user, details["id"])
                st.success("Marked as watched.")


# ============================================================
# WATCHLIST
# ============================================================

elif page == "📋 My Watchlist":

    st.title(f"📋 {user}'s Watchlist")

    data = get_watchlist(user)

    if data.empty:
        st.info("Your watchlist is empty.")
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

    st.title(f"🎬 {user}'s Watched Movies")

    data = get_watch_history(user, 100)

    if data.empty:
        st.info("Nothing recorded yet.")
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

    st.title(f"⭐ {user}'s Ratings")

    data = get_ratings(user)

    if data.empty:
        st.info("You haven't rated anything yet.")
    else:
        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")
    st.subheader("⭐ Rate a Movie")

    search = st.text_input(
        "Search for a movie to rate",
        placeholder="e.g. The Dark Knight",
    )

    selected_movie = None

    if search:
        results = search_movies(search)

        if results:
            options = {
                f"{m.get('title', 'Unknown')} "
                f"({m.get('release_date', '')[:4]})": m["id"]
                for m in results[:10]
            }

            choice = st.selectbox(
                "Choose the movie",
                list(options.keys()),
            )

            if choice:
                selected_movie = get_movie_details(options[choice])

    rating = st.slider(
        "Rating",
        0.5, 5.0, 3.0, 0.5
    )

    review = st.text_area(
        "Review",
        placeholder="Optional",
    )

    favourite = st.checkbox("❤️ Favourite")

    if st.button(
        "Save Rating",
        use_container_width=True,
    ):
        if not selected_movie:
            st.error("Search for and select a movie first.")
        else:
            save_movie(selected_movie)
            save_rating(
                user,
                selected_movie["id"],
                rating,
                review or None,
                favourite,
            )
            st.success(
                f"⭐ {selected_movie['title']} rated {rating}/5"
            )
            st.rerun()


# ============================================================
# FAVOURITES
# ============================================================

elif page == "❤️ Favourites":

    st.title(f"❤️ {user}'s Favourites")

    data = get_favourites(user)

    if data.empty:
        st.info("No favourites yet.")
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

    st.title("👥 Anthony + Kseniia")

    st.subheader("🍿 Movies you're both likely to enjoy")

    recommendations = get_shared_recommendations(
        "Anthony",
        "Kseniia",
        20,
    )

    if not recommendations:
        st.info("Build both profiles using 🧠 Build My Profile.")
    else:
        cols = st.columns(4)

        for i, movie in enumerate(recommendations):
            with cols[i % 4]:
                display_movie(movie)
