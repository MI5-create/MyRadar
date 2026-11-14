from kivy.metrics import dp

# =================== 网络与数据源 ===================
MQTT_UID = "3fb220237d11846c8112d3eae4b7e72d"
MQTT_TOPIC = "radar001"
FALLBACK_LAT = 33.22
FALLBACK_LON = 107.54
RADIUS_KM = 650
REFRESH_INTERVAL = 60
OPENSKY_CLIENT_ID = ""
OPENSKY_CLIENT_SECRET = ""

# =================== WiFi 雷达 ===================
RADAR_SOURCE = "udp"     # tcp_client / tcp_server / udp / http_poll / http_post / bemfa / simulate
RADAR_ANGLE_FIELD = "angle_deg"
RADAR_DIST_FIELD = "distance_cm"

TCP_RADAR_IP = "192.168.1.100"
TCP_RADAR_PORT = 8888
TCP_LISTEN_IP = "0.0.0.0"
UDP_LISTEN_IP = "0.0.0.0"
UDP_LISTEN_PORT = 8888
HTTP_RADAR_URL = "http://192.168.1.100/radar"
HTTP_POLL_INTERVAL = 1.0
HTTP_POST_LISTEN_IP = "0.0.0.0"
HTTP_POST_LISTEN_PORT = 8889

# =================== 配色 ===================
C_BG           = (0.96, 0.97, 0.98, 1)
C_GLASS        = (1.00, 1.00, 1.00, 0.96)
C_TEXT_MAIN    = (0.10, 0.13, 0.18, 1)
C_TEXT_SUB     = (0.42, 0.47, 0.54, 1)
C_PRIMARY      = (0.17, 0.33, 0.64, 1)
C_PRIMARY_DARK = (0.12, 0.24, 0.48, 1)
C_PRIMARY_SOFT = (0.17, 0.33, 0.64, 0.10)
C_TAG_RED      = (0.88, 0.26, 0.28, 1)
C_GOLD         = (0.85, 0.65, 0.18, 1)
C_ACTIVE       = (0.13, 0.65, 0.44, 1)
C_DIVIDER      = (0.86, 0.88, 0.91, 1)
C_RADAR_BG     = (0.07, 0.10, 0.15, 1)
C_RADAR_GRID   = (0.20, 0.55, 0.45, 0.45)
C_RADAR_POINT  = (1.00, 0.32, 0.32, 1)
C_RADAR_GLOW   = (1.00, 0.32, 0.32, 0.18)

SP_XS = dp(4)
SP_S  = dp(8)
SP_M  = dp(12)
SP_L  = dp(16)
SP_XL = dp(24)

# =================== 217个航司字典 ===================
AIRLINES_ICAO_TO_IATA = {
    # 中国大陆及港澳台
    "CCA": ("中国国航", "CA"), "CSN": ("南方航空", "CZ"), "CES": ("东方航空", "MU"),
    "CHH": ("海南航空", "HU"), "CSZ": ("深圳航空", "ZH"), "CQH": ("春秋航空", "9C"),
    "CKE": ("吉祥航空", "HO"), "CSC": ("四川航空", "3U"), "CXA": ("厦门航空", "MF"),
    "CDG": ("山东航空", "SC"), "CSH": ("上海航空", "FM"), "CHB": ("西部航空", "PN"),
    "CQN": ("重庆航空", "OQ"), "CJX": ("江西航空", "RY"), "CDC": ("长龙航空", "GJ"),
    "CQG": ("华夏航空", "G5"), "CUA": ("联航", "KN"), "CPA": ("国泰航空", "CX"),
    "HAD": ("香港航空", "HX"), "EVA": ("长荣航空", "BR"), "CAL": ("中华航空", "CI"),
    "JNA": ("真航空", "LJ"), "KAL": ("大韩航空", "KE"), "AAR": ("韩亚航空", "OZ"),
    "ANA": ("全日空", "NH"), "JAL": ("日本航空", "JL"), "SIA": ("新加坡航空", "SQ"),
    "THA": ("泰国航空", "TG"), "UAE": ("阿联酋航空", "EK"), "CSZ": ("深圳航空", "ZH"),
    "CBJ": ("北京航空", "CA"), "CCD": ("大连航空", "CA"), "CCJ": ("中航货运", "CA"),
    "CDI": ("国航内蒙", "CA"), "CFA": ("中国飞龙", "CA"), "CKK": ("中国货运", "CK"),
    "CGH": ("桂林航空", "GT"), "CGZ": ("多彩贵州", "GY"), "CHJ": ("河北航空", "NS"),
    "CJR": ("金鹏航空", "Y8"), "CJX": ("江西航空", "RY"), "CKC": ("昆明航空", "KY"),
    "CQH": ("春秋航空", "9C"), "CSJ": ("长安航空", "9H"), "CSN": ("南方航空", "CZ"),
    "CSZ": ("深圳航空", "ZH"), "CTJ": ("天津航空", "GS"), "CUA": ("中国联航", "KN"),
    "CXN": ("乌鲁木齐航空", "UQ"), "CYN": ("湖南航空", "A6"), "CYZ": ("圆通航空", "YG"),
    "CZH": ("东海航空", "DZ"), "DAP": ("九元航空", "AQ"), "DKH": ("吉祥航空", "HO"),
    "ESR": ("顺丰航空", "O3"), "GDC": ("北部湾航空", "GX"), "HXA": ("华夏航空", "G5"),
    "JYH": ("奥凯航空", "BK"), "LKE": ("祥鹏航空", "8L"), "OKA": ("奥凯航空", "BK"),
    "RLH": ("瑞丽航空", "DR"), "SFJ": ("顺丰航空", "O3"), "TBA": ("西藏航空", "TV"),
    "UEA": ("成都航空", "EU"), "XAX": ("星宇航空", "JX"), "XMN": ("厦门航空", "MF"),
    "HVN": ("越捷航空", "VJ"), "MAS": ("马来西亚", "MH"), "AXM": ("亚洲航空", "AK"),
    "PAL": ("菲律宾航空", "PR"), "CEB": ("宿务太平洋", "5J"), "GIA": ("印尼鹰航", "GA"),
    "CPA": ("国泰航空", "CX"), "HDA": ("香港快运", "UO"), "AMU": ("澳门航空", "NX"),
    "CRK": ("香港航空", "HX"), "TTW": ("台湾虎航", "IT"), "UIA": ("立荣航空", "B7"),
    "FEA": ("远东航空", "FE"), "MDA": ("华信航空", "AE"), "SJX": ("星宇航空", "JX"),
    
    # 亚洲其他
    "JJP": ("捷星日本", "GK"), "APJ": ("乐桃航空", "MM"), "SKY": ("天马航空", "BC"),
    "SDA": ("春秋航空日本", "IJ"), "TGW": ("酷航", "TR"), "SLK": ("胜安航空", "MI"),
    "THA": ("泰国国际", "TG"), "TLM": ("泰狮航空", "SL"), "NOK": ("皇雀航空", "DD"),
    "AIQ": ("泰亚航空", "FD"), "HVN": ("越南航空", "VN"), "VJC": ("越捷航空", "VJ"),
    "PIC": ("太平洋航空", "BL"), "JSA": ("捷星亚洲", "3K"), "MKR": ("印尼狮航", "JT"),
    "BTK": ("巴泽航空", "ID"), "AWQ": ("印尼亚洲", "QZ"), "SIA": ("新加坡航空", "SQ"),
    "SLK": ("胜安航空", "MI"), "MXD": ("马印航空", "OD"), "RBA": ("文莱皇家", "BI"),
    "IGO": ("靛蓝航空", "6E"), "SEJ": ("香料航空", "SG"), "AIC": ("印度航空", "AI"),
    "VTI": ("维斯塔拉", "UK"), "PIA": ("巴基斯坦", "PK"), "SVA": ("沙特航空", "SV"),
    "ETD": ("阿提哈德", "EY"), "QTR": ("卡塔尔航空", "QR"), "ELY": ("以色列航空", "LY"),
    "KAC": ("科威特航空", "KU"), "OMA": ("阿曼航空", "WY"), "RJA": ("皇家约旦", "RJ"),
    "MEA": ("中东航空", "ME"), "THY": ("土耳其航空", "TK"), "PGT": ("飞马航空", "PC"),

    # 欧洲
    "DLH": ("汉莎航空", "LH"), "AFR": ("法国航空", "AF"), "KLM": ("荷兰皇家", "KL"),
    "BAW": ("英国航空", "BA"), "VIR": ("维珍航空", "VS"), "SWR": ("瑞士航空", "LX"),
    "AUA": ("奥地利航空", "OS"), "SAS": ("北欧航空", "SK"), "FIN": ("芬兰航空", "AY"),
    "LOT": ("波兰航空", "LO"), "CSA": ("捷克航空", "OK"), "AFL": ("俄罗斯航空", "SU"),
    "UIA": ("乌克兰国际", "PS"), "ITY": ("意大利航空", "AZ"), "IBE": ("伊比利亚", "IB"),
    "VLG": ("伏林航空", "VY"), "AEA": ("欧罗巴航空", "UX"), "TAP": ("葡萄牙航空", "TP"),
    "AEE": ("爱琴海航空", "A3"), "RYR": ("瑞安航空", "FR"), "EZY": ("易捷航空", "U2"),
    "WZZ": ("维兹航空", "W6"), "NAX": ("挪威航空", "DY"), "ICE": ("冰岛航空", "FI"),
    "BEL": ("布鲁塞尔", "SN"), "AAL": ("爱尔兰航空", "EI"), "LGL": ("卢森堡", "LG"),
    "ALK": ("斯里兰卡", "UL"), "AZU": ("蓝色巴西", "AD"),

    # 美洲
    "DAL": ("达美航空", "DL"), "UAL": ("美联航", "UA"), "AAL": ("美国航空", "AA"),
    "SWA": ("西南航空", "WN"), "JBU": ("捷蓝航空", "B6"), "ASA": ("阿拉斯加", "AS"),
    "HAL": ("夏威夷航空", "HA"), "NKS": ("精神航空", "NK"), "FFT": ("边疆航空", "F9"),
    "ACA": ("加拿大航空", "AC"), "WJA": ("西捷航空", "WS"), "AMX": ("墨西哥航空", "AM"),
    "VOI": ("沃拉里斯", "Y4"), "LAN": ("智利航空", "LA"), "ARG": ("阿根廷航空", "AR"),
    "GLO": ("高尔航空", "G3"), "TAM": ("巴西天马", "JJ"), "AVA": ("哥伦比亚航空", "AV"),
    "CMP": ("巴拿马航空", "CM"),

    # 大洋洲与非洲
    "QFA": ("澳洲航空", "QF"), "VOZ": ("维珍澳洲", "VA"), "JST": ("捷星航空", "JQ"),
    "ANZ": ("新西兰航空", "NZ"), "SAA": ("南非航空", "SA"), "ETH": ("埃塞俄比亚", "ET"),
    "MSR": ("埃及航空", "MS"), "RAM": ("皇家摩洛哥", "AT"), "KQA": ("肯尼亚航空", "KQ"),
    "MAU": ("毛里求斯", "MK")
}

def get_airline_info(callsign):
    prefix = callsign[:3].upper()
    return AIRLINES_ICAO_TO_IATA.get(prefix, (prefix, prefix))