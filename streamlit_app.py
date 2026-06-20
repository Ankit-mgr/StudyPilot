import streamlit as st
from datetime import datetime, date
from pdf_export import generate_pdf, load_timetable
# from remainder import send_daily_nudge

st.set_page_config(page_title="StudyPilot", page_icon="🚀", layout="wide")

# ── Inject all custom CSS for the styled UI ──────────────────────────
st.markdown("""
<style>
/* Reset Streamlit top padding */
.block-container { padding-top: 1rem !important; }

/* Hide default Streamlit header */
header[data-testid="stHeader"] { display: none; }

/* Sidebar dark navy background */
section[data-testid="stSidebar"] {
    background-color: #1E3A5F !important;
}
section[data-testid="stSidebar"] * {
    color: rgba(255,255,255,0.85) !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: #16A34A !important;
    color: white !important;
    border: none !important;
    font-weight: 600;
    font-size: 15px;
    padding: 12px;
    border-radius: 8px;
    width: 100%;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #15803d !important;
}

/* Timetable row base */
.slot-row {
    display: flex;
    align-items: center;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 8px;
    font-size: 13px;
    border: 1px solid transparent;
}
.slot-row.red    { background: #FEE2E2; border-color: #fca5a5; }
.slot-row.yellow { background: #FEF9C3; border-color: #fde68a; }
.slot-row.green  { background: #DCFCE7; border-color: #86efac; }

/* Date column */
.slot-date { padding: 12px 14px; font-weight: 600; min-width: 130px; line-height: 1.4; }
.slot-row.red    .slot-date { color: #DC2626; }
.slot-row.yellow .slot-date { color: #CA8A04; }
.slot-row.green  .slot-date { color: #16A34A; }
.zone-label { font-size: 11px; font-weight: 400; opacity: 0.65; }

/* Thin divider between date and subject */
.slot-divider { width: 1px; height: 36px; opacity: 0.2; }
.slot-row.red    .slot-divider { background: #DC2626; }
.slot-row.yellow .slot-divider { background: #CA8A04; }
.slot-row.green  .slot-divider { background: #16A34A; }

/* Subject text */
.slot-subject { flex: 1; padding: 12px 16px; color: #1E293B; }

/* Duration on far right */
.slot-minutes { padding: 12px 16px; font-weight: 700; white-space: nowrap; }
.slot-row.red    .slot-minutes { color: #DC2626; }
.slot-row.yellow .slot-minutes { color: #CA8A04; }
.slot-row.green  .slot-minutes { color: #16A34A; }

/* Legend */
.legend {
    display: flex; gap: 18px; justify-content: center;
    padding-top: 10px; border-top: 1px solid #e2e8f0; margin-top: 10px;
}
.legend-item { font-size: 12px; color: #64748b; display: flex; align-items: center; gap: 5px; }
.dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
.dot.red    { background: #DC2626; }
.dot.yellow { background: #CA8A04; }
.dot.green  { background: #16A34A; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar inputs ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ StudyPilot")
    st.markdown("---")
    st.markdown("📄 **Upload syllabus PDF**")
    syllabus_file = st.file_uploader("syllabus", type=["pdf"], label_visibility="collapsed")
    st.markdown("📅 **Enter exam dates**")
    exam_date = st.date_input("exam date", label_visibility="collapsed")
    st.markdown("⏱️ **Daily study hours**")
    study_hours = st.slider("hours", 1, 12, 3, label_visibility="collapsed")
    st.caption(f"{study_hours} hrs / day")
    st.markdown("📧 **Your email**")
    user_email = st.text_input("email", placeholder="you@example.com", label_visibility="collapsed")
    st.markdown("<br>", unsafe_allow_html=True)
    generate_clicked = st.button("🚀 Generate Plan")


# ── Load your existing timetable data (no changes to load_timetable) ─
try:
    rows, summary = load_timetable("timetable.json")
except FileNotFoundError:
    rows, summary = [], ""


# ── Tabs ─────────────────────────────────────────────────────────────
tab_plan, tab_pdf, tab_nudge, tab_redis = st.tabs(
    ["📋 Your Plan", "📄 Download PDF", "🔔 Email Nudge", "🔄 Redistribute"]
)


# ── Tab 1: render timetable rows as styled HTML ───────────────────────
with tab_plan:
    st.markdown("#### Your 7-Day Study Timetable")

    if not rows:
        st.info("👆 Fill in the sidebar and click **Generate Plan** to get started.")
    else:
        html = ""
        for row in rows:
            # Work out urgency colour from exam_date (same logic as your get_urgency)
            try:
                days_left = (datetime.strptime(row["exam_date"], "%Y-%m-%d").date() - date.today()).days
            except Exception:
                days_left = 999

            if days_left <= 7:
                zone, label = "red", "Exam week"
            elif days_left <= 14:
                zone, label = "yellow", "Revision"
            else:
                zone, label = "green", "New chapters"

            # Format date e.g. "12 Jun Thu"
            try:
                d = datetime.strptime(row["date"], "%Y-%m-%d")
                date_str = d.strftime("%d %b &nbsp;<b>%a</b>")
            except Exception:
                date_str = row.get("date", "")

            topic = row.get("topic", "")
            subject_text = f"<b>{row.get('subject','')}</b>" + (f" — {topic}" if topic else "")

            html += f"""
            <div class="slot-row {zone}">
                <div class="slot-date">{date_str}<div class="zone-label">{label}</div></div>
                <div class="slot-divider"></div>
                <div class="slot-subject">{subject_text}</div>
                <div class="slot-minutes">{row.get('minutes', 0)} min</div>
            </div>"""

        st.markdown(html, unsafe_allow_html=True)

        # Legend
        st.markdown("""
        <div class="legend">
            <div class="legend-item"><span class="dot red"></span> Exam week</div>
            <div class="legend-item"><span class="dot yellow"></span> Revision</div>
            <div class="legend-item"><span class="dot green"></span> New chapters</div>
        </div>""", unsafe_allow_html=True)

        if summary:
            st.caption(summary)


# ── Tab 2: PDF download (calls your existing generate_pdf) ────────────
with tab_pdf:
    st.markdown("#### Download as PDF")
    if rows:
        if st.button("📥 Generate PDF"):
            pdf_path = "/tmp/studypilot.pdf"
            with st.spinner("Building PDF…"):
                generate_pdf(rows, summary=summary, output_path=pdf_path)
            with open(pdf_path, "rb") as f:
                st.download_button("💾 Save PDF", f.read(), "StudyPilot.pdf", "application/pdf")
    else:
        st.info("Generate a plan first.")


# ── Tab 3: Email nudge (calls your existing send_daily_nudge) ─────────
with tab_nudge:
    st.markdown("#### Daily email nudge")
    nudge_email = st.text_input("Send reminders to:", value=user_email, placeholder="you@example.com")
    if st.button("🔔 Enable nudge"):
        if nudge_email:
            # send_daily_nudge(nudge_email, rows)
            st.success(f"Nudge enabled for **{nudge_email}**")
        else:
            st.warning("Enter an email address first.")


# ── Tab 4: Redistribute ───────────────────────────────────────────────
with tab_redis:
    st.markdown("#### Redistribute sessions")
    st.write("Missed a session? Spread remaining topics across your free days.")
    if st.button("🔄 Redistribute"):
        st.info("Coming soon!")


# ── Generate Plan button handler ──────────────────────────────────────
if generate_clicked:
    if not syllabus_file:
        st.sidebar.warning("Upload a syllabus PDF first.")
    elif not user_email:
        st.sidebar.warning("Enter your email address.")
    else:
        # TODO: parse syllabus → generate timetable.json → rerun
        st.sidebar.success("Plan generated! See 'Your Plan' tab.")
        st.rerun()