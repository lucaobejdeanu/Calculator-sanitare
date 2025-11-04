import streamlit as st
import pandas as pd
import numpy as np
import math
from typing import List, Dict, Tuple, Optional
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

# ======================== DESTINAȚII CLĂDIRI ========================
DESTINATII_CLADIRE = {
    "Clădiri de locuit": {
        "descriere": "Blocuri rezidențiale, case, apartamente",
        "k_canalizare": 0.5,
        "coef_a_arm": 0.45,
        "coef_b_acm": 0.45,
        "metoda": "B",
        "v_min": 0.20,
        "perioada_consum_h": 24,
        "Ko": 5,
        "necesar_specific_zi": {
            "total": 100,  # l/pers/zi
            "acm": 40      # l/pers/zi
        },
        "persoane_per_unitate": 2.5
    },
    "Clădiri administrative/birouri": {
        "descriere": "Sedii companii, spații birouri",
        "k_canalizare": 0.5,
        "coef_a_arm": 0.55,
        "coef_b_acm": 0.25,
        "metoda": "C",
        "E_min": 1.5,
        "perioada_consum_h": 8,
        "Ko": 5,
        "necesar_specific_zi": {
            "total": 25,   # l/pers/zi
            "acm": 10      # l/pers/zi
        },
        "persoane_per_unitate": 1
    },
    "Instituții învățământ/școli": {
        "descriere": "Școli, licee, grădinițe",
        "k_canalizare": 0.7,
        "coef_a_arm": 0.60,
        "coef_b_acm": 0.27,
        "metoda": "C",
        "E_min": 1.8,
        "perioada_consum_h": 8,
        "Ko": 5,
        "necesar_specific_zi": {
            "total": 20,   # l/elev/zi
            "acm": 5       # l/elev/zi
        },
        "persoane_per_unitate": 1
    },
    "Spitale/sanatorii": {
        "descriere": "Unități medicale cu internare",
        "k_canalizare": 0.7,
        "coef_a_arm": 0.67,
        "coef_b_acm": 0.30,
        "metoda": "C",
        "E_min": 2.2,
        "perioada_consum_h": 24,
        "Ko": 3,
        "necesar_specific_zi": {
            "total": 220,  # l/pat/zi
            "acm": 88      # l/pat/zi
        },
        "persoane_per_unitate": 1
    },
    "Hoteluri cu grup sanitar în cameră": {
        "descriere": "Hoteluri 2-4 stele",
        "k_canalizare": 0.7,
        "coef_a_arm": 0.60,
        "coef_b_acm": 0.27,
        "metoda": "C",
        "E_min": 1.8,
        "perioada_consum_h": 24,
        "Ko": 4,
        "necesar_specific_zi": {
            "total": 275,  # l/loc/zi (medie 2-3 stele)
            "acm": 110     # l/loc/zi
        },
        "persoane_per_unitate": 1
    },
    "Hoteluri cu grup sanitar comun": {
        "descriere": "Hosteluri, pensiuni economice",
        "k_canalizare": 1.0,
        "coef_a_arm": 0.85,
        "coef_b_acm": 0.38,
        "metoda": "C",
        "E_min": 3.6,
        "perioada_consum_h": 24,
        "Ko": 4,
        "necesar_specific_zi": {
            "total": 140,  # l/loc/zi
            "acm": 56      # l/loc/zi
        },
        "persoane_per_unitate": 1
    },
    "Cămine studenți/internate": {
        "descriere": "Cămine, internate, cămine muncitori",
        "k_canalizare": 1.0,
        "coef_a_arm": 1.0,
        "coef_b_acm": 0.45,
        "metoda": "C",
        "E_min": 5.0,
        "perioada_consum_h": 24,
        "Ko": 4,
        "necesar_specific_zi": {
            "total": 130,  # l/ocupant/zi
            "acm": 50      # l/ocupant/zi
        },
        "persoane_per_unitate": 1
    },
    "Restaurante/cantine": {
        "descriere": "Spații alimentație publică",
        "k_canalizare": 0.7,
        "coef_a_arm": 0.67,
        "coef_b_acm": 0.30,
        "metoda": "C",
        "E_min": 2.2,
        "perioada_consum_h": 12,
        "Ko": 4,
        "necesar_specific_zi": {
            "total": 25,   # l/masă/zi
            "acm": 10      # l/masă/zi
        },
        "persoane_per_unitate": 1
    },
    "Grupuri sanitare publice/stadioane": {
        "descriere": "Băi publice, vestiare sportivi, stadioane",
        "k_canalizare": 1.0,
        "coef_a_arm": 1.0,
        "coef_b_acm": 0.45,
        "metoda": "C",
        "E_min": 5.0,
        "perioada_consum_h": 12,
        "Ko": 3,
        "necesar_specific_zi": {
            "total": 50,   # l/persoană/zi
            "acm": 20      # l/persoană/zi
        },
        "persoane_per_unitate": 1
    },
    "Ateliere/unități producție": {
        "descriere": "Vestiare ateliere, producție",
        "k_canalizare": 1.2,
        "coef_a_arm": 2.0,
        "coef_b_acm": 0.90,
        "metoda": "C",
        "E_min": 20.0,
        "perioada_consum_h": 8,
        "Ko": 5,
        "necesar_specific_zi": {
            "total": 45,   # l/muncitor/schimb
            "acm": 18      # l/muncitor/schimb
        },
        "persoane_per_unitate": 1
    }
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
        "categorie": "Baie", "debit_evacuare": 2.0, "unitate_scurgere": 2.0
    },
    "WC cu robinet flotor": {
        "debit": 1.50, "unitate": 15.0, "presiune_min": 50.0, "diametru_min": 20,
        "categorie": "Baie", "debit_evacuare": 2.0, "unitate_scurgere": 15.0
    },
    "Pisoar cu robinet": {
        "debit": 0.30, "unitate": 2.0, "presiune_min": 15.0, "diametru_min": 12,
        "categorie": "Baie", "debit_evacuare": 0.5, "unitate_scurgere": 2.0
    },
    "Lavoar": {
        "debit": 0.10, "unitate": 1.0, "presiune_min": 10.0, "diametru_min": 10,
        "categorie": "Baie", "debit_evacuare": 0.3, "unitate_scurgere": 1.0
    },
    "Bideu": {
        "debit": 0.10, "unitate": 1.0, "presiune_min": 10.0, "diametru_min": 10,
        "categorie": "Baie", "debit_evacuare": 0.2, "unitate_scurgere": 1.0
    },
    "Duș": {
        "debit": 0.20, "unitate": 2.0, "presiune_min": 12.0, "diametru_min": 12,
        "categorie": "Baie", "debit_evacuare": 0.4, "unitate_scurgere": 2.0
    },
    "Cadă < 150L": {
        "debit": 0.25, "unitate": 3.0, "presiune_min": 13.0, "diametru_min": 13,
        "categorie": "Baie", "debit_evacuare": 0.5, "unitate_scurgere": 3.0
    },
    "Cadă > 150L": {
        "debit": 0.33, "unitate": 4.0, "presiune_min": 13.0, "diametru_min": 13,
        "categorie": "Baie", "debit_evacuare": 0.7, "unitate_scurgere": 4.0
    },
    "Spălător vase (chiuvetă)": {
        "debit": 0.20, "unitate": 2.0, "presiune_min": 12.0, "diametru_min": 12,
        "categorie": "Bucătărie", "debit_evacuare": 0.5, "unitate_scurgere": 2.0
    },
    "Mașină spălat vase": {
        "debit": 0.20, "unitate": 2.0, "presiune_min": 12.0, "diametru_min": 12,
        "categorie": "Bucătărie", "debit_evacuare": 0.2, "unitate_scurgere": 2.0
    },
    "Mașină spălat rufe": {
        "debit": 0.20, "unitate": 2.0, "presiune_min": 12.0, "diametru_min": 12,
        "categorie": "Utilitate", "debit_evacuare": 0.2, "unitate_scurgere": 2.0
    },
    "Robinet serviciu 1/2\"": {
        "debit": 0.20, "unitate": 1.5, "presiune_min": 10.0, "diametru_min": 13,
        "categorie": "Utilitate", "debit_evacuare": 0.2, "unitate_scurgere": 1.5
    },
    "Robinet serviciu 3/4\"": {
        "debit": 0.40, "unitate": 2.5, "presiune_min": 10.0, "diametru_min": 19,
        "categorie": "Utilitate", "debit_evacuare": 0.4, "unitate_scurgere": 2.5
    },
    "Robinet grădină": {
        "debit": 0.70, "unitate": 3.5, "presiune_min": 15.0, "diametru_min": 19,
        "categorie": "Exterior", "debit_evacuare": 0, "unitate_scurgere": 0
    },
    "Robinet spălare auto": {
        "debit": 1.00, "unitate": 5.0, "presiune_min": 20.0, "diametru_min": 25,
        "categorie": "Exterior", "debit_evacuare": 0, "unitate_scurgere": 0
    }
}

# ======================== FUNCȚII DE CALCUL ========================

def calcul_debit_probabilistic_cu_destinatie(consumatori_selectati: List[Dict], 
                                             destinatie: str,
                                             tip_apa: str = "ARM") -> Tuple[float, str]:
    """
    Calculează debitul probabilistic conform I9-2022 în funcție de destinația clădirii
    
    Args:
        consumatori_selectati: Lista cu consumatori și cantități
        destinatie: Cheia destinației din DESTINATII_CLADIRE
        tip_apa: "ARM" sau "ACM"
    
    Returns:
        Tuple (debit_calcul, formula_folosita)
    """
    config = DESTINATII_CLADIRE[destinatie]
    
    # Calculez suma Vs (suma debitelor specifice)
    suma_vs = sum(c["debit"] * c["cantitate"] for c in consumatori_selectati)
    
    # Calculez E (echivalenți de debit)
    suma_E = sum(c["unitate"] * c["cantitate"] for c in consumatori_selectati)
    
    if config["metoda"] == "B":
        # Metoda B - pentru clădiri de locuit
        if suma_vs >= config["v_min"]:
            debit = config["coef_a_arm"] * math.sqrt(suma_vs)
            formula = f"Metoda B: {config['coef_a_arm']} × √{suma_vs:.3f} = {debit:.3f} l/s"
        else:
            debit = suma_vs
            formula = f"Vs < {config['v_min']} l/s: Vc = {suma_vs:.3f} l/s (debit direct)"
    else:
        # Metoda C - pentru clădiri administrative, social-culturale
        if suma_E >= config["E_min"]:
            coef = config["coef_b_acm"] if tip_apa == "ACM" else config["coef_a_arm"]
            debit = coef * math.sqrt(suma_E)
            formula = f"Metoda C: {coef} × √E = {coef} × √{suma_E:.1f} = {debit:.3f} l/s"
        else:
            debit = 0.2 * suma_E
            formula = f"E < {config['E_min']}: Vc = 0.2 × {suma_E:.1f} = {debit:.3f} l/s (debit direct)"
    
    return debit, formula

def calcul_debit_canalizare_cu_destinatie(consumatori_selectati: List[Dict],
                                          destinatie: str) -> Tuple[float, str]:
    """
    Calculează debitul de canalizare conform I9-2022 (14.2)
    
    Vc,ww = k × √Vcs
    unde Vcs = Σ(ni × Vs,i)
    """
    config = DESTINATII_CLADIRE[destinatie]
    k = config["k_canalizare"]
    
    # Calculez Vcs (suma debitelor de evacuare)
    suma_vcs = sum(c.get("debit_evacuare", c["debit"]) * c["cantitate"] 
                   for c in consumatori_selectati)
    
    debit_canalizare = k * math.sqrt(suma_vcs) if suma_vcs > 0 else 0
    formula = f"Vc,ww = {k} × √{suma_vcs:.3f} = {debit_canalizare:.3f} l/s"
    
    return debit_canalizare, formula

def calcul_necesar_zilnic_maxim(destinatie: str, 
                               numar_persoane: int,
                               tip_apa: str = "total") -> Dict:
    """
    Calculează necesarul zilnic maxim conform Anexa 1.2 din I9-2022
    
    Returns:
        Dict cu necesarul zilnic, maxim orar, și coeficienți
    """
    config = DESTINATII_CLADIRE[destinatie]
    
    # Necesar specific pe persoană/unitate
    necesar_spec = config["necesar_specific_zi"][tip_apa]
    
    # Necesar mediu zilnic (l/zi)
    Q_med_zi = necesar_spec * numar_persoane
    
    # Coeficient variație zilnică (din SR 1343-1, considerat 1.15)
    K_zi = 1.15
    
    # Necesar maxim zilnic
    Q_max_zi = K_zi * Q_med_zi
    
    # Coeficient variație orară (din normativ, specific destinației)
    Ko = config["Ko"]
    
    # Perioada de consum
    tc = config["perioada_consum_h"]
    
    # Necesar maxim orar
    Q_max_orar = (Ko * Q_max_zi) / tc
    
    return {
        "Q_med_zi": Q_med_zi,
        "Q_max_zi": Q_max_zi,
        "Q_max_orar": Q_max_orar,
        "K_zi": K_zi,
        "Ko": Ko,
        "tc": tc,
        "necesar_spec": necesar_spec
    }

def calcul_diametru_minim(debit: float, viteza_max: float) -> float:
    """Calculează diametrul minim necesar din debit și viteză maximă admisă"""
    if debit <= 0 or viteza_max <= 0:
        return 0
    # A = Q/v => d = sqrt(4*Q/(pi*v))
    return math.sqrt((4 * debit / 1000) / (math.pi * viteza_max)) * 1000  # mm

def calcul_viteza_curenta(debit_ls: float, diametru_int_mm: float) -> float:
    """Calculează viteza curentă în conductă"""
    if diametru_int_mm <= 0:
        return 0
    sectiune_m2 = math.pi * (diametru_int_mm/1000)**2 / 4
    return (debit_ls / 1000) / sectiune_m2 if sectiune_m2 > 0 else 0

def viscozitate_cinematica(temperatura: float) -> float:
    """Returnează viscozitatea cinematică a apei în funcție de temperatură"""
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
    """Număr Reynolds"""
    if viscozitate == 0:
        return 0
    return (viteza * diametru_m) / viscozitate

def calculeaza_lambda_haaland(reynolds: float, rugozitate_rel: float) -> float:
    """Coeficient λ prin aproximarea Haaland pentru Colebrook-White"""
    if reynolds < 2300:  # Laminar
        return 64 / reynolds if reynolds > 0 else 0.02
    else:  # Turbulent
        try:
            term1 = (rugozitate_rel / 3.71) ** 1.11
            term2 = 6.9 / reynolds
            lambda_val = (-1.8 * math.log10(term1 + term2)) ** (-2)
            return max(0.008, min(0.1, lambda_val))
        except:
            return 0.02

def calcul_pierderi_liniare(lungime_m: float, lambda_coef: float, 
                           viteza_ms: float, diametru_int_m: float) -> float:
    """Calculează pierderile liniare de presiune (Darcy-Weisbach)"""
    if diametru_int_m <= 0:
        return 0
    return lambda_coef * (lungime_m / diametru_int_m) * (viteza_ms**2 / (2 * G))

def calcul_pierderi_locale(viteza_ms: float, suma_zeta: float) -> float:
    """Calculează pierderile locale de presiune"""
    return suma_zeta * (viteza_ms**2 / (2 * G))

def dimensioneaza_tronson_complet(debit_ls: float, lungime_m: float, 
                                 material: str, temperatura: float,
                                 pierderi_locale_zeta: float) -> Optional[Dict]:
    """
    Dimensionează complet un tronson de conductă
    """
    if debit_ls <= 0:
        return None
    
    info_material = MATERIALE_CONDUCTE[material]
    rugozitate_mm = info_material["rugozitate_mm"]
    v_max_admis = info_material["v_max"]
    diametre_disponibile = info_material["diametre_mm"]
    
    # Diametru minim teoretic
    d_min_teoretic = calcul_diametru_minim(debit_ls, v_max_admis)
    
    # Selectez diametrul comercial
    dn_ales = None
    d_int_mm = None
    for dn, d_int in sorted(diametre_disponibile.items()):
        if d_int >= d_min_teoretic:
            dn_ales = dn
            d_int_mm = d_int
            break
    
    if dn_ales is None:
        # Iau cel mai mare diametru disponibil
        dn_ales = max(diametre_disponibile.keys())
        d_int_mm = diametre_disponibile[dn_ales]
    
    # Calcule hidraulice
    viteza = calcul_viteza_curenta(debit_ls, d_int_mm)
    viscozitate = viscozitate_cinematica(temperatura)
    reynolds = calculeaza_reynolds(viteza, d_int_mm/1000, viscozitate)
    rugozitate_rel = rugozitate_mm / d_int_mm
    lambda_coef = calculeaza_lambda_haaland(reynolds, rugozitate_rel)
    
    # Pierderi de presiune
    h_lin_m = calcul_pierderi_liniare(lungime_m, lambda_coef, viteza, d_int_mm/1000)
    h_loc_m = calcul_pierderi_locale(viteza, pierderi_locale_zeta)
    h_total_m = h_lin_m + h_loc_m
    
    return {
        "dn": dn_ales,
        "d_int_mm": d_int_mm,
        "viteza_ms": viteza,
        "reynolds": reynolds,
        "lambda": lambda_coef,
        "h_lin_m": h_lin_m,
        "h_loc_m": h_loc_m,
        "h_total_m": h_total_m,
        "i_specific_pa_m": (h_lin_m / lungime_m) * 1000 * G if lungime_m > 0 else 0
    }

# ======================== MAIN APP ========================
def main():
    # CSS personalizat
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
        }
        .info-box {
            background-color: #e3f2fd;
            padding: 1rem;
            border-left: 4px solid #2196f3;
            border-radius: 5px;
            margin: 1rem 0;
        }
        .success-box {
            background-color: #e8f5e9;
            padding: 1rem;
            border-left: 4px solid #4caf50;
            border-radius: 5px;
            margin: 1rem 0;
        }
        .warning-box {
            background-color: #fff3e0;
            padding: 1rem;
            border-left: 4px solid #ff9800;
            border-radius: 5px;
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>💧 Calculator Profesional Instalații Sanitare</h1>
        <p>Conform normativului I9-2022 și SR 1343-1:2006</p>
        <p style="font-size: 0.9em;">Designed by <strong>Ing. Luca Obejdeanu</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # ======================== SIDEBAR - CONFIGURARE PROIECT ========================
    with st.sidebar:
        st.header("⚙️ Configurare Proiect")
        
        # 🎯 SELECTARE DESTINAȚIE CLĂDIRE
        st.subheader("🏢 Destinația clădirii")
        
        destinatie_aleasa = st.selectbox(
            "Selectează tipul clădirii",
            options=list(DESTINATII_CLADIRE.keys()),
            help="Destinația clădirii influențează toți coeficienții de calcul"
        )
        
        config_destinatie = DESTINATII_CLADIRE[destinatie_aleasa]
        
        # Afișez informații despre destinația aleasă
        st.markdown(f"""
        <div class="info-box">
            <strong>📋 Parametri destinație:</strong><br>
            📝 {config_destinatie['descriere']}<br>
            🔧 Metodă: {config_destinatie['metoda']}<br>
            💧 k canalizare: {config_destinatie['k_canalizare']}<br>
            ⏰ Perioadă consum: {config_destinatie['perioada_consum_h']}h<br>
            📊 Ko: {config_destinatie['Ko']}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Informații proiect
        st.subheader("📄 Informații proiect")
        nume_proiect = st.text_input("Nume proiect", "Instalații sanitare")
        beneficiar = st.text_input("Beneficiar", "")
        
        st.markdown("---")
        
        # Date generale
        st.subheader("🏗️ Date generale clădire")
        
        numar_etaje = st.number_input(
            "Număr etaje",
            min_value=1, max_value=50, value=5,
            help="Numărul de etaje ale clădirii"
        )
        
        unitati_per_etaj = st.number_input(
            f"Unități/etaj ({['ap.', 'birouri', 'săli', 'paturi', 'camere'][list(DESTINATII_CLADIRE.keys()).index(destinatie_aleasa) if list(DESTINATII_CLADIRE.keys()).index(destinatie_aleasa) < 5 else 4]})",
            min_value=1, max_value=20, value=2,
            help="Numărul de unități (apartamente, birouri, camere etc.) per etaj"
        )
        
        numar_total_persoane = st.number_input(
            "Număr total persoane/utilizatori",
            min_value=1, max_value=5000, 
            value=int(numar_etaje * unitati_per_etaj * config_destinatie["persoane_per_unitate"]),
            help="Numărul total de persoane care utilizează clădirea"
        )
    
    # ======================== TABS PRINCIPALE ========================
    tab_principal = st.tabs([
        "💧 Dimensionare Apa Rece",
        "🔥 Dimensionare Apa Caldă",
        "🚽 Canalizare Menajeră",
        "🌧️ Ape Pluviale",
        "⚡ Echipamente",
        "📊 Rapoarte"
    ])
    
    # =============== TAB APĂ RECE ===============
    with tab_principal[0]:
        st.info(f"💧 **Calculator pentru apă rece menajeră - {destinatie_aleasa}**")
        
        st.subheader("🔧 Selectare consumatori")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("**Selectați consumatorii pentru tronsonul analizat:**")
            
            consumatori_selectati_arm = []
            
            for nume_cons, date_cons in CONSUMATORI.items():
                col_a, col_b, col_c = st.columns([3, 1, 1])
                
                with col_a:
                    st.write(f"**{nume_cons}**")
                    st.caption(f"📊 Vs={date_cons['debit']} l/s | Ui={date_cons['unitate']} | P={date_cons['presiune_min']} mCA")
                
                with col_b:
                    cantitate = st.number_input(
                        "Buc",
                        min_value=0, max_value=100, value=0,
                        key=f"arm_{nume_cons}",
                        label_visibility="collapsed"
                    )
                
                with col_c:
                    if cantitate > 0:
                        st.success(f"✓ {cantitate}")
                        consumatori_selectati_arm.append({
                            "nume": nume_cons,
                            "debit": date_cons["debit"],
                            "unitate": date_cons["unitate"],
                            "cantitate": cantitate,
                            "presiune_min": date_cons["presiune_min"],
                            "debit_evacuare": date_cons.get("debit_evacuare", date_cons["debit"])
                        })
        
        with col2:
            st.write("**📊 Rezumat tronson:**")
            
            if consumatori_selectati_arm:
                total_consumatori = sum(c["cantitate"] for c in consumatori_selectati_arm)
                suma_vs = sum(c["debit"] * c["cantitate"] for c in consumatori_selectati_arm)
                suma_E = sum(c["unitate"] * c["cantitate"] for c in consumatori_selectati_arm)
                
                st.metric("Total consumatori", f"{total_consumatori} buc")
                st.metric("Σ Vs", f"{suma_vs:.3f} l/s")
                st.metric("Σ E", f"{suma_E:.1f}")
                
                # Calculez debit de calcul
                debit_calc_arm, formula_arm = calcul_debit_probabilistic_cu_destinatie(
                    consumatori_selectati_arm,
                    destinatie_aleasa,
                    "ARM"
                )
                
                st.markdown(f"""
                <div class="success-box">
                    <strong>✅ Debit de calcul ARM</strong><br>
                    <span style="font-size: 1.5em; color: #2196f3; font-weight: bold;">
                        {debit_calc_arm:.3f} l/s
                    </span><br>
                    <small>{formula_arm}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Afișez necesarul zilnic
                necesar_zilnic_arm = calcul_necesar_zilnic_maxim(
                    destinatie_aleasa,
                    numar_total_persoane,
                    "total"
                )
                
                st.write("**📅 Necesar zilnic:**")
                st.caption(f"Qmed,zi = {necesar_zilnic_arm['Q_med_zi']:.0f} l/zi")
                st.caption(f"Qmax,zi = {necesar_zilnic_arm['Q_max_zi']:.0f} l/zi")
                st.caption(f"Qmax,orar = {necesar_zilnic_arm['Q_max_orar']:.1f} l/h")
        
        # Dimensionare tronson
        if consumatori_selectati_arm:
            st.markdown("---")
            st.subheader("📐 Dimensionare tronson")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                material_arm = st.selectbox(
                    "Material conductă",
                    options=list(MATERIALE_CONDUCTE.keys()),
                    index=0,
                    key="mat_arm"
                )
                
                st.caption(f"ℹ️ {MATERIALE_CONDUCTE[material_arm]['info']}")
            
            with col2:
                lungime_tronson_arm = st.number_input(
                    "Lungime tronson (m)",
                    min_value=0.1, max_value=100.0, value=5.0,
                    step=0.5,
                    key="lung_arm"
                )
            
            with col3:
                temperatura_arm = st.slider(
                    "Temperatură apă (°C)",
                    min_value=5, max_value=30, value=10,
                    key="temp_arm"
                )
            
            # Pierderi locale
            st.write("**⚙️ Pierderi locale:**")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                nr_coturi_90 = st.number_input("Coturi 90° (ζ=1.0)", 0, 20, 2, key="cot_arm")
            with col2:
                nr_tee = st.number_input("Tee-uri (ζ=1.8)", 0, 20, 1, key="tee_arm")
            with col3:
                nr_robineti = st.number_input("Robinete (ζ=0.5)", 0, 20, 1, key="rob_arm")
            with col4:
                nr_clapete = st.number_input("Clapete (ζ=2.5)", 0, 10, 0, key="clap_arm")
            
            suma_zeta_arm = nr_coturi_90 * 1.0 + nr_tee * 1.8 + nr_robineti * 0.5 + nr_clapete * 2.5
            st.info(f"**Σ ζ = {suma_zeta_arm:.1f}**")
            
            # Dimensionare
            rezultat_arm = dimensioneaza_tronson_complet(
                debit_calc_arm,
                lungime_tronson_arm,
                material_arm,
                temperatura_arm,
                suma_zeta_arm
            )
            
            if rezultat_arm:
                st.markdown("---")
                st.subheader("✅ Rezultate dimensionare")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Diametru nominal", f"DN{rezultat_arm['dn']}")
                    # Afișare corelație specifică
                    tip_material_corelatie = "PPR" if "PPR" in material_arm else \
                                           "PEX/Multistrat" if "PEX" in material_arm or "Multistrat" in material_arm else \
                                           "Cupru" if "Cupru" in material_arm else \
                                           "PE-HD" if "PE-HD" in material_arm else \
                                           "Oțel"
                    if rezultat_arm['dn'] in CORELARE_DN_DIAMETRE.get(tip_material_corelatie, {}):
                        denom_com = CORELARE_DN_DIAMETRE[tip_material_corelatie][rezultat_arm['dn']]
                        st.caption(f"Denumire: {denom_com}")
                    st.caption(f"d_int = {rezultat_arm['d_int_mm']:.1f} mm")
                
                with col2:
                    v_color = "🟢" if rezultat_arm['viteza_ms'] <= MATERIALE_CONDUCTE[material_arm]['v_max'] else "🔴"
                    st.metric("Viteză", f"{rezultat_arm['viteza_ms']:.2f} m/s {v_color}")
                    st.caption(f"v_max = {MATERIALE_CONDUCTE[material_arm]['v_max']} m/s")
                    st.caption(f"Re = {rezultat_arm['reynolds']:.0f}")
                
                with col3:
                    st.metric("Pierderi liniare", f"{rezultat_arm['h_lin_m']:.3f} mCA")
                    st.caption(f"i = {rezultat_arm['i_specific_pa_m']:.0f} Pa/m")
                    st.caption(f"λ = {rezultat_arm['lambda']:.4f}")
                
                with col4:
                    st.metric("Pierderi locale", f"{rezultat_arm['h_loc_m']:.3f} mCA")
                    st.metric("Pierderi totale", f"{rezultat_arm['h_total_m']:.3f} mCA")
                
                # Grafic pierderi
                fig_pierderi_arm = go.Figure(data=[
                    go.Bar(
                        x=['Liniare', 'Locale', 'Total'],
                        y=[rezultat_arm['h_lin_m'], rezultat_arm['h_loc_m'], rezultat_arm['h_total_m']],
                        marker_color=['#2196f3', '#ff9800', '#4caf50'],
                        text=[f"{rezultat_arm['h_lin_m']:.3f}", f"{rezultat_arm['h_loc_m']:.3f}", 
                              f"{rezultat_arm['h_total_m']:.3f}"],
                        textposition='outside'
                    )
                ])
                fig_pierderi_arm.update_layout(
                    title="Distribuția pierderilor de presiune",
                    yaxis_title="Pierderi (mCA)",
                    height=300
                )
                st.plotly_chart(fig_pierderi_arm, use_container_width=True)
    
    # =============== TAB APĂ CALDĂ ===============
    with tab_principal[1]:
        st.info(f"🔥 **Calculator pentru apă caldă menajeră - {destinatie_aleasa}**")
        
        st.subheader("🔧 Selectare consumatori")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("**Selectați consumatorii pentru tronsonul analizat:**")
            
            consumatori_selectati_acm = []
            
            # Consumatori care folosesc apă caldă
            consumatori_acm = {k: v for k, v in CONSUMATORI.items() 
                              if k in ["Lavoar", "Bideu", "Duș", "Cadă < 150L", "Cadă > 150L", 
                                      "Spălător vase (chiuvetă)", "Mașină spălat vase", "Mașină spălat rufe"]}
            
            for nume_cons, date_cons in consumatori_acm.items():
                col_a, col_b, col_c = st.columns([3, 1, 1])
                
                with col_a:
                    st.write(f"**{nume_cons}**")
                    st.caption(f"📊 Vs={date_cons['debit']} l/s | Ui={date_cons['unitate']} | P={date_cons['presiune_min']} mCA")
                
                with col_b:
                    cantitate = st.number_input(
                        "Buc",
                        min_value=0, max_value=100, value=0,
                        key=f"acm_{nume_cons}",
                        label_visibility="collapsed"
                    )
                
                with col_c:
                    if cantitate > 0:
                        st.success(f"✓ {cantitate}")
                        consumatori_selectati_acm.append({
                            "nume": nume_cons,
                            "debit": date_cons["debit"],
                            "unitate": date_cons["unitate"],
                            "cantitate": cantitate,
                            "presiune_min": date_cons["presiune_min"]
                        })
        
        with col2:
            st.write("**📊 Rezumat tronson:**")
            
            if consumatori_selectati_acm:
                total_consumatori_acm = sum(c["cantitate"] for c in consumatori_selectati_acm)
                suma_vs_acm = sum(c["debit"] * c["cantitate"] for c in consumatori_selectati_acm)
                suma_E_acm = sum(c["unitate"] * c["cantitate"] for c in consumatori_selectati_acm)
                
                st.metric("Total consumatori", f"{total_consumatori_acm} buc")
                st.metric("Σ Vs", f"{suma_vs_acm:.3f} l/s")
                st.metric("Σ E", f"{suma_E_acm:.1f}")
                
                # Calculez debit de calcul
                debit_calc_acm, formula_acm = calcul_debit_probabilistic_cu_destinatie(
                    consumatori_selectati_acm,
                    destinatie_aleasa,
                    "ACM"
                )
                
                st.markdown(f"""
                <div class="success-box">
                    <strong>✅ Debit de calcul ACM</strong><br>
                    <span style="font-size: 1.5em; color: #ff5722; font-weight: bold;">
                        {debit_calc_acm:.3f} l/s
                    </span><br>
                    <small>{formula_acm}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Afișez necesarul zilnic
                necesar_zilnic_acm = calcul_necesar_zilnic_maxim(
                    destinatie_aleasa,
                    numar_total_persoane,
                    "acm"
                )
                
                st.write("**📅 Necesar zilnic ACM (60°C):**")
                st.caption(f"Qmed,zi = {necesar_zilnic_acm['Q_med_zi']:.0f} l/zi")
                st.caption(f"Qmax,zi = {necesar_zilnic_acm['Q_max_zi']:.0f} l/zi")
                st.caption(f"Qmax,orar = {necesar_zilnic_acm['Q_max_orar']:.1f} l/h")
                st.caption(f"Necesar spec = {necesar_zilnic_acm['necesar_spec']} l/pers/zi")
        
        # Dimensionare tronson ACM
        if consumatori_selectati_acm:
            st.markdown("---")
            st.subheader("📐 Dimensionare tronson")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                material_acm = st.selectbox(
                    "Material conductă",
                    options=[m for m in MATERIALE_CONDUCTE.keys() if "PVC" not in m],  # PVC nu e pt ACM
                    index=0,
                    key="mat_acm"
                )
                
                st.caption(f"ℹ️ {MATERIALE_CONDUCTE[material_acm]['info']}")
            
            with col2:
                lungime_tronson_acm = st.number_input(
                    "Lungime tronson (m)",
                    min_value=0.1, max_value=100.0, value=5.0,
                    step=0.5,
                    key="lung_acm"
                )
            
            with col3:
                temperatura_acm = st.slider(
                    "Temperatură ACM (°C)",
                    min_value=40, max_value=70, value=60,
                    key="temp_acm"
                )
            
            # Pierderi locale
            st.write("**⚙️ Pierderi locale:**")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                nr_coturi_90_acm = st.number_input("Coturi 90° (ζ=1.0)", 0, 20, 2, key="cot_acm")
            with col2:
                nr_tee_acm = st.number_input("Tee-uri (ζ=1.8)", 0, 20, 1, key="tee_acm")
            with col3:
                nr_robineti_acm = st.number_input("Robinete (ζ=0.5)", 0, 20, 1, key="rob_acm")
            with col4:
                nr_clapete_acm = st.number_input("Clapete (ζ=2.5)", 0, 10, 1, key="clap_acm")
            
            suma_zeta_acm = nr_coturi_90_acm * 1.0 + nr_tee_acm * 1.8 + nr_robineti_acm * 0.5 + nr_clapete_acm * 2.5
            st.info(f"**Σ ζ = {suma_zeta_acm:.1f}**")
            
            # Dimensionare
            rezultat_acm = dimensioneaza_tronson_complet(
                debit_calc_acm,
                lungime_tronson_acm,
                material_acm,
                temperatura_acm,
                suma_zeta_acm
            )
            
            if rezultat_acm:
                st.markdown("---")
                st.subheader("✅ Rezultate dimensionare")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Diametru nominal", f"DN{rezultat_acm['dn']}")
                    tip_material_corelatie = "PPR" if "PPR" in material_acm else \
                                           "PEX/Multistrat" if "PEX" in material_acm or "Multistrat" in material_acm else \
                                           "Cupru" if "Cupru" in material_acm else \
                                           "PE-HD" if "PE-HD" in material_acm else \
                                           "Oțel"
                    if rezultat_acm['dn'] in CORELARE_DN_DIAMETRE.get(tip_material_corelatie, {}):
                        denom_com = CORELARE_DN_DIAMETRE[tip_material_corelatie][rezultat_acm['dn']]
                        st.caption(f"Denumire: {denom_com}")
                    st.caption(f"d_int = {rezultat_acm['d_int_mm']:.1f} mm")
                
                with col2:
                    v_color = "🟢" if rezultat_acm['viteza_ms'] <= MATERIALE_CONDUCTE[material_acm]['v_max'] else "🔴"
                    st.metric("Viteză", f"{rezultat_acm['viteza_ms']:.2f} m/s {v_color}")
                    st.caption(f"v_max = {MATERIALE_CONDUCTE[material_acm]['v_max']} m/s")
                    st.caption(f"Re = {rezultat_acm['reynolds']:.0f}")
                
                with col3:
                    st.metric("Pierderi liniare", f"{rezultat_acm['h_lin_m']:.3f} mCA")
                    st.caption(f"i = {rezultat_acm['i_specific_pa_m']:.0f} Pa/m")
                    st.caption(f"λ = {rezultat_acm['lambda']:.4f}")
                
                with col4:
                    st.metric("Pierderi locale", f"{rezultat_acm['h_loc_m']:.3f} mCA")
                    st.metric("Pierderi totale", f"{rezultat_acm['h_total_m']:.3f} mCA")
                
                # Grafic comparație ACM vs ARM
                if consumatori_selectati_arm and rezultat_arm:
                    st.markdown("---")
                    st.subheader("📊 Comparație ARM vs ACM")
                    
                    fig_comp = go.Figure()
                    fig_comp.add_trace(go.Bar(
                        name='Debit',
                        x=['ARM', 'ACM'],
                        y=[debit_calc_arm, debit_calc_acm],
                        marker_color=['#2196f3', '#ff5722']
                    ))
                    fig_comp.update_layout(
                        title="Debite de calcul",
                        yaxis_title="Debit (l/s)",
                        height=300
                    )
                    st.plotly_chart(fig_comp, use_container_width=True)
    
    # =============== TAB CANALIZARE MENAJERĂ ===============
    with tab_principal[2]:
        st.info(f"🚽 **Calculator pentru canalizare menajeră - {destinatie_aleasa}**")
        
        st.markdown(f"""
        <div class="info-box">
            <strong>Coeficient simultaneitate k = {config_destinatie['k_canalizare']}</strong><br>
            <small>Conform tabel 14.1 din I9-2022</small>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("📐 Dimensionare coloane și colectoare")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🏢 Date clădire:**")
            
            # Folosesc datele din sidebar
            st.metric("Număr etaje", numar_etaje)
            st.metric("Unități/etaj", unitati_per_etaj)
            
            # Calcul simplificat unități de scurgere
            # Presupun în medie 6 US per apartament/unitate
            unitati_scurgere_medie_per_unitate = 6
            unitati_scurgere_totale = numar_etaje * unitati_per_etaj * unitati_scurgere_medie_per_unitate
            
            # Ajustare în funcție de destinație
            if "birouri" in destinatie_aleasa.lower():
                unitati_scurgere_totale *= 0.7  # Mai puține US în birouri
            elif "hotel" in destinatie_aleasa.lower():
                unitati_scurgere_totale *= 1.2  # Mai multe US în hoteluri
            
            # Calculez debitul de canalizare
            if consumatori_selectati_arm:
                debit_can, formula_can = calcul_debit_canalizare_cu_destinatie(
                    consumatori_selectati_arm,
                    destinatie_aleasa
                )
                
                st.markdown(f"""
                <div class="success-box">
                    <strong>✅ Debit canalizare</strong><br>
                    <span style="font-size: 1.5em; color: #795548; font-weight: bold;">
                        {debit_can:.3f} l/s
                    </span><br>
                    <small>{formula_can}</small>
                </div>
                """, unsafe_allow_html=True)
            
            # Diametru coloană conform SR EN 12056-2
            if unitati_scurgere_totale <= 20:
                diam_coloana = 75
            elif unitati_scurgere_totale <= 160:
                diam_coloana = 110
            elif unitati_scurgere_totale <= 360:
                diam_coloana = 125
            else:
                diam_coloana = 160
            
            st.success(f"📏 **Diametru coloană: DN{diam_coloana}**")
            st.info(f"Unități de scurgere estimate: {unitati_scurgere_totale:.0f} US")
        
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
            diam_colector = diam_coloana if unitati_scurgere_totale < 100 else diam_coloana + 25
            st.metric("Diametru colector", f"DN{diam_colector}")
            st.metric("Pantă minimă", f"{panta_colector}%")
    
    # =============== TAB APE PLUVIALE ===============
    with tab_principal[3]:
        st.info("🌧️ **Calculator pentru ape pluviale**")
        
        st.subheader("🏗️ Date acoperire")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            suprafata_acoperis = st.number_input(
                "Suprafață acoperire (m²)",
                min_value=10.0, max_value=10000.0, value=100.0,
                step=10.0
            )
        
        with col2:
            intensitate_ploaie = st.number_input(
                "Intensitate ploaie (l/s·ha)",
                min_value=100, max_value=500, value=400,
                step=10,
                help="Conform STAS 1795, frecvență 1/5 ani pentru zone urbane"
            )
        
        with col3:
            coef_scurgere = st.slider(
                "Coeficient scurgere φ",
                min_value=0.5, max_value=1.0, value=0.9, step=0.05,
                help="0.9 pentru acoperiș dur, 0.5 pentru acoperiș verde"
            )
        
        # Calcul debit pluvial
        debit_pluvial = 0.0001 * intensitate_ploaie * coef_scurgere * suprafata_acoperis
        
        st.markdown(f"""
        <div class="success-box">
            <strong>✅ Debit pluvial de calcul</strong><br>
            <span style="font-size: 1.5em; color: #03a9f4; font-weight: bold;">
                {debit_pluvial:.3f} l/s
            </span><br>
            <small>Vc,i = 0.0001 × {intensitate_ploaie} × {coef_scurgere} × {suprafata_acoperis:.0f} = {debit_pluvial:.3f} l/s</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Dimensionare coloane pluviale
        st.subheader("📏 Dimensionare coloană pluvială")
        
        col1, col2 = st.columns(2)
        
        with col1:
            inaltime_coloana_pluv = st.number_input(
                "Înălțime coloană (m)",
                min_value=3.0, max_value=100.0, value=20.0,
                step=1.0
            )
            
            # Diametru coloană conform SR EN 12056-3
            if debit_pluvial <= 1.5:
                diam_coloana_pluv = 50
            elif debit_pluvial <= 2.5:
                diam_coloana_pluv = 70
            elif debit_pluvial <= 4.0:
                diam_coloana_pluv = 90
            elif debit_pluvial <= 7.0:
                diam_coloana_pluv = 110
            else:
                diam_coloana_pluv = 125
            
            st.success(f"📏 **Diametru coloană: DN{diam_coloana_pluv}**")
        
        with col2:
            st.write("**📊 Receptor pluvial:**")
            
            # Diametru receptor
            if debit_pluvial <= 4.0:
                diam_receptor = 110
            else:
                diam_receptor = 125
            
            st.metric("Diametru receptor", f"DN{diam_receptor}")
            
            # Înălțime utilă receptor
            inaltime_receptor = 14  # cm, standard
            st.metric("Înălțime utilă", f"{inaltime_receptor} cm")
        
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
    
    # =============== TAB ECHIPAMENTE ===============
    with tab_principal[4]:
        st.info("⚡ **Calculator echipamente și sisteme**")
        
        st.subheader("🔧 Stație de pompare/Hidrofor")
        
        if consumatori_selectati_arm:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**💧 Parametri rețea:**")
                
                # Presiune necesară în punctul cel mai defavorizat
                presiune_consumator_max = max([c["presiune_min"] for c in consumatori_selectati_arm])
                
                st.metric("Presiune minimă consumator", f"{presiune_consumator_max:.0f} mCA")
                
                if rezultat_arm:
                    presiune_pierderi = rezultat_arm['h_total_m']
                    st.metric("Pierderi totale rețea", f"{presiune_pierderi:.2f} mCA")
                else:
                    presiune_pierderi = 10.0  # estimare
                    st.metric("Pierderi estimate rețea", f"{presiune_pierderi:.0f} mCA")
                
                inaltime_geometrica = st.number_input(
                    "Înălțime geometrică (m)",
                    min_value=0.0, max_value=100.0, value=15.0,
                    help="Diferența de nivel între sursa de apă și consumatorul cel mai înalt"
                )
                
                presiune_necesara = presiune_consumator_max + presiune_pierderi + inaltime_geometrica
                
                st.markdown(f"""
                <div class="success-box">
                    <strong>✅ Presiune necesară pompă</strong><br>
                    <span style="font-size: 1.5em; color: #4caf50; font-weight: bold;">
                        {presiune_necesara:.1f} mCA
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.write("**⚙️ Selectare pompă:**")
                
                debit_pompa = debit_calc_arm * 3.6  # conversie în m³/h
                
                st.metric("Debit pompă", f"{debit_pompa:.2f} m³/h")
                st.metric("Înălțime pompă", f"{presiune_necesara:.1f} mCA")
                
                # Putere pompă
                randament = 0.65  # randament estimat
                putere_pompa = (debit_pompa/3600 * presiune_necesara * 9810) / (1000 * randament)
                
                st.metric("Putere pompă necesară", f"{putere_pompa:.2f} kW")
                
                # Volum hidrofor
                nr_porniri_ora = 20  # standard
                volum_hidrofor = (debit_pompa * 1000) / (4 * nr_porniri_ora)
                
                st.metric("Volum minim hidrofor", f"{volum_hidrofor:.0f} litri")
        
        else:
            st.warning("⚠️ Selectați mai întâi consumatorii în tab-ul 'Dimensionare Apă Rece'")
        
        # Preparare ACM
        st.markdown("---")
        st.subheader("🔥 Preparare apă caldă menajeră")
        
        if consumatori_selectati_acm:
            necesar_acm_zi = calcul_necesar_zilnic_maxim(destinatie_aleasa, numar_total_persoane, "acm")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**📊 Necesar ACM:**")
                st.metric("Necesar zilnic", f"{necesar_acm_zi['Q_max_zi']:.0f} l/zi")
                st.metric("Necesar orar maxim", f"{necesar_acm_zi['Q_max_orar']:.1f} l/h")
                
                # Capacitate boiler
                coef_acumulare = st.slider(
                    "Coeficient acumulare",
                    min_value=0.5, max_value=2.0, value=1.0, step=0.1,
                    help="1.0 = boiler egal cu necesarul orar maxim"
                )
                
                capacitate_boiler = necesar_acm_zi['Q_max_orar'] * coef_acumulare
                st.success(f"📊 **Capacitate boiler: {capacitate_boiler:.0f} litri**")
            
            with col2:
                st.write("**🔥 Putere termică:**")
                
                temp_rece = st.number_input("Temperatură apă rece (°C)", 5, 20, 10)
                temp_calda = st.number_input("Temperatură ACM (°C)", 50, 80, 60)
                
                delta_t = temp_calda - temp_rece
                
                # Putere = Q * ρ * c * ΔT / t
                # Q = l/h, ρ = 1 kg/l, c = 4.18 kJ/kg·K
                putere_termica = (necesar_acm_zi['Q_max_orar'] * 4.18 * delta_t) / 3600
                
                st.metric("Putere termică necesară", f"{putere_termica:.1f} kW")
                
                # Timpi
                timp_incalzire = (capacitate_boiler * 4.18 * delta_t) / (putere_termica * 3.6)
                st.metric("Timp încălzire boiler", f"{timp_incalzire:.0f} min")
    
    # =============== TAB RAPOARTE ===============
    with tab_principal[5]:
        st.info("📊 **Generator de rapoarte tehnice**")
        
        st.subheader("📄 Export rezultate")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📋 Informații raport:**")
            
            st.write(f"**Proiect:** {nume_proiect}")
            st.write(f"**Beneficiar:** {beneficiar if beneficiar else 'N/A'}")
            st.write(f"**Destinație:** {destinatie_aleasa}")
            st.write(f"**Proiectant:** Ing. Luca Obejdeanu")
            
            st.markdown("---")
            
            st.write("**Conținut raport:**")
            include_arm = st.checkbox("Dimensionare ARM", value=True)
            include_acm = st.checkbox("Dimensionare ACM", value=True)
            include_canalizare = st.checkbox("Canalizare menajeră", value=True)
            include_pluviale = st.checkbox("Ape pluviale", value=True)
            include_echipamente = st.checkbox("Echipamente", value=True)
        
        with col2:
            st.write("**📊 Statistici proiect:**")
            
            if consumatori_selectati_arm:
                st.metric("Total consumatori ARM", sum(c["cantitate"] for c in consumatori_selectati_arm))
                st.metric("Debit calcul ARM", f"{debit_calc_arm:.3f} l/s")
            
            if consumatori_selectati_acm:
                st.metric("Total consumatori ACM", sum(c["cantitate"] for c in consumatori_selectati_acm))
                st.metric("Debit calcul ACM", f"{debit_calc_acm:.3f} l/s")
            
            st.metric("Etaje clădire", numar_etaje)
            st.metric("Persoane totale", numar_total_persoane)
        
        if st.button("📥 **Generează Raport**", type="primary"):
            st.success("✅ Raport generat cu succes!")
            
            st.info("""
            ℹ️ **Nota:** Funcționalitatea completă de generare rapoarte PDF/Excel 
            va fi implementată în versiunea următoare folosind bibliotecile 
            reportlab/xlsxwriter.
            """)

# ======================== FOOTER ========================
def footer():
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px;'>
        <h4 style='color: #1e3d59; margin: 0;'>Calculator Profesional Instalații Sanitare</h4>
        <p style='color: #5c7080; margin: 10px 0;'>Conform normativelor românești în vigoare: I9-2022, SR 1343-1:2006, STAS 1795, SR EN 12056</p>
        <p style='color: #8b9dc3; font-size: 14px; margin: 5px 0;'>
            <strong>Designed by Ing. Luca Obejdeanu</strong>
        </p>
        <p style='color: #8b9dc3; font-size: 12px; margin: 5px 0;'>
            © 2024 | Versiunea 2.0 cu Destinație Clădire | Contact: luca.obejdeanu@gmail.com
        </p>
    </div>
    """, unsafe_allow_html=True)

# ======================== RULARE APLICAȚIE ========================
if __name__ == "__main__":
    main()
    footer()
