import os
import json
from kivy.app import App
from config import FALLBACK_LAT, FALLBACK_LON, RADIUS_KM


class LocalStore:
    """跨平台本地存储，Android 落在应用私有目录，Windows 落在 %APPDATA%"""
    def __init__(self):
        try:
            base = App.get_running_app().user_data_dir
        except Exception:
            base = os.path.expanduser("~")
        os.makedirs(base, exist_ok=True)
        self.path = os.path.join(base, "radar_state.json")
        self.data = {
            "lat": FALLBACK_LAT,
            "lon": FALLBACK_LON,
            "radius_km": RADIUS_KM,
            "flights": [],
            "source": "",
            "starred": {},
        }
        self.load()

    def load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data.update(json.load(f))
        except Exception:
            pass
        return self.data

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False)
        except Exception:
            pass

    # ---- 星座关注 ----
    def is_starred(self, callsign):
        return callsign in self.data.get("starred", {})

    def toggle_star(self, callsign, info=None):
        starred = self.data.setdefault("starred", {})
        if callsign in starred:
            del starred[callsign]
            result = False
        else:
            starred[callsign] = info or {}
            result = True
        self.save()
        return result

    def starred_list(self):
        return list(self.data.get("starred", {}).keys())


# 全局单例
_STORE = None

def get_store():
    global _STORE
    if _STORE is None:
        _STORE = LocalStore()
    return _STORE