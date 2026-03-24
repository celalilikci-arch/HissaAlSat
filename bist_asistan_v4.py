import streamlit as st
import pandas as pd
import math
from datetime import datetime

# --- BIST FİYAT ADIMI (TICK SIZE) MOTORU ---
def get_tick_size(price, direction="down"):
    p = price - 0.001 if direction == "down" else price + 0.001
    if p < 20: return 0.01
    elif p < 50: return 0.02
    elif p < 100: return 0.05
    elif p < 250: return 0.10
    elif p < 500: return 0.25
    elif p < 1000: return 0.50
    elif p < 2500: return 1.00
    else: return 2.50

def shift_price(price, ticks, direction="down"):
    new_price = float(price)
    for _ in range(int(ticks)):
        step = get_tick_size(new_price, direction)
        if direction == "down":
            new_price -= step
        else:
            new_price += step
        new_price = round(new_price, 2)
    return max(new_price, 0.01)

def para_fmt(sayi, ondalik=2):
    """Türkçe para formatı: 1.234,56 (nokta=binlik, virgül=ondalık)"""
    formatted = f"{sayi:,.{ondalik}f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return formatted

# --- SAYFA AYARLARI (MOBİL UYUMLU) ---
st.set_page_config(
    page_title="BIST Asistan",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stButton > button { width: 100%; padding: 0.6rem; font-size: 1rem; }
    .stNumberInput input, .stSelectbox select { font-size: 1rem !important; min-height: 44px; }
    h1 { font-size: 1.4rem !important; }
    h2 { font-size: 1.2rem !important; }
    h3 { font-size: 1.1rem !important; }
    .stTable { overflow-x: auto; }
    section[data-testid="stSidebar"] { min-width: 280px; }
    .hisse-info-box {
        background: transparent;
        border-left: 3px solid #4fc3f7;
        border-radius: 0 4px 4px 0;
        padding: 4px 12px;
        margin: 4px 0 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- TAM BIST VERİTABANI (586 Hisse) ---
BIST_HISSELER = {
    "AEFES": {"firma": "ANADOLU EFES BİRACILIK VE MALT SANAYİİ A.Ş.", "sektor": "GIDA"},
    "AKBNK": {"firma": "AKBANK T.A.Ş.", "sektor": "BANKALAR"},
    "ASELS": {"firma": "ASELSAN ELEKTRONİK SANAYİ VE TİCARET A.Ş.", "sektor": "SAVUNMA"},
    "ASTOR": {"firma": "ASTOR ENERJİ A.Ş.", "sektor": "METAL EŞYA"},
    "BIMAS": {"firma": "BİM BİRLEŞİK MAĞAZALAR A.Ş.", "sektor": "PERAKENDE TİCARET"},
    "DSTKF": {"firma": "DESTEK FİNANS FAKTORİNG A.Ş.", "sektor": "FİNANSAL KİRALAMA"},
    "EKGYO": {"firma": "EMLAK KONUT GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "ENKAI": {"firma": "ENKA İNŞAAT VE SANAYİ A.Ş.", "sektor": "İNŞAAT"},
    "EREGL": {"firma": "EREĞLİ DEMİR VE ÇELİK FABRİKALARI T.A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "FROTO": {"firma": "FORD OTOMOTİV SANAYİ A.Ş.", "sektor": "OTOMOTİV"},
    "GARAN": {"firma": "TÜRKİYE GARANTİ BANKASI A.Ş.", "sektor": "BANKALAR"},
    "GUBRF": {"firma": "GÜBRE FABRİKALARI T.A.Ş.", "sektor": "GÜBRE"},
    "ISCTR": {"firma": "TÜRKİYE İŞ BANKASI A.Ş.", "sektor": "BANKALAR"},
    "KCHOL": {"firma": "KOÇ HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "KRDMD": {"firma": "KARDEMİR KARABÜK DEMİR ÇELİK SANAYİ VE TİCARET A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "MGROS": {"firma": "MİGROS TİCARET A.Ş.", "sektor": "PERAKENDE TİCARET"},
    "PETKM": {"firma": "PETKİM PETROKİMYA HOLDİNG A.Ş.", "sektor": "PETROL"},
    "PGSUS": {"firma": "PEGASUS HAVA TAŞIMACILIĞI A.Ş.", "sektor": "HAVACILIK"},
    "SAHOL": {"firma": "HACI ÖMER SABANCI HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "SASA": {"firma": "SASA POLYESTER SANAYİ A.Ş.", "sektor": "KİMYA"},
    "SISE": {"firma": "TÜRKİYE ŞİŞE VE CAM FABRİKALARI A.Ş.", "sektor": "CAM"},
    "TAVHL": {"firma": "TAV HAVALİMANLARI HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "TCELL": {"firma": "TURKCELL İLETİŞİM HİZMETLERİ A.Ş.", "sektor": "TELEKOMÜNİKASYON"},
    "THYAO": {"firma": "TÜRK HAVA YOLLARI A.O.", "sektor": "HAVACILIK"},
    "TOASO": {"firma": "TOFAŞ TÜRK OTOMOBİL FABRİKASI A.Ş.", "sektor": "OTOMOTİV"},
    "TRALT": {"firma": "TÜRK ALTIN HOLDİNG A.Ş.", "sektor": "MADENCİLİK"},
    "TTKOM": {"firma": "TÜRK TELEKOMÜNİKASYON A.Ş.", "sektor": "TELEKOMÜNİKASYON"},
    "TUPRS": {"firma": "TÜPRAŞ-TÜRKİYE PETROL RAFİNERİLERİ A.Ş.", "sektor": "PETROL"},
    "ULKER": {"firma": "ÜLKER BİSKÜVİ SANAYİ A.Ş.", "sektor": "GIDA"},
    "YKBNK": {"firma": "YAPI VE KREDİ BANKASI A.Ş.", "sektor": "BANKALAR"},
    "ALARK": {"firma": "ALARKO HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "ARCLK": {"firma": "ARÇELİK A.Ş.", "sektor": "METAL EŞYA"},
    "BRSAN": {"firma": "BORUSAN BİRLEŞİK BORU FABRİKALARI SANAYİ VE TİCARET A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "CCOLA": {"firma": "COCA-COLA İÇECEK A.Ş.", "sektor": "GIDA"},
    "CIMSA": {"firma": "ÇİMSA ÇİMENTO SANAYİ VE TİCARET A.Ş.", "sektor": "ÇİMENTO"},
    "DOAS": {"firma": "DOĞUŞ OTOMOTİV SERVİS VE TİCARET A.Ş.", "sektor": "OTOMOTİV"},
    "DOHOL": {"firma": "DOĞAN ŞİRKETLER GRUBU HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "HALKB": {"firma": "TÜRKİYE HALK BANKASI A.Ş.", "sektor": "BANKALAR"},
    "HEKTS": {"firma": "HEKTAŞ TİCARET T.A.Ş.", "sektor": "GÜBRE"},
    "KONTR": {"firma": "KONTROLMATİK TEKNOLOJİ ENERJİ VE MÜHENDİSLİK A.Ş.", "sektor": "TEKNOLOJİ"},
    "TRMET": {"firma": "ANADOLU METAL MADENCİLİK İŞLETMELERİ A.Ş.", "sektor": "MADENCİLİK"},
    "KUYAS": {"firma": "KUYAŞ YATIRIM A.Ş.", "sektor": "MADENCİLİK"},
    "MAVI": {"firma": "MAVİ GİYİM SANAYİ VE TİCARET A.Ş.", "sektor": "PERAKENDE TİCARET"},
    "MIATK": {"firma": "MİA TEKNOLOJİ A.Ş.", "sektor": "TEKNOLOJİ"},
    "OYAKC": {"firma": "OYAK ÇİMENTO FABRİKALARI A.Ş.", "sektor": "ÇİMENTO"},
    "SOKM": {"firma": "ŞOK MARKETLER TİCARET A.Ş.", "sektor": "PERAKENDE TİCARET"},
    "TKFEN": {"firma": "TEKFEN HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "TSKB": {"firma": "TÜRKİYE SINAİ KALKINMA BANKASI A.Ş.", "sektor": "BANKALAR"},
    "VAKBN": {"firma": "TÜRKİYE VAKIFLAR BANKASI T.A.O.", "sektor": "BANKALAR"},
    "VESTL": {"firma": "VESTEL ELEKTRONİK SANAYİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "AGHOL": {"firma": "AG ANADOLU GRUBU HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "AKSA": {"firma": "AKSA AKRİLİK KİMYA SANAYİİ A.Ş.", "sektor": "KİMYA"},
    "AKSEN": {"firma": "AKSA ENERJİ ÜRETİM A.Ş.", "sektor": "ENERJİ"},
    "ALFAS": {"firma": "ALFA SOLAR ENERJİ SANAYİ VE TİCARET A.Ş.", "sektor": "ENERJİ"},
    "ALTNY": {"firma": "ALTINAY SAVUNMA TEKNOLOJİLERİ A.Ş.", "sektor": "SAVUNMA"},
    "ANSGR": {"firma": "ANADOLU ANONİM TÜRK SİGORTA ŞİRKETİ", "sektor": "SİGORTA"},
    "AVPGY": {"firma": "AVRUPAKENT GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "BALSU": {"firma": "BALSU GIDA SANAYİ VE TİCARET A.Ş.", "sektor": "GIDA"},
    "BERA": {"firma": "BERA HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "BINHO": {"firma": "1000 YATIRIMLAR HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "BRYAT": {"firma": "BORUSAN YATIRIM VE PAZARLAMA A.Ş.", "sektor": "HOLDİNGLER"},
    "BSOKE": {"firma": "BATISÖKE SÖKE ÇİMENTO SANAYİİ T.A.Ş.", "sektor": "ÇİMENTO"},
    "BTCIM": {"firma": "BATIÇİM BATI ANADOLU ÇİMENTO SANAYİİ A.Ş.", "sektor": "ÇİMENTO"},
    "CANTE": {"firma": "ÇAN2 TERMİK A.Ş.", "sektor": "ENERJİ"},
    "CLEBI": {"firma": "ÇELEBİ HAVA SERVİSİ A.Ş.", "sektor": "HAVACILIK"},
    "CWENE": {"firma": "CW ENERJİ MÜHENDİSLİK TİCARET VE SANAYİ A.Ş.", "sektor": "ENERJİ"},
    "EFORC": {"firma": "EFOR ÇAY SANAYİ TİCARET A.Ş.", "sektor": "GIDA"},
    "EGEEN": {"firma": "EGE ENDÜSTRİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "ENERY": {"firma": "ENERYA ENERJİ A.Ş.", "sektor": "ENERJİ"},
    "ENJSA": {"firma": "ENERJİSA ENERJİ A.Ş.", "sektor": "ENERJİ"},
    "EUPWR": {"firma": "EUROPOWER ENERJİ VE OTOMASYON TEKNOLOJİLERİ SANAYİ TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "FENER": {"firma": "FENERBAHÇE FUTBOL A.Ş.", "sektor": "SPOR"},
    "GENIL": {"firma": "GEN İLAÇ VE SAĞLIK ÜRÜNLERİ SANAYİ VE TİCARET A.Ş.", "sektor": "İLAÇ"},
    "GESAN": {"firma": "GİRİŞİM ELEKTRİK SANAYİ TAAHHÜT VE TİCARET A.Ş.", "sektor": "İNŞAAT"},
    "GLRMK": {"firma": "GÜLERMAK AĞIR SANAYİ İNŞAAT VE TAAHHÜT A.Ş.", "sektor": "İNŞAAT"},
    "GRSEL": {"firma": "GÜR-SEL TURİZM TAŞIMACILIK VE SERVİS TİCARET A.Ş.", "sektor": "ULAŞTIRMA VE DEPOLAMA"},
    "GRTHO": {"firma": "GRAINTURK HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "GSRAY": {"firma": "GALATASARAY SPORTİF SINAİ VE TİCARİ YATIRIMLAR A.Ş.", "sektor": "SPOR"},
    "IEYHO": {"firma": "IŞIKLAR ENERJİ VE YAPI HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "TRENJ": {"firma": "DOĞAL ENERJİ KAYNAKLARI ARAŞTIRMA VE ÜRETİM A.Ş.", "sektor": "ENERJİ"},
    "ISMEN": {"firma": "İŞ YATIRIM MENKUL DEĞERLER A.Ş.", "sektor": "ARACI KURUMLAR"},
    "KCAER": {"firma": "KOCAER ÇELİK SANAYİ VE TİCARET A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "KTLEV": {"firma": "KATILIMEVİM TASARRUF FİNANSMAN A.Ş.", "sektor": "FİNANSAL KİRALAMA"},
    "LMKDC": {"firma": "LİMAK DOĞU ANADOLU ÇİMENTO SANAYİ VE TİCARET A.Ş.", "sektor": "ÇİMENTO"},
    "MAGEN": {"firma": "MARGÜN ENERJİ ÜRETİM SANAYİ VE TİCARET A.Ş.", "sektor": "ENERJİ"},
    "MPARK": {"firma": "MLP SAĞLIK HİZMETLERİ A.Ş.", "sektor": "SAĞLIK"},
    "OBAMS": {"firma": "OBA MAKARNACILIK SANAYİ VE TİCARET A.Ş.", "sektor": "GIDA"},
    "ODAS": {"firma": "ODAŞ ELEKTRİK ÜRETİM SANAYİ TİCARET A.Ş.", "sektor": "ENERJİ"},
    "OTKAR": {"firma": "OTOKAR OTOMOTİV VE SAVUNMA SANAYİ A.Ş.", "sektor": "OTOMOTİV"},
    "PASEU": {"firma": "PASİFİK EURASİA LOJİSTİK DIŞ TİCARET A.Ş.", "sektor": "ULAŞTIRMA VE DEPOLAMA"},
    "RALYH": {"firma": "RAL YATIRIM HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "REEDR": {"firma": "REEDER TEKNOLOJİ SANAYİ VE TİCARET A.Ş.", "sektor": "TEKNOLOJİ"},
    "SKBNK": {"firma": "ŞEKERBANK T.A.Ş.", "sektor": "BANKALAR"},
    "SMRTG": {"firma": "SMART GÜNEŞ ENERJİSİ TEKNOLOJİLERİ ARAŞTIRMA GELİŞTİRME ÜRETİM SANAYİ VE TİCARET A.Ş.", "sektor": "ENERJİ"},
    "TABGD": {"firma": "TAB GIDA SANAYİ VE TİCARET A.Ş.", "sektor": "YİYECEK VE İÇECEK HİZMETLERİ"},
    "TTRAK": {"firma": "TÜRK TRAKTÖR VE ZİRAAT MAKİNELERİ A.Ş.", "sektor": "OTOMOTİV"},
    "TUREX": {"firma": "TUREKS TURİZM TAŞIMACILIK A.Ş.", "sektor": "ULAŞTIRMA VE DEPOLAMA"},
    "TURSG": {"firma": "TÜRKİYE SİGORTA A.Ş.", "sektor": "SİGORTA"},
    "YEOTK": {"firma": "YEO TEKNOLOJİ ENERJİ VE ENDÜSTRİ A.Ş.", "sektor": "TEKNOLOJİ"},
    "ZOREN": {"firma": "ZORLU ENERJİ ELEKTRİK ÜRETİM A.Ş.", "sektor": "ENERJİ"},
    "XU100": {"firma": "BIST100 ENDEKSİ", "sektor": "ENDEKS"},
    "A1CAP": {"firma": "A1 CAPİTAL YATIRIM MENKUL DEĞERLER A.Ş.", "sektor": "ARACI KURUMLAR"},
    "A1YEN": {"firma": "A1 YENİLENEBİLİR ENERJİ ÜRETİM A.Ş.", "sektor": "ENERJİ"},
    "ACSEL": {"firma": "ACISELSAN ACIPAYAM SELÜLOZ SANAYİ VE TİCARET A.Ş.", "sektor": "KİMYA"},
    "ADEL": {"firma": "ADEL KALEMCİLİK TİCARET VE SANAYİ A.Ş.", "sektor": "KIRTASİYE"},
    "ADESE": {"firma": "ADESE GAYRİMENKUL YATIRIM A.Ş.", "sektor": "GAYRİMENKUL FAALİYETLERİ"},
    "ADGYO": {"firma": "ADRA GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "AFYON": {"firma": "AFYON ÇİMENTO SANAYİ T.A.Ş.", "sektor": "ÇİMENTO"},
    "AGESA": {"firma": "AGESA HAYAT VE EMEKLİLİK A.Ş.", "sektor": "SİGORTA"},
    "AGROT": {"firma": "AGROTECH YÜKSEK TEKNOLOJİ VE YATIRIM A.Ş.", "sektor": "TARIM VE HAYVANCILIK"},
    "AGYO": {"firma": "ATAKULE GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "AHGAZ": {"firma": "AHLATCI DOĞAL GAZ DAĞITIM ENERJİ VE YATIRIM A.Ş.", "sektor": "ENERJİ"},
    "AHSGY": {"firma": "AHES GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "AKCNS": {"firma": "AKÇANSA ÇİMENTO SANAYİ VE TİCARET A.Ş.", "sektor": "ÇİMENTO"},
    "AKENR": {"firma": "AKENERJİ ELEKTRİK ÜRETİM A.Ş.", "sektor": "ENERJİ"},
    "AKFGY": {"firma": "AKFEN GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "AKFIS": {"firma": "AKFEN İNŞAAT TURİZM VE TİCARET A.Ş.", "sektor": "İNŞAAT"},
    "AKFYE": {"firma": "AKFEN YENİLENEBİLİR ENERJİ A.Ş.", "sektor": "ENERJİ"},
    "AKGRT": {"firma": "AKSİGORTA A.Ş.", "sektor": "SİGORTA"},
    "AKMGY": {"firma": "AKMERKEZ GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "AKSGY": {"firma": "AKİŞ GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "AKSUE": {"firma": "AKSU ENERJİ VE TİCARET A.Ş.", "sektor": "ENERJİ"},
    "AKYHO": {"firma": "AKDENİZ YATIRIM HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "ALBRK": {"firma": "ALBARAKA TÜRK KATILIM BANKASI A.Ş.", "sektor": "BANKALAR"},
    "ALCAR": {"firma": "ALARKO CARRIER SANAYİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "ALCTL": {"firma": "ALCATEL LUCENT TELETAŞ TELEKOMÜNİKASYON A.Ş.", "sektor": "TEKNOLOJİ"},
    "ALGYO": {"firma": "ALARKO GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "ALKA": {"firma": "ALKİM KAĞIT SANAYİ VE TİCARET A.Ş.", "sektor": "KAĞIT VE KAĞIT ÜRÜNLERİ"},
    "ALKIM": {"firma": "ALKİM ALKALİ KİMYA A.Ş.", "sektor": "KİMYA"},
    "ALKLC": {"firma": "ALTINKILIÇ GIDA VE SÜT SANAYİ TİCARET A.Ş.", "sektor": "GIDA"},
    "ALVES": {"firma": "ALVES KABLO SANAYİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "ANELE": {"firma": "ANEL ELEKTRİK PROJE TAAHHÜT VE TİCARET A.Ş.", "sektor": "İNŞAAT"},
    "ANGEN": {"firma": "ANATOLİA TANI VE BİYOTEKNOLOJİ ÜRÜNLERİ ARAŞTIRMA GELİŞTİRME SANAYİ VE TİCARET A.Ş.", "sektor": "SAĞLIK"},
    "ANHYT": {"firma": "ANADOLU HAYAT EMEKLİLİK A.Ş.", "sektor": "SİGORTA"},
    "ARASE": {"firma": "DOĞU ARAS ENERJİ YATIRIMLARI A.Ş.", "sektor": "ENERJİ"},
    "ARDYZ": {"firma": "ARD GRUP BİLİŞİM TEKNOLOJİLERİ A.Ş.", "sektor": "BİLİŞİM"},
    "ARENA": {"firma": "ARENA BİLGİSAYAR SANAYİ VE TİCARET A.Ş.", "sektor": "TEKNOLOJİ"},
    "ARMGD": {"firma": "ARMADA GIDA TİCARET SANAYİ A.Ş.", "sektor": "GIDA"},
    "ARSAN": {"firma": "ARSAN TEKSTİL TİCARET VE SANAYİ A.Ş.", "sektor": "TEKSTİL"},
    "ARTMS": {"firma": "ARTEMİS HALI A.Ş.", "sektor": "TEKSTİL"},
    "ARZUM": {"firma": "ARZUM ELEKTRİKLİ EV ALETLERİ SANAYİ VE TİCARET A.Ş.", "sektor": "TOPTAN TİCARET"},
    "ASGYO": {"firma": "ASCE GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "ASUZU": {"firma": "ANADOLU ISUZU OTOMOTİV SANAYİ VE TİCARET A.Ş.", "sektor": "OTOMOTİV"},
    "ATAGY": {"firma": "ATA GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "ATAKP": {"firma": "ATAKEY PATATES GIDA SANAYİ VE TİCARET A.Ş.", "sektor": "GIDA"},
    "ATATP": {"firma": "ATP YAZILIM VE TEKNOLOJİ A.Ş.", "sektor": "BİLİŞİM"},
    "ATEKS": {"firma": "AKIN TEKSTİL A.Ş.", "sektor": "TEKSTİL"},
    "ATLAS": {"firma": "ATLAS MENKUL KIYMETLER YATIRIM ORTAKLIĞI A.Ş.", "sektor": "MENKUL KIYMET YATIRIM ORTAKLIKLARI"},
    "ATSYH": {"firma": "ATLANTİS YATIRIM HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "AVGYO": {"firma": "AVRASYA GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "AVHOL": {"firma": "AVRUPA YATIRIM HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "AVOD": {"firma": "A.V.O.D. KURUTULMUŞ GIDA VE TARIM ÜRÜNLERİ SANAYİ TİCARET A.Ş.", "sektor": "GIDA"},
    "AVTUR": {"firma": "AVRASYA PETROL VE TURİSTİK TESİSLER YATIRIMLAR A.Ş.", "sektor": "KONAKLAMA"},
    "AYCES": {"firma": "ALTIN YUNUS ÇEŞME TURİSTİK TESİSLER A.Ş.", "sektor": "KONAKLAMA"},
    "AYDEM": {"firma": "AYDEM YENİLENEBİLİR ENERJİ A.Ş.", "sektor": "ENERJİ"},
    "AYEN": {"firma": "AYEN ENERJİ A.Ş.", "sektor": "ENERJİ"},
    "AYES": {"firma": "AYES ÇELİK HASIR VE ÇİT SANAYİ A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "AYGAZ": {"firma": "AYGAZ A.Ş.", "sektor": "PETROL"},
    "AZTEK": {"firma": "AZTEK TEKNOLOJİ ÜRÜNLERİ TİCARET A.Ş.", "sektor": "TEKNOLOJİ"},
    "BAGFS": {"firma": "BAGFAŞ BANDIRMA GÜBRE FABRİKALARI A.Ş.", "sektor": "GÜBRE"},
    "BAHKM": {"firma": "BAHADIR KİMYA SANAYİ VE TİCARET A.Ş.", "sektor": "KİMYA"},
    "BAKAB": {"firma": "BAK AMBALAJ SANAYİ VE TİCARET A.Ş.", "sektor": "KAĞIT VE KAĞIT ÜRÜNLERİ"},
    "BALAT": {"firma": "BALATACILAR BALATACILIK SANAYİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "BANVT": {"firma": "BANVİT BANDIRMA VİTAMİNLİ YEM SANAYİ A.Ş.", "sektor": "GIDA"},
    "BARMA": {"firma": "BAREM AMBALAJ SANAYİ VE TİCARET A.Ş.", "sektor": "KAĞIT VE KAĞIT ÜRÜNLERİ"},
    "BASCM": {"firma": "BAŞTAŞ BAŞKENT ÇİMENTO SANAYİ VE TİCARET A.Ş.", "sektor": "ÇİMENTO"},
    "BASGZ": {"firma": "BAŞKENT DOĞALGAZ DAĞITIM GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "BAYRK": {"firma": "BAYRAK EBT TABAN SANAYİ VE TİCARET A.Ş.", "sektor": "KİMYA"},
    "BEGYO": {"firma": "BATI EGE GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "BESLR": {"firma": "BESLER GIDA VE KİMYA SANAYİ VE TİCARET A.Ş.", "sektor": "GIDA"},
    "BEYAZ": {"firma": "BEYAZ FİLO OTO KİRALAMA A.Ş.", "sektor": "FİLO KİRALAMA"},
    "BFREN": {"firma": "BOSCH FREN SİSTEMLERİ SANAYİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "BIENY": {"firma": "BİEN YAPI ÜRÜNLERİ SANAYİ TURİZM VE TİCARET A.Ş.", "sektor": "SERAMİK"},
    "BIGCH": {"firma": "BÜYÜK ŞEFLER GIDA TURİZM TEKSTİL DANIŞMANLIK ORGANİZASYON EĞİTİM SANAYİ VE TİCARET A.Ş.", "sektor": "YİYECEK VE İÇECEK HİZMETLERİ"},
    "BIGEN": {"firma": "BİRLEŞİM GRUP ENERJİ YATIRIMLARI A.Ş.", "sektor": "ENERJİ"},
    "BINBN": {"firma": "BİN ULAŞIM VE AKILLI ŞEHİR TEKNOLOJİLERİ A.Ş.", "sektor": "TEKNOLOJİ"},
    "BIOEN": {"firma": "BİOTREND ÇEVRE VE ENERJİ YATIRIMLARI A.Ş.", "sektor": "ENERJİ"},
    "BIZIM": {"firma": "BİZİM TOPTAN SATIŞ MAĞAZALARI A.Ş.", "sektor": "TOPTAN TİCARET"},
    "BJKAS": {"firma": "BEŞİKTAŞ FUTBOL YATIRIMLARI SANAYİ VE TİCARET A.Ş.", "sektor": "SPOR"},
    "BLCYT": {"firma": "BİLİCİ YATIRIM SANAYİ VE TİCARET A.Ş.", "sektor": "TEKSTİL"},
    "BMSCH": {"firma": "BMS ÇELİK HASIR SANAYİ VE TİCARET A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "BMSTL": {"firma": "BMS BİRLEŞİK METAL SANAYİ VE TİCARET A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "BNTAS": {"firma": "BANTAŞ BANDIRMA AMBALAJ SANAYİ VE TİCARET A.Ş.", "sektor": "KİMYA"},
    "BOBET": {"firma": "BOĞAZİÇİ BETON SANAYİ VE TİCARET A.Ş.", "sektor": "ÇİMENTO"},
    "BORLS": {"firma": "BORLEASE OTOMOTİV A.Ş.", "sektor": "FİLO KİRALAMA"},
    "BORSK": {"firma": "BOR ŞEKER A.Ş.", "sektor": "GIDA"},
    "BOSSA": {"firma": "BOSSA TİCARET VE SANAYİ İŞLETMELERİ T.A.Ş.", "sektor": "TEKSTİL"},
    "BRISA": {"firma": "BRİSA BRİDGESTONE SABANCI LASTİK SANAYİ VE TİCARET A.Ş.", "sektor": "LASTİK"},
    "BRKO": {"firma": "BİRKO BİRLEŞİK KOYUNLULULAR MENSUCAT TİCARET VE SANAYİ A.Ş.", "sektor": "TEKSTİL"},
    "BRKSN": {"firma": "BERKOSAN YALITIM VE TECRİT MADDELERİ ÜRETİM VE TİCARET A.Ş.", "sektor": "KİMYA"},
    "BRKVY": {"firma": "BİRİKİM VARLIK YÖNETİM A.Ş.", "sektor": "VARLIK YÖNETİM"},
    "BRLSM": {"firma": "BİRLEŞİM MÜHENDİSLİK ISITMA SOĞUTMA HAVALANDIRMA SANAYİ VE TİCARET A.Ş.", "sektor": "İNŞAAT"},
    "BRMEN": {"firma": "BİRLİK MENSUCAT TİCARET VE SANAYİ İŞLETMESİ A.Ş.", "sektor": "TEKSTİL"},
    "BUCIM": {"firma": "BURSA ÇİMENTO FABRİKASI A.Ş.", "sektor": "ÇİMENTO"},
    "BULGS": {"firma": "BULLS GİRİŞİM SERMAYESİ YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GİRİŞİM SERMAYESİ YATIRIM ORTAKLIKLARI"},
    "BURCE": {"firma": "BURÇELİK BURSA ÇELİK DÖKÜM SANAYİİ A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "BURVA": {"firma": "BURÇELİK VANA SANAYİ VE TİCARET A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "BVSAN": {"firma": "BÜLBÜLOĞLU VİNÇ SANAYİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "BYDNR": {"firma": "BAYDÖNER RESTORANLARI A.Ş.", "sektor": "YİYECEK VE İÇECEK HİZMETLERİ"},
    "CASA": {"firma": "CASA EMTİA PETROL KİMYEVİ VE TÜREVLERİ SANAYİ VE TİCARET A.Ş.", "sektor": "PETROL"},
    "CATES": {"firma": "ÇATES ELEKTRİK ÜRETİM A.Ş.", "sektor": "ENERJİ"},
    "CELHA": {"firma": "ÇELİK HALAT VE TEL SANAYİİ A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "CEMAS": {"firma": "ÇEMAŞ DÖKÜM SANAYİ A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "CEMTS": {"firma": "ÇEMTAŞ ÇELİK MAKİNA SANAYİ VE TİCARET A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "CEMZY": {"firma": "CEM ZEYTİN A.Ş.", "sektor": "GIDA"},
    "CEOEM": {"firma": "CEO EVENT MEDYA A.Ş.", "sektor": "TOPLANTI HİZMETLERİ"},
    "CGCAM": {"firma": "ÇAĞDAŞ CAM SANAYİ VE TİCARET A.Ş.", "sektor": "CAM"},
    "CMBTN": {"firma": "ÇİMBETON HAZIRBETON VE PREFABRİK YAPI ELEMANLARI SANAYİ VE TİCARET A.Ş.", "sektor": "ÇİMENTO"},
    "CMENT": {"firma": "ÇİMENTAŞ İZMİR ÇİMENTO FABRİKASI T.A.Ş.", "sektor": "ÇİMENTO"},
    "CONSE": {"firma": "CONSUS ENERJİ İŞLETMECİLİĞİ VE HİZMETLERİ A.Ş.", "sektor": "ENERJİ"},
    "COSMO": {"firma": "COSMOS YATIRIM HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "CRDFA": {"firma": "CREDITWEST FAKTORİNG A.Ş.", "sektor": "FİNANSAL KİRALAMA"},
    "CRFSA": {"firma": "CARREFOURSA CARREFOUR SABANCI TİCARET MERKEZİ A.Ş.", "sektor": "PERAKENDE TİCARET"},
    "CUSAN": {"firma": "ÇUHADAROĞLU METAL SANAYİ VE PAZARLAMA A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "CVKMD": {"firma": "CVK MADEN İŞLETMELERİ SANAYİ VE TİCARET A.Ş.", "sektor": "MADENCİLİK"},
    "DAGI": {"firma": "DAGİ GİYİM SANAYİ VE TİCARET A.Ş.", "sektor": "TEKSTİL"},
    "DAPGM": {"firma": "DAP GAYRİMENKUL GELİŞTİRME A.Ş.", "sektor": "İNŞAAT"},
    "DARDL": {"firma": "DARDANEL ÖNENTAŞ GIDA SANAYİ A.Ş.", "sektor": "GIDA"},
    "DCTTR": {"firma": "DCT TRADİNG DIŞ TİCARET A.Ş.", "sektor": "TOPTAN TİCARET"},
    "DENGE": {"firma": "DENGE YATIRIM HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "DERHL": {"firma": "DERLÜKS YATIRIM HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "DERIM": {"firma": "DERİMOD KONFEKSİYON AYAKKABI DERİ SANAYİ VE TİCARET A.Ş.", "sektor": "TEKSTİL"},
    "DESA": {"firma": "DESA DERİ SANAYİ VE TİCARET A.Ş.", "sektor": "TEKSTİL"},
    "DESPC": {"firma": "DESPEC BİLGİSAYAR PAZARLAMA VE TİCARET A.Ş.", "sektor": "TEKNOLOJİ"},
    "DEVA": {"firma": "DEVA HOLDİNG A.Ş.", "sektor": "İLAÇ"},
    "DGATE": {"firma": "DATAGATE BİLGİSAYAR MALZEMELERİ TİCARET A.Ş.", "sektor": "TEKNOLOJİ"},
    "DGGYO": {"firma": "DOĞUŞ GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "DGNMO": {"firma": "DOĞANLAR MOBİLYA GRUBU İMALAT SANAYİ VE TİCARET A.Ş.", "sektor": "MOBİLYA"},
    "DIRIT": {"firma": "DİRİTEKS DİRİLİŞ TEKSTİL SANAYİ VE TİCARET A.Ş.", "sektor": "TEKSTİL"},
    "DITAS": {"firma": "DİTAŞ DOĞAN YEDEK PARÇA İMALAT VE TEKNİK A.Ş.", "sektor": "METAL EŞYA"},
    "DMRGD": {"firma": "DMR UNLU MAMULLER ÜRETİM GIDA TOPTAN PERAKENDE İHRACAT A.Ş.", "sektor": "GIDA"},
    "DMSAS": {"firma": "DEMİSAŞ DÖKÜM EMAYE MAMÜLLERİ SANAYİ A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "DNISI": {"firma": "DİNAMİK ISI MAKİNA YALITIM MALZEMELERİ SANAYİ VE TİCARET A.Ş.", "sektor": "KİMYA"},
    "DOBUR": {"firma": "DOĞAN BURDA DERGİ YAYINCILIK VE PAZARLAMA A.Ş.", "sektor": "MEDYA"},
    "DOCO": {"firma": "DO & CO AKTIENGESELLSCHAFT", "sektor": "YİYECEK VE İÇECEK HİZMETLERİ"},
    "DOFER": {"firma": "DOFER YAPI MALZEMELERİ SANAYİ VE TİCARET A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "DOGUB": {"firma": "DOĞUSAN BORU SANAYİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "DOKTA": {"firma": "DÖKTAŞ DÖKÜMCÜLÜK TİCARET VE SANAYİ A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "DURDO": {"firma": "DURAN DOĞAN BASIM VE AMBALAJ SANAYİ A.Ş.", "sektor": "KAĞIT VE KAĞIT ÜRÜNLERİ"},
    "DURKN": {"firma": "DURUKAN ŞEKERLEME SANAYİ VE TİCARET A.Ş.", "sektor": "GIDA"},
    "DYOBY": {"firma": "DYO BOYA FABRİKALARI SANAYİ VE TİCARET A.Ş.", "sektor": "KİMYA"},
    "DZGYO": {"firma": "DENİZ GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "EBEBK": {"firma": "EBEBEK MAĞAZACILIK A.Ş.", "sektor": "PERAKENDE TİCARET"},
    "ECILC": {"firma": "EİS ECZACIBAŞI İLAÇ SINAİ VE FİNANSAL YATIRIMLAR SANAYİ VE TİCARET A.Ş.", "sektor": "İLAÇ"},
    "ECZYT": {"firma": "ECZACIBAŞI YATIRIM HOLDİNG ORTAKLIĞI A.Ş.", "sektor": "HOLDİNGLER"},
    "EDATA": {"firma": "E-DATA TEKNOLOJİ PAZARLAMA A.Ş.", "sektor": "TEKNOLOJİ"},
    "EDIP": {"firma": "EDİP GAYRİMENKUL YATIRIM SANAYİ VE TİCARET A.Ş.", "sektor": "İNŞAAT"},
    "EGEGY": {"firma": "EGEYAPI AVRUPA GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "EGEPO": {"firma": "NASMED ÖZEL SAĞLIK HİZMETLERİ TİCARET A.Ş.", "sektor": "SAĞLIK"},
    "EGGUB": {"firma": "EGE GÜBRE SANAYİİ A.Ş.", "sektor": "GÜBRE"},
    "EGPRO": {"firma": "EGE PROFİL TİCARET VE SANAYİ A.Ş.", "sektor": "PLASTİK"},
    "EGSER": {"firma": "EGE SERAMİK SANAYİ VE TİCARET A.Ş.", "sektor": "SERAMİK"},
    "EKIZ": {"firma": "EKİZ KİMYA SANAYİ VE TİCARET A.Ş.", "sektor": "KİMYA"},
    "EKOS": {"firma": "EKOS TEKNOLOJİ VE ELEKTRİK A.Ş.", "sektor": "METAL EŞYA"},
    "EKSUN": {"firma": "EKSUN GIDA TARIM SANAYİ VE TİCARET A.Ş.", "sektor": "GIDA"},
    "ELITE": {"firma": "ELİTE NATUREL ORGANİK GIDA SANAYİ VE TİCARET A.Ş.", "sektor": "GIDA"},
    "EMKEL": {"firma": "EMEK ELEKTRİK ENDÜSTRİSİ A.Ş.", "sektor": "METAL EŞYA"},
    "EMNIS": {"firma": "EMİNİŞ AMBALAJ SANAYİ VE TİCARET A.Ş.", "sektor": "PLASTİK"},
    "ENDAE": {"firma": "ENDA ENERJİ HOLDİNG A.Ş.", "sektor": "ENERJİ"},
    "ENSRI": {"firma": "ENSARİ SINAİ YATIRIMLAR A.Ş.", "sektor": "TEKSTİL"},
    "ENTRA": {"firma": "IC ENTERRA YENİLENEBİLİR ENERJİ A.Ş.", "sektor": "ENERJİ"},
    "EPLAS": {"firma": "EGEPLAST EGE PLASTİK TİCARET VE SANAYİ A.Ş.", "sektor": "PLASTİK"},
    "ERBOS": {"firma": "ERBOSAN ERCİYAS BORU SANAYİ VE TİCARET A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "ERCB": {"firma": "ERCİYAS ÇELİK BORU SANAYİ A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "ERSU": {"firma": "ERSU MEYVE VE GIDA SANAYİ A.Ş.", "sektor": "GIDA"},
    "ESCAR": {"firma": "ESCAR FİLO KİRALAMA HİZMETLERİ A.Ş.", "sektor": "FİLO KİRALAMA"},
    "ESCOM": {"firma": "ESCORT TEKNOLOJİ YATIRIM A.Ş.", "sektor": "TEKNOLOJİ"},
    "ESEN": {"firma": "ESENBOĞA ELEKTRİK ÜRETİM A.Ş.", "sektor": "ENERJİ"},
    "ETILR": {"firma": "ETİLER GIDA VE TİCARİ YATIRIMLAR SANAYİ VE TİCARET A.Ş.", "sektor": "GIDA"},
    "ETYAT": {"firma": "EURO TREND YATIRIM ORTAKLIĞI A.Ş.", "sektor": "MENKUL KIYMET YATIRIM ORTAKLIKLARI"},
    "EUHOL": {"firma": "EURO YATIRIM HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "EUKYO": {"firma": "EURO KAPİTAL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "MENKUL KIYMET YATIRIM ORTAKLIKLARI"},
    "EUREN": {"firma": "EUROPEN ENDÜSTRİ İNŞAAT SANAYİ VE TİCARET A.Ş.", "sektor": "PLASTİK"},
    "EUYO": {"firma": "EURO MENKUL KIYMET YATIRIM ORTAKLIĞI A.Ş.", "sektor": "MENKUL KIYMET YATIRIM ORTAKLIKLARI"},
    "EYGYO": {"firma": "EYG GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "FADE": {"firma": "FADE GIDA YATIRIM SANAYİ TİCARET A.Ş.", "sektor": "GIDA"},
    "FLAP": {"firma": "FLAP KONGRE TOPLANTI HİZMETLERİ OTOMOTİV VE TURİZM A.Ş.", "sektor": "TOPLANTI HİZMETLERİ"},
    "FMIZP": {"firma": "FEDERAL MOGUL İZMİT PİSTON VE PİM ÜRETİM TESİSLERİ A.Ş.", "sektor": "METAL EŞYA"},
    "FONET": {"firma": "FONET BİLGİ TEKNOLOJİLERİ A.Ş.", "sektor": "BİLİŞİM"},
    "FORMT": {"firma": "FORMET METAL VE CAM SANAYİ A.Ş.", "sektor": "METAL EŞYA"},
    "FORTE": {"firma": "FORTE BİLGİ İLETİŞİM TEKNOLOJİLERİ VE SAVUNMA SANAYİ A.Ş.", "sektor": "BİLİŞİM"},
    "FRIGO": {"firma": "FRİGO-PAK GIDA MADDELERİ SANAYİ VE TİCARET A.Ş.", "sektor": "GIDA"},
    "FZLGY": {"firma": "FUZUL GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "GARFA": {"firma": "GARANTİ FAKTORİNG A.Ş.", "sektor": "FİNANSAL KİRALAMA"},
    "GEDIK": {"firma": "GEDİK YATIRIM MENKUL DEĞERLER A.Ş.", "sektor": "ARACI KURUMLAR"},
    "GEDZA": {"firma": "GEDİZ AMBALAJ SANAYİ VE TİCARET A.Ş.", "sektor": "PLASTİK"},
    "GENTS": {"firma": "GENTAŞ DEKORATİF YÜZEYLER SANAYİ VE TİCARET A.Ş.", "sektor": "MOBİLYA"},
    "GEREL": {"firma": "GERSAN ELEKTRİK TİCARET VE SANAYİ A.Ş.", "sektor": "METAL EŞYA"},
    "GIPTA": {"firma": "GIPTA OFİS KIRTASİYE VE PROMOSYON ÜRÜNLERİ İMALAT SANAYİ A.Ş.", "sektor": "KIRTASİYE"},
    "GLBMD": {"firma": "GLOBAL MENKUL DEĞERLER A.Ş.", "sektor": "ARACI KURUMLAR"},
    "GLCVY": {"firma": "GELECEK VARLIK YÖNETİMİ A.Ş.", "sektor": "VARLIK YÖNETİM"},
    "GLRYH": {"firma": "GÜLER YATIRIM HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "GLYHO": {"firma": "GLOBAL YATIRIM HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "GMTAS": {"firma": "GİMAT MAĞAZACILIK SANAYİ VE TİCARET A.Ş.", "sektor": "TOPTAN TİCARET"},
    "GOKNR": {"firma": "GÖKNUR GIDA MADDELERİ ENERJİ İMALAT İTHALAT İHRACAT TİCARET VE SANAYİ A.Ş.", "sektor": "GIDA"},
    "GOLTS": {"firma": "GÖLTAŞ GÖLLER BÖLGESİ ÇİMENTO SANAYİ VE TİCARET A.Ş.", "sektor": "ÇİMENTO"},
    "GOODY": {"firma": "GOODYEAR LASTİKLERİ T.A.Ş.", "sektor": "LASTİK"},
    "GOZDE": {"firma": "GÖZDE GİRİŞİM SERMAYESİ YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GİRİŞİM SERMAYESİ YATIRIM ORTAKLIKLARI"},
    "GRNYO": {"firma": "GARANTİ YATIRIM ORTAKLIĞI A.Ş.", "sektor": "MENKUL KIYMET YATIRIM ORTAKLIKLARI"},
    "GSDDE": {"firma": "GSD DENİZCİLİK GAYRİMENKUL İNŞAAT SANAYİ VE TİCARET A.Ş.", "sektor": "ULAŞTIRMA VE DEPOLAMA"},
    "GSDHO": {"firma": "GSD HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "GUNDG": {"firma": "GÜNDOĞDU GIDA SÜT ÜRÜNLERİ SANAYİ VE DIŞ TİCARET A.Ş.", "sektor": "GIDA"},
    "GWIND": {"firma": "GALATA WIND ENERJİ A.Ş.", "sektor": "ENERJİ"},
    "GZNMI": {"firma": "GEZİNOMİ SEYAHAT TURİZM TİCARET A.Ş.", "sektor": "TURİZM"},
    "HATEK": {"firma": "HATEKS HATAY TEKSTİL İŞLETMELERİ A.Ş.", "sektor": "TEKSTİL"},
    "HATSN": {"firma": "HAT-SAN GEMİ İNŞAA BAKIM ONARIM DENİZ NAKLİYAT SANAYİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "HDFGS": {"firma": "HEDEF GİRİŞİM SERMAYESİ YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GİRİŞİM SERMAYESİ YATIRIM ORTAKLIKLARI"},
    "HEDEF": {"firma": "HEDEF HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "HKTM": {"firma": "HİDROPAR HAREKET KONTROL TEKNOLOJİLERİ MERKEZİ SANAYİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "HLGYO": {"firma": "HALK GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "HOROZ": {"firma": "HOROZ LOJİSTİK KARGO HİZMETLERİ VE TİCARET A.Ş.", "sektor": "ULAŞTIRMA VE DEPOLAMA"},
    "HRKET": {"firma": "HAREKET PROJE TAŞIMACILIĞI VE YÜK MÜHENDİSLİĞİ A.Ş.", "sektor": "ULAŞTIRMA VE DEPOLAMA"},
    "HTTBT": {"firma": "HİTİT BİLGİSAYAR HİZMETLERİ A.Ş.", "sektor": "TEKNOLOJİ"},
    "HUBVC": {"firma": "HUB GİRİŞİM SERMAYESİ YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GİRİŞİM SERMAYESİ YATIRIM ORTAKLIKLARI"},
    "HUNER": {"firma": "HUN YENİLENEBİLİR ENERJİ ÜRETİM A.Ş.", "sektor": "ENERJİ"},
    "HURGZ": {"firma": "HÜRRİYET GAZETECİLİK VE MATBAACILIK A.Ş.", "sektor": "MEDYA"},
    "ICBCT": {"firma": "ICBC TURKEY BANK A.Ş.", "sektor": "BANKALAR"},
    "ICUGS": {"firma": "ICU GİRİŞİM SERMAYESİ YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GİRİŞİM SERMAYESİ YATIRIM ORTAKLIKLARI"},
    "IDGYO": {"firma": "İDEALİST GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "IHAAS": {"firma": "İHLAS HABER AJANSI A.Ş.", "sektor": "MEDYA"},
    "IHEVA": {"firma": "İHLAS EV ALETLERİ İMALAT SANAYİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "IHGZT": {"firma": "İHLAS GAZETECİLİK A.Ş.", "sektor": "MEDYA"},
    "IHLAS": {"firma": "İHLAS HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "IHLGM": {"firma": "İHLAS GAYRİMENKUL PROJE GELİŞTİRME VE TİCARET A.Ş.", "sektor": "GAYRİMENKUL FAALİYETLERİ"},
    "IHYAY": {"firma": "İHLAS YAYIN HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "IMASM": {"firma": "İMAŞ MAKİNA SANAYİ A.Ş.", "sektor": "METAL EŞYA"},
    "INDES": {"firma": "İNDEKS BİLGİSAYAR SİSTEMLERİ MÜHENDİSLİK SANAYİ VE TİCARET A.Ş.", "sektor": "TEKNOLOJİ"},
    "INFO": {"firma": "İNFO YATIRIM MENKUL DEĞERLER A.Ş.", "sektor": "ARACI KURUMLAR"},
    "INGRM": {"firma": "INGRAM MİCRO BİLİŞİM SİSTEMLERİ A.Ş.", "sektor": "BİLİŞİM"},
    "INTEK": {"firma": "İNNOSA TEKNOLOJİ A.Ş.", "sektor": "TEKNOLOJİ"},
    "INTEM": {"firma": "İNTEMA İNŞAAT VE TESİSAT MALZEMELERİ YATIRIM VE PAZARLAMA A.Ş.", "sektor": "TOPTAN TİCARET"},
    "INVEO": {"firma": "INVEO YATIRIM HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "INVES": {"firma": "INVESTCO HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "ISBIR": {"firma": "İŞBİR HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "ISDMR": {"firma": "İSKENDERUN DEMİR VE ÇELİK A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "ISFIN": {"firma": "İŞ FİNANSAL KİRALAMA A.Ş.", "sektor": "FİNANSAL KİRALAMA"},
    "ISGSY": {"firma": "İŞ GİRİŞİM SERMAYESİ YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GİRİŞİM SERMAYESİ YATIRIM ORTAKLIKLARI"},
    "ISGYO": {"firma": "İŞ GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "ISKPL": {"firma": "IŞIK PLASTİK SANAYİ VE DIŞ TİCARET PAZARLAMA A.Ş.", "sektor": "PLASTİK"},
    "ISSEN": {"firma": "İŞBİR SENTETİK DOKUMA SANAYİ A.Ş.", "sektor": "TEKSTİL"},
    "ISYAT": {"firma": "İŞ YATIRIM ORTAKLIĞI A.Ş.", "sektor": "MENKUL KIYMET YATIRIM ORTAKLIKLARI"},
    "IZENR": {"firma": "İZDEMİR ENERJİ ELEKTRİK ÜRETİM A.Ş.", "sektor": "ENERJİ"},
    "IZFAS": {"firma": "İZMİR FIRÇA SANAYİ VE TİCARET A.Ş.", "sektor": "KİMYA"},
    "IZINV": {"firma": "İZ YATIRIM HOLDİNG A.Ş.", "sektor": "TARIM VE HAYVANCILIK"},
    "IZMDC": {"firma": "İZMİR DEMİR ÇELİK SANAYİ A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "JANTS": {"firma": "JANTSA JANT SANAYİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "KAPLM": {"firma": "KAPLAMİN AMBALAJ SANAYİ VE TİCARET A.Ş.", "sektor": "PLASTİK"},
    "KAREL": {"firma": "KAREL ELEKTRONİK SANAYİ VE TİCARET A.Ş.", "sektor": "TEKNOLOJİ"},
    "KARSN": {"firma": "KARSAN OTOMOTİV SANAYİİ VE TİCARET A.Ş.", "sektor": "OTOMOTİV"},
    "KARTN": {"firma": "KARTONSAN KARTON SANAYİ VE TİCARET A.Ş.", "sektor": "KAĞIT VE KAĞIT ÜRÜNLERİ"},
    "KATMR": {"firma": "KATMERCİLER ARAÇ ÜSTÜ EKİPMAN SANAYİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "KAYSE": {"firma": "KAYSERİ ŞEKER FABRİKASI A.Ş.", "sektor": "GIDA"},
    "KBORU": {"firma": "KUZEY BORU A.Ş.", "sektor": "KİMYA"},
    "KENT": {"firma": "KENT GIDA MADDELERİ SANAYİİ VE TİCARET A.Ş.", "sektor": "GIDA"},
    "KERVN": {"firma": "KERVANSARAY YATIRIM HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "KFEIN": {"firma": "KAFEİN YAZILIM HİZMETLERİ TİCARET A.Ş.", "sektor": "BİLİŞİM"},
    "KGYO": {"firma": "KORAY GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "KIMMR": {"firma": "ERSAN ALIŞVERİŞ HİZMETLERİ VE GIDA SANAYİ TİCARET A.Ş.", "sektor": "PERAKENDE TİCARET"},
    "KLGYO": {"firma": "KİLER GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "KLKIM": {"firma": "KALEKİM KİMYEVİ MADDELER SANAYİ VE TİCARET A.Ş.", "sektor": "SERAMİK"},
    "KLMSN": {"firma": "KLİMASAN KLİMA SANAYİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "KLNMA": {"firma": "TÜRKİYE KALKINMA VE YATIRIM BANKASI A.Ş.", "sektor": "BANKALAR"},
    "KLRHO": {"firma": "KİLER HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "KLSER": {"firma": "KALESERAMİK ÇANAKKALE KALEBODUR SERAMİK SANAYİ A.Ş.", "sektor": "SERAMİK"},
    "KLSYN": {"firma": "KOLEKSİYON MOBİLYA SANAYİ A.Ş.", "sektor": "MOBİLYA"},
    "KLYPV": {"firma": "KALYON GÜNEŞ TEKNOLOJİLERİ ÜRETİM A.Ş.", "sektor": "ENERJİ"},
    "KMPUR": {"firma": "KİMTEKS POLİÜRETAN SANAYİ VE TİCARET A.Ş.", "sektor": "KİMYA"},
    "KNFRT": {"firma": "KONFRUT TARIM A.Ş.", "sektor": "TARIM VE HAYVANCILIK"},
    "KOCMT": {"firma": "KOÇ METALURJİ A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "KONKA": {"firma": "KONYA KAĞIT SANAYİ VE TİCARET A.Ş.", "sektor": "KAĞIT VE KAĞIT ÜRÜNLERİ"},
    "KONYA": {"firma": "KONYA ÇİMENTO SANAYİİ A.Ş.", "sektor": "ÇİMENTO"},
    "KOPOL": {"firma": "KOZA POLYESTER SANAYİ VE TİCARET A.Ş.", "sektor": "KİMYA"},
    "KORDS": {"firma": "KORDSA TEKNİK TEKSTİL A.Ş.", "sektor": "TEKSTİL"},
    "KOTON": {"firma": "KOTON MAĞAZACILIK TEKSTİL SANAYİ VE TİCARET A.Ş.", "sektor": "PERAKENDE TİCARET"},
    "KRGYO": {"firma": "KÖRFEZ GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "KRONT": {"firma": "KRON TEKNOLOJİ A.Ş.", "sektor": "TEKNOLOJİ"},
    "KRPLS": {"firma": "KOROPLAST TEMİZLİK AMBALAJ ÜRÜNLERİ SANAYİ VE DIŞ TİCARET A.Ş.", "sektor": "KİMYA"},
    "KRSTL": {"firma": "KRİSTAL KOLA VE MEŞRUBAT SANAYİ TİCARET A.Ş.", "sektor": "GIDA"},
    "KRTEK": {"firma": "KARSU TEKSTİL SANAYİİ VE TİCARET A.Ş.", "sektor": "TEKSTİL"},
    "KRVGD": {"firma": "KERVAN GIDA SANAYİ VE TİCARET A.Ş.", "sektor": "GIDA"},
    "KSTUR": {"firma": "KUŞTUR KUŞADASI TURİZM ENDÜSTRİSİ A.Ş.", "sektor": "KONAKLAMA"},
    "KTSKR": {"firma": "KÜTAHYA ŞEKER FABRİKASI A.Ş.", "sektor": "GIDA"},
    "KUTPO": {"firma": "KÜTAHYA PORSELEN SANAYİ A.Ş.", "sektor": "SERAMİK"},
    "KUVVA": {"firma": "KUVVA GIDA TİCARET VE SANAYİ YATIRIMLARI A.Ş.", "sektor": "TOPTAN TİCARET"},
    "KZBGY": {"firma": "KIZILBÜK GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "KZGYO": {"firma": "KUZUGRUP GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "LIDER": {"firma": "LDR TURİZM A.Ş.", "sektor": "TURİZM"},
    "LIDFA": {"firma": "LİDER FAKTORİNG A.Ş.", "sektor": "FİNANSAL KİRALAMA"},
    "LILAK": {"firma": "LİLA KAĞIT SANAYİ VE TİCARET A.Ş.", "sektor": "KAĞIT VE KAĞIT ÜRÜNLERİ"},
    "LINK": {"firma": "LİNK BİLGİSAYAR SİSTEMLERİ YAZILIMI VE DONANIMI SANAYİ VE TİCARET A.Ş.", "sektor": "TEKNOLOJİ"},
    "LKMNH": {"firma": "LOKMAN HEKİM ENGÜRÜSAĞ SAĞLIK TURİZM EĞİTİM HİZMETLERİ VE İNŞAAT TAAHHÜT A.Ş.", "sektor": "SAĞLIK"},
    "LOGO": {"firma": "LOGO YAZILIM SANAYİ VE TİCARET A.Ş.", "sektor": "BİLİŞİM"},
    "LRSHO": {"firma": "LORAS HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "LUKSK": {"firma": "LÜKS KADİFE TİCARET VE SANAYİİ A.Ş.", "sektor": "TEKSTİL"},
    "LYDHO": {"firma": "LYDİA HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "LYDYE": {"firma": "LYDİA YEŞİL ENERJİ KAYNAKLARI A.Ş.", "sektor": "ENERJİ"},
    "MAALT": {"firma": "MARMARİS ALTINYUNUS TURİSTİK TESİSLER A.Ş.", "sektor": "KONAKLAMA"},
    "MACKO": {"firma": "MACKOLİK İNTERNET HİZMETLERİ TİCARET A.Ş.", "sektor": "BİLİŞİM"},
    "MAKIM": {"firma": "MAKİM MAKİNA TEKNOLOJİLERİ SANAYİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "MAKTK": {"firma": "MAKİNA TAKIM ENDÜSTRİSİ A.Ş.", "sektor": "METAL EŞYA"},
    "MANAS": {"firma": "MANAS ENERJİ YÖNETİMİ SANAYİ VE TİCARET A.Ş.", "sektor": "TEKNOLOJİ"},
    "MARBL": {"firma": "TUREKS TURUNÇ MADENCİLİK İÇ VE DIŞ TİCARET A.Ş.", "sektor": "MADENCİLİK"},
    "MARKA": {"firma": "MARKA YATIRIM HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "MARTI": {"firma": "MARTI OTEL İŞLETMELERİ A.Ş.", "sektor": "KONAKLAMA"},
    "MEDTR": {"firma": "MEDİTERA TIBBİ MALZEME SANAYİ VE TİCARET A.Ş.", "sektor": "SAĞLIK"},
    "MEGAP": {"firma": "MEGA POLİETİLEN KÖPÜK SANAYİ VE TİCARET A.Ş.", "sektor": "TEKSTİL"},
    "MEGMT": {"firma": "MEGA METAL SANAYİ VE TİCARET A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "MEKAG": {"firma": "MEKA GLOBAL MAKİNE İMALAT SANAYİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "MEPET": {"firma": "MEPET METRO PETROL VE TESİSLERİ SANAYİ TİCARET A.Ş.", "sektor": "PETROL"},
    "MERCN": {"firma": "MERCAN KİMYA SANAYİ VE TİCARET A.Ş.", "sektor": "KİMYA"},
    "MERIT": {"firma": "MERİT TURİZM YATIRIM VE İŞLETME A.Ş.", "sektor": "KONAKLAMA"},
    "MERKO": {"firma": "MERKO GIDA SANAYİ VE TİCARET A.Ş.", "sektor": "GIDA"},
    "METRO": {"firma": "METRO TİCARİ VE MALİ YATIRIMLAR HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "METUR": {"firma": "BLUME METAL KİMYA A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "MHRGY": {"firma": "MHR GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "MMCAS": {"firma": "MMC SANAYİ VE TİCARİ YATIRIMLAR A.Ş.", "sektor": "HOLDİNGLER"},
    "MNDRS": {"firma": "MENDERES TEKSTİL SANAYİ VE TİCARET A.Ş.", "sektor": "TEKSTİL"},
    "MNDTR": {"firma": "MONDİ TURKEY OLUKLU MUKAVVA KAĞIT VE AMBALAJ SANAYİ A.Ş.", "sektor": "KAĞIT VE KAĞIT ÜRÜNLERİ"},
    "MOBTL": {"firma": "MOBİLTEL İLETİŞİM HİZMETLERİ SANAYİ VE TİCARET A.Ş.", "sektor": "TEKNOLOJİ"},
    "MOGAN": {"firma": "MOGAN ENERJİ YATIRIM HOLDİNG A.Ş.", "sektor": "ENERJİ"},
    "MOPAS": {"firma": "MOPAŞ MARKETÇİLİK GIDA SANAYİ VE TİCARET A.Ş.", "sektor": "PERAKENDE TİCARET"},
    "MRGYO": {"firma": "MARTI GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "MRSHL": {"firma": "MARSHALL BOYA VE VERNİK SANAYİİ A.Ş.", "sektor": "KİMYA"},
    "MSGYO": {"firma": "MİSTRAL GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "MTRKS": {"firma": "MATRİKS FİNANSAL TEKNOLOJİLER A.Ş.", "sektor": "BİLİŞİM"},
    "MTRYO": {"firma": "METRO YATIRIM ORTAKLIĞI A.Ş.", "sektor": "MENKUL KIYMET YATIRIM ORTAKLIKLARI"},
    "MZHLD": {"firma": "MAZHAR ZORLU HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "NATEN": {"firma": "NATUREL YENİLENEBİLİR ENERJİ TİCARET A.Ş.", "sektor": "ENERJİ"},
    "NETAS": {"firma": "NETAŞ TELEKOMÜNİKASYON A.Ş.", "sektor": "TEKNOLOJİ"},
    "NIBAS": {"firma": "NİĞBAŞ NİĞDE BETON SANAYİ VE TİCARET A.Ş.", "sektor": "ÇİMENTO"},
    "NTGAZ": {"firma": "NATURELGAZ SANAYİ VE TİCARET A.Ş.", "sektor": "ENERJİ"},
    "NTHOL": {"firma": "NET HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "NUGYO": {"firma": "NUROL GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "NUHCM": {"firma": "NUH ÇİMENTO SANAYİ A.Ş.", "sektor": "ÇİMENTO"},
    "OBASE": {"firma": "OBASE BİLGİSAYAR VE DANIŞMANLIK HİZMETLERİ TİCARET A.Ş.", "sektor": "TEKNOLOJİ"},
    "ODINE": {"firma": "ODİNE SOLUTİONS TEKNOLOJİ TİCARET VE SANAYİ A.Ş.", "sektor": "TEKNOLOJİ"},
    "OFSYM": {"firma": "OFİS YEM GIDA SANAYİ TİCARET A.Ş.", "sektor": "GIDA"},
    "ONCSM": {"firma": "ONCOSEM ONKOLOJİK SİSTEMLER SANAYİ VE TİCARET A.Ş.", "sektor": "SAĞLIK"},
    "ONRYT": {"firma": "ONUR YÜKSEK TEKNOLOJİ A.Ş.", "sektor": "TEKNOLOJİ"},
    "ORCAY": {"firma": "ORÇAY ORTAKÖY ÇAY SANAYİ VE TİCARET A.Ş.", "sektor": "GIDA"},
    "ORGE": {"firma": "ORGE ENERJİ ELEKTRİK TAAHHÜT A.Ş.", "sektor": "İNŞAAT"},
    "ORMA": {"firma": "ORMA ORMAN MAHSÜLLERİ İNTEGRE SANAYİ VE TİCARET A.Ş.", "sektor": "MOBİLYA"},
    "OSMEN": {"firma": "OSMANLI YATIRIM MENKUL DEĞERLER A.Ş.", "sektor": "ARACI KURUMLAR"},
    "OSTIM": {"firma": "OSTİM ENDÜSTRİYEL YATIRIMLAR VE İŞLETME A.Ş.", "sektor": "HOLDİNGLER"},
    "OTTO": {"firma": "OTTO HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "OYAYO": {"firma": "OYAK YATIRIM ORTAKLIĞI A.Ş.", "sektor": "MENKUL KIYMET YATIRIM ORTAKLIKLARI"},
    "OYLUM": {"firma": "OYLUM SINAİ YATIRIMLAR A.Ş.", "sektor": "GIDA"},
    "OYYAT": {"firma": "OYAK YATIRIM MENKUL DEĞERLER A.Ş.", "sektor": "ARACI KURUMLAR"},
    "OZATD": {"firma": "ÖZATA DENİZCİLİK SANAYİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "OZGYO": {"firma": "ÖZDERİCİ GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "OZKGY": {"firma": "ÖZAK GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "OZRDN": {"firma": "ÖZERDEN AMBALAJ SANAYİ A.Ş.", "sektor": "KİMYA"},
    "OZSUB": {"firma": "ÖZSU BALIK ÜRETİM A.Ş.", "sektor": "TARIM VE HAYVANCILIK"},
    "OZYSR": {"firma": "ÖZYAŞAR TEL VE GALVANİZLEME SANAYİ A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "PAGYO": {"firma": "PANORA GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "PAMEL": {"firma": "PAMEL YENİLENEBİLİR ELEKTRİK ÜRETİM A.Ş.", "sektor": "ENERJİ"},
    "PAPIL": {"firma": "PAPİLON SAVUNMA TEKNOLOJİ VE TİCARET A.Ş.", "sektor": "SAVUNMA"},
    "PARSN": {"firma": "PARSAN MAKİNA PARÇALARI SANAYİİ A.Ş.", "sektor": "METAL EŞYA"},
    "PATEK": {"firma": "PASİFİK TEKNOLOJİ A.Ş.", "sektor": "TEKNOLOJİ"},
    "PCILT": {"firma": "PC İLETİŞİM VE MEDYA HİZMETLERİ SANAYİ TİCARET A.Ş.", "sektor": "MEDYA"},
    "PEKGY": {"firma": "PEKER GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "PENGD": {"firma": "PENGUEN GIDA SANAYİ A.Ş.", "sektor": "GIDA"},
    "PENTA": {"firma": "PENTA TEKNOLOJİ ÜRÜNLERİ DAĞITIM TİCARET A.Ş.", "sektor": "TEKNOLOJİ"},
    "PETUN": {"firma": "PINAR ENTEGRE ET VE UN SANAYİİ A.Ş.", "sektor": "GIDA"},
    "PINSU": {"firma": "PINAR SU VE İÇECEK SANAYİ VE TİCARET A.Ş.", "sektor": "GIDA"},
    "PKART": {"firma": "PLASTİKKART AKILLI KART İLETİŞİM SİSTEMLERİ SANAYİ VE TİCARET A.Ş.", "sektor": "TEKNOLOJİ"},
    "PKENT": {"firma": "PETROKENT TURİZM A.Ş.", "sektor": "KONAKLAMA"},
    "PLTUR": {"firma": "PLATFORM TURİZM TAŞIMACILIK GIDA İNŞAAT TEMİZLİK HİZMETLERİ SANAYİ VE TİCARET A.Ş.", "sektor": "TURİZM"},
    "PNLSN": {"firma": "PANELSAN ÇATI CEPHE SİSTEMLERİ SANAYİ VE TİCARET A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "PNSUT": {"firma": "PINAR SÜT MAMÜLLERİ SANAYİİ A.Ş.", "sektor": "GIDA"},
    "POLHO": {"firma": "POLİSAN HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "POLTK": {"firma": "POLİTEKNİK METAL SANAYİ VE TİCARET A.Ş.", "sektor": "KİMYA"},
    "PRDGS": {"firma": "PARDUS GİRİŞİM SERMAYESİ YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GİRİŞİM SERMAYESİ YATIRIM ORTAKLIKLARI"},
    "PRKAB": {"firma": "TÜRK PRYSMİAN KABLO VE SİSTEMLERİ A.Ş.", "sektor": "KİMYA"},
    "PRKME": {"firma": "PARK ELEKTRİK ÜRETİM MADENCİLİK SANAYİ VE TİCARET A.Ş.", "sektor": "MADENCİLİK"},
    "PRZMA": {"firma": "PRİZMA PRES MATBAACILIK YAYINCILIK SANAYİ VE TİCARET A.Ş.", "sektor": "KAĞIT VE KAĞIT ÜRÜNLERİ"},
    "PSDTC": {"firma": "PERGAMON STATUS DIŞ TİCARET A.Ş.", "sektor": "TOPTAN TİCARET"},
    "PSGYO": {"firma": "PASİFİK GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "QNBFK": {"firma": "QNB FİNANSAL KİRALAMA A.Ş.", "sektor": "FİNANSAL KİRALAMA"},
    "QNBTR": {"firma": "QNB BANK A.Ş.", "sektor": "BANKALAR"},
    "QUAGR": {"firma": "QUA GRANITE HAYAL YAPI VE ÜRÜNLERİ SANAYİ TİCARET A.Ş.", "sektor": "SERAMİK"},
    "RAYSG": {"firma": "RAY SİGORTA A.Ş.", "sektor": "SİGORTA"},
    "RGYAS": {"firma": "RÖNESANS GAYRİMENKUL YATIRIM A.Ş.", "sektor": "GAYRİMENKUL FAALİYETLERİ"},
    "RNPOL": {"firma": "RAİNBOW POLİKARBONAT SANAYİ TİCARET A.Ş.", "sektor": "KİMYA"},
    "RODRG": {"firma": "RODRİGO TEKSTİL SANAYİ VE TİCARET A.Ş.", "sektor": "TEKSTİL"},
    "ROYAL": {"firma": "ROYAL HALI İPLİK TEKSTİL MOBİLYA SANAYİ VE TİCARET A.Ş.", "sektor": "TEKSTİL"},
    "RTALB": {"firma": "RTA LABORATUVARLARI BİYOLOJİK ÜRÜNLER İLAÇ VE MAKİNE SANAYİ TİCARET A.Ş.", "sektor": "SAĞLIK"},
    "RUBNS": {"firma": "RUBENİS TEKSTİL SANAYİ TİCARET A.Ş.", "sektor": "TEKSTİL"},
    "RUZYE": {"firma": "RUZY MADENCİLİK VE ENERJİ YATIRIMLARI SANAYİ VE TİCARET A.Ş.", "sektor": "MADENCİLİK"},
    "RYGYO": {"firma": "REYSAŞ GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "RYSAS": {"firma": "REYSAŞ TAŞIMACILIK VE LOJİSTİK TİCARET A.Ş.", "sektor": "ULAŞTIRMA VE DEPOLAMA"},
    "SAFKR": {"firma": "SAFKAR EGE SOĞUTMACILIK KLİMA SOĞUK HAVA TESİSLERİ İHRACAT İTHALAT SANAYİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "SAMAT": {"firma": "SARAY MATBAACILIK KAĞITÇILIK KIRTASİYECİLİK TİCARET VE SANAYİ A.Ş.", "sektor": "KAĞIT VE KAĞIT ÜRÜNLERİ"},
    "SANEL": {"firma": "SAN-EL MÜHENDİSLİK ELEKTRİK TAAHHÜT SANAYİ VE TİCARET A.Ş.", "sektor": "İNŞAAT"},
    "SANFM": {"firma": "SANİFOAM ENDÜSTRİ VE TÜKETİM ÜRÜNLERİ SANAYİ TİCARET A.Ş.", "sektor": "KİMYA"},
    "SANKO": {"firma": "SANKO PAZARLAMA İTHALAT İHRACAT A.Ş.", "sektor": "TOPTAN TİCARET"},
    "SARKY": {"firma": "SARKUYSAN ELEKTROLİTİK BAKIR SANAYİ VE TİCARET A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "SAYAS": {"firma": "SAY YENİLENEBİLİR ENERJİ EKİPMANLARI SANAYİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "SDTTR": {"firma": "SDT UZAY VE SAVUNMA TEKNOLOJİLERİ A.Ş.", "sektor": "SAVUNMA"},
    "SEGMN": {"firma": "SEĞMEN KARDEŞLER GIDA ÜRETİM VE AMBALAJ SANAYİ A.Ş.", "sektor": "GIDA"},
    "SEGYO": {"firma": "ŞEKER GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "SEKFK": {"firma": "ŞEKER FİNANSAL KİRALAMA A.Ş.", "sektor": "FİNANSAL KİRALAMA"},
    "SEKUR": {"firma": "SEKURO PLASTİK AMBALAJ SANAYİ A.Ş.", "sektor": "PLASTİK"},
    "SELEC": {"firma": "SELÇUK ECZA DEPOSU TİCARET VE SANAYİ A.Ş.", "sektor": "İLAÇ"},
    "SELGD": {"firma": "DÜNYA HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "SELVA": {"firma": "SELVA GIDA SANAYİ A.Ş.", "sektor": "GIDA"},
    "SERNT": {"firma": "SERANİT GRANİT SERAMİK SANAYİ VE TİCARET A.Ş.", "sektor": "SERAMİK"},
    "SEYKM": {"firma": "SEYİTLER KİMYA SANAYİ A.Ş.", "sektor": "KİMYA"},
    "SILVR": {"firma": "SİLVERLİNE ENDÜSTRİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "SKTAS": {"firma": "SÖKTAŞ TEKSTİL SANAYİ VE TİCARET A.Ş.", "sektor": "TEKSTİL"},
    "SKYLP": {"firma": "SKYALP FİNANSAL TEKNOLOJİLER VE DANIŞMANLIK A.Ş.", "sektor": "TEKNOLOJİ"},
    "SKYMD": {"firma": "ŞEKER YATIRIM MENKUL DEĞERLER A.Ş.", "sektor": "ARACI KURUMLAR"},
    "SMART": {"firma": "SMARTİKS YAZILIM A.Ş.", "sektor": "BİLİŞİM"},
    "SMRVA": {"firma": "SÜMER VARLIK YÖNETİM A.Ş.", "sektor": "VARLIK YÖNETİM"},
    "SNGYO": {"firma": "SİNPAŞ GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "SNICA": {"firma": "SANİCA ISI SANAYİ A.Ş.", "sektor": "METAL EŞYA"},
    "SNKRN": {"firma": "SENKRON SİBER GÜVENLİK YAZILIM VE BİLİŞİM ÇÖZÜMLERİ A.Ş.", "sektor": "BİLİŞİM"},
    "SNPAM": {"firma": "SÖNMEZ PAMUKLU SANAYİİ A.Ş.", "sektor": "TEKSTİL"},
    "SODSN": {"firma": "SODAŞ SODYUM SANAYİİ A.Ş.", "sektor": "KİMYA"},
    "SOKE": {"firma": "SÖKE DEĞİRMENCİLİK SANAYİ VE TİCARET A.Ş.", "sektor": "GIDA"},
    "SONME": {"firma": "SÖNMEZ FİLAMENT SENTETİK İPLİK VE ELYAF SANAYİ A.Ş.", "sektor": "TEKSTİL"},
    "SRVGY": {"firma": "SERVET GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "SUMAS": {"firma": "SUMAŞ SUNİ TAHTA VE MOBİLYA SANAYİİ A.Ş.", "sektor": "MOBİLYA"},
    "SUNTK": {"firma": "SUN TEKSTİL SANAYİ VE TİCARET A.Ş.", "sektor": "TEKSTİL"},
    "SURGY": {"firma": "SUR TATİL EVLERİ GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "SUWEN": {"firma": "SUWEN TEKSTİL SANAYİ PAZARLAMA A.Ş.", "sektor": "PERAKENDE TİCARET"},
    "TARKM": {"firma": "TARKİM BİTKİ KORUMA SANAYİ VE TİCARET A.Ş.", "sektor": "KİMYA"},
    "TATEN": {"firma": "TATLIPINAR ENERJİ ÜRETİM A.Ş.", "sektor": "ENERJİ"},
    "TATGD": {"firma": "TAT GIDA SANAYİ A.Ş.", "sektor": "GIDA"},
    "TBORG": {"firma": "TÜRK TUBORG BİRA VE MALT SANAYİİ A.Ş.", "sektor": "GIDA"},
    "TCKRC": {"firma": "KIRAÇ GALVANİZ TELEKOMİNİKASYON METAL MAKİNE İNŞAAT ELEKTRİK SANAYİ VE TİCARET A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "TDGYO": {"firma": "TREND GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "TEHOL": {"firma": "TERA YATIRIM TEKNOLOJİ HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "TEKTU": {"firma": "TEK-ART İNŞAAT TİCARET TURİZM SANAYİ VE YATIRIMLAR A.Ş.", "sektor": "KONAKLAMA"},
    "TERA": {"firma": "TERA YATIRIM MENKUL DEĞERLER A.Ş.", "sektor": "ARACI KURUMLAR"},
    "TEZOL": {"firma": "EUROPAP TEZOL KAĞIT SANAYİ VE TİCARET A.Ş.", "sektor": "KAĞIT VE KAĞIT ÜRÜNLERİ"},
    "TGSAS": {"firma": "TGS DIŞ TİCARET A.Ş.", "sektor": "TOPTAN TİCARET"},
    "TKNSA": {"firma": "TEKNOSA İÇ VE DIŞ TİCARET A.Ş.", "sektor": "PERAKENDE TİCARET"},
    "TLMAN": {"firma": "TRABZON LİMAN İŞLETMECİLİĞİ A.Ş.", "sektor": "ULAŞTIRMA VE DEPOLAMA"},
    "TMPOL": {"firma": "TEMAPOL POLİMER PLASTİK VE İNŞAAT SANAYİ TİCARET A.Ş.", "sektor": "PLASTİK"},
    "TMSN": {"firma": "TÜMOSAN MOTOR VE TRAKTÖR SANAYİ A.Ş.", "sektor": "METAL EŞYA"},
    "TNZTP": {"firma": "TAPDİ OKSİJEN ÖZEL SAĞLIK VE EĞİTİM HİZMETLERİ SANAYİ TİCARET A.Ş.", "sektor": "SAĞLIK"},
    "TRCAS": {"firma": "TURCAS HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "TRGYO": {"firma": "TORUNLAR GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "TRHOL": {"firma": "TERA FİNANSAL YATIRIMLAR HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "TRILC": {"firma": "TURK İLAÇ VE SERUM SANAYİ A.Ş.", "sektor": "İLAÇ"},
    "TSGYO": {"firma": "TSKB GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "TSPOR": {"firma": "TRABZONSPOR SPORTİF YATIRIM VE FUTBOL İŞLETMECİLİĞİ TİCARET A.Ş.", "sektor": "SPOR"},
    "TUCLK": {"firma": "TUĞÇELİK ALÜMİNYUM VE METAL MAMÜLLERİ SANAYİ VE TİCARET A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "TUKAS": {"firma": "TUKAŞ GIDA SANAYİ VE TİCARET A.Ş.", "sektor": "GIDA"},
    "TURGG": {"firma": "TÜRKER PROJE GAYRİMENKUL VE YATIRIM GELİŞTİRME A.Ş.", "sektor": "İNŞAAT"},
    "UFUK": {"firma": "UFUK YATIRIM YÖNETİM VE GAYRİMENKUL A.Ş.", "sektor": "HOLDİNGLER"},
    "ULAS": {"firma": "ULAŞLAR TURİZM ENERJİ TARIM GIDA VE İNŞAAT YATIRIMLARI A.Ş.", "sektor": "KONAKLAMA"},
    "ULUFA": {"firma": "ULUSAL FAKTORİNG A.Ş.", "sektor": "FİNANSAL KİRALAMA"},
    "ULUSE": {"firma": "ULUSOY ELEKTRİK İMALAT TAAHHÜT VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "ULUUN": {"firma": "ULUSOY UN SANAYİ VE TİCARET A.Ş.", "sektor": "GIDA"},
    "UMPAS": {"firma": "UMPAŞ HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "UNLU": {"firma": "ÜNLÜ YATIRIM HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "USAK": {"firma": "UŞAK SERAMİK SANAYİ A.Ş.", "sektor": "ÇİMENTO"},
    "VAKFN": {"firma": "VAKIF FİNANSAL KİRALAMA A.Ş.", "sektor": "FİNANSAL KİRALAMA"},
    "VAKKO": {"firma": "VAKKO TEKSTİL VE HAZIR GİYİM SANAYİ İŞLETMELERİ A.Ş.", "sektor": "PERAKENDE TİCARET"},
    "VANGD": {"firma": "VANET GIDA SANAYİ İÇ VE DIŞ TİCARET A.Ş.", "sektor": "GIDA"},
    "VBTYZ": {"firma": "VBT YAZILIM A.Ş.", "sektor": "BİLİŞİM"},
    "VERTU": {"firma": "VERUSATURK GİRİŞİM SERMAYESİ YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GİRİŞİM SERMAYESİ YATIRIM ORTAKLIKLARI"},
    "VERUS": {"firma": "VERUSA HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "VESBE": {"firma": "VESTEL BEYAZ EŞYA SANAYİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "VKFYO": {"firma": "VAKIF MENKUL KIYMET YATIRIM ORTAKLIĞI A.Ş.", "sektor": "MENKUL KIYMET YATIRIM ORTAKLIKLARI"},
    "VKGYO": {"firma": "VAKIF GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "VKING": {"firma": "VİKİNG KAĞIT VE SELÜLOZ A.Ş.", "sektor": "KAĞIT VE KAĞIT ÜRÜNLERİ"},
    "VRGYO": {"firma": "VERA KONSEPT GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "VSNMD": {"firma": "VİŞNE MADENCİLİK ÜRETİM SANAYİ VE TİCARET A.Ş.", "sektor": "MADENCİLİK"},
    "YAPRK": {"firma": "YAPRAK SÜT VE BESİ ÇİFTLİKLERİ SANAYİ VE TİCARET A.Ş.", "sektor": "TARIM VE HAYVANCILIK"},
    "YATAS": {"firma": "YATAŞ YATAK VE YORGAN SANAYİ TİCARET A.Ş.", "sektor": "TEKSTİL"},
    "YAYLA": {"firma": "YAYLA ENERJİ ÜRETİM TURİZM VE İNŞAAT TİCARET A.Ş.", "sektor": "İNŞAAT"},
    "YBTAS": {"firma": "YİBİTAŞ YOZGAT İŞÇİ BİRLİĞİ İNŞAAT MALZEMELERİ TİCARET VE SANAYİ A.Ş.", "sektor": "İNŞAAT"},
    "YESIL": {"firma": "YEŞİL YATIRIM HOLDİNG A.Ş.", "sektor": "HOLDİNGLER"},
    "YGGYO": {"firma": "YENİ GİMAT GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "YGYO": {"firma": "YEŞİL GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
    "YIGIT": {"firma": "YİĞİT AKÜ MALZEMELERİ NAKLİYAT TURİZM İNŞAAT SANAYİ VE TİCARET A.Ş.", "sektor": "METAL EŞYA"},
    "YKSLN": {"firma": "YÜKSELEN ÇELİK A.Ş.", "sektor": "ANA METAL SANAYİ"},
    "YONGA": {"firma": "YONGA MOBİLYA SANAYİ VE TİCARET A.Ş.", "sektor": "MOBİLYA"},
    "YUNSA": {"firma": "YÜNSA YÜNLÜ SANAYİ VE TİCARET A.Ş.", "sektor": "TEKSTİL"},
    "YYAPI": {"firma": "YEŞİL YAPI ENDÜSTRİSİ A.Ş.", "sektor": "İNŞAAT"},
    "YYLGD": {"firma": "YAYLA AGRO GIDA SANAYİ VE TİCARET A.Ş.", "sektor": "GIDA"},
    "ZEDUR": {"firma": "ZEDUR ENERJİ ELEKTRİK ÜRETİM A.Ş.", "sektor": "ENERJİ"},
    "ZRGYO": {"firma": "ZİRAAT GAYRİMENKUL YATIRIM ORTAKLIĞI A.Ş.", "sektor": "GAYRİMENKUL YATIRIM ORTAKLIKLARI"},
}

HISSE_KODLARI = list(BIST_HISSELER.keys())

def hisse_bilgi_goster(kod):
    """Seçilen hissenin firma adı ve sektörünü göster"""
    if kod and kod in BIST_HISSELER:
        firma = BIST_HISSELER[kod]["firma"]
        sektor = BIST_HISSELER[kod]["sektor"]
        st.markdown(f"""<div class="hisse-info-box">
            🏢 <b>{firma}</b><br>
            <i style="font-size:0.8rem;">{sektor}</i>
        </div>""", unsafe_allow_html=True)

# --- SESSION STATE ---
for key, default in [
    ("portfoy", []),
    ("logs", []),
    ("pending_alis", None),
    ("pending_satis", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

def log_ekle(islem_tipi, hisse, detay):
    st.session_state.logs.append({
        "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "İşlem": islem_tipi,
        "Hisse": hisse,
        "Detay": detay
    })

def portfoy_ekle_alis(hisse, alis_tarihi, lot, alis_fiyati, alis_maliyeti):
    st.session_state.portfoy.append({
        "id": len(st.session_state.portfoy),
        "hisse": hisse,
        "firma": BIST_HISSELER.get(hisse, {}).get("firma", "-"),
        "sektor": BIST_HISSELER.get(hisse, {}).get("sektor", "-"),
        "alis_tarihi": str(alis_tarihi),
        "lot": lot,
        "alis_fiyati": round(alis_fiyati, 2),
        "alis_maliyeti": round(alis_maliyeti, 2),
        "satis_tarihi": None,
        "satis_fiyati": None,
        "satis_geliri": None,
        "durum": "Açık"
    })

# --- YAN MENÜ ---
with st.sidebar:
    st.header("⚙️ Ayarlar")
    komisyon_orani = st.number_input("Komisyon (Binde)", min_value=0.0, value=2.0, step=0.1) / 1000
    bsmv_orani = st.number_input("BSMV (%)", min_value=0.0, value=5.0, step=1.0) / 100
    efektif_komisyon = komisyon_orani * (1 + bsmv_orani)
    st.info(f"Net Kesinti: **%{efektif_komisyon*100:.4f}**")
    mevduat_faizi_sidebar = st.number_input("Mevduat Faizi (%/yıl)", value=45.0, step=1.0) / 100

# --- ANA EKRAN ---
st.title("📈 BIST Yatırımcı Asistanı")
st.caption("586 hisse · Komisyon dahil maliyet · Paçal · Kâr analizi")

tab_alis, tab_satis, tab_portfoy, tab_log = st.tabs(["🟢 Alış", "🔴 Satış", "💼 Portföy", "📋 Log"])

# ==========================================
# 🟢 ALIŞ SEKMESİ
# ==========================================
with tab_alis:
    alis_modu = st.radio(
        "İşlem Tipi:",
        ["💰 Param Var → Kaç Lot?", "📦 Lot Alacağım → Ne Kadar Para?", "📉 Maliyet Düşür (Paçal)"]
    )
    st.divider()

    if alis_modu == "💰 Param Var → Kaç Lot?":
        hisse = st.selectbox("Hisse Kodu", options=HISSE_KODLARI, key="a1_hisse")
        hisse_bilgi_goster(hisse)
        fiyat = st.number_input("Başlangıç Fiyatı (TL)", min_value=0.01, value=100.00, step=0.01, format="%.2f")
        st.caption(f"📌 Tick: **{get_tick_size(fiyat):.2f} TL**")
        butce = st.number_input("Toplam Bütçe (TL)", min_value=1.0, value=10000.0, step=1000.0)

        with st.expander("⚙️ Kademe Ayarları (opsiyonel)"):
            kademe_sayisi = st.number_input("Kademe Sayısı", min_value=1, max_value=20, value=1, key="k1")
            fiyat_adimi_tick = st.number_input("Kademeler Arası (Tick)", min_value=1, value=1, key="t1") if kademe_sayisi > 1 else 0
            dagilim_mantigi = st.selectbox("Dağılım", ["Eşit", "Piramit (Düştükçe Artan)"], key="d1") if kademe_sayisi > 1 else "Eşit"

        if st.button("📊 Alış Planı Oluştur", type="primary", key="btn1"):
            agirliklar = [1]*kademe_sayisi if "Eşit" in dagilim_mantigi else list(range(1, kademe_sayisi+1))
            toplam_agirlik = sum(agirliklar)
            plan, toplam_lot, toplam_maliyet = [], 0, 0.0
            kademe_fiyati = fiyat
            for i in range(kademe_sayisi):
                if i > 0:
                    kademe_fiyati = shift_price(kademe_fiyati, fiyat_adimi_tick, "down")
                if kademe_fiyati <= 0.01 and i > 0:
                    st.warning(f"⚠️ {i+1}. kademede fiyat tabana ulaştı.")
                    break
                kademe_butce = butce * (agirliklar[i] / toplam_agirlik)
                maliyet_lot = kademe_fiyati * (1 + efektif_komisyon)
                lot = math.floor(kademe_butce / maliyet_lot)
                gercek = lot * maliyet_lot
                toplam_lot += lot
                toplam_maliyet += gercek
                plan.append({
                    "Kademe": f"{i+1}",
                    "Fiyat": para_fmt(kademe_fiyati) + " ₺",
                    "Lot": lot,
                    "Maliyet": para_fmt(gercek) + " ₺"
                })
            st.session_state.pending_alis = {
                "hisse": hisse, "toplam_lot": toplam_lot,
                "toplam_maliyet": toplam_maliyet,
                "ort_fiyat": toplam_maliyet / toplam_lot if toplam_lot > 0 else fiyat,
                "plan": plan
            }

        if st.session_state.pending_alis and st.session_state.pending_alis.get("hisse") == hisse:
            pa = st.session_state.pending_alis
            st.dataframe(pd.DataFrame(pa["plan"]), use_container_width=True, hide_index=True)
            st.success(f"✅ **{pa['toplam_lot']} Lot** | Toplam Maliyet: **{para_fmt(pa['toplam_maliyet'])} TL** | Kalan: **{para_fmt(butce - pa['toplam_maliyet'])} TL**")
            st.divider()
            st.markdown("#### ✅ İşlem Gerçekleşti mi?")
            gercek_tarih = st.date_input("Alış Tarihi", key="alis_tarih_kayit")
            gercek_lot = st.number_input("Gerçekleşen Lot", min_value=1, value=int(pa["toplam_lot"]), key="alis_lot_kayit")
            gercek_fiyat = st.number_input("Gerçekleşen Ort. Fiyat (TL)", min_value=0.01, value=float(pa["ort_fiyat"]), format="%.2f", key="alis_fiyat_kayit")
            if st.button("📁 Portföye Ekle", type="primary", key="btn_portfoy_ekle"):
                gercek_maliyet = gercek_lot * gercek_fiyat * (1 + efektif_komisyon)
                portfoy_ekle_alis(pa["hisse"], gercek_tarih, gercek_lot, gercek_fiyat, gercek_maliyet)
                log_ekle("ALIŞ", pa["hisse"], f"{gercek_lot} lot @ {para_fmt(gercek_fiyat)} ₺ → Maliyet: {para_fmt(gercek_maliyet)} ₺")
                st.session_state.pending_alis = None
                st.success("✅ Portföye eklendi! Portföy sekmesinden takip edebilirsiniz.")
                st.rerun()

    elif alis_modu == "📦 Lot Alacağım → Ne Kadar Para?":
        hisse = st.selectbox("Hisse Kodu", options=HISSE_KODLARI, key="a2_hisse")
        hisse_bilgi_goster(hisse)
        fiyat = st.number_input("Başlangıç Fiyatı (TL)", min_value=0.01, value=100.00, step=0.01, format="%.2f")
        st.caption(f"📌 Tick: **{get_tick_size(fiyat):.2f} TL**")
        hedef_lot = st.number_input("Hedef Lot Sayısı", min_value=1, value=100)

        with st.expander("⚙️ Kademe Ayarları (opsiyonel)"):
            kademe_sayisi = st.number_input("Kademe Sayısı", min_value=1, max_value=20, value=1, key="k2")
            fiyat_adimi_tick = st.number_input("Kademeler Arası (Tick)", min_value=1, value=1, key="t2") if kademe_sayisi > 1 else 0
            dagilim_mantigi = st.selectbox("Dağılım", ["Eşit", "Piramit (Düştükçe Artan)"], key="d2") if kademe_sayisi > 1 else "Eşit"

        if st.button("💵 Gereken Nakdi Hesapla", type="primary", key="btn2"):
            agirliklar = [1]*kademe_sayisi if "Eşit" in dagilim_mantigi else list(range(1, kademe_sayisi+1))
            toplam_agirlik = sum(agirliklar)
            plan, toplam_para, kalan_lot = [], 0.0, hedef_lot
            kademe_fiyati = fiyat
            for i in range(kademe_sayisi):
                if i > 0:
                    kademe_fiyati = shift_price(kademe_fiyati, fiyat_adimi_tick, "down")
                if kademe_fiyati <= 0.01 and i > 0: break
                kademe_lot = kalan_lot if i == kademe_sayisi-1 else math.floor(hedef_lot*(agirliklar[i]/toplam_agirlik))
                if i < kademe_sayisi-1: kalan_lot -= kademe_lot
                maliyet = kademe_lot * kademe_fiyati * (1 + efektif_komisyon)
                toplam_para += maliyet
                plan.append({
                    "Kademe": f"{i+1}",
                    "Fiyat": para_fmt(kademe_fiyati) + " ₺",
                    "Lot": kademe_lot,
                    "Nakit": para_fmt(maliyet) + " ₺"
                })
            st.session_state.pending_alis = {
                "hisse": hisse, "toplam_lot": hedef_lot,
                "toplam_maliyet": toplam_para,
                "ort_fiyat": fiyat, "plan": plan
            }

        if st.session_state.pending_alis and st.session_state.pending_alis.get("hisse") == hisse:
            pa = st.session_state.pending_alis
            st.dataframe(pd.DataFrame(pa["plan"]), use_container_width=True, hide_index=True)
            st.success(f"✅ **{pa['toplam_lot']} Lot** için gerekli nakit: **{para_fmt(pa['toplam_maliyet'])} TL**")
            st.divider()
            st.markdown("#### ✅ İşlem Gerçekleşti mi?")
            gercek_tarih = st.date_input("Alış Tarihi", key="alis_tarih_kayit2")
            gercek_lot = st.number_input("Gerçekleşen Lot", min_value=1, value=int(pa["toplam_lot"]), key="alis_lot_kayit2")
            gercek_fiyat = st.number_input("Gerçekleşen Ort. Fiyat (TL)", min_value=0.01, value=float(pa["ort_fiyat"]), format="%.2f", key="alis_fiyat_kayit2")
            if st.button("📁 Portföye Ekle", type="primary", key="btn_portfoy_ekle2"):
                gercek_maliyet = gercek_lot * gercek_fiyat * (1 + efektif_komisyon)
                portfoy_ekle_alis(pa["hisse"], gercek_tarih, gercek_lot, gercek_fiyat, gercek_maliyet)
                log_ekle("ALIŞ", pa["hisse"], f"{gercek_lot} lot @ {para_fmt(gercek_fiyat)} ₺ → Maliyet: {para_fmt(gercek_maliyet)} ₺")
                st.session_state.pending_alis = None
                st.success("✅ Portföye eklendi!")
                st.rerun()

    else:  # Paçal
        hisse = st.selectbox("Hisse Kodu", options=HISSE_KODLARI, key="a3_hisse")
        hisse_bilgi_goster(hisse)
        mevcut_lot = st.number_input("Elinizdeki Lot", min_value=1, value=100)
        mevcut_maliyet = st.number_input("Mevcut Ortalama Maliyet (TL)", min_value=0.01, value=120.0, format="%.2f")
        guncel_fiyat = st.number_input("Şu Anki Fiyat (TL)", min_value=0.01, value=100.0, format="%.2f")
        hedef_maliyet = st.number_input("Hedef Maliyet (TL)", min_value=0.01, value=110.0, format="%.2f")

        if st.button("🔢 Paçal Denklemini Çöz", type="primary", key="btn3"):
            maliyet_lot = guncel_fiyat * (1 + efektif_komisyon)
            if hedef_maliyet >= mevcut_maliyet:
                st.error("Hedef maliyet, mevcut maliyetten düşük olmalı!")
            elif hedef_maliyet <= maliyet_lot:
                st.error(f"Hedefe ulaşılamaz. Min. fiyat: {para_fmt(maliyet_lot)} ₺")
            else:
                gerekli_lot = math.ceil((mevcut_lot * (mevcut_maliyet - hedef_maliyet)) / (hedef_maliyet - maliyet_lot))
                st.success(f"✅ **{gerekli_lot} Lot** daha almalısınız")
                st.info(f"Gerekli yatırım: **{para_fmt(gerekli_lot * maliyet_lot)} TL**")
                log_ekle("PAÇAL", hisse, f"Hedef {para_fmt(hedef_maliyet)} ₺ → {gerekli_lot} lot")

# ==========================================
# 🔴 SATIŞ SEKMESİ
# ==========================================
with tab_satis:
    satis_modu = st.radio(
        "İşlem Tipi:",
        ["💵 Ne Kadar Nakit → Kaç Lot?", "📦 Elimdekini Sat → Ne Geçer?", "📊 Reel Kâr & Faiz Analizi"]
    )
    st.divider()

    if satis_modu == "💵 Ne Kadar Nakit → Kaç Lot?":
        hisse_sat = st.selectbox("Hisse Kodu", options=HISSE_KODLARI, key="s1_hisse")
        hisse_bilgi_goster(hisse_sat)
        fiyat_sat = st.number_input("Satış Fiyatı (TL)", min_value=0.01, value=150.00, step=0.01, format="%.2f")
        st.caption(f"📌 Tick: **{get_tick_size(fiyat_sat,'up'):.2f} TL**")
        ihtiyac_nakit = st.number_input("Hesaba Geçmesi Gereken NET Nakit (TL)", min_value=1.0, value=50000.0)

        with st.expander("⚙️ Kademe Ayarları (opsiyonel)"):
            kademe_sayisi_s = st.number_input("Kademe Sayısı", min_value=1, max_value=20, value=1, key="ks1")
            fiyat_adimi_s = st.number_input("Kademeler Arası (Tick)", min_value=1, value=1, key="ts1") if kademe_sayisi_s > 1 else 0
            dagilim_s = st.selectbox("Dağılım", ["Eşit", "Piramit (Çıktıkça Artan)"], key="ds1") if kademe_sayisi_s > 1 else "Eşit"

        if st.button("📊 Satış Planı", type="primary", key="btn4"):
            agirliklar = [1]*kademe_sayisi_s if "Eşit" in dagilim_s else list(range(1, kademe_sayisi_s+1))
            toplam_agirlik = sum(agirliklar)
            plan, toplam_lot, toplam_nakit, kalan_hedef = [], 0, 0.0, ihtiyac_nakit
            kademe_fiyati = fiyat_sat
            for i in range(kademe_sayisi_s):
                if i > 0: kademe_fiyati = shift_price(kademe_fiyati, fiyat_adimi_s, "up")
                net_lot = kademe_fiyati * (1 - efektif_komisyon)
                kademe_hedef = kalan_hedef if i == kademe_sayisi_s-1 else ihtiyac_nakit*(agirliklar[i]/toplam_agirlik)
                if i < kademe_sayisi_s-1: kalan_hedef -= kademe_hedef
                lot = math.ceil(kademe_hedef / net_lot)
                gercek = lot * net_lot
                toplam_lot += lot; toplam_nakit += gercek
                plan.append({
                    "Kad.": f"{i+1}",
                    "Fiyat": para_fmt(kademe_fiyati) + " ₺",
                    "Lot": lot,
                    "Net Gelir": para_fmt(gercek) + " ₺"
                })
            st.session_state.pending_satis = {
                "hisse": hisse_sat, "toplam_lot": toplam_lot,
                "toplam_nakit": toplam_nakit, "ort_fiyat": fiyat_sat, "plan": plan
            }

        if st.session_state.pending_satis and st.session_state.pending_satis.get("hisse") == hisse_sat:
            ps = st.session_state.pending_satis
            st.dataframe(pd.DataFrame(ps["plan"]), use_container_width=True, hide_index=True)
            st.warning(f"Satılması gereken: **{ps['toplam_lot']} Lot**")
            st.success(f"Hesabınıza geçecek: **{para_fmt(ps['toplam_nakit'])} TL**")
            st.divider()
            st.markdown("#### ✅ İşlem Gerçekleşti mi?")
            acik_pozisyonlar = [p for p in st.session_state.portfoy if p["hisse"] == hisse_sat and p["durum"] == "Açık"]
            if acik_pozisyonlar:
                secenekler = {f"{p['alis_tarihi']} — {p['lot']} lot @ {para_fmt(p['alis_fiyati'])} ₺": p["id"] for p in acik_pozisyonlar}
                secim = st.selectbox("Portföydeki Hangi Pozisyon?", list(secenekler.keys()), key="satis_poz_sec")
                poz_id = secenekler[secim]
            else:
                poz_id = None
                st.info("Bu hisse için portföyde açık pozisyon yok. İşlem yalnızca loga kaydedilir.")
            gercek_satis_tarih = st.date_input("Satış Tarihi", key="satis_tarih_kayit")
            gercek_satis_lot = st.number_input("Gerçekleşen Lot", min_value=1, value=int(ps["toplam_lot"]), key="satis_lot_kayit")
            gercek_satis_fiyat = st.number_input("Gerçekleşen Ort. Satış Fiyatı (TL)", min_value=0.01, value=float(ps["ort_fiyat"]), format="%.2f", key="satis_fiyat_kayit")
            if st.button("📁 Satışı Kaydet", type="primary", key="btn_satis_kaydet"):
                gercek_gelir = gercek_satis_lot * gercek_satis_fiyat * (1 - efektif_komisyon)
                if poz_id is not None:
                    for p in st.session_state.portfoy:
                        if p["id"] == poz_id:
                            p["satis_tarihi"] = str(gercek_satis_tarih)
                            p["satis_fiyati"] = round(gercek_satis_fiyat, 2)
                            p["satis_geliri"] = round(gercek_gelir, 2)
                            p["durum"] = "Kapalı"
                log_ekle("SATIŞ", hisse_sat, f"{gercek_satis_lot} lot @ {para_fmt(gercek_satis_fiyat)} ₺ → Gelir: {para_fmt(gercek_gelir)} ₺")
                st.session_state.pending_satis = None
                st.success("✅ Satış kaydedildi!")
                st.rerun()

    elif satis_modu == "📦 Elimdekini Sat → Ne Geçer?":
        hisse_sat = st.selectbox("Hisse Kodu", options=HISSE_KODLARI, key="s2_hisse")
        hisse_bilgi_goster(hisse_sat)
        fiyat_sat = st.number_input("Satış Fiyatı (TL)", min_value=0.01, value=150.00, step=0.01, format="%.2f")
        satilacak_lot = st.number_input("Satılacak Lot Sayısı", min_value=1, value=100)

        with st.expander("⚙️ Kademe Ayarları (opsiyonel)"):
            kademe_sayisi_s = st.number_input("Kademe Sayısı", min_value=1, max_value=20, value=1, key="ks2")
            fiyat_adimi_s = st.number_input("Kademeler Arası (Tick)", min_value=1, value=1, key="ts2") if kademe_sayisi_s > 1 else 0
            dagilim_s = st.selectbox("Dağılım", ["Eşit", "Piramit (Çıktıkça Artan)"], key="ds2") if kademe_sayisi_s > 1 else "Eşit"

        if st.button("💵 Ele Geçecek Tutarı Hesapla", type="primary", key="btn5"):
            agirliklar = [1]*kademe_sayisi_s if "Eşit" in dagilim_s else list(range(1, kademe_sayisi_s+1))
            toplam_agirlik = sum(agirliklar)
            plan, toplam_nakit, kalan_lot = [], 0.0, satilacak_lot
            kademe_fiyati = fiyat_sat
            for i in range(kademe_sayisi_s):
                if i > 0: kademe_fiyati = shift_price(kademe_fiyati, fiyat_adimi_s, "up")
                kademe_lot = kalan_lot if i == kademe_sayisi_s-1 else math.floor(satilacak_lot*(agirliklar[i]/toplam_agirlik))
                if i < kademe_sayisi_s-1: kalan_lot -= kademe_lot
                net = kademe_lot * kademe_fiyati * (1 - efektif_komisyon)
                toplam_nakit += net
                plan.append({
                    "Kad.": f"{i+1}",
                    "Fiyat": para_fmt(kademe_fiyati) + " ₺",
                    "Lot": kademe_lot,
                    "Net Gelir": para_fmt(net) + " ₺"
                })
            st.session_state.pending_satis = {
                "hisse": hisse_sat, "toplam_lot": satilacak_lot,
                "toplam_nakit": toplam_nakit, "ort_fiyat": fiyat_sat, "plan": plan
            }

        if st.session_state.pending_satis and st.session_state.pending_satis.get("hisse") == hisse_sat:
            ps = st.session_state.pending_satis
            st.dataframe(pd.DataFrame(ps["plan"]), use_container_width=True, hide_index=True)
            st.success(f"**{ps['toplam_lot']} Lot** → **{para_fmt(ps['toplam_nakit'])} TL** net")
            st.divider()
            st.markdown("#### ✅ İşlem Gerçekleşti mi?")
            acik_pozisyonlar = [p for p in st.session_state.portfoy if p["hisse"] == hisse_sat and p["durum"] == "Açık"]
            if acik_pozisyonlar:
                secenekler = {f"{p['alis_tarihi']} — {p['lot']} lot @ {para_fmt(p['alis_fiyati'])} ₺": p["id"] for p in acik_pozisyonlar}
                secim = st.selectbox("Portföydeki Hangi Pozisyon?", list(secenekler.keys()), key="satis_poz_sec2")
                poz_id = secenekler[secim]
            else:
                poz_id = None
                st.info("Bu hisse için portföyde açık pozisyon yok. İşlem yalnızca loga kaydedilir.")
            gercek_satis_tarih = st.date_input("Satış Tarihi", key="satis_tarih_kayit2")
            gercek_satis_fiyat = st.number_input("Gerçekleşen Ort. Satış Fiyatı (TL)", min_value=0.01, value=float(ps["ort_fiyat"]), format="%.2f", key="satis_fiyat_kayit2")
            if st.button("📁 Satışı Kaydet", type="primary", key="btn_satis_kaydet2"):
                gercek_gelir = ps["toplam_lot"] * gercek_satis_fiyat * (1 - efektif_komisyon)
                if poz_id is not None:
                    for p in st.session_state.portfoy:
                        if p["id"] == poz_id:
                            p["satis_tarihi"] = str(gercek_satis_tarih)
                            p["satis_fiyati"] = round(gercek_satis_fiyat, 2)
                            p["satis_geliri"] = round(gercek_gelir, 2)
                            p["durum"] = "Kapalı"
                log_ekle("SATIŞ", hisse_sat, f"{ps['toplam_lot']} lot @ {para_fmt(gercek_satis_fiyat)} ₺ → Gelir: {para_fmt(gercek_gelir)} ₺")
                st.session_state.pending_satis = None
                st.success("✅ Satış kaydedildi!")
                st.rerun()

    else:  # Reel Kâr Analizi
        st.info("Borsa getirinizi mevduat fırsat maliyetiyle karşılaştırır.")
        alis_tarihi = st.date_input("Alış Tarihi")
        alis_fiyati_r = st.number_input("Ortalama Alış Fiyatı (TL)", min_value=0.01, value=100.0)
        lot_miktari = st.number_input("Lot Sayısı", min_value=1, value=100)
        satis_tarihi = st.date_input("Satış Tarihi")
        satis_fiyati_r = st.number_input("Satış Fiyatı (TL)", min_value=0.01, value=120.0)
        faiz_giris = st.number_input("Yıllık Mevduat Faizi (%)", min_value=0.0, value=45.0, step=1.0, key="faiz_reel")
        faiz_kullanim = faiz_giris / 100

        if st.button("📊 Reel Getiriyi Hesapla", type="primary", key="btn6"):
            gun = (satis_tarihi - alis_tarihi).days
            if gun < 0:
                st.error("Satış tarihi alış tarihinden önce olamaz!")
            else:
                gun = max(gun, 1)
                alis_m = lot_miktari * alis_fiyati_r * (1 + efektif_komisyon)
                satis_g = lot_miktari * satis_fiyati_r * (1 - efektif_komisyon)
                borsa_kar = satis_g - alis_m
                faiz_kar = alis_m * faiz_kullanim * gun / 365
                reel = borsa_kar - faiz_kar
                st.metric("Yatırım Süresi", f"{gun} gün")
                st.metric("Borsa Net Kârı", f"{para_fmt(borsa_kar)} TL")
                st.metric("Mevduat Alternatifi", f"{para_fmt(faiz_kar)} TL")
                if reel > 0:
                    st.success(f"🏆 Faizi yendiniz! **Reel Kâr: +{para_fmt(reel)} TL**")
                else:
                    st.error(f"⚠️ Faizin altında kaldınız. **Reel Kayıp: {para_fmt(reel)} TL**")
                log_ekle("REEL KAR", "-", f"{gun} gün → Reel: {para_fmt(reel)} TL")

# ==========================================
# 💼 PORTFÖY SEKMESİ
# ==========================================
with tab_portfoy:
    st.header("💼 Portföyüm")

    faiz_portfoy = st.number_input("Karşılaştırma Faizi (%/yıl)", min_value=0.0, value=45.0, step=1.0, key="faiz_portfoy") / 100

    if not st.session_state.portfoy:
        st.info("Henüz portföye eklenmiş işlem yok. Alış/Satış sekmelerinden işlemlerinizi ekleyin.")
    else:
        rows = []
        for p in st.session_state.portfoy:
            row = {
                "Hisse": p["hisse"],
                "Firma": p["firma"],
                "Sektör": p["sektor"],
                "Alış Tarihi": p["alis_tarihi"],
                "Lot": p["lot"],
                "Alış Fiy.": para_fmt(p["alis_fiyati"]) + " ₺",
                "Alış Maliyeti": para_fmt(p["alis_maliyeti"]) + " ₺",
                "Satış Tarihi": p["satis_tarihi"] or "-",
                "Satış Fiy.": para_fmt(p["satis_fiyati"]) + " ₺" if p["satis_fiyati"] else "-",
                "Satış Geliri": para_fmt(p["satis_geliri"]) + " ₺" if p["satis_geliri"] else "-",
                "Durum": p["durum"],
                "Net Kâr": "-",
                "Reel Kâr": "-",
            }
            if p["durum"] == "Kapalı" and p["satis_geliri"]:
                net_kar = p["satis_geliri"] - p["alis_maliyeti"]
                alis_dt = datetime.strptime(p["alis_tarihi"], "%Y-%m-%d")
                satis_dt = datetime.strptime(p["satis_tarihi"], "%Y-%m-%d")
                gun = max((satis_dt - alis_dt).days, 1)
                faiz_getiri = p["alis_maliyeti"] * faiz_portfoy * gun / 365
                reel_kar = net_kar - faiz_getiri
                row["Net Kâr"] = para_fmt(net_kar) + " ₺"
                row["Reel Kâr"] = ("+" if reel_kar >= 0 else "") + para_fmt(reel_kar) + " ₺"
            rows.append(row)

        df_portfoy = pd.DataFrame(rows)
        st.dataframe(df_portfoy, use_container_width=True, hide_index=True)

        # Özet
        kapali = [p for p in st.session_state.portfoy if p["durum"] == "Kapalı" and p["satis_geliri"]]
        if kapali:
            toplam_maliyet = sum(p["alis_maliyeti"] for p in kapali)
            toplam_gelir = sum(p["satis_geliri"] for p in kapali)
            toplam_net = toplam_gelir - toplam_maliyet
            st.divider()
            col1, col2, col3 = st.columns(3)
            col1.metric("Toplam Maliyet", para_fmt(toplam_maliyet) + " ₺")
            col2.metric("Toplam Gelir", para_fmt(toplam_gelir) + " ₺")
            col3.metric("Toplam Net Kâr", para_fmt(toplam_net) + " ₺", delta=f"%{(toplam_net/toplam_maliyet*100):.1f}" if toplam_maliyet > 0 else "")

        st.divider()
        if st.button("🗑️ Portföyü Temizle", type="secondary"):
            st.session_state.portfoy = []
            st.rerun()

# ==========================================
# 📋 LOG SEKMESİ
# ==========================================
with tab_log:
    st.header("Geçmiş İşlemler")
    if st.session_state.logs:
        st.dataframe(pd.DataFrame(st.session_state.logs), use_container_width=True, hide_index=True)
        if st.button("🗑️ Kayıtları Temizle", type="secondary"):
            st.session_state.logs = []
            st.rerun()
    else:
        st.info("Henüz kaydedilmiş işlem yok.")
