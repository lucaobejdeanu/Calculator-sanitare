import streamlit as st
import pandas as pd
import numpy as np
import math
from typing import List, Dict, Tuple
import plotly.graph_objects as go

# ======================== CONFIGURARE PAGINĂ ========================
st.set_page_config(
    page_title="Calculator Instalații Sanitare - Tronsoane Progressive",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================== CONSTANTE ========================
G = 9.81

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

# ======================== MATERIALE ========================
MATERIALE_CONDUCTE = {
    "PPR (Polipropilen)": {
        "rugozitate_mm": 0.0015,
        "diametre_mm": {10: 10, 15: 13.2, 20: 16.6, 25: 20.4, 32: 26.2, 40: 32.6, 
                       50: 40.8, 63: 51.4, 75: 61.2, 90: 73.6, 110: 90.0},
        "v_max": 2.0,
    },
    "PEX/Multistrat": {
        "rugozitate_mm": 0.0015,
        "diametre_mm": {16: 12, 20: 16, 25: 20, 32: 26, 40: 32, 50: 40, 63: 50},
        "v_max": 2.0,
    },
    "Cupru": {
        "rugozitate_mm": 0.0015,
        "diametre_mm": {12: 10, 15: 13, 18: 16, 22: 20, 28: 26, 35: 33, 
                       42: 40, 54: 52, 76: 74, 108: 106},
        "v_max": 2.5,
    },
}

# ======================== CONSUMATORI ========================
CONSUMATORI = {
    "WC cu rezervor": {"debit": 0.10, "unitate": 1.0, "presiune_min": 8.0},
    "Lavoar": {"debit": 0.10, "unitate": 1.0, "presiune_min": 10.0},
    "Bideu": {"debit": 0.10, "unitate": 1.0, "presiune_min": 10.0},
    "Duș": {"debit": 0.20, "unitate": 2.0, "presiune_min": 12.0},
    "Cadă < 150L": {"debit": 0.25, "unitate": 3.0, "presiune_min": 13.0},
    "Cadă > 150L": {"debit": 0.33, "unitate": 4.0, "presiune_min": 13.0},
    "Spălător vase": {"debit": 0.20, "unitate": 2.0, "presiune_min": 12.0},
    "MSV": {"debit": 0.20, "unitate": 2.0, "presiune_min": 12.0},
    "MSR": {"debit": 0.20, "unitate": 2.0, "presiune_min": 12.0},
}

# ======================== FUNCȚII CALCUL ========================

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

# ======================== INIȚIALIZARE SESSION STATE ========================
if 'tronsoane_arm' not in st.session_state:
    st.session_state.tronsoane_arm = []

if 'tronsoane_acm' not in st.session_state:
    st.session_state.tronsoane_acm = []

# ======================== MAIN APP ========================
def main():
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 2rem;'>
        <h1>💧 Calculator Instalații Sanitare - Tronsoane Progressive</h1>
        <p>Conform I9-2022 | Designed by Ing. Luca Obejdeanu</p>
    </div>
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
            "🔧 Material conductă",
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
    
    # ======================== TABS ========================
    tab_arm, tab_acm = st.tabs(["💧 Apă Rece Menajeră", "🔥 Apă Caldă Menajeră"])
    
    # ======================== TAB ARM ========================
    with tab_arm:
        st.subheader("💧 Dimensionare Tronsoane ARM")

        # Afișare tronsoane existente în carduri
        if st.session_state.tronsoane_arm:
            st.markdown("### 📋 Tronsoane Definite")

            for idx, tronson in enumerate(st.session_state.tronsoane_arm):
                with st.container():
                    col_info, col_delete = st.columns([5, 1])

                    with col_info:
                        st.markdown(f"""
                        <div style='background-color: #e3f2fd; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #2196f3;'>
                            <h4 style='margin: 0; color: #1976d2;'>🔹 Tronson {tronson['nr']}</h4>
                            <p style='margin: 0.5rem 0;'><strong>Lungime:</strong> {tronson['lungime']} m | <strong>Σ ζ:</strong> {tronson['suma_zeta']:.1f}</p>
                            <p style='margin: 0;'><strong>Obiecte sanitare:</strong> {', '.join([f'{cons} ({cant}×)' for cons, cant in tronson['consumatori'].items()])}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_delete:
                        if st.button("🗑️", key=f"delete_arm_{idx}", help="Șterge tronson"):
                            st.session_state.tronsoane_arm.pop(idx)
                            # Renumerotare tronsoane
                            for i, t in enumerate(st.session_state.tronsoane_arm):
                                t['nr'] = i + 1
                            st.rerun()

            st.markdown("---")

        # Formular nou tronson
        with st.expander("➕ Adaugă Tronson NOU", expanded=len(st.session_state.tronsoane_arm) == 0):
            st.info("ℹ️ **Introduceți doar obiectele sanitare pentru acest tronson specific** (nu toate din sistem)")

            # Nume tronson
            nume_tronson = st.text_input(
                "Nume tronson (opțional)",
                value=f"Tronson {len(st.session_state.tronsoane_arm) + 1}",
                key="arm_new_nume"
            )

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
                    min_value=0.1, max_value=100.0, value=5.0,
                    key="arm_new_lungime"
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
                        "nume": nume_tronson,
                        "consumatori": consumatori_tronson,
                        "lungime": lungime_tronson,
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
                    h_tot = (suma_i_L_cumulata + suma_h_loc_cumulata) / 1000  # în mCA
                    
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
            
            # Buton export Excel
            if st.button("📥 Exportă în Excel ARM"):
                output_path = "/mnt/user-data/outputs/Calcul_ARM_Tronsoane.xlsx"
                df_rezultate.to_excel(output_path, index=False, sheet_name="ARM")
                st.success(f"✅ Tabelul a fost exportat!")
        
        else:
            st.info("ℹ️ Nu există tronsoane definite. Adaugă primul tronson!")
    
    # ======================== TAB ACM ========================
    with tab_acm:
        st.subheader("🔥 Dimensionare Tronsoane ACM")

        # Similar cu ARM dar pentru ACM
        # Consumatori ACM (doar cei care folosesc apă caldă)
        consumatori_acm = {k: v for k, v in CONSUMATORI.items()
                          if k in ["Lavoar", "Bideu", "Duș", "Cadă < 150L", "Cadă > 150L",
                                  "Spălător vase", "MSV", "MSR"]}

        # Afișare tronsoane existente în carduri
        if st.session_state.tronsoane_acm:
            st.markdown("### 📋 Tronsoane Definite ACM")

            for idx, tronson in enumerate(st.session_state.tronsoane_acm):
                with st.container():
                    col_info, col_delete = st.columns([5, 1])

                    with col_info:
                        st.markdown(f"""
                        <div style='background-color: #ffebee; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #f44336;'>
                            <h4 style='margin: 0; color: #c62828;'>🔹 Tronson {tronson['nr']}</h4>
                            <p style='margin: 0.5rem 0;'><strong>Lungime:</strong> {tronson['lungime']} m | <strong>Σ ζ:</strong> {tronson['suma_zeta']:.1f}</p>
                            <p style='margin: 0;'><strong>Obiecte sanitare:</strong> {', '.join([f'{cons} ({cant}×)' for cons, cant in tronson['consumatori'].items()])}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_delete:
                        if st.button("🗑️", key=f"delete_acm_{idx}", help="Șterge tronson"):
                            st.session_state.tronsoane_acm.pop(idx)
                            # Renumerotare tronsoane
                            for i, t in enumerate(st.session_state.tronsoane_acm):
                                t['nr'] = i + 1
                            st.rerun()

            st.markdown("---")

        with st.expander("➕ Adaugă Tronson NOU ACM", expanded=len(st.session_state.tronsoane_acm) == 0):
            st.info("ℹ️ **Introduceți doar obiectele sanitare pentru acest tronson specific** (nu toate din sistem)")

            # Nume tronson
            nume_tronson_acm = st.text_input(
                "Nume tronson (opțional)",
                value=f"Tronson {len(st.session_state.tronsoane_acm) + 1}",
                key="acm_new_nume"
            )

            st.write("**Selectează consumatorii pentru acest tronson:**")

            consumatori_tronson_acm = {}
            cols = st.columns(3)

            for idx, (nume, date) in enumerate(consumatori_acm.items()):
                with cols[idx % 3]:
                    cant = st.number_input(
                        f"{nume} (Vs={date['debit']}, U={date['unitate']})",
                        min_value=0, max_value=50, value=0,
                        key=f"acm_new_{nume}"
                    )
                    if cant > 0:
                        consumatori_tronson_acm[nume] = cant

            col1, col2, col3 = st.columns(3)

            with col1:
                lungime_tronson_acm = st.number_input(
                    "Lungime tronson (m)",
                    min_value=0.1, max_value=100.0, value=5.0,
                    key="acm_new_lungime"
                )

            with col2:
                nr_coturi_acm = st.number_input("Coturi 90° (ζ=1.0)", 0, 20, 2, key="acm_new_cot")
                nr_tee_acm = st.number_input("Tee-uri (ζ=1.8)", 0, 20, 1, key="acm_new_tee")

            with col3:
                nr_robineti_acm = st.number_input("Robinete (ζ=0.5)", 0, 20, 1, key="acm_new_rob")
                nr_clapete_acm = st.number_input("Clapete (ζ=2.5)", 0, 10, 1, key="acm_new_clap")

            suma_zeta_acm = nr_coturi_acm * 1.0 + nr_tee_acm * 1.8 + nr_robineti_acm * 0.5 + nr_clapete_acm * 2.5
            st.info(f"Σ ζ = {suma_zeta_acm:.1f}")

            if st.button("✅ Adaugă Tronson ACM", type="primary"):
                if consumatori_tronson_acm:
                    tronson_acm = {
                        "nr": len(st.session_state.tronsoane_acm) + 1,
                        "nume": nume_tronson_acm,
                        "consumatori": consumatori_tronson_acm,
                        "lungime": lungime_tronson_acm,
                        "suma_zeta": suma_zeta_acm
                    }
                    st.session_state.tronsoane_acm.append(tronson_acm)
                    st.success(f"✅ Tronson {tronson_acm['nr']} ACM adăugat!")
                    st.rerun()
                else:
                    st.warning("⚠️ Selectați cel puțin un consumator!")
        
        # Calcul și afișare similar cu ARM
        if st.session_state.tronsoane_acm:
            st.markdown("---")
            st.subheader("📊 Tronsoane Definite ACM")
            
            rezultate_acm = []
            consumatori_cumulate_acm = {}
            suma_i_L_cumulata_acm = 0
            suma_h_loc_cumulata_acm = 0
            
            for tronson in st.session_state.tronsoane_acm:
                for cons, cant in tronson["consumatori"].items():
                    consumatori_cumulate_acm[cons] = consumatori_cumulate_acm.get(cons, 0) + cant
                
                suma_vs_acm = sum(CONSUMATORI[c]["debit"] * q for c, q in consumatori_cumulate_acm.items())
                suma_E_acm = sum(CONSUMATORI[c]["unitate"] * q for c, q in consumatori_cumulate_acm.items())
                N_acm = sum(consumatori_cumulate_acm.values())
                f_acm = calcul_factor_f(N_acm, destinatie_aleasa)
                
                Vc_acm = calcul_debit_cu_destinatie(suma_vs_acm, suma_E_acm, destinatie_aleasa, "ACM")
                
                info_material = MATERIALE_CONDUCTE[material_ales]
                dim_acm = dimensioneaza_tronson(
                    Vc_acm, tronson["lungime"], material_ales, 
                    60, tronson["suma_zeta"], info_material  # Temp 60°C pentru ACM
                )
                
                if dim_acm:
                    suma_i_L_cumulata_acm += dim_acm["i_L"]
                    suma_h_loc_cumulata_acm += dim_acm["h_loc_mmca"]
                    h_tot_acm = (suma_i_L_cumulata_acm + suma_h_loc_cumulata_acm) / 1000
                    
                    rezultate_acm.append({
                        "Tronson": tronson["nr"],
                        "Consumatori": ", ".join([f"{c}:{q}" for c, q in tronson["consumatori"].items()]),
                        "Utot": suma_E_acm,
                        "N": N_acm,
                        "f": f_acm,
                        "Vs": suma_vs_acm,
                        "Vc": Vc_acm,
                        "DN": dim_acm["dn"],
                        "d_int": dim_acm["d_int_mm"],
                        "v": dim_acm["viteza_ms"],
                        "i": dim_acm["i_specific_pa_m"],
                        "L": tronson["lungime"],
                        "i*L": dim_acm["i_L"],
                        "Σ i*L": suma_i_L_cumulata_acm,
                        "Σ ζ": tronson["suma_zeta"],
                        "h_loc": dim_acm["h_loc_mmca"],
                        "Σ h_loc": suma_h_loc_cumulata_acm,
                        "h_tot": h_tot_acm
                    })
            
            df_rezultate_acm = pd.DataFrame(rezultate_acm)
            
            st.dataframe(
                df_rezultate_acm.style.format({
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
                    "h_tot": "{:.3f}"
                }),
                use_container_width=True,
                height=400
            )
            
            # Metrici finale ACM
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            
            ultima_linie_acm = df_rezultate_acm.iloc[-1]
            
            with col1:
                st.metric("🔴 Debit calcul final ACM", f"{ultima_linie_acm['Vc']:.3f} l/s")
                st.metric("📏 Diametru final", f"DN{ultima_linie_acm['DN']}")
            
            with col2:
                st.metric("💨 Viteză finală", f"{ultima_linie_acm['v']:.2f} m/s")
                st.metric("🔢 Nr. consumatori", f"{int(ultima_linie_acm['N'])}")
            
            with col3:
                st.metric("📐 Σ i*L", f"{ultima_linie_acm['Σ i*L']:.1f} mmCA")
                st.metric("⚙️ Σ h_loc", f"{ultima_linie_acm['Σ h_loc']:.1f} mmCA")
            
            with col4:
                st.metric("📊 h_tot", f"{ultima_linie_acm['h_tot']:.3f} mCA")
                st.metric("🎯 Factor f", f"{ultima_linie_acm['f']:.3f}")
            
            if st.button("📥 Exportă în Excel ACM"):
                output_path = "/mnt/user-data/outputs/Calcul_ACM_Tronsoane.xlsx"
                df_rezultate_acm.to_excel(output_path, index=False, sheet_name="ACM")
                st.success(f"✅ Tabelul a fost exportat!")
        
        else:
            st.info("ℹ️ Nu există tronsoane ACM definite. Adaugă primul tronson!")

if __name__ == "__main__":
    main()
