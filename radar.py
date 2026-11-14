import json
import time
import socket
import random
import threading
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
import config


def parse_radar_message(text):
    """兼容 JSON / CSV / key=value 三种格式，返回 (angle, dist) 或 None"""
    if not text:
        return None
    text = text.strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            a = (data.get(config.RADAR_ANGLE_FIELD) or data.get("angle")
                 or data.get("angle_deg"))
            d = (data.get(config.RADAR_DIST_FIELD) or data.get("distance")
                 or data.get("dist") or data.get("distance_cm"))
            if a is not None and d is not None:
                return float(a), float(d)
    except Exception:
        pass
    try:
        if "," in text:
            parts = text.replace(" ", "").split(",")
            if len(parts) >= 2:
                return float(parts[0]), float(parts[1])
        if "=" in text:
            kv = dict(p.split("=") for p in text.replace(" ", "").split(",") if "=" in p)
            a = kv.get("angle") or kv.get("angle_deg")
            d = kv.get("distance") or kv.get("dist") or kv.get("distance_cm")
            if a and d:
                return float(a), float(d)
    except Exception:
        pass
    return None


class RadarSource:
    """统一入口：start() / stop()。按 config.RADAR_SOURCE 选择协议。"""
    def __init__(self, on_data, on_status):
        self.on_data = on_data
        self.on_status = on_status
        self._running = False
        self._thread = None
        self._sock = None
        self._server = None

    def start(self):
        if self._running:
            return
        self._running = True
        targets = {
            "tcp_client": self._tcp_client_loop,
            "tcp_server": self._tcp_server_loop,
            "udp":        self._udp_loop,
            "http_poll":  self._http_poll_loop,
            "http_post":  self._http_post_loop,
            "bemfa":      self._bemfa_loop,
            "simulate":   self._simulate_loop,
        }
        target = targets.get(config.RADAR_SOURCE)
        if not target:
            self.on_status(f"未知雷达模式: {config.RADAR_SOURCE}")
            self._running = False
            return
        self._thread = threading.Thread(target=target, daemon=True)
        self._thread.start()
        self.on_status(f"雷达已启动 ({config.RADAR_SOURCE})")

    def stop(self):
        self._running = False
        try:
            if self._sock:
                self._sock.close()
        except Exception:
            pass
        try:
            if self._server:
                self._server.shutdown()
        except Exception:
            pass
        self.on_status("雷达已断开")

    # ---------- 模式 1：TCP 客户端（雷达当服务端）----------
    def _tcp_client_loop(self):
        while self._running:
            try:
                self.on_status(f"连接 {config.TCP_RADAR_IP}:{config.TCP_RADAR_PORT}…")
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                s.connect((config.TCP_RADAR_IP, config.TCP_RADAR_PORT))
                s.settimeout(1)
                self._sock = s
                self.on_status("雷达已连接")
                buf = b""
                while self._running:
                    try:
                        chunk = s.recv(1024)
                        if not chunk:
                            break
                        buf += chunk
                        while b"\n" in buf:
                            line, buf = buf.split(b"\n", 1)
                            parsed = parse_radar_message(line.decode("utf-8", "ignore"))
                            if parsed:
                                self.on_data(*parsed)
                    except socket.timeout:
                        continue
            except Exception as e:
                self.on_status(f"TCP 断开: {e}")
            if self._running:
                time.sleep(3)

    # ---------- 模式 2：TCP 服务端（雷达主动连过来）----------
    def _tcp_server_loop(self):
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((config.TCP_LISTEN_IP, config.TCP_RADAR_PORT))
            srv.listen(1)
            srv.settimeout(1)
            self._sock = srv
            self.on_status(f"等待雷达连接 :{config.TCP_RADAR_PORT}")
            while self._running:
                try:
                    conn, addr = srv.accept()
                except socket.timeout:
                    continue
                self.on_status(f"雷达 {addr[0]} 已连接")
                conn.settimeout(1)
                buf = b""
                while self._running:
                    try:
                        chunk = conn.recv(1024)
                        if not chunk:
                            break
                        buf += chunk
                        while b"\n" in buf:
                            line, buf = buf.split(b"\n", 1)
                            parsed = parse_radar_message(line.decode("utf-8", "ignore"))
                            if parsed:
                                self.on_data(*parsed)
                    except socket.timeout:
                        continue
                conn.close()
                self.on_status("雷达连接断开，继续等待")
        except Exception as e:
            self.on_status(f"TCP 服务异常: {e}")

    # ---------- 模式 3：UDP 监听 ----------
    def _udp_loop(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((config.UDP_LISTEN_IP, config.UDP_LISTEN_PORT))
            s.settimeout(1)
            self._sock = s
            self.on_status(f"UDP 监听 :{config.UDP_LISTEN_PORT}")
            while self._running:
                try:
                    data, addr = s.recvfrom(1024)
                    parsed = parse_radar_message(data.decode("utf-8", "ignore"))
                    if parsed:
                        self.on_data(*parsed)
                except socket.timeout:
                    continue
        except Exception as e:
            self.on_status(f"UDP 异常: {e}")

    # ---------- 模式 4：HTTP 轮询 ----------
    def _http_poll_loop(self):
        self.on_status("HTTP 轮询启动")
        while self._running:
            try:
                resp = requests.get(config.HTTP_RADAR_URL, timeout=3)
                if resp.status_code == 200:
                    parsed = parse_radar_message(resp.text)
                    if parsed:
                        self.on_data(*parsed)
            except Exception:
                pass
            time.sleep(config.HTTP_POLL_INTERVAL)

    # ---------- 模式 5：HTTP POST 接收 ----------
    def _http_post_loop(self):
        on_data = self.on_data

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(length).decode("utf-8", "ignore")
                    parsed = parse_radar_message(body)
                    if parsed:
                        on_data(*parsed)
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"ok")
                except Exception:
                    self.send_response(400)
                    self.end_headers()

            def log_message(self, *args):
                pass

        try:
            self._server = HTTPServer(
                (config.HTTP_POST_LISTEN_IP, config.HTTP_POST_LISTEN_PORT),
                Handler)
            self.on_status(f"HTTP 接收 :{config.HTTP_POST_LISTEN_PORT}")
            self._server.serve_forever()
        except Exception as e:
            self.on_status(f"HTTP 服务异常: {e}")

    # ---------- 模式 6：巴法云 ----------
    def _bemfa_loop(self):
        self.on_status("巴法云轮询启动")
        while self._running:
            try:
                resp = requests.get(
                    "https://apis.bemfa.com/va/getmsg",
                    params={"uid": config.MQTT_UID,
                            "topic": config.MQTT_TOPIC,
                            "type": 1, "num": 1},
                    timeout=3)
                data = resp.json()
                if data.get("code", data.get("status")) == 0 and data.get("data"):
                    raw = data["data"]
                    msg_str = raw.get("msg") if isinstance(raw, dict) else (
                        raw[-1].get("msg") if isinstance(raw, list) and raw else None)
                    if msg_str:
                        parsed = parse_radar_message(msg_str)
                        if parsed:
                            self.on_data(*parsed)
            except Exception:
                pass
            time.sleep(1)

    # ---------- 模式 7：模拟 ----------
    def _simulate_loop(self):
        self.on_status("模拟雷达运行中")
        angle = 0
        while self._running:
            angle = (angle + 15) % 360
            dist = random.randint(30, 180)
            self.on_data(angle, dist)
            time.sleep(0.5)