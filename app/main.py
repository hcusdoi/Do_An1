"""
main.py — Movie Recommender Web App (FastAPI)
Chay bang lenh: python -m uvicorn app.main:app --reload
Hoac truc tiep:  python app/main.py
"""
import sys, os

# Ensure project root is in path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from fastapi import FastAPI, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from typing import Optional
import uvicorn

from bll import BLL

# ─── App setup ────────────────────────────────────────────────────────
app = FastAPI(title="Movie Recommender Demo")

# Session middleware (luu session trong cookie)
app.add_middleware(SessionMiddleware, secret_key="movie_rec_secret_2024", max_age=86400)

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)



# ─── Helpers ──────────────────────────────────────────────────────────
def current_user(request: Request):
    """Lay thong tin user hien tai tu session."""
    return request.session.get("user")

def require_login(request: Request):
    """Redirect ve trang login neu chua dang nhap."""
    u = current_user(request)
    if not u:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return u


# ─── TRANG CHU ────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = current_user(request)
    with BLL() as db:
        popular = db.get_popular_movies(limit=12)
        genres  = db.get_all_genres()
    return templates.TemplateResponse(request=request, name="index.html", context={
        "user": user,
        "popular_movies": popular,
        "genres": genres,
        "page": "home"
    })


# ─── ĐĂNG NHẬP ────────────────────────────────────────────────────────
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None, next: str = "/"):
    if current_user(request):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse(request=request, name="login.html", context={
        "error": error, "next": next, "page": "login"
    })

@app.post("/login")
async def login_post(request: Request,
                     username: str = Form(...),
                     password: str = Form(...),
                     next: str = Form("/")):
    with BLL() as db:
        user = db.login(username.strip(), password)
    if user:
        # Luu session (khong luu password_hash)
        request.session["user"] = user.model_dump()
        return RedirectResponse(next or "/", status_code=302)
    return templates.TemplateResponse(request=request, name="login.html", context={
        "error": "Tên đăng nhập hoặc mật khẩu không đúng",
        "next": next, "page": "login"
    })


# ─── ĐĂNG KÝ ──────────────────────────────────────────────────────────
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    if current_user(request):
        return RedirectResponse("/", status_code=302)
    with BLL() as db:
        genres = db.get_all_genres()
    return templates.TemplateResponse(request=request, name="register.html", context={
        "genres": genres, "page": "register"
    })

@app.post("/register")
async def register_post(request: Request,
                        username: str = Form(...),
                        email: str = Form(...),
                        password: str = Form(...),
                        confirm_password: str = Form(...),
                        display_name: str = Form(""),
                        fav_genres: list = Form(default=[])):
    errors = []
    if len(password) < 6:
        errors.append("Mật khẩu phải có ít nhất 6 ký tự")
    if password != confirm_password:
        errors.append("Mật khẩu xác nhận không khớp")
    if len(username) < 3:
        errors.append("Tên đăng nhập phải có ít nhất 3 ký tự")

    if errors:
        with BLL() as db:
            genres = db.get_all_genres()
        return templates.TemplateResponse(request=request, name="register.html", context={
            "errors": errors,
            "genres": genres, "page": "register"
        })

    with BLL() as db:
        result = db.register(username, email, password,
                             display_name or username)
        if result.ok:
            user_id = result.user.id
            # Luu so thich the loai
            if fav_genres:
                db.set_genre_preferences(user_id, fav_genres[:5])
            request.session["user"] = result.user.model_dump()
            return RedirectResponse("/onboarding", status_code=302)
        else:
            genres = db.get_all_genres()
            return templates.TemplateResponse(request=request, name="register.html", context={
                "errors": [result.error],
                "genres": genres, "page": "register"
            })


# ─── ONBOARDING (sau dang ki) ─────────────────────────────────────────
@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    with BLL() as db:
        popular = db.get_popular_movies(limit=20)
        genres  = db.get_all_genres()
    return templates.TemplateResponse(request=request, name="onboarding.html", context={
        "user": user,
        "popular_movies": popular, "genres": genres, "page": "onboarding"
    })


# ─── ĐĂNG XUẤT ────────────────────────────────────────────────────────
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)


# ─── TRANG GỢI Ý ──────────────────────────────────────────────────────
@app.get("/recommendations", response_class=HTMLResponse)
async def recommendations_page(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login?next=/recommendations", status_code=302)

    user_id = user["id"]
    recs_cf = recs_cbf = recs_hybrid = []

    with BLL() as db:
        # Kiem tra cache
        recs_hybrid = db.get_cached_recommendations(user_id, "Hybrid") or []
        rated_count = len(db.get_user_ratings(user_id))

        # Neu chua co cache va co model
        if not recs_hybrid:
            try:
                df = db.get_hybrid_recommendations(
                    user_id=user_id, top_n=12, cf_weight=0.7)
                if df is not None and not df.empty:
                    if "genres_clean" in df.columns:
                        df["genres_clean"] = df["genres_clean"].apply(
                            lambda x: ", ".join(x) if isinstance(x, list) else str(x))
                    recs_hybrid = df.fillna("").to_dict(orient="records")
                    db.save_recommendations(user_id, "Hybrid", recs_hybrid)
            except Exception as e:
                print(f"Hybrid rec error: {e}")

        # Fallback: popular neu chua du ratings
        if not recs_hybrid:
            recs_hybrid = db.get_popular_movies(limit=12)

        genres = db.get_all_genres()

    return templates.TemplateResponse(request=request, name="recommendations.html", context={
        "user": user,
        "recs_hybrid": recs_hybrid,
        "rated_count": rated_count,
        "genres": genres, "page": "recommendations"
    })


# ─── TRANG PHIM ───────────────────────────────────────────────────────
@app.get("/movies", response_class=HTMLResponse)
async def movies_page(request: Request,
                      search: str = None, genre: str = None,
                      page_num: int = 1):
    user = current_user(request)
    per_page = 24
    offset   = (page_num - 1) * per_page
    with BLL() as db:
        movies  = db.get_movies(limit=per_page, offset=offset,
                                genre=genre, search=search)
        genres  = db.get_all_genres()
        # Total for pagination
        total_q = "SELECT COUNT(*) FROM movies WHERE 1=1"
        params  = []
        if genre:
            total_q += " AND genres LIKE ?"; params.append(f"%{genre}%")
        if search:
            total_q += " AND title LIKE ?"; params.append(f"%{search}%")
        total = db.conn.execute(total_q, params).fetchone()[0] if False else len(movies)

    return templates.TemplateResponse(request=request, name="movies.html", context={
        "user": user,
        "movies": movies, "genres": genres,
        "search": search or "", "genre": genre or "",
        "page_num": page_num, "per_page": per_page,
        "page": "movies"
    })


# ─── CHI TIẾT PHIM ────────────────────────────────────────────────────
@app.get("/movie/{movie_id}", response_class=HTMLResponse)
async def movie_detail(request: Request, movie_id: int):
    user = current_user(request)
    with BLL() as db:
        movie = db.get_movie_by_id(movie_id)
        if not movie:
            raise HTTPException(404, "Không tìm thấy phim")
        reviews  = db.get_movie_ratings(movie_id, limit=10)
        user_rating = None
        in_watchlist = False
        if user:
            user_rating  = db.get_user_rating_for_movie(user["id"], movie_id)
            in_watchlist = db.is_in_watchlist(user["id"], movie_id)
            db.log_action(user["id"], movie_id, "view")

        # Phim tuong tu (CBF)
        similar = []
        try:
            df = db.get_hybrid_recommendations(
                movie_id=movie_id, top_n=6, cf_weight=0.0)
            if df is not None and not df.empty:
                if "genres_clean" in df.columns:
                    df["genres_clean"] = df["genres_clean"].apply(
                        lambda x: ", ".join(x) if isinstance(x, list) else str(x))
                similar = df.fillna("").to_dict(orient="records")
        except Exception as e:
            print(f"Similar rec error: {e}")

    return templates.TemplateResponse(request=request, name="movie_detail.html", context={
        "user": user,
        "movie": movie, "reviews": reviews,
        "user_rating": user_rating, "in_watchlist": in_watchlist,
        "similar": similar, "page": "movies"
    })


# ─── HỒ SƠ NGƯỜI DÙNG ─────────────────────────────────────────────────
@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login?next=/profile", status_code=302)
    with BLL() as db:
        ratings   = db.get_user_ratings(user["id"])
        watchlist = db.get_watchlist(user["id"])
        genres    = db.get_genre_preferences(user["id"])
        history   = db.get_user_history(user["id"], limit=10)
    return templates.TemplateResponse(request=request, name="profile.html", context={
        "user": user,
        "ratings": ratings, "watchlist": watchlist,
        "genre_prefs": genres, "history": history,
        "page": "profile"
    })


# ─── API ENDPOINTS ────────────────────────────────────────────────────
@app.post("/api/rate")
async def api_rate(request: Request,
                   movie_id: int = Form(...),
                   rating: float = Form(...)):
    user = current_user(request)
    if not user:
        return JSONResponse({"ok": False, "error": "Chưa đăng nhập"}, 401)
    with BLL() as db:
        ok = db.rate_movie(user["id"], movie_id, rating)
    return JSONResponse({"ok": ok})

@app.post("/api/watchlist/toggle")
async def api_watchlist_toggle(request: Request,
                                movie_id: int = Form(...)):
    user = current_user(request)
    if not user:
        return JSONResponse({"ok": False, "error": "Chưa đăng nhập"}, 401)
    with BLL() as db:
        in_wl = db.is_in_watchlist(user["id"], movie_id)
        if in_wl:
            db.remove_from_watchlist(user["id"], movie_id)
            action = "removed"
        else:
            db.add_to_watchlist(user["id"], movie_id)
            action = "added"
    return JSONResponse({"ok": True, "action": action})

@app.get("/api/search")
async def api_search(q: str = Query(""), limit: int = 10):
    with BLL() as db:
        results = db.search_movies(q, limit=limit)
    return JSONResponse(results)

@app.get("/api/movies")
async def api_movies(genre: str = None, search: str = None,
                     limit: int = 24, offset: int = 0):
    with BLL() as db:
        movies = db.get_movies(limit=limit, offset=offset,
                               genre=genre, search=search)
    return JSONResponse(movies)

@app.get("/api/recommend")
async def api_recommend(request: Request,
                         user_id: int = Query(None),
                         movie_id: int = Query(None),
                         top_n: int = 12,
                         cf_weight: float = 0.7):
    try:
        with BLL() as db:
            df = db.get_hybrid_recommendations(
                user_id=user_id, movie_id=movie_id,
                top_n=top_n, cf_weight=cf_weight)
            if df is None or df.empty:
                return JSONResponse([])
            if "genres_clean" in df.columns:
                df["genres_clean"] = df["genres_clean"].apply(
                    lambda x: ", ".join(x) if isinstance(x, list) else str(x))
            return JSONResponse(df.fillna("").to_dict(orient="records"))
    except Exception as e:
        return JSONResponse({"error": str(e)}, 500)

@app.post("/api/genres")
async def api_set_genres(request: Request, genres: list = Form(...)):
    user = current_user(request)
    if not user:
        return JSONResponse({"ok": False}, 401)
    with BLL() as db:
        db.set_genre_preferences(user["id"], genres)
    return JSONResponse({"ok": True})


# ─── ENTRY POINT ──────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
