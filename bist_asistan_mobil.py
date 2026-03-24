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

# --- SAYFA AYARLARI (MOBİL UYUMLU) ---
st.set_page_config(
    page_title="BIST Asistan",
    layout="centered",           # ← wide → centered (mobilde kritik)
    initial_sidebar_state="collapsed"  # ← mobilde sidebar kapalı başlar
)

# Mobil için ekstra CSS
st.markdown("""
<style>
    /* Butonları tam genişlik yap */
    .stButton > button {
        width: 100%;
        padding: 0.6rem;
        font-size: 1rem;
    }
    /* Input alanlarını büyüt (dokunmatik için) */
    .stNumberInput input, .stSelectbox select {
        font-size: 1rem !important;
        min-height: 44px;
    }
    /* Başlığı küçült */
    h1 { font-size: 1.4rem !important; }
    h2 { font-size: 1.2rem !important; }
    h3 { font-size: 1.1rem !important; }
    /* Tablo taşmasını önle */
    .stTable { overflow-x: auto; }
    /* Sidebar toggle daha erişilebilir */
    section[data-testid="stSidebar"] { min-width: 280px; }
</style>
""", unsafe_allow_html=True)

# --- STATİK VERİTABANI ---
BIST_HISSELER = {
    "THYAO": "Ulaştırma", "PGSUS": "Ulaştırma", "TAVHL": "Ulaştırma",
    "TUPRS": "Enerji", "ASTOR": "Enerji", "ENJSA": "Enerji",
    "AKBNK": "Banka", "GARAN": "Banka", "ISCTR": "Banka", "YKBNK": "Banka",
    "EREGL": "Demir Çelik", "KRDMD": "Demir Çelik",
    "FROTO": "Otomotiv", "TOASO": "Otomotiv", "DOAS": "Otomotiv",
    "BIMAS": "Perakende", "MGROS": "Perakende", "SOKM": "Perakende",
    "TCELL": "İletişim", "TTKOM": "İletişim",
    "ASELS": "Savunma", "SASA": "Kimya", "HEKTS": "Kimya",
    "KCHOL": "Holding", "SAHOL": "Holding", "SISE": "Cam"
}

# --- LOG HAFIZASI ---
if 'logs' not in st.session_state:
    st.session_state.logs = []

def log_ekle(islem_tipi, hisse, detay):
    st.session_state.logs.append({
        "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "İşlem": islem_tipi,
        "Hisse": hisse,
        "Detay": detay
    })

# --- YAN MENÜ (sidebar) ---
with st.sidebar:
    st.header("⚙️ Ayarlar")
    komisyon_orani = st.number_input("Komisyon (Binde)", min_value=0.0, value=2.0, step=0.1) / 1000
    bsmv_orani = st.number_input("BSMV (%)", min_value=0.0, value=5.0, step=1.0) / 100
    efektif_komisyon = komisyon_orani * (1 + bsmv_orani)
    st.info(f"Net Kesinti: **%{efektif_komisyon*100:.4f}**")
    mevduat_faizi = st.number_input("Mevduat Faizi (%/yıl)", value=45.0, step=1.0) / 100

# Sidebar kapalıysa bile efektif_komisyon tanımlı kalsın
if 'efektif_komisyon' not in dir():
    komisyon_orani = 2.0 / 1000
    bsmv_orani = 5.0 / 100
    efektif_komisyon = komisyon_orani * (1 + bsmv_orani)
    mevduat_faizi = 45.0 / 100

# --- ANA EKRAN ---
st.title("📈 BIST Yatırımcı Asistanı")
st.caption("Komisyon dahil maliyet, paçal ve kâr analizi")

tab_alis, tab_satis, tab_portfoy, tab_log = st.tabs([
    "🟢 Alış", "🔴 Satış", "💼 Portföy", "📋 Log"
])

# ==========================================
# 🟢 ALIŞ SEKMESİ
# ==========================================
with tab_alis:
    # horizontal=True KALDIRILDI → dikey radio (mobilde taşmaz)
    alis_modu = st.radio(
        "İşlem Tipi:",
        ["💰 Param Var → Kaç Lot?", "📦 Lot Alacağım → Ne Kadar Para?", "📉 Maliyet Düşür (Paçal)"]
    )
    st.divider()

    # --- MOD 1: Miktardan Adete ---
    if alis_modu == "💰 Param Var → Kaç Lot?":
        hisse = st.selectbox("Hisse", options=list(BIST_HISSELER.keys()), key="alis_hisse_1")
        fiyat = st.number_input("Başlangıç Fiyatı (TL)", min_value=0.01, value=100.00, step=0.01, format="%.2f")
        st.caption(f"📌 Tick boyutu: **{get_tick_size(fiyat):.2f} TL**")
        butce = st.number_input("Toplam Bütçe (TL)", min_value=1.0, value=10000.0, step=1000.0)

        # Kademe ayarları - expander ile gizlendi (mobilde temiz görünüm)
        with st.expander("⚙️ Kademe Ayarları (opsiyonel)"):
            kademe_sayisi = st.number_input("Kademe Sayısı", min_value=1, max_value=20, value=1, key="k1")
            fiyat_adimi_tick = st.number_input("Kademeler Arası (Tick)", min_value=1, value=1, key="t1") if kademe_sayisi > 1 else 0
            dagilim_mantigi = st.selectbox("Dağılım", ["Eşit", "Piramit (Düştükçe Artan)"], key="d1") if kademe_sayisi > 1 else "Eşit"

        if st.button("📊 Alış Planı Oluştur", type="primary", key="btn_alis1"):
            agirliklar = [1]*kademe_sayisi if "Eşit" in dagilim_mantigi else list(range(1, kademe_sayisi+1))
            toplam_agirlik = sum(agirliklar)
            plan, toplam_lot, toplam_maliyet = [], 0, 0
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
                plan.append({"Kademe": f"{i+1}", "Fiyat ₺": f"{kademe_fiyati:.2f}", "Lot": lot, "Maliyet ₺": round(gercek, 2)})

            st.dataframe(pd.DataFrame(plan), use_container_width=True, hide_index=True)
            st.success(f"✅ **{toplam_lot} Lot** | Kalan: **{round(butce-toplam_maliyet,2)} TL**")
            log_ekle("ALIŞ→LOT", hisse, f"{butce}TL → {toplam_lot} lot")

    # --- MOD 2: Adetten Miktara ---
    elif alis_modu == "📦 Lot Alacağım → Ne Kadar Para?":
        hisse = st.selectbox("Hisse", options=list(BIST_HISSELER.keys()), key="alis_hisse_2")
        fiyat = st.number_input("Başlangıç Fiyatı (TL)", min_value=0.01, value=100.00, step=0.01, format="%.2f")
        st.caption(f"📌 Tick boyutu: **{get_tick_size(fiyat):.2f} TL**")
        hedef_lot = st.number_input("Hedef Lot Sayısı", min_value=1, value=100)

        with st.expander("⚙️ Kademe Ayarları (opsiyonel)"):
            kademe_sayisi = st.number_input("Kademe Sayısı", min_value=1, max_value=20, value=1, key="k2")
            fiyat_adimi_tick = st.number_input("Kademeler Arası (Tick)", min_value=1, value=1, key="t2") if kademe_sayisi > 1 else 0
            dagilim_mantigi = st.selectbox("Dağılım", ["Eşit", "Piramit (Düştükçe Artan)"], key="d2") if kademe_sayisi > 1 else "Eşit"

        if st.button("💵 Gereken Nakdi Hesapla", type="primary", key="btn_alis2"):
            agirliklar = [1]*kademe_sayisi if "Eşit" in dagilim_mantigi else list(range(1, kademe_sayisi+1))
            toplam_agirlik = sum(agirliklar)
            plan, toplam_para, kalan_lot = [], 0, hedef_lot
            kademe_fiyati = fiyat

            for i in range(kademe_sayisi):
                if i > 0:
                    kademe_fiyati = shift_price(kademe_fiyati, fiyat_adimi_tick, "down")
                if kademe_fiyati <= 0.01 and i > 0: break
                if i == kademe_sayisi - 1:
                    kademe_lot = kalan_lot
                else:
                    kademe_lot = math.floor(hedef_lot * (agirliklar[i] / toplam_agirlik))
                    kalan_lot -= kademe_lot
                maliyet = kademe_lot * kademe_fiyati * (1 + efektif_komisyon)
                toplam_para += maliyet
                plan.append({"Kademe": f"{i+1}", "Fiyat ₺": f"{kademe_fiyati:.2f}", "Lot": kademe_lot, "Nakit ₺": round(maliyet,2)})

            st.dataframe(pd.DataFrame(plan), use_container_width=True, hide_index=True)
            st.success(f"✅ **{hedef_lot} Lot** için gerekli nakit: **{round(toplam_para,2)} TL**")
            log_ekle("LOT→NAKİT", hisse, f"{hedef_lot} lot → {round(toplam_para,2)} TL")

    # --- MOD 3: Paçal ---
    else:
        mevcut_lot = st.number_input("Elinizdeki Lot", min_value=1, value=100)
        mevcut_maliyet = st.number_input("Mevcut Ortalama Maliyet (TL)", min_value=0.01, value=120.0, format="%.2f")
        guncel_fiyat = st.number_input("Şu Anki Fiyat (TL)", min_value=0.01, value=100.0, format="%.2f")
        hedef_maliyet = st.number_input("Hedef Maliyet (TL)", min_value=0.01, value=110.0, format="%.2f")

        if st.button("🔢 Paçal Denklemini Çöz", type="primary", key="btn_pacal"):
            maliyet_lot = guncel_fiyat * (1 + efektif_komisyon)
            if hedef_maliyet >= mevcut_maliyet:
                st.error("Hedef maliyet, mevcut maliyetten düşük olmalı!")
            elif hedef_maliyet <= maliyet_lot:
                st.error(f"Hedefe matematik olarak ulaşılamaz. Min. fiyat: {round(maliyet_lot,2)} TL")
            else:
                gerekli_lot = math.ceil((mevcut_lot * (mevcut_maliyet - hedef_maliyet)) / (hedef_maliyet - maliyet_lot))
                gerekli_para = gerekli_lot * maliyet_lot
                st.success(f"✅ **{gerekli_lot} Lot** daha almalısınız")
                st.info(f"Gerekli yeni yatırım: **{round(gerekli_para,2)} TL**")
                log_ekle("PAÇAL", "-", f"Hedef {hedef_maliyet} TL → {gerekli_lot} lot")

# ==========================================
# 🔴 SATIŞ SEKMESİ
# ==========================================
with tab_satis:
    satis_modu = st.radio(
        "İşlem Tipi:",
        ["💵 Ne Kadar Nakit Çekeceğim → Kaç Lot?", "📦 Elimdekini Satacağım → Ne Geçer?", "📊 Reel Kâr & Faiz Analizi"]
    )
    st.divider()

    if satis_modu == "💵 Ne Kadar Nakit Çekeceğim → Kaç Lot?":
        hisse_sat = st.selectbox("Hisse", options=list(BIST_HISSELER.keys()), key="sat1")
        fiyat_sat = st.number_input("Satış Fiyatı (TL)", min_value=0.01, value=150.00, step=0.01, format="%.2f")
        st.caption(f"📌 Tick: **{get_tick_size(fiyat_sat,'up'):.2f} TL**")
        ihtiyac_nakit = st.number_input("Hesaba Geçmesi Gereken NET Nakit (TL)", min_value=1.0, value=50000.0)

        with st.expander("⚙️ Kademe Ayarları (opsiyonel)"):
            kademe_sayisi_s = st.number_input("Kademe Sayısı", min_value=1, max_value=20, value=1, key="ks1")
            fiyat_adimi_s = st.number_input("Kademeler Arası (Tick)", min_value=1, value=1, key="ts1") if kademe_sayisi_s > 1 else 0
            dagilim_s = st.selectbox("Dağılım", ["Eşit", "Piramit (Çıktıkça Artan)"], key="ds1") if kademe_sayisi_s > 1 else "Eşit"

        if st.button("📊 Satış Planı Oluştur", type="primary", key="btn_sat1"):
            agirliklar = [1]*kademe_sayisi_s if "Eşit" in dagilim_s else list(range(1, kademe_sayisi_s+1))
            toplam_agirlik = sum(agirliklar)
            plan, toplam_lot, toplam_nakit = [], 0, 0
            kalan_hedef = ihtiyac_nakit
            kademe_fiyati = fiyat_sat

            for i in range(kademe_sayisi_s):
                if i > 0:
                    kademe_fiyati = shift_price(kademe_fiyati, fiyat_adimi_s, "up")
                net_lot = kademe_fiyati * (1 - efektif_komisyon)
                kademe_hedef = kalan_hedef if i == kademe_sayisi_s-1 else ihtiyac_nakit*(agirliklar[i]/toplam_agirlik)
                if i < kademe_sayisi_s-1: kalan_hedef -= kademe_hedef
                lot = math.ceil(kademe_hedef / net_lot)
                gercek = lot * net_lot
                toplam_lot += lot
                toplam_nakit += gercek
                plan.append({"Kad.": f"{i+1}", "Fiyat ₺": f"{kademe_fiyati:.2f}", "Lot": lot, "Net ₺": round(gercek,2)})

            st.dataframe(pd.DataFrame(plan), use_container_width=True, hide_index=True)
            st.warning(f"Satılması gereken: **{toplam_lot} Lot**")
            st.success(f"Hesabınıza geçecek: **{round(toplam_nakit,2)} TL**")
            log_ekle("SATIŞ→LOT", hisse_sat, f"Hedef {ihtiyac_nakit} TL → {toplam_lot} lot")

    elif satis_modu == "📦 Elimdekini Satacağım → Ne Geçer?":
        hisse_sat = st.selectbox("Hisse", options=list(BIST_HISSELER.keys()), key="sat2")
        fiyat_sat = st.number_input("Satış Fiyatı (TL)", min_value=0.01, value=150.00, step=0.01, format="%.2f")
        satilacak_lot = st.number_input("Satılacak Lot Sayısı", min_value=1, value=100)

        with st.expander("⚙️ Kademe Ayarları (opsiyonel)"):
            kademe_sayisi_s = st.number_input("Kademe Sayısı", min_value=1, max_value=20, value=1, key="ks2")
            fiyat_adimi_s = st.number_input("Kademeler Arası (Tick)", min_value=1, value=1, key="ts2") if kademe_sayisi_s > 1 else 0
            dagilim_s = st.selectbox("Dağılım", ["Eşit", "Piramit (Çıktıkça Artan)"], key="ds2") if kademe_sayisi_s > 1 else "Eşit"

        if st.button("💵 Ele Geçecek Tutarı Hesapla", type="primary", key="btn_sat2"):
            agirliklar = [1]*kademe_sayisi_s if "Eşit" in dagilim_s else list(range(1, kademe_sayisi_s+1))
            toplam_agirlik = sum(agirliklar)
            plan, toplam_nakit, kalan_lot = [], 0, satilacak_lot
            kademe_fiyati = fiyat_sat

            for i in range(kademe_sayisi_s):
                if i > 0:
                    kademe_fiyati = shift_price(kademe_fiyati, fiyat_adimi_s, "up")
                if i == kademe_sayisi_s-1:
                    kademe_lot = kalan_lot
                else:
                    kademe_lot = math.floor(satilacak_lot*(agirliklar[i]/toplam_agirlik))
                    kalan_lot -= kademe_lot
                net = kademe_lot * kademe_fiyati * (1 - efektif_komisyon)
                toplam_nakit += net
                plan.append({"Kad.": f"{i+1}", "Fiyat ₺": f"{kademe_fiyati:.2f}", "Lot": kademe_lot, "Net ₺": round(net,2)})

            st.dataframe(pd.DataFrame(plan), use_container_width=True, hide_index=True)
            st.success(f"**{satilacak_lot} Lot** → **{round(toplam_nakit,2)} TL** net")
            log_ekle("LOT→NAKİT SATIŞ", hisse_sat, f"{satilacak_lot} lot → {round(toplam_nakit,2)} TL")

    else:  # Reel kâr analizi
        st.info("Borsa getirinizi mevduat fırsat maliyetiyle karşılaştırır.")
        alis_tarihi = st.date_input("Alış Tarihi")
        alis_fiyati = st.number_input("Ortalama Alış Fiyatı (TL)", min_value=0.01, value=100.0)
        lot_miktari = st.number_input("Lot Sayısı", min_value=1, value=100)
        satis_tarihi = st.date_input("Satış Tarihi")
        satis_fiyati_r = st.number_input("Satış Fiyatı (TL)", min_value=0.01, value=120.0)
        st.caption(f"Faiz ayarı: **%{mevduat_faizi*100:.0f}** (Menüden değiştirin)")

        if st.button("📊 Reel Getiriyi Hesapla", type="primary", key="btn_reel"):
            gun = max((satis_tarihi - alis_tarihi).days, 1)
            if (satis_tarihi - alis_tarihi).days < 0:
                st.error("Satış tarihi alış tarihinden önce olamaz!")
            else:
                alis_m = lot_miktari * alis_fiyati * (1 + efektif_komisyon)
                satis_g = lot_miktari * satis_fiyati_r * (1 - efektif_komisyon)
                borsa_kar = satis_g - alis_m
                faiz_kar = alis_m * mevduat_faizi * gun / 365
                reel = borsa_kar - faiz_kar

                st.metric("Yatırım Süresi", f"{gun} gün")
                st.metric("Borsa Net Kârı", f"{round(borsa_kar,2)} TL")
                st.metric("Mevduat Alternatifi", f"{round(faiz_kar,2)} TL")

                if reel > 0:
                    st.success(f"🏆 Faizi yendiniz! **Reel Kâr: +{round(reel,2)} TL**")
                else:
                    st.error(f"⚠️ Faizin altında kaldınız. **Reel Kayıp: {round(reel,2)} TL**")
                log_ekle("REEL KAR", "-", f"{gun} gün, Borsa: {round(borsa_kar,2)}, Reel: {round(reel,2)}")

# ==========================================
# 💼 PORTFÖY SEKMESİ
# ==========================================
with tab_portfoy:
    st.header("Sektör Korumalı Sepet")
    toplam_butce = st.number_input("Toplam Yatırım (TL)", min_value=1000.0, value=100000.0, step=5000.0)
    secilen_hisseler = st.multiselect("Portföye Hisse Ekle", options=list(BIST_HISSELER.keys()))

    # Kâr/zarar alarmları - expander ile
    with st.expander("🔔 Alarm Ayarları"):
        hedef_kar = st.number_input("Kâr-Al Oranı (%)", min_value=1.0, value=20.0)
        zarar_kes = st.number_input("Zarar-Kes Oranı (%)", min_value=1.0, value=5.0)

    if secilen_hisseler:
        sektorler = [BIST_HISSELER[h] for h in secilen_hisseler]
        gorulmus = set()
        cakisan = set(x for x in sektorler if x in gorulmus or gorulmus.add(x))

        if cakisan:
            st.error(f"⚠️ Aynı sektörden birden fazla hisse var: **{', '.join(cakisan)}**")
        else:
            st.success("✅ Sektörel dağılım iyi!")
            st.markdown("**Bütçe Dağılımı (%)**")

            oranlar = {}
            # Mobil için 2 kolonlu yerleşim (3'ten daha iyi)
            cols = st.columns(2)
            for i, hisse in enumerate(secilen_hisseler):
                with cols[i % 2]:
                    oran = st.number_input(f"{hisse}", min_value=1, max_value=100,
                                           value=math.floor(100/len(secilen_hisseler)),
                                           key=f"oran_{hisse}")
                    oranlar[hisse] = oran

            toplam_oran = sum(oranlar.values())
            st.progress(min(toplam_oran, 100), text=f"Toplam: %{toplam_oran}")

            if toplam_oran != 100:
                st.warning(f"Toplam %100 olmalı. Şu an: %{toplam_oran}")
            else:
                if st.button("🧾 Alım Reçetesi Oluştur", type="primary"):
                    recete, toplam_h = [], 0
                    for hisse, oran in oranlar.items():
                        h_butce = toplam_butce * (oran / 100)
                        temsili = 50.0
                        maliyet = temsili * (1 + efektif_komisyon)
                        lot = math.floor(h_butce / maliyet)
                        harcama = lot * maliyet
                        toplam_h += harcama
                        recete.append({
                            "Hisse": hisse, "Sektör": BIST_HISSELER[hisse],
                            "Bütçe ₺": round(h_butce, 2), "Lot*": lot,
                            "Harcama ₺": round(harcama, 2)
                        })

                    st.dataframe(pd.DataFrame(recete), use_container_width=True, hide_index=True)
                    st.caption("*50₺ temsili fiyat üzerinden hesaplanmıştır.")
                    st.info(f"Kalan nakit: **{round(toplam_butce-toplam_h,2)} TL**")
                    st.write(f"🟢 Kâr-Al hedefi: **{round(toplam_h*(1+hedef_kar/100),2)} TL**")
                    st.write(f"🔴 Zarar-Kes sınırı: **{round(toplam_h*(1-zarar_kes/100),2)} TL**")
                    log_ekle("PORTFÖY", f"{len(secilen_hisseler)} hisse", f"Toplam: {round(toplam_h,2)} TL")

# ==========================================
# 📋 LOG SEKMESİ
# ==========================================
with tab_log:
    st.header("Geçmiş İşlemler")
    if st.session_state.logs:
        df = pd.DataFrame(st.session_state.logs)
        st.dataframe(df, use_container_width=True, hide_index=True)
        if st.button("🗑️ Kayıtları Temizle", type="secondary"):
            st.session_state.logs = []
            st.rerun()
    else:
        st.info("Henüz hesaplanmış işlem yok.")
