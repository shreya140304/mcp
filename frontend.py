import streamlit as st
import requests

from new_food_qdrant_system import xyz


st.set_page_config(page_title="Food AI System", layout="wide")
st.title("🍽️ AI Food Recommendation System")

# -------------------------------
# USER INPUT
# -------------------------------
query = st.text_input(
    "What are you craving?",
    placeholder="High protein vegetarian dinner"
)

st.subheader("Optional Nutrition Filters")

col1, col2, col3, col4 = st.columns(4)

with col1:
    protein_min = st.number_input("Min Protein (g)", 0, 100, 0)
with col2:
    carb_min = st.number_input("Min Carbs (g)", 0, 200, 0)
with col3:
    fat_max = st.number_input("Max Fat (g)", 0, 100, 100)
with col4:
    limit = st.slider("Results", 1, 10, 5)

filters = {}
if protein_min > 0:
    filters["protein_g"] = (protein_min, None)
if carb_min > 0:
    filters["carb_g"] = (carb_min, None)
if fat_max < 100:
    filters["fat_g"] = (None, fat_max)

# -------------------------------
# RUN RECOMMENDER
# -------------------------------
if st.button("🔍 Recommend Food"):
    if not query.strip():
        st.warning("Please enter a query")
    else:
        with st.spinner("Searching food database..."):
            result_json = xyz(
                query=query,
                filters=filters if filters else None,
                limit=limit
            )

        st.session_state["food_json"] = result_json
        st.session_state["action"] = None

# -------------------------------
# SHOW RESULTS
# -------------------------------
if "food_json" in st.session_state:
    st.subheader("✅ Recommended Dishes")

    foods = []

    for r in st.session_state["food_json"]["results"]:
        foods.append(r["food_name"])

        with st.expander(r["food_name"]):
            st.write(f"**Score:** {r['score']}")
            st.write("**Ingredients:**", ", ".join(r["ingredients"]))
            st.write("**Nutrition:**")
            st.json(r["nutrition"])

    st.session_state["foods"] = foods

    st.markdown("---")
    st.subheader("Next step")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🍳 Fetch Recipes"):
            st.session_state["action"] = "recipe"

    with col2:
        if st.button("📍 Find Restaurants"):
            st.session_state["action"] = "restaurant"

# -------------------------------
# RECIPE FLOW (FastAPI)
# -------------------------------
if st.session_state.get("action") == "recipe":
    st.subheader("🍳 Recipes")

    for dish in st.session_state["foods"]:
        with st.spinner(f"Fetching recipe for {dish}..."):
            resp = requests.get(
                "http://localhost:8000/dishes/search",
                params={"name": dish}
            )

        if resp.status_code == 200:
            data = resp.json()
            st.markdown(f"### {data['dish_name']}")
            st.write("**Ingredients:**")
            st.write(data["ingredients"])
            st.write("**Recipe:**")
            st.write(data["recipe"])
            st.markdown("---")
        else:
            st.warning(f"Recipe not found for {dish}")

# -------------------------------
# RESTAURANT MATCHING (FastAPI)
# -------------------------------
if st.session_state.get("action") == "restaurant":
    st.subheader("📍 Nearby Restaurants")

    payload = {
        "dishes": st.session_state["foods"],
        "top_k": 10
    }

    with st.spinner("Finding matching restaurants..."):
        resp = requests.post(
            "http://localhost:8000/restaurants/match",
            json=payload
        )

    if resp.status_code != 200:
        st.error("Failed to fetch restaurants")
        st.stop()

    data = resp.json()

    if not data["restaurants"]:
        st.warning("No matching restaurants found")
        st.stop()

    for r in data["restaurants"]:
        st.markdown(f"### 🍽️ {r['name']}")
        st.write(f"📍 Location: {r['location']}")
        st.write("**Popular dishes:**", ", ".join(r["liked_dishes"]))
        st.write(f"**Match score:** {r['score']}")
        st.markdown("---")

