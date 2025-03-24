
import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO

# Connect to database
conn = sqlite3.connect("industry_activities_v2.db")

# Highlighted categories
highlighted_level1 = [
    "التجارة", "المقاولات", "الصناعة والتعدين والتدوير", "الأمن والسلامة",
    "النقل والبريد والتخزين", "المهن الاستشارية", "السياحة والمطاعم والفنادق وتنظيم المعارض", "الخدمات الأخرى"
]

highlighted_level2 = [  # trimmed list for brevity
    "تجارة الملابس والاقمشة والعطور والساعات وأدوات التجميل والنظارات", "تجارة الكماليات", "مقاولات الانشاءات العامة",
    "صُنع الأثاث", "أنشطة الامن والسلامة", "انشطة النقل والتخزين", "أنشطة المعارض والمؤتمرات"
]

highlighted_level3_keywords = ["البيع", "تركيب", "صيانة", "صناعة", "تنظيم", "إصلاح", "تسجيل", "تنجيد"]

def export_button(df, filename):
    if not df.empty:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        st.download_button("⬇️ تحميل النتائج", data=output.getvalue(), file_name=filename, mime="application/vnd.ms-excel")

st.set_page_config(page_title="دليل الأنشطة - مجموعة المديفر", layout="wide")

tab1, tab2, tab3, tab4 = st.tabs(["📂 التصنيفات", "🏢 شركات المديفر", "🔁 المقارنات", "📌 من النشاط إلى الشركات"])

# ==== TAB 1: CATEGORIES ====
with tab1:
    st.header("📂 تصفح حسب التصنيفات")

    level1_df = pd.read_sql("SELECT level1_id, name_ar FROM Level1", conn)
    level1_df["⭐"] = level1_df["name_ar"].apply(lambda x: "⭐" if x in highlighted_level1 else "")
    level1_df = level1_df.sort_values("⭐", ascending=False)
    selected_l1 = st.selectbox("اختر قطاعًا رئيسيًا", level1_df["name_ar"])
    level1_row = level1_df[level1_df["name_ar"] == selected_l1]
    level1_id = level1_row["level1_id"].values[0] if not level1_row.empty else None

    level2_df = pd.read_sql("SELECT level2_id, name_ar FROM Level2 WHERE level1_id = ?", conn, params=[level1_id])
    level2_df["⭐"] = level2_df["name_ar"].apply(lambda x: "⭐" if x in highlighted_level2 else "")
    level2_df = level2_df.sort_values("⭐", ascending=False)
    selected_l2 = st.selectbox("اختر قطاعًا فرعيًا", level2_df["name_ar"])
    level2_row = level2_df[level2_df["name_ar"] == selected_l2]
    level2_id = level2_row["level2_id"].values[0] if not level2_row.empty else None

    level3_df = pd.read_sql("SELECT level3_id AS 'رمز النشاط', name_ar AS 'النشاط التفصيلي' FROM Level3 WHERE level2_id = ?", conn, params=[level2_id])
    level3_df["⭐"] = level3_df["النشاط التفصيلي"].apply(lambda x: "⭐" if any(word in x for word in highlighted_level3_keywords) else "")
    level3_df = pd.concat([
        level3_df[level3_df["⭐"] == "⭐"],
        level3_df[level3_df["⭐"] != "⭐"]
    ])
    st.dataframe(level3_df.drop(columns=["⭐"]))
    export_button(level3_df, f"{selected_l2}_activities.xlsx")

# ==== TAB 2: COMPANIES ====
with tab2:
    st.header("🏢 شركات مجموعة المديفر")
    company_df = pd.read_csv("company_level3_all_with_flags.csv")

    selected_company = st.selectbox("اختر اسم الشركة", company_df["company"].unique())
    company_activities = company_df[company_df["company"] == selected_company]

    # Join to get Level 2 and Level 1
    l3 = company_activities["رمز النشاط"].astype(str).unique().tolist()
    level3_meta = pd.read_sql("SELECT level3_id, name_ar, level2_id FROM Level3 WHERE level3_id IN ({})".format(",".join(["?"]*len(l3))), conn, params=l3)
    level2_meta = pd.read_sql("SELECT level2_id, name_ar, level1_id FROM Level2", conn)
    level1_meta = pd.read_sql("SELECT level1_id, name_ar FROM Level1", conn)

    
company_activities["رمز النشاط"] = company_activities["رمز النشاط"].astype(str)
level3_meta["level3_id"] = level3_meta["level3_id"].astype(str)
merged = company_activities.merge(level3_meta, left_on="رمز النشاط", right_on="level3_id", how="left")

    merged = merged.merge(level2_meta, on="level2_id", how="left")
    merged = merged.merge(level1_meta, on="level1_id", how="left")
    merged = merged.rename(columns={
        "name_ar_x": "النشاط التفصيلي", "name_ar_y": "القطاع الفرعي", "name_ar": "القطاع الرئيسي"
    })
    st.dataframe(merged[["رمز النشاط", "النشاط التفصيلي", "القطاع الفرعي", "القطاع الرئيسي"]])
    export_button(merged, f"{selected_company}_activities.xlsx")

# ==== TAB 3: SHARED CATEGORIES ====
with tab3:
    st.header("🔁 الأنشطة المشتركة بين الشركات")
    shared_df = company_df[company_df["مشترك بين شركات؟"] == "⭐ مشترك"]
    st.dataframe(shared_df[["رمز النشاط", "اسم النشاط", "company"]])
    export_button(shared_df, "الأنشطة_المشتركة.xlsx")

    st.subheader("🔎 البحث داخل الأنشطة")
    query = st.text_input("اكتب جزء من اسم النشاط أو الرقم")
    if query:
        result = shared_df[
            shared_df["رمز النشاط"].astype(str).str.contains(query) |
            shared_df["اسم النشاط"].str.contains(query, case=False, na=False)
        ]
        st.dataframe(result)

# ==== TAB 4: FROM CATEGORY TO COMPANIES ====
with tab4:
    st.header("📌 معرفة الشركات حسب النشاط")

    all_activities = company_df[["رمز النشاط", "اسم النشاط"]].drop_duplicates().sort_values("اسم النشاط")
    selected_activity = st.selectbox("اختر نشاطًا تفصيليًا", all_activities["اسم النشاط"])
    activity_code = all_activities[all_activities["اسم النشاط"] == selected_activity]["رمز النشاط"].values[0]
    filtered = company_df[company_df["رمز النشاط"] == activity_code]

    st.dataframe(filtered[["company", "رمز النشاط", "اسم النشاط"]])
    export_button(filtered, f"شركات_تمارس_{activity_code}.xlsx")
