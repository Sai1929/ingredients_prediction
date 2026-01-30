"""
Recipe Ingredient Calculator - Streamlit App
AI-powered ingredient calculator using Google Gemini
"""

import streamlit as st
import google.generativeai as genai
import json
import os

# Page configuration
st.set_page_config(
    page_title="Recipe Ingredient Calculator",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #6b7280;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .ingredient-card {
        background: #f8fafc;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
    .nutrition-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
    }
    .step-number {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 10px;
    }
    .tip-box {
        background: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        border-radius: 0 10px 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Category icons and colors
CATEGORY_CONFIG = {
    "protein": {"icon": "🍖", "color": "#ef4444"},
    "vegetable": {"icon": "🥬", "color": "#22c55e"},
    "spice": {"icon": "🌶️", "color": "#f97316"},
    "dairy": {"icon": "🥛", "color": "#3b82f6"},
    "grain": {"icon": "🌾", "color": "#eab308"},
    "condiment": {"icon": "🧂", "color": "#ec4899"},
    "oil": {"icon": "🫒", "color": "#facc15"},
    "herb": {"icon": "🌿", "color": "#10b981"},
    "other": {"icon": "📦", "color": "#6b7280"},
}

# Popular dishes
POPULAR_DISHES = [
    "Chicken 65", "Biryani", "Butter Chicken", "Pasta Carbonara",
    "Tacos", "Pad Thai", "Sushi Roll", "Caesar Salad"
]

# Dietary options
DIETARY_OPTIONS = [
    "Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free",
    "Nut-Free", "Halal", "Kosher", "Low-Carb"
]


def get_gemini_response(dish_name: str, servings: int, cuisine_type: str = None, dietary_restrictions: list = None):
    """Call Gemini API to get recipe ingredients."""

    api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")

    if not api_key:
        st.error("GEMINI_API_KEY not configured. Please add it to your Streamlit secrets.")
        return None

    genai.configure(api_key=api_key)

    # Build prompt
    extras = ""
    if cuisine_type:
        extras += f" Style:{cuisine_type}."
    if dietary_restrictions:
        extras += f" Diet:{','.join(dietary_restrictions)}."

    prompt = f"""Chef recipe: "{dish_name}" for {servings} servings.{extras}

SCALE: Protein 150g/person, Veg 120g/person, Grain 80g/person. Spices scale 1.5x when doubling. Liquids scale 80%.

UNITS: grams(solids), ml(liquids), tsp(<10g). Include oil,salt,water.

CATEGORIES: protein|vegetable|grain|dairy|spice|oil|condiment|herb|other

Return JSON only:
{{"dish_name":"{dish_name}","servings":{servings},"total_prep_time_minutes":N,"cuisine_type":"X","ingredients":[{{"name":"X","quantity":N,"unit":"X","category":"X","notes":"X"}}],"cooking_instructions":["step1","step2"],"cooking_tips":"tips","nutritional_info":{{"calories_per_serving":N,"protein_grams":N,"carbs_grams":N,"fat_grams":N}},"estimated_cost":"$X"}}

Short clear steps. Pro tips. Valid JSON only."""

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,
                top_p=0.95,
                max_output_tokens=4096,
            )
        )

        # Parse response
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        return json.loads(text)

    except json.JSONDecodeError as e:
        st.error(f"Failed to parse recipe response: {e}")
        return None
    except Exception as e:
        st.error(f"Error calling Gemini API: {e}")
        return None


def display_ingredients(ingredients):
    """Display ingredients in a nice format."""
    cols = st.columns(2)

    for idx, ing in enumerate(ingredients):
        category = ing.get("category", "other").lower()
        config = CATEGORY_CONFIG.get(category, CATEGORY_CONFIG["other"])

        with cols[idx % 2]:
            st.markdown(f"""
            <div class="ingredient-card" style="border-left-color: {config['color']}">
                <span style="font-size: 1.5rem">{config['icon']}</span>
                <strong>{ing['name']}</strong><br>
                <span style="font-size: 1.2rem; color: #667eea; font-weight: bold">
                    {ing['quantity']} {ing['unit']}
                </span>
                <span style="background: {config['color']}20; color: {config['color']};
                       padding: 2px 8px; border-radius: 10px; font-size: 0.8rem; margin-left: 10px">
                    {category}
                </span>
                {f"<br><small style='color: #6b7280'>{ing.get('notes', '')}</small>" if ing.get('notes') else ""}
            </div>
            """, unsafe_allow_html=True)


def display_nutrition(nutrition):
    """Display nutritional information."""
    if not nutrition:
        return

    cols = st.columns(4)

    metrics = [
        ("🔥 Calories", nutrition.get("calories_per_serving", "N/A"), ""),
        ("🥩 Protein", nutrition.get("protein_grams", "N/A"), "g"),
        ("🍞 Carbs", nutrition.get("carbs_grams", "N/A"), "g"),
        ("🥑 Fat", nutrition.get("fat_grams", "N/A"), "g"),
    ]

    for col, (label, value, unit) in zip(cols, metrics):
        with col:
            st.metric(label=label, value=f"{value}{unit}")


def main():
    # Header
    st.markdown('<p class="main-header">🍳 Recipe Ingredient Calculator</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Ingredient Calculator • Powered by Google Gemini</p>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # Cuisine type
        cuisine_type = st.text_input("🌍 Cuisine Type (optional)", placeholder="e.g., Indian, Italian")

        # Dietary restrictions
        st.subheader("🥗 Dietary Restrictions")
        dietary_restrictions = []
        cols = st.columns(2)
        for idx, option in enumerate(DIETARY_OPTIONS):
            with cols[idx % 2]:
                if st.checkbox(option, key=f"diet_{option}"):
                    dietary_restrictions.append(option)

        st.divider()
        st.markdown("**Made with ❤️ for food lovers**")
        st.markdown("Powered by Google Gemini AI")

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        dish_name = st.text_input(
            "🍽️ Enter Dish Name",
            placeholder="e.g., Chicken Biryani, Pasta Carbonara",
            key="dish_input"
        )

    with col2:
        servings = st.number_input(
            "👥 Servings",
            min_value=1,
            max_value=100,
            value=4,
            step=1
        )

    # Popular dishes quick select
    st.markdown("**🔥 Quick Select:**")
    cols = st.columns(8)
    for idx, dish in enumerate(POPULAR_DISHES):
        with cols[idx % 8]:
            if st.button(dish, key=f"popular_{dish}", use_container_width=True):
                st.session_state.dish_input = dish
                st.rerun()

    st.divider()

    # Calculate button
    if st.button("🧮 Calculate Ingredients", type="primary", use_container_width=True):
        if not dish_name:
            st.warning("Please enter a dish name!")
        else:
            with st.spinner(f"🤖 Calculating ingredients for {dish_name}..."):
                result = get_gemini_response(
                    dish_name=dish_name,
                    servings=servings,
                    cuisine_type=cuisine_type if cuisine_type else None,
                    dietary_restrictions=dietary_restrictions if dietary_restrictions else None
                )

                if result:
                    st.session_state.recipe_result = result

    # Display results
    if "recipe_result" in st.session_state and st.session_state.recipe_result:
        result = st.session_state.recipe_result

        st.divider()

        # Recipe header
        st.header(f"📖 {result.get('dish_name', dish_name)}")

        # Badges
        badge_cols = st.columns(4)
        with badge_cols[0]:
            st.info(f"👥 {result.get('servings', servings)} servings")
        with badge_cols[1]:
            st.info(f"⏱️ {result.get('total_prep_time_minutes', 'N/A')} mins")
        with badge_cols[2]:
            st.info(f"🌍 {result.get('cuisine_type', 'Various')}")
        with badge_cols[3]:
            st.info(f"💰 {result.get('estimated_cost', 'N/A')}")

        # Nutritional info
        st.subheader("📊 Nutrition (per serving)")
        display_nutrition(result.get("nutritional_info"))

        st.divider()

        # Ingredients
        st.subheader(f"🛒 Ingredients ({len(result.get('ingredients', []))} items)")
        display_ingredients(result.get("ingredients", []))

        st.divider()

        # Cooking instructions
        if result.get("cooking_instructions"):
            st.subheader("👨‍🍳 Cooking Instructions")
            for idx, step in enumerate(result["cooking_instructions"], 1):
                st.markdown(f"""
                <div style="display: flex; align-items: flex-start; margin: 1rem 0;">
                    <span class="step-number">{idx}</span>
                    <span style="flex: 1">{step}</span>
                </div>
                """, unsafe_allow_html=True)

        # Cooking tips
        if result.get("cooking_tips"):
            st.divider()
            st.subheader("💡 Pro Tips")
            st.markdown(f"""
            <div class="tip-box">
                {result['cooking_tips']}
            </div>
            """, unsafe_allow_html=True)

        # Download button
        st.divider()
        st.download_button(
            label="📥 Download Recipe (JSON)",
            data=json.dumps(result, indent=2),
            file_name=f"{result.get('dish_name', 'recipe').replace(' ', '_').lower()}_recipe.json",
            mime="application/json"
        )


if __name__ == "__main__":
    main()
