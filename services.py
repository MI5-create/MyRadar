import threading
import time
import requests
from kivy.utils import platform
import config


class OpenSkyAuth:
    """管理 OAuth2 令牌，30 分钟有效，快过期自动刷新"""
    _token = None
    _expire_at = 0
    _lock = threading.Lock()

    @classmethod
    def get_headers(cls):
        if not config.OPENSKY_CLIENT_ID or not config.OPENSKY_CLIENT_SECRET:
            return {}
        with cls._lock:
            now = time.time()
            if cls._token and now < cls._expire_at - 60:
                return {"Authorization": f"Bearer {cls._token}"}
            try:
                resp = requests.post(
                    "https://auth.opensky-network.org/auth/realms/"
                    "opensky-network/protocol/openid-connect/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": config.OPENSKY_CLIENT_ID,
                        "client_secret": config.OPENSKY_CLIENT_SECRET,
                    },
                    timeout=10,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    cls._token = data.get("access_token")
                    cls._expire_at = now + data.get("expires_in", 1800)
                    return {"Authorization": f"Bearer {cls._token}"}
            except Exception:
                pass
            return {}


class PermissionManager:
    """Android 动态申请权限，其他平台直接通过"""
    @staticmethod
    def request_all(on_done):
        if platform == "android":
            try:
                from android.permissions import request_permissions, Permission
                request_permissions(
                    [
                        Permission.ACCESS_FINE_LOCATION,
                        Permission.ACCESS_COARSE_LOCATION,
                        Permission.WRITE_EXTERNAL_STORAGE,
                        Permission.READ_EXTERNAL_STORAGE,
                    ],
                    lambda perms, grants: on_done(all(grants)),
                )
                return
            except Exception:
                on_done(False)
                return
        on_done(True)