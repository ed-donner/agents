import streamlit as st
from latest_market_research.crew import LatestMarketResearch

st.set_page_config(page_title="Stock Picker", page_icon="📈")

st.title("Stock Picker")

# Input fields
topic = st.text_input("Topic", "Technology")
risk_profile = st.selectbox("Risk Profile", ["Low", "Medium", "High"])
investment_horizon = st.selectbox("Investment Horizon", ["Short", "Medium", "Long"])
region = st.text_input("Region", "Europe")
market_cap_preference = st.selectbox("Market Cap Preference", ["Any", "Large", "Mid", "Small"])
number_of_picks = st.number_input("Number of Picks", min_value=1, max_value=10, value=3, step=1)

# Run button
if st.button("Pick Stocks"):
    input_dict = {
        "topic": topic,
        "risk_profile": risk_profile,
        "investment_horizon": investment_horizon,
        "region": region,
        "market_cap_preference": market_cap_preference,
        "number_of_picks": number_of_picks,
    }

    st.info("Running the Stock Picker...")

    try:
        crew_instance = LatestMarketResearch()
        result = crew_instance.crew().kickoff(inputs=input_dict)
        st.success("Done!")
        st.json(result.raw)
    except Exception as e:
        st.error(f"Error: {e}")
