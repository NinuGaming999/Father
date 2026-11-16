"""Embedded Arlecchino 3D avatar with a safe animated fallback when Qt WebEngine is unavailable."""

import json
import logging
import sys
import time
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .widgets import OrbWidget, STATE_COLORS

log = logging.getLogger("trilion.avatar")


def asset_path(*parts):
    """Resolve bundled PyInstaller assets or the source checkout."""
    base = getattr(sys, "_MEIPASS", None)
    root = Path(base) if base else Path(__file__).resolve().parents[2]
    return root.joinpath(*parts)


class AvatarWidget(QWidget):
    """Three.js renderer hosted in Qt WebEngine; never required for the assistant's core loop."""

    def __init__(self, version=""):
        super().__init__()
        self.version = version
        self.state = "idle"
        self.level = 0.0
        self.mood = "neutral"
        self._ready = False
        self._last_js = 0.0
        self._fallback = None
        self._view = None
        self._label = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        try:
            from PySide6.QtWebEngineCore import QWebEngineSettings
            from PySide6.QtWebEngineWidgets import QWebEngineView

            page = asset_path("assets", "avatar", "viewer.html")
            model = asset_path("assets", "avatar", "arlecchino.glb")
            three = asset_path("assets", "vendor", "three.module.js")
            loader = asset_path("assets", "vendor", "loaders", "GLTFLoader.js")
            if not all(p.is_file() for p in (page, model, three, loader)):
                raise FileNotFoundError("Avatar runtime assets are incomplete.")

            view = QWebEngineView(self)
            settings = view.settings()
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, False)
            view.setContextMenuPolicy(Qt.NoContextMenu)
            view.setPageBackgroundColor(Qt.transparent)
            view.loadFinished.connect(self._on_loaded)
            view.load(QUrl.fromLocalFile(str(page.resolve())))
            self._view = view
            layout.addWidget(view, 1)
        except Exception as exc:
            log.warning("3D avatar renderer unavailable; using the lightweight core display: %s", exc)
            self._fallback = OrbWidget(version)
            layout.addWidget(self._fallback, 1)
            self._label = QLabel("3D avatar unavailable in this build")
            self._label.setAlignment(Qt.AlignCenter)
            self._label.setStyleSheet("color:#7a9cc8;font-size:9px")
            layout.addWidget(self._label)

    @property
    def renderer_available(self):
        return self._view is not None

    def _on_loaded(self, ok):
        if not ok:
            log.error("Arlecchino viewer page failed to load.")
            return
        self._ready = True
        self._push_state(force=True)

    def set_activity(self, state, level=0.0):
        state = state if state in ("idle", "listening", "thinking", "speaking", "acting") else "idle"
        level = max(0.0, min(1.0, float(level or 0.0)))
        changed = state != self.state or abs(level - self.level) >= 0.06
        self.state, self.level = state, level
        if self._fallback:
            colors = {
                "idle": STATE_COLORS["idle"],
                "listening": STATE_COLORS["listening"],
                "thinking": STATE_COLORS["thinking"],
                "speaking": STATE_COLORS["speaking"],
                "acting": STATE_COLORS["acting"],
            }
            self._fallback.tick(time.monotonic(), level, state, colors[state])
        elif changed:
            self._push_state()

    def set_mood(self, mood):
        mood = str(mood or "neutral").lower()
        if mood not in ("neutral", "warm", "amused", "stern", "thoughtful", "concerned", "alert"):
            mood = "neutral"
        if mood != self.mood:
            self.mood = mood
            self._push_state()

    def _push_state(self, force=False):
        if not self._ready or not self._view:
            return
        now = time.monotonic()
        if not force and now - self._last_js < 0.025:
            return
        self._last_js = now
        payload = json.dumps({"state": self.state, "level": self.level, "mood": self.mood})
        self._view.page().runJavaScript(f"window.trilionAvatar && window.trilionAvatar.setState({payload});")

    def closeEvent(self, event):
        if self._view:
            try:
                self._view.stop()
            except Exception:
                pass
        super().closeEvent(event)
