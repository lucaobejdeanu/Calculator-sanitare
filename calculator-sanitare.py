import streamlit as st
import pandas as pd
import numpy as np
import math
from typing import List, Dict, Tuple
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO
import base64

# Import pentru PDF
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    PDF_AVAILABLE = True
except:
    PDF_AVAILABLE = False

# ======================== CONFIGURARE PAGINĂ ========================
st.set_page_config(
    page_title="Calculator Instalații Sanitare - Ing. Luca Obejdeanu",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================== INIȚIALIZARE SESSION STATE ========================
if 'tronsoane' not in st.session_state:
    st.session_state.tronsoane = []

if 'rezultate_calcul' not in st.session_state:
    st.session_state.rezultate_calcul = None

# ======================== CONSTANTE ========================
G = 9.81  # gravitație m/s²

# ======================== BAZE DE DATE CONSUMATORI ========================
# Pentru APĂ RECE - toți consumatorii
CONSUMATORI_AR = {
    "WC cu rezervor": {
        "debit": 0.10, "unitate": 1.0, "presiune_min": 5.0, "diametru_min": 10,
        "categorie": "Baie", "apa_calda": False
    },
    "WC cu robinet flotor": {
        "debit": 1.50, "unitate": 5.0, "presiune_min": 50.0, "diametru_min": 20,
        "categorie": "Baie", "apa_calda": False
    },
    "Pisoar": {
        "debit": 0.30, "unitate": 2.0, "presiune_min": 15.0, "diametru_min": 10,
        "categorie": "Baie", "apa_calda": False
    },
    "Lavoar": {
        "debit": 0.10, "unitate": 1.0, "presiune_min": 10.0, "diametru_min": 10,
        "categorie": "Baie", "apa_calda": True
    },
    "Bideu": {
        "debit": 0.10, "unitate": 1.0, "presiune_min": 10.0, "diametru_min": 10,
        "categorie": "Baie", "apa_calda": True
    },
    "Duș": {
        "debit": 0.20, "unitate": 2.0, "presiune_min": 12.0, "diametru_min": 12,
        "categorie": "Baie", "apa_calda": True
    },
    "Cadă < 150L": {
        "debit": 0.25, "unitate": 3.0, "presiune_min": 13.0, "diametru_min": 13,
        "categorie": "Baie", "apa_calda": True
    },
    "Cadă > 150L": {
        "debit": 0.33, "unitate": 4.0, "presiune_min": 13.0, "diametru_min": 13,
        "categorie": "Baie", "apa_calda": True
    },
    "Chiuvetă bucătărie": {
        "debit": 0.20, "unitate": 2.0, "presiune_min": 12.0, "diametru_min": 12,
        "categorie": "Bucătărie", "apa_calda": True
    },
    "Mașină spălat vase": {
        "debit": 0.20, "unitate": 2.0, "presiune_min": 12.0, "diametru_min": 10,
        "categorie": "Bucătărie", "apa_calda": True
    },
    "Mașină spălat rufe": {
        "debit": 0.20, "unitate": 2.0, "presiune_min": 12.0, "diametru_min": 10,
        "categorie": "Utilitate", "apa_calda": True
    },
    "Robinet 1/2\"": {
        "debit": 0.20, "unitate": 1.5, "presiune_min": 10.0, "diametru_min": 13,
        "categorie": "Utilitate", "apa_calda": False
    },
    "Robinet 3/4\"": {
        "debit": 0.40, "unitate": 2.5, "presiune_min": 10.0, "diametru_min": 19,
        "categorie": "Utilitate", "apa_calda": False
    },
    "Robinet grădină": {
        "debit": 0.70, "unitate": 3.5, "presiune_min": 15.0, "diametru_min": 19,
        "categorie": "Exterior", "apa_calda": False
    }
}

# Pentru APĂ CALDĂ - doar cei cu apă caldă
CONSUMATORI_AC = {k: v for k, v in CONSUMATORI_AR.items() if v["apa_calda"]}

# ======================== CORELAȚIE DN - DIAMETRE ========================
CORELARE_DN = {
    "PPR": {
        15: "d20", 20: "d25", 25: "d32", 32: "d40", 
        40: "d50", 50: "d63", 63: "d75", 75: "d90", 90: "d110"
    },
    "Oțel": {
        15: "1/2\"", 20: "3/4\"", 25: "1\"", 32: "1 1/4\"",
        40: "1 1/2\"", 50: "2\"", 65: "2 1/2\"", 80: "3\"", 100: "4\""
    },
    "Cupru": {
        12: "12×1", 15: "15×1", 18: "18×1", 22: "22×1", 
        28: "28×1.5", 35: "35×1.5", 42: "42×1.5", 54: "54×2"
    }
}

# ======================== MATERIALE CONDUCTE ========================
MATERIALE_CONDUCTE = {
    "PPR cu fibră de sticlă": {
        "rugozitate_mm": 0.001,
        "diametre_mm": {
            20: 16.6, 25: 20.4, 32: 26.2, 40: 32.6, 
            50: 40.8, 63: 51.4, 75: 61.2, 90: 73.6, 110: 90.0
        },
        "v_max": 2.0,
        "info": "PPR armat cu fibră, dilatare redusă"
    },
    "PPR simplu": {
        "rugozitate_mm": 0.0015,
        "diametre_mm": {
            20: 16.6, 25: 20.4, 32: 26.2, 40: 32.6,
            50: 40.8, 63: 51.4, 75: 61.2, 90: 73.6, 110: 90.0
        },
        "v_max": 2.0,
        "info": "Economic, pentru temperaturi < 70°C"
    },
    "PE-HD": {
        "rugozitate_mm": 0.002,
        "diametre_mm": {
            20: 14.4, 25: 20.4, 32: 26, 40: 32.6, 50: 40.8, 
            63: 51.4, 75: 61.4, 90: 73.6, 110: 90, 125: 102.2
        },
        "v_max": 2.5,
        "info": "Pentru branșamente și apă rece"
    },
    "Cupru": {
        "rugozitate_mm": 0.0015,
        "diametre_mm": {
            12: 10, 15: 13, 18: 16, 22: 20, 28: 26, 
            35: 33, 42: 40, 54: 52
        },
        "v_max": 2.5,
        "info": "Premium, antibacterian"
    },
    "Oțel zincat": {
        "rugozitate_mm": 0.15,
        "diametre_mm": {
            15: 16.0, 20: 21.7, 25: 27.3, 32: 36.0, 
            40: 41.9, 50: 53.1, 65: 68.9, 80: 80.9, 100: 105.3
        },
        "v_max": 3.0,
        "info": "Tradițional, rezistent"
    }
}

# Coeficienți pierderi locale
COEFICIENTI_PIERDERI_LOCALE = {
    "Teu derivație": 1.8,
    "Teu trecere": 0.3,
    "Cot 90°": 0.9,
    "Cot 45°": 0.4,
    "Reducție": 0.3,
    "Robinet cu sertar": 0.5,
    "Robinet cu bilă": 0.1,
    "Clapetă de sens": 2.5,
    "Filtru": 2.0,
    "Contor apă": 10.0
}

# ======================== FUNCȚII CALCUL ========================

def calcul_debit_probabilistic(consumatori: Dict[str, int], tip_apa: str = "rece") -> Tuple[float, float]:
    """
    Calculează debitul probabilistic conform SR 1343-1:2006
    Returnează (debit L/s, suma unități)
    """
    baza_consumatori = CONSUMATORI_AR if tip_apa == "rece" else CONSUMATORI_AC
    
    suma_debit_unitate = sum(
        baza_consumatori[cons]["debit"] * baza_consumatori[cons]["unitate"] * cant
        for cons, cant in consumatori.items() if cons in baza_consumatori
    )
    
    if suma_debit_unitate <= 0:
        return 0.0, 0.0
    elif suma_debit_unitate <= 0.2:
        debit = suma_debit_unitate
    elif suma_debit_unitate <= 1.6:
        debit = 0.2 + 0.25 * (suma_debit_unitate - 0.2)**0.5
    else:
        debit = 0.466 * suma_debit_unitate**0.5
    
    return debit, suma_debit_unitate

def reynolds(viteza: float, diametru: float, temperatura: float = 10.0) -> float:
    """Calculează numărul Reynolds"""
    vascozitate = 1.3e-6 if temperatura <= 10 else 1.0e-6
    return viteza * diametru / vascozitate

def factor_frecare_colebrook(re: float, rugozitate: float, diametru: float) -> float:
    """Calculează factorul de frecare prin Colebrook-White"""
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
        
        if abs(f_nou - f_vechi) < 1e-6:
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

def selectare_diametru(debit: float, material: str, v_max: float = None) -> Tuple[int, float, float]:
    """
    Selectează diametrul optim pentru debit dat
    Returnează (DN, Di, viteza)
    """
    if material not in MATERIALE_CONDUCTE:
        return 0, 0, 0
    
    info = MATERIALE_CONDUCTE[material]
    v_max = v_max or info["v_max"]
    
    for dn, di in sorted(info["diametre_mm"].items()):
        area = math.pi * (di/1000)**2 / 4
        viteza = debit / area if area > 0 else 0
        
        if viteza <= v_max:
            return dn, di, viteza
    
    # Dacă nu găsește, returnează ultimul disponibil
    dn = max(info["diametre_mm"].keys())
    di = info["diametre_mm"][dn]
    area = math.pi * (di/1000)**2 / 4
    viteza = debit / area if area > 0 else 0
    return dn, di, viteza

def get_diametru_specific(material: str, dn: int) -> str:
    """Obține notația specifică pentru diametru"""
    if "PPR" in material:
        return CORELARE_DN.get("PPR", {}).get(dn, f"d{dn}")
    elif "Cupru" in material:
        return CORELARE_DN.get("Cupru", {}).get(dn, f"{dn}×1")
    elif "Oțel" in material:
        return CORELARE_DN.get("Oțel", {}).get(dn, f"DN{dn}")
    else:
        return f"DN{dn}"

def genereaza_pdf(rezultate_ar: pd.DataFrame = None, rezultate_ac: pd.DataFrame = None, 
                  date_proiect: Dict = None) -> BytesIO:
    """Generează PDF cu rezultate"""
    if not PDF_AVAILABLE:
        return None
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Titlu
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e3d59'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph("MEMORIU TEHNIC INSTALAȚII SANITARE", title_style))
    elements.append(Spacer(1, 20))
    
    # Date proiect
    if date_proiect:
        info_style = ParagraphStyle(
            'Info',
            parent=styles['Normal'],
            fontSize=12,
            leading=16
        )
        
        elements.append(Paragraph(f"<b>Proiect:</b> {date_proiect.get('nume', 'N/A')}", info_style))
        elements.append(Paragraph(f"<b>Beneficiar:</b> {date_proiect.get('beneficiar', 'N/A')}", info_style))
        elements.append(Paragraph(f"<b>Proiectant:</b> Ing. Luca Obejdeanu", info_style))
        elements.append(Spacer(1, 30))
    
    # Tabel APĂ RECE
    if rezultate_ar is not None and not rezultate_ar.empty:
        elements.append(Paragraph("DIMENSIONARE APĂ RECE", styles['Heading2']))
        elements.append(Spacer(1, 10))
        
        # Convertire DataFrame la tabel
        data = [rezultate_ar.columns.tolist()] + rezultate_ar.values.tolist()
        
        table = Table(data, colWidths=[1.5*cm] + [2*cm] * (len(data[0])-1))
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        elements.append(PageBreak())
    
    # Tabel APĂ CALDĂ
    if rezultate_ac is not None and not rezultate_ac.empty:
        elements.append(Paragraph("DIMENSIONARE APĂ CALDĂ MENAJERĂ", styles['Heading2']))
        elements.append(Spacer(1, 10))
        
        data = [rezultate_ac.columns.tolist()] + rezultate_ac.values.tolist()
        
        table = Table(data, colWidths=[1.5*cm] + [2*cm] * (len(data[0])-1))
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    
    elements.append(Spacer(1, 50))
    elements.append(Paragraph("Document generat automat - Calculator Instalații Sanitare", footer_style))
    elements.append(Paragraph("Ing. Luca Obejdeanu © 2024", footer_style))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ======================== INTERFAȚA STREAMLIT ========================

def main():
    # Header
    st.markdown("""
    <h1 style='text-align: center; color: #1e3d59;'>
        Calculator Profesional Instalații Sanitare
    </h1>
    <h3 style='text-align: center; color: #5c7080;'>
        Conform I9-2022 și SR 1343-1:2006
    </h3>
    <p style='text-align: center; color: #8b9dc3; font-size: 14px;'>
        Dimensionare instalații alimentare cu apă pentru consum menajer
    </p>
    """, unsafe_allow_html=True)
    
    # Tabs principale
    tab_ar, tab_ac, tab_rapoarte, tab_doc = st.tabs([
        "💧 Apă Rece",
        "♨️ Apă Caldă Menajeră",
        "📊 Rapoarte",
        "📚 Documentație"
    ])
    
    # =============== TAB APĂ RECE ===============
    with tab_ar:
        st.info("💧 **Dimensionare conductă alimentare cu apă rece**")
        
        # Configurare generală
        with st.expander("⚙️ **Configurare sistem**", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                material = st.selectbox(
                    "Material conductă",
                    list(MATERIALE_CONDUCTE.keys()),
                    index=0
                )
                st.caption(MATERIALE_CONDUCTE[material]["info"])
            
            with col2:
                temperatura = st.number_input(
                    "Temperatură apă (°C)",
                    min_value=5.0, max_value=25.0, value=10.0
                )
            
            with col3:
                presiune_disponibila = st.number_input(
                    "Presiune disponibilă (mCA)",
                    min_value=10.0, max_value=100.0, value=30.0
                )
        
        st.markdown("---")
        
        # Gestiune tronsoane
        st.subheader("📏 Definire tronsoane")
        st.caption("⚠️ Tronsoanele se definesc de la consumatorul cel mai îndepărtat spre branșament. Debitele CRESC!")
        
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            if st.button("➕ Adaugă tronson", type="primary"):
                nr_nou = len(st.session_state.tronsoane) + 1
                st.session_state.tronsoane.append({
                    'nr': nr_nou,
                    'consumatori': {},
                    'lungime': 10.0,
                    'dif_nivel': 0.0,
                    'este_ultimul': (nr_nou == 1),  # Primul adăugat = ultimul fizic
                    'pierderi_locale': {}
                })
        
        with col_btn2:
            if st.button("🗑️ Șterge ultimul") and st.session_state.tronsoane:
                st.session_state.tronsoane.pop()
        
        with col_btn3:
            if st.button("🔄 Resetează tot"):
                st.session_state.tronsoane = []
                st.session_state.rezultate_calcul = None
        
        # Afișare tronsoane
        for idx, tronson in enumerate(st.session_state.tronsoane):
            with st.expander(f"**Tronson {tronson['nr']}** {'🏁 (Ultimul etaj - cel mai îndepărtat)' if tronson['este_ultimul'] else ''}", 
                           expanded=(idx == 0)):
                
                # Configurare tronson
                col_t1, col_t2, col_t3, col_t4 = st.columns(4)
                
                with col_t1:
                    tronson['lungime'] = st.number_input(
                        "Lungime (m)",
                        min_value=0.5, max_value=100.0, 
                        value=float(tronson['lungime']),
                        key=f"lung_ar_{idx}"
                    )
                
                with col_t2:
                    tronson['dif_nivel'] = st.number_input(
                        "Δh (m)",
                        min_value=-50.0, max_value=50.0,
                        value=float(tronson['dif_nivel']),
                        key=f"dh_ar_{idx}",
                        help="+ pentru urcare, - pentru coborâre"
                    )
                
                with col_t3:
                    tronson['este_ultimul'] = st.checkbox(
                        "Ultimul etaj",
                        value=tronson['este_ultimul'],
                        key=f"ultim_ar_{idx}",
                        help="Punctul cel mai defavorabil"
                    )
                
                with col_t4:
                    # Calculăm consumatorii cumulați
                    cons_cumulate = {}
                    for i in range(idx + 1):
                        for cons, cant in st.session_state.tronsoane[i].get('consumatori', {}).items():
                            cons_cumulate[cons] = cons_cumulate.get(cons, 0) + cant
                    
                    total_cons = sum(cons_cumulate.values())
                    st.metric("Total aparate", total_cons)
                
                st.markdown("**Consumatori pe acest tronson:**")
                
                # Grupare consumatori pe categorii
                categorii = {}
                for cons, date in CONSUMATORI_AR.items():
                    cat = date['categorie']
                    if cat not in categorii:
                        categorii[cat] = []
                    categorii[cat].append(cons)
                
                # Afișare consumatori pe categorii
                for categorie, lista_cons in categorii.items():
                    st.caption(f"**{categorie}:**")
                    cols = st.columns(min(4, len(lista_cons)))
                    
                    for i, cons in enumerate(lista_cons):
                        with cols[i % 4]:
                            cant = st.number_input(
                                cons,
                                min_value=0, max_value=20, value=0,
                                key=f"cons_ar_{idx}_{cons}",
                                help=f"Q={CONSUMATORI_AR[cons]['debit']} L/s"
                            )
                            if cant > 0:
                                tronson['consumatori'][cons] = cant
                            elif cons in tronson['consumatori']:
                                del tronson['consumatori'][cons]
                
                # Pierderi locale
                st.markdown("**Elemente locale pe tronson:**")
                
                if tronson['este_ultimul']:
                    st.caption("⚠️ Ultimul etaj - se calculează TOATE pierderile locale")
                    elemente = ["Cot 90°", "Cot 45°", "Robinet cu bilă", "Clapetă de sens", "Filtru"]
                else:
                    st.caption("ℹ️ Etaj intermediar - doar Tee-uri")
                    elemente = ["Teu derivație", "Teu trecere"]
                
                cols_loc = st.columns(len(elemente))
                for i, elem in enumerate(elemente):
                    with cols_loc[i]:
                        cant = st.number_input(
                            f"{elem}",
                            min_value=0, max_value=10, value=0,
                            key=f"loc_ar_{idx}_{elem}",
                            help=f"ξ={COEFICIENTI_PIERDERI_LOCALE.get(elem, 1.0)}"
                        )
                        if cant > 0:
                            tronson['pierderi_locale'][elem] = cant
        
        # Buton calcul
        if st.session_state.tronsoane:
            st.markdown("---")
            
            if st.button("🔬 **CALCULEAZĂ DIMENSIONARE APĂ RECE**", type="primary", use_container_width=True):
                rezultate = []
                pierdere_totala = 0
                
                for idx, tronson in enumerate(st.session_state.tronsoane):
                    # Consumatori cumulați (de la tronsonul curent înapoi)
                    cons_cumulate = {}
                    for i in range(idx + 1):
                        for cons, cant in st.session_state.tronsoane[i].get('consumatori', {}).items():
                            cons_cumulate[cons] = cons_cumulate.get(cons, 0) + cant
                    
                    # Calcul debit
                    debit, suma_unitati = calcul_debit_probabilistic(cons_cumulate, "rece")
                    
                    if debit > 0:
                        # Selectare diametru
                        dn, di, viteza = selectare_diametru(debit/1000, material)
                        
                        # Pierderi distribuite
                        h_dist = pierdere_presiune_distribuita(
                            debit/1000, tronson['lungime'], di,
                            MATERIALE_CONDUCTE[material]['rugozitate_mm']
                        )
                        
                        # Pierderi locale
                        h_loc = 0
                        for elem, cant in tronson.get('pierderi_locale', {}).items():
                            if elem in COEFICIENTI_PIERDERI_LOCALE:
                                h_loc += cant * COEFICIENTI_PIERDERI_LOCALE[elem] * viteza**2 / (2*G)
                        
                        # Pierdere geometrică
                        h_geom = tronson['dif_nivel']
                        
                        # Total tronson
                        h_total = h_dist + h_loc + h_geom
                        pierdere_totala += h_total
                        
                        rezultate.append({
                            "Tronson": f"T{tronson['nr']}",
                            "Poziție": "🏁 ULTIM" if tronson['este_ultimul'] else "→",
                            "Q (L/s)": f"{debit:.3f}",
                            "DN": f"DN{dn}",
                            "D.Spec": get_diametru_specific(material, dn),
                            "Di (mm)": f"{di:.1f}",
                            "v (m/s)": f"{viteza:.2f}",
                            "L (m)": tronson['lungime'],
                            "ΔH.dist": f"{h_dist:.2f}",
                            "ΔH.loc": f"{h_loc:.2f}",
                            "ΔH.geom": f"{h_geom:.2f}",
                            "ΔH.tot": f"{h_total:.2f}"
                        })
                
                # Afișare rezultate
                if rezultate:
                    st.success(f"✅ **Dimensionare completă APĂ RECE**")
                    
                    col_r1, col_r2, col_r3 = st.columns(3)
                    with col_r1:
                        st.metric("Pierdere totală", f"{pierdere_totala:.2f} mCA")
                    with col_r2:
                        st.metric("Presiune necesară", f"{pierdere_totala + 10:.1f} mCA")
                    with col_r3:
                        verificare = "✅ OK" if pierdere_totala + 10 < presiune_disponibila else "❌ Insuficient"
                        st.metric("Verificare", verificare)
                    
                    # Tabel rezultate
                    df = pd.DataFrame(rezultate)
                    st.session_state.rezultate_ar = df
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Grafic
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=[r["Tronson"] for r in rezultate],
                        y=[float(r["ΔH.tot"]) for r in rezultate],
                        name="Pierderi totale",
                        marker_color='#3498db'
                    ))
                    fig.update_layout(
                        title="Distribuția pierderilor APĂ RECE",
                        xaxis_title="Tronson",
                        yaxis_title="Pierdere (mCA)",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    # =============== TAB APĂ CALDĂ ===============
    with tab_ac:
        st.info("♨️ **Dimensionare conductă alimentare cu apă caldă menajeră**")
        st.warning("⚠️ Pentru ACM se exclud automat: WC-uri, pisoare și robineți exteriori")
        
        # Configurare
        with st.expander("⚙️ **Configurare sistem ACM**", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                material_ac = st.selectbox(
                    "Material conductă ACM",
                    ["PPR cu fibră de sticlă", "Cupru", "Oțel zincat"],
                    key="mat_ac"
                )
            
            with col2:
                temperatura_ac = st.number_input(
                    "Temperatură ACM (°C)",
                    min_value=40.0, max_value=70.0, value=55.0,
                    key="temp_ac"
                )
            
            with col3:
                recirculare = st.checkbox(
                    "Sistem cu recirculare",
                    value=False,
                    help="Pentru clădiri mari"
                )
        
        st.markdown("---")
        
        # Preluare date din APĂ RECE
        if st.session_state.tronsoane:
            st.subheader("📏 Tronsoane ACM")
            st.caption("Preluate automat din sistemul de apă rece, fără consumatorii nepotriviți")
            
            # Copiere tronsoane și filtrare consumatori
            tronsoane_ac = []
            for tronson_ar in st.session_state.tronsoane:
                consumatori_ac = {}
                for cons, cant in tronson_ar.get('consumatori', {}).items():
                    if cons in CONSUMATORI_AC:
                        consumatori_ac[cons] = cant
                
                if consumatori_ac:  # Doar dacă are consumatori de ACM
                    tronsoane_ac.append({
                        'nr': tronson_ar['nr'],
                        'consumatori': consumatori_ac,
                        'lungime': tronson_ar['lungime'] * 1.2,  # +20% pentru traseu ACM
                        'dif_nivel': tronson_ar['dif_nivel'],
                        'este_ultimul': tronson_ar['este_ultimul'],
                        'pierderi_locale': tronson_ar.get('pierderi_locale', {})
                    })
            
            # Afișare tronsoane ACM
            for idx, tronson in enumerate(tronsoane_ac):
                with st.expander(f"**Tronson ACM {tronson['nr']}**", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Consumatori ACM:**")
                        for cons, cant in tronson['consumatori'].items():
                            st.write(f"• {cons}: {cant} buc")
                    
                    with col2:
                        st.metric("Lungime", f"{tronson['lungime']:.1f} m")
                        st.metric("Δh", f"{tronson['dif_nivel']:.1f} m")
                        
                        if tronson['este_ultimul']:
                            st.info("🏁 Ultimul etaj")
            
            # Calcul ACM
            if st.button("🔬 **CALCULEAZĂ DIMENSIONARE APĂ CALDĂ**", type="primary", use_container_width=True):
                rezultate_ac = []
                pierdere_totala_ac = 0
                
                for idx, tronson in enumerate(tronsoane_ac):
                    # Consumatori cumulați
                    cons_cumulate = {}
                    for i in range(idx + 1):
                        for cons, cant in tronsoane_ac[i]['consumatori'].items():
                            cons_cumulate[cons] = cons_cumulate.get(cons, 0) + cant
                    
                    # Calcul debit ACM
                    debit, suma_unitati = calcul_debit_probabilistic(cons_cumulate, "calda")
                    
                    if debit > 0:
                        # Selectare diametru
                        dn, di, viteza = selectare_diametru(debit/1000, material_ac, 1.8)  # v_max mai mică pentru ACM
                        
                        # Pierderi cu temperatura ACM
                        h_dist = pierdere_presiune_distribuita(
                            debit/1000, tronson['lungime'], di,
                            MATERIALE_CONDUCTE[material_ac]['rugozitate_mm'],
                            temperatura_ac
                        )
                        
                        # Pierderi locale
                        h_loc = 0
                        for elem, cant in tronson.get('pierderi_locale', {}).items():
                            if elem in COEFICIENTI_PIERDERI_LOCALE:
                                h_loc += cant * COEFICIENTI_PIERDERI_LOCALE[elem] * viteza**2 / (2*G)
                        
                        h_geom = tronson['dif_nivel']
                        h_total = h_dist + h_loc + h_geom
                        pierdere_totala_ac += h_total
                        
                        rezultate_ac.append({
                            "Tronson": f"T{tronson['nr']}",
                            "Q (L/s)": f"{debit:.3f}",
                            "DN": f"DN{dn}",
                            "D.Spec": get_diametru_specific(material_ac, dn),
                            "v (m/s)": f"{viteza:.2f}",
                            "ΔH.tot": f"{h_total:.2f}"
                        })
                
                if rezultate_ac:
                    st.success(f"✅ **Dimensionare completă APĂ CALDĂ**")
                    st.metric("Pierdere totală ACM", f"{pierdere_totala_ac:.2f} mCA")
                    
                    df_ac = pd.DataFrame(rezultate_ac)
                    st.session_state.rezultate_ac = df_ac
                    st.dataframe(df_ac, use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ Definește mai întâi tronsoanele în tab-ul APĂ RECE")
    
    # =============== TAB RAPOARTE ===============
    with tab_rapoarte:
        st.info("📊 **Generator rapoarte tehnice**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📄 Date proiect")
            nume_proiect = st.text_input("Nume proiect", "Instalații sanitare bloc locuințe")
            beneficiar = st.text_input("Beneficiar", "")
            adresa = st.text_input("Adresă obiectiv", "")
        
        with col2:
            st.subheader("📥 Export")
            
            if PDF_AVAILABLE:
                if st.button("📑 **Generează PDF**", type="primary", use_container_width=True):
                    date_proiect = {
                        'nume': nume_proiect,
                        'beneficiar': beneficiar,
                        'adresa': adresa
                    }
                    
                    rezultate_ar = st.session_state.get('rezultate_ar', None)
                    rezultate_ac = st.session_state.get('rezultate_ac', None)
                    
                    if rezultate_ar is not None or rezultate_ac is not None:
                        pdf_buffer = genereaza_pdf(rezultate_ar, rezultate_ac, date_proiect)
                        
                        if pdf_buffer:
                            st.success("✅ PDF generat cu succes!")
                            
                            b64 = base64.b64encode(pdf_buffer.read()).decode()
                            href = f'<a href="data:application/pdf;base64,{b64}" download="memoriu_tehnic_sanitare.pdf">📥 Descarcă PDF</a>'
                            st.markdown(href, unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ Nu există rezultate de exportat. Calculează mai întâi dimensionarea.")
            else:
                st.error("❌ Librăria ReportLab nu este instalată. Rulează: pip install reportlab")
            
            # Export Excel
            if st.button("📊 **Export Excel**", use_container_width=True):
                rezultate_ar = st.session_state.get('rezultate_ar', None)
                rezultate_ac = st.session_state.get('rezultate_ac', None)
                
                if rezultate_ar is not None or rezultate_ac is not None:
                    buffer = BytesIO()
                    
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        if rezultate_ar is not None:
                            rezultate_ar.to_excel(writer, sheet_name='Apă Rece', index=False)
                        if rezultate_ac is not None:
                            rezultate_ac.to_excel(writer, sheet_name='Apă Caldă', index=False)
                    
                    buffer.seek(0)
                    st.download_button(
                        label="📥 Descarcă Excel",
                        data=buffer,
                        file_name="calcul_sanitare.xlsx",
                        mime="application/vnd.ms-excel"
                    )
    
    # =============== TAB DOCUMENTAȚIE ===============
    with tab_doc:
        st.info("📚 **Documentație tehnică**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📖 Normative")
            st.write("""
            **Utilizate în calcul:**
            - I9-2022 - Instalații sanitare
            - SR 1343-1:2006 - Calculul debitelor
            - STAS 1795 - Canalizări interioare
            
            **Metodologie:**
            - Debit probabilistic pentru consum menajer
            - Pierderi distribuite: Colebrook-White
            - Pierderi locale: coeficienți standard
            """)
            
            st.subheader("🔧 Logica de calcul")
            st.write("""
            **Ordine tronsoane:**
            - Se pornește de la consumatorul cel mai îndepărtat
            - Debitele CRESC spre branșament
            - Fiecare tronson cumulează consumatorii anteriori
            
            **Pierderi locale:**
            - Ultimul etaj: toate elementele locale
            - Etaje intermediare: doar Tee-uri
            - Presiunea se calculează pentru cazul cel mai defavorabil
            """)
        
        with col2:
            st.subheader("📊 Valori de referință")
            
            with st.expander("Viteze recomandate"):
                st.write("""
                - Distribuție: 0.5 - 2.0 m/s
                - Coloane: 1.0 - 2.5 m/s  
                - ACM: 0.5 - 1.8 m/s
                - Recirculare: 0.3 - 0.8 m/s
                """)
            
            with st.expander("Presiuni minime"):
                st.write("""
                - Lavoar: 10 mCA
                - Duș: 12 mCA
                - Cadă: 13 mCA
                - WC rezervor: 5 mCA
                - Mașină spălat: 12 mCA
                """)
            
            with st.expander("Diferențe ACM vs AR"):
                st.write("""
                **Consumatori ACM exclud:**
                - WC-uri (toate tipurile)
                - Pisoare
                - Robineți grădină/exterior
                
                **Modificări calcul ACM:**
                - Temperatură mai mare (55-60°C)
                - Viteză max mai mică (1.8 m/s)
                - Lungimi +20% (traseu diferit)
                - Izolație termică obligatorie
                """)

# Footer
def footer():
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px;'>
        <h4 style='color: #1e3d59; margin: 0;'>Calculator Instalații Sanitare</h4>
        <p style='color: #5c7080; margin: 10px 0;'>Conform normativelor românești în vigoare</p>
        <p style='color: #8b9dc3; font-size: 14px; margin: 5px 0;'>
            <strong>Designed by Ing. Luca Obejdeanu</strong>
        </p>
        <p style='color: #8b9dc3; font-size: 12px; margin: 5px 0;'>
            © 2024 | Versiunea 2.0
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    footer()
