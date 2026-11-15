import io
import time
import math
import threading
import requests
from math import radians, cos, sin, atan2, degrees

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle, InstructionGroup
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image as KivyImage
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.relativelayout import RelativeLayout

from config import (
    C_GLASS, C_TEXT_MAIN, C_TEXT_SUB, C_PRIMARY, C_PRIMARY_DARK,
    C_PRIMARY_SOFT, C_TAG_RED, C_GOLD, C_DIVIDER,
    C_RADAR_BG, C_RADAR_GRID, C_RADAR_POINT, C_RADAR_GLOW,
    SP_XS, SP_S, SP_M, SP_L, SP_XL,
    FALLBACK_LAT, FALLBACK_LON, get_airline_info,
)
from storage import get_store

class GlassCard(BoxLayout):
    def __init__(self, bg_color=C_GLASS, radius=16, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.radius = radius
        self.bind(pos=self._draw, size=self._draw)
        with self.canvas.before:
            Color(0, 0, 0, 0.04)
            self._shadow = RoundedRectangle(
                pos=(self.x, self.y - 2),
                size=(self.width, self.height + 4),
                radius=[self.radius + 1])
            Color(*self.bg_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size,
                                          radius=[self.radius])
            Color(*C_DIVIDER)
            self._border = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height,
                                   self.radius), width=0.8)

    def _draw(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size
        self._shadow.pos = (self.x, self.y - 2)
        self._shadow.size = (self.width, self.height + 4)
        self._border.rounded_rectangle = (
            self.x, self.y, self.width, self.height, self.radius)

class FlightCard(GlassCard):
    def __init__(self, callsign, alt, spd, dist, raw_data, on_click,
                 on_toggle_star=None, **kwargs):
        super().__init__(bg_color=C_GLASS, radius=12,
                         size_hint=(1, None), height=dp(72),
                         padding=[dp(6), dp(8)], spacing=dp(6), **kwargs)
        self.raw_data = raw_data
        self.on_click = on_click
        self.callsign = callsign
        self.on_toggle_star = on_toggle_star
        self.is_starred = get_store().is_starred(callsign)

        prefix = callsign[:3].upper()
        cn_name, iata = get_airline_info(callsign)
        
        display_callsign = callsign.strip()
        if iata != prefix and len(callsign) > 3:
            display_callsign = iata + callsign[3:]

        badge = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(52),
                          spacing=dp(2))
        
        lbl_name = Label(text=cn_name, color=C_TEXT_MAIN,
                         font_size="11sp", bold=True, halign="center",
                         valign="middle")
        lbl_name.bind(size=lbl_name.setter('text_size'))
        badge.add_widget(lbl_name)
        
        badge.add_widget(Label(text=f"{alt}m", color=C_TEXT_SUB,
                               font_size="10sp", halign="center"))
        self.add_widget(badge)

        mid = BoxLayout(orientation="vertical", spacing=dp(2), size_hint_x=1)
        
        name_lbl = Label(text=display_callsign, color=C_TEXT_MAIN,
                         font_size="16sp", bold=True, halign="left",
                         valign="middle")
        name_lbl.bind(size=name_lbl.setter("text_size"))
        mid.add_widget(name_lbl)
        
        info_lbl = Label(text=f"地速 {spd} m/s", color=C_TEXT_SUB,
                         font_size="11sp", halign="left")
        info_lbl.bind(size=info_lbl.setter("text_size"))
        mid.add_widget(info_lbl)
        
        self.add_widget(mid)

        star = Button(text="已关注" if self.is_starred else "+ 关注",
                      background_normal="", 
                      background_color=C_GOLD if self.is_starred else C_PRIMARY,
                      color=(1, 1, 1, 1),
                      font_size="11sp", 
                      size_hint=(None, None), size=(dp(48), dp(28)),
                      pos_hint={"center_y": 0.5})
        star.bind(on_press=self._on_star)
        self.add_widget(star)
        self.star_btn = star

        tag = BoxLayout(size_hint_x=None, width=dp(50),
                        pos_hint={"center_y": 0.5})
        with tag.canvas.before:
            Color(*C_PRIMARY_SOFT)
            self._tag_rect = RoundedRectangle(pos=tag.pos, size=tag.size,
                                              radius=[dp(6)])
        def _tag_update(*a):
            self._tag_rect.pos = tag.pos
            self._tag_rect.size = tag.size
        tag.bind(pos=_tag_update, size=_tag_update)
        
        dist_lbl = Label(text=f"{dist}km", color=C_PRIMARY,
                         font_size="11sp", bold=True, halign="center",
                         valign="middle")
        dist_lbl.bind(size=dist_lbl.setter('text_size'))
        tag.add_widget(dist_lbl)
        self.add_widget(tag)

    def _on_star(self, *a):
        info = {"lat": self.raw_data[6], "lon": self.raw_data[5],
                "alt": self.raw_data[7], "spd": self.raw_data[9],
                "ts": time.time()}
        now_starred = get_store().toggle_star(self.callsign, info)
        self.is_starred = now_starred
        self.star_btn.text = "已关注" if now_starred else "+ 关注"
        self.star_btn.background_color = C_GOLD if now_starred else C_PRIMARY
        if self.on_toggle_star:
            self.on_toggle_star(self.callsign)

    def on_touch_down(self, touch):
        if self.star_btn.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if self.collide_point(*touch.pos):
            if self.on_click:
                self.on_click(self.raw_data)
            return True
        return super().on_touch_down(touch)

class TacticalRadarView(RelativeLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.center_lat = FALLBACK_LAT
        self.center_lon = FALLBACK_LON
        self.flight_lat = None
        self.flight_lon = None
        self.flight_heading = 0
        self.flight_spd = 0
        self.scan_angle = 0
        self.max_range = 500.0 
        self.dist_to_center = 0
        self.bearing = 0

        with self.canvas:
            Color(*C_RADAR_BG)
            self.bg_rect = RoundedRectangle(radius=[16])
            
            Color(*C_RADAR_GRID)
            self.line_out = Line(width=1.2)
            self.line_in = Line(width=1.2)
            self.line_in2 = Line(width=1.2)
            self.line_h = Line(width=1.0)
            self.line_v = Line(width=1.0)
            
            Color(0.2, 0.9, 0.4, 0.8)
            self.scan_line = Line(width=2.5)
            
            Color(1, 1, 1, 0.8)
            self.center_dot = Ellipse(size=(6, 6))
            
            Color(*C_RADAR_GLOW)
            self.glow = Ellipse(size=(18, 18))
            Color(*C_RADAR_POINT)
            self.dot = Ellipse(size=(8, 8))

        for t in ["N", "S", "W", "E"]:
            lbl = Label(text=t, color=C_RADAR_GRID, bold=True,
                        font_size="12sp", size_hint=(None, None),
                        size=(dp(26), dp(26)), halign="center", valign="middle")
            lbl.text_size = lbl.size
            setattr(self, f"lbl_{t}", lbl)
            self.add_widget(lbl)

        self.bind(pos=self._layout, size=self._layout)
        self._ev = Clock.schedule_interval(self._update_anim, 0.05)

    def _update_anim(self, dt):
        self.scan_angle = (self.scan_angle + 6) % 360
        
        w, h = self.width, self.height
        if w > 50 and h > 50:
            cx, cy = w / 2.0, h / 2.0
            radius = min(w, h) / 2.0 - 30
            rad = radians(self.scan_angle)
            self.scan_line.points = [cx, cy, cx + radius * sin(rad), cy + radius * cos(rad)]

        if self.flight_lat is not None and self.flight_spd > 0:
            multiplier = 30
            dist_m = self.flight_spd * dt * multiplier
            self.flight_lat += (dist_m * cos(radians(self.flight_heading))) / 111000.0
            self.flight_lon += (dist_m * sin(radians(self.flight_heading))) / (111000.0 * cos(radians(self.flight_lat)))
            self._calc_flight_pos()
            self._draw_flight()

    def update_position(self, lat, lon, heading, spd):
        self.flight_lat = lat
        self.flight_lon = lon
        self.flight_heading = heading or 0
        self.flight_spd = spd or 0
        self._calc_flight_pos()
        self._draw_flight()

    def _calc_flight_pos(self):
        if self.flight_lat is None: return
        R = 6371.0
        d_lat = radians(self.flight_lat - self.center_lat)
        d_lon = radians(self.flight_lon - self.center_lon)
        a = (sin(d_lat / 2) ** 2 + cos(radians(self.center_lat))
             * cos(radians(self.flight_lat)) * sin(d_lon / 2) ** 2)
        a = min(1.0, max(0.0, a)) 
        self.dist_to_center = 2 * R * math.asin(math.sqrt(a))
        
        y = sin(d_lon) * cos(radians(self.flight_lat))
        x = (cos(radians(self.center_lat)) * sin(radians(self.flight_lat))
             - sin(radians(self.center_lat)) * cos(radians(self.flight_lat)) * cos(d_lon))
        self.bearing = (degrees(atan2(y, x)) + 360) % 360

    def _layout(self, *args):
        w, h = self.width, self.height
        if w < 50 or h < 50: return
        self.bg_rect.pos = (0, 0)
        self.bg_rect.size = (w, h)
        
        cx, cy = w / 2.0, h / 2.0
        radius = min(w, h) / 2.0 - 30

        self.line_out.circle = (cx, cy, radius)
        self.line_in.circle = (cx, cy, radius * 0.66)
        self.line_in2.circle = (cx, cy, radius * 0.33)
        self.line_h.points = [cx - radius, cy, cx + radius, cy]
        self.line_v.points = [cx, cy - radius, cx, cy + radius]
        
        self.center_dot.pos = (cx - 3, cy - 3)
        self.center_dot.size = (6, 6)

        self.lbl_N.pos = (cx - dp(13), cy + radius - 15 - dp(13))
        self.lbl_S.pos = (cx - dp(13), cy - radius + 15 - dp(13))
        self.lbl_W.pos = (cx - radius + 15 - dp(13), cy - dp(13))
        self.lbl_E.pos = (cx + radius - 15 - dp(13), cy - dp(13))
        
        self._draw_flight()

    def _draw_flight(self):
        w, h = self.width, self.height
        if w < 50 or h < 50: return
        cx, cy = w / 2.0, h / 2.0
        radius = min(w, h) / 2.0 - 30

        if self.flight_lat is not None:
            r = (min(self.dist_to_center, self.max_range) / self.max_range) * radius
            rad = radians(self.bearing)
            px = cx + r * sin(rad)
            py = cy + r * cos(rad)
            self.glow.pos = (px - 9, py - 9)
            self.dot.pos = (px - 4, py - 4)
        else:
            self.glow.pos = (-100, -100)
            self.dot.pos = (-100, -100)

class FlightDetailPopup(ModalView):
    def __init__(self, raw_data, center_lat, center_lon, on_star_change=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.90, 0.86)
        self.background_color = (0, 0, 0, 0.38)
        self.icao24 = raw_data[0]
        self.raw_data = raw_data
        self.on_star_change = on_star_change

        root = GlassCard(bg_color=C_GLASS, radius=20,
                         orientation="vertical", padding=[0, 0])
        self.add_widget(root)

        callsign = (raw_data[1] or "").strip() or "未知"
        self.callsign = callsign
        prefix = callsign[:3].upper()
        _, iata_code = get_airline_info(callsign)
        self.is_starred = get_store().is_starred(callsign)
        
        display_callsign = callsign
        if iata_code != prefix and len(callsign) > 3:
            display_callsign = iata_code + callsign[3:]

        top = BoxLayout(size_hint_y=None, height=dp(88),
                        padding=[SP_L, SP_M], spacing=SP_M)
        self.logo_box = BoxLayout(size_hint=(None, None), size=(dp(56), dp(56)))
        self._draw_fallback_logo()
        top.add_widget(self.logo_box)

        info = BoxLayout(orientation="vertical", spacing=dp(1))
        title = Label(text=f"{display_callsign} (V3)", color=C_TEXT_MAIN, font_size="20sp",
                      bold=True, halign="left", valign="middle")
        title.bind(size=title.setter("text_size"))
        info.add_widget(title)
        self.aircraft_lbl = Label(text="机型: 正在查询…", color=C_TEXT_SUB,
                                  font_size="12sp", halign="left")
        self.aircraft_lbl.bind(size=self.aircraft_lbl.setter("text_size"))
        info.add_widget(self.aircraft_lbl)
        self.reg_lbl = Label(text="注册号: 正在查询…", color=C_TEXT_SUB,
                             font_size="12sp", halign="left")
        self.reg_lbl.bind(size=self.reg_lbl.setter("text_size"))
        info.add_widget(self.reg_lbl)
        top.add_widget(info)
        root.add_widget(top)

        data_layout = GridLayout(cols=2, size_hint_y=None, height=dp(92),
                                 padding=[SP_L, SP_S], spacing=SP_S)
        alt = raw_data[7] if raw_data[7] else 0
        spd = raw_data[9] if raw_data[9] else 0
        lat, lon = raw_data[6], raw_data[5]

        for k, v in [("气压高度", f"{alt:.0f} m"), ("地速", f"{spd:.0f} m/s"),
                     ("纬度", f"{lat:.4f}"), ("经度", f"{lon:.4f}")]:
            row = BoxLayout()
            row.add_widget(Label(text=k, color=C_TEXT_SUB, size_hint_x=0.4, halign='left'))
            row.add_widget(Label(text=v, color=C_TEXT_MAIN, bold=True,
                                 size_hint_x=0.6, halign='left'))
            data_layout.add_widget(row)
        root.add_widget(data_layout)

        radar_container = BoxLayout(padding=[SP_L, SP_XS, SP_L, SP_L])
        self.radar_view = TacticalRadarView(size_hint=(1, 1))
        self.radar_view.center_lat = center_lat
        self.radar_view.center_lon = center_lon
        heading = raw_data[10] if len(raw_data) > 10 else 0
        self.radar_view.update_position(lat, lon, heading, spd)
        radar_container.add_widget(self.radar_view)
        root.add_widget(radar_container)

        btn_box = BoxLayout(size_hint_y=None, height=dp(60),
                            padding=[SP_L, 0, SP_L, SP_L], spacing=SP_M)
        
        close_btn = Button(text="关闭 V3", background_normal="",
                           background_color=C_DIVIDER,
                           color=C_TEXT_MAIN, bold=True)
        close_btn.bind(on_press=self.dismiss)
        btn_box.add_widget(close_btn)

        self.star_btn = Button(
            text="已关注" if self.is_starred else "+ 关注此航班",
            background_normal="",
            background_color=C_GOLD if self.is_starred else C_PRIMARY,
            color=(1, 1, 1, 1), bold=True, font_size="15sp")
        self.star_btn.bind(on_press=self._toggle_star)
        btn_box.add_widget(self.star_btn)

        root.add_widget(btn_box)

        threading.Thread(target=self._fetch_details,
                         args=(callsign, iata_code), daemon=True).start()

    def dismiss(self, *args):
        if hasattr(self.radar_view, '_ev') and self.radar_view._ev:
            self.radar_view._ev.cancel()
        self.clear_widgets()
        super().dismiss()
        if self.on_star_change:
            Clock.schedule_once(lambda dt: self.on_star_change(self.callsign), 0.1)

    def _toggle_star(self, *a):
        info = {"lat": 0, "lon": 0, "alt": 0, "spd": 0, "ts": time.time()}
        now = get_store().toggle_star(self.callsign, info)
        self.is_starred = now
        self.star_btn.text = "已关注" if now else "+ 关注此航班"
        self.star_btn.background_color = C_GOLD if now else C_PRIMARY

    def _draw_fallback_logo(self):
        self.logo_box.canvas.before.clear()
        with self.logo_box.canvas.before:
            Color(*C_PRIMARY)
            self.logo_rect = RoundedRectangle(pos=self.logo_box.pos,
                                              size=self.logo_box.size,
                                              radius=[dp(10)])
        text = self.callsign[:2] if self.callsign else "AC"
        lbl = Label(text=text, color=(1, 1, 1, 1), font_size='20sp', bold=True)
        self.logo_box.clear_widgets()
        self.logo_box.add_widget(lbl)

    def _fetch_details(self, callsign, iata_code):
        if not self.icao24 or self.icao24 == "fake" or len(self.icao24) != 6:
            Clock.schedule_once(lambda dt: self._update_info("机型: 暂无数据",
                                                             "注册号: 暂无数据"), 0)
            return
        try:
            resp = requests.get(f"https://hexdb.io/api/v1/aircraft/{self.icao24}", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                tc = data.get("ICAOTypeCode") or data.get("typecode") or data.get("TypeCode") or "未知"
                reg = data.get("Registration") or data.get("registration") or data.get("Reg") or "未知"
                Clock.schedule_once(lambda dt: self._update_info(f"机型: {tc}",
                                                                 f"注册号: {reg}"), 0)
            elif resp.status_code == 404:
                Clock.schedule_once(lambda dt: self._update_info("机型: 未收录",
                                                                 "注册号: 未收录"), 0)
            else:
                Clock.schedule_once(lambda dt: self._update_info("机型: 暂无",
                                                                 "注册号: 暂无"), 0)
        except requests.exceptions.Timeout:
            Clock.schedule_once(lambda dt: self._update_info("机型: 查询超时",
                                                             "注册号: 查询超时"), 0)
        except Exception:
            Clock.schedule_once(lambda dt: self._update_info("机型: 查询失败",
                                                             "注册号: 查询失败"), 0)

        if not iata_code or iata_code == callsign[:3]:
            return
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "image/png,image/*"}
        for url in [f"https://content.airhex.com/content/logos/airlines_{iata_code}_200_200_s.png",
                    f"https://pics.avs.io/200/200/{iata_code}.png",
                    f"https://pics.avs.io/200/200/{iata_code}@2x.png"]:
            try:
                r = requests.get(url, headers=headers, timeout=6)
                if r.status_code != 200 or len(r.content) < 500:
                    continue
                ctype = r.headers.get("Content-Type", "").lower()
                if "jpeg" in ctype or "jpg" in ctype or r.content[:2] == b'\xff\xd8':
                    ext = 'jpg'
                elif "webp" in ctype or r.content[:4] == b'RIFF':
                    ext = 'webp'
                else:
                    ext = 'png'
                Clock.schedule_once(lambda dt, c=r.content, e=ext: self._set_logo(c, e), 0)
                return
            except Exception:
                continue

    def _update_info(self, t, r):
        self.aircraft_lbl.text = t
        self.reg_lbl.text = r

    def _set_logo(self, data, ext='png'):
        try:
            tex = CoreImage(io.BytesIO(data), ext=ext).texture
            self.logo_box.clear_widgets()
            self.logo_box.add_widget(KivyImage(texture=tex, size_hint=(1, 1)))
        except Exception:
            pass

class RadarView(RelativeLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.points = []
        self.scan_angle = 0
        
        with self.canvas.before:
            Color(*C_RADAR_BG)
            self.bg_rect = RoundedRectangle(radius=[16])
            Color(*C_RADAR_GRID)
            self.line_out = Line(width=1.2)
            self.line_in = Line(width=1.2)
            self.line_h = Line(width=1.0)
            self.line_v = Line(width=1.0)
            
        with self.canvas:
            Color(0.2, 0.9, 0.4, 0.6)
            self.scan_line = Line(width=2.5)
            
            self.points_group = InstructionGroup()
            self.canvas.add(self.points_group)

        self.labels = {}
        for t in ["N", "S", "W", "E"]:
            lbl = Label(text=t, color=C_RADAR_GRID, bold=True,
                        font_size='11sp', size_hint=(None, None),
                        size=(dp(26), dp(26)), halign='center', valign='middle')
            lbl.text_size = lbl.size
            self.labels[t] = lbl
            self.add_widget(lbl)

        self.bind(pos=self._layout, size=self._layout)
        self._ev = Clock.schedule_interval(self._update_anim, 0.05)

    def _update_anim(self, dt):
        self.scan_angle = (self.scan_angle + 6) % 360
        w, h = self.width, self.height
        if w < 50 or h < 50: return
        cx, cy = w / 2.0, h / 2.0
        r = min(w, h) / 2 - 30
        
        rad = radians(self.scan_angle)
        self.scan_line.points = [cx, cy, cx + r * sin(rad), cy + r * cos(rad)]

    def add_point(self, a, d):
        self.points.append((a, d))
        if len(self.points) > 60:
            self.points.pop(0)
        self._draw_points()

    def _layout(self, *args):
        w, h = self.width, self.height
        if w < 50 or h < 50: return
        self.bg_rect.pos = (0, 0)
        self.bg_rect.size = (w, h)
        
        cx, cy = w / 2.0, h / 2.0
        r = min(w, h) / 2 - 30

        self.line_out.circle = (cx, cy, r)
        self.line_in.circle = (cx, cy, r * 0.5)
        self.line_h.points = [cx - r, cy, cx + r, cy]
        self.line_v.points = [cx, cy - r, cx, cy + r]

        self.labels["N"].pos = (cx - dp(13), cy + r - 15 - dp(13))
        self.labels["S"].pos = (cx - dp(13), cy - r + 15 - dp(13))
        self.labels["W"].pos = (cx - r + 15 - dp(13), cy - dp(13))
        self.labels["E"].pos = (cx + r - 15 - dp(13), cy - dp(13))
        
        self._draw_points()

    def _draw_points(self):
        self.points_group.clear()
        w, h = self.width, self.height
        if w < 50 or h < 50: return
        cx, cy = w / 2.0, h / 2.0
        r = min(w, h) / 2 - 30

        for a, d in self.points:
            pr = min(d / 200, 1.0) * r
            rad = radians(a)
            px = cx + pr * sin(rad)
            py = cy + pr * cos(rad)
            self.points_group.add(Color(*C_RADAR_POINT))
            self.points_group.add(Ellipse(pos=(px - 4, py - 4), size=(8, 8)))

    def on_parent(self, widget, parent):
        if parent is None:
            if hasattr(self, '_ev') and self._ev:
                self._ev.cancel()

class PermissionPopup(ModalView):
    def __init__(self, on_done, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.9, 0.65)
        self.background_color = (0, 0, 0, 0.55)
        self.on_done = on_done

        card = GlassCard(bg_color=C_GLASS, radius=20, orientation="vertical",
                         padding=[SP_XL, SP_XL], spacing=SP_L)
        self.add_widget(card)

        card.add_widget(Label(text="权限申请", color=C_TEXT_MAIN,
                              font_size="24sp", bold=True,
                              size_hint_y=None, height=dp(40)))
        
        msg_lbl = Label(
            text="为了给你精准的航班雷达体验，\n需要获取以下权限：\n\n"
                 "· GPS 位置（查询附近航班）\n"
                 "· 本地存储（保存星座与缓存）\n\n"
                 "数据仅保存在你的设备本地。",
            color=C_TEXT_SUB, font_size="16sp",
            halign="center", valign="middle")
        msg_lbl.bind(size=msg_lbl.setter('text_size'))
        card.add_widget(msg_lbl)

        btn = Button(text="同意并继续", background_normal="",
                     background_color=C_PRIMARY, color=(1, 1, 1, 1),
                     bold=True, size_hint_y=None, height=dp(50),
                     font_size="18sp")
        btn.bind(on_press=self._agree)
        card.add_widget(btn)

        btn2 = Button(text="暂不授权", background_normal="",
                      background_color=(0, 0, 0, 0), color=C_TEXT_SUB,
                      size_hint_y=None, height=dp(40),
                      font_size="16sp")
        btn2.bind(on_press=self._deny)
        card.add_widget(btn2)

    def _agree(self, *a):
        self.dismiss()
        from services import PermissionManager
        PermissionManager.request_all(self.on_done)

    def _deny(self, *a):
        self.dismiss()
        self.on_done(False)
