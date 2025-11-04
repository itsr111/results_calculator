import streamlit as st
import psycopg2
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def get_db_connection():
    """Create database connection"""
    try:
        return psycopg2.connect(os.environ['DATABASE_URL'])
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return None

def save_calculation(notes, coeffs, weighted_avg, matieres):
    """Save calculation to database"""
    try:
        conn = get_db_connection()
        if conn is None:
            return False
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO grade_history 
            (maths, fr, ar, pc, hg, svt, filo, ii, ang, slk, eps, weighted_average,
             maths_coef, fr_coef, ar_coef, pc_coef, hg_coef, svt_coef, filo_coef, ii_coef, ang_coef, slk_coef, eps_coef)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (*notes, weighted_avg, *coeffs))

        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error saving calculation: {str(e)}")
        return False

def get_history():
    """Retrieve calculation history"""
    try:
        conn = get_db_connection()
        if conn is None:
            return []
        cur = conn.cursor()

        cur.execute("""
            SELECT id, calculation_date, maths, fr, ar, pc, hg, svt, filo, ii, ang, slk, eps, weighted_average
            FROM grade_history
            ORDER BY calculation_date DESC
            LIMIT 20
        """)

        results = cur.fetchall()
        cur.close()
        conn.close()

        return results
    except Exception as e:
        st.error(f"Error retrieving history: {str(e)}")
        return []

def calculate_improvement_suggestions(notes, coeffs, matieres, current_avg):
    """Calculate which subject improvement would help most"""
    suggestions = []

    for i, (matiere, note, coef) in enumerate(zip(matieres, notes, coeffs)):
        if note < 20:
            new_notes = notes.copy()
            new_notes[i] = note + 1

            new_total = sum(n * c for n, c in zip(new_notes, coeffs))
            new_avg = new_total / sum(coeffs)

            improvement = new_avg - current_avg
            suggestions.append({
                'matiere': matiere,
                'current_note': note,
                'coefficient': coef,
                'improvement': improvement
            })

    return sorted(suggestions, key=lambda x: x['improvement'], reverse=True)

st.title("🎓 Results Calculator")

tab1, tab2, tab3 = st.tabs(["📝 Calculator", "📊 Charts & History", "⚙️ Settings"])

default_matieres = ["Maths", "FR", "Ar", "PC", "HG", "SVT", "Filo", "II", "Ang", "SLK", "EPS"]
default_coeffs = [9, 4, 2, 7, 2, 3, 2, 2, 2, 1, 2]

if st.session_state.get('reset_coeffs', False):
    for matiere in default_matieres:
        if f"coef_{matiere}" in st.session_state:
            del st.session_state[f"coef_{matiere}"]
    st.session_state['reset_coeffs'] = False

with tab3:
    st.subheader("Customize Coefficients")
    st.write("Adjust the weight of each subject:")

    cols = st.columns(3)
    for i, matiere in enumerate(default_matieres):
        with cols[i % 3]:
            if f"coef_{matiere}" not in st.session_state:
                st.session_state[f"coef_{matiere}"] = default_coeffs[i]

            st.number_input(
                f"{matiere}", 
                min_value=1, 
                max_value=10, 
                value=st.session_state[f"coef_{matiere}"],
                key=f"coef_{matiere}"
            )

    if st.button("🔄 Reset to Default",key="reset_button"):
        st.session_state['reset_coeffs'] = True
        st.rerun()

with tab1:
    st.subheader("Enter Your Grades")

    matieres = default_matieres
    coeffs = [st.session_state.get(f"coef_{matiere}", default_coeffs[i]) for i, matiere in enumerate(default_matieres)]

    notes = []
    cols = st.columns(2)
    for i, matiere in enumerate(matieres):
        with cols[i % 2]:
            note = st.number_input(
                f"xhal jbti f{matiere} (Coef: {coeffs[i]})", 
                min_value=0.0, 
                max_value=20.0, 
                step=0.1,
                value=None,
                key=f"note_{matiere}"
            )
            notes.append(note if note is not None else 0.0)
    if st.button("🧮 Calculer la moyenne", type="primary",key="calc_button" ):
           total = sum(note * coef for note, coef in zip(notes, coeffs))
           No9ta = total / sum(coeffs)

           save_calculation(notes, coeffs,No9ta, matieres)

           st.divider()



           st.session_state["No9ta"] = No9ta

           if No9ta >= 16:
            st.success(f"m9awd , rak jbti {No9ta:.2f}") 
           elif No9ta >= 14:
            st.warning(f"9wdtiha azbe jayb {No9ta:.2f}") 
           elif No9ta < 10:
            st.error("💀💀")
           else:
              st.session_state["show_radio"] = True 
              st.session_state["No9ta"] = No9ta


if st.session_state.get("show_radio", False):
    No9ta = st.session_state["No9ta"]
    st.write("mt2kd baghe t3rf chal jbti gha sir 9tl hssen krk rak mkl5 bzf")
    st.session_state["reponse"] = st.radio("5tar :", ["ah", "la"], index=None, key="reponse_radio")

    if st.session_state["reponse"] == "ah":
            st.error(f"jyb {No9ta:.2f} w baghe t3rfha nkon ana blacek nchn9 kri hssen 😒")
    elif st.session_state["reponse"] == "la":
            st.warning("sf sir twa khdem 3la krk 😒")
            st.divider() 
            st.subheader("💡 Improvement Suggestions") 
            st.write("To improve your average the most, focus on these subjects:")

    suggestions = calculate_improvement_suggestions(notes, coeffs, matieres, No9ta)



    st.divider()
    st.subheader("📥 Export Results")

    export_data = { 'Subject': matieres, 'Grade': notes, 'Coefficient': coeffs, 'Weighted Points': [n * c for n, c in zip(notes, coeffs)] }
    total = sum(note * coef for note, coef in zip(notes, coeffs))
    df_export = pd.DataFrame(export_data)
    df_export.loc[len(df_export)] = ['TOTAL', '', sum(coeffs), total]
    df_export.loc[len(df_export)] = ['AVERAGE', No9ta, '', '']


    csv = df_export.to_csv(index=False)
    st.download_button(
            label="📄 Download as CSV",
            data=csv,
            file_name=f"grades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        ,key="download_button")

    with tab2:
     st.subheader("📊 Grade Distribution")

    history = get_history()

    if len(history) > 0:
        latest = history[0]
        latest_notes = [float(latest[2]), float(latest[3]), float(latest[4]), float(latest[5]), 
                       float(latest[6]), float(latest[7]), float(latest[8]), float(latest[9]), 
                       float(latest[10]), float(latest[11]), float(latest[12])]

        fig = px.bar(
            x=matieres,
            y=latest_notes,
            labels={'x': 'Subject', 'y': 'Grade'},
            title='Your Latest Grades by Subject',
            color=latest_notes,
            color_continuous_scale='RdYlGn'
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        fig2 = go.Figure()
        fig2.add_trace(go.Scatterpolar(
            r=latest_notes,
            theta=matieres,
            fill='toself',
            name='Grades'
        ))
        fig2.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 20])),
            showlegend=False,
            title='Grade Radar Chart'
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No calculations yet. Go to the Calculator tab to add your first grades!")

    st.divider()
    st.subheader("📜 Calculation History")

    if len(history) > 0:
        history_data = []
        for record in history:
            history_data.append({
                'Date': record[1].strftime('%Y-%m-%d %H:%M'),
                'Average': f"{float(record[13]):.2f}",
                'Maths': float(record[2]),
                'FR': float(record[3]),
                'Ar': float(record[4]),
                'PC': float(record[5]),
                'HG': float(record[6]),
                'SVT': float(record[7]),
                'Filo': float(record[8]),
                'II': float(record[9]),
                'Ang': float(record[10]),
                'SLK': float(record[11]),
                'EPS': float(record[12])
            })

        df_history = pd.DataFrame(history_data)
        st.dataframe(df_history, use_container_width=True)

        if len(history) > 1:
            st.subheader("📈 Average Progress Over Time")
            dates = [record[1] for record in history][::-1]
            averages = [float(record[13]) for record in history][::-1]

            fig3 = px.line(
                x=dates,
                y=averages,
                labels={'x': 'Date', 'y': 'Weighted Average'},
                title='Your Average Trend',
                markers=True
            )
            fig3.update_layout(yaxis_range=[0, 20])
            st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No history available yet. Start calculating to build your history!")


