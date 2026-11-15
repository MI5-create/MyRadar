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
import config

CHINA_AIRLINES_MATRIX = {
    "CCA": ("中国国际航空", "CA"), "CSN": ("中国南方航空", "CZ"), "CES": ("中国东方航空", "MU"),
    "CBJ": ("北京航空", "CA"), "CCD": ("大连航空", "CA"), "CDI": ("国航内蒙", "CA"),
    "CFA": ("中国飞龙", "CA"), "CKK": ("中国货运航空", "CK"), "CGH": ("桂林航空", "GT"),
    "CGZ": ("多彩贵州航空", "GY"), "CHJ": ("河北航空", "NS"), "CJR": ("金鹏航空", "Y8"),
    "CJX": ("江西航空", "RY"), "CKC": ("昆明航空", "KY"), "CQH": ("春秋航空", "9C"),
    "CSJ": ("长安航空", "9H"), "CSZ": ("深圳航空", "ZH"), "CTJ": ("天津航空", "GS"),
    "CUA": ("中国联合航空", "KN"), "CXN": ("乌鲁木齐航空", "UQ"), "CYN": ("湖南航空", "A6"),
    "CYZ": ("圆通航空", "YG"), "CZH": ("东海航空", "DZ"), "DAP": ("九元航空", "AQ"),
    "DKH": ("吉祥航空", "HO"), "ESR": ("顺丰航空", "O3"), "GDC": ("北部湾航空", "GX"),
    "HXA": ("华夏航空", "G5"), "JYH": ("奥凯航空", "BK"), "LKE": ("祥鹏航空", "8L"),
    "OKA": ("奥凯航空", "BK"), "RLH": ("瑞丽航空", "DR"), "SFJ": ("顺丰航空", "O3"),
    "TBA": ("西藏航空", "TV"), "UEA": ("成都航空", "EU"), "XMN": ("厦门航空", "MF"),
    "CSC": ("四川航空", "3U"), "CKE": ("吉祥航空", "HO"), "CDG": ("山东航空", "SC"),
    "CSH": ("上海航空", "FM"), "CHB": ("西部航空", "PN"), "CQN": ("重庆航空", "OQ"),
    "CDC": ("长龙航空", "GJ"), "CQG": ("华夏航空", "G5"), "CXA": ("厦门航空", "MF"),
    "FZA": ("福州航空", "FU"), "CAB": ("中国国际货运航空", "CA"), "COC": ("中国货运邮政", "8Y"),
    "CPA": ("国泰航空", "CX"), "HAD": ("香港航空", "HX"), "EVA": ("长荣航空", "BR"),
    "CAL": ("中华航空", "CI"), "JNA": ("真航空", "LJ"), "KAL": ("大韩航空", "KE"),
    "AAR": ("韩亚航空", "OZ"), "ANA": ("全日空", "NH"), "JAL": ("日本航空", "JL"),
    "SIA": ("新加坡航空", "SQ"), "THA": ("泰国航空", "TG"), "UAE": ("阿联酋航空", "EK"),
    "HDA": ("香港快运", "UO"), "AMU": ("澳门航空", "NX"), "CRK": ("香港航空", "HX"),
    "TTW": ("台湾虎航", "IT"), "UIA": ("立荣航空", "B7"), "FEA": ("远东航空", "FE"),
    "MDA": ("华信航空", "AE"), "SJX": ("星宇航空", "JX"), "XAX": ("星宇航空", "JX"),
    "HVN": ("越捷航空", "VJ"), "MAS": ("马来西亚航空", "MH"), "AXM": ("亚洲航空", "AK"),
    "PAL": ("菲律宾航空", "PR"), "CEB": ("宿务太平洋", "5J"), "GIA": ("印尼鹰航", "GA")
}

IATA_TO_ICAO = {}
for icao, (cn, iata) in CHINA_AIRLINES_MATRIX.items():
    IATA_TO_ICAO[iata] = icao

def get_airline_info(callsign):
    callsign = callsign.strip().upper()
    prefix3 = callsign[:3]
    prefix2 = callsign[:2]
    
    if prefix3 in CHINA_AIRLINES_MATRIX:
        return CHINA_AIRLINES_MATRIX[prefix3]
    
    if len(callsign) >= 3 and prefix2 in IATA_TO_ICAO and callsign[2].isdigit():
        return CHINA_AIRLINES_MATRIX[IATA_TO_ICAO[prefix2]]
        
    return (prefix3, prefix2)

config.CHINA_AIRLINES_MATRIX = CHINA_AIRLINES_MATRIX
config.get_airline_info = get_airline_info

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
        self._last_rows = []
        self.show_starred_only = False
        self.current_tab = "list"

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

        self.content_box = BoxLayout(size_hint=(1, 1), spacing=SP_S)

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

        self.btn_tab_switch = Button(text="硬件雷达", background_normal="",
                                     background_color=C_PRIMARY_DARK,
                                     color=(1, 1, 1, 1), bold=True)
        self.btn_tab_switch.bind(on_press=self._on_tab_switch)
        bottom_bar.add_widget(self.btn_tab_switch)
        self.add_widget(bottom_bar)

        self.content_box.add_widget(self.flight_view)
        Window.bind(size=self._on_window_resize)
        Window.bind(on_pause=self._on_pause, on_resume=self._on_resume)
        Clock.schedule_once(lambda dt: self._ask_permission(), 0.3)
        
        self._on_action_click(None)

    def _ask_permission(self):
        def on_done(granted):
            if granted:
                self._start_gps()
                self.status_label.text = "定位已授权"
            else:
                self.status_label.text = "使用备用位置"
                self._load_cache()
        PermissionPopup(on_done=on_done).open()

    def _load_cache(self):
        store = get_store()
        cached = store.data.get("flights", [])
        if not cached: return
        rows = []
        for item in cached:
            c, a, s, d = item.get("c", "?"), item.get("a", "0"), item.get("s", "0"), item.get("d", 0)
            raw = ["fake", c, "China", 0, 0, self.current_lon, self.current_lat, int(float(a)), 0, float(s), 0]
            rows.append((c, a, s, d, raw))
        self._last_rows = rows
        self.status_label.text = f"缓存 {len(rows)} 架"
        self._refresh_display()

    def _start_gps(self):
        if not HAS_GPS:
            self._load_cache()
            return
        try:
            gps.configure(on_location=self._on_gps_location, on_status=self._on_gps_status)
            gps.start(minTime=1000, minDistance=1)
            self._load_cache()
        except Exception:
            self._load_cache()

    def _stop_gps(self):
        try: gps.stop()
        except: pass

    def _on_pause(self, *args):
        self._stop_gps()
        return True

    def _on_resume(self, *args):
        self._start_gps()

    def _on_gps_location(self, **kw):
        lat, lon = kw.get('lat'), kw.get('lon')
        if lat and lon:
            self.current_lat, self.current_lon = lat, lon
            store = get_store()
            store.data["lat"], store.data["lon"] = lat, lon
            store.save()
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', "定位成功"), 0)

    def _on_gps_status(self, stype, status): pass

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def _on_window_resize(self, window, size): pass

    def _toggle_star_filter(self, *a):
        self.show_starred_only = not self.show_starred_only
        self.btn_star_filter.background_color = (C_PRIMARY_DARK if self.show_starred_only else C_GOLD)
        self._refresh_display()

    def _refresh_display(self):
        self.grid.clear_widgets()
        for c, a, s, d, raw in self._last_rows:
            if self.show_starred_only and not get_store().is_starred(c): continue
            self.grid.add_widget(FlightCard(c, a, s, d, raw, self._show_detail, on_toggle_star=self._on_star_change))

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
        if self.auto_refresh_event:
            self.auto_refresh_event.cancel()
            self.auto_refresh_event = None
            self.btn_action.text = "自动刷新"
            self.btn_action.background_color = C_PRIMARY
            return

        self.btn_action.text = "停止"
        self.btn_action.background_color = C_TAG_RED
        self.countdown = REFRESH_INTERVAL
        self._fetch_flights()
        self.auto_refresh_event = Clock.schedule_interval(self._tick, 1.0)

    def _tick(self, dt):
        if self._fetching: return
        self.countdown -= 1
        if self.countdown <= 0:
            self.countdown = REFRESH_INTERVAL
            self._fetch_flights()
        else:
            self.status_label.text = f"倒计时 {self.countdown}s"

    def _fetch_flights(self):
        if self._fetching: return
        self._fetching = True
        self.status_label.text = "请求中…"
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        radius_nm = int(RADIUS_KM / 1.852)
        headers = {"User-Agent": "Mozilla/5.0"}
        
        # 3秒超时：良好网络下绝对够用，弱网下最多卡3秒就会跳过
        timeout_sec = 3.0  

        try:
            url = f"https://api.airplanes.live/v2/point/{self.current_lat}/{self.current_lon}/{radius_nm}"
            resp = requests.get(url, headers=headers, timeout=timeout_sec, verify=False)
            if resp.status_code == 200 and resp.json().get("ac"):
                self._parse_adsb_data(resp.json().get("ac"), "真实(主)")
                return
        except Exception: pass

        try:
            url = f"https://api.adsb.lol/v2/point/{self.current_lat}/{self.current_lon}/{radius_nm}"
            resp = requests.get(url, headers=headers, timeout=timeout_sec, verify=False)
            if resp.status_code == 200 and resp.json().get("ac"):
                self._parse_adsb_data(resp.json().get("ac"), "真实(备)")
                return
        except Exception: pass

        try:
            url = f"https://opendata.adsb.fi/api/v2/lat/{self.current_lat}/lon/{self.current_lon}/dist/{radius_nm}"
            resp = requests.get(url, headers=headers, timeout=timeout_sec, verify=False)
            if resp.status_code == 200 and resp.json().get("ac"):
                self._parse_adsb_data(resp.json().get("ac"), "真实(兜底)")
                return
        except Exception: pass

        try:
            d_lat = RADIUS_KM / 111.0
            d_lon = RADIUS_KM / (111.0 * math.cos(math.radians(self.current_lat)))
            bbox = (self.current_lat - d_lat, self.current_lat + d_lat,
                    self.current_lon - d_lon, self.current_lon + d_lon)
            os_headers = {"User-Agent": "Mozilla/5.0"}
            os_headers.update(OpenSkyAuth.get_headers())
            resp = requests.get(
                "https://opensky-network.org/api/states/all",
                params={"lamin": bbox[0], "lamax": bbox[1], "lomin": bbox[2], "lomax": bbox[3]},
                headers=os_headers, timeout=timeout_sec, verify=False)
            if resp.status_code == 200:
                states = resp.json().get("states")
                if states:
                    rows = []
                    for s in states:
                        if not isinstance(s, list) or len(s) < 11: continue
                        cs = (s[1] or "").strip()
                        if not cs: continue
                        lon, lat = s[5], s[6]
                        if lat is None or lon is None: continue
                        dist = self._haversine(self.current_lat, self.current_lon, lat, lon)
                        alt = s[7] if s[7] is not None else 0
                        spd = s[9] if s[9] is not None else 0
                        rows.append((cs, f"{alt:.0f}", f"{spd:.0f}", round(dist), s))
                    if rows:
                        rows.sort(key=lambda x: x[3])
                        Clock.schedule_once(lambda dt: self._on_success(rows[:150], "OpenSky数据"), 0)
                        return
        except Exception: pass

        def fail_callback(dt):
            self._last_rows = []
            self._refresh_display()
            self.status_label.text = "无网络或当前无航班"
            self._fetching = False
        Clock.schedule_once(fail_callback, 0)

    def _parse_adsb_data(self, ac_list, source_name):
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
            Clock.schedule_once(lambda dt: self._on_success(rows[:150], source_name), 0)

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

    def _on_tab_switch(self, instance):
        self.content_box.clear_widgets()
        if self.current_tab == "list":
            self.current_tab = "radar"
            self.btn_tab_switch.text = "航班列表"
            
            self.radar_status.text = "雷达未连接"
            self.radar_box.clear_widgets()
            self.radar_box.add_widget(self.radar_status)
            
            self.content_box.add_widget(self.radar_card)
            
            if self.radar_source:
                self.radar_source.stop()
            self.radar_status.text = "等待数据…"
            self.radar_box.clear_widgets()
            self.radar_view = RadarView(size_hint=(1, 1))
            self.radar_box.add_widget(self.radar_view)
            self.radar_source = RadarSource(self._radar_data, self._radar_status)
            self.radar_source.start()
        else:
            self.current_tab = "list"
            self.btn_tab_switch.text = "硬件雷达"
            self.content_box.add_widget(self.flight_view)
            if self.radar_source:
                self.radar_source.stop()

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
