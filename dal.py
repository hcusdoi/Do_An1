import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), 'app.db')

class DAL:
    def __init__(self, path: str = DB_PATH):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    # ------------------------------------------------------------------
    # USERS
    # ------------------------------------------------------------------
    def create_user(self, username: str, email: str, password_hash: str, display_name: str) -> Optional[Dict]:
        try:
            cur = self.conn.execute("""
                INSERT INTO users (username, email, password_hash, display_name)
                VALUES (?,?,?,?)
            """, (username.strip(), email.strip().lower(), password_hash, display_name))
            self.conn.commit()
            return self.get_user_by_id(cur.lastrowid)
        except sqlite3.IntegrityError:
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        row = self.conn.execute("""
            SELECT * FROM users WHERE username = ? COLLATE NOCASE
        """, (username,)).fetchone()
        return dict(row) if row else None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        row = self.conn.execute("""
            SELECT * FROM users WHERE email = ? COLLATE NOCASE
        """, (email,)).fetchone()
        return dict(row) if row else None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        row = self.conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(row) if row else None

    def update_last_login(self, user_id: int):
        self.conn.execute("""
            UPDATE users SET last_login = datetime('now','localtime') WHERE id = ?
        """, (user_id,))
        self.conn.commit()

    def update_profile(self, user_id: int, display_name: str = None, avatar_url: str = None) -> bool:
        if display_name:
            self.conn.execute("UPDATE users SET display_name=? WHERE id=?", (display_name, user_id))
        if avatar_url:
            self.conn.execute("UPDATE users SET avatar_url=? WHERE id=?", (avatar_url, user_id))
        self.conn.commit()
        return True

    def update_password(self, user_id: int, password_hash: str) -> bool:
        self.conn.execute("UPDATE users SET password_hash=? WHERE id=?", (password_hash, user_id))
        self.conn.commit()
        return True

    # ------------------------------------------------------------------
    # MOVIES
    # ------------------------------------------------------------------
    def get_movies(self, limit: int = 50, offset: int = 0, genre: str = None, search: str = None, sort_by: str = 'num_ratings') -> List[Dict]:
        q = "SELECT * FROM movies WHERE 1=1"
        params: List[Any] = []
        if genre:
            q += " AND genres LIKE ?"
            params.append(f'%{genre}%')
        if search:
            q += " AND title LIKE ?"
            params.append(f'%{search}%')
        safe_sort = sort_by if sort_by in ('num_ratings','avg_rating','title','year') else 'num_ratings'
        q += f" ORDER BY {safe_sort} DESC LIMIT ? OFFSET ?"
        params += [limit, offset]
        rows = self.conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]

    def get_movie_by_id(self, movie_id: int) -> Optional[Dict]:
        row = self.conn.execute("SELECT * FROM movies WHERE movie_id=?", (movie_id,)).fetchone()
        return dict(row) if row else None

    def search_movies(self, query: str, limit: int = 20) -> List[Dict]:
        rows = self.conn.execute("""
            SELECT * FROM movies WHERE title LIKE ? ORDER BY num_ratings DESC LIMIT ?
        """, (f'%{query}%', limit)).fetchall()
        return [dict(r) for r in rows]

    def get_popular_movies(self, limit: int = 20, genre: str = None) -> List[Dict]:
        q = "SELECT * FROM movies WHERE num_ratings > 0"
        params: List[Any] = []
        if genre:
            q += " AND genres LIKE ?"
            params.append(f'%{genre}%')
        q += " ORDER BY num_ratings DESC LIMIT ?"
        params.append(limit)
        return [dict(r) for r in self.conn.execute(q, params).fetchall()]

    def get_all_genres(self) -> List[str]:
        rows = self.conn.execute("SELECT DISTINCT genres FROM movies WHERE genres IS NOT NULL").fetchall()
        genres = set()
        for row in rows:
            for g in row['genres'].split(','):
                g = g.strip()
                if g:
                    genres.add(g)
        return sorted(genres)

    def get_all_movie_ids(self) -> List[int]:
        rows = self.conn.execute("SELECT movie_id FROM movies").fetchall()
        return [r['movie_id'] for r in rows]

    # ------------------------------------------------------------------
    # RATINGS
    # ------------------------------------------------------------------
    def rate_movie(self, user_id: int, movie_id: int, rating: float) -> bool:
        self.conn.execute("""
            INSERT INTO ratings (user_id, movie_id, rating)
            VALUES (?,?,?)
            ON CONFLICT(user_id, movie_id) DO UPDATE SET rating=excluded.rating,
                created_at=datetime('now','localtime')
        """, (user_id, movie_id, rating))
        self.conn.execute("UPDATE users SET is_new_user=0 WHERE id=?", (user_id,))
        self.conn.execute("DELETE FROM recommendations_cache WHERE user_id=?", (user_id,))
        self.conn.commit()
        return True

    def delete_rating(self, user_id: int, movie_id: int) -> bool:
        self.conn.execute("DELETE FROM ratings WHERE user_id=? AND movie_id=?", (user_id, movie_id))
        self.conn.commit()
        return True

    def get_user_ratings(self, user_id: int) -> List[Dict]:
        rows = self.conn.execute("""
            SELECT r.*, m.title, m.genres, m.avg_rating, m.poster_url
            FROM ratings r
            JOIN movies m ON m.movie_id = r.movie_id
            WHERE r.user_id = ?
            ORDER BY r.created_at DESC
        """, (user_id,)).fetchall()
        return [dict(r) for r in rows]

    def get_movie_ratings(self, movie_id: int, limit: int = 20) -> List[Dict]:
        rows = self.conn.execute("""
            SELECT r.rating, r.created_at, u.display_name, u.avatar_url
            FROM ratings r
            JOIN users u ON u.id = r.user_id
            WHERE r.movie_id = ?
            ORDER BY r.created_at DESC LIMIT ?
        """, (movie_id, limit)).fetchall()
        return [dict(r) for r in rows]

    def get_user_rating_for_movie(self, user_id: int, movie_id: int) -> Optional[float]:
        row = self.conn.execute("SELECT rating FROM ratings WHERE user_id=? AND movie_id=?", (user_id, movie_id)).fetchone()
        return row['rating'] if row else None

    def get_rated_movie_ids(self, user_id: int) -> List[int]:
        rows = self.conn.execute("SELECT movie_id FROM ratings WHERE user_id=?", (user_id,)).fetchall()
        return [r['movie_id'] for r in rows]

    # ------------------------------------------------------------------
    # HISTORY
    # ------------------------------------------------------------------
    def log_action(self, user_id: int, movie_id: int, action: str = 'view'):
        self.conn.execute("""
            INSERT INTO user_history (user_id, movie_id, action)
            VALUES (?,?,?)
        """, (user_id, movie_id, action))
        self.conn.commit()

    def get_user_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        rows = self.conn.execute("""
            SELECT h.*, m.title, m.genres, m.poster_url
            FROM user_history h
            JOIN movies m ON m.movie_id = h.movie_id
            WHERE h.user_id = ?
            ORDER BY h.created_at DESC LIMIT ?
        """, (user_id, limit)).fetchall()
        return [dict(r) for r in rows]

    def get_recently_viewed_movie_ids(self, user_id: int, limit: int = 20) -> List[int]:
        rows = self.conn.execute("""
            SELECT DISTINCT movie_id FROM user_history
            WHERE user_id=? ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit)).fetchall()
        return [r['movie_id'] for r in rows]

    # ------------------------------------------------------------------
    # WATCHLIST
    # ------------------------------------------------------------------
    def add_to_watchlist(self, user_id: int, movie_id: int) -> bool:
        try:
            self.conn.execute("INSERT INTO watchlist (user_id, movie_id) VALUES (?,?)", (user_id, movie_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_from_watchlist(self, user_id: int, movie_id: int) -> bool:
        self.conn.execute("DELETE FROM watchlist WHERE user_id=? AND movie_id=?", (user_id, movie_id))
        self.conn.commit()
        return True

    def get_watchlist(self, user_id: int) -> List[Dict]:
        rows = self.conn.execute("""
            SELECT w.added_at, m.*
            FROM watchlist w
            JOIN movies m ON m.movie_id = w.movie_id
            WHERE w.user_id = ?
            ORDER BY w.added_at DESC
        """, (user_id,)).fetchall()
        return [dict(r) for r in rows]

    def is_in_watchlist(self, user_id: int, movie_id: int) -> bool:
        row = self.conn.execute("SELECT 1 FROM watchlist WHERE user_id=? AND movie_id=?", (user_id, movie_id)).fetchone()
        return row is not None

    # ------------------------------------------------------------------
    # USER GENRE PREFERENCES
    # ------------------------------------------------------------------
    def set_genre_preferences(self, user_id: int, genres: List[str]):
        self.conn.execute("DELETE FROM user_genres WHERE user_id=?", (user_id,))
        for i, genre in enumerate(genres):
            weight = 1.5 - i * 0.1
            self.conn.execute("INSERT INTO user_genres (user_id, genre, weight) VALUES (?,?,?)", (user_id, genre, max(0.5, weight)))
        self.conn.execute("DELETE FROM recommendations_cache WHERE user_id=?", (user_id,))
        self.conn.commit()

    def get_genre_preferences(self, user_id: int) -> List[Dict]:
        rows = self.conn.execute("SELECT genre, weight FROM user_genres WHERE user_id=? ORDER BY weight DESC", (user_id,)).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # RECOMMENDATIONS CACHE
    # ------------------------------------------------------------------
    def save_recommendations(self, user_id: int, method: str, results: List[Dict], ttl_hours: int = 24):
        expires = (datetime.now() + timedelta(hours=ttl_hours)).strftime('%Y-%m-%d %H:%M:%S')
        self.conn.execute("""
            INSERT INTO recommendations_cache (user_id, method, results, expires_at)
            VALUES (?,?,?,?)
            ON CONFLICT(user_id, method) DO UPDATE SET
                results=excluded.results,
                created_at=datetime('now','localtime'),
                expires_at=excluded.expires_at
        """, (user_id, method, json.dumps(results, ensure_ascii=False), expires))
        self.conn.commit()

    def get_cached_recommendations(self, user_id: int, method: str) -> Optional[List[Dict]]:
        row = self.conn.execute("SELECT results, expires_at FROM recommendations_cache WHERE user_id=? AND method=?", (user_id, method)).fetchone()
        if not row:
            return None
        if row['expires_at'] and datetime.now().strftime('%Y-%m-%d %H:%M:%S') > row['expires_at']:
            return None
        return json.loads(row['results'])

    def invalidate_cache(self, user_id: int):
        self.conn.execute("DELETE FROM recommendations_cache WHERE user_id=?", (user_id,))
        self.conn.commit()

    # ------------------------------------------------------------------
    # STATS
    # ------------------------------------------------------------------
    def get_stats(self) -> Dict:
        stats = {}
        for table, col in [('users','id'),('movies','movie_id'),('ratings','id'),('watchlist','id')]:
            row = self.conn.execute(f"SELECT COUNT({col}) FROM {table}").fetchone()
            stats[f'total_{table}'] = row[0]
        rows = self.conn.execute("""
            SELECT m.title, m.avg_rating, m.num_ratings
            FROM movies m
            WHERE m.num_ratings > 50
            ORDER BY m.avg_rating DESC LIMIT 5
        """).fetchall()
        stats['top_movies'] = [dict(r) for r in rows]
        rows = self.conn.execute("""
            SELECT u.username, u.display_name, COUNT(r.id) as rating_count
            FROM users u LEFT JOIN ratings r ON r.user_id = u.id
            GROUP BY u.id ORDER BY rating_count DESC LIMIT 5
        """).fetchall()
        stats['active_users'] = [dict(r) for r in rows]
        return stats

