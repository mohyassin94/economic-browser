
import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO

# Predefined highlighted names
highlighted_level1 = [
    "التجارة", "المقاولات", "الصناعة والتعدين والتدوير", "الأمن والسلامة",
    "النقل والبريد والتخزين", "المهن الاستشارية",
    "السياحة والمطاعم والفنادق وتنظيم المعارض", "الخدمات الأخرى"
]

highlighted_level2 = [
    "تجارة الملابس والاقمشة والعطور والساعات وأدوات التجميل والنظارات",
    "تجارة الكماليات",
    "تجارة الاثاث المنزلي والمفروشات والستائر والسجاد",
    "تجارة الأواني والأدوات المنزلية",
    "تجارة الأدوات والآلات والاجهزة",
    "تجارة مواد البناء والادوات الكهربائية والصحية",
    "تجارة المواد الكيماوية",
    "مقاولات الانشاءات العامة",
    "مقاولات عامة للمباني (الانشاء، الإصلاح، الهدم، الترميم)",
    "مقاولات فرعية تخصصية (الحفر، الخرسانة الجاهزة، اعمال اللياسة...)",
    "التشغيل والصيانة والنظافة للمنشآت",
    "صُنع المنسوجات", "صُنع الملبوسات", "صُنع المنتجات الجلدية والمنتجات ذات الصلة",
    "صُنع منتجات المعادن المشكّلة ، باستثناء الآلات والمعدات", "صُنع الأثاث",
    "أنشطة الامن والسلامة", "انشطة النقل والتخزين", "انشطة الاستشارات الادارية",
    "أنشطة المعارض والمؤتمرات", "خدمات تنجيد الأثاث", "الخدمات التجارية"
]

highlighted_level3_keywords = [
    "البيع بالجملة", "البيع بالتجزئة", "وكلاء البيع", "تركيب", "صيانة", "أنظمة", "صناعة", "تنظيم", "إصلاح", "تسجيل", "تنجيد"
]

# Connect to DB
conn = sqlite3.connect("industry_activities_v2.db")

st.title("⭐ الأنشطة المحددة والمميزة")

def export_button(dataframe, filename):
    if not dataframe.empty:
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            dataframe.to_excel(writer, index=False)
        st.download_button(
            label="⬇️ تحميل النتائج كـ Excel",
            data=output.getvalue(),
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Load Level 1
level1_df = pd.read_sql_query("SELECT level1_id, name_ar FROM Level1", conn)
level1_df["display"] = level1_df["name_ar"].apply(
    lambda name: f"⭐ {name}" if name in highlighted_level1 else name
)
level1_dict = level1_df.set_index("display")["level1_id"].to_dict()

# Prioritize highlighted Level 1 options
highlighted_l1_df = level1_df[level1_df["name_ar"].isin(highlighted_level1)]
non_highlighted_l1_df = level1_df[~level1_df["name_ar"].isin(highlighted_level1)]
sorted_level1_df = pd.concat([highlighted_l1_df, non_highlighted_l1_df])
level1_dict = sorted_level1_df.set_index("display")["level1_id"].to_dict()

selected_l1 = st.selectbox("📘 اختر قطاعًا رئيسيًا", list(level1_dict.keys()))

level1_id = level1_dict[selected_l1]

# Load Level 2
level2_df = pd.read_sql_query("SELECT level2_id, name_ar FROM Level2 WHERE level1_id = ?", conn, params=[level1_id])
level2_df["display"] = level2_df["name_ar"].apply(
    lambda name: f"⭐ {name}" if name in highlighted_level2 else name
)

highlighted_df = level2_df[level2_df["name_ar"].isin(highlighted_level2)]
non_highlighted_df = level2_df[~level2_df["name_ar"].isin(highlighted_level2)]
sorted_level2_df = pd.concat([highlighted_df, non_highlighted_df])
level2_dict = sorted_level2_df.set_index("display")["level2_id"].to_dict()

selected_l2 = st.selectbox("📗 اختر قطاعًا فرعيًا", list(level2_dict.keys()))
level2_id = level2_dict[selected_l2]

# Load Level 3
level3_df = pd.read_sql_query("SELECT level3_id AS 'رقم النشاط', name_ar AS 'النشاط التفصيلي' FROM Level3 WHERE level2_id = ?", conn, params=[level2_id])

def highlight_level3(row):
    for word in highlighted_level3_keywords:
        if word in row["النشاط التفصيلي"]:
            return f"⭐ {row['النشاط التفصيلي']}"
    return row["النشاط التفصيلي"]

level3_df["النشاط التفصيلي"] = level3_df.apply(highlight_level3, axis=1)


st.subheader("📙 الأنشطة التفصيلية (Level 3)")
search_term = st.text_input("🔍 ابحث داخل الأنشطة التفصيلية", "")
if search_term:
    level3_df = level3_df[level3_df['النشاط التفصيلي'].str.contains(search_term)]


# Reorder Level 3 to put highlighted items first
highlighted_l3 = level3_df[level3_df['النشاط التفصيلي'].str.contains("⭐")]
non_highlighted_l3 = level3_df[~level3_df['النشاط التفصيلي'].str.contains("⭐")]
level3_df = pd.concat([highlighted_l3, non_highlighted_l3])

st.dataframe(level3_df.style.applymap(lambda x: "background-color: #fff5b1" if isinstance(x, str) and x.startswith("⭐") else ""))

export_button(level3_df, f"{selected_l2}_activities.xlsx")
