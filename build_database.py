"""
Build complete demo database (app.db) for Movie Recommender web app.
Schema:
  users        - dang nhap / dang ki
  movies       - catalog phim (tu movies.db hien co)
  ratings      - user ratings (from rating.csv, sampled)
  user_history - lich su xem / click
  user_genres  - so thich the loai (cold start)
  recommendations_cache - luu cache goi y
"""
import sqlite3, csv, hashlib, os, sys, re, random, datetime, json
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'app.db'

# Xoa cu neu muon reset
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"Removed old {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
conn.execute("PRAGMA journal_mode = WAL")
cur  = conn.cursor()

# =====================================================================
# 1. CREATE TABLES
# =====================================================================
cur.executescript("""
-- Bang nguoi dung
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT    NOT NULL,
    display_name  TEXT,
    avatar_url    TEXT,
    role          TEXT    NOT NULL DEFAULT 'user',  -- 'user' | 'admin'
    is_new_user   INTEGER NOT NULL DEFAULT 1,       -- 1 = chua co rating
    created_at    TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    last_login    TEXT
);

-- Bang phim
CREATE TABLE movies (
    movie_id      INTEGER PRIMARY KEY,
    title         TEXT    NOT NULL,
    year          INTEGER,
    genres        TEXT,                -- "action,comedy,drama"
    soup          TEXT,                -- full text cho CBF
    avg_rating    REAL    DEFAULT 0,
    num_ratings   INTEGER DEFAULT 0,
    poster_url    TEXT,
    overview      TEXT
);

-- Bang danh gia (user ratings)
CREATE TABLE ratings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
    movie_id   INTEGER NOT NULL REFERENCES movies(movie_id),
    rating     REAL    NOT NULL CHECK(rating >= 0.5 AND rating <= 5.0),
    created_at TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    UNIQUE(user_id, movie_id)
);

-- Lich su xem / click
CREATE TABLE user_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    movie_id   INTEGER NOT NULL REFERENCES movies(movie_id),
    action     TEXT    NOT NULL DEFAULT 'view',  -- 'view'|'click'|'rate'|'skip'
    created_at TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- So thich the loai (cho cold start)
CREATE TABLE user_genres (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    genre    TEXT    NOT NULL,
    weight   REAL    NOT NULL DEFAULT 1.0,
    UNIQUE(user_id, genre)
);

-- Cache ket qua goi y (tranh re-compute)
CREATE TABLE recommendations_cache (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    method     TEXT    NOT NULL,   -- 'CF'|'CBF'|'Hybrid'
    results    TEXT    NOT NULL,   -- JSON array [{movie_id, score, title}]
    created_at TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    expires_at TEXT,
    UNIQUE(user_id, method)
);

-- Bang phim yeu thich (watchlist)
CREATE TABLE watchlist (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    movie_id   INTEGER NOT NULL REFERENCES movies(movie_id),
    added_at   TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    UNIQUE(user_id, movie_id)
);

-- Index de truy van nhanh
CREATE INDEX idx_ratings_user    ON ratings(user_id);
CREATE INDEX idx_ratings_movie   ON ratings(movie_id);
CREATE INDEX idx_history_user    ON user_history(user_id);
CREATE INDEX idx_cache_user      ON recommendations_cache(user_id);
CREATE INDEX idx_watchlist_user  ON watchlist(user_id);
""")
conn.commit()
print("Created all tables.")

# =====================================================================
# 2. POPULATE movies FROM movies.db + movie.csv
# =====================================================================
print("\nLoading movies...")

# Doc tu movies.db hien co
src_conn = sqlite3.connect('movies.db')
src_cur  = src_conn.cursor()
src_cur.execute("SELECT movieId, title, genres_clean FROM Movies")
movies_from_db = {row[0]: {'title': row[1], 'genres': row[2]} for row in src_cur.fetchall()}
src_conn.close()

# Doc them tu movie.csv (de lay nam)
year_map = {}
try:
    with open('movie.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            mid = int(row['movieId'])
            m = re.search(r'\((\d{4})\)\s*$', row.get('title',''))
            if m:
                year_map[mid] = int(m.group(1))
except Exception as e:
    print(f"  Warning: {e}")

# Doc rating stats tu rating.csv (lay avg va count cho moi phim)
print("  Computing avg ratings (this may take a moment)...")
rating_stats = {}
try:
    with open('rating.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            mid = int(row['movieId'])
            r   = float(row['rating'])
            if mid not in rating_stats:
                rating_stats[mid] = [0, 0]
            rating_stats[mid][0] += r
            rating_stats[mid][1] += 1
except Exception as e:
    print(f"  Warning: {e}")

# Insert movies
movies_data = []
for mid, info in movies_from_db.items():
    title  = info['title']
    genres = info['genres']
    year   = year_map.get(mid)
    stats  = rating_stats.get(mid, [0, 0])
    avg_r  = round(stats[0]/stats[1], 2) if stats[1] > 0 else 0.0
    num_r  = stats[1]
    movies_data.append((mid, title, year, genres, None, avg_r, num_r, None, None))

cur.executemany("""
    INSERT OR IGNORE INTO movies
    (movie_id, title, year, genres, soup, avg_rating, num_ratings, poster_url, overview)
    VALUES (?,?,?,?,?,?,?,?,?)
""", movies_data)
conn.commit()
print(f"  Inserted {len(movies_data)} movies.")

# =====================================================================
# 3. CREATE DEMO USERS
# =====================================================================
print("\nCreating demo users...")

def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

demo_users = [
    # (username, email, password, display_name, role)
    ('admin',   'admin@demo.vn',   'admin123',  'Administrator',   'admin'),
    ('alice',   'alice@demo.vn',   'alice123',  'Alice Nguyen',    'user'),
    ('bob',     'bob@demo.vn',     'bob123',    'Bob Tran',        'user'),
    ('charlie', 'charlie@demo.vn', 'charlie123','Charlie Le',      'user'),
    ('demo',    'demo@demo.vn',    'demo123',   'Demo User',       'user'),
]

for uname, email, pw, dname, role in demo_users:
    cur.execute("""
        INSERT INTO users (username, email, password_hash, display_name, role, is_new_user)
        VALUES (?,?,?,?,?,0)
    """, (uname, email, hash_pw(pw), dname, role))

conn.commit()
print(f"  Created {len(demo_users)} demo users.")

# =====================================================================
# 4. POPULATE SAMPLE RATINGS FROM rating.csv (subset for demo users)
# =====================================================================
print("\nLoading sample ratings from rating.csv ...")

# Lay 5 userId thuc te tu rating.csv co nhieu rating (lam demo)
sample_user_ids = set()
real_user_ratings = {}

try:
    with open('rating.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count_map = {}
        for row in reader:
            uid = int(row['userId'])
            count_map[uid] = count_map.get(uid, 0) + 1

    # Lay 5 user co nhieu rating nhat tu du lieu goc (lam mau demo)
    top_users = sorted(count_map.items(), key=lambda x: -x[1])[:5]
    sample_user_ids = {uid for uid, _ in top_users}
    print(f"  Selected real userId samples: {sample_user_ids}")

    # Doc ratings cua nhung user nay
    with open('rating.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            uid = int(row['userId'])
            if uid in sample_user_ids:
                mid = int(row['movieId'])
                r   = float(row['rating'])
                if uid not in real_user_ratings:
                    real_user_ratings[uid] = []
                real_user_ratings[uid].append((mid, r))
except Exception as e:
    print(f"  Warning: {e}")

# Map real userId -> demo userId (alice=2, bob=3, charlie=4, ...)
valid_movie_ids = {row[0] for row in movies_data}
demo_user_ids   = [2, 3, 4, 5]  # alice, bob, charlie, demo
real_uid_list   = sorted(sample_user_ids)

ratings_to_insert = []
for i, real_uid in enumerate(real_uid_list[:len(demo_user_ids)]):
    demo_uid = demo_user_ids[i]
    user_ratings = real_user_ratings.get(real_uid, [])
    # Chi lay ratings cho phim co trong movies table
    filtered = [(mid, r) for mid, r in user_ratings if mid in valid_movie_ids]
    for mid, r in filtered[:200]:  # Gioi han 200 ratings / user de demo nhanh
        ratings_to_insert.append((demo_uid, mid, r))

cur.executemany("""
    INSERT OR IGNORE INTO ratings (user_id, movie_id, rating)
    VALUES (?,?,?)
""", ratings_to_insert)
conn.commit()

# Cap nhat is_new_user = 0 cho nhung user co ratings
cur.execute("""
    UPDATE users SET is_new_user = 0
    WHERE id IN (SELECT DISTINCT user_id FROM ratings)
""")
conn.commit()
print(f"  Inserted {len(ratings_to_insert)} sample ratings.")

# =====================================================================
# 5. SEED USER GENRES (cho cold start)
# =====================================================================
print("\nSeeding user genre preferences...")

genre_seeds = {
    2: [('action',1.5),('adventure',1.2),('sci-fi',1.0)],  # alice
    3: [('comedy',1.5),('romance',1.2),('drama',1.0)],      # bob
    4: [('thriller',1.5),('crime',1.2),('mystery',1.0)],    # charlie
    5: [('animation',1.5),('family',1.2),('fantasy',1.0)],  # demo
}
for uid, genres in genre_seeds.items():
    for genre, weight in genres:
        cur.execute("""
            INSERT OR IGNORE INTO user_genres (user_id, genre, weight) VALUES (?,?,?)
        """, (uid, genre, weight))
conn.commit()

# =====================================================================
# 6. ADD SOME WATCHLIST ENTRIES
# =====================================================================
print("Seeding watchlist...")

top_movies = [row[0] for row in sorted(movies_data, key=lambda x: -x[6])[:20]]
watchlist_entries = []
for uid in demo_user_ids:
    picks = random.sample(top_movies, min(5, len(top_movies)))
    for mid in picks:
        watchlist_entries.append((uid, mid))

cur.executemany("""
    INSERT OR IGNORE INTO watchlist (user_id, movie_id) VALUES (?,?)
""", watchlist_entries)
conn.commit()

# =====================================================================
# 7. VERIFICATION
# =====================================================================
print("\n=== DATABASE SUMMARY ===")
for table in ['users','movies','ratings','user_genres','watchlist','recommendations_cache']:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    print(f"  {table:<30}: {cur.fetchone()[0]:>6} rows")

print("\n=== DEMO LOGIN CREDENTIALS ===")
creds = [
    ("admin",   "admin123",  "Quan tri vien - xem tat ca"),
    ("alice",   "alice123",  "User co ratings (Action fan)"),
    ("bob",     "bob123",    "User co ratings (Comedy fan)"),
    ("charlie", "charlie123","User co ratings (Thriller fan)"),
    ("demo",    "demo123",   "User demo don gian"),
]
print(f"  {'Username':<12} {'Password':<15} {'Mo ta'}")
print(f"  {'-'*12} {'-'*15} {'-'*30}")
for u, p, d in creds:
    print(f"  {u:<12} {p:<15} {d}")

print(f"\nDatabase saved to: {os.path.abspath(DB_PATH)}")
conn.close()
print("Done!")
