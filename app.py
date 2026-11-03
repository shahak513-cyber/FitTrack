"""FitTrack — נקודת הכניסה של האתר.

מריצים את הקובץ הזה עם Streamlit.
הוא בונה את העיצוב ואת תפריט הניווט, והמסכים עצמם נמצאים ב-fittrack/pages.py.
"""

import html

import streamlit as st

from fittrack.database import get_profile, init_db
from fittrack.pages import page_nutrition, page_profile, page_progress, page_workouts

st.set_page_config(
    page_title="FitTrack",
    page_icon=":material/exercise:",
    layout="wide",
    initial_sidebar_state="expanded",
)

STYLES = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: "Heebo", "Segoe UI", "Arial Hebrew", sans-serif;
    }

    .stApp {
        direction: rtl;
        text-align: right;
        background:
            radial-gradient(circle at 100% 0%, #e6f4ee 0%, #f5f7f6 38%, #eef1ef 100%);
        color: #1b2b26;
    }

    section[data-testid="stSidebar"] {
        background: #132e29;
        border-left: 1px solid #234740;
    }

    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p {
        color: #f3f7f5;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #ffffff;
        font-weight: 800;
        letter-spacing: 0;
    }

    .hero {
        background: #17362f;
        color: #f7fbf9;
        border-radius: 24px;
        padding: 28px 32px 22px;
        margin-bottom: 16px;
        box-shadow: 0 16px 40px rgba(19, 46, 41, 0.12);
    }

    .hero h1 {
        margin: 0 0 6px;
        font-size: 2.1rem;
        font-weight: 800;
        color: #ffffff;
    }

    .hero p {
        margin: 0;
        color: #d5e6e0;
        font-size: 1.05rem;
    }

    .eyebrow {
        margin: 0 0 8px;
        color: #f0b27a;
        font-weight: 700;
        letter-spacing: 0.08em;
    }

    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e1ebe6;
        border-radius: 16px;
        padding: 12px 14px;
        box-shadow: 0 8px 24px rgba(23, 54, 47, 0.04);
    }

    div[data-testid="stForm"],
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.78);
        border-radius: 18px;
    }

    .stButton > button {
        background: #1f6a4a;
        color: #ffffff;
        border: 0;
        border-radius: 12px;
        font-weight: 700;
    }

    .stButton > button:hover {
        background: #18553b;
        color: #ffffff;
    }

    h1, h2, h3, h4 {
        color: #17362f;
        font-weight: 800;
    }

    footer {visibility: hidden;}
</style>
"""

PAGES = {
    "פרופיל": page_profile,
    "תזונה": page_nutrition,
    "אימונים": page_workouts,
    "התקדמות": page_progress,
}


def render_header():
    profile = get_profile()
    if profile:
        title = f"שלום, {html.escape(profile['name'])}"
    else:
        title = "בואו נבנה נקודת התחלה"
    st.markdown(
        f"""
        <div class="hero">
            <p class="eyebrow">FITTRACK</p>
            <h1>{title}</h1>
            <p>יעדים אישיים לכושר ולתזונה, בשפה פשוטה ובלי חשבון בענן.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "FitTrack מיועד למבוגרים בריאים. המספרים, הארוחות ותוכניות האימון "
        "הם הערכות כלליות ללמידה ולמעקב אישי — לא ייעוץ רפואי, תזונתי או אימון אישי."
    )


def main():
    init_db()
    st.markdown(STYLES, unsafe_allow_html=True)

    st.sidebar.markdown("# FitTrack")
    st.sidebar.write("כושר ותזונה, בקצב שלך.")
    page_name = st.sidebar.radio("ניווט", list(PAGES.keys()), label_visibility="collapsed")
    st.sidebar.divider()
    st.sidebar.caption("הנתונים נשמרים בקובץ מקומי על המחשב הזה.")

    render_header()
    PAGES[page_name]()


if __name__ == "__main__":
    main()
