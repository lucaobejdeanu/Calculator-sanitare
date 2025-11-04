import streamlit as st
import pandas as pd
import numpy as np
import math
from typing import List, Dict, Tuple

# ======================== CONFIGURARE PAGINĂ ========================
st.set_page_config(
    page_title="Calculator Sanitare Pro I9-2022",
    page_icon="💧",
    layout="wide"
)

# ======================== CONSTANTE ========================
G = 9.81  # gravitație m/s²

# ======================== BAZE DE DATE ========================

# Materiale conducte cu date reale din piață
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
        "info": "Flexibil, rezistent coroziune, montaj rapid"
    },
    "Oțel zincat": {
        "rugozitate_mm": 0.15,
        "diametre_mm": {15: 12, 20: 16, 25: 20, 32: 26, 40: 32, 50: 40, 
                       65: 52, 80: 66, 100: 82},
        "v_max": 2.0,
        "info": "Uzual în clădiri vechi, corozibil"
    }
}

# Aparate sanitare cu PRESIUNI MINIME conform I9-2022
APARATE_SANITARE = {
    "WC cu rezervor": {
        "debit": 0.12,
        "unitate": 1.0,
        "presiune_min": 10.0,  # mCA
        "diametru_min": 10,
        "categorie": "Baie",
        "pierderi_automate": {
            "Cot cu talpă": 1.5,
            "Robinet colar - Robinet": 10.0,
            "Robinet colar - Cot": 1.0,
            "Robinet colar - Reducție": 0.5
        }
    },
    "WC jet sub presiune": {
        "debit": 1.5,
        "unitate": 15.0,
        "presiune_min": 25.0,
        "diametru_min": 10,
        "categorie": "Baie",
        "pierderi_automate": {
            "Cot cu talpă": 1.5,
            "Robinet": 10.0,
            "Cot": 1.0,
            "Reducție": 0.5
        }
    },
    "Lavoar": {
        "debit": 0.10,
        "unitate": 1.5,
        "presiune_min": 10.0,
        "diametru_min": 10,
        "categorie": "Baie",
        "pierderi_automate": {
            "Cot cu talpă": 1.5,
            "Baterie cu perlator": 10.0,
            "Reducție": 0.5
        }
    },
    "Lavoar grup sanitar": {
        "debit": 0.15,
        "unitate": 1.5,
        "presiune_min": 10.0,
        "diametru_min": 10,
        "categorie": "Baie",
        "pierderi_automate": {
            "Cot cu talpă": 1.5,
            "Baterie": 10.0,
            "Reducție": 0.5
        }
    },
    "Bideu": {
        "debit": 0.10,
        "unitate": 1.0,
        "presiune_min": 10.0,
        "diametru_min": 10,
        "categorie": "Baie",
        "pierderi_automate": {
            "Cot cu talpă": 1.5,
            "Baterie": 10.0,
            "Reducție": 0.5
        }
    },
    "Duș": {
        "debit": 0.20,
        "unitate": 2.0,
        "presiune_min": 12.0,
        "diametru_min": 12,
        "categorie": "Baie",
        "pierderi_automate": {
            "Cot cu talpă": 1.5,
            "Baterie dus": 10.0,
            "Reducție": 0.5
        }
    },
    "Cadă < 150L": {
        "debit": 0.25,
        "unitate": 3.0,
        "presiune_min": 13.0,
        "diametru_min": 13,
        "categorie": "Baie",
        "pierderi_automate": {
            "Cot cu talpă": 1.5,
            "Baterie cada": 10.0,
            "Reducție": 0.5
        }
    },
    "Cadă > 150L": {
        "debit": 0.33,
        "unitate": 4.0,
        "presiune_min": 13.0,
        "diametru_min": 13,
        "categorie": "Baie",
        "pierderi_automate": {
            "Cot cu talpă": 1.5,
            "Baterie cada": 10.0,
            "Reducție": 0.5
        }
    },
    "Spălător vase": {
        "debit": 0.20,
        "unitate": 2.0,
        "presiune_min": 12.0,
        "diametru_min": 12,
        "categorie": "Bucătărie",
        "pierderi_automate": {
            "Cot cu talpă": 1.5,
            "Baterie chiuvetă": 10.0,
            "Reducție": 0.5
        }
    },
    "Mașină spălat vase": {
        "debit": 0.20,
        "unitate": 2.0,
        "presiune_min": 12.0,
        "diametru_min": 12,
        "categorie": "Bucătărie",
        "pierderi_automate": {
            "Cot cu talpă": 1.5,
            "Robinet colar - Robinet": 10.0,
            "Robinet colar - Reducție marire": 0.5
        }
    },
    "Mașină spălat rufe": {
        "debit": 0.20,
        "unitate": 2.0,
        "presiune_min": 12.0,
        "diametru_min": 12,
        "categorie": "Utilitate",
        "pierderi_automate": {
            "Cot cu talpă": 1.5,
            "Robinet colar - Robinet": 10.0,
            "Robinet colar - Reducție marire": 0.5
        }
    },
    "Robinet serviciu 1/2\"": {
        "debit": 0.20,
        "unitate": 2.0,
        "presiune_min": 12.0,
        "diametru_min": 15,
        "categorie": "Utilitate",
        "pierderi_automate": {
            "Cot cu talpă": 1.5,
            "Robinet": 10.0
        }
    },
    "Robinet serviciu 3/4\"": {
        "debit": 0.42,
        "unitate": 4.0,
        "presiune_min": 12.0,
        "diametru_min": 20,
        "categorie": "Utilitate",
        "pierderi_automate": {
            "Cot cu talpă": 1.5,
            "Robinet": 10.0
        }
    }
}

# Coeficienți pentru calcul debite conform I9-2022
COEFICIENTI_CLADIRE = {
    "Clădiri de locuit": {
        "metoda": "Metoda B",
        "a": 0.45,
        "b": 0.20,
        "v_min": 0.20,
        "E_min": 1.0,
        "descriere": "Rezidențial - factor simultaneitate"
    },
    "Clădiri administrative": {
        "metoda": "Metoda C",
        "a": 0.55,
        "b": 0.25,
        "v_min": 0.30,
        "E_min": 1.5,
        "descriere": "Birouri - unități de încărcare"
    },
    "Hoteluri cu grup sanitar în cameră": {
        "metoda": "Metoda C",
        "a": 0.60,
        "b": 0.27,
        "v_min": 0.36,
        "E_min": 1.8,
        "descriere": "Hotel - unități de încărcare"
    },
    "Instituții învățământ": {
        "metoda": "Metoda C",
        "a": 0.60,
        "b": 0.27,
        "v_min": 0.36,
        "E_min": 1.8,
        "descriere": "Școli - unități de încărcare"
    },
    "Spitale, cantine, restaurante": {
        "metoda": "Metoda C",
        "a": 0.67,
        "b": 0.30,
        "v_min": 0.44,
        "E_min": 2.2,
        "descriere": "Medical/Alimentație - unități"
    },
    "Hoteluri cu grup sanitar comun": {
        "metoda": "Metoda C",
        "a": 0.85,
        "b": 0.38,
        "v_min": 0.72,
        "E_min": 3.6,
        "descriere": "Hotel comun - unități"
    },
    "Cămine, internate, băi publice": {
        "metoda": "Metoda C",
        "a": 1.00,
        "b": 0.45,
        "v_min": 1.00,
        "E_min": 5.0,
        "descriere": "Colectiv - unități"
    },
    "Vestiare ateliere/producție": {
        "metoda": "Metoda C",
        "a": 2.00,
        "b": 0.90,
        "v_min": 4.00,
        "E_min": 20.0,
        "descriere": "Industrial - unități"
    }
}

# Pierderi locale standardizate - OBLIGATORII pe instalație
PIERDERI_OBLIGATORII = {
    "Contor apă": {"zeta": 6.0, "descriere": "Obligatoriu la branșament, max 6 mH2O conform I9-2022"},
    "Filtru după contor": {"zeta": 3.0, "descriere": "Obligatoriu pentru protecție instalație"},
    "Robinet închidere branșament": {"zeta": 0.2, "descriere": "Vană cu bilă la branșament"}
}

# Pierderi locale OPȚIONALE
PIERDERI_OPTIONALE = {
    "Reductor presiune": {"zeta": 1.5, "descriere": "Dacă presiunea rețea > 6 bar"},
    "Distribuitor/Colector": {"zeta": 2.0, "descriere": "Pentru instalații cu colector"}
}

# Pierderi locale pe TRONSON (automate)
PIERDERI_TRONSON = {
    "Teu trecere la racord": {"zeta": 0.5, "descriere": "Automat de la tronsonul 2"},
    "Vană închidere derivație": {"zeta": 0.2, "descriere": "Pe fiecare tronson"}
}

# Pierderi locale EXTRA (utilizator)
PIERDERI_EXTRA = {
    "Cot 90° standard": 1.0,
    "Cot 45°": 0.4,
    "Curbă 90°": 0.5,
    "Teu derivație": 1.5,
    "Reducție": 0.3,
    "Vană cu bilă": 0.2,
    "Vană cu ventil": 4.0,
    "Filtru": 3.0,
    "Clapetă reținere": 2.0
}

# ======================== FUNCȚII CALCUL ========================

def calculeaza_viscozitate(temperatura: float) -> float:
    """Viscozitate cinematică apă în funcție de temperatură"""
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
            return max(0.008, min(0.1, lambda_val))  # Limitare rezonabilă
        except:
            return 0.02

def calculeaza_debit_calcul(tip_cladire: str, v_total: float, E_total: float, 
                           aplica_siguranta: bool) -> Tuple[float, str]:
    """Calculează debitul de calcul conform I9-2022"""
    coef = COEFICIENTI_CLADIRE[tip_cladire]
    
    if coef["metoda"] == "Metoda B":
        if v_total >= coef["v_min"]:
            debit_calc = coef["a"] * math.sqrt(v_total)
            formula = f"{coef['a']} × √{v_total:.3f}"
        else:
            debit_calc = v_total
            formula = f"{v_total:.3f} (sub limită)"
    else:  # Metoda C
        if E_total >= coef["E_min"]:
            debit_calc = coef["b"] * math.sqrt(E_total)
            formula = f"{coef['b']} × √{E_total:.1f}"
        else:
            debit_calc = 0.2 * E_total
            formula = f"0.2 × {E_total:.1f} (sub limită)"
    
    if aplica_siguranta:
        debit_calc *= 1.1
        formula += " × 1.1"
    
    return debit_calc, formula

def dimensioneaza_conducta(debit_m3s: float, material: str, temperatura: float) -> Dict:
    """Dimensionează conducta și calculează parametrii hidraulici"""
    if debit_m3s <= 0:
        return None
    
    info_material = MATERIALE_CONDUCTE[material]
    rugozitate_mm = info_material["rugozitate_mm"]
    diametre = info_material["diametre_mm"]
    v_max = info_material["v_max"]
    viscozitate = calculeaza_viscozitate(temperatura)
    
    rezultate_valide = []
    
    for dn, di_mm in diametre.items():
        di_m = di_mm / 1000
        aria = math.pi * (di_m ** 2) / 4
        viteza = debit_m3s / aria
        
        # Verificare viteză maximă
        if viteza > v_max:
            continue
        
        # Calcul hidraulic
        reynolds = calculeaza_reynolds(viteza, di_m, viscozitate)
        rugozitate_rel = (rugozitate_mm / 1000) / di_m
        lambda_val = calculeaza_lambda_haaland(reynolds, rugozitate_rel)
        
        # Pierdere unitară: i = λ × v² / (2gD)
        pierdere_unitara = lambda_val * (viteza ** 2) / (2 * G * di_m)
        
        rezultate_valide.append({
            "dn": dn,
            "diametru": di_mm,
            "viteza": viteza,
            "reynolds": reynolds,
            "lambda": lambda_val,
            "pierdere_unitara": pierdere_unitara
        })
    
    if not rezultate_valide:
        return None
    
    # Returnează cel mai mic diametru valid
    return min(rezultate_valide, key=lambda x: x["dn"])

def calculeaza_pierderi_locale(viteza: float, lista_zeta: List[float]) -> float:
    """h_loc = Σζ × v² / (2g)"""
    if viteza <= 0:
        return 0
    suma_zeta = sum(lista_zeta)
    return suma_zeta * (viteza ** 2) / (2 * G)

# ======================== INIȚIALIZARE STATE ========================
if 'tronsoane' not in st.session_state:
    st.session_state.tronsoane = []

if 'pierderi_obligatorii_active' not in st.session_state:
    st.session_state.pierderi_obligatorii_active = {
        "Contor apă": True,
        "Filtru după contor": True,
        "Robinet închidere branșament": True
    }

if 'pierderi_optionale_active' not in st.session_state:
    st.session_state.pierderi_optionale_active = {}

# ======================== INTERFAȚĂ ========================

st.title("💧 Calculator Instalații Sanitare Profesional I9-2022")
st.markdown("**Versiune 5.0 Pro** - Pierderi automate, presiuni minime, bibliotecă extinsă materiale")
st.divider()

# ======================== SIDEBAR ========================
with st.sidebar:
    st.header("⚙️ Configurare Proiect")
    
    tip_instalatie = st.radio(
        "Tip instalație:",
        ["🔵 Apă rece", "🔴 Apă caldă"]
    )
    
    temperatura = 10 if "rece" in tip_instalatie else 55
    st.caption(f"**Temperatură:** {temperatura}°C")
    
    material = st.selectbox(
        "Material conducte:",
        list(MATERIALE_CONDUCTE.keys())
    )
    
    with st.expander("📋 Info Material"):
        info = MATERIALE_CONDUCTE[material]
        st.caption(f"**k:** {info['rugozitate_mm']} mm")
        st.caption(f"**v_max:** {info['v_max']} m/s")
        st.caption(f"**DN:** {len(info['diametre_mm'])} mărimi")
        st.info(info['info'])
    
    tip_cladire = st.selectbox(
        "Tip clădire:",
        list(COEFICIENTI_CLADIRE.keys())
    )
    
    metoda_auto = COEFICIENTI_CLADIRE[tip_cladire]["metoda"]
    st.info(f"**{metoda_auto}** (automat)")
    st.caption(COEFICIENTI_CLADIRE[tip_cladire]["descriere"])
    
    aplica_siguranta = st.checkbox(
        "Coeficient +10% siguranță",
        value=True,
        help="Recomandat I9-2022"
    )
    
    st.divider()
    
    presiune_retea = st.number_input(
        "Presiune rețea (mCA):",
        min_value=0.0,
        max_value=100.0,
        value=30.0,
        step=5.0
    )
    
    st.divider()
    
    # Pierderi obligatorii
    st.subheader("🔧 Pierderi Obligatorii")
    for nume, info in PIERDERI_OBLIGATORII.items():
        activ = st.checkbox(
            f"{nume} (ζ={info['zeta']})",
            value=st.session_state.pierderi_obligatorii_active.get(nume, True),
            key=f"obl_{nume}",
            help=info['descriere']
        )
        st.session_state.pierderi_obligatorii_active[nume] = activ
    
    # Pierderi opționale
    with st.expander("⚙️ Pierderi Opționale"):
        for nume, info in PIERDERI_OPTIONALE.items():
            activ = st.checkbox(
                f"{nume} (ζ={info['zeta']})",
                value=st.session_state.pierderi_optionale_active.get(nume, False),
                key=f"opt_{nume}",
                help=info['descriere']
            )
            st.session_state.pierderi_optionale_active[nume] = activ

# ======================== SECȚIUNE PRINCIPALĂ ========================

st.header("📐 Definire Tronsoane")

col_info1, col_info2 = st.columns([3, 1])

with col_info1:
    st.info("""
    **🎯 Workflow:**
    1. **Tronson 1** = consumatorul cel mai dezavantajat
    2. Adaugă aparate → pierderi locale **calculate automat**
    3. **Tronson 2+** = aparatele anterioare sunt **automat incluse**
    4. Calculează dimensionarea completă
    """)

with col_info2:
    st.metric("Tronsoane", len(st.session_state.tronsoane))
    
    if st.button("➕ Adaugă", type="primary", use_container_width=True):
        st.session_state.tronsoane.append({
            'nr': len(st.session_state.tronsoane) + 1,
            'aparate_noi': {},
            'lungime': 5.0,
            'dif_nivel': 3.0 if len(st.session_state.tronsoane) == 0 else 0.0,
            'pierderi_extra': {}
        })
        st.rerun()
    
    if len(st.session_state.tronsoane) > 0 and st.button("🗑️ Șterge", use_container_width=True):
        st.session_state.tronsoane.pop()
        st.rerun()

st.divider()

# ======================== DEFINIRE TRONSOANE ========================

for idx, tronson in enumerate(st.session_state.tronsoane):
    nr_tronson = tronson['nr']
    
    # Calcul aparate cumulate
    aparate_cumulate = {}
    for i in range(idx + 1):
        for aparat, nr in st.session_state.tronsoane[i]['aparate_noi'].items():
            aparate_cumulate[aparat] = aparate_cumulate.get(aparat, 0) + nr
    
    total_ap_cumulate = sum(aparate_cumulate.values())
    
    with st.expander(
        f"🔹 **TRONSON {nr_tronson}**" + 
        (f" - {total_ap_cumulate} aparate" if total_ap_cumulate > 0 else ""),
        expanded=(idx == len(st.session_state.tronsoane) - 1)
    ):
        
        # Afișare moștenire
        if idx > 0:
            ap_anterioare = {}
            for i in range(idx):
                for ap, nr in st.session_state.tronsoane[i]['aparate_noi'].items():
                    ap_anterioare[ap] = ap_anterioare.get(ap, 0) + nr
            
            if ap_anterioare:
                st.success(f"✅ **Moșteninește:** " + 
                         ", ".join([f"{nr}× {ap}" for ap, nr in ap_anterioare.items()]))
        
        # Selectare aparate NOI
        st.markdown("### Aparate NOI:")
        
        # Grupare pe categorii
        categorii = {}
        for ap, date in APARATE_SANITARE.items():
            cat = date.get("categorie", "Alte")
            if cat not in categorii:
                categorii[cat] = []
            categorii[cat].append(ap)
        
        for categorie, lista_ap in categorii.items():
            st.markdown(f"**{categorie}:**")
            cols = st.columns(min(3, len(lista_ap)))
            
            for i, aparat in enumerate(lista_ap):
                with cols[i % 3]:
                    date_ap = APARATE_SANITARE[aparat]
                    
                    nr_ap = st.number_input(
                        aparat,
                        min_value=0,
                        max_value=50,
                        value=tronson['aparate_noi'].get(aparat, 0),
                        key=f"t{nr_tronson}_{aparat}",
                        help=f"Q: {date_ap['debit']} L/s | Ui: {date_ap['unitate']} | Pmin: {date_ap['presiune_min']} mCA"
                    )
                    
                    if nr_ap > 0:
                        st.caption(f"💧{date_ap['debit']} L/s | 📊{date_ap['unitate']} Ui | ⚡{date_ap['presiune_min']} mCA")
                        tronson['aparate_noi'][aparat] = nr_ap
                    elif aparat in tronson['aparate_noi']:
                        del tronson['aparate_noi'][aparat]
        
        st.divider()
        
        # Calcul totale
        total_debit = sum(APARATE_SANITARE[ap]["debit"] * nr 
                         for ap, nr in aparate_cumulate.items())
        total_ui = sum(APARATE_SANITARE[ap]["unitate"] * nr 
                      for ap, nr in aparate_cumulate.items())
        
        # Calcul debit de calcul
        debit_calc, formula_debit = calculeaza_debit_calcul(
            tip_cladire, total_debit, total_ui, aplica_siguranta
        )
        
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        
        with col_t1:
            st.metric("Aparate", f"{total_ap_cumulate}")
        with col_t2:
            st.metric("Σ Debite", f"{total_debit:.3f} L/s")
        with col_t3:
            st.metric("Σ Ui", f"{total_ui:.1f}")
        with col_t4:
            st.metric("Q calcul", f"{debit_calc:.3f} L/s", 
                     help=f"Formula: {formula_debit}")
        
        st.divider()
        
        # Geometrie
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            lungime = st.number_input(
                "Lungime (m):",
                0.1, 100.0,
                float(tronson['lungime']),
                0.5,
                key=f"lung{nr_tronson}"
            )
            tronson['lungime'] = lungime
        
        with col_g2:
            dif_nivel = st.number_input(
                "Δh nivel (m):",
                -50.0, 50.0,
                float(tronson['dif_nivel']),
                0.5,
                key=f"dh{nr_tronson}",
                help="+ urcare, - coborâre"
            )
            tronson['dif_nivel'] = dif_nivel
        
        st.divider()
        
        # PIERDERI LOCALE
        st.markdown("### 🔧 Pierderi Locale")
        
        # AUTOMATE pentru aparate
        pierderi_aparate = []
        detalii_automate = []
        
        for aparat, nr_ap in aparate_cumulate.items():
            date_ap = APARATE_SANITARE[aparat]
            for nume_pierdere, zeta in date_ap["pierderi_automate"].items():
                pierderi_aparate.extend([zeta] * nr_ap)
                detalii_automate.append(f"{nr_ap}× {nume_pierdere} (ζ={zeta})")
        
        # AUTOMATE pe tronson
        pierderi_tronson_auto = []
        if idx > 0:  # De la tronsonul 2 încolo
            pierderi_tronson_auto.append(PIERDERI_TRONSON["Teu trecere la racord"]["zeta"])
            detalii_automate.append(f"Teu trecere racord (ζ={PIERDERI_TRONSON['Teu trecere la racord']['zeta']})")
        
        pierderi_tronson_auto.append(PIERDERI_TRONSON["Vană închidere derivație"]["zeta"])
        detalii_automate.append(f"Vană închidere (ζ={PIERDERI_TRONSON['Vană închidere derivație']['zeta']})")
        
        total_automate = sum(pierderi_aparate) + sum(pierderi_tronson_auto)
        
        with st.expander(f"✅ Pierderi AUTOMATE (Σζ = {total_automate:.1f})", expanded=False):
            for detaliu in detalii_automate:
                st.caption(f"• {detaliu}")
        
        # EXTRA
        st.markdown("**Pierderi EXTRA (opțional):**")
        
        cols_extra = st.columns(3)
        pierderi_extra_vals = []
        
        for i, (nume, zeta) in enumerate(PIERDERI_EXTRA.items()):
            with cols_extra[i % 3]:
                nr = st.number_input(
                    f"{nume} (ζ={zeta}):",
                    0, 50, 
                    tronson['pierderi_extra'].get(nume, 0),
                    key=f"extra{nr_tronson}_{nume}"
                )
                tronson['pierderi_extra'][nume] = nr
                if nr > 0:
                    pierderi_extra_vals.extend([zeta] * nr)
        
        total_extra = sum(pierderi_extra_vals)
        total_zeta_tronson = total_automate + total_extra
        
        col_z1, col_z2, col_z3 = st.columns(3)
        with col_z1:
            st.metric("Σζ Automate", f"{total_automate:.1f}")
        with col_z2:
            st.metric("Σζ Extra", f"{total_extra:.1f}")
        with col_z3:
            st.metric("**Σζ TOTAL**", f"{total_zeta_tronson:.1f}")

# ======================== CALCUL DIMENSIONARE ========================

if len(st.session_state.tronsoane) > 0:
    st.divider()
    
    if st.button("🔬 CALCULEAZĂ DIMENSIONARE", type="primary", use_container_width=True):
        st.header("📊 Rezultate Dimensionare")
        
        # Calculare pierderi obligatorii și opționale
        pierderi_instalatie = []
        for nume, activ in st.session_state.pierderi_obligatorii_active.items():
            if activ:
                pierderi_instalatie.append(PIERDERI_OBLIGATORII[nume]["zeta"])
        
        for nume, activ in st.session_state.pierderi_optionale_active.items():
            if activ:
                pierderi_instalatie.append(PIERDERI_OPTIONALE[nume]["zeta"])
        
        # Procesare tronsoane
        rezultate = []
        h_lin_totala = 0
        h_loc_totala = 0
        dif_nivel_totala = 0
        presiune_min_necesara = 0  # Se determină din tronsonul 1
        
        for idx, tronson in enumerate(st.session_state.tronsoane):
            nr_t = tronson['nr']
            
            # Aparate cumulate
            aparate_cum = {}
            for i in range(idx + 1):
                for ap, nr in st.session_state.tronsoane[i]['aparate_noi'].items():
                    aparate_cum[ap] = aparate_cum.get(ap, 0) + nr
            
            total_debit = sum(APARATE_SANITARE[ap]["debit"] * nr 
                             for ap, nr in aparate_cum.items())
            total_ui = sum(APARATE_SANITARE[ap]["unitate"] * nr 
                          for ap, nr in aparate_cum.items())
            
            # Presiune minimă necesară (din tronsonul 1)
            if idx == 0 and aparate_cum:
                presiune_min_necesara = max(
                    APARATE_SANITARE[ap]["presiune_min"] 
                    for ap in aparate_cum.keys()
                )
            
            # Debit calcul
            debit_calc, _ = calculeaza_debit_calcul(
                tip_cladire, total_debit, total_ui, aplica_siguranta
            )
            
            debit_m3s = debit_calc / 1000
            
            # Dimensionare
            rez_dim = dimensioneaza_conducta(debit_m3s, material, temperatura)
            
            if rez_dim:
                # Pierderi liniare
                h_lin = rez_dim['pierdere_unitara'] * tronson['lungime']
                
                # Pierderi locale TOATE
                toate_zeta = []
                
                # Din aparate
                for ap, nr_ap in aparate_cum.items():
                    for zeta in APARATE_SANITARE[ap]["pierderi_automate"].values():
                        toate_zeta.extend([zeta] * nr_ap)
                
                # Pe tronson
                if idx > 0:
                    toate_zeta.append(PIERDERI_TRONSON["Teu trecere la racord"]["zeta"])
                toate_zeta.append(PIERDERI_TRONSON["Vană închidere derivație"]["zeta"])
                
                # Extra
                for nume, nr in tronson['pierderi_extra'].items():
                    if nr > 0:
                        toate_zeta.extend([PIERDERI_EXTRA[nume]] * nr)
                
                # Pierderi instalație (doar pe primul tronson)
                if idx == 0:
                    toate_zeta.extend(pierderi_instalatie)
                
                h_loc = calculeaza_pierderi_locale(rez_dim['viteza'], toate_zeta)
                
                h_lin_totala += h_lin
                h_loc_totala += h_loc
                dif_nivel_totala += tronson['dif_nivel']
                
                rezultate.append({
                    "Tronson": nr_t,
                    "Aparate": ", ".join([f"{nr}{ap[:4]}" for ap, nr in aparate_cum.items()]),
                    "Q (L/s)": f"{debit_calc:.3f}",
                    "DN": rez_dim['diametru'],
                    "v (m/s)": f"{rez_dim['viteza']:.2f}",
                    "Re": f"{rez_dim['reynolds']:.0f}",
                    "λ": f"{rez_dim['lambda']:.4f}",
                    "L (m)": f"{tronson['lungime']:.1f}",
                    "i (‰)": f"{rez_dim['pierdere_unitara']*1000:.2f}",
                    "h_lin": f"{h_lin:.3f}",
                    "Σζ": f"{sum(toate_zeta):.1f}",
                    "h_loc": f"{h_loc:.3f}",
                    "Δh": f"{tronson['dif_nivel']:.1f}",
                    "h_total": f"{h_lin + h_loc:.3f}"
                })
        
        # Tabel
        if rezultate:
            df_rez = pd.DataFrame(rezultate)
            st.dataframe(df_rez, use_container_width=True, hide_index=True)
            
            st.divider()
            
            # Metrici
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            with col_m1:
                st.metric("Σ h_liniare", f"{h_lin_totala:.3f} mCA")
            with col_m2:
                st.metric("Σ h_locale", f"{h_loc_totala:.3f} mCA")
            with col_m3:
                st.metric("Σ Δh nivel", f"{dif_nivel_totala:.2f} m")
            with col_m4:
                h_totala = h_lin_totala + h_loc_totala
                st.metric("**h TOTALĂ**", f"{h_totala:.3f} mCA")
            
            st.divider()
            
            # Sarcină hidrodinamică
            st.header("⚡ Calcul Sarcină Hidrodinamică")
            
            col_s1, col_s2 = st.columns([1, 1])
            
            with col_s1:
                st.info(f"""
                **Presiune minimă necesară:**  
                **{presiune_min_necesara:.1f} mCA**
                
                Determinată automat din aparatele de pe tronsonul 1  
                (consumatorul cel mai dezavantajat)
                """)
            
            with col_s2:
                # Hu
                Hu = presiune_min_necesara + dif_nivel_totala
                st.metric("Hu - Sarcină utilă", f"{Hu:.2f} mCA",
                         help="Hu = Pmin + Δh_nivel")
                
                # Hr
                Hr = Hu + h_totala
                st.metric("Hr - Sarcină necesară", f"{Hr:.2f} mCA",
                         help="Hr = Hu + h_totală")
                
                # Hg
                Hg = Hr - presiune_retea
                
                if Hg > 0:
                    st.error(f"⚠️ **POMPĂ NECESARĂ**")
                    st.metric("Hg - Pompă", f"{Hg:.2f} mCA")
                    st.warning(f"Presiunea din rețea ({presiune_retea:.1f} mCA) NU este suficientă!")
                    st.info(f"💪 **Specificații pompă:**\n- Hg ≥ {Hg:.2f} mCA\n- Q = {debit_calc:.3f} L/s")
                else:
                    st.success("✅ **Presiune SUFICIENTĂ!**")
                    st.metric("Presiune excedentară", f"{abs(Hg):.2f} mCA")
            
            # Verificări
            st.divider()
            st.header("✅ Verificări I9-2022")
            
            v_max_normativ = 2.0 if "locuit" in tip_cladire.lower() else 3.0
            
            viteze_ok = True
            for rez in rezultate:
                v = float(rez["v (m/s)"])
                if v > v_max_normativ:
                    st.error(f"❌ Tronson {rez['Tronson']}: v = {v:.2f} m/s > {v_max_normativ} m/s")
                    viteze_ok = False
            
            if viteze_ok:
                st.success(f"✅ Viteze ≤ {v_max_normativ} m/s")
            
            if h_lin_totala > 0:
                raport = h_loc_totala / h_lin_totala
                if raport <= 0.5:
                    st.success(f"✅ Raport h_loc/h_lin = {raport:.2f} ≤ 0.5")
                else:
                    st.warning(f"⚠️ Raport h_loc/h_lin = {raport:.2f} > 0.5")
            
            # Export
            st.divider()
            csv = df_rez.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Descarcă CSV",
                csv,
                f"sanitare_{material.replace(' ', '_')}.csv",
                "text/csv",
                use_container_width=True
            )

else:
    st.info("👆 **Adaugă primul tronson pentru a începe!**")

# Footer
st.divider()
st.caption("""
**Calculator Instalații Sanitare v5.0 Pro** | Conform I9-2022  
✅ Presiuni minime automate | ✅ Pierderi standardizate | ✅ 6 materiale | ✅ Sistem progresiv  
© 2024 - Pentru ingineri ISC 🇷🇴
""")