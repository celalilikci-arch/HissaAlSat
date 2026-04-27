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

# --- TAM BIST VERİTABANI (606 Hisse) ---
BIST_HISSELER = {
    "A1CAP": {"firma": "A1 Capital Yatitim Menkul Degerler A.S.", "sektor": "Finans"},
    "A1YEN": {"firma": "A1 Yenilenebilir Enerji Uretim As", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "AAGYO": {"firma": "Agaoglu Avrasya Gayrimenkul Yatirim Ortakligi As", "sektor": "Finans"},
    "ACSEL": {"firma": "Acıselsan Acıpayam Selüloz Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "ADEL": {"firma": "Adel Kalemcilik Ticaret Ve Sanayi A.Ş.", "sektor": "Dayanıklı tüketim malları"},
    "ADESE": {"firma": "Adese Gayrimenkul Yatırım A.Ş.", "sektor": "Finans"},
    "ADGYO": {"firma": "Adra Gayrimenkul Yatirim Ortakligi A.S.", "sektor": "Finans"},
    "AEFES": {"firma": "Anadolu Efes Biracılık Ve Malt Sanayii A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "AFYON": {"firma": "Afyon Çimento Sanayi T.A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "AGESA": {"firma": "Agesa Hayat Ve Emeklilik A.Ş.", "sektor": "Finans"},
    "AGHOL": {"firma": "Ag Anadolu Grubu Holding A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "AGROT": {"firma": "Agrotech Yuksek Teknoloji Ve Yatirim As", "sektor": "Teknoloji hizmetleri"},
    "AGYO": {"firma": "Atakule Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "AHGAZ": {"firma": "Ahlatcı Doğal Gaz Dağıtım Enerji Ve Yatırım A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "AHSGY": {"firma": "Ahes Gayrimenkul Yatirim Ortakligi As", "sektor": "Finans"},
    "AKBNK": {"firma": "Akbank T.A.Ş.", "sektor": "Finans"},
    "AKCNS": {"firma": "Akçansa Çimento Sanayi Ve Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "AKENR": {"firma": "Akenerji Elektrik Üretim A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "AKFGY": {"firma": "Akfen Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "AKFIS": {"firma": "Akfen İnsaat Turizm Ve Ticaret As", "sektor": "Endüstriyel hizmetler"},
    "AKFYE": {"firma": "Akfen Yenilenebilir Enerji A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "AKGRT": {"firma": "Aksigorta A.Ş.", "sektor": "Finans"},
    "AKHAN": {"firma": "Akhan Un Fabrikasi Ve Tarim Urunleri Gida Sanayi Ticaret Anonim Sirketi", "sektor": "İşlenebilen endüstriler"},
    "AKMGY": {"firma": "Akmerkez Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "AKSA": {"firma": "Aksa Akrilik Kimya Sanayii A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "AKSEN": {"firma": "Aksa Enerji Üretim A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "AKSGY": {"firma": "Akiş Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "AKSUE": {"firma": "Aksu Enerji Ve Ticaret A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "AKYHO": {"firma": "Akdeniz Yatırım Holding A.Ş.", "sektor": "Ticari hizmetler"},
    "ALARK": {"firma": "Alarko Holding A.Ş.", "sektor": "Finans"},
    "ALBRK": {"firma": "Albaraka Türk Katılım Bankası A.Ş.", "sektor": "Finans"},
    "ALCAR": {"firma": "Alarko Carrıer Sanayi Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "ALCTL": {"firma": "Alcatel Lucent Teletaş Telekomünikasyon A.Ş.", "sektor": "Elektronik teknoloji"},
    "ALFAS": {"firma": "Alfa Solar Enerji Sanayi Ve Ticaret A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "ALGYO": {"firma": "Alarko Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "ALKA": {"firma": "Alkim Kağıt Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "ALKIM": {"firma": "Alkim Alkali Kimya A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "ALKLC": {"firma": "Altinkilic Gida Ve Sut Sanayi Ticaret As", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "ALTIN": {"firma": "Darphane Altın Sertifikası", "sektor": ""},
    "ALTNY": {"firma": "Altinay Savunma Teknolojileri A.S.", "sektor": "Elektronik teknoloji"},
    "ALVES": {"firma": "Alves Kablo Sanayi Ve Ticaret A. S.", "sektor": "Üretici imalatı"},
    "ANELE": {"firma": "Anel Elektrik Proje Taahhüt Ve Ticaret A.Ş.", "sektor": "Endüstriyel hizmetler"},
    "ANGEN": {"firma": "Anatolia Tanı Ve Biyoteknoloji Ürünleri Araştırma Geliştirme Sanayi Ve Ticaret A.Ş.", "sektor": "Sağlık teknolojisi"},
    "ANHYT": {"firma": "Anadolu Hayat Emeklilik A.Ş.", "sektor": "Finans"},
    "ANSGR": {"firma": "Anadolu Anonim Türk Sigorta Şirketi", "sektor": "Finans"},
    "ARASE": {"firma": "Doğu Aras Enerji Yatırımları A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "ARCLK": {"firma": "Arçelik A.Ş.", "sektor": "Dayanıklı tüketim malları"},
    "ARDYZ": {"firma": "Ard Grup Bilişim Teknolojileri A.Ş.", "sektor": "Teknoloji hizmetleri"},
    "ARENA": {"firma": "Arena Bilgisayar Sanayi Ve Ticaret A.Ş.", "sektor": "Dağıtım servisleri"},
    "ARFYE": {"firma": "Arf Bio Yenilenebilir Enerji Uretim As", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "ARMGD": {"firma": "Armada Gida Ticaret Ve Sanayi Anonim Sirketi", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "ARSAN": {"firma": "Arsan Tekstil Ticaret Ve Sanayi A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "ARTMS": {"firma": "Artemis Hali A. S.", "sektor": "Perakende satış"},
    "ARZUM": {"firma": "Arzum Elektrikli Ev Aletleri Sanayi Ve Ticaret A.Ş.", "sektor": "Dağıtım servisleri"},
    "ASELS": {"firma": "Aselsan Elektronik Sanayi Ve Ticaret A.Ş.", "sektor": "Elektronik teknoloji"},
    "ASGYO": {"firma": "Asce Gayrımenkul Yatırım Ortaklıgı A.S.", "sektor": "Finans"},
    "ASTOR": {"firma": "Astor Enerji A.Ş.", "sektor": "Üretici imalatı"},
    "ASUZU": {"firma": "Anadolu Isuzu Otomotiv Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı tüketim malları"},
    "ATAGY": {"firma": "Ata Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "ATAKP": {"firma": "Atakey Patates Gida Sanayi Ve Ticaret As", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "ATATP": {"firma": "Atp Yazılım Ve Teknoloji A.Ş.", "sektor": "Teknoloji hizmetleri"},
    "ATATR": {"firma": "Ata Turizm Isletmecilik Tasimacilik Madencilik Kuyumculu", "sektor": "Tüketici hizmetleri"},
    "ATEKS": {"firma": "Akın Tekstil A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "ATLAS": {"firma": "Atlas Menkul Kıymetler Yatırım Ortaklığı A.Ş.", "sektor": "Çeşitli Hizmetler"},
    "ATSYH": {"firma": "Atlantis Yatırım Holding A.Ş.", "sektor": "Çeşitli Hizmetler"},
    "AVGYO": {"firma": "Avrasya Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "AVHOL": {"firma": "Avrupa Yatırım Holding A.Ş.", "sektor": "Sağlık hizmetleri"},
    "AVOD": {"firma": "A.V.O.D. Kurutulmuş Gıda Ve Tarım Ürünleri Sanayi Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "AVPGY": {"firma": "Avrupakent Gayrimenkul Yatirim Ortakligi Sa", "sektor": "Finans"},
    "AYCES": {"firma": "Altın Yunus Çeşme Turistik Tesisler A.Ş.", "sektor": "Tüketici hizmetleri"},
    "AYDEM": {"firma": "Aydem Yenilenebilir Enerji A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "AYEN": {"firma": "Ayen Enerji A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "AYES": {"firma": "Ayes Çelik Hasır Ve Çit Sanayi A.Ş.", "sektor": "Üretici imalatı"},
    "AYGAZ": {"firma": "Aygaz A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "AZTEK": {"firma": "Aztek Teknoloji Ürünleri Ticaret A.Ş.", "sektor": "Dağıtım servisleri"},
    "BAGFS": {"firma": "Bagfaş Bandırma Gübre Fabrikaları A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "BAHKM": {"firma": "Bahadir Kimya Sanayi Ve Ticaret Anonim Sirketi", "sektor": "İşlenebilen endüstriler"},
    "BAKAB": {"firma": "Bak Ambalaj Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "BALAT": {"firma": "Balatacılar Balatacılık Sanayi Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "BALSU": {"firma": "Balsu Gida Sanayi Ve Ticaret Anonim Sirketi", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "BANVT": {"firma": "Banvit Bandırma Vitaminli Yem Sanayii A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "BARMA": {"firma": "Barem Ambalaj Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "BASCM": {"firma": "Baştaş Başkent Çimento Sanayi Ve Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "BASGZ": {"firma": "Başkent Doğalgaz Dağıtım Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "BAYRK": {"firma": "Bayrak Ebt Taban Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "BEGYO": {"firma": "Bati Ege Gayrimenkul Yatirim Ortakligi A.S.", "sektor": "Finans"},
    "BERA": {"firma": "Bera Holding A.Ş.", "sektor": "Üretici imalatı"},
    "BESLR": {"firma": "Besler Gida Ve Kimya Sanayi Ve Ticaret As", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "BESTE": {"firma": "Best Brands Grup Enerji Yatirim As", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "BEYAZ": {"firma": "Beyaz Filo Oto Kiralama A.Ş.", "sektor": "Perakende satış"},
    "BFREN": {"firma": "Bosch Fren Sistemleri Sanayi Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "BIENY": {"firma": "Bien Yapı Ürünleri Sanayi Turizm Ve Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "BIGCH": {"firma": "Büyük Şefler Gıda Turizm Tekstil Danışmanlık Organizasyon Eğitim Sanayi Ve Ticaret A.Ş.", "sektor": "Tüketici hizmetleri"},
    "BIGEN": {"firma": "Birlesim Grup Enerji Yatirimlari As", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "BIGTK": {"firma": "Big Medya Teknoloji A.S.", "sektor": "Tüketici hizmetleri"},
    "BIMAS": {"firma": "Bim Birleşik Mağazalar A.Ş.", "sektor": "Perakende satış"},
    "BINBN": {"firma": "Bin Ulasim Ve Akilli Sehir Teknolojileri As", "sektor": "Ticari hizmetler"},
    "BINHO": {"firma": "1000 Yatirimlar Holding As", "sektor": "Teknoloji hizmetleri"},
    "BIOEN": {"firma": "Biotrend Çevre Ve Enerji Yatırımları A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "BIZIM": {"firma": "Bizim Toptan Satış Mağazaları A.Ş.", "sektor": "Perakende satış"},
    "BJKAS": {"firma": "Beşiktaş Futbol Yatırımları Sanayi Ve Ticaret A.Ş.", "sektor": "Tüketici hizmetleri"},
    "BLCYT": {"firma": "Bilici Yatırım Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "BLUME": {"firma": "Blume Metal Kimya Anonim Sirketi", "sektor": "Tüketici hizmetleri"},
    "BMSCH": {"firma": "Bms Çelik Hasır Sanayi Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "BMSTL": {"firma": "Bms Birleşik Metal Sanayi Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "BNTAS": {"firma": "Bantaş Bandırma Ambalaj Sanayi Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "BOBET": {"firma": "Boğaziçi Beton Sanayi Ve Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "BORLS": {"firma": "Borlease Otomotiv As", "sektor": "Finans"},
    "BORSK": {"firma": "Bor Seker A.S.", "sektor": "İşlenebilen endüstriler"},
    "BOSSA": {"firma": "Bossa Ticaret Ve Sanayi İşletmeleri T.A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "BRISA": {"firma": "Brisa Brıdgestone Sabancı Lastik Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı tüketim malları"},
    "BRKO": {"firma": "Birko Birleşik Koyunlulular Mensucat Ticaret Ve Sanayi A.Ş.", "sektor": "Dayanıklı tüketim malları"},
    "BRKSN": {"firma": "Berkosan Yalıtım Ve Tecrit Maddeleri Üretim Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "BRKVY": {"firma": "Birikim Varlık Yönetim A.Ş.", "sektor": "Finans"},
    "BRLSM": {"firma": "Birleşim Mühendislik Isıtma Soğutma Havalandırma Sanayi Ve Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "BRMEN": {"firma": "Birlik Mensucat Ticaret Ve Sanayi İşletmesi A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "BRSAN": {"firma": "Borusan Mannesmann Boru Sanayi Ve Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "BRYAT": {"firma": "Borusan Yatırım Ve Pazarlama A.Ş.", "sektor": "Çeşitli Hizmetler"},
    "BSOKE": {"firma": "Batısöke Söke Çimento Sanayii T.A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "BTCIM": {"firma": "Batıçim Batı Anadolu Çimento Sanayii A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "BUCIM": {"firma": "Bursa Çimento Fabrikası A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "BULGS": {"firma": "Bulls Girisim Sermayesi Yatirim Ortakligi Anonim Sirketi", "sektor": "Finans"},
    "BURCE": {"firma": "Burçelik Bursa Çelik Döküm Sanayii A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "BURVA": {"firma": "Burçelik Vana Sanayi Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "BVSAN": {"firma": "Bülbüloğlu Vinç Sanayi Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "BYDNR": {"firma": "Baydoner Restoranlari A.S.", "sektor": "Tüketici hizmetleri"},
    "CANTE": {"firma": "Çan2 Termik A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "CASA": {"firma": "Casa Emtia Petrol Kimyevi Ve Türevleri Sanayi Ticaret A.Ş.", "sektor": "Dağıtım servisleri"},
    "CATES": {"firma": "Cates Elektrik Uretim Anonim Sirketi", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "CCOLA": {"firma": "Coca-Cola İçecek A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "CELHA": {"firma": "Çelik Halat Ve Tel Sanayii A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "CEMAS": {"firma": "Çemaş Döküm Sanayi A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "CEMTS": {"firma": "Çemtaş Çelik Makina Sanayi Ve Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "CEMZY": {"firma": "Cem Zeytın Anonım Sırketı", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "CEOEM": {"firma": "Ceo Event Medya A.Ş.", "sektor": "Tüketici hizmetleri"},
    "CGCAM": {"firma": "Cagdas Cam Sanayi Ve Ticaret As", "sektor": "Dayanıklı tüketim malları"},
    "CIMSA": {"firma": "Çimsa Çimento Sanayi Ve Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "CLEBI": {"firma": "Çelebi Hava Servisi A.Ş.", "sektor": "Taşımacılık"},
    "CMBTN": {"firma": "Çimbeton Hazırbeton Ve Prefabrik Yapı Elemanları Sanayi Ve Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "CMENT": {"firma": "Çimentaş İzmir Çimento Fabrikası T.A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "CONSE": {"firma": "Consus Enerji İşletmeciliği Ve Hizmetleri A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "COSMO": {"firma": "Cosmos Yatırım Holding A.Ş.", "sektor": "Dağıtım servisleri"},
    "CRDFA": {"firma": "Credıtwest Faktoring A.Ş.", "sektor": "Finans"},
    "CRFSA": {"firma": "Carrefoursa Carrefour Sabancı Ticaret Merkezi A.Ş.", "sektor": "Perakende satış"},
    "CUSAN": {"firma": "Çuhadaroğlu Metal Sanayi Ve Pazarlama A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "CVKMD": {"firma": "Cvk Maden İşletmeleri Sanayi Ve Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "CWENE": {"firma": "Cw Enerji Mühendislik Ticaret Ve Sanayi A.Ş.", "sektor": "Elektronik teknoloji"},
    "DAGI": {"firma": "Dagi Giyim Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "DAPGM": {"firma": "Dap Gayrimenkul Geliştirme A.Ş.", "sektor": "Finans"},
    "DARDL": {"firma": "Dardanel Önentaş Gıda Sanayi A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "DCTTR": {"firma": "Dct Trading Dis Ticaret Anonim Sirketi", "sektor": "Dağıtım servisleri"},
    "DENGE": {"firma": "Denge Yatırım Holding A.Ş.", "sektor": "Finans"},
    "DERHL": {"firma": "Derlüks Yatırım Holding A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "DERIM": {"firma": "Derimod Konfeksiyon Ayakkabı Deri Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "DESA": {"firma": "Desa Deri Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "DESPC": {"firma": "Despec Bilgisayar Pazarlama Ve Ticaret A.Ş.", "sektor": "Dağıtım servisleri"},
    "DEVA": {"firma": "Deva Holding A.Ş.", "sektor": "Sağlık teknolojisi"},
    "DGATE": {"firma": "Datagate Bilgisayar Malzemeleri Ticaret A.Ş.", "sektor": "Dağıtım servisleri"},
    "DGGYO": {"firma": "Doğuş Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "DGNMO": {"firma": "Doğanlar Mobilya Grubu İmalat Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı tüketim malları"},
    "DIRIT": {"firma": "Diriteks Diriliş Tekstil Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "DITAS": {"firma": "Ditaş Doğan Yedek Parça İmalat Ve Teknik A.Ş.", "sektor": "Üretici imalatı"},
    "DMLKT": {"firma": "Emlak Konut Gayrimenkul Yatirim Ortakligi A.S. 0 % Certificates 2025-31.12.2199", "sektor": "Finans"},
    "DMRGD": {"firma": "Dmr Unlu Mamuller Uretim Gida Toptan Perakende Ihracat A.S.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "DMSAS": {"firma": "Demisaş Döküm Emaye Mamülleri Sanayii A.Ş.", "sektor": "Üretici imalatı"},
    "DNISI": {"firma": "Dinamik Isı Makina Yalıtım Malzemeleri Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "DOAS": {"firma": "Doğuş Otomotiv Servis Ve Ticaret A.Ş.", "sektor": "Perakende satış"},
    "DOCO": {"firma": "Do & Co Aktıengesellschaft", "sektor": "Tüketici hizmetleri"},
    "DOFER": {"firma": "Dofer Yapi Maizemeleri Sanayi Ve Ticaret A.S.", "sektor": "Enerji-dışı mineraller"},
    "DOFRB": {"firma": "Dof Robotik Sanayi Anonim Sirketi", "sektor": "Üretici imalatı"},
    "DOGUB": {"firma": "Doğusan Boru Sanayii Ve Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "DOHOL": {"firma": "Doğan Şirketler Grubu Holding A.Ş.", "sektor": "Perakende satış"},
    "DOKTA": {"firma": "Döktaş Dökümcülük Ticaret Ve Sanayi A.Ş.", "sektor": "Üretici imalatı"},
    "DSTKF": {"firma": "Destek Faktoring A.Ş.", "sektor": "Finans"},
    "DUNYH": {"firma": "Dunya Holding Anonim Sirketi", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "DURDO": {"firma": "Duran Doğan Basım Ve Ambalaj Sanayi A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "DURKN": {"firma": "Durukan Sekerleme Sanayi Ve Ticaret As", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "DYOBY": {"firma": "Dyo Boya Fabrikaları Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "DZGYO": {"firma": "Deniz Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "EBEBK": {"firma": "Ebebek Magazacılık Anonım Sırketı", "sektor": "Perakende satış"},
    "ECILC": {"firma": "Eis Eczacıbaşı İlaç Sınai Ve Finansal Yatırımlar Sanayi Ve Ticaret A.Ş.", "sektor": "Sağlık teknolojisi"},
    "ECOGR": {"firma": "Ecogreen Enerji Holding A.S.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "ECZYT": {"firma": "Eczacıbaşı Yatırım Holding Ortaklığı A.Ş.", "sektor": "Finans"},
    "EDATA": {"firma": "E-Data Teknoloji Pazarlama A.Ş.", "sektor": "Ticari hizmetler"},
    "EDIP": {"firma": "Edip Gayrimenkul Yatırım Sanayi Ve Ticaret A.Ş.", "sektor": "Finans"},
    "EFOR": {"firma": "Efor Yatirim Sanayi Ticaret A.S.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "EGEEN": {"firma": "Ege Endüstri Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "EGEGY": {"firma": "Egeyapi Avrupa Gayrimenkul Yatirim Ortakligi A.S.", "sektor": "Finans"},
    "EGEPO": {"firma": "Nasmed Özel Sağlık Hizmetleri Ticaret A.Ş.", "sektor": "Sağlık hizmetleri"},
    "EGGUB": {"firma": "Ege Gübre Sanayii A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "EGPRO": {"firma": "Ege Profil Ticaret Ve Sanayi A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "EGSER": {"firma": "Ege Seramik Sanayi Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "EKGYO": {"firma": "Emlak Konut Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "EKIZ": {"firma": "Ekiz Kimya Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "EKOS": {"firma": "Ekos Teknoloji Ve Elektrik As", "sektor": "Üretici imalatı"},
    "EKSUN": {"firma": "Eksun Gıda Tarım Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "ELITE": {"firma": "Elite Naturel Organik Gıda Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "EMKEL": {"firma": "Emek Elektrik Endüstrisi A.Ş.", "sektor": "Üretici imalatı"},
    "EMNIS": {"firma": "Eminiş Ambalaj Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "EMPAE": {"firma": "Empa Elektronik Sanayi Ve Ticaret A.S.", "sektor": "Elektronik teknoloji"},
    "ENDAE": {"firma": "Enda Enerji Holding Anonim Sirketi", "sektor": "Finans"},
    "ENERY": {"firma": "Enerya Enerji A.S.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "ENJSA": {"firma": "Enerjisa Enerji A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "ENKAI": {"firma": "Enka İnşaat Ve Sanayi A.Ş.", "sektor": "Endüstriyel hizmetler"},
    "ENPRA": {"firma": "Enpara Bank A.S.", "sektor": "Finans"},
    "ENSRI": {"firma": "Ensari Deri Gıda Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "ENTRA": {"firma": "Ic Enterra Yenilenebilir Enerji As", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "EPLAS": {"firma": "Egeplast Ege Plastik Ticaret Ve Sanayi A.Ş.", "sektor": "Üretici imalatı"},
    "ERBOS": {"firma": "Erbosan Erciyas Boru Sanayii Ve Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "ERCB": {"firma": "Erciyas Çelik Boru Sanayi A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "EREGL": {"firma": "Ereğli Demir Ve Çelik Fabrikaları T.A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "ERSU": {"firma": "Ersu Meyve Ve Gıda Sanayi A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "ESCAR": {"firma": "Escar Filo Kiralama Hizmetleri A.Ş.", "sektor": "Finans"},
    "ESCOM": {"firma": "Escort Teknoloji Yatırım A.Ş.", "sektor": "Elektronik teknoloji"},
    "ESEN": {"firma": "Esenboğa Elektrik Üretim A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "ETILR": {"firma": "Etiler Gıda Ve Ticari Yatırımlar Sanayi Ve Ticaret A.Ş.", "sektor": "Tüketici hizmetleri"},
    "ETYAT": {"firma": "Euro Trend Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "EUHOL": {"firma": "Euro Yatırım Holding A.Ş.", "sektor": "Finans"},
    "EUKYO": {"firma": "Euro Kapital Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "EUPWR": {"firma": "Europower Enerji Ve Otomasyon Teknolojileri Sanayi Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "EUREN": {"firma": "Europen Endüstri İnşaat Sanayi Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "EUYO": {"firma": "Euro Menkul Kıymet Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "EYGYO": {"firma": "Eyg Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "FADE": {"firma": "Fade Gıda Yatırım Sanayi Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "FENER": {"firma": "Fenerbahçe Futbol A.Ş.", "sektor": "Tüketici hizmetleri"},
    "FLAP": {"firma": "Flap Kongre Toplantı Hizmetleri Otomotiv Ve Turizm A.Ş.", "sektor": "Tüketici hizmetleri"},
    "FMIZP": {"firma": "Federal-Mogul İzmit Piston Ve Pim Üretim Tesisleri A.Ş.", "sektor": "Üretici imalatı"},
    "FONET": {"firma": "Fonet Bilgi Teknolojileri A.Ş.", "sektor": "Teknoloji hizmetleri"},
    "FORMT": {"firma": "Formet Metal Ve Cam Sanayi A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "FORTE": {"firma": "Forte Bılgı Iletısım Teknolojılerı Ve Savunma Sanayı A.S.", "sektor": "Teknoloji hizmetleri"},
    "FRIGO": {"firma": "Frigo-Pak Gıda Maddeleri Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "FRMPL": {"firma": "Formul Plastik Ve Metal Sanayi As", "sektor": "Üretici imalatı"},
    "FROTO": {"firma": "Ford Otomotiv Sanayi A.Ş.", "sektor": "Dayanıklı tüketim malları"},
    "FZLGY": {"firma": "Fuzul Gayrımenkul Yatırım Ortaklıgı A.S.", "sektor": "Dayanıklı tüketim malları"},
    "GARAN": {"firma": "Türkiye Garanti Bankası A.Ş.", "sektor": "Finans"},
    "GARFA": {"firma": "Garanti Faktoring A.Ş.", "sektor": "Finans"},
    "GATEG": {"firma": "Gate Group Teknoloji Medya Ve Siber Guvenlik Hizmetleri A.S.", "sektor": "Ticari hizmetler"},
    "GEDIK": {"firma": "Gedik Yatırım Menkul Değerler A.Ş.", "sektor": "Finans"},
    "GEDZA": {"firma": "Gediz Ambalaj Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "GENIL": {"firma": "Gen İlaç Ve Sağlık Ürünleri Sanayi Ve Ticaret A.Ş.", "sektor": "Sağlık teknolojisi"},
    "GENKM": {"firma": "Gentas Kimya Sanayi Ve Ticaret Pazarlama", "sektor": "İşlenebilen endüstriler"},
    "GENTS": {"firma": "Gentaş Dekoratif Yüzeyler Sanayi Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "GEREL": {"firma": "Gersan Elektrik Ticaret Ve Sanayi A.Ş.", "sektor": "Üretici imalatı"},
    "GESAN": {"firma": "Girişim Elektrik Sanayi Taahhüt Ve Ticaret A.Ş.", "sektor": "Elektronik teknoloji"},
    "GIPTA": {"firma": "Gipta Ofis Kirtasiye Ve Promosyon Urunleri Imalat Sanayi A.S.", "sektor": "Üretici imalatı"},
    "GLBMD": {"firma": "Global Menkul Değerler A.Ş.", "sektor": "Finans"},
    "GLCVY": {"firma": "Gelecek Varlık Yönetimi A.Ş.", "sektor": "Finans"},
    "GLRMK": {"firma": "Gulermak Agir Sanayi Insaat Ve Taahhut A.S.", "sektor": "Endüstriyel hizmetler"},
    "GLRYH": {"firma": "Güler Yatırım Holding A.Ş.", "sektor": "Finans"},
    "GLYHO": {"firma": "Global Yatırım Holding A.Ş.", "sektor": "Finans"},
    "GMTAS": {"firma": "Gimat Mağazacılık Sanayi Ve Ticaret A.Ş.", "sektor": "Perakende satış"},
    "GOKNR": {"firma": "Göknur Gıda Maddeleri Enerji İmalat İthalat İhracat Ticaret Ve Sanayi A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "GOLTS": {"firma": "Göltaş Göller Bölgesi Çimento Sanayi Ve Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "GOODY": {"firma": "Goodyear Lastikleri T.A.Ş.", "sektor": "Dayanıklı tüketim malları"},
    "GOZDE": {"firma": "Gözde Girişim Sermayesi Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "GRNYO": {"firma": "Garanti Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "GRSEL": {"firma": "Gür-Sel Turizm Taşımacılık Ve Servis Ticaret A.Ş.", "sektor": "Tüketici hizmetleri"},
    "GRTHO": {"firma": "Grainturk Holding A.S.", "sektor": "Dağıtım servisleri"},
    "GSDDE": {"firma": "Gsd Denizcilik Gayrimenkul İnşaat Sanayi Ve Ticaret A.Ş.", "sektor": "Taşımacılık"},
    "GSDHO": {"firma": "Gsd Holding A.Ş.", "sektor": "Taşımacılık"},
    "GSRAY": {"firma": "Galatasaray Sportif Sınai Ve Ticari Yatırımlar A.Ş.", "sektor": "Tüketici hizmetleri"},
    "GUBRF": {"firma": "Gübre Fabrikaları T.A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "GUNDG": {"firma": "Gundogdu Gida Sut Urunleri Sanayi Ve Dis Ticaret As", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "GWIND": {"firma": "Galata Wınd Enerji A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "GZNMI": {"firma": "Gezinomi Seyahat Turizm Ticaret A.Ş.", "sektor": "Tüketici hizmetleri"},
    "HALKB": {"firma": "Türkiye Halk Bankası A.Ş.", "sektor": "Finans"},
    "HATEK": {"firma": "Hateks Hatay Tekstil İşletmeleri A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "HATSN": {"firma": "Hat-San Gemi Insaa Bakim Onarim Deniz Nakliyat Sanayi Ve Ticaret A.S.", "sektor": "Üretici imalatı"},
    "HDFGS": {"firma": "Hedef Girişim Sermayesi Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "HEDEF": {"firma": "Hedef Holding A.Ş.", "sektor": "Finans"},
    "HEKTS": {"firma": "Hektaş Ticaret T.A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "HKTM": {"firma": "Hidropar Hareket Kontrol Teknolojileri Merkezi Sanayi Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "HLGYO": {"firma": "Halk Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "HOROZ": {"firma": "Horoz Lojistik Kargo Hizmetleri Ve Ticaret As", "sektor": "Taşımacılık"},
    "HRKET": {"firma": "Hareket Proje Tasimaciligi Ve Yuk Muhendisligi As", "sektor": "Taşımacılık"},
    "HTTBT": {"firma": "Hitit Bilgisayar Hizmetleri A.Ş.", "sektor": "Teknoloji hizmetleri"},
    "HUBVC": {"firma": "Hub Girişim Sermayesi Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "HUNER": {"firma": "Hun Yenilenebilir Enerji Üretim A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "HURGZ": {"firma": "Hürriyet Gazetecilik Ve Matbaacılık A.Ş.", "sektor": "Tüketici hizmetleri"},
    "ICBCT": {"firma": "Icbc Turkey Bank A.Ş.", "sektor": "Finans"},
    "ICUGS": {"firma": "Icu Girisim Sermayesi Yatirim Ortakligi A.S.", "sektor": "Finans"},
    "IDGYO": {"firma": "İdealist Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "IEYHO": {"firma": "Işıklar Enerji Ve Yapı Holding A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "IHAAS": {"firma": "İhlas Haber Ajansı A.Ş.", "sektor": "Ticari hizmetler"},
    "IHEVA": {"firma": "İhlas Ev Aletleri İmalat Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı tüketim malları"},
    "IHGZT": {"firma": "İhlas Gazetecilik A.Ş.", "sektor": "Tüketici hizmetleri"},
    "IHLAS": {"firma": "İhlas Holding A.Ş.", "sektor": "Finans"},
    "IHLGM": {"firma": "İhlas Gayrimenkul Proje Geliştirme Ve Ticaret A.Ş.", "sektor": "Finans"},
    "IHYAY": {"firma": "İhlas Yayın Holding A.Ş.", "sektor": "Tüketici hizmetleri"},
    "IMASM": {"firma": "İmaş Makina Sanayi A.Ş.", "sektor": "Üretici imalatı"},
    "INDES": {"firma": "İndeks Bilgisayar Sistemleri Mühendislik Sanayi Ve Ticaret A.Ş.", "sektor": "Dağıtım servisleri"},
    "INFO": {"firma": "İnfo Yatırım Menkul Değerler A.Ş.", "sektor": "Finans"},
    "INGRM": {"firma": "Ingram Micro Bilişim Sistemleri A.Ş.", "sektor": "Dağıtım servisleri"},
    "INTEK": {"firma": "Innosa Teknoloji Anonim Sirketi", "sektor": "İşlenebilen endüstriler"},
    "INTEM": {"firma": "İntema İnşaat Ve Tesisat Malzemeleri Yatırım Ve Pazarlama A.Ş.", "sektor": "Üretici imalatı"},
    "INVEO": {"firma": "Inveo Yatırım Holding A.Ş.", "sektor": "Finans"},
    "INVES": {"firma": "Investco Holding A.Ş.", "sektor": "Finans"},
    "ISBIR": {"firma": "İşbir Holding A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "ISBTR": {"firma": "Türkiye İş Bankası A.Ş.", "sektor": "Finans"},
    "ISCTR": {"firma": "Türkiye İş Bankası A.Ş.", "sektor": "Finans"},
    "ISDMR": {"firma": "İskenderun Demir Ve Çelik A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "ISFIN": {"firma": "İş Finansal Kiralama A.Ş.", "sektor": "Finans"},
    "ISGYO": {"firma": "İş Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "ISKPL": {"firma": "Işık Plastik Sanayi Ve Dış Ticaret Pazarlama A.Ş.", "sektor": "Üretici imalatı"},
    "ISKUR": {"firma": "Türkiye İş Bankası A.Ş.", "sektor": "Finans"},
    "ISMEN": {"firma": "İş Yatırım Menkul Değerler A.Ş.", "sektor": "Finans"},
    "ISSEN": {"firma": "İşbir Sentetik Dokuma Sanayi A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "IZENR": {"firma": "Izdemir Enerji Elektrik Uretim A.S.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "IZFAS": {"firma": "İzmir Fırça Sanayi Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "IZINV": {"firma": "İz Yatırım Holding A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "IZMDC": {"firma": "İzmir Demir Çelik Sanayi A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "JANTS": {"firma": "Jantsa Jant Sanayi Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "KAPLM": {"firma": "Kaplamin Ambalaj Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "KAREL": {"firma": "Karel Elektronik Sanayi Ve Ticaret A.Ş.", "sektor": "Elektronik teknoloji"},
    "KARSN": {"firma": "Karsan Otomotiv Sanayii Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "KARTN": {"firma": "Kartonsan Karton Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "KATMR": {"firma": "Katmerciler Araç Üstü Ekipman Sanayi Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "KAYSE": {"firma": "Kayseri Şeker Fabrikası A.Ş.", "sektor": "Sağlık teknolojisi"},
    "KBORU": {"firma": "Kuzey Boru A.S.", "sektor": "Üretici imalatı"},
    "KCAER": {"firma": "Kocaer Çelik Sanayi Ve Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "KCHOL": {"firma": "Koç Holding A.Ş.", "sektor": "Enerji mineralleri"},
    "KENT": {"firma": "Kent Gıda Maddeleri Sanayii Ve Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "KERVN": {"firma": "Kervansaray Yatırım Holding A.Ş.", "sektor": "Tüketici hizmetleri"},
    "KFEIN": {"firma": "Kafein Yazılım Hizmetleri Ticaret A.Ş.", "sektor": "Teknoloji hizmetleri"},
    "KGYO": {"firma": "Koray Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "KIMMR": {"firma": "Ersan Alışveriş Hizmetleri Ve Gıda Sanayi Ticaret A.Ş.", "sektor": "Perakende satış"},
    "KLGYO": {"firma": "Kiler Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "KLKIM": {"firma": "Kalekim Kimyevi Maddeler Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "KLMSN": {"firma": "Klimasan Klima Sanayi Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "KLNMA": {"firma": "Türkiye Kalkınma Ve Yatırım Bankası A.Ş.", "sektor": "Finans"},
    "KLRHO": {"firma": "Kiler Holding A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "KLSER": {"firma": "Kaleseramik Canakkale Kalebodur Seramik A.S.", "sektor": "Üretici imalatı"},
    "KLSYN": {"firma": "Koleksiyon Mobilya Sanayi A.Ş.", "sektor": "Dayanıklı tüketim malları"},
    "KLYPV": {"firma": "Kalyon Gunes Teknolojileri Uretim Anonim Sirketi", "sektor": "Üretici imalatı"},
    "KMPUR": {"firma": "Kimteks Poliüretan Sanayi Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "KNFRT": {"firma": "Konfrut Gıda Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "KOCMT": {"firma": "Koc Metalurji As", "sektor": "Enerji-dışı mineraller"},
    "KONKA": {"firma": "Konya Kağıt Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "KONTR": {"firma": "Kontrolmatik Teknoloji Enerji Ve Mühendislik A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "KONYA": {"firma": "Konya Çimento Sanayii A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "KOPOL": {"firma": "Koza Polyester Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "KORDS": {"firma": "Kordsa Teknik Tekstil A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "KOTON": {"firma": "Koton Mağazacılık Tekstil Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "KRDMA": {"firma": "Kardemir Karabük Demir Çelik Sanayi Ve Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "KRDMB": {"firma": "Kardemir Karabük Demir Çelik Sanayi Ve Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "KRDMD": {"firma": "Kardemir Karabük Demir Çelik Sanayi Ve Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "KRGYO": {"firma": "Körfez Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "KRONT": {"firma": "Kron Telekomünikasyon Hizmetleri A.Ş.", "sektor": "İletişim"},
    "KRPLS": {"firma": "Koroplast Temizlik Ambalaj Ürünleri Sanayi Ve Dış Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "KRSTL": {"firma": "Kristal Kola Ve Meşrubat Sanayi Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "KRTEK": {"firma": "Karsu Tekstil Sanayii Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "KRVGD": {"firma": "Kervan Gıda Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "KSTUR": {"firma": "Kuştur Kuşadası Turizm Endüstri A.Ş.", "sektor": "Tüketici hizmetleri"},
    "KTLEV": {"firma": "Katılımevım Tasarruf Fınansman A.S.", "sektor": "Finans"},
    "KTSKR": {"firma": "Kütahya Şeker Fabrikası A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "KUTPO": {"firma": "Kütahya Porselen Sanayi A.Ş.", "sektor": "Dayanıklı tüketim malları"},
    "KUVVA": {"firma": "Kuvva Gıda Ticaret Ve Sanayi Yatırımları A.Ş.", "sektor": "Dayanıklı tüketim malları"},
    "KUYAS": {"firma": "Kuyaş Yatırım A.Ş.", "sektor": "Finans"},
    "KZBGY": {"firma": "Kızılbük Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "KZGYO": {"firma": "Kuzugrup Gayrimenkul Yatirim Ortakligi As", "sektor": "Finans"},
    "LIDER": {"firma": "Ldr Turizm A.Ş.", "sektor": "Finans"},
    "LIDFA": {"firma": "Lider Faktoring A.Ş.", "sektor": "Finans"},
    "LILAK": {"firma": "Lila Kagit Sanayi Ve Ticaret Anonim Sirketi", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "LINK": {"firma": "Link Bilgisayar Sistemleri Yazılımı Ve Donanımı Sanayi Ve Ticaret A.Ş.", "sektor": "Teknoloji hizmetleri"},
    "LKMNH": {"firma": "Lokman Hekim Engürüsağ Sağlık Turizm Eğitim Hizmetleri Ve İnşaat Taahhüt A.Ş.", "sektor": "Sağlık hizmetleri"},
    "LMKDC": {"firma": "Limak Dogu Anadolu Cimento Sanayi Ve Ticaret As", "sektor": "Enerji-dışı mineraller"},
    "LOGO": {"firma": "Logo Yazılım Sanayi Ve Ticaret A.Ş.", "sektor": "Teknoloji hizmetleri"},
    "LRSHO": {"firma": "Loras Holding Anonim Sirketi", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "LUKSK": {"firma": "Lüks Kadife Ticaret Ve Sanayii A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "LXGYO": {"firma": "Luxera Gayrimenkul Yatirim Ortakligi A.S.", "sektor": "Finans"},
    "LYDHO": {"firma": "Lydia Holding A.S.", "sektor": "Dağıtım servisleri"},
    "LYDYE": {"firma": "Lydia Yesil Enerji Kaynaklari A.S.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "MAALT": {"firma": "Marmaris Altınyunus Turistik Tesisler A.Ş.", "sektor": "Tüketici hizmetleri"},
    "MACKO": {"firma": "Mackolik İnternet Hizmetleri Ticaret A.Ş.", "sektor": "Ticari hizmetler"},
    "MAGEN": {"firma": "Margün Enerji Üretim Sanayi Ve Ticaret A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "MAKIM": {"firma": "Makim Makina Teknolojileri Sanayi Ve Ticaret A.Ş.", "sektor": "Elektronik teknoloji"},
    "MAKTK": {"firma": "Makina Takım Endüstrisi A.Ş.", "sektor": "Üretici imalatı"},
    "MANAS": {"firma": "Manas Enerji Yönetimi Sanayi Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "MARBL": {"firma": "Tureks Turunc Madencilik Ic Ve Dis Ticaret A.S.", "sektor": "Enerji-dışı mineraller"},
    "MARKA": {"firma": "Marka Yatırım Holding A.Ş.", "sektor": "Dağıtım servisleri"},
    "MARMR": {"firma": "Marmara Holding As", "sektor": "Finans"},
    "MARTI": {"firma": "Martı Otel İşletmeleri A.Ş.", "sektor": "Tüketici hizmetleri"},
    "MAVI": {"firma": "Mavi Giyim Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "MCARD": {"firma": "Metropal Kurumsal Hizmetler A.S.", "sektor": "Ticari hizmetler"},
    "MEDTR": {"firma": "Meditera Tıbbi Malzeme Sanayi Ve Ticaret A.Ş.", "sektor": "Sağlık teknolojisi"},
    "MEGAP": {"firma": "Mega Polietilen Köpük Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "MEGMT": {"firma": "Mega Metal Sanayi Ve Ticaret A.S.", "sektor": "Enerji-dışı mineraller"},
    "MEKAG": {"firma": "Meka Global Makine Imalat Sanayi Ve Ticaret A.S.", "sektor": "Üretici imalatı"},
    "MEPET": {"firma": "Mepet Metro Petrol Ve Tesisleri Sanayi Ticaret A.Ş.", "sektor": "Perakende satış"},
    "MERCN": {"firma": "Mercan Kimya Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "MERIT": {"firma": "Merit Turizm Yatırım Ve İşletme A.Ş.", "sektor": "Tüketici hizmetleri"},
    "MERKO": {"firma": "Merko Gıda Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "METRO": {"firma": "Metro Ticari Ve Mali Yatırımlar Holding A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "MEYSU": {"firma": "Meysu Gida Sanayi Ve Ticaret A.S.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "MGROS": {"firma": "Migros Ticaret A.Ş.", "sektor": "Perakende satış"},
    "MHRGY": {"firma": "Mhr Gayrimenkul Yatirim Ortakligi Anonim Sirketi", "sektor": "Finans"},
    "MIATK": {"firma": "Mia Teknoloji A.Ş.", "sektor": "Teknoloji hizmetleri"},
    "MMCAS": {"firma": "Mmc Sanayi Ve Ticari Yatırımlar A.Ş.", "sektor": "Taşımacılık"},
    "MNDRS": {"firma": "Menderes Tekstil Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "MNDTR": {"firma": "Mondi Turkey Oluklu Mukavva Kağıt Ve Ambalaj Sanayi A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "MOBTL": {"firma": "Mobiltel İletişim Hizmetleri Sanayi Ve Ticaret A.Ş.", "sektor": "Dağıtım servisleri"},
    "MOGAN": {"firma": "Mogan Enerji Yatirim Holding", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "MOPAS": {"firma": "Mopas Marketcilik Gida Sanayi Ve Ticaret A.S.", "sektor": "Perakende satış"},
    "MPARK": {"firma": "Mlp Sağlık Hizmetleri A.Ş.", "sektor": "Sağlık hizmetleri"},
    "MRGYO": {"firma": "Martı Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "MRSHL": {"firma": "Marshall Boya Ve Vernik Sanayii A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "MSGYO": {"firma": "Mistral Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "MTRKS": {"firma": "Matriks Finansal Teknolojiler A.Ş.", "sektor": "Teknoloji hizmetleri"},
    "MTRYO": {"firma": "Metro Yatırım Ortaklığı A.Ş.", "sektor": "Çeşitli Hizmetler"},
    "MZHLD": {"firma": "Mazhar Zorlu Holding A.Ş.", "sektor": "Üretici imalatı"},
    "NATEN": {"firma": "Naturel Yenilenebilir Enerji Ticaret A.Ş.", "sektor": "Endüstriyel hizmetler"},
    "NETAS": {"firma": "Netaş Telekomünikasyon A.Ş.", "sektor": "Teknoloji hizmetleri"},
    "NETCD": {"firma": "Netcad Yazilim A.S.", "sektor": "Teknoloji hizmetleri"},
    "NIBAS": {"firma": "Niğbaş Niğde Beton Sanayi Ve Ticaret A.Ş.", "sektor": "Endüstriyel hizmetler"},
    "NTGAZ": {"firma": "Naturelgaz Sanayi Ve Ticaret A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "NTHOL": {"firma": "Net Holding A.Ş.", "sektor": "Tüketici hizmetleri"},
    "NUGYO": {"firma": "Nurol Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "NUHCM": {"firma": "Nuh Çimento Sanayi A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "OBAMS": {"firma": "Oba Makarnacilik Sanayi Ve Ticaret A. S.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "OBASE": {"firma": "Obase Bilgisayar Ve Danışmanlık Hizmetleri Ticaret A.Ş.", "sektor": "Teknoloji hizmetleri"},
    "ODAS": {"firma": "Odaş Elektrik Üretim Sanayi Ticaret A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "ODINE": {"firma": "Odine Solutions Teknoloji Ticaret Ve Sanayi As", "sektor": "Teknoloji hizmetleri"},
    "OFSYM": {"firma": "Ofis Yem Gida Sanayi Ve Ticaret A.S.", "sektor": "İşlenebilen endüstriler"},
    "ONCSM": {"firma": "Oncosem Onkolojik Sistemler Sanayi Ve Ticaret A.Ş.", "sektor": "Sağlık teknolojisi"},
    "ONRYT": {"firma": "Onur Yuksek Teknoloji As", "sektor": "Elektronik teknoloji"},
    "ORCAY": {"firma": "Orçay Ortaköy Çay Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "ORGE": {"firma": "Orge Enerji Elektrik Taahhüt A.Ş.", "sektor": "Endüstriyel hizmetler"},
    "ORMA": {"firma": "Orma Orman Mahsulleri İntegre Sanayi Ve Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "OSMEN": {"firma": "Osmanlı Yatırım Menkul Değerler A.Ş.", "sektor": "Finans"},
    "OSTIM": {"firma": "Ostim Endüstriyel Yatırımlar Ve İşletme A.Ş.", "sektor": "Çeşitli Hizmetler"},
    "OTKAR": {"firma": "Otokar Otomotiv Ve Savunma Sanayi A.Ş.", "sektor": "Dayanıklı tüketim malları"},
    "OTTO": {"firma": "Otto Holding A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "OYAKC": {"firma": "Oyak Çimento Fabrikaları A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "OYAYO": {"firma": "Oyak Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "OYLUM": {"firma": "Oylum Sınai Yatırımlar A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "OYYAT": {"firma": "Oyak Yatırım Menkul Değerler A.Ş.", "sektor": "Finans"},
    "OZATD": {"firma": "Ozata Denızcılık Sanayı Ve Tıcaret As", "sektor": "Üretici imalatı"},
    "OZGYO": {"firma": "Özderici Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "OZKGY": {"firma": "Özak Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "OZRDN": {"firma": "Özerden Plastik Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "OZSUB": {"firma": "Özsu Balık Üretim A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "OZYSR": {"firma": "Ozyasar Tel Ve Galvanizleme Sanayi Anonim Sirketi", "sektor": "Üretici imalatı"},
    "PAGYO": {"firma": "Panora Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "PAHOL": {"firma": "Pasıfık Holdıng A.S", "sektor": "Çeşitli Hizmetler"},
    "PAMEL": {"firma": "Pamel Yenilenebilir Elektrik Üretim A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "PAPIL": {"firma": "Papilon Savunma Teknoloji Ve Ticaret A.Ş.", "sektor": "Elektronik teknoloji"},
    "PARSN": {"firma": "Parsan Makina Parçaları Sanayii A.Ş.", "sektor": "Üretici imalatı"},
    "PASEU": {"firma": "Pasifik Eurasia Lojistik Dis Ticaret As", "sektor": "Taşımacılık"},
    "PATEK": {"firma": "Pasifik Teknoloji As", "sektor": "Teknoloji hizmetleri"},
    "PCILT": {"firma": "Pc İletişim Ve Medya Hizmetleri Sanayi Ticaret A.Ş.", "sektor": "Ticari hizmetler"},
    "PEKGY": {"firma": "Peker Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "PENGD": {"firma": "Penguen Gıda Sanayi A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "PENTA": {"firma": "Penta Teknoloji Ürünleri Dağıtım Ticaret A.Ş.", "sektor": "Dağıtım servisleri"},
    "PETKM": {"firma": "Petkim Petrokimya Holding A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "PETUN": {"firma": "Pınar Entegre Et Ve Un Sanayii A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "PGSUS": {"firma": "Pegasus Hava Taşımacılığı A.Ş.", "sektor": "Taşımacılık"},
    "PINSU": {"firma": "Pınar Su Ve İçecek Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "PKART": {"firma": "Plastikkart Akıllı Kart İletişim Sistemleri Sanayi Ve Ticaret A.Ş.", "sektor": "Ticari hizmetler"},
    "PKENT": {"firma": "Petrokent Turizm A.Ş.", "sektor": "Tüketici hizmetleri"},
    "PLTUR": {"firma": "Platform Turizm Taşımacılık Gıda İnşaat Temizlik Hizmetleri Sanayi Ve Ticaret A.Ş.", "sektor": "Taşımacılık"},
    "PNLSN": {"firma": "Panelsan Çatı Cephe Sistemleri Sanayi Ve Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "PNSUT": {"firma": "Pınar Süt Mamulleri Sanayii A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "POLHO": {"firma": "Polisan Holding A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "POLTK": {"firma": "Politeknik Metal Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "PRDGS": {"firma": "Pardus Girişim Sermayesi Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "PRKAB": {"firma": "Türk Prysmian Kablo Ve Sistemleri A.Ş.", "sektor": "Üretici imalatı"},
    "PRKME": {"firma": "Park Elektrik Üretim Madencilik Sanayi Ve Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "PRZMA": {"firma": "Prizma Pres Matbaacılık Yayıncılık Sanayi Ve Ticaret A.Ş.", "sektor": "Ticari hizmetler"},
    "PSDTC": {"firma": "Pergamon Status Dış Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "PSGYO": {"firma": "Pasifik Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "QNBFK": {"firma": "Qnb Finansal Kiralama A.S.", "sektor": "Finans"},
    "QNBTR": {"firma": "Qnb Bank As", "sektor": "Finans"},
    "QUAGR": {"firma": "Qua Granıte Hayal Yapı Ve Ürünleri Sanayi Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "RALYH": {"firma": "Ral Yatırım Holding A.Ş.", "sektor": "Endüstriyel hizmetler"},
    "RAYSG": {"firma": "Ray Sigorta A.Ş.", "sektor": "Finans"},
    "REEDR": {"firma": "Reeder Teknoloji Sanayi Ve Ticaret A.S.", "sektor": "Teknoloji hizmetleri"},
    "RGYAS": {"firma": "Rönesans Gayrimenkul Yatırım A.Ş.", "sektor": "Finans"},
    "RNPOL": {"firma": "Rainbow Polikarbonat Sanayi Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "RODRG": {"firma": "Rodrigo Tekstil Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "RTALB": {"firma": "Rta Laboratuvarları Biyolojik Ürünler İlaç Ve Makine Sanayi Ticaret A.Ş.", "sektor": "Sağlık teknolojisi"},
    "RUBNS": {"firma": "Rubenis Tekstil Sanayi Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "RUZYE": {"firma": "Ruzy Madencilik Ve Enerji Yatirimlari Sanayi Ve Ticaret A.S.", "sektor": "İşlenebilen endüstriler"},
    "RYGYO": {"firma": "Reysaş Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "RYSAS": {"firma": "Reysaş Taşımacılık Ve Lojistik Ticaret A.Ş.", "sektor": "Taşımacılık"},
    "SAFKR": {"firma": "Safkar Ege Soğutmacılık Klima Soğuk Hava Tesisleri İhracat İthalat Sanayi Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "SAHOL": {"firma": "Hacı Ömer Sabancı Holding A.Ş.", "sektor": "Finans"},
    "SAMAT": {"firma": "Saray Matbaacılık Kağıtçılık Kırtasiyecilik Ticaret Ve Sanayi A.Ş.", "sektor": "Ticari hizmetler"},
    "SANEL": {"firma": "San-El Mühendislik Elektrik Taahhüt Sanayi Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "SANFM": {"firma": "Sanifoam Endüstri Ve Tüketim Ürünleri Sanayi Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "SANKO": {"firma": "Sanko Pazarlama İthalat İhracat A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "SARKY": {"firma": "Sarkuysan Elektrolitik Bakır Sanayi Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "SASA": {"firma": "Sasa Polyester Sanayi A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "SAYAS": {"firma": "Say Yenilenebilir Enerji Ekipmanları Sanayi Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "SDTTR": {"firma": "Sdt Uzay Ve Savunma Teknolojileri A.Ş.", "sektor": "Elektronik teknoloji"},
    "SEGMN": {"firma": "Segmen Kardesler Gida Uretim Ve Ambalaj Sanayi As", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "SEGYO": {"firma": "Şeker Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "SEKFK": {"firma": "Şeker Finansal Kiralama A.Ş.", "sektor": "Finans"},
    "SEKUR": {"firma": "Sekuro Plastik Ambalaj Sanayi A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "SELEC": {"firma": "Selçuk Ecza Deposu Ticaret Ve Sanayi A.Ş.", "sektor": "Dağıtım servisleri"},
    "SELVA": {"firma": "Selva Gıda Sanayi A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "SERNT": {"firma": "Seranit Granit Seramik Sanayi Ve Ticaret A.S.", "sektor": "Üretici imalatı"},
    "SEYKM": {"firma": "Seyitler Kimya Sanayi A.Ş.", "sektor": "Sağlık teknolojisi"},
    "SILVR": {"firma": "Silverline Endüstri Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "SISE": {"firma": "Türkiye Şişe Ve Cam Fabrikaları A.Ş.", "sektor": "Dayanıklı tüketim malları"},
    "SKBNK": {"firma": "Şekerbank T.A.Ş.", "sektor": "Finans"},
    "SKTAS": {"firma": "Söktaş Tekstil Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "SKYLP": {"firma": "Skyalp Finansal Teknolojiler Ve Danismanlik A.S", "sektor": "Ticari hizmetler"},
    "SKYMD": {"firma": "Seker Yatirim Menkul Degerler A.S.", "sektor": "Finans"},
    "SMART": {"firma": "Smartiks Yazılım A.Ş.", "sektor": "Teknoloji hizmetleri"},
    "SMRTG": {"firma": "Smart Güneş Enerjisi Teknolojileri Araştırma Geliştirme Üretim Sanayi Ve Ticaret A.Ş.", "sektor": "Elektronik teknoloji"},
    "SMRVA": {"firma": "Sumer Varlik Yonetim A.S.", "sektor": "Ticari hizmetler"},
    "SNGYO": {"firma": "Sinpaş Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "SNICA": {"firma": "Sanica Isı Sanayi A.Ş.", "sektor": "Üretici imalatı"},
    "SNPAM": {"firma": "Sönmez Pamuklu Sanayii A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "SODSN": {"firma": "Sodaş Sodyum Sanayii A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "SOKE": {"firma": "Söke Değirmencilik Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "SOKM": {"firma": "Şok Marketler Ticaret A.Ş.", "sektor": "Perakende satış"},
    "SONME": {"firma": "Sönmez Filament Sentetik İplik Ve Elyaf Sanayi A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "SRVGY": {"firma": "Servet Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "SUMAS": {"firma": "Sumaş Suni Tahta Ve Mobilya Sanayi A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "SUNTK": {"firma": "Sun Tekstil Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "SURGY": {"firma": "Sur Tatil Evleri Gayrimenkul Yatirim Ortakligi A.S.", "sektor": "Finans"},
    "SUWEN": {"firma": "Suwen Tekstil Sanayi Pazarlama A.Ş.", "sektor": "Perakende satış"},
    "SVGYO": {"firma": "Savur Gayrimenkul Yatirim Ortakligi A.S", "sektor": "Finans"},
    "TABGD": {"firma": "Tab Gida Sanayi Ve Ticaret A.S.", "sektor": "Tüketici hizmetleri"},
    "TARKM": {"firma": "Tarkim Bitki Koruma Sanayi Ve Ticaret A.S.", "sektor": "İşlenebilen endüstriler"},
    "TATEN": {"firma": "Tatlipinar Enerji Uretim A.S.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "TATGD": {"firma": "Tat Gıda Sanayi A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "TAVHL": {"firma": "Tav Havalimanları Holding A.Ş.", "sektor": "Taşımacılık"},
    "TBORG": {"firma": "Türk Tuborg Bira Ve Malt Sanayii A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "TCELL": {"firma": "Turkcell İletişim Hizmetleri A.Ş.", "sektor": "İletişim"},
    "TCKRC": {"firma": "Kirac Galvaniz Telekominikasyon Metal Makine Insaat Elektrik Sanayi Ve Ticaret As", "sektor": "Üretici imalatı"},
    "TDGYO": {"firma": "Trend Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "TEHOL": {"firma": "Tera Yatirim Teknoloji Holding A.S.", "sektor": "Finans"},
    "TEKTU": {"firma": "Tek-Art İnşaat Ticaret Turizm Sanayi Ve Yatırımlar A.Ş.", "sektor": "Tüketici hizmetleri"},
    "TERA": {"firma": "Tera Yatırım Menkul Değerler A.Ş.", "sektor": "Finans"},
    "TEZOL": {"firma": "Europap Tezol Kağıt Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "TGSAS": {"firma": "Tgs Dış Ticaret A.Ş.", "sektor": "Dağıtım servisleri"},
    "THYAO": {"firma": "Türk Hava Yolları A.O.", "sektor": "Taşımacılık"},
    "TKFEN": {"firma": "Tekfen Holding A.Ş.", "sektor": "Endüstriyel hizmetler"},
    "TKNSA": {"firma": "Teknosa İç Ve Dış Ticaret A.Ş.", "sektor": "Perakende satış"},
    "TLMAN": {"firma": "Trabzon Liman İşletmeciliği A.Ş.", "sektor": "Taşımacılık"},
    "TMPOL": {"firma": "Temapol Polimer Plastik Ve İnşaat Sanayi Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "TMSN": {"firma": "Tümosan Motor Ve Traktör Sanayi A.Ş.", "sektor": "Üretici imalatı"},
    "TNZTP": {"firma": "Tapdi Oksijen Özel Sağlık Ve Eğitim Hizmetleri Sanayi Ticaret A.Ş.", "sektor": "Sağlık hizmetleri"},
    "TOASO": {"firma": "Tofaş Türk Otomobil Fabrikası A.Ş.", "sektor": "Dayanıklı tüketim malları"},
    "TRALT": {"firma": "Turk Altin Isletmeleri A.S.", "sektor": "Enerji-dışı mineraller"},
    "TRCAS": {"firma": "Turcas Petrol A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "TRENJ": {"firma": "Tr Dogal Enerji Kaynaklari Arastirma Ve Uretim Anonim Sirketi", "sektor": "Enerji mineralleri"},
    "TRGYO": {"firma": "Torunlar Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "TRHOL": {"firma": "Tera Financial Investments Holding A.S.", "sektor": "Finans"},
    "TRILC": {"firma": "Turk İlaç Ve Serum Sanayi A.Ş.", "sektor": "Sağlık teknolojisi"},
    "TRMET": {"firma": "Tr Anadolu Metal Madencilik Isletmeleri Anonim Sirketi", "sektor": "Enerji-dışı mineraller"},
    "TSGYO": {"firma": "Tskb Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "TSKB": {"firma": "Türkiye Sınai Kalkınma Bankası A.Ş.", "sektor": "Finans"},
    "TSPOR": {"firma": "Trabzonspor Sportif Yatırım Ve Futbol İşletmeciliği Ticaret A.Ş.", "sektor": "Tüketici hizmetleri"},
    "TTKOM": {"firma": "Türk Telekomünikasyon A.Ş.", "sektor": "İletişim"},
    "TTRAK": {"firma": "Türk Traktör Ve Ziraat Makineleri A.Ş.", "sektor": "Üretici imalatı"},
    "TUCLK": {"firma": "Tuğçelik Alüminyum Ve Metal Mamülleri Sanayi Ve Ticaret A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "TUKAS": {"firma": "Tukaş Gıda Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "TUPRS": {"firma": "Tüpraş-Türkiye Petrol Rafinerileri A.Ş.", "sektor": "Enerji mineralleri"},
    "TUREX": {"firma": "Tureks Turizm Taşımacılık A.Ş.", "sektor": "Finans"},
    "TURGG": {"firma": "Türker Proje Gayrimenkul Ve Yatırım Geliştirme A.Ş.", "sektor": "Finans"},
    "TURSG": {"firma": "Türkiye Sigorta A.Ş.", "sektor": "Finans"},
    "UCAYM": {"firma": "Ucay Muhendislik Enerji Ve Iklimlendirme Teknolojileri", "sektor": "Endüstriyel hizmetler"},
    "UFUK": {"firma": "Ufuk Yatırım Yönetim Ve Gayrimenkul A.Ş.", "sektor": "Finans"},
    "ULAS": {"firma": "Ulaşlar Turizm Yatırımları Ve Dayanıklı Tüketim Malları Ticaret Pazarlama A.Ş.", "sektor": "Tüketici hizmetleri"},
    "ULKER": {"firma": "Ülker Bisküvi Sanayi A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "ULUFA": {"firma": "Ulusal Faktoring A.Ş.", "sektor": "Finans"},
    "ULUSE": {"firma": "Ulusoy Elektrik İmalat Taahhüt Ve Ticaret A.Ş.", "sektor": "Üretici imalatı"},
    "ULUUN": {"firma": "Ulusoy Un Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "UNLU": {"firma": "Ünlü Yatırım Holding A.Ş.", "sektor": "Finans"},
    "USAK": {"firma": "Uşak Seramik Sanayi A.Ş.", "sektor": "Üretici imalatı"},
    "VAKBN": {"firma": "Türkiye Vakıflar Bankası T.A.O.", "sektor": "Finans"},
    "VAKFA": {"firma": "Vakıf Faktoring A.Ş.", "sektor": "Finans"},
    "VAKFN": {"firma": "Vakıf Finansal Kiralama A.Ş.", "sektor": "Finans"},
    "VAKKO": {"firma": "Vakko Tekstil Ve Hazır Giyim Sanayi İşletmeleri A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "VANGD": {"firma": "Vanet Gıda Sanayi İç Ve Dış Ticaret A.Ş.", "sektor": "Dağıtım servisleri"},
    "VBTYZ": {"firma": "Vbt Yazılım A.Ş.", "sektor": "Teknoloji hizmetleri"},
    "VERUS": {"firma": "Verusa Holding A.Ş.", "sektor": "Finans"},
    "VESBE": {"firma": "Vestel Beyaz Eşya Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı tüketim malları"},
    "VESTL": {"firma": "Vestel Elektronik Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı tüketim malları"},
    "VKFYO": {"firma": "Vakıf Menkul Kıymet Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "VKGYO": {"firma": "Vakıf Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "VKING": {"firma": "Viking Kağıt Ve Selüloz A.Ş.", "sektor": "Dayanıklı olmayan tüketici ürünleri"},
    "VRGYO": {"firma": "Vera Konsept Gayrimenkul Yatirim Ortakligi A.S.", "sektor": "Finans"},
    "VSNMD": {"firma": "Visne Madencilik Uretim Sanayi Ve Ticaret As", "sektor": "Enerji-dışı mineraller"},
    "YAPRK": {"firma": "Yaprak Süt Ve Besi Çiftlikleri Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "YATAS": {"firma": "Yataş Yatak Ve Yorgan Sanayi Ticaret A.Ş.", "sektor": "Dağıtım servisleri"},
    "YAYLA": {"firma": "Yayla Enerji Üretim Turizm Ve İnşaat Ticaret A.Ş.", "sektor": "Endüstriyel hizmetler"},
    "YBTAS": {"firma": "Yibitaş Yozgat İşçi Birliği İnşaat Malzemeleri Ticaret Ve Sanayi A.Ş.", "sektor": "Enerji-dışı mineraller"},
    "YEOTK": {"firma": "Yeo Teknoloji Enerji Ve Endüstri A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "YESIL": {"firma": "Yeşil Yatırım Holding A.Ş.", "sektor": "Çeşitli Hizmetler"},
    "YGGYO": {"firma": "Yeni Gimat Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
    "YIGIT": {"firma": "Yigit Aku Malzemeleri Nakliyat Turizm Insaat Sanayi Ve Ticaret", "sektor": "Üretici imalatı"},
    "YKBNK": {"firma": "Yapı Ve Kredi Bankası A.Ş.", "sektor": "Finans"},
    "YKSLN": {"firma": "Yükselen Çelik A.Ş.", "sektor": "Dağıtım servisleri"},
    "YONGA": {"firma": "Yonga Mobilya Sanayi Ve Ticaret A.Ş.", "sektor": "Dayanıklı tüketim malları"},
    "YUNSA": {"firma": "Yünsa Yünlü Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "YYAPI": {"firma": "Yeşil Yapı Endüstrisi A.Ş.", "sektor": "Endüstriyel hizmetler"},
    "YYLGD": {"firma": "Yayla Agro Gıda Sanayi Ve Ticaret A.Ş.", "sektor": "İşlenebilen endüstriler"},
    "ZEDUR": {"firma": "Zedur Enerji Elektrik Üretim A.Ş.", "sektor": "Tüketici hizmetleri"},
    "ZERGY": {"firma": "Zeray Gayrimenkul Yatirim Ortakligi As", "sektor": "Finans"},
    "ZGYO": {"firma": "Z Gayrimenkul Yatirim Ortakligi A.S.", "sektor": "Finans"},
    "ZOREN": {"firma": "Zorlu Enerji Elektrik Üretim A.Ş.", "sektor": "Elektrik, Su, Gaz Hizmetleri"},
    "ZRGYO": {"firma": "Ziraat Gayrimenkul Yatırım Ortaklığı A.Ş.", "sektor": "Finans"},
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
    komisyon_orani = st.number_input("Komisyon (Binde)", min_value=0.0, value=0.5, step=0.1) / 1000
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
        butce = st.number_input("Toplam Bütçe (TL)", min_value=1.0, value=10000.0, step=1000.0, format="%.2f")

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
        ihtiyac_nakit = st.number_input("Hesaba Geçmesi Gereken NET Nakit (TL)", min_value=1.0, value=50000.0, format="%.2f")

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
        st.info("Borsa getirinizi mevduat fırsat maliyetiyle karşılaştırır. Faiz getirisi **%17,5 stopaj** kesintisi sonrası net hesaplanır.")
        alis_tarihi = st.date_input("Alış Tarihi")
        alis_fiyati_r = st.number_input("Ortalama Alış Fiyatı (TL)", min_value=0.01, value=100.0, format="%.2f")
        lot_miktari = st.number_input("Lot Sayısı", min_value=1, value=100)
        satis_tarihi = st.date_input("Satış Tarihi")
        satis_fiyati_r = st.number_input("Satış Fiyatı (TL)", min_value=0.01, value=120.0, format="%.2f")
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
                faiz_kar = alis_m * faiz_kullanim * gun / 365 * 0.825  # %17,5 stopaj sonrası net
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

    faiz_portfoy = st.number_input("Karşılaştırma Faizi (%/yıl)", min_value=0.0, value=45.0, step=0.5, key="faiz_portfoy") / 100

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
                faiz_getiri = p["alis_maliyeti"] * faiz_portfoy * gun / 365 * 0.825  # %17,5 stopaj sonrası net
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
