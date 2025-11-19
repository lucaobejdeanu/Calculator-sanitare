import streamlit as st
import pandas as pd
import numpy as np
import math
from typing import List, Dict, Tuple
import plotly.graph_objects as go
import plotly.express as px
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import datetime

# ======================== CONFIGURARE PAGINĂ ========================
st.set_page_config(
    page_title="Calculator Sanitare Pro I9-2022 v6.1",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================== CONSTANTE ========================
G = 9.81  # gravitație m/s²

# ======================== DESTINAȚII CLĂDIRI ========================
DESTINATII_CLADIRE = {
    "Clădiri de locuit": {
        "k_canalizare": 0.5,
        "coef_a_arm": 0.45,
        "coef_b_acm": 0.45,
        "metoda": "B",
        "v_min": 0.20,
    },
    "Clădiri administrative/birouri": {
        "k_canalizare": 0.5,
        "coef_a_arm": 0.55,
        "coef_b_acm": 0.25,
        "metoda": "C",
        "E_min": 1.5,
    },
    "Instituții învățământ/școli": {
        "k_canalizare": 0.7,
        "coef_a_arm": 0.60,
        "coef_b_acm": 0.27,
        "metoda": "C",
        "E_min": 1.8,
    },
    "Spitale/sanatorii": {
        "k_canalizare": 0.7,
        "coef_a_arm": 0.67,
        "coef_b_acm": 0.30,
        "metoda": "C",
        "E_min": 2.2,
    },
    "Hoteluri cu grup sanitar în cameră": {
        "k_canalizare": 0.7,
        "coef_a_arm": 0.60,
        "coef_b_acm": 0.27,
        "metoda": "C",
        "E_min": 1.8,
    },
    "Hoteluri cu grup sanitar comun": {
        "k_canalizare": 1.0,
        "coef_a_arm": 0.85,
        "coef_b_acm": 0.38,
        "metoda": "C",
        "E_min": 3.6,
    },
}

# ======================== COEFICIENȚI PIERDERI LOCALE ========================
COEFICIENTI_PIERDERI_LOCALE = {
    # Armături
    "Robinet cu sertar DN15-50": 0.5,
    "Robinet cu sertar DN65-100": 0.3,
    "Robinet cu sferă (bilă) - deschis total": 0.1,
    "Robinet colțar": 8.0,
    "Clapetă de sens": 2.5,
    "Clapetă de sens cu arc": 3.0,
    "Filtru Y": 2.0,
    "Contor apă DN15-20": 10.0,
    "Contor apă DN25-40": 7.0,
    "Contor apă DN50-100": 5.0,
    
    # Fitinguri - Coturi
    "Cot 90° cu rază mică (r/d=1)": 1.5,
    "Cot 90° cu rază normală (r/d=1.5)": 0.9,
    "Cot 90° cu rază mare (r/d=2)": 0.7,
    "Cot 45°": 0.4,
    "Cot 30°": 0.25,
    
    # Fitinguri - Tee-uri
    "Tee - trecere directă": 0.3,
    "Tee - derivație 90° (ramificație)": 1.8,
    "Tee - confluență": 1.5,
    
    # Reducții
    "Reducție graduală (unghi < 20°)": 0.15,
    "Reducție bruscă 2:1": 0.5,
    "Reducție bruscă 3:2": 0.3,
    "Lărgire graduală": 0.3,
    "Lărgire bruscă 1:2": 1.0,
    
    # Intrări/Ieșiri
    "Intrare în conductă (muchie ascuțită)": 0.5,
    "Intrare în conductă (racordată)": 0.25,
    "Ieșire din conductă": 1.0,
    "Ieșire în rezervor": 1.0,
}

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
    "PPR (Polipropilenă) PN20": {
        "rugozitate_mm": 0.007,
        "diametre_mm": {20: 13.2, 25: 16.6, 32: 21.2, 40: 26.6, 50: 33.2, 63: 42.0, 75: 50.0, 90: 60.0, 110: 73.2},
        "v_max": 2.0,
        "info": "SDR 6, Seria 2.5, pentru apă rece/caldă presiune ridicată"
    },
    "PPR (Polipropilenă) PN16": {
        "rugozitate_mm": 0.007,
        "diametre_mm": {20: 14.4, 25: 18.0, 32: 23.2, 40: 29.0, 50: 36.2, 63: 45.8, 75: 54.4, 90: 65.4, 110: 79.8},
        "v_max": 2.0,
        "info": "SDR 7.4, Seria 3.2, uzual pentru apă rece"
    },
    "PE-HD (Polietilenă) PE100 PN16": {
        "rugozitate_mm": 0.007,
        "diametre_mm": {20: 16.0, 25: 20.4, 32: 26.0, 40: 32.6, 50: 40.8, 63: 51.4, 75: 61.4, 90: 73.6, 110: 90.0},
        "v_max": 2.0,
        "info": "Branșamente și rețele exterioare, SDR 11"
    },
    "PEX (Polietilenă reticulată)": {
        "rugozitate_mm": 0.007,
        "diametre_mm": {16: 12.0, 20: 16.0, 25: 20.0, 32: 26.0, 40: 32.6, 50: 40.8, 63: 51.4},
        "v_max": 2.0,
        "info": "Încălzire și sanitare, flexibil"
    },
    "Cupru (Teavă trasă)": {
        "rugozitate_mm": 0.0015,
        "diametre_mm": {15: 13.0, 18: 16.0, 22: 20.0, 28: 26.0, 35: 33.0, 42: 40.0, 54: 52.0},
        "v_max": 1.5,
        "info": "Instalații aparente, calitate superioară"
    },
    "Oțel Zincat": {
        "rugozitate_mm": 0.15,
        "diametre_mm": {15: 16.0, 20: 21.6, 25: 27.2, 32: 35.9, 40: 41.8, 50: 53.0, 65: 68.8, 80: 80.8, 100: 105.3},
        "v_max": 2.0,
        "info": "Instalații industriale, PSI"
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
    "Spălător vase": {
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
    }
}

# ======================== FUNCȚII DE CALCUL ========================

def calcul_debit_cu_destinatie(suma_vs: float, suma_E: float, destinatie: str, tip_apa: str = "ARM"):
    """Calculează debitul conform destinației"""
    config = DESTINATII_CLADIRE[destinatie]
    
    if config["metoda"] == "B":
        if suma_vs >= config["v_min"]:
            debit = config["coef_a_arm"] * math.sqrt(suma_vs)
        else:
            debit = suma_vs
    else:  # Metoda C
        coef = config["coef_b_acm"] if tip_apa == "ACM" else config["coef_a_arm"]
        if suma_E >= config["E_min"]:
            debit = coef * math.sqrt(suma_E)
        else:
            debit = 0.2 * suma_E
    
    return debit

def calcul_factor_f(N: int, destinatie: str):
    """Calculează factorul de simultaneitate f"""
    # Formula din normativ pentru clădiri de locuit
    if N <= 0:
        return 0
    elif N == 1:
        return 1.0
    else:
        return 1.0 / math.sqrt(N)

def viscozitate_cinematica(temperatura: float) -> float:
    """Viscozitate cinematică"""
    if temperatura <= 10:
        return 1.307e-6
    elif temperatura <= 20:
        return 1.004e-6
    elif temperatura <= 30:
        return 0.801e-6
    elif temperatura <= 40:
        return 0.658e-6
    elif temperatura <= 50:
        return 0.553e-6
    elif temperatura <= 60:
        return 0.475e-6
    else:
        return 0.413e-6

def calculeaza_reynolds(viteza: float, diametru_m: float, viscozitate: float) -> float:
    if viscozitate == 0:
        return 0
    return (viteza * diametru_m) / viscozitate

def calculeaza_lambda_haaland(reynolds: float, rugozitate_rel: float) -> float:
    if reynolds < 2300:
        return 64 / reynolds if reynolds > 0 else 0.02
    else:
        try:
            term1 = (rugozitate_rel / 3.71) ** 1.11
            term2 = 6.9 / reynolds
            lambda_val = (-1.8 * math.log10(term1 + term2)) ** (-2)
            return max(0.008, min(0.1, lambda_val))
        except:
            return 0.02

def dimensioneaza_tronson(debit_ls: float, lungime_m: float, material: str, 
                         temperatura: float, suma_zeta: float, info_material: dict):
    """Dimensionează un tronson"""
    if debit_ls <= 0:
        return None
    
    rugozitate_mm = info_material["rugozitate_mm"]
    v_max_admis = info_material["v_max"]
    diametre = info_material["diametre_mm"]
    
    # Diametru minim teoretic
    d_min = math.sqrt((4 * debit_ls / 1000) / (math.pi * v_max_admis)) * 1000
    
    # Selectez DN comercial
    dn_ales = None
    d_int_mm = None
    for dn, d_int in sorted(diametre.items()):
        if d_int >= d_min:
            dn_ales = dn
            d_int_mm = d_int
            break
    
    if dn_ales is None:
        dn_ales = max(diametre.keys())
        d_int_mm = diametre[dn_ales]
    
    # Calcule hidraulice
    sectiune = math.pi * (d_int_mm/1000)**2 / 4
    viteza = (debit_ls / 1000) / sectiune if sectiune > 0 else 0
    
    viscozitate = viscozitate_cinematica(temperatura)
    reynolds = calculeaza_reynolds(viteza, d_int_mm/1000, viscozitate)
    rugozitate_rel = rugozitate_mm / d_int_mm
    lambda_coef = calculeaza_lambda_haaland(reynolds, rugozitate_rel)
    
    # Pierderi
    h_lin_m = lambda_coef * (lungime_m / (d_int_mm/1000)) * (viteza**2 / (2 * G))
    h_loc_m = suma_zeta * (viteza**2 / (2 * G))
    i_specific = (h_lin_m / lungime_m) * 1000 * G if lungime_m > 0 else 0
    
    return {
        "dn": dn_ales,
        "d_int_mm": d_int_mm,
        "viteza_ms": viteza,
        "reynolds": reynolds,
        "lambda": lambda_coef,
        "h_lin_m": h_lin_m,
        "h_loc_m": h_loc_m,
        "i_specific_pa_m": i_specific,
        "i_L": h_lin_m * 1000,  # în mmCA
        "h_loc_mmca": h_loc_m * 1000
    }

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

def calcul_pierderi_locale_tronson(viteza: float, elemente_locale: Dict[str, int], 
                                   este_ultimul_etaj: bool = False) -> float:
    """
    Calculează pierderile locale pentru un tronson
    
    Args:
        viteza: viteza fluidului în m/s
        elemente_locale: dicționar cu elementele și cantitățile lor
        este_ultimul_etaj: True pentru ultimul etaj (cel mai defavorabil)
    
    Returns:
        Pierderea locală totală în mCA
    """
    pierdere_totala = 0.0
    
    for element, cantitate in elemente_locale.items():
        if element in COEFICIENTI_PIERDERI_LOCALE:
            # Pentru etajele inferioare, luăm în calcul doar tee-urile
            if not este_ultimul_etaj and "Tee" not in element:
                continue
            
            coef = COEFICIENTI_PIERDERI_LOCALE[element]
            pierdere_totala += cantitate * pierdere_presiune_locala(viteza, coef)
    
    return pierdere_totala

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

# ======================== FUNCȚII ECHIPAMENTE NOI ========================

def calcul_bransament(debit_total: float, lungime: float = 50, 
                     diferenta_cota: float = 2.0) -> Dict:
    """Dimensionează conducta de branșament"""
    # Folosim PE-HD pentru branșament
    material = "PE-HD (Polietilenă) PE100 PN16"
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
    volum_rezervor_m3 = (debit * 3600 * 0.25) / porniri_pe_ora
    volum_rezervor_litri = volum_rezervor_m3 * 1000  # Conversie în litri
    
    # Rotunjire la valori standard
    volume_standard = [24, 50, 80, 100, 150, 200, 300, 500, 750, 1000, 1500, 2000, 3000, 5000]
    volum_ales = next((v for v in volume_standard if v >= volum_rezervor_litri), volume_standard[-1])
    
    # Caracteristici pompă
    debit_pompa = debit / numar_pompe if numar_pompe > 1 else debit * 1.1
    inaltime_pompare = presiune_oprire
    
    # Putere hidraulică (kW) = (Q * H * rho * g) / (eta * 1000)
    # rho = 1000 kg/m3, g = 9.81
    # eta (randament) estimat la 0.65
    putere_hidraulica = (debit_pompa * inaltime_pompare * 9.81) / (0.65 * 1000)
    putere_motor_estimata = putere_hidraulica * 1.2  # +20% rezervă
    
    return {
        "numar_pompe": numar_pompe,
        "debit_pompa": debit_pompa * 3600,  # m³/h
        "inaltime_pompare": inaltime_pompare,
        "presiune_pornire": presiune_pornire,
        "presiune_oprire": presiune_oprire,
        "volum_rezervor": volum_ales,
        "porniri_ora_max": porniri_pe_ora,
        "putere_estimata": putere_motor_estimata,
        "configuratie": f"{numar_pompe}x pompe active" if numar_pompe > 1 else "1 pompă activă"
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

# ======================== FUNCȚII RAPOARTE ========================
def create_pdf_report(data: dict):
    """Generează raportul PDF detaliat - Memoriu Tehnic Extins"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          rightMargin=2*cm, leftMargin=2.5*cm, 
                          topMargin=2*cm, bottomMargin=2*cm)
    
    # Înregistrare font pentru diacritice
    try:
        pdfmetrics.registerFont(TTFont('Arial', '/System/Library/Fonts/Supplemental/Arial.ttf'))
        font_name = 'Arial'
    except:
        font_name = 'Helvetica'  # Fallback
    
    styles = getSampleStyleSheet()
    
    # Stiluri personalizate
    style_title = ParagraphStyle(
        'CustomTitle', 
        parent=styles['Heading1'], 
        fontName=font_name,
        alignment=1, 
        spaceAfter=30,
        fontSize=18,
        textColor=colors.black
    )
    
    style_heading1 = ParagraphStyle(
        'CustomHeading1', 
        parent=styles['Heading1'],
        fontName=font_name,
        spaceBefore=20, 
        spaceAfter=15,
        fontSize=14,
        textColor=colors.black,
        keepWithNext=True
    )
    
    style_heading2 = ParagraphStyle(
        'CustomHeading2', 
        parent=styles['Heading2'],
        fontName=font_name,
        spaceBefore=15, 
        spaceAfter=10,
        fontSize=12,
        textColor=colors.black,
        keepWithNext=True
    )
    
    style_normal = ParagraphStyle(
        'CustomNormal', 
        parent=styles['Normal'],
        fontName=font_name,
        spaceAfter=10,
        leading=14,
        alignment=4,  # Justify
        fontSize=10
    )
    
    style_list = ParagraphStyle(
        'CustomList',
        parent=style_normal,
        leftIndent=20,
        bulletIndent=10
    )
    
    story = []
    
    # --- PAGINA DE TITLU ---
    story.append(Spacer(1, 5*cm))
    story.append(Paragraph("MEMORIU TEHNIC", style_title))
    story.append(Paragraph("INSTALAȚII SANITARE INTERIOARE", style_title))
    story.append(Paragraph("ALIMENTARE CU APĂ", style_title))
    story.append(Spacer(1, 8*cm))
    story.append(Paragraph(f"Data elaborării: {datetime.datetime.now().strftime('%d.%m.%Y')}", style_normal))
    story.append(PageBreak())
    
    # --- CAPITOLUL 1: DATE GENERALE ---
    story.append(Paragraph("1. DATE GENERALE", style_heading1))
    
    story.append(Paragraph("1.1. Obiectul proiectului", style_heading2))
    text_obiect = """Prezenta documentație tratează proiectarea instalațiilor sanitare interioare de alimentare cu apă rece și apă caldă de consum pentru obiectivul analizat. Soluțiile tehnice adoptate au ca scop asigurarea confortului utilizatorilor, siguranța în exploatare și optimizarea consumurilor energetice."""
    story.append(Paragraph(text_obiect, style_normal))
    
    story.append(Paragraph("1.2. Baze de proiectare", style_heading2))
    story.append(Paragraph("La baza elaborării prezentului proiect au stat următoarele:", style_normal))
    normative = [
        "• Tema de proiectare stabilită de beneficiar;",
        "• Planurile de arhitectură ale clădirii;",
        "• Normativ I9-2022 - Normativ pentru proiectarea, executarea și exploatarea instalațiilor sanitare;",
        "• SR 1343-1:2006 - Alimentări cu apă. Determinarea cantităților de apă potabilă pentru localități urbane și rurale;",
        "• NP 084-2003 - Normativ privind proiectarea, executarea și exploatarea instalațiilor sanitare aferente clădirilor;",
        "• Legea 10/1995 privind calitatea în construcții, cu modificările și completările ulterioare;",
        "• P118-99 - Normativ de siguranță la foc a construcțiilor."
    ]
    for n in normative:
        story.append(Paragraph(n, style_list))
        
    story.append(Paragraph("1.3. Caracteristicile amplasamentului", style_heading2))
    info_gen = f"""
    Clădirea analizată are funcțiunea de <b>{data.get('destinatie', 'Locuință')}</b>.
    Sursa de apă: Rețeaua publică de distribuție / Sursă proprie.
    Regimul de presiune disponibil asigură funcționarea normală a instalației, fiind prevăzută (după caz) o stație de pompare hidropneumatică.
    """
    story.append(Paragraph(info_gen, style_normal))
    
    # --- CAPITOLUL 2: DESCRIEREA INSTALAȚIILOR ---
    story.append(Paragraph("2. DESCRIEREA TEHNICĂ A INSTALAȚIILOR", style_heading1))
    
    story.append(Paragraph("2.1. Alimentarea cu apă rece", style_heading2))
    descriere_apa = f"""
    Instalația de alimentare cu apă rece este realizată în sistem ramificat/inelar, dimensionată pentru a asigura debitele și presiunile necesare la punctele de consum cele mai dezavantajate.
    Conductele de distribuție sunt realizate din <b>{data.get('material', 'N/A')}</b>, material ales pentru rezistența sa la coroziune, depuneri și presiune.
    Traseele conductelor sunt pozate mascat (în ghene, șape, pereți falși) sau aparent, conform planurilor de arhitectură.
    """
    story.append(Paragraph(descriere_apa, style_normal))
    
    story.append(Paragraph("2.2. Izolații termice", style_heading2))
    text_izolatii = """
    Conductele de distribuție a apei reci se vor izola termic pentru a preveni formarea condensului și încălzirea apei. Izolația va fi de tip elastomer sau polietilenă expandată, cu grosimea minimă de 9-13 mm, în funcție de diametrul conductei și condițiile de montaj.
    """
    story.append(Paragraph(text_izolatii, style_normal))

    # --- CAPITOLUL 3: BREVIAR DE CALCUL ---
    story.append(Paragraph("3. BREVIAR DE CALCUL HIDRAULIC", style_heading1))
    
    story.append(Paragraph("3.1. Metodologia de calcul", style_heading2))
    metodologie = """
    Dimensionarea conductelor s-a efectuat conform SR 1343-1:2006. Debitul de calcul (qc) s-a determinat probabilistic în funcție de numărul de unități de consum și tipul clădirii.
    
    Relațiile de calcul utilizate:
    """
    story.append(Paragraph(metodologie, style_normal))
    
    formule = [
        "• Debitul de calcul: qc = a * sqrt(E) [l/s] sau qc = c * sqrt(E) [l/s]",
        "• Pierderea de sarcină liniară (Darcy-Weisbach): hd = λ * (L/D) * (v²/2g)",
        "• Coeficientul de frecare (λ): Formula Colebrook-White",
        "• Pierderea de sarcină locală: hl = Σζ * (v²/2g)",
        "• Presiunea necesară la branșament: Hnec = Hg + Σhd + Σhl + Hu"
    ]
    for f in formule:
        story.append(Paragraph(f, style_list))
        
    story.append(Paragraph("3.2. Parametri de calcul considerați", style_heading2))
    params = f"""
    • Temperatura apei reci: {data.get('temperatura', '10')} °C
    • Presiunea minimă de utilizare la cel mai dezavantajat consumator: 15 mCA (1.5 bar)
    • Viteze maxime admise: conform normativului I9-2022 (2.0 - 3.0 m/s în funcție de material și amplasare)
    """
    story.append(Paragraph(params, style_normal))
    
    # --- CAPITOLUL 4: REZULTATELE DIMENSIONĂRII ---
    story.append(PageBreak())
    story.append(Paragraph("4. TABEL CENTRALIZATOR DE DIMENSIONARE", style_heading1))
    
    if 'rezultate_arm' in data:
        df = data['rezultate_arm']
        
        # Header tabel
        table_data = [[
            'Tronson', 
            'Debit\n(l/s)', 
            'DN\n(mm)', 
            'Viteză\n(m/s)', 
            'L\n(m)', 
            'ΔH lin\n(mCA)', 
            'ΔH loc\n(mCA)', 
            'ΔH tot\n(mCA)'
        ]]
        
        # Date tabel
        for _, row in df.iterrows():
            table_data.append([
                str(row['Tronson']),
                f"{row['Vc']:.3f}",
                str(row['DN']),
                f"{row['v']:.2f}",
                f"{row['L']:.1f}",
                f"{row['Σ i*L']:.2f}",
                f"{row['Σ h_loc']:.2f}",
                f"{row['h_tot']:.2f}"
            ])
            
        # Stil tabel
        t = Table(table_data, colWidths=[1.5*cm, 2*cm, 2*cm, 2*cm, 1.5*cm, 2*cm, 2*cm, 2*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        story.append(t)
        
        story.append(Spacer(1, 15))
        
        # Rezultate finale evidențiate
        story.append(Paragraph("REZULTATE FINALE ȘI NECESAR DE PRESIUNE", style_heading2))
        
        final_stats = [
            f"Debit total de calcul (Qc): {data.get('debit_total', 0):.3f} l/s",
            f"Pierdere de sarcină totală pe traseu: {data.get('presiune_totala', 0):.2f} mCA",
            "Presiune de utilizare necesară: 15.00 mCA",
            f"Presiune totală necesară la branșament (Hnec): {data.get('presiune_totala', 0) + 15.0:.2f} mCA"
        ]
        
        for stat in final_stats:
            story.append(Paragraph(f"• <b>{stat}</b>", style_normal))

    # --- CAPITOLUL 5: INSTRUCȚIUNI DE EXECUȚIE ȘI MONTAJ ---
    story.append(PageBreak())
    story.append(Paragraph("5. CAIET DE SARCINI - INSTRUCȚIUNI DE EXECUȚIE", style_heading1))
    
    instructiuni = [
        "Execuția instalațiilor se va face numai de către personal calificat și autorizat.",
        "La montajul conductelor se vor respecta instrucțiunile producătorului privind tăierea, îmbinarea și fixarea acestora.",
        "Se vor prevedea puncte fixe și puncte de alunecare pentru preluarea dilatărilor termice.",
        "Trecerea conductelor prin pereți și planșee se va face prin tuburi de protecție.",
        "Distanța dintre elementele de susținere va respecta normativul I9-2022, în funcție de diametrul și materialul conductei.",
        "După montaj, instalația se va spăla cu apă potabilă până la limpezire."
    ]
    
    for instr in instructiuni:
        story.append(Paragraph(f"• {instr}", style_list))
        
    story.append(Paragraph("5.1. Proba de presiune", style_heading2))
    proba = """
    Instalația se va supune probei de presiune la rece. Presiunea de probă va fi de 1.5 x Presiunea de regim, dar nu mai puțin de 6 bar.
    Durata probei va fi de minim 2 ore. Pe durata probei nu se admit scurgeri sau deformări ale elementelor instalației.
    Rezultatele probei se vor consemna într-un Proces Verbal de Probe.
    """
    story.append(Paragraph(proba, style_normal))
    
    # --- CAPITOLUL 6: EXPLOATARE ȘI ÎNTREȚINERE ---
    story.append(Paragraph("6. EXPLOATARE ȘI ÎNTREȚINERE", style_heading1))
    mentenanta = """
    Beneficiarul are obligația de a asigura verificarea periodică a etanșeității instalației și a bunei funcționări a armăturilor.
    Se recomandă:
    """
    story.append(Paragraph(mentenanta, style_normal))
    
    recomandari = [
        "Verificarea vizuală lunară a traseelor aparente;",
        "Manevrarea robineților de închidere cel puțin o dată la 6 luni pentru a preveni blocarea;",
        "Curățarea filtrelor Y și a aeratoarelor bateriilor trimestrial;",
        "Verificarea presiunii în vasul de expansiune al hidroforului (dacă există) semestrial."
    ]
    for rec in recomandari:
        story.append(Paragraph(f"- {rec}", style_list))
        
    # --- CAPITOLUL 7: MĂSURI DE SSM ȘI PSI ---
    story.append(Paragraph("7. MĂSURI DE SĂNĂTATE ȘI SECURITATE ÎN MUNCĂ", style_heading1))
    ssm = """
    La execuția lucrărilor se vor respecta normele generale de protecție a muncii și normele specifice pentru lucrări de instalații tehnico-sanitare.
    Personalul va fi dotat cu echipament de protecție adecvat (salopetă, cască, mănuși, încălțăminte de protecție).
    Se vor respecta normele de prevenire și stingere a incendiilor specifice șantierelor de construcții.
    """
    story.append(Paragraph(ssm, style_normal))
    
    # Final
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("Întocmit,", style_normal))
    story.append(Paragraph("Inginer Proiectant", style_normal))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ======================== INIȚIALIZARE SESSION STATE ========================
if 'tronsoane_arm' not in st.session_state:
    st.session_state.tronsoane_arm = []

if 'tronsoane_acm' not in st.session_state:
    st.session_state.tronsoane_acm = []

if 'rezultate_calcul' not in st.session_state:
    st.session_state.rezultate_calcul = {}

# ======================== INTERFAȚA STREAMLIT ========================

def main():
    # Header cu stil
    st.markdown("""
    <h1 style='text-align: center; color: #2E86AB;'>
        💧 Calculator Instalații Sanitare Pro v6.1 💧
    </h1>
    <h3 style='text-align: center; color: #A23B72;'>
        Conform I9-2022 și SR 1343-1:2006 | Calcul avansat pierderi locale
    </h3>
    """, unsafe_allow_html=True)
    
    # ======================== SIDEBAR ========================
    with st.sidebar:
        st.header("⚙️ Configurare Proiect")
        
        destinatie_aleasa = st.selectbox(
            "🏢 Destinația clădirii",
            options=list(DESTINATII_CLADIRE.keys()),
        )
        
        config_destinatie = DESTINATII_CLADIRE[destinatie_aleasa]
        
        st.info(f"""
        **Parametri destinație:**  
        📝 Metodă: {config_destinatie['metoda']}  
        💧 k canalizare: {config_destinatie['k_canalizare']}  
        🔧 Coef. a (ARM): {config_destinatie['coef_a_arm']}  
        🔥 Coef. b (ACM): {config_destinatie['coef_b_acm']}
        """)
        
        st.markdown("---")
        
        material_ales = st.selectbox(
            "� Material conductă",
            options=list(MATERIALE_CONDUCTE.keys())
        )
        
        temperatura = st.slider(
            "🌡️ Temperatură (°C)",
            min_value=5, max_value=70, value=10
        )
        
        st.markdown("---")
        
        # Butoane acțiuni
        if st.button("🗑️ Șterge toate tronsoanele ARM", type="secondary"):
            st.session_state.tronsoane_arm = []
            st.rerun()
        
        if st.button("🗑️ Șterge toate tronsoanele ACM", type="secondary"):
            st.session_state.tronsoane_acm = []
            st.rerun()

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
        st.info("📐 **Calculator complet pentru instalații de alimentare cu apă - v6.1 cu pierderi locale detaliate**")
        
        # Sub-tabs pentru diferite componente
        sub_tabs = st.tabs([
            "Consumatori & Trasee",
            "Branșament",
            "Vas Tampon",
            "Hidrofor"
        ])
        
        # --- Sub-tab Consumatori & Trasee ---
        with sub_tabs[0]:
            st.subheader("� Dimensionare Tronsoane ARM (Progresiv)")
            
            # Formular nou tronson
            with st.expander("➕ Adaugă Tronson NOU", expanded=len(st.session_state.tronsoane_arm) == 0):
                st.write("**Selectează consumatorii pentru acest tronson:**")
                
                consumatori_tronson = {}
                cols = st.columns(3)
                
                for idx, (nume, date) in enumerate(CONSUMATORI.items()):
                    with cols[idx % 3]:
                        cant = st.number_input(
                            f"{nume} (Vs={date['debit']}, U={date['unitate']})",
                            min_value=0, max_value=50, value=0,
                            key=f"arm_new_{nume}"
                        )
                        if cant > 0:
                            consumatori_tronson[nume] = cant
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    lungime_tronson = st.number_input(
                        "Lungime tronson (m)", 
                        min_value=0.1, max_value=200.0, value=5.0,
                        key="arm_new_lungime"
                    )
                    diferenta_nivel = st.number_input(
                        "Diferență nivel (m)", 
                        min_value=-20.0, max_value=20.0, value=0.0,
                        help="Pozitiv dacă urcă, negativ dacă coboară",
                        key="arm_new_nivel"
                    )
                
                with col2:
                    nr_coturi = st.number_input("Coturi 90° (ζ=1.0)", 0, 20, 2, key="arm_new_cot")
                    nr_tee = st.number_input("Tee-uri (ζ=1.8)", 0, 20, 1, key="arm_new_tee")
                
                with col3:
                    nr_robineti = st.number_input("Robinete (ζ=0.5)", 0, 20, 1, key="arm_new_rob")
                    nr_clapete = st.number_input("Clapete (ζ=2.5)", 0, 10, 0, key="arm_new_clap")
                
                suma_zeta = nr_coturi * 1.0 + nr_tee * 1.8 + nr_robineti * 0.5 + nr_clapete * 2.5
                st.info(f"Σ ζ = {suma_zeta:.1f}")
                
                if st.button("✅ Adaugă Tronson ARM", type="primary"):
                    if consumatori_tronson:
                        tronson = {
                            "nr": len(st.session_state.tronsoane_arm) + 1,
                            "consumatori": consumatori_tronson,
                            "lungime": lungime_tronson,
                            "diferenta_nivel": diferenta_nivel,
                            "suma_zeta": suma_zeta
                        }
                        st.session_state.tronsoane_arm.append(tronson)
                        st.success(f"✅ Tronson {tronson['nr']} adăugat!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Selectați cel puțin un consumator!")
            
            # Afișare și calcul tronsoane
            if st.session_state.tronsoane_arm:
                st.markdown("---")
                st.subheader("📊 Tronsoane Definite")
                
                # Calcul cumulat
                rezultate = []
                consumatori_cumulate = {}
                suma_i_L_cumulata = 0
                suma_h_loc_cumulata = 0
                suma_h_geom_cumulata = 0
                
                for tronson in st.session_state.tronsoane_arm:
                    # Actualizez consumatorii cumulați
                    for cons, cant in tronson["consumatori"].items():
                        consumatori_cumulate[cons] = consumatori_cumulate.get(cons, 0) + cant
                    
                    # Calcul Vs și E cumulate
                    suma_vs = sum(CONSUMATORI[c]["debit"] * q for c, q in consumatori_cumulate.items())
                    suma_E = sum(CONSUMATORI[c]["unitate"] * q for c, q in consumatori_cumulate.items())
                    suma_Utot = suma_E  # Utot = E
                    N = sum(consumatori_cumulate.values())
                    f = calcul_factor_f(N, destinatie_aleasa)
                    
                    # Debit de calcul
                    Vc = calcul_debit_cu_destinatie(suma_vs, suma_E, destinatie_aleasa, "ARM")
                    
                    # Dimensionare
                    info_material = MATERIALE_CONDUCTE[material_ales]
                    dim = dimensioneaza_tronson(
                        Vc, tronson["lungime"], material_ales, 
                        temperatura, tronson["suma_zeta"], info_material
                    )
                    
                    if dim:
                        suma_i_L_cumulata += dim["i_L"]
                        suma_h_loc_cumulata += dim["h_loc_mmca"]
                        suma_h_geom_cumulata += tronson.get("diferenta_nivel", 0) * 1000 # convertim in mmCA pentru consistenta interna
                        
                        # h_tot (mCA) = (Liniare + Locale + Geometrice) / 1000
                        h_tot = (suma_i_L_cumulata + suma_h_loc_cumulata + suma_h_geom_cumulata) / 1000
                        
                        rezultate.append({
                            "Tronson": tronson["nr"],
                            "Consumatori": ", ".join([f"{c}:{q}" for c, q in tronson["consumatori"].items()]),
                            "Utot": suma_Utot,
                            "N": N,
                            "f": f,
                            "Vs": suma_vs,
                            "Vc": Vc,
                            "DN": dim["dn"],
                            "d_int": dim["d_int_mm"],
                            "v": dim["viteza_ms"],
                            "i": dim["i_specific_pa_m"],
                            "L": tronson["lungime"],
                            "i*L": dim["i_L"],
                            "Σ i*L": suma_i_L_cumulata,
                            "Σ ζ": tronson["suma_zeta"],
                            "h_loc": dim["h_loc_mmca"],
                            "Σ h_loc": suma_h_loc_cumulata,
                            "h_geom": tronson.get("diferenta_nivel", 0),
                            "Σ h_geom": suma_h_geom_cumulata / 1000,
                            "h_tot": h_tot
                        })
                
                # Tabel rezultate
                df_rezultate = pd.DataFrame(rezultate)
                
                # Formatare tabel
                st.dataframe(
                    df_rezultate.style.format({
                        "Utot": "{:.1f}",
                        "f": "{:.3f}",
                        "Vs": "{:.3f}",
                        "Vc": "{:.3f}",
                        "d_int": "{:.1f}",
                        "v": "{:.2f}",
                        "i": "{:.0f}",
                        "L": "{:.1f}",
                        "i*L": "{:.1f}",
                        "Σ i*L": "{:.1f}",
                        "Σ ζ": "{:.1f}",
                        "h_loc": "{:.1f}",
                        "Σ h_loc": "{:.1f}",
                        "h_geom": "{:.2f}",
                        "Σ h_geom": "{:.2f}",
                        "h_tot": "{:.3f}"
                    }),
                    use_container_width=True,
                    height=400
                )
                
                # Rezultate finale
                st.markdown("---")
                col1, col2, col3, col4 = st.columns(4)
                
                ultima_linie = df_rezultate.iloc[-1]
                
                with col1:
                    st.metric("🔵 Debit calcul final", f"{ultima_linie['Vc']:.3f} l/s")
                    st.metric("📏 Diametru final", f"DN{ultima_linie['DN']}")
                
                with col2:
                    st.metric("💨 Viteză finală", f"{ultima_linie['v']:.2f} m/s")
                    st.metric("🔢 Nr. consumatori", f"{int(ultima_linie['N'])}")
                
                with col3:
                    st.metric("📐 Σ i*L", f"{ultima_linie['Σ i*L']:.1f} mmCA")
                    st.metric("⚙️ Σ h_loc", f"{ultima_linie['Σ h_loc']:.1f} mmCA")
                    st.metric("🏔️ Σ h_geom", f"{ultima_linie['Σ h_geom']:.2f} m")
                
                with col4:
                    st.metric("📊 h_tot", f"{ultima_linie['h_tot']:.3f} mCA")
                    st.metric("🎯 Factor f", f"{ultima_linie['f']:.3f}")
                
                # Grafic evoluție pierderi
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_rezultate['Tronson'],
                    y=df_rezultate['Σ i*L'],
                    name='Σ i*L (mmCA)',
                    mode='lines+markers',
                    line=dict(color='#2196f3', width=3)
                ))
                fig.add_trace(go.Scatter(
                    x=df_rezultate['Tronson'],
                    y=df_rezultate['Σ h_loc'],
                    name='Σ h_loc (mmCA)',
                    mode='lines+markers',
                    line=dict(color='#ff9800', width=3)
                ))
                fig.update_layout(
                    title="Evoluția pierderilor cumulate",
                    xaxis_title="Tronson",
                    yaxis_title="Pierderi (mmCA)",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Salvare rezultate în session state pentru alte tab-uri
                ultima_linie = df_rezultate.iloc[-1]
                st.session_state.rezultate_calcul = {
                    "debit_total": float(ultima_linie['Vc']),
                    "presiune_totala": float(ultima_linie['h_tot']),
                    "df_arm": df_rezultate,
                    "material": material_ales,
                    "destinatie": destinatie_aleasa,
                    "temperatura": temperatura
                }
                
                # Buton export Excel
                if st.button("📥 Exportă în Excel ARM"):
                    output_path = "Calcul_ARM_Tronsoane.xlsx"
                    df_rezultate.to_excel(output_path, index=False, sheet_name="ARM")
                    st.success(f"✅ Tabelul a fost exportat!")
            
            else:
                st.info("ℹ️ Nu există tronsoane definite. Adaugă primul tronson!")
                st.session_state.rezultate_calcul = {}
        
        # --- Sub-tab Branșament ---
        with sub_tabs[1]:
            st.subheader("🔌 Dimensionare Branșament")
            
            if not st.session_state.rezultate_calcul:
                st.warning("⚠️ Vă rugăm să calculați întâi tronsoanele în tab-ul 'Consumatori & Trasee'!")
            else:
                debit_auto = st.session_state.rezultate_calcul.get('debit_total', 0)
                st.info(f"ℹ️ Debit preluat din calcul: **{debit_auto:.3f} L/s**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    debit_bransament = st.number_input(
                        "Debit total (L/s)", 
                        min_value=0.1, max_value=50.0, value=float(debit_auto),
                        disabled=True
                    )
                    lungime_bransament = st.number_input(
                        "Lungime branșament (m)", 
                        min_value=1.0, max_value=200.0, value=50.0
                    )
                    diferenta_cota_brans = st.number_input(
                        "Diferență de cotă (m)", 
                        min_value=-10.0, max_value=20.0, value=2.0
                    )
                
                with col2:
                    if st.button("📐 Calculează Branșament"):
                        rezultat = calcul_bransament(
                            debit_bransament/1000,
                            lungime_bransament,
                            diferenta_cota_brans
                        )
                        
                        st.success("✅ **Rezultate Branșament:**")
                        st.write(f"📦 Material: **{rezultat['material']}**")
                        st.write(f"📏 Dimensiune: **DN{int(rezultat['dn'])}** ({rezultat['diametru_specific']})")
                        st.write(f"💨 Viteză: **{rezultat['viteza']:.2f} m/s**")
                        st.write(f"📉 Pierdere totală: **{rezultat['pierdere_totala']:.2f} mCA**")
                        st.write(f"⚡ Presiune necesară la branșament: **{rezultat['presiune_necesara_bransament']:.1f} mCA**")
        
        # --- Sub-tab Vas Tampon ---
        with sub_tabs[2]:
            st.subheader("💧 Dimensionare Vas Tampon (Rezervor de Rupere)")
            
            if not st.session_state.rezultate_calcul:
                st.warning("⚠️ Vă rugăm să calculați întâi tronsoanele în tab-ul 'Consumatori & Trasee'!")
            else:
                debit_l_s = st.session_state.rezultate_calcul.get('debit_total', 0)
                debit_m3_h = debit_l_s * 3.6
                st.info(f"ℹ️ Debit preluat din calcul: **{debit_l_s:.3f} L/s** ({debit_m3_h:.2f} m³/h)")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    debit_orar = st.number_input(
                        "Debit orar maxim (m³/h)", 
                        min_value=0.1, max_value=100.0, value=float(debit_m3_h),
                        disabled=True
                    )
                    timp_rezerva = st.number_input(
                        "Timp de rezervă (minute)", 
                        min_value=15, max_value=120, value=30
                    )
                
                with col2:
                    if st.button("📐 Calculează Vas Tampon"):
                        rezultat = calcul_vas_tampon(debit_orar, timp_rezerva)
                        
                        st.success("✅ **Dimensionare Vas Tampon:**")
                        st.write(f"📊 Volum necesar: **{rezultat['volum_necesar']:.0f} L**")
                        st.write(f"✅ Volum ales (standard): **{rezultat['volum_ales']} L**")
                        st.write(f"⬇️ DN alimentare: **DN{rezultat['diametru_alimentare']}**")
                        st.write(f"⬆️ DN plecare: **DN{rezultat['diametru_plecare']}**")
                        st.write(f"🚪 DN golire: **DN{rezultat['diametru_golire']}**")
                        st.write(f"💧 Debit alimentare: **{rezultat['debit_alimentare']:.2f} m³/h**")
        
        # --- Sub-tab Hidrofor ---
        with sub_tabs[3]:
            st.subheader("🚀 Dimensionare Stație Hidrofor")
            
            if not st.session_state.rezultate_calcul:
                st.warning("⚠️ Vă rugăm să calculați întâi tronsoanele în tab-ul 'Consumatori & Trasee'!")
            else:
                debit_auto = st.session_state.rezultate_calcul.get('debit_total', 0)
                presiune_auto = st.session_state.rezultate_calcul.get('presiune_totala', 0)
                
                st.info(f"ℹ️ Date preluate: Q = **{debit_auto:.3f} L/s**, H_necesar = **{presiune_auto:.2f} mCA**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    debit_hidrofor = st.number_input(
                        "Debit necesar (L/s)", 
                        min_value=0.1, max_value=50.0, value=float(debit_auto),
                        disabled=True
                    )
                    presiune_utilizator = st.number_input(
                        "Presiune utilizator (mCA)", 
                        min_value=10.0, max_value=50.0, value=15.0,
                        help="Presiunea necesară la cel mai defavorizat consumator"
                    )
                    presiune_necesara = st.number_input(
                        "Presiune totală necesară (mCA)", 
                        min_value=10.0, max_value=100.0, value=float(presiune_auto + presiune_utilizator),
                        help="Include pierderile de sarcină + presiunea de utilizare"
                    )
                    numar_pompe = st.selectbox(
                        "Configurație pompe",
                        [1, 2, 3, 4],
                        index=1
                    )
                
                with col2:
                    if st.button("📐 Calculează Hidrofor"):
                        rezultat = calcul_hidrofor(
                            debit_hidrofor/1000,
                            presiune_necesara,
                            numar_pompe
                        )
                        
                        st.success("✅ **Parametri Hidrofor:**")
                        st.write(f"� Configurație: **{rezultat['configuratie']}**")
                        st.write(f"💧 Debit pompă: **{rezultat['debit_pompa']:.2f} m³/h**")
                        st.write(f"� Înălțime pompare: **{rezultat['inaltime_pompare']:.1f} mCA**")
                        st.write(f"� Presiune pornire: **{rezultat['presiune_pornire']:.1f} mCA**")
                        st.write(f"� Presiune oprire: **{rezultat['presiune_oprire']:.1f} mCA**")
                        st.write(f"🛢️ Volum rezervor: **{rezultat['volum_rezervor']} L**")
                        st.write(f"⚡ Putere estimată: **{rezultat['putere_estimata']:.2f} kW**")
                        st.write(f"🔄 Porniri/oră max: **{rezultat['porniri_ora_max']}**")
    
    # =============== TAB APE PLUVIALE ===============
    with tab_principal[1]:
        st.info("🌧️ **Calculator pentru sisteme de preluare ape pluviale** (în dezvoltare)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Date de intrare")
            suprafata_acoperis = st.number_input(
                "Suprafață acoperiș (m²)", 
                min_value=10.0, max_value=10000.0, value=200.0
            )
            intensitate_ploaie = st.number_input(
                "Intensitate ploaie (L/s/ha)", 
                min_value=100.0, max_value=400.0, value=200.0
            )
            coef_scurgere = st.slider(
                "Coeficient de scurgere",
                min_value=0.5, max_value=1.0, value=0.9
            )
        
        with col2:
            st.subheader("🧮 Rezultate")
            debit_pluvial = (suprafata_acoperis * intensitate_ploaie * coef_scurgere) / 10000
            st.success(f"💧 Debit pluvial: **{debit_pluvial:.2f} L/s**")
            
            # Bazin retenție
            timp_retentie = st.number_input(
                "Timp retenție (minute)",
                min_value=5, max_value=60, value=15
            )
            volum_bazin = debit_pluvial * timp_retentie * 60
            st.info(f"🏊 Volum bazin retenție: **{volum_bazin:.0f} L**")
    
    # =============== TAB CANALIZARE MENAJERĂ ===============
    with tab_principal[2]:
        st.info("🚽 **Calculator pentru canalizare menajeră** (în dezvoltare)")
        
        st.write("Module în dezvoltare:")
        st.write("• Dimensionare coloane de scurgere")
        st.write("• Calculul ventilațiilor")
        st.write("• Dimensionare colectoare orizontale")
        st.write("• Cămine și separatoare")
    
    # =============== TAB RAPOARTE ===============
    with tab_principal[3]:
        st.info("📊 **Generator de rapoarte tehnice**")
        
        if st.session_state.rezultate_calcul:
            data_raport = {
                'rezultate_arm': st.session_state.rezultate_calcul.get('df_arm'),
                'debit_total': st.session_state.rezultate_calcul.get('debit_total'),
                'presiune_totala': st.session_state.rezultate_calcul.get('presiune_totala'),
                'material': st.session_state.rezultate_calcul.get('material'),
                'destinatie': st.session_state.rezultate_calcul.get('destinatie'),
                'temperatura': st.session_state.rezultate_calcul.get('temperatura')
            }
            
            if st.button("📄 Generează Raport PDF"):
                pdf_buffer = create_pdf_report(data_raport)
                st.success("✅ Raport generat cu succes!")
                st.download_button(
                    label="⬇️ Descarcă Raport PDF",
                    data=pdf_buffer,
                    file_name="Memoriu_Tehnic_Sanitare.pdf",
                    mime="application/pdf"
                )
        else:
            st.warning("⚠️ Nu există date calculate pentru a genera raportul. Vă rugăm să efectuați calculele în tab-ul 'Consumatori & Trasee'.")
    
    # =============== TAB DOCUMENTAȚIE ===============
    with tab_principal[4]:
        st.info("📚 **Documentație și standarde**")
        
        st.write("""
        ### Normative utilizate:
        - **I9-2022** - Normativ instalații sanitare
        - **SR 1343-1:2006** - Alimentări cu apă
        - **STAS 1795** - Canalizări interioare
        - **SR 8591** - Rețele edilitare
        
        ### Logica calcul pierderi locale (v6.1):
        
        #### Pentru ULTIMUL ETAJ (cel mai defavorabil):
        - Se calculează TOATE pierderile locale:
          - Robinete, clapete de sens, filtre
          - Coturi, tee-uri, reducții
          - Intrări/ieșiri din rezervoare
        - Aceasta determină presiunea necesară maximă
        
        #### Pentru RESTUL ETAJELOR:
        - Se calculează DOAR Tee-urile (derivații)
        - Restul pierderilor locale sunt acoperite de calculul pentru ultimul etaj
        - Aceasta este abordarea corectă din punct de vedere hidraulic
        
        ### Coeficienți pierderi locale (ξ):
        - Cot 90° normal: 0.9
        - Tee derivație: 1.8
        - Robinet cu sertar: 0.3-0.5
        - Clapetă de sens: 2.5-3.0
        - Filtru Y: 2.0
        - Contor apă: 5.0-10.0
        
        ### Formule utilizate:
        - Pierdere locală: ΔH = ξ × v²/(2g)
        - Pierdere distribuită: Colebrook-White
        - Debit probabilistic: SR 1343-1:2006
        """)

# ======================== FOOTER ========================
def footer():
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>📧 Dezvoltat pentru ingineri de instalații | v6.1 cu calcul avansat pierderi locale | 2024</p>
        <p>⚡ Powered by Streamlit & Python</p>
    </div>
    """, unsafe_allow_html=True)

# ======================== RULARE APLICAȚIE ========================
if __name__ == "__main__":
    main()
    footer()