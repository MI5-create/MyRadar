import warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore")

from kivy.config import Config
Config.set('graphics', 'multisamples', '0')
Config.set('graphics', 'window_state', 'maximized')

from kivy.core.text import LabelBase
try:
    LabelBase.register(name='Roboto', fn_regular='SIMHEI.TTF')
except Exception:
    pass

import math
import threading
import requests

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

try:
    from plyer import gps
    HAS_GPS = True
except Exception:
    HAS_GPS = False

from config import (
    C_BG, C_GLASS, C_TEXT_MAIN, C_TEXT_SUB, C_PRIMARY, C_PRIMARY_DARK,
    C_TAG_RED, C_GOLD, SP_XS, SP_S, SP_M, SP_L, SP_XL,
    RADIUS_KM, REFRESH_INTERVAL, FALLBACK_LAT, FALLBACK_LON,
)
from storage import get_store
from services import OpenSkyAuth
from radar import RadarSource
from ui_components import (
    GlassCard, FlightCard, RadarView, FlightDetailPopup, PermissionPopup,
)

class FlightRadarRoot(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical",
                         padding=[SP_S, dp(30), SP_S, SP_S],
                         spacing=SP_S)
        with self.canvas.before:
            Color(*C_BG)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        store = get_store()
        self.current_lat = store.data.get("lat", FALLBACK_LAT)
        self.current_lon = store.data.get("lon", FALLBACK_LON)
        self._fetching = False
        self.auto_refresh_event = None
        self.countdown = REFRESH_INTERVAL
        self.radar_source = None
        self.radar_view = None
        self._gps_started = False
        self._layout_mode = None
        self._resize_event = None
        self._last_rows = []
        self.show_starred_only = False

        header = BoxLayout(size_hint=(1, None), height=dp(44), spacing=SP_S)
        title_box = BoxLayout(size_hint_x=0.5, orientation="vertical",
                              spacing=dp(0), padding=[0, dp(2)])
        title_box.add_widget(Label(text="航班雷达", color=C_TEXT_MAIN,
                                   font_size="20sp", bold=True,
                                   halign="left", valign="bottom"))
        self.status_label = Label(text="定位中…", color=C_TEXT_SUB,
                                  font_size="11sp", halign="left", valign="top")
        title_box.add_widget(self.status_label)
        header.add_widget(title_box)

        self.btn_star_filter = Button(text="★ 星座", background_normal="",
                                      background_color=C_GOLD,
                                      color=(1, 1, 1, 1), bold=True,
                                      size_hint_x=0.5, font_size="13sp")
        self.btn_star_filter.bind(on_press=self._toggle_star_filter)
        header.add_widget(self.btn_star_filter)
        self.add_widget(header)

        self.content_box = BoxLayout(size_hint=(1, 1), spacing=SP_S,
                                     orientation="horizontal")

        self.flight_view = ScrollView()
        self.grid = GridLayout(cols=1, size_hint_y=None, spacing=SP_S)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        self.flight_view.add_widget(self.grid)

        self.radar_card = GlassCard(bg_color=C_GLASS, radius=16,
                                    padding=[SP_XS, SP_XS])
        self.radar_status = Label(text="雷达未连接", font_size="18sp",
                                  color=C_TEXT_SUB, bold=True)
        self.radar_box = BoxLayout()
        self.radar_box.add_widget(self.radar_status)
        self.radar_card.add_widget(self.radar_box)
        self.add_widget(self.content_box)

        bottom_bar = BoxLayout(size_hint=(1, None), height=dp(48), spacing=SP_S)
        self.btn_action = Button(text="自动刷新", background_normal="",
                                 background_color=C_PRIMARY,
                                 color=(1, 1, 1, 1), bold=True)
        self.btn_action.bind(on_press=self._on_action_click)
        bottom_bar.add_widget(self.btn_action)

        self.btn_radar = Button(text="雷达", background_normal="",
                                background_color=C_PRIMARY_DARK,
                                color=(1, 1, 1, 1), bold=True)
        self.btn_radar.bind(on_press=self._on_radar_click)
        bottom_bar.add_widget(self.btn_radar)
        self.add_widget(bottom_bar)

        self._set_mode("split" if Window.width >= 1000 else "flight")
        Window.bind(size=self._on_window_resize)
        Window.bind(on_pause=self._on_pause, on_resume=self._on_resume)
        Clock.schedule_once(lambda dt: self._ask_permission(), 0.3)

    def _ask_permission(self):
        def on_done(granted):
            if granted:
                self._start_gps()
                self.status_label.text = "权限已授予"
            else:
                self.status_label.text = "权限受限·使用备用位置"
                self._load_cache()
        PermissionPopup(on_done=on_done).open()

    def _load_cache(self):
        store = get_store()
        cached = store.data.get("flights", [])
        if not cached:
            return
        rows = []
        for item in cached:
            c = item.get("c", "?")
            a = item.get("a", "0")
            s = item.get("s", "0")
            d = item.get("d", 0)
            try:
                alt_v = int(float(a))
                spd_v = float(s)
            except Exception:
                alt_v, spd_v = 0, 0
            raw = ["fake", c, "China", 0, 0,
                   self.current_lon, self.current_lat,
                   alt_v, 0, spd_v, 0]
            rows.append((c, a, s, d, raw))
        self._last_rows = rows
        self.status_label.text = f"加载缓存 {len(rows)} 架"
        self._refresh_display()

    def _start_gps(self):
        if not HAS_GPS:
            self.status_label.text = "GPS不可用·使用备用"
            self._load_cache()
            return
        try:
            gps.configure(on_location=self._on_gps_location,
                          on_status=self._on_gps_status)
            gps.start(minTime=1000, minDistance=1)
            self._gps_started = True
            self._load_cache()
        except Exception:
            self.status_label.text = "使用备用位置"
            self._load_cache()

    def _stop_gps(self):
        try:
            gps.stop()
        except Exception:
            pass
        self._gps_started = False

    def _on_pause(self, *args):
        self._stop_gps()
        return True

    def _on_resume(self, *args):
        self._start_gps()

    def _on_gps_location(self, **kw):
        lat = kw.get('lat')
        lon = kw.get('lon')
        if lat is not None and lon is not None:
            self.current_lat = lat
            self.current_lon = lon
            store = get_store()
            store.data["lat"] = lat
            store.data["lon"] = lon
            store.save()
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', "定位成功"), 0)

    def _on_gps_status(self, stype, status):
        pass

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def _on_window_resize(self, window, size):
        if self._resize_event:
            self._resize_event.cancel()
        self._resize_event = Clock.schedule_once(lambda dt: self._apply_resize(size), 0.15)

    def _apply_resize(self, size):
        w = size[0]
        if w >= 1400:
            mode = "triple"
        elif w >= 1000:
            mode = "split"
        else:
            mode = "flight"
        self._set_mode(mode)

    def _set_mode(self, mode):
        if mode == self._layout_mode:
            return
        self._layout_mode = mode
        self.content_box.clear_widgets()

        if mode == "flight":
            self.content_box.orientation = "vertical"
            self.flight_view.size_hint_x = 1
            self.flight_view.size_hint_y = 1
            self.radar_card.size_hint_x = 1
            self.radar_card.size_hint_y = 0
            self.content_box.add_widget(self.flight_view)
        elif mode == "triple":
            self.content_box.orientation = "horizontal"
            self.flight_view.size_hint_x = 1
            self.flight_view.size_hint_y = 1
            self.radar_card.size_hint_x = 0.45
            self.radar_card.size_hint_y = 1
            self.content_box.add_widget(self.flight_view)
            self.content_box.add_widget(self.radar_card)
        else:
            self.content_box.orientation = "horizontal"
            self.flight_view.size_hint_x = 0.6
            self.flight_view.size_hint_y = 1
            self.radar_card.size_hint_x = 0.4
            self.radar_card.size_hint_y = 1
            self.content_box.add_widget(self.flight_view)
            self.content_box.add_widget(self.radar_card)

    def _toggle_star_filter(self, *a):
        self.show_starred_only = not self.show_starred_only
        self.btn_star_filter.background_color = (C_PRIMARY_DARK if self.show_starred_only else C_GOLD)
        self._refresh_display()

    def _refresh_display(self):
        self.grid.clear_widgets()
        for c, a, s, d, raw in self._last_rows:
            if self.show_starred_only and not get_store().is_starred(c):
                continue
            self.grid.add_widget(FlightCard(c, a, s, d, raw, self._show_detail,
                                            on_toggle_star=self._on_star_change))

    def _on_star_change(self, callsign):
        is_now = get_store().is_starred(callsign)
        for child in self.grid.children:
            if getattr(child, "callsign", None) == callsign:
                child.is_starred = is_now
                child.star_btn.text = "已关注" if is_now else "+ 关注"
                child.star_btn.background_color = C_GOLD if is_now else C_PRIMARY
        if self.show_starred_only:
            self._refresh_display()

    def _on_action_click(self, instance):
        if self.btn_action.text == "停止":
            if self.auto_refresh_event:
                self.auto_refresh_event.cancel()
            self.btn_action.text = "自动刷新"
            self.btn_action.background_color = C_PRIMARY
            return
        self.btn_action.text = "停止"
        self.btn_action.background_color = C_TAG_RED
        self.countdown = REFRESH_INTERVAL
        self._fetch_flights()
        self.auto_refresh_event = Clock.schedule_interval(self._tick, 1.0)

    def _tick(self, dt):
        if self._fetching:
            return
        self.countdown -= 1
        if self.countdown <= 0:
            self.countdown = REFRESH_INTERVAL
            self._fetch_flights()
        else:
            self.status_label.text = f"倒计时 {self.countdown}s"

    def _fetch_flights(self):
        if self._fetching:
            return
        self._fetching = True
        self.status_label.text = "请求中…"
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            radius_nm = int(RADIUS_KM / 1.852)
            url = f"https://api.airplanes.live/v2/point/{self.current_lat}/{self.current_lon}/{radius_nm}"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=15, verify=False)
            resp.raise_for_status()
            data = resp.json()
            ac_list = data.get("ac", [])
            
            if ac_list:
                rows = []
                for ac in ac_list:
                    callsign = (ac.get("flight") or "").strip()
                    if not callsign: continue
                    lat = ac.get("lat")
                    lon = ac.get("lon")
                    if lat is None or lon is None: continue
                    
                    alt = ac.get("alt_baro", 0)
                    if alt == "ground": alt = 0
                    spd = ac.get("gs", 0)
                    track = ac.get("track", 0)
                    hex_code = ac.get("hex", "fake")
                    
                    dist = self._haversine(self.current_lat, self.current_lon, lat, lon)
                    raw = [hex_code, callsign, "China", 0, 0, lon, lat, alt, 0, spd, track]
                    rows.append((callsign, f"{alt}", f"{spd}", round(dist), raw))
                
                if rows:
                    rows.sort(key=lambda x: x[3])
                    Clock.schedule_once(lambda dt: self._on_success(rows[:150], "真实数据(ADS-B)"), 0)
                    return
        except Exception:
            pass

        try:
            radius_nm = int(RADIUS_KM / 1.852)
            url = f"https://opendata.adsb.fi/api/v2/lat/{self.current_lat}/lon/{self.current_lon}/dist/{radius_nm}"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=15, verify=False)
            resp.raise_for_status()
            data = resp.json()
            ac_list = data.get("ac", [])
            
            if ac_list:
                rows = []
                for ac in ac_list:
                    callsign = (ac.get("flight") or "").strip()
                    if not callsign: continue
                    lat = ac.get("lat")
                    lon = ac.get("lon")
                    if lat is None or lon is None: continue
                    
                    alt = ac.get("alt_baro", 0)
                    if alt == "ground": alt = 0
                    spd = ac.get("gs", 0)
                    track = ac.get("track", 0)
                    hex_code = ac.get("hex", "fake")
                    
                    dist = self._haversine(self.current_lat, self.current_lon, lat, lon)
                    raw = [hex_code, callsign, "China", 0, 0, lon, lat, alt, 0, spd, track]
                    rows.append((callsign, f"{alt}", f"{spd}", round(dist), raw))
                
                if rows:
                    rows.sort(key=lambda x: x[3])
                    Clock.schedule_once(lambda dt: self._on_success(rows[:150], "真实数据(备用)"), 0)
                    return
        except Exception:
            pass

        try:
            d_lat = RADIUS_KM / 111.0
            d_lon = RADIUS_KM / (111.0 * math.cos(math.radians(self.current_lat)))
            bbox = (self.current_lat - d_lat, self.current_lat + d_lat,
                    self.current_lon - d_lon, self.current_lon + d_lon)
            headers = {"User-Agent": "Mozilla/5.0"}
            headers.update(OpenSkyAuth.get_headers())
            resp = requests.get(
                "https://opensky-network.org/api/states/all",
                params={"lamin": bbox[0], "lamax": bbox[1],
                        "lomin": bbox[2], "lomax": bbox[3]},
                headers=headers, timeout=15, verify=False)
            resp.raise_for_status()
            states = resp.json().get("states")
            
            if states:
                rows = []
                for s in states:
                    if not isinstance(s, list) or len(s) < 11: continue
                    callsign = (s[1] or "").strip()
                    if not callsign: continue
                    lon, lat = s[5], s[6]
                    if lat is None or lon is None: continue
                    dist = self._haversine(self.current_lat, self.current_lon, lat, lon)
                    alt = s[7] if s[7] is not None else 0
                    spd = s[9] if s[9] is not None else 0
                    rows.append((callsign, f"{alt:.0f}", f"{spd:.0f}", round(dist), s))
                
                if rows:
                    rows.sort(key=lambda x: x[3])
                    Clock.schedule_once(lambda dt: self._on_success(rows[:150], "真实数据(OS)"), 0)
                    return
        except Exception:
            pass

        def fail_callback(dt):
            self.status_label.text = "网络受限或周围无航班"
            self._refresh_display()
            self._fetching = False
        Clock.schedule_once(fail_callback, 0)

    def _on_success(self, rows, source_text):
        self._last_rows = rows
        self.status_label.text = f"已更新 {len(rows)} 架 ({source_text})"
        store = get_store()
        store.data["flights"] = [{"c": c, "a": a, "s": s, "d": d} for c, a, s, d, _ in rows[:50]]
        store.data["source"] = source_text
        store.save()
        self._refresh_display()
        self._fetching = False

    def _show_detail(self, raw):
        FlightDetailPopup(raw, self.current_lat, self.current_lon,
                          on_star_change=self._on_star_change).open()

    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2):
        R = 6371.0
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp_ = math.radians(lat2 - lat1)
        dl = math.radians(lon2 - lon1)
        a = (math.sin(dp_ / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
        return 2 * R * math.asin(math.sqrt(a))

    def _on_radar_click(self, instance):
        if self._layout_mode == "flight":
            if self.btn_radar.text == "断开雷达":
                if self.radar_source:
                    self.radar_source.stop()
                self.btn_radar.text = "雷达"
                self.btn_radar.background_color = C_PRIMARY_DARK
                self.content_box.clear_widgets()
                self.content_box.add_widget(self.flight_view)
                return
            else:
                self.btn_radar.text = "断开雷达"
                self.btn_radar.background_color = C_TAG_RED
                self.content_box.clear_widgets()
                self.content_box.add_widget(self.radar_card)
                
                self.radar_status.text = "等待数据…"
                self.radar_box.clear_widgets()
                self.radar_view = RadarView(size_hint=(1, 1))
                self.radar_box.add_widget(self.radar_view)
                self.radar_source = RadarSource(self._radar_data, self._radar_status)
                self.radar_source.start()
                return

        if self.btn_radar.text == "断开雷达":
            if self.radar_source:
                self.radar_source.stop()
            self.btn_radar.text = "连接雷达"
            self.btn_radar.background_color = C_PRIMARY_DARK
            self.radar_status.text = "雷达未连接"
            return
        self.btn_radar.text = "连接中…"
        self.btn_radar.background_color = C_TEXT_SUB
        self.radar_status.text = "等待数据…"
        self.radar_box.clear_widgets()
        self.radar_view = RadarView(size_hint=(1, 1))
        self.radar_box.add_widget(self.radar_view)
        self.radar_source = RadarSource(self._radar_data, self._radar_status)
        self.radar_source.start()

    def _radar_status(self, text):
        Clock.schedule_once(lambda dt: self._set_radar_status_ui(text), 0)

    def _set_radar_status_ui(self, text):
        if self.radar_view is None: return
        self.radar_status.text = text

    def _radar_data(self, angle, dist):
        def update(dt):
            if self.radar_view:
                self.radar_view.add_point(angle, dist)
                self.radar_status.text = f"角度 {angle}° / {dist}cm"
        Clock.schedule_once(update, 0)

class FlightRadarApp(App):
    def build(self):
        return FlightRadarRoot()

if __name__ == "__main__":
    FlightRadarApp().run()
