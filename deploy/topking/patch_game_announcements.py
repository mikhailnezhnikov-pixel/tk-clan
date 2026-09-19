from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text()
MARKER = "GAME_ANNOUNCEMENTS_V1"
if MARKER in s:
    print("GAME_ANNOUNCEMENTS_ALREADY_PRESENT")
    raise SystemExit(0)

helpers = r'''
# GAME_ANNOUNCEMENTS_V1
_GAME_ANNOUNCEMENTS_CACHE = {"at": 0, "items": [], "error": ""}


def game_announcements_payload(force: bool = False) -> dict:
    import html as _html
    import re as _re
    import urllib.request as _urlrequest
    from html.parser import HTMLParser as _HTMLParser

    now = utc_now()
    if (not force and _GAME_ANNOUNCEMENTS_CACHE["items"]
            and now - int(_GAME_ANNOUNCEMENTS_CACHE["at"] or 0) < 300):
        return {
            "ok": True,
            "source": "https://t.me/hamsterking_game",
            "channel": "Hamster King Announcement",
            "items": _GAME_ANNOUNCEMENTS_CACHE["items"],
            "cached_at": _GAME_ANNOUNCEMENTS_CACHE["at"],
        }

    class _TelegramPreviewParser(_HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.items = []
            self.current = None
            self.in_text = 0
            self.in_time = 0
            self.text_parts = []

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            classes = set(str(attrs.get("class", "")).split())
            if tag == "div" and "tgme_widget_message" in classes and attrs.get("data-post"):
                data_post = str(attrs.get("data-post") or "")
                if "/" not in data_post:
                    return
                channel, post_id = data_post.rsplit("/", 1)
                self.current = {
                    "id": post_id,
                    "data_post": data_post,
                    "url": "https://t.me/" + data_post,
                    "datetime": "",
                    "text": "",
                    "image_url": "",
                }
                self.text_parts = []
                return
            if not self.current:
                return
            if tag == "div" and "tgme_widget_message_text" in classes:
                self.in_text += 1
                return
            if tag == "br" and self.in_text:
                self.text_parts.append("\n")
                return
            if tag == "time":
                value = str(attrs.get("datetime") or "")
                if value:
                    self.current["datetime"] = value
                self.in_time += 1
                return
            if tag in ("a", "i", "div"):
                style = str(attrs.get("style") or "")
                if "background-image" in style and not self.current.get("image_url"):
                    match = _re.search(r"""background-image\s*:\s*url\(['"]?([^'")]+)""", style)
                    if match:
                        self.current["image_url"] = _html.unescape(match.group(1))

        def handle_endtag(self, tag):
            if not self.current:
                return
            if tag == "div" and self.in_text:
                self.in_text -= 1
                if self.in_text == 0:
                    text = "".join(self.text_parts)
                    text = _re.sub(r"\n{3,}", "\n\n", text).strip()
                    self.current["text"] = text
                return
            if tag == "time" and self.in_time:
                self.in_time -= 1
                return
            if tag == "div" and not self.in_text and self.current.get("text"):
                item = self.current
                self.current = None
                self.text_parts = []
                if item["text"]:
                    self.items.append(item)

        def handle_data(self, data):
            if self.current and self.in_text:
                self.text_parts.append(data)

    try:
        req = _urlrequest.Request(
            "https://t.me/s/hamsterking_game",
            headers={
                "User-Agent": "Mozilla/5.0 TopKingCabinet/1.0",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        with _urlrequest.urlopen(req, timeout=12) as response:
            raw = response.read(2_500_000)
        page = raw.decode("utf-8", "replace")
        parser = _TelegramPreviewParser()
        parser.feed(page)

        # Parser end-tag nesting on Telegram preview markup can vary.
        # De-duplicate by post id and keep the newest visible preview posts.
        unique = {}
        for item in parser.items:
            post_id = str(item.get("id") or "")
            text = str(item.get("text") or "").strip()
            if not post_id or not text:
                continue
            unique[post_id] = {
                "id": post_id,
                "url": str(item.get("url") or ""),
                "datetime": str(item.get("datetime") or ""),
                "text": text[:12000],
                "image_url": str(item.get("image_url") or ""),
            }

        items = list(unique.values())
        items.sort(key=lambda x: int(x["id"]) if x["id"].isdigit() else 0, reverse=True)
        items = items[:30]

        if not items:
            # Conservative regex fallback for Telegram preview HTML.
            blocks = _re.findall(
                r'<div class="tgme_widget_message[^"]*"[^>]*data-post="hamsterking_game/(\d+)"[\s\S]*?'
                r'<div class="tgme_widget_message_text[^"]*"[^>]*>([\s\S]*?)</div>[\s\S]*?'
                r'<time datetime="([^"]+)"',
                page,
                flags=_re.I,
            )
            for post_id, body, dt in blocks[:30]:
                body = _re.sub(r"<br\s*/?>", "\n", body, flags=_re.I)
                body = _re.sub(r"<[^>]+>", "", body)
                body = _html.unescape(body)
                body = _re.sub(r"\n{3,}", "\n\n", body).strip()
                if body:
                    items.append({
                        "id": post_id,
                        "url": "https://t.me/hamsterking_game/" + post_id,
                        "datetime": dt,
                        "text": body[:12000],
                        "image_url": "",
                    })
            items.sort(key=lambda x: int(x["id"]) if x["id"].isdigit() else 0, reverse=True)
            items = items[:30]

        if not items:
            raise RuntimeError("telegram_preview_empty")

        _GAME_ANNOUNCEMENTS_CACHE["at"] = now
        _GAME_ANNOUNCEMENTS_CACHE["items"] = items
        _GAME_ANNOUNCEMENTS_CACHE["error"] = ""
        return {
            "ok": True,
            "source": "https://t.me/hamsterking_game",
            "channel": "Hamster King Announcement",
            "items": items,
            "cached_at": now,
        }
    except Exception as exc:
        _GAME_ANNOUNCEMENTS_CACHE["error"] = type(exc).__name__
        if _GAME_ANNOUNCEMENTS_CACHE["items"]:
            return {
                "ok": True,
                "source": "https://t.me/hamsterking_game",
                "channel": "Hamster King Announcement",
                "items": _GAME_ANNOUNCEMENTS_CACHE["items"],
                "cached_at": _GAME_ANNOUNCEMENTS_CACHE["at"],
                "stale": True,
            }
        return {
            "ok": False,
            "source": "https://t.me/hamsterking_game",
            "channel": "Hamster King Announcement",
            "items": [],
            "error": "source_unavailable",
        }


'''

anchor = '\ndef page_shell(title: str, content: str) -> bytes:\n'
if anchor not in s:
    raise SystemExit("page_shell anchor missing")
s = s.replace(anchor, '\n' + helpers + 'def page_shell(title: str, content: str) -> bytes:\n', 1)

get_anchor = '''        elif path == "/api/v1/cabinet/clan-shop/history":
            origin = self.headers.get("Origin", "")
'''
get_route = '''        elif path == "/api/v1/cabinet/announcements":
            origin = self.headers.get("Origin", "")
            if origin not in CABINET_ORIGINS:
                self.send_cabinet_json(HTTPStatus.FORBIDDEN, {"error": "origin_not_allowed"})
                return
            member = self.cabinet_member()
            if not member:
                self.send_cabinet_json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return
            result = game_announcements_payload()
            self.send_cabinet_json(HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_GATEWAY, result)
        elif path == "/api/v1/cabinet/clan-shop/history":
            origin = self.headers.get("Origin", "")
'''
if get_anchor not in s:
    raise SystemExit("cabinet history GET anchor missing")
s = s.replace(get_anchor, get_route, 1)

path.write_text(s)
print("GAME_ANNOUNCEMENTS_PATCH_OK")
