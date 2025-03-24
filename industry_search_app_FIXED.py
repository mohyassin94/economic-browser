
import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO

# Connect to the database
conn = sqlite3.connect("industry_activities_v2.db")

st.title("🛠 تصفح وتصنيف الأنشطة الاقتصادية")

def export_button(dataframe, filename):
    if not dataframe.empty:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            dataframe.to_excel(writer, index=False)
        st.download_button(
            label="⬇️ تحميل النتائج كـ Excel",
            data=output.getvalue(),
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Load all Level 1 options
level1_df = pd.read_sql_query("SELECT level1_id, name_ar FROM Level1", conn)
level1_options = level1_df.set_index('name_ar')['level1_id'].to_dict()
selected_level1_name = st.selectbox("📘 اختر قطاعًا رئيسيًا", list(level1_options.keys()))

if selected_level1_name:
    selected_level1_id = level1_options[selected_level1_name]

    # Load Level 2 under selected Level 1
    level2_df = pd.read_sql_query(
        "SELECT level2_id, name_ar FROM Level2 WHERE level1_id = ?", conn, params=[selected_level1_id]
    )

    if not level2_df.empty:
        level2_options = level2_df.set_index('name_ar')['level2_id'].to_dict()
        selected_level2_name = st.selectbox("📗 اختر قطاعًا فرعيًا", list(level2_options.keys()))

        if selected_level2_name:
            selected_level2_id = level2_options[selected_level2_name]

            # Load Level 3 under selected Level 2
            level3_df = pd.read_sql_query(
                "SELECT level3_id AS 'رقم النشاط', name_ar AS 'النشاط التفصيلي' FROM Level3 WHERE level2_id = ?",
                conn, params=[selected_level2_id]
            )

            st.subheader("📙 الأنشطة التفصيلية (Level 3)")
            st.dataframe(level3_df)
            export_button(level3_df, f"{selected_level2_name}_activities.xlsx")
    else:
        st.warning("⚠️ لا توجد بيانات في المستوى الثاني (Level 2) لهذا القطاع.")
