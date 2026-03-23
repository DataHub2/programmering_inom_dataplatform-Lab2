import streamlit as st

pg = st.navigation([
    st.Page("pages/first_page.py",      title="Översikt",    default=True),
    st.Page("pages/page_voteringar.py", title="Voteringar"),
    st.Page("pages/page_anforanden.py", title="Anföranden"),
])
pg.run()