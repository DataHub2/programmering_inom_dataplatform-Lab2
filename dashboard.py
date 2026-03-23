import streamlit as st

pg = st.navigation([
    st.Page("pages/first_page.py", title="Översikt", default=True),
    #st.Page("pages/first_page.py", title="Översikt")
])
pg.run()

