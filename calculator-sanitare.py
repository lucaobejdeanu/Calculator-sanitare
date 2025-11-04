import streamlit as st
import pandas as pd
import numpy as np
import math
from typing import List, Dict, Tuple
import plotly.graph_objects as go
import plotly.express as px

# ======================== CONFIGURARE PAGINĂ ========================
st.set_page_config(
    page_title="Calculator Instalații Sanitare - Ing. Luca Obejdeanu",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================== CONSTANTE ========================
G = 9.81  # gravitație m/s²

# ======================== CORELAȚIE DN - DIAMETRE SPECIFICE ========================
CORELARE_DN_DIAMETRE = {
    "Oțel": {
        15: "1/2\"",
        20: "3/4\"", 
        25: "1\"",
        32: "1 1/4\"",
        40: "1 1/2\"",
        50: "2\"",
        65: "2 1/2\"",
        80: "3\"",
        100: "4\"",
        125: "5\"",
        150: "6\""
    },
    "PPR": {
        10: "d16",
        15: "d20",
        20: "d25",
        25: "d32",
        32: "d40",
        40: "d50",
        50: "d63",
        65: "d75",
        80: "d90",
        100: "d110",
        125: "d125",
        150: "d160"
    },
    "PEX/Multistrat": {
        10: "16x2",
        12: "16x2",
        15: "20x2",
        20: "25x2.5",
        25: "32x3",
        32: "40x3.5",
        40: "50x4",
        50: "63x4.5"
    },
    "Cupru": {
        10: "12x1",
        12: "15x1",
        15: "18x1",
        20: "22x1",
        25: "28x1.5",
        32: "35x1.5",
        40: "42x1.5",
        50: "54x2",
        65: "76x2",
        80: "88.9x2",
        100: "108x2.5"
    },
    "PE-HD": {
        15: "d20",
        20: "d25",
        25: "d32",
        32: "d40",
        40: "d50",
        50: "d63",
        65: "d75",
        80: "d90",
        100: "d110",
        125: "d125",
        150: "d160",
        200: "d200"
    }
}

# ======================== BAZE DE DATE MATERIALE ========================
MATERIALE_CONDUCTE = {
    "PPR (Polipropilen)": {
        "rugozitate_mm": 0.0015,
        "diametre_mm": {10: 10, 15: 13.2, 20: 16.6, 25: 20.4, 32: 26.2, 40: 32.6, 
                       50: 40.8, 63: 51.4, 75: 61.2, 90: 73.6, 110: 90.0},
        "v_max": 2.0,
        "info": "Cel mai popular, rezistent la temperaturi până la 95°C"
    },
    "PPR cu fibră de sticlă": {
        "rugozitate_mm": 0.001,
        "diametre_mm": {20: 16.6, 25: 20.4, 32: 26.2, 40: 32.6, 50: 40.8, 
                       63: 51.4, 75: 61.2, 90: 73.6, 110: 90.0},
        "v_max": 2.0,
        "info": "PPR armat cu fibră, dilatare redusă cu 75%"
    },
    "PEX/Multistrat (Henco, KAN)": {
        "rugozitate_mm": 0.0015,
        "diametre_mm": {16: 12, 20: 16, 25: 20, 32: 26, 40: 32, 50: 40, 63: 50},
        "v_max": 2.0,
        "info": "Flexibil, montaj rapid, presare/compresie"
    },
    "Cupru": {
        "rugozitate_mm": 0.0015,
        "diametre_mm": {12: 10, 15: 13, 18: 16, 22: 20, 28: 26, 35: 33, 
                       42: 40, 54: 52, 76: 74, 108: 106},
        "v_max": 2.5,
        "info": "Premium, antibacterian, durată nelimitată"
    },
    "Inox ondulat": {
        "rugozitate_mm": 0.002,
        "diametre_mm": {16: 12, 20: 16, 25: 20, 32: 26, 40: 32, 50: 40},
        "v_max": 2.0,
        "info": "Flexibil, montaj rapid, fără fitinguri"
    },
    "PE-HD": {
        "rugozitate_mm": 0.002,
        "diametre_mm": {20: 14.4, 25: 20.4, 32: 26, 40: 32.6, 50: 40.8, 
                       63: 51.4, 75: 61.4, 90: 73.6, 110: 90, 125: 102.2, 
                       160: 130.8, 200: 163.6},
        "v_max": 2.5,
        "info": "Pentru branșamente, rezistent UV"
    },
    "Oțel zincat": {
        "rugozitate_mm": 0.15,
        "diametre_mm": {15: 16.0, 20: 21.7, 25: 27.3, 32: 36.0, 40: 41.9, 
                       50: 53.1, 65: 68.9, 80: 80.9, 100: 105.3},
        "v_max": 3.0,
        "info": "Tradițional, pentru instalații industriale"
    },
    "PVC-U Presiune": {
        "rugozitate_mm": 0.002,
        "diametre_mm": {20: 15.4, 25: 20.4, 32: 26.2, 40: 34.2, 50: 43.4, 
                       63: 55.2, 75: 65.8, 90: 79, 110: 96.8},
        "v_max": 2.5,
        "info": "Economic, pentru apă rece"
    }
}

# ======================== CONSUMATORI ========================
CONSUMATORI = {
    "WC cu rezervor": {
        "debit": 0.10, "unitate": 1.0, "presiune_min": 8.0, "diametru_min": 10,
        "categorie": "Baie"
    },
    "WC cu robinet flotor": {
        "debit": 1.50, "unitate": 5.0, "presiune_min": 50.0, "diametru_min": 20,
        "categorie": "Baie"
    },
    "Pisoar cu robinet": {
        "debit": 0.30, "unitate": 2.0, "presiune_min": 15.0, "diametru_min": 12,
        "categorie": "Baie"
    },
    "Lavoar": {
        "debit": 0.10, "unitate": 1.0, "presiune_min": 10.0, "diametru_min": 10,
        "categorie": "Baie"
    },
    "Bideu": {
        "debit": 0.10, "unitate": 1.0, "presiune_min": 10.0, "diametru_min": 10,
        "categorie": "Baie"
    },
    "Duș": {
        "debit": 0.20, "unitate": 2.0, "presiune_min": 12.0, "diametru_min": 12,
        "categorie": "Baie"
    },
    "Cadă < 150L": {
        "debit": 0.25, "unitate": 3.0, "presiune_min": 13.0, "diametru_min": 13,
        "categorie": "Baie"
    },
    "Cadă > 150L": {
        "debit": 0.33, "unitate": 4.0, "presiune_min": 13.0, "diametru_min": 13,
        "categorie": "Baie"
    },
    "Spălător vase (chiuvetă)": {
        "debit": 0.20, "unitate": 2.0, "presiune_min": 12.0, "diametru_min": 12,
        "categorie": "Bucătărie"
    },
    "Mașină spălat vase": {
        "debit": 0.20, "unitate": 2.0, "presiune_min": 12.0, "diametru_min": 12,
        "categorie": "Bucătărie"
    },
    "Mașină spălat rufe": {
        "debit": 0.20, "unitate": 2.0, "presiune_min": 12.0, "diametru_min": 12,
        "categorie": "Utilitate"
    },
    "Robinet serviciu 1/2\"": {
        "debit": 0.20, "unitate": 1.5, "presiune_min": 10.0, "diametru_min": 13,
        "categorie": "Utilitate"
    },
    "Robinet serviciu 3/4\"": {
        "debit": 0.40, "unitate": 2.5, "presiune_min": 10.0, "diametru_min": 19,
        "categorie": "Utilitate"
    },
    "Robinet grădină": {
        "debit": 0.70, "unitate": 3.5, "presiune_min": 15.0, "diametru_min": 19,
        "categorie": "Exterior"
    },
    "Robinet spălare auto": {
        "debit": 1.00, "unitate": 5.0, "presiune_min": 20.0, "diametru_min": 25,
        "categorie": "Exterior"
    }
}

# ======================== FUNCȚII DE CALCUL ========================

def calcul_debit_probabilistic(consumatori_selectati: List[Dict]) -> float:
    """Calculează debitul probabilistic conform SR 1343-1:2006"""
    suma_debit_unitate = sum(c["debit"] * c["unitate"] * c["cantitate"] 
                              for c in consumatori_selectati)
    
    if suma_debit_unitate <= 0:
        return 0.0
    elif suma_debit_unitate <= 0.2:
        return suma_debit_unitate
    elif suma_debit_unitate <= 1.6:
        return 0.2 + 0.25 * (suma_debit_unitate - 0.2)**0.5
    else:
        return 0.466 * suma_debit_unitate**0.5

def calcul_diametru_minim(debit: float, viteza_max: float) -> float:
    """Calculează diametrul minim necesar în mm"""
    if debit <= 0 or viteza_max <= 0:
        return 0.0
    return 1000 * math.sqrt(4 * debit / (math.pi * viteza_max))

def reynolds(viteza: float, diametru: float, temperatura: float = 10.0) -> float:
    """Calculează numărul Reynolds"""
    vascozitate = 1.3e-6 if temperatura <= 10 else 1.0e-6
    return viteza * diametru / vascozitate

def factor_frecare_colebrook(re: float, rugozitate: float, diametru: float, 
                            epsilon: float = 1e-6) -> float:
    """Calculează factorul de frecare prin formula Colebrook-White"""
    if re < 2300:
        return 64 / re
    
    rugozitate_relativa = rugozitate / diametru
    f_vechi = 0.02
    
    for _ in range(100):
        if f_vechi <= 0:
            f_vechi = 0.02
        
        partea_dreapta = -2 * math.log10(
            rugozitate_relativa / 3.7 + 2.51 / (re * math.sqrt(f_vechi))
        )
        
        if partea_dreapta <= 0:
            return 0.02
            
        f_nou = (1 / partea_dreapta) ** 2
        
        if abs(f_nou - f_vechi) < epsilon:
            return f_nou
        
        f_vechi = f_nou
    
    return f_vechi

def pierdere_presiune_distribuita(debit: float, lungime: float, 
                                 diametru: float, rugozitate: float,
                                 temperatura: float = 10.0) -> float:
    """Calculează pierderea de presiune distribuită în mCA"""
    if diametru <= 0 or debit <= 0:
        return 0.0
    
    viteza = 4 * debit / (math.pi * (diametru/1000)**2)
    re = reynolds(viteza, diametru/1000, temperatura)
    f = factor_frecare_colebrook(re, rugozitate/1000, diametru/1000)
    
    return f * lungime * viteza**2 / (2 * G * diametru/1000)

def pierdere_presiune_locala(viteza: float, coeficient: float) -> float:
    """Calculează pierderea de presiune locală în mCA"""
    return coeficient * viteza**2 / (2 * G)

def calcul_pierderi_locale_tronson(pierdere_dist: float, este_ultimul_etaj: bool, 
                                   numar_tee: int = 1) -> float:
    """
    Calculează pierderile locale pentru un tronson
    
    Pentru ultimul etaj: 40% din pierderea distribuită (toate elementele)
    Pentru restul: doar Tee-uri (coef 1.8 per bucată, estimat ca 5% din pierderea distribuită)
    """
    if este_ultimul_etaj:
        # Ultimul etaj - toate pierderile locale (40% din distribuită)
        return 0.4 * pierdere_dist
    else:
        # Restul etajelor - doar Tee-uri (5% per Tee)
        return 0.05 * pierdere_dist * numar_tee

def selectare_diametru_material(material: str, diametru_minim: float) -> Tuple[float, float]:
    """Selectează diametrul comercial disponibil și returnează DN"""
    if material not in MATERIALE_CONDUCTE:
        return 0, 0
    
    diametre_disponibile = MATERIALE_CONDUCTE[material]["diametre_mm"]
    
    for dn_comercial, di_real in sorted(diametre_disponibile.items()):
        if di_real >= diametru_minim:
            return dn_comercial, di_real
    
    return max(diametre_disponibile.keys()), diametre_disponibile[max(diametre_disponibile.keys())]

def get_diametru_specific(material: str, dn: float) -> str:
    """Obține diametrul specific pentru un material și DN dat"""
    # Determinăm tipul de material pentru corelație
    tip_material = None
    
    if "PPR" in material:
        tip_material = "PPR"
    elif "PEX" in material or "Multistrat" in material:
        tip_material = "PEX/Multistrat"
    elif "Cupru" in material:
        tip_material = "Cupru"
    elif "PE-HD" in material:
        tip_material = "PE-HD"
    elif "Oțel" in material:
        tip_material = "Oțel"
    elif "PVC" in material:
        tip_material = "PPR"  # Folosim notația similară PPR
    
    if tip_material and tip_material in CORELARE_DN_DIAMETRE:
        if dn in CORELARE_DN_DIAMETRE[tip_material]:
            return CORELARE_DN_DIAMETRE[tip_material][dn]
    
    return f"DN{int(dn)}"

# ======================== FUNCȚII ECHIPAMENTE ========================

def calcul_bransament(debit_total: float, lungime: float = 50, 
                     diferenta_cota: float = 2.0) -> Dict:
    """Dimensionează conducta de branșament"""
    # Folosim PE-HD pentru branșament
    material = "PE-HD"
    v_max = 2.5  # m/s pentru branșament
    
    # Diametru minim necesar
    d_min = calcul_diametru_minim(debit_total, v_max)
    dn, di = selectare_diametru_material(material, d_min)
    
    # Calcul pierderi
    rugozitate = MATERIALE_CONDUCTE[material]["rugozitate_mm"]
    pierdere_dist = pierdere_presiune_distribuita(debit_total, lungime, di, rugozitate)
    pierdere_locala = diferenta_cota  # Pierdere geometrică
    
    return {
        "material": material,
        "dn": dn,
        "diametru_interior": di,
        "diametru_specific": get_diametru_specific(material, dn),
        "lungime": lungime,
        "debit": debit_total,
        "viteza": 4 * debit_total / (math.pi * (di/1000)**2),
        "pierdere_totala": pierdere_dist + pierdere_locala,
        "presiune_necesara_bransament": max(20.0, pierdere_dist + pierdere_locala + 5.0)
    }

def calcul_vas_tampon(debit_orar_maxim: float, timp_rezerva_min: float = 30) -> Dict:
    """Calculează volumul vasului tampon (rezervor de rupere)"""
    # Volum necesar = debit orar maxim * timp rezervă
    volum_necesar = debit_orar_maxim * 3600 * (timp_rezerva_min / 60)  # litri
    
    # Rotunjim la valori standard
    volume_standard = [500, 1000, 2000, 3000, 5000, 10000]
    volum_ales = next((v for v in volume_standard if v >= volum_necesar), volume_standard[-1])
    
    return {
        "volum_necesar": volum_necesar,
        "volum_ales": volum_ales,
        "timp_rezerva": timp_rezerva_min,
        "debit_alimentare": debit_orar_maxim * 1.2,  # 20% marjă de siguranță
        "diametru_alimentare": int(calcul_diametru_minim(debit_orar_maxim * 1.2 / 3600, 1.5)),
        "diametru_plecare": int(calcul_diametru_minim(debit_orar_maxim / 3600, 2.0)),
        "diametru_golire": max(50, int(volum_ales / 100))  # DN minim 50mm
    }

def calcul_hidrofor(debit: float, presiune_necesara: float, 
                   numar_pompe: int = 2) -> Dict:
    """Dimensionează stația de hidrofor"""
    # Presiuni de lucru
    presiune_pornire = presiune_necesara
    presiune_oprire = presiune_pornire + 20  # +2 bar
    presiune_medie = (presiune_pornire + presiune_oprire) / 2
    
    # Volum rezervor hidrofor (formula Aquamax)
    porniri_pe_ora = 15  # maxim recomandat
    volum_rezervor = (debit * 3600 * 0.25) / porniri_pe_ora
    
    # Rotunjire la valori standard
    volume_standard = [24, 50, 80, 100, 200, 300, 500, 750, 1000]
    volum_ales = next((v for v in volume_standard if v >= volum_rezervor), volume_standard[-1])
    
    # Caracteristici pompă
    debit_pompa = debit / numar_pompe if numar_pompe > 1 else debit * 1.1
    inaltime_pompare = presiune_oprire
    
    return {
        "numar_pompe": numar_pompe,
        "debit_pompa": debit_pompa * 3600,  # m³/h
        "inaltime_pompare": inaltime_pompare,
        "presiune_pornire": presiune_pornire,
        "presiune_oprire": presiune_oprire,
        "volum_rezervor": volum_ales,
        "porniri_ora_max": porniri_pe_ora,
        "putere_estimata": (debit_pompa * inaltime_pompare * G) / (0.7 * 1000),  # kW
        "configuratie": f"{numar_pompe}x pompe ({numar_pompe-1} active + 1 rezervă)" if numar_pompe > 1 else "1 pompă"
    }

def calcul_reducator_presiune(presiune_intrare: float, presiune_iesire: float,
                             debit: float) -> Dict:
    """Selectează reducător de presiune"""
    # Calculăm DN bazat pe debit
    viteza_recomandata = 2.0  # m/s prin reducător
    dn_necesar = calcul_diametru_minim(debit, viteza_recomandata)
    
    # Selectăm DN standard
    dn_standard = [15, 20, 25, 32, 40, 50, 65, 80, 100]
    dn_ales = next((d for d in dn_standard if d >= dn_necesar), dn_standard[-1])
    
    return {
        "dn": dn_ales,
        "presiune_intrare_max": presiune_intrare,
        "presiune_reglata": presiune_iesire,
        "debit_nominal": debit * 3600,  # m³/h
        "raport_reducere": presiune_intrare / presiune_iesire,
        "tip_recomandat": "Cu pistoane" if dn_ales <= 50 else "Cu membrană",
        "manometru_intrare": "0-10 bar" if presiune_intrare <= 60 else "0-16 bar",
        "manometru_iesire": "0-6 bar"
    }

# ======================== INTERFAȚA STREAMLIT ========================

def main():
    # Header profesional
    st.markdown("""
    <h1 style='text-align: center; color: #1e3d59;'>
        Calculator Profesional Instalații Sanitare
    </h1>
    <h3 style='text-align: center; color: #5c7080;'>
        Conform I9-2022 și SR 1343-1:2006
    </h3>
    <p style='text-align: center; color: #8b9dc3; font-size: 14px;'>
        Dimensionare instalații de alimentare cu apă pentru consum menajer
    </p>
    """, unsafe_allow_html=True)
    
    # Tabs principale
    tab_principal = st.tabs([
        "🚿 Alimentare cu Apă",
        "🌧️ Ape Pluviale", 
        "🚽 Canalizare Menajeră",
        "📊 Rapoarte",
        "📚 Documentație"
    ])
    
    # =============== TAB ALIMENTARE CU APĂ ===============
    with tab_principal[0]:
        st.info("📐 **Modul complet pentru dimensionare instalații de alimentare cu apă**")
        
        # Sub-tabs pentru diferite componente
        sub_tabs = st.tabs([
            "Consumatori & Trasee",
            "Branșament",
            "Vas Tampon",
            "Hidrofor",
            "Echipamente"
        ])
        
        # --- Sub-tab Consumatori & Trasee ---
        with sub_tabs[0]:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader("🚿 Selectare Consumatori")
                
                # Grupare pe categorii
                categorii = set(c["categorie"] for c in CONSUMATORI.values())
                
                consumatori_selectati = []
                for categorie in sorted(categorii):
                    with st.expander(f"📁 {categorie}", expanded=(categorie=="Baie")):
                        for nume, date in CONSUMATORI.items():
                            if date["categorie"] == categorie:
                                cantitate = st.number_input(
                                    f"{nume} (Q={date['debit']} L/s)",
                                    min_value=0, max_value=50, value=0, step=1,
                                    key=f"cons_{nume}"
                                )
                                if cantitate > 0:
                                    consumatori_selectati.append({
                                        "nume": nume,
                                        "cantitate": cantitate,
                                        **date
                                    })
                
                # Calcul debit
                if consumatori_selectati:
                    debit_prob = calcul_debit_probabilistic(consumatori_selectati)
                    st.success(f"💧 **Debit probabilistic total: {debit_prob:.3f} L/s**")
                    st.info(f"📊 **Debit orar maxim: {debit_prob*3.6:.2f} m³/h**")
            
            with col2:
                st.subheader("📏 Dimensionare Tronsoane")
                
                if consumatori_selectati:
                    # Selectare material
                    material = st.selectbox(
                        "🔧 Material conductă",
                        list(MATERIALE_CONDUCTE.keys()),
                        index=1  # PPR cu fibră default
                    )
                    
                    # Afișare info material
                    st.caption(f"ℹ️ {MATERIALE_CONDUCTE[material]['info']}")
                    
                    # Input tronsoane
                    st.write("---")
                    st.write("**📐 Definire tronsoane:**")
                    
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        num_tronsoane = st.slider(
                            "Număr tronsoane", 
                            min_value=1, max_value=10, value=3
                        )
                    with col_b:
                        st.info(f"**Total: {num_tronsoane} tronsoane**")
                    
                    tronsoane = []
                    for i in range(num_tronsoane):
                        with st.expander(f"**Tronson {i+1}**", expanded=(i==0)):
                            col_a, col_b, col_c, col_d = st.columns(4)
                            with col_a:
                                lungime = st.number_input(
                                    "📏 Lungime (m)", 
                                    min_value=0.5, max_value=100.0, value=10.0, 
                                    key=f"lung_{i}"
                                )
                            with col_b:
                                debit_tronson = st.number_input(
                                    "💧 Debit (L/s)", 
                                    min_value=0.01, max_value=10.0, 
                                    value=round(debit_prob * (1 - i*0.2), 3) if i < 4 else debit_prob*0.2,
                                    key=f"deb_{i}"
                                )
                            with col_c:
                                diferenta_nivel = st.number_input(
                                    "📐 Δh nivel (m)", 
                                    min_value=-50.0, max_value=50.0, 
                                    value=3.0 if i > 0 else 0.0,
                                    key=f"dh_{i}",
                                    help="Diferența de cotă față de tronsonul anterior"
                                )
                            with col_d:
                                este_ultimul = st.checkbox(
                                    "🏁 Ultimul etaj",
                                    key=f"ultim_{i}",
                                    value=(i == num_tronsoane - 1),
                                    help="Bifați pentru punctul cel mai defavorabil"
                                )
                            
                            numar_tee = 1
                            if not este_ultimul and i < num_tronsoane - 1:
                                numar_tee = st.number_input(
                                    "🔀 Număr Tee-uri pe tronson",
                                    min_value=0, max_value=5, value=1,
                                    key=f"tee_{i}",
                                    help="Pentru derivații către consumatori"
                                )
                            
                            tronsoane.append({
                                "nr": i+1,
                                "lungime": lungime,
                                "debit": debit_tronson,
                                "diferenta_nivel": diferenta_nivel,
                                "este_ultimul_etaj": este_ultimul,
                                "numar_tee": numar_tee
                            })
                    
                    if st.button("🔍 **CALCULEAZĂ DIMENSIUNI**", type="primary"):
                        rezultate = []
                        pierdere_totala_traseu = 0
                        
                        st.write("---")
                        st.subheader("📊 Rezultate dimensionare")
                        
                        for tronson in tronsoane:
                            # Calcule pentru fiecare tronson
                            v_max = MATERIALE_CONDUCTE[material]["v_max"]
                            d_min = calcul_diametru_minim(tronson["debit"]/1000, v_max)
                            dn, di = selectare_diametru_material(material, d_min)
                            
                            viteza = 4 * tronson["debit"]/1000 / (math.pi * (di/1000)**2)
                            
                            # Pierderi distribuite
                            pierdere_dist = pierdere_presiune_distribuita(
                                tronson["debit"]/1000,
                                tronson["lungime"],
                                di,
                                MATERIALE_CONDUCTE[material]["rugozitate_mm"]
                            )
                            
                            # Pierderi locale - logica corectă
                            pierdere_locala = calcul_pierderi_locale_tronson(
                                pierdere_dist,
                                tronson["este_ultimul_etaj"],
                                tronson["numar_tee"]
                            )
                            
                            # Pierdere geometrică
                            pierdere_geometrica = tronson["diferenta_nivel"]
                            
                            # Total
                            pierdere_totala = pierdere_dist + pierdere_locala + pierdere_geometrica
                            pierdere_totala_traseu += pierdere_totala
                            
                            rezultate.append({
                                "Tronson": f"T{tronson['nr']}",
                                "Poziție": "🏁 ULTIM" if tronson["este_ultimul_etaj"] else f"🔀 {tronson['numar_tee']} Tee",
                                "L (m)": tronson["lungime"],
                                "Q (L/s)": f"{tronson['debit']:.3f}",
                                "DN": f"DN{int(dn)}",
                                "D. Specific": get_diametru_specific(material, dn),
                                "Di (mm)": f"{di:.1f}",
                                "v (m/s)": f"{viteza:.2f}",
                                "ΔH dist": f"{pierdere_dist:.2f}",
                                "ΔH loc": f"{pierdere_locala:.2f}",
                                "ΔH geom": f"{pierdere_geometrica:.2f}",
                                "ΔH tot": f"{pierdere_totala:.2f}"
                            })
                        
                        # Afișare rezultate
                        col_res1, col_res2 = st.columns([2, 1])
                        
                        with col_res1:
                            st.success(f"✅ **Pierdere totală traseu: {pierdere_totala_traseu:.2f} mCA**")
                            
                            # Presiune necesară
                            presiune_necesara = pierdere_totala_traseu + 10  # +10 mCA rezervă la consumator
                            st.info(f"⚡ **Presiune necesară la bază: {presiune_necesara:.1f} mCA**")
                        
                        with col_res2:
                            st.metric(
                                "Presiune (bar)",
                                f"{presiune_necesara/10:.1f}",
                                f"+{1.0:.1f} rezervă"
                            )
                        
                        # Tabel rezultate
                        df_rezultate = pd.DataFrame(rezultate)
                        st.dataframe(
                            df_rezultate,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Poziție": st.column_config.TextColumn(
                                    "Tip tronson",
                                    help="🏁 = Ultimul etaj (toate pierderile), 🔀 = Număr Tee-uri"
                                ),
                                "ΔH dist": st.column_config.TextColumn("ΔH dist (mCA)"),
                                "ΔH loc": st.column_config.TextColumn("ΔH loc (mCA)"),
                                "ΔH geom": st.column_config.TextColumn("ΔH geom (m)"),
                                "ΔH tot": st.column_config.TextColumn("ΔH total (mCA)")
                            }
                        )
                        
                        # Note explicative
                        with st.expander("ℹ️ **Explicație calcul pierderi locale**"):
                            st.write("""
                            **Logica aplicată conform practicii inginerești:**
                            
                            • **Tronsoane marcate ca ULTIM (🏁)**:
                              - Se calculează TOATE pierderile locale
                              - Include: robinete, coturi, tee-uri, reducții, clapete de sens
                              - Estimare: 40% din pierderea distribuită
                            
                            • **Restul tronsoanelor (🔀)**:
                              - Se calculează DOAR pierderile pentru Tee-uri
                              - Motivație: presiunea calculată pentru ultimul etaj acoperă toate celelalte
                              - Estimare: 5% din pierderea distribuită per Tee
                            
                            Această abordare evită supradimensionarea sistemului și reflectă comportamentul real hidraulic.
                            """)
                        
                        # Grafic pierderi
                        fig = go.Figure()
                        
                        # Stacked bar pentru tipuri de pierderi
                        fig.add_trace(go.Bar(
                            x=[r["Tronson"] for r in rezultate],
                            y=[float(r["ΔH dist"]) for r in rezultate],
                            name="Distribuite",
                            marker_color='#3498db',
                            text=[f"{float(r['ΔH dist']):.1f}" for r in rezultate],
                            textposition='inside'
                        ))
                        
                        fig.add_trace(go.Bar(
                            x=[r["Tronson"] for r in rezultate],
                            y=[float(r["ΔH loc"]) for r in rezultate],
                            name="Locale",
                            marker_color='#e74c3c',
                            text=[f"{float(r['ΔH loc']):.1f}" for r in rezultate],
                            textposition='inside'
                        ))
                        
                        fig.add_trace(go.Bar(
                            x=[r["Tronson"] for r in rezultate],
                            y=[float(r["ΔH geom"]) for r in rezultate],
                            name="Geometrice",
                            marker_color='#2ecc71',
                            text=[f"{float(r['ΔH geom']):.1f}" for r in rezultate],
                            textposition='inside'
                        ))
                        
                        fig.update_layout(
                            title="Distribuția pierderilor de presiune pe tronsoane",
                            xaxis_title="Tronson",
                            yaxis_title="Pierdere (mCA)",
                            barmode='stack',
                            height=400,
                            showlegend=True,
                            hovermode='x unified'
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
        # --- Sub-tab Branșament ---
        with sub_tabs[1]:
            st.subheader("🔌 Dimensionare Branșament")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Parametri branșament:**")
                debit_bransament = st.number_input(
                    "💧 Debit total (L/s)", 
                    min_value=0.1, max_value=50.0, value=2.0,
                    help="Debitul probabilistic total al clădirii"
                )
                lungime_bransament = st.number_input(
                    "📏 Lungime branșament (m)", 
                    min_value=1.0, max_value=200.0, value=50.0,
                    help="Distanța de la rețeaua publică la clădire"
                )
                diferenta_cota_brans = st.number_input(
                    "📐 Diferență de cotă (m)", 
                    min_value=-10.0, max_value=20.0, value=2.0,
                    help="Pozitiv dacă clădirea e mai sus decât rețeaua"
                )
            
            with col2:
                st.write("**Material recomandat: PE-HD**")
                st.caption("Rezistent UV, flexibil, durată mare de viață")
                
                if st.button("📐 **Calculează Branșament**", key="btn_brans"):
                    rezultat = calcul_bransament(
                        debit_bransament/1000,
                        lungime_bransament,
                        diferenta_cota_brans
                    )
                    
                    st.success("✅ **Rezultate Branșament:**")
                    
                    col_r1, col_r2 = st.columns(2)
                    
                    with col_r1:
                        st.metric("Dimensiune", f"DN{int(rezultat['dn'])}")
                        st.metric("Diametru specific", rezultat['diametru_specific'])
                        st.metric("Viteză", f"{rezultat['viteza']:.2f} m/s")
                    
                    with col_r2:
                        st.metric("Pierdere totală", f"{rezultat['pierdere_totala']:.2f} mCA")
                        st.metric("Presiune necesară", f"{rezultat['presiune_necesara_bransament']:.1f} mCA")
                        st.metric("Material", rezultat['material'])
        
        # --- Sub-tab Vas Tampon ---
        with sub_tabs[2]:
            st.subheader("💧 Dimensionare Vas Tampon (Rezervor de Rupere)")
            
            st.info("Rezervorul tampon asigură o rezervă de apă și decuplează presiunea de la rețea")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Parametri de calcul:**")
                debit_orar = st.number_input(
                    "📊 Debit orar maxim (m³/h)", 
                    min_value=0.5, max_value=100.0, value=5.0,
                    help="Debitul probabilistic × 3.6"
                )
                timp_rezerva = st.slider(
                    "⏱️ Timp de rezervă (minute)", 
                    min_value=15, max_value=120, value=30,
                    help="Autonomie în caz de întrerupere alimentare"
                )
            
            with col2:
                st.write("**Volume standard disponibile:**")
                st.caption("500L, 1000L, 2000L, 3000L, 5000L, 10000L")
                
                if st.button("📐 **Calculează Vas Tampon**", key="btn_vas"):
                    rezultat = calcul_vas_tampon(debit_orar, timp_rezerva)
                    
                    st.success("✅ **Dimensionare Vas Tampon:**")
                    
                    col_v1, col_v2 = st.columns(2)
                    
                    with col_v1:
                        st.metric("Volum necesar", f"{rezultat['volum_necesar']:.0f} L")
                        st.metric("Volum ales", f"{rezultat['volum_ales']} L", "Standard")
                        st.metric("Timp rezervă", f"{rezultat['timp_rezerva']} min")
                    
                    with col_v2:
                        st.metric("DN alimentare", f"DN{rezultat['diametru_alimentare']}")
                        st.metric("DN plecare", f"DN{rezultat['diametru_plecare']}")
                        st.metric("DN golire", f"DN{rezultat['diametru_golire']}")
        
        # --- Sub-tab Hidrofor ---
        with sub_tabs[3]:
            st.subheader("🚀 Dimensionare Stație Hidrofor")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Parametri sistem:**")
                debit_hidrofor = st.number_input(
                    "💧 Debit necesar (L/s)", 
                    min_value=0.5, max_value=50.0, value=3.0,
                    help="Debitul probabilistic total"
                )
                presiune_necesara = st.number_input(
                    "⚡ Presiune necesară (mCA)", 
                    min_value=10.0, max_value=100.0, value=35.0,
                    help="Presiunea calculată din pierderi + rezervă"
                )
                numar_pompe = st.selectbox(
                    "🔧 Configurație pompe",
                    [1, 2, 3, 4],
                    index=1,
                    format_func=lambda x: f"{x} pompă" if x==1 else f"{x} pompe ({x-1}+1 rezervă)"
                )
            
            with col2:
                st.write("**Parametri funcționare:**")
                st.caption("• Porniri max/oră: 15")
                st.caption("• Diferența presiune: 2 bar")
                st.caption("• Randament pompă: 70%")
                
                if st.button("📐 **Calculează Hidrofor**", key="btn_hidro"):
                    rezultat = calcul_hidrofor(
                        debit_hidrofor/1000,
                        presiune_necesara,
                        numar_pompe
                    )
                    
                    st.success("✅ **Parametri Hidrofor:**")
                    
                    col_h1, col_h2, col_h3 = st.columns(3)
                    
                    with col_h1:
                        st.metric("Configurație", rezultat['configuratie'])
                        st.metric("Debit pompă", f"{rezultat['debit_pompa']:.2f} m³/h")
                        st.metric("Putere motor", f"{rezultat['putere_estimata']:.2f} kW")
                    
                    with col_h2:
                        st.metric("Presiune pornire", f"{rezultat['presiune_pornire']:.1f} mCA")
                        st.metric("Presiune oprire", f"{rezultat['presiune_oprire']:.1f} mCA")
                        st.metric("Înălțime pompare", f"{rezultat['inaltime_pompare']:.1f} m")
                    
                    with col_h3:
                        st.metric("Volum rezervor", f"{rezultat['volum_rezervor']} L")
                        st.metric("Porniri/oră", f"max {rezultat['porniri_ora_max']}")
                        st.metric("Presiune (bar)", f"{rezultat['presiune_oprire']/10:.1f}")
        
        # --- Sub-tab Echipamente ---
        with sub_tabs[4]:
            st.subheader("⚙️ Echipamente Auxiliare")
            
            # Reducător de presiune
            with st.expander("🔽 **Reducător de Presiune**"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Parametri reducător:**")
                    presiune_intrare = st.number_input(
                        "📈 Presiune intrare (mCA)", 
                        min_value=20.0, max_value=160.0, value=60.0
                    )
                    presiune_iesire = st.number_input(
                        "📉 Presiune ieșire dorită (mCA)", 
                        min_value=10.0, max_value=50.0, value=30.0
                    )
                    debit_reducator = st.number_input(
                        "💧 Debit (L/s)", 
                        min_value=0.1, max_value=20.0, value=2.0
                    )
                
                with col2:
                    st.write("**Tipuri disponibile:**")
                    st.caption("• Cu pistoane (DN ≤ 50)")
                    st.caption("• Cu membrană (DN > 50)")
                    
                    if st.button("Selectează Reducător", key="btn_reducator"):
                        rezultat = calcul_reducator_presiune(
                            presiune_intrare,
                            presiune_iesire,
                            debit_reducator/1000
                        )
                        
                        st.success("✅ **Specificații Reducător:**")
                        
                        col_red1, col_red2 = st.columns(2)
                        with col_red1:
                            st.metric("Dimensiune", f"DN{rezultat['dn']}")
                            st.metric("Tip", rezultat['tip_recomandat'])
                            st.metric("Raport reducere", f"1:{rezultat['raport_reducere']:.1f}")
                        
                        with col_red2:
                            st.metric("Manometru IN", rezultat['manometru_intrare'])
                            st.metric("Manometru OUT", rezultat['manometru_iesire'])
                            st.metric("Debit nominal", f"{rezultat['debit_nominal']:.2f} m³/h")
            
            # Clapete de sens
            with st.expander("↗️ **Clapete de Sens**"):
                st.info("Clapetele de sens previn curgerea inversă a apei")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Tipuri principale:**")
                    st.write("• **Cu arc** - universale")
                    st.write("• **Cu bilă** - pentru impurități")
                    st.write("• **Tip fluture** - DN mare")
                    st.write("• **Cu disc oscilant** - presiuni mici")
                
                with col2:
                    dn_clapeta = st.selectbox(
                        "Selectează DN clapetă",
                        [15, 20, 25, 32, 40, 50, 65, 80, 100, 125, 150],
                        index=2
                    )
                    
                    tip_clapeta = "Cu arc" if dn_clapeta <= 50 else "Tip fluture"
                    st.success(f"✅ Clapetă de sens **DN{dn_clapeta}**")
                    st.info(f"Tip recomandat: **{tip_clapeta}**")
            
            # Filtre
            with st.expander("🔍 **Filtre de Apă**"):
                st.info("Filtrele protejează instalația și echipamentele")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    tip_filtru = st.selectbox(
                        "Tip filtru",
                        ["Filtru Y cu sită inox",
                         "Filtru magnetic",
                         "Filtru cu cartuș lavabil",
                         "Filtru automat cu spălare inversă"]
                    )
                    
                    finete_filtrare = st.select_slider(
                        "Finețe filtrare (μm)",
                        [5000, 2000, 1000, 500, 200, 100, 50, 25, 10, 5],
                        value=100
                    )
                
                with col2:
                    st.write("**Recomandări finețe:**")
                    st.caption("• 500-1000 μm - protecție generală")
                    st.caption("• 100-200 μm - după contor")
                    st.caption("• 25-50 μm - protecție fină")
                    st.caption("• 5-10 μm - apă potabilă")
                    
                    st.success(f"✅ {tip_filtru}")
                    st.info(f"Finețe: **{finete_filtrare} μm**")
    
    # =============== TAB APE PLUVIALE ===============
    with tab_principal[1]:
        st.info("🌧️ **Calculator pentru sisteme de preluare ape pluviale**")
        
        st.subheader("📐 Dimensionare sistem pluvial")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Date acoperiș:**")
            suprafata_acoperis = st.number_input(
                "Suprafață acoperiș (m²)", 
                min_value=10.0, max_value=10000.0, value=200.0
            )
            tip_acoperis = st.selectbox(
                "Tip acoperiș",
                ["Țiglă", "Tablă", "Membrană", "Beton", "Sticlă"]
            )
        
        with col2:
            st.write("**Parametri ploaie:**")
            intensitate_ploaie = st.number_input(
                "Intensitate ploaie (L/s/ha)", 
                min_value=100.0, max_value=400.0, value=200.0,
                help="Conform zonei climatice"
            )
            coef_scurgere = st.slider(
                "Coeficient de scurgere",
                min_value=0.5, max_value=1.0, value=0.9,
                help="Depinde de materialul acoperișului"
            )
        
        with col3:
            st.write("**Rezultate calcul:**")
            debit_pluvial = (suprafata_acoperis * intensitate_ploaie * coef_scurgere) / 10000
            st.metric("Debit pluvial", f"{debit_pluvial:.2f} L/s")
            
            # Număr receptoare
            nr_receptoare = max(1, int(suprafata_acoperis / 80))  # 1 receptor la 80 mp
            st.metric("Receptoare necesare", nr_receptoare)
            
            # Diametru jgheab
            diam_jgheab = 125 if suprafata_acoperis < 150 else 150
            st.metric("Diametru jgheab", f"{diam_jgheab} mm")
        
        st.write("---")
        
        # Bazin retenție
        st.subheader("💧 Bazin de retenție")
        
        col1, col2 = st.columns(2)
        
        with col1:
            timp_retentie = st.slider(
                "⏱️ Timp retenție (minute)",
                min_value=5, max_value=60, value=15,
                help="Pentru atenuarea debitului de vârf"
            )
            
            volum_bazin = debit_pluvial * timp_retentie * 60
            st.success(f"📊 **Volum bazin necesar: {volum_bazin:.0f} litri**")
            
            # Volum standard
            volume_bazin = [1000, 2000, 3000, 5000, 10000, 15000, 20000]
            volum_standard = next((v for v in volume_bazin if v >= volum_bazin), volume_bazin[-1])
            st.info(f"✅ **Volum ales: {volum_standard} litri**")
        
        with col2:
            st.write("**Sistem de pompare evacuare:**")
            
            debit_evacuare = st.number_input(
                "Debit evacuare permis (L/s)",
                min_value=0.5, max_value=10.0, value=2.0,
                help="Conform aviz canalizare"
            )
            
            inaltime_pompare = st.number_input(
                "Înălțime pompare (m)",
                min_value=1.0, max_value=20.0, value=5.0
            )
            
            # Putere pompă
            putere_pompa = (debit_evacuare/1000 * inaltime_pompare * 9.81) / 0.6
            st.metric("Putere pompă", f"{putere_pompa:.2f} kW")
            
            # Timp golire
            timp_golire = volum_standard / (debit_evacuare * 60)
            st.metric("Timp golire bazin", f"{timp_golire:.1f} min")
    
    # =============== TAB CANALIZARE MENAJERĂ ===============
    with tab_principal[2]:
        st.info("🚽 **Calculator pentru canalizare menajeră**")
        
        st.subheader("📐 Dimensionare coloane și colectoare")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🏢 Coloane de scurgere:**")
            
            tip_cladire = st.selectbox(
                "Tip clădire",
                ["Bloc locuințe", "Clădire birouri", "Hotel", "Spital", "Școală"]
            )
            
            numar_etaje = st.number_input(
                "Număr etaje",
                min_value=1, max_value=30, value=10
            )
            
            apartamente_etaj = st.number_input(
                "Apartamente/etaj",
                min_value=1, max_value=10, value=2
            )
            
            # Calcul simplificat
            unitati_scurgere = numar_etaje * apartamente_etaj * 6  # ~6 US per apartament
            
            # Diametru coloană
            if unitati_scurgere <= 20:
                diam_coloana = 75
            elif unitati_scurgere <= 160:
                diam_coloana = 110
            elif unitati_scurgere <= 360:
                diam_coloana = 125
            else:
                diam_coloana = 160
            
            st.success(f"📏 **Diametru coloană: DN{diam_coloana}**")
            st.info(f"Unități de scurgere: {unitati_scurgere} US")
        
        with col2:
            st.write("**🔄 Ventilații:**")
            
            # Diametru ventilație
            diam_ventilatie = 75 if diam_coloana <= 110 else 110
            st.metric("Ventilație principală", f"DN{diam_ventilatie}")
            
            # Ventilație secundară
            if numar_etaje > 5:
                st.info("✅ Necesară ventilație secundară")
                st.caption(f"Diametru: DN{diam_ventilatie - 25}")
            else:
                st.success("❌ Nu e necesară ventilație secundară")
            
            st.write("---")
            st.write("**📊 Colector orizontal:**")
            
            panta_colector = st.slider(
                "Pantă colector (%)",
                min_value=0.5, max_value=3.0, value=1.5, step=0.5
            )
            
            # Diametru colector
            diam_colector = diam_coloana if unitati_scurgere < 100 else diam_coloana + 25
            st.metric("Diametru colector", f"DN{diam_colector}")
            st.metric("Pantă minimă", f"{panta_colector}%")
    
    # =============== TAB RAPOARTE ===============
    with tab_principal[3]:
        st.info("📊 **Generator de rapoarte tehnice**")
        
        st.subheader("📄 Export rezultate")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Format raport:**")
            format_raport = st.radio(
                "Selectează format",
                ["PDF", "Excel", "Word"],
                horizontal=False
            )
        
        with col2:
            st.write("**Conținut raport:**")
            include_calcule = st.checkbox("Memoriu de calcul", value=True)
            include_tabele = st.checkbox("Tabele dimensionare", value=True)
            include_grafice = st.checkbox("Grafice și diagrame", value=True)
            include_normative = st.checkbox("Referințe normative", value=True)
        
        with col3:
            st.write("**Informații proiect:**")
            nume_proiect = st.text_input("Nume proiect", "Instalații sanitare")
            beneficiar = st.text_input("Beneficiar", "")
            proiectant = st.text_input("Proiectant", "Ing. Luca Obejdeanu")
        
        if st.button("📥 **Generează Raport**", type="primary"):
            st.success("✅ Raport generat cu succes!")
            
            # Simulare descărcare
            dummy_content = f"Raport {nume_proiect} - {proiectant}"
            file_name = f"Raport_{nume_proiect.replace(' ', '_')}.{format_raport.lower()}"
            
            st.download_button(
                label=f"⬇️ **Descarcă {format_raport}**",
                data=dummy_content.encode(),
                file_name=file_name,
                mime="application/octet-stream"
            )
    
    # =============== TAB DOCUMENTAȚIE ===============
    with tab_principal[4]:
        st.info("📚 **Documentație tehnică și normative**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📖 Normative utilizate")
            st.write("""
            **Principale:**
            - **I9-2022** - Normativ pentru proiectarea și executarea instalațiilor sanitare
            - **SR 1343-1:2006** - Alimentări cu apă. Calculul debitelor
            - **STAS 1795** - Canalizări interioare
            - **SR 8591** - Rețele edilitare subterane
            
            **Complementare:**
            - **GP 120-2013** - Ghid privind proiectarea sistemelor centralizate de alimentare cu apă
            - **NP 133-2013** - Normativ privind proiectarea sistemelor de canalizare
            - **SR EN 12056** - Sisteme de canalizare gravitaționale în clădiri
            """)
        
        with col2:
            st.subheader("🔧 Valori de referință")
            
            with st.expander("**Viteze recomandate**"):
                st.write("""
                - Conducte distribuție: **0.5 - 2.0 m/s**
                - Conducte principale: **1.0 - 2.5 m/s**
                - Branșamente: **0.8 - 2.5 m/s**
                - Aspirație pompe: **0.5 - 1.5 m/s**
                - Refulare pompe: **1.5 - 3.0 m/s**
                """)
            
            with st.expander("**Presiuni minime consumatori**"):
                st.write("""
                - Lavoar, bideu: **10 mCA**
                - Duș: **12 mCA**
                - Cadă: **13 mCA**
                - WC cu rezervor: **8 mCA**
                - Mașină spălat: **12 mCA**
                - Robinet grădină: **15 mCA**
                """)
            
            with st.expander("**Coeficienți pierderi locale**"):
                st.write("""
                - Cot 90°: **ξ = 0.9 - 1.5**
                - Tee derivație: **ξ = 1.8**
                - Robinet cu sertar: **ξ = 0.3 - 0.5**
                - Clapetă de sens: **ξ = 2.5 - 3.0**
                - Contor apă: **ξ = 5 - 10**
                - Filtru Y: **ξ = 2.0**
                """)

# ======================== FOOTER ========================
def footer():
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px;'>
        <h4 style='color: #1e3d59; margin: 0;'>Calculator Profesional Instalații Sanitare</h4>
        <p style='color: #5c7080; margin: 10px 0;'>Conform normativelor românești în vigoare</p>
        <p style='color: #8b9dc3; font-size: 14px; margin: 5px 0;'>
            <strong>Designed by Ing. Luca Obejdeanu</strong>
        </p>
        <p style='color: #8b9dc3; font-size: 12px; margin: 5px 0;'>
            © 2024 | Versiunea 1.0 | Contact: luca.obejdeanu@gmail.com
        </p>
    </div>
    """, unsafe_allow_html=True)

# ======================== RULARE APLICAȚIE ========================
if __name__ == "__main__":
    main()
    footer()
