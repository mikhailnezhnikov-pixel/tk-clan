from pathlib import Path
import sys

path=Path(sys.argv[1])
s=path.read_text()
MARKER="SITE_ANALYTICS_V1"
if MARKER in s:
    print("SITE_ANALYTICS_V1_ALREADY_PRESENT")
    raise SystemExit(0)

# 1) DB schema.
schema_anchor='''            CREATE INDEX IF NOT EXISTS idx_public_ratings_kind
                ON public_rating_snapshots(kind, rank);
'''
schema_add=schema_anchor+'''            -- SITE_ANALYTICS_V1
            CREATE TABLE IF NOT EXISTS site_pageviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at INTEGER NOT NULL,
                day_key TEXT NOT NULL,
                path TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                referrer_host TEXT NOT NULL DEFAULT '',
                source_group TEXT NOT NULL DEFAULT 'direct',
                language TEXT NOT NULL DEFAULT '',
                device TEXT NOT NULL DEFAULT '',
                visitor_hash TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_site_pageviews_created
                ON site_pageviews(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_site_pageviews_path
                ON site_pageviews(path, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_site_pageviews_visitor
                ON site_pageviews(day_key, visitor_hash);
'''
if schema_anchor not in s:
    raise SystemExit("site analytics schema anchor missing")
s=s.replace(schema_anchor,schema_add,1)

# 2) Helpers.
helper_anchor="\n\n# TELEGRAM_APPLICATION_I18N_V1\n"
helpers=r'''

# SITE_ANALYTICS_V1
SITE_ANALYTICS_PATH_RE = re.compile(r"^/[A-Za-z0-9_./-]{0,220}$")
SITE_ANALYTICS_LANG_RE = re.compile(r"^[A-Za-z-]{0,16}$")


def site_analytics_source(host: str) -> str:
    host=(host or "").lower().strip(".")
    if not host:
        return "direct"
    if host in {"t.me","telegram.me","web.telegram.org"} or host.endswith(".t.me"):
        return "telegram"
    if any(host==name or host.endswith("."+name) for name in (
        "google.com","google.ru","yandex.ru","yandex.com","bing.com",
        "duckduckgo.com","search.brave.com"
    )):
        return "search"
    if any(host==name or host.endswith("."+name) for name in (
        "vk.com","instagram.com","facebook.com","youtube.com","x.com","twitter.com"
    )):
        return "social"
    if host in {"tk-clan.ru","www.tk-clan.ru"}:
        return "internal"
    return "referral"


def site_analytics_clean_path(value: object) -> str:
    value=str(value or "/").split("?",1)[0].split("#",1)[0].strip()
    if not value.startswith("/"):
        value="/"+value
    value=re.sub(r"/index\.html$", "/", value, flags=re.I)
    value=re.sub(r"/{2,}", "/", value)
    if not SITE_ANALYTICS_PATH_RE.fullmatch(value):
        return "/"
    if len(value)>1 and value.endswith("/"):
        return value
    return value[:220]


def site_analytics_visitor(ip: str, user_agent: str, day_key: str) -> str:
    # Daily rotating anonymous fingerprint. Raw IP and UA are never stored.
    material=f"site-analytics:{day_key}:{ip}:{user_agent[:300]}".encode()
    return hmac.new(SIGNING_SECRET.encode(), material, hashlib.sha256).hexdigest()[:24]


def record_site_pageview(document: object, ip: str, user_agent: str) -> dict:
    if not isinstance(document, dict):
        raise ValueError("analytics object required")
    now=utc_now()
    day_key=datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%d")
    page=site_analytics_clean_path(document.get("path"))
    title=clean_public_name(document.get("title"), 160)
    referrer=clean_public_name(document.get("referrer_host"), 180).lower()
    referrer=re.sub(r"[^a-z0-9.:-]", "", referrer)[:180]
    language=str(document.get("language") or "").strip().lower()[:16]
    if not SITE_ANALYTICS_LANG_RE.fullmatch(language):
        language=""
    device=str(document.get("device") or "other").strip().lower()
    if device not in {"desktop","mobile","tablet","other"}:
        device="other"
    visitor=site_analytics_visitor(ip,user_agent,day_key)
    source=site_analytics_source(referrer)
    with db_session() as db:
        db.execute("""INSERT INTO site_pageviews
                      (created_at,day_key,path,title,referrer_host,source_group,language,device,visitor_hash)
                      VALUES(?,?,?,?,?,?,?,?,?)""",
                   (now,day_key,page,title,referrer,source,language,device,visitor))
        # Keep six months. This also bounds DB growth.
        db.execute("DELETE FROM site_pageviews WHERE created_at<?", (now-180*86400,))
    return {"ok":True}


def site_analytics_stats(days: int = 30) -> dict:
    days=max(1,min(int(days or 30),180))
    now=utc_now()
    start=now-days*86400
    today=datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%d")
    with db_session() as db:
        total=db.execute("SELECT COUNT(*) AS n FROM site_pageviews WHERE created_at>=?",(start,)).fetchone()["n"]
        unique_today=db.execute("""SELECT COUNT(DISTINCT visitor_hash) AS n
                                   FROM site_pageviews WHERE day_key=?""",(today,)).fetchone()["n"]
        views_today=db.execute("SELECT COUNT(*) AS n FROM site_pageviews WHERE day_key=?",(today,)).fetchone()["n"]
        pages=db.execute("""SELECT path,MAX(title) AS title,COUNT(*) AS views,
                                   COUNT(DISTINCT day_key||':'||visitor_hash) AS visitor_days
                            FROM site_pageviews WHERE created_at>=?
                            GROUP BY path ORDER BY views DESC,path LIMIT 30""",(start,)).fetchall()
        daily=db.execute("""SELECT day_key,COUNT(*) AS views,COUNT(DISTINCT visitor_hash) AS visitors
                            FROM site_pageviews WHERE created_at>=?
                            GROUP BY day_key ORDER BY day_key""",(start,)).fetchall()
        sources=db.execute("""SELECT source_group AS name,COUNT(*) AS views
                              FROM site_pageviews WHERE created_at>=?
                              GROUP BY source_group ORDER BY views DESC""",(start,)).fetchall()
        devices=db.execute("""SELECT device AS name,COUNT(*) AS views
                              FROM site_pageviews WHERE created_at>=?
                              GROUP BY device ORDER BY views DESC""",(start,)).fetchall()
        languages=db.execute("""SELECT language AS name,COUNT(*) AS views
                                FROM site_pageviews WHERE created_at>=? AND language<>''
                                GROUP BY language ORDER BY views DESC LIMIT 10""",(start,)).fetchall()
    return {
        "ok":True,"days":days,"total_views":total,
        "views_today":views_today,"unique_today":unique_today,
        "pages":[dict(row) for row in pages],
        "daily":[dict(row) for row in daily],
        "sources":[dict(row) for row in sources],
        "devices":[dict(row) for row in devices],
        "languages":[dict(row) for row in languages],
        "updated_at":now,
    }
'''
if helper_anchor not in s:
    raise SystemExit("site analytics helper anchor missing")
s=s.replace(helper_anchor,helpers+helper_anchor,1)

# 3) Public pageview route. Put it before /check.
post_anchor='''            elif path == "/api/v1/check":
'''
post_route='''            elif path == "/api/v1/site-analytics/view":
                origin=self.headers.get("Origin","")
                if origin and origin not in PUBLIC_RECIPE_ORIGINS:
                    self.send_public_json(HTTPStatus.FORBIDDEN, {"error":"origin_not_allowed"}); return
                if not rate_allowed(f"site-view:{self.client_ip()}", 90, 60):
                    self.send_public_json(HTTPStatus.TOO_MANY_REQUESTS, {"error":"rate_limited"}); return
                try:
                    result=record_site_pageview(
                        self.read_json(8192),
                        self.client_ip(),
                        self.headers.get("User-Agent","")
                    )
                except ValueError:
                    self.send_public_json(HTTPStatus.BAD_REQUEST, {"error":"invalid_analytics"}); return
                self.send_public_json(HTTPStatus.OK, result)
            elif path == "/api/v1/check":
'''
if post_anchor not in s:
    raise SystemExit("site analytics public route anchor missing")
s=s.replace(post_anchor,post_route,1)

# 4) Authenticated cabinet stats route.
cab_anchor='''            elif path == "/api/v1/cabinet/login":
'''
cab_route='''            elif path == "/api/v1/cabinet/site-stats":
                origin=self.headers.get("Origin","")
                if origin not in CABINET_ORIGINS:
                    self.send_cabinet_json(HTTPStatus.FORBIDDEN, {"error":"origin_not_allowed"}); return
                member=self.cabinet_member()
                if not member:
                    self.send_cabinet_json(HTTPStatus.UNAUTHORIZED, {"error":"unauthorized"}); return
                body=self.read_json(2048)
                try:
                    days=int(body.get("days") or 30)
                except (TypeError,ValueError):
                    days=30
                self.send_cabinet_json(HTTPStatus.OK, site_analytics_stats(days))
            elif path == "/api/v1/cabinet/login":
'''
if cab_anchor not in s:
    raise SystemExit("site analytics cabinet route anchor missing")
s=s.replace(cab_anchor,cab_route,1)

path.write_text(s)
print("SITE_ANALYTICS_V1_PATCH_OK")
