from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text()
MARKER = "GAME_ANNOUNCEMENTS_TRANSLATION_V4"
if MARKER in s:
    print("GAME_ANNOUNCEMENTS_TRANSLATION_V4_ALREADY_PRESENT")
    raise SystemExit(0)

start = s.find("def game_announcements_payload(")
end = s.find("\n\ndef page_shell(", start)
if start < 0 or end < 0:
    raise SystemExit("game announcements function anchor missing")

new_function = r'''# GAME_ANNOUNCEMENTS_TRANSLATION_V4
def game_announcements_payload(force: bool = False, lang: str = "en") -> dict:
    import html as _html
    import json as _json
    import re as _re
    import urllib.parse as _urlparse
    import urllib.request as _urlrequest
    from html.parser import HTMLParser as _HTMLParser

    lang = str(lang or "en").lower()
    if lang not in ("en", "ru", "fa"):
        lang = "en"

    def _clean_english_text(value: str) -> str:
        lines = []
        for raw_line in str(value or "").replace("\r", "").split("\n"):
            line = raw_line.strip()
            if not line:
                if lines and lines[-1] != "":
                    lines.append("")
                continue
            probe = _re.sub(r"^[>»›\-–—\s\[\]]+", "", line).strip()
            if _re.match(
                r"(?i)^(русская версия|russian version|extended version(?: of patch note)?|"
                r"english version|persian version|farsi version|نسخه فارسی|فارسی)",
                probe,
            ):
                continue
            lines.append(line)
        text = "\n".join(lines)
        text = _re.sub(r"\n{3,}", "\n\n", text).strip()
        return text

    def _split_chunks(text: str, limit: int = 2600) -> list[str]:
        text = str(text or "").strip()
        if len(text) <= limit:
            return [text] if text else []
        chunks = []
        current = ""
        for paragraph in text.split("\n\n"):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            candidate = paragraph if not current else current + "\n\n" + paragraph
            if len(candidate) <= limit:
                current = candidate
                continue
            if current:
                chunks.append(current)
                current = ""
            while len(paragraph) > limit:
                cut = paragraph.rfind(" ", 0, limit)
                if cut < limit // 2:
                    cut = limit
                chunks.append(paragraph[:cut].strip())
                paragraph = paragraph[cut:].strip()
            current = paragraph
        if current:
            chunks.append(current)
        return chunks

    def _machine_translate(text: str, target: str) -> tuple[str, bool]:
        text = str(text or "").strip()
        if not text or target == "en":
            return text, False
        cache = globals().setdefault("_GAME_ANNOUNCEMENTS_TRANSLATION_CACHE", {})
        cache_key = target + "\n" + text
        cached = cache.get(cache_key)
        if isinstance(cached, str) and cached:
            return cached, True
        translated_chunks = []
        try:
            for chunk in _split_chunks(text):
                query = _urlparse.urlencode({
                    "client": "gtx",
                    "sl": "en",
                    "tl": target,
                    "dt": "t",
                    "q": chunk,
                })
                req = _urlrequest.Request(
                    "https://translate.googleapis.com/translate_a/single?" + query,
                    headers={
                        "User-Agent": "Mozilla/5.0 TopKingNews/4.0",
                        "Accept": "application/json,text/plain,*/*",
                    },
                )
                with _urlrequest.urlopen(req, timeout=10) as response:
                    data = _json.loads(response.read(1_500_000).decode("utf-8", "replace"))
                parts = []
                if isinstance(data, list) and data and isinstance(data[0], list):
                    for segment in data[0]:
                        if isinstance(segment, list) and segment and segment[0]:
                            parts.append(str(segment[0]))
                translated = "".join(parts).strip()
                if not translated:
                    raise RuntimeError("translation_empty")
                translated_chunks.append(translated)
            result = "\n\n".join(translated_chunks).strip()
            if result:
                if len(cache) > 500:
                    cache.clear()
                cache[cache_key] = result
                return result, True
        except Exception:
            pass
        return text, False

    now = utc_now()
    cache_fresh = (
        not force
        and _GAME_ANNOUNCEMENTS_CACHE["items"]
        and now - int(_GAME_ANNOUNCEMENTS_CACHE["at"] or 0) < 300
    )

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

        def _message_media_from_attrs(self, tag, attrs, classes):
            if not self.current or self.current.get("image_url"):
                return
            # Only Telegram's actual message media wrappers count as an announcement image.
            # Never use arbitrary <img> tags: those include avatars, icons and link previews.
            if tag not in ("a", "i", "div"):
                return
            if not (
                "tgme_widget_message_photo_wrap" in classes
                or "tgme_widget_message_video_player" in classes
                or "tgme_widget_message_photo" in classes
            ):
                return
            style = str(attrs.get("style") or "")
            match = _re.search(r"""background-image\s*:\s*url\(['"]?([^'")]+)""", style)
            if not match:
                return
            value = _html.unescape(match.group(1)).strip()
            if value.startswith(("https://", "http://")):
                self.current["image_url"] = value

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

            self._message_media_from_attrs(tag, attrs, classes)

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

    stale = False
    if not cache_fresh:
        try:
            req = _urlrequest.Request(
                "https://t.me/s/hamsterking_game",
                headers={
                    "User-Agent": "Mozilla/5.0 TopKingNews/4.0",
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
                text_en = _clean_english_text(str(item.get("text") or ""))
                if not post_id or not text_en:
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
                    "text_en": text_en[:16000],
                    "image_url": str(item.get("image_url") or ""),
                    "links": links[:20],
                }

            items = list(unique.values())
            items.sort(key=lambda x: int(x["id"]) if x["id"].isdigit() else 0, reverse=True)
            items = items[:10]

            if not items:
                raise RuntimeError("telegram_preview_empty")

            _GAME_ANNOUNCEMENTS_CACHE["at"] = now
            _GAME_ANNOUNCEMENTS_CACHE["items"] = items
            _GAME_ANNOUNCEMENTS_CACHE["error"] = ""
        except Exception as exc:
            _GAME_ANNOUNCEMENTS_CACHE["error"] = type(exc).__name__
            if not _GAME_ANNOUNCEMENTS_CACHE["items"]:
                return {
                    "ok": False,
                    "source": "https://t.me/hamsterking_game",
                    "channel": "Hamster King Announcement",
                    "items": [],
                    "error": "source_unavailable",
                }
            stale = True

    source_items = list(_GAME_ANNOUNCEMENTS_CACHE["items"] or [])[:10]
    items = []
    for source in source_items:
        text_en = str(source.get("text_en") or source.get("text") or "").strip()
        if not text_en:
            continue
        localized, translated = _machine_translate(text_en, lang)
        item = dict(source)
        item["text_en"] = text_en
        item["text"] = localized
        item["lang"] = lang
        item["translated"] = bool(translated)
        items.append(item)

    return {
        "ok": True,
        "source": "https://t.me/hamsterking_game",
        "channel": "Hamster King Announcement",
        "items": items,
        "cached_at": _GAME_ANNOUNCEMENTS_CACHE["at"],
        "stale": stale,
        "lang": lang,
    }
'''

s = s[:start] + new_function + s[end:]

old_route = '''            result = game_announcements_payload()
            self.send_cabinet_json(HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_GATEWAY, result)
'''
new_route = '''            query = parse_qs(urlsplit(self.path).query)
            lang = str(query.get("lang", ["en"])[-1] or "en").lower()
            if lang not in ("en", "ru", "fa"):
                lang = "en"
            result = game_announcements_payload(lang=lang)
            self.send_cabinet_json(HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_GATEWAY, result)
'''
if old_route not in s:
    raise SystemExit("public announcements route response anchor missing")
s = s.replace(old_route, new_route, 1)

path.write_text(s)
print("GAME_ANNOUNCEMENTS_TRANSLATION_V4_PATCH_OK")
