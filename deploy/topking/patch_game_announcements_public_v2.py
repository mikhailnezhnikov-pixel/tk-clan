from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text()
MARKER = "GAME_ANNOUNCEMENTS_PUBLIC_V3"
if MARKER in s:
    print("GAME_ANNOUNCEMENTS_PUBLIC_V3_ALREADY_PRESENT")
    raise SystemExit(0)

start = s.find("def game_announcements_payload(force: bool = False) -> dict:")
end = s.find("\n\ndef page_shell(", start)
if start < 0 or end < 0:
    raise SystemExit("game announcements function anchor missing")

new_function = r'''# GAME_ANNOUNCEMENTS_PUBLIC_V3
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
            self.text_parts = []
            self.link_stack = []

        def _add_link(self, href, label=""):
            if not self.current:
                return
            href = _html.unescape(str(href or "")).strip()
            if not href.startswith(("https://", "http://")):
                return
            links = self.current.setdefault("links", [])
            clean_label = str(label or "").strip()[:200]
            for existing in links:
                if str(existing.get("url") or "") == href:
                    if clean_label and not str(existing.get("label") or "").strip():
                        existing["label"] = clean_label
                    return
            links.append({"url": href, "label": clean_label})

        def _image_from_attrs(self, tag, attrs, classes):
            if not self.current or self.current.get("image_url"):
                return
            candidates = []
            if tag == "img":
                for key in ("src", "data-src"):
                    if attrs.get(key):
                        candidates.append(str(attrs.get(key)))
            if tag in ("a", "i", "div") and (
                "tgme_widget_message_photo_wrap" in classes
                or "tgme_widget_message_video_player" in classes
                or "tgme_widget_message_photo" in classes
            ):
                style = str(attrs.get("style") or "")
                match = _re.search(r"""background-image\s*:\s*url\(['"]?([^'")]+)""", style)
                if match:
                    candidates.append(match.group(1))
            for value in candidates:
                value = _html.unescape(value).strip()
                if value.startswith(("https://", "http://")):
                    self.current["image_url"] = value
                    return

        def handle_starttag(self, tag, raw_attrs):
            attrs = dict(raw_attrs)
            classes = set(str(attrs.get("class", "")).split())
            if tag == "div" and "tgme_widget_message" in classes and attrs.get("data-post"):
                data_post = str(attrs.get("data-post") or "")
                if "/" not in data_post:
                    return
                _, post_id = data_post.rsplit("/", 1)
                self.current = {
                    "id": post_id,
                    "data_post": data_post,
                    "url": "https://t.me/" + data_post,
                    "datetime": "",
                    "text": "",
                    "image_url": "",
                    "links": [],
                }
                self.text_parts = []
                self.link_stack = []
                return
            if not self.current:
                return

            self._image_from_attrs(tag, attrs, classes)

            if tag == "a":
                href = str(attrs.get("href") or "")
                self.link_stack.append({"href": href, "parts": []})
                self._add_link(href)

            if tag == "div" and "tgme_widget_message_text" in classes:
                self.in_text += 1
                return
            if tag == "br" and self.in_text:
                self.text_parts.append("\n")
                if self.link_stack:
                    self.link_stack[-1]["parts"].append(" ")
                return
            if tag == "time":
                value = str(attrs.get("datetime") or "")
                if value:
                    self.current["datetime"] = value

        def handle_endtag(self, tag):
            if not self.current:
                return
            if tag == "a" and self.link_stack:
                link = self.link_stack.pop()
                label = "".join(link["parts"]).strip()
                self._add_link(link["href"], label)
                return
            if tag == "div" and self.in_text:
                self.in_text -= 1
                if self.in_text == 0:
                    text = "".join(self.text_parts)
                    text = _re.sub(r"\n{3,}", "\n\n", text).strip()
                    self.current["text"] = text
                return
            if tag == "div" and not self.in_text and self.current.get("text"):
                item = self.current
                self.current = None
                self.text_parts = []
                self.link_stack = []
                if item["text"]:
                    self.items.append(item)

        def handle_data(self, data):
            if self.current and self.in_text:
                self.text_parts.append(data)
            if self.current and self.link_stack:
                self.link_stack[-1]["parts"].append(data)

    try:
        req = _urlrequest.Request(
            "https://t.me/s/hamsterking_game",
            headers={
                "User-Agent": "Mozilla/5.0 TopKingNews/2.0",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        with _urlrequest.urlopen(req, timeout=12) as response:
            raw = response.read(3_000_000)
        page = raw.decode("utf-8", "replace")
        parser = _TelegramPreviewParser()
        parser.feed(page)

        unique = {}
        for item in parser.items:
            post_id = str(item.get("id") or "")
            text = str(item.get("text") or "").strip()
            if not post_id or not text:
                continue
            links = []
            for link in item.get("links") or []:
                url = str(link.get("url") or "").strip()
                label = str(link.get("label") or "").strip()
                if url and not any(x["url"] == url for x in links):
                    links.append({"url": url, "label": label})
            unique[post_id] = {
                "id": post_id,
                "url": str(item.get("url") or ""),
                "datetime": str(item.get("datetime") or ""),
                "text": text[:16000],
                "image_url": str(item.get("image_url") or ""),
                "links": links[:20],
            }

        items = list(unique.values())
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

s = s[:start] + new_function + s[end:]

cabinet_anchor = '''        elif path == "/api/v1/cabinet/announcements":
'''
if cabinet_anchor not in s:
    raise SystemExit("cabinet announcements route anchor missing")

public_route = '''        elif path == "/api/v1/announcements":
            origin = self.headers.get("Origin", "")
            if origin not in CABINET_ORIGINS:
                self.send_cabinet_json(HTTPStatus.FORBIDDEN, {"error": "origin_not_allowed"})
                return
            if not rate_allowed(f"public-announcements:{self.client_ip()}", 60, 60):
                self.send_cabinet_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "rate_limited"})
                return
            result = game_announcements_payload()
            self.send_cabinet_json(HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_GATEWAY, result)
'''
if 'elif path == "/api/v1/announcements":' not in s:
    s = s.replace(cabinet_anchor, public_route + cabinet_anchor, 1)

path.write_text(s)
print("GAME_ANNOUNCEMENTS_PUBLIC_V3_PATCH_OK")
