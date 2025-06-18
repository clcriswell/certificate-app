import streamlit as st

st.set_page_config(page_title="LegAid", page_icon="📜", layout="wide")

# Display logo image (must be a valid path!)
st.image("Assets/MainLogo.png", width=150)

# Now display the HTML-styled title and subtitle
st.markdown(
    """
    <div style='text-align:center; padding:0 0 2rem 0;'>
        <h1 style='margin-bottom:0;'>LegAid</h1>
        <h4 style='margin-top:0; color: gray;'>Tools for Legislative Productivity</h4>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("Select a tool from the sidebar to begin.")

