"""Startup Intelligence Dashboard - Find and Evaluate Startup Ideas.

The app has two primary user flows:
1) "Find My Startup Idea" (idea discovery)
2) "Evaluate My Startup Idea" (idea evaluation)

GENERAL RULES:
- Use structured inputs only (dropdowns, numeric fields)
- All logic must be explainable and deterministic (no black-box LLM output)
- Data source is precomputed aggregated market data from MongoDB
- Results must include reasoning, not just scores
"""

import logging
import pandas as pd
import streamlit as st
from pymongo.collection import Collection
from src.database.connection import get_database
from src.utils.logging import setup_logging

# Configure
setup_logging()
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Startup Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Modern Dark Blue Aesthetic Theme
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Main App Background - Beautiful Dark Blue Gradient */
    .stApp {
        background: linear-gradient(135deg, #0a1628 0%, #1a2332 25%, #0d1b2a 50%, #1b263b 75%, #0d1b2a 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Main content area */
    .main {
        background: transparent;
    }
    
    /* Beautiful gradient text for headers */
    h1, h2, h3 {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 50%, #2563eb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    /* Regular text styling */
    p, label, .stMarkdown {
        color: #e2e8f0 !important;
        font-weight: 400;
    }
    
    /* Premium Button Styling */
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 14px 32px;
        font-weight: 600;
        font-size: 16px;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4);
        transition: all 0.3s ease;
        text-transform: uppercase;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        box-shadow: 0 6px 30px rgba(59, 130, 246, 0.6);
        transform: translateY(-2px);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* Beautiful Glass-morphism Cards */
    .result-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(96, 165, 250, 0.2);
        border-radius: 16px;
        padding: 24px;
        margin: 20px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    /* Premium Score Badges */
    .score-badge {
        display: inline-block;
        font-size: 52px;
        font-weight: 700;
        padding: 24px 48px;
        border-radius: 16px;
        margin: 24px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        letter-spacing: -0.02em;
    }
    
    .score-high {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 50%, #1d4ed8 100%);
        color: white;
        border: 2px solid rgba(96, 165, 250, 0.3);
    }
    
    .score-medium {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
        color: white;
        border: 2px solid rgba(147, 197, 253, 0.3);
    }
    
    .score-low {
        background: linear-gradient(135deg, #475569 0%, #334155 100%);
        color: white;
        border: 2px solid rgba(148, 163, 184, 0.3);
    }
    
    /* Modern Progress Bar */
    .score-bar {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 12px;
        height: 28px;
        margin: 12px 0;
        overflow: hidden;
        border: 1px solid rgba(96, 165, 250, 0.2);
    }
    
    .score-fill {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 50%, #1d4ed8 100%);
        height: 100%;
        border-radius: 12px;
        transition: width 0.5s ease;
        display: flex;
        align-items: center;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
        justify-content: center;
        color: white;
        font-weight: 600;
        padding-left: 12px;
    }
    
    /* Premium Input Fields */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        background: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(96, 165, 250, 0.3) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        padding: 12px 16px !important;
        font-size: 15px !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus {
        border-color: rgba(96, 165, 250, 0.6) !important;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.3) !important;
    }
    
    /* Section Headers with Glow */
    .section-header {
        font-size: 28px;
        font-weight: 700;
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-top: 32px;
        margin-bottom: 20px;
        border-bottom: 2px solid rgba(96, 165, 250, 0.3);
        padding-bottom: 12px;
    }
    
    /* Glass Metric Boxes */
    .metric-box {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(10px);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(96, 165, 250, 0.2);
        margin: 12px 0;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }
    
    .metric-box:hover {
        border-color: rgba(96, 165, 250, 0.4);
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.3);
        transform: translateY(-2px);
    }
    
    .metric-label {
        font-size: 14px;
        color: #94a3b8;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-top: 8px;
    }
    
    /* Metric containers */
    [data-testid="stMetricValue"] {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
    }
    
    /* Beautiful List Items */
    .reason-list {
        list-style-type: none;
        padding-left: 0;
    }
    
    .reason-item {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(10px);
        padding: 16px;
        margin: 10px 0;
        border-radius: 12px;
        border-left: 4px solid #3b82f6;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
        color: #e2e8f0;
    }
    
    .reason-item:hover {
        border-left-color: #60a5fa;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3);
        transform: translateX(4px);
    }
    
    .reason-item::before {
        content: "✓ ";
        color: #60a5fa;
        font-weight: bold;
        margin-right: 10px;
        font-size: 18px;
    }
    
    /* Data Tables */
    .dataframe {
        background: rgba(30, 41, 59, 0.6) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    
    .dataframe th {
        background: rgba(59, 130, 246, 0.2) !important;
        color: #60a5fa !important;
        font-weight: 600 !important;
        padding: 12px !important;
    }
    
    .dataframe td {
        color: #e2e8f0 !important;
        padding: 10px !important;
        border-bottom: 1px solid rgba(96, 165, 250, 0.1) !important;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a1628 0%, #1a2332 100%);
        border-right: 1px solid rgba(96, 165, 250, 0.2);
    }
    
    /* Back button */
    .back-button {
        background: rgba(59, 130, 246, 0.2) !important;
        border: 1px solid rgba(96, 165, 250, 0.3) !important;
    }
    
    /* Section divider */
    hr {
        border: none;
        border-top: 2px solid rgba(96, 165, 250, 0.2);
        margin: 32px 0;
    }
    
    /* Charts and visualizations */
    .js-plotly-plot {
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def load_market_data() -> pd.DataFrame:
    """Load market intelligence data from MongoDB."""
    try:
        db = get_database()
        collection: Collection = db["aggregated_sectors"]
        cursor = collection.find({})
        df = pd.DataFrame(list(cursor))
        if "_id" in df.columns:
            df = df.drop(columns=["_id"])
        return df
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


def calculate_opportunity_score(row: pd.Series) -> float:
    """Calculate 0-10 opportunity score for a sector.
    
    Logic:
    - Lower saturation = better (30% weight)
    - Higher growth = better (30% weight)
    - Lower risk = better (20% weight)
    - Higher activity rate = better (20% weight)
    """
    saturation_score = (1 - row["saturation_score"]) * 3
    growth_score = max(0, min(3, (row["growth_rate"] + 0.1) * 15))
    risk_score = (1 - row["risk_score"]) * 2
    active_ratio = row["active_startups"] / max(row["total_startups"], 1)
    activity_score = active_ratio * 2
    
    total = saturation_score + growth_score + risk_score + activity_score
    return min(10, max(0, total))


def get_score_class(score: float) -> str:
    """Return CSS class based on score."""
    if score >= 7:
        return "score-high"
    elif score >= 4:
        return "score-medium"
    else:
        return "score-low"


def render_score_bar(label: str, score: float, max_score: float = 10):
    """Render a visual progress bar for a score."""
    percentage = (score / max_score) * 100
    st.markdown(f"""
    <div style="margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
            <span style="color: #6C757D; font-weight: 500;">{label}</span>
            <span style="color: #2E5C8A; font-weight: 600;">{score:.1f}/{max_score}</span>
        </div>
        <div class="score-bar">
            <div class="score-fill" style="width: {percentage}%;">
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_landing_page():
    """PAGE 1: Landing / Home."""
    st.title("Startup Intelligence Dashboard")
    st.markdown("### Data-driven insights to launch your next venture")
    st.markdown("Choose your path below to get started")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("### Find a Startup Idea")
        st.markdown("Discover high-potential startup sectors based on your resources and preferences.")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Discover Opportunities", key="find", use_container_width=True, type="primary"):
            st.session_state.page = "find_idea"
            st.rerun()
    
    with col2:
        st.markdown("### Evaluate My Idea")
        st.markdown("Assess your startup concept against market data and get actionable insights.")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Evaluate Idea", key="eval", use_container_width=True, type="primary"):
            st.session_state.page = "evaluate_idea"
            st.rerun()


def show_find_idea_page(df: pd.DataFrame):
    """PAGE 1: Find My Startup Idea.
    
    All filters are OPTIONAL. Returns 3-5 ranked recommendations.
    """
    # Header with back button
    col1, col2 = st.columns([1, 6])
    with col1:
        if st.button("← Back", key="back1"):
            st.session_state.page = "home"
            st.rerun()
    with col2:
        st.title("Find Your Startup Idea")
    
    st.markdown("Select your preferences below. All filters are optional.")
    st.markdown("---")
    
    # Filter Panel
    st.subheader("Your Preferences")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        location = st.selectbox(
            "Preferred Location",
            ["Any"] + df["top_countries"].explode().dropna().unique().tolist()[:10],
            help="Where do you want to operate?"
        )
        
        capital = st.selectbox(
            "Available Capital",
            ["Any", "< $50K", "$50K - $500K", "$500K - $5M", "$5M+"],
            help="How much can you invest?"
        )
    
    with col2:
        time_horizon = st.selectbox(
            "Expected Time to Return",
            ["Any", "Short-term (1-2 years)", "Medium-term (3-5 years)", "Long-term (5+ years)"],
            help="When do you expect returns?"
        )
        
        industry = st.selectbox(
            "Preferred Industry",
            ["Any"] + sorted(df["sector"].unique().tolist()),
            help="Focus on a specific sector?"
        )
    
    with col3:
        risk_appetite = st.selectbox(
            "Risk Appetite",
            ["Any", "Low Risk", "Medium Risk", "High Risk"],
            help="How much risk can you handle?"
        )
    
    # Search button
    st.markdown("<br>", unsafe_allow_html=True)
    search = st.button("Find Opportunities", type="primary", use_container_width=True)
    
    if search:
        st.markdown("---")
        st.subheader("Top Recommendations")
        
        # Filter data based on inputs (soft filtering - score-based)
        filtered_df = df.copy()
        
        # Apply hard filters only for specific industry selection
        if industry != "Any":
            filtered_df = filtered_df[filtered_df["sector"] == industry]
        
        # For other filters, use scoring instead of hard filtering
        # Calculate opportunity scores first
        filtered_df["opportunity_score"] = filtered_df.apply(calculate_opportunity_score, axis=1)
        
        # Adjust scores based on preferences (soft filtering)
        if risk_appetite == "Low Risk":
            filtered_df["opportunity_score"] = filtered_df["opportunity_score"] + (1 - filtered_df["risk_score"]) * 2
        elif risk_appetite == "Medium Risk":
            # Favor medium risk
            filtered_df["opportunity_score"] = filtered_df["opportunity_score"] + \
                (1 - abs(filtered_df["risk_score"] - 0.45)) * 2
        elif risk_appetite == "High Risk":
            filtered_df["opportunity_score"] = filtered_df["opportunity_score"] + filtered_df["risk_score"] * 2
        
        # Adjust for capital preference
        if capital != "Any":
            if "< $50K" in capital:
                # Favor lower funding requirements
                filtered_df["opportunity_score"] = filtered_df["opportunity_score"] + \
                    (1 - (filtered_df["avg_funding_per_startup"] / filtered_df["avg_funding_per_startup"].max())) * 1.5
            elif "$50K - $500K" in capital:
                # Favor mid-range funding
                target = 275000
                filtered_df["opportunity_score"] = filtered_df["opportunity_score"] + \
                    (1 - abs(filtered_df["avg_funding_per_startup"] - target) / target) * 1.5
            elif "$500K - $5M" in capital:
                # Favor higher funding
                filtered_df["opportunity_score"] = filtered_df["opportunity_score"] + \
                    (filtered_df["avg_funding_per_startup"] / filtered_df["avg_funding_per_startup"].max()) * 1.5
        
        # Always show at least 2 best matches (or all if less than 2)
        min_results = min(2, len(filtered_df))
        max_results = min(5, len(filtered_df))
        
        # Get top results
        results = filtered_df.nlargest(max(max_results, min_results), "opportunity_score")
        
        if len(results) == 0:
            st.warning("No data available. Please check your database connection.")
        else:
            # Show info message about showing best matches
            if len(results) >= min_results:
                st.info(f"✨ Showing top {len(results)} opportunities ranked by best fit with your preferences")
            
            for idx, (_, row) in enumerate(results.iterrows(), 1):
                # Card layout
                st.markdown(f"""
                <div class="result-card">
                    <h3 style="margin-top: 0;">#{idx} — {row['sector']}</h3>
                    <div style="color: #2E5C8A; font-size: 24px; font-weight: bold; margin: 10px 0;">
                        Score: {row['opportunity_score']:.1f}/10
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Metrics in columns
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Avg Capital", f"${row['avg_funding_per_startup']/1000:.0f}K")
                col2.metric("Growth Rate", f"{row['growth_rate']*100:.1f}%")
                col3.metric("Risk Level", f"{row['risk_score']*100:.0f}%")
                col4.metric("Market Size", f"{row['total_startups']:,}")
                
                # Explanation bullets
                st.markdown("**Why this is a good opportunity:**")
                
                reasons = []
                if row["saturation_score"] < 0.5:
                    reasons.append(f"Low market saturation ({row['saturation_score']*100:.0f}%) — room for new entrants")
                if row["growth_rate"] > 0.05:
                    reasons.append(f"Growing market with {row['growth_rate']*100:.1f}% year-over-year growth")
                if row["risk_score"] < 0.4:
                    reasons.append(f"Lower risk sector with {row['risk_score']*100:.0f}% failure rate")
                if row["active_startups"] / row["total_startups"] > 0.6:
                    reasons.append(f"High success rate — {row['active_startups']/row['total_startups']*100:.0f}% of startups remain active")
                
                if len(reasons) == 0:
                    reasons.append("Balanced opportunity with moderate characteristics across all metrics")
                
                for reason in reasons:
                    st.markdown(f"- {reason}")
                
                # Additional info
                st.markdown(f"**Top Locations:** {', '.join(row['top_countries'][:3])}")
                
                st.markdown("<br>", unsafe_allow_html=True)


def show_evaluate_idea_page(df: pd.DataFrame):
    """PAGE 2: Evaluate My Startup Idea.
    
    All fields are REQUIRED. Returns detailed score breakdown.
    """
    # Header with back button
    col1, col2 = st.columns([1, 6])
    with col1:
        if st.button("← Back", key="back2"):
            st.session_state.page = "home"
            st.rerun()
    with col2:
        st.title("Evaluate Your Startup Idea")
    
    st.markdown("Enter your startup details to receive a comprehensive evaluation.")
    st.markdown("---")
    
    # Input Panel - ALL REQUIRED
    st.subheader("Your Startup Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        industry = st.selectbox(
            "Industry / Sector *",
            sorted(df["sector"].unique().tolist()),
            help="Required: What industry are you targeting?"
        )
        
        location = st.selectbox(
            "Target Location *",
            df["top_countries"].explode().dropna().unique().tolist()[:10],
            help="Required: Where will you operate?"
        )
        
        capital = st.number_input(
            "Available Capital (USD) *",
            min_value=0,
            value=100000,
            step=10000,
            help="Required: How much can you invest?"
        )
    
    with col2:
        price_tier = st.selectbox(
            "Pricing Tier *",
            ["Budget (<$50)", "Mid-range ($50-$500)", "Premium ($500-$5K)", "Luxury ($5K+)"],
            help="Required: What price point are you targeting?"
        )
        
        time_horizon = st.selectbox(
            "Expected Time Horizon *",
            ["Short-term (1-2 years)", "Medium-term (3-5 years)", "Long-term (5+ years)"],
            help="Required: When do you expect returns?"
        )
    
    st.markdown("<small>* All fields required</small>", unsafe_allow_html=True)
    
    # Evaluate button
    st.markdown("<br>", unsafe_allow_html=True)
    evaluate = st.button("Evaluate Idea", type="primary", use_container_width=True)
    
    if evaluate:
        st.markdown("---")
        
        # Get sector data
        sector_data = df[df["sector"] == industry].iloc[0]
        
        # Calculate subscores (0-10 scale)
        
        # 1. Saturation Score (lower saturation = higher score)
        saturation_subscore = (1 - sector_data["saturation_score"]) * 10
        
        # 2. Growth Score
        growth_subscore = max(0, min(10, (sector_data["growth_rate"] + 0.2) * 25))
        
        # 3. Capital Fit Score
        avg_funding = sector_data["avg_funding_per_startup"]
        if avg_funding == 0 or avg_funding < 1000:
            capital_subscore = 5.0  # Neutral if no data
        elif capital >= avg_funding:
            capital_subscore = 10.0
        elif capital >= avg_funding * 0.5:
            capital_subscore = 7.0
        elif capital >= avg_funding * 0.2:
            capital_subscore = 4.0
        else:
            capital_subscore = 2.0
        
        # 4. Risk Alignment (lower risk = higher score)
        risk_subscore = (1 - sector_data["risk_score"]) * 10
        
        # Overall Score (weighted average)
        overall_score = (
            saturation_subscore * 0.30 +
            growth_subscore * 0.30 +
            capital_subscore * 0.20 +
            risk_subscore * 0.20
        )
        
        # Display Overall Score
        st.markdown(f"""
        <div style="text-align: center;">
            <div class="score-badge {get_score_class(overall_score)}">
                {overall_score:.1f} / 10
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        score_label = "Excellent Opportunity" if overall_score >= 7 else "Good Opportunity" if overall_score >= 5 else "Challenging Opportunity"
        st.markdown(f"<h3 style='text-align: center; color: #2E5C8A;'>{score_label}</h3>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Score Breakdown
        st.subheader("Score Breakdown")
        
        render_score_bar("Market Saturation", saturation_subscore)
        render_score_bar("Growth Potential", growth_subscore)
        render_score_bar("Capital Fit", capital_subscore)
        render_score_bar("Risk Alignment", risk_subscore)
        
        st.markdown("---")
        
        # Explanation
        st.subheader("Analysis & Recommendations")
        
        st.markdown("**Why this score?**")
        
        if overall_score >= 7:
            st.success(f"""
            Your idea aligns well with market conditions in {industry}. 
            The sector shows {sector_data['growth_rate']*100:.1f}% growth with {sector_data['saturation_score']*100:.0f}% market saturation. 
            Based on historical data, this represents a strong opportunity.
            """)
        elif overall_score >= 5:
            st.warning(f"""
            Your idea has potential but faces some challenges in {industry}. 
            Consider the factors below carefully. You may need to adjust your approach or differentiate strongly.
            """)
        else:
            st.error(f"""
            This idea faces significant headwinds in {industry}. 
            Review the breakdown below and consider the alternative suggestions.
            """)
        
        st.markdown("**What factors are affecting your score:**")
        
        factors = []
        
        if saturation_subscore < 5:
            factors.append(f"**High competition:** Market is {sector_data['saturation_score']*100:.0f}% saturated with {sector_data['total_startups']:,} existing startups")
        
        if growth_subscore < 5:
            factors.append(f"**Limited growth:** Sector growing at {sector_data['growth_rate']*100:.1f}% annually, below average")
        
        if capital_subscore < 5:
            factors.append(f"**Capital gap:** Typical startups require ${avg_funding/1000:.0f}K, but you have ${capital/1000:.0f}K available")
        
        if risk_subscore < 5:
            factors.append(f"**Higher risk:** {sector_data['risk_score']*100:.0f}% historical failure rate in this sector")
        
        if len(factors) == 0:
            st.markdown("- All factors are within acceptable ranges")
        else:
            for factor in factors:
                st.markdown(f"- {factor}")
        
        st.markdown("**Concrete suggestions:**")
        
        suggestions = []
        
        if saturation_subscore < 6:
            # Find less saturated alternatives
            less_saturated = df[df["saturation_score"] < sector_data["saturation_score"]].nsmallest(2, "saturation_score")
            if len(less_saturated) > 0:
                alt_sectors = ", ".join(less_saturated["sector"].tolist())
                suggestions.append(f"Consider less saturated sectors: {alt_sectors}")
        
        if capital_subscore < 6 and capital < avg_funding:
            suggestions.append(f"Raise additional capital (target: ${avg_funding/1000:.0f}K) or start with a smaller scope")
        
        if growth_subscore < 6:
            # Find faster growing alternatives
            faster_growth = df[df["growth_rate"] > sector_data["growth_rate"]].nlargest(2, "growth_rate")
            if len(faster_growth) > 0:
                alt_sectors = ", ".join(faster_growth["sector"].tolist())
                suggestions.append(f"Look at faster-growing sectors: {alt_sectors}")
        
        if len(suggestions) == 0:
            suggestions.append("Your current approach is well-positioned. Focus on execution and differentiation.")
        
        for suggestion in suggestions:
            st.markdown(f"- {suggestion}")
        
        # Always show alternatives
        if overall_score < 8:
            st.markdown("---")
            st.subheader("Alternative Sectors to Consider")
            
            alternatives = df[df["sector"] != industry].copy()
            alternatives["score"] = alternatives.apply(calculate_opportunity_score, axis=1)
            top_alternatives = alternatives.nlargest(3, "score")
            
            for _, alt in top_alternatives.iterrows():
                alt_score = calculate_opportunity_score(alt)
                st.markdown(f"""
                <div class="result-card">
                    <strong>{alt['sector']}</strong> (Score: {alt_score:.1f}/10)<br>
                    Growth: {alt['growth_rate']*100:.1f}% | Risk: {alt['risk_score']*100:.0f}% | Saturation: {alt['saturation_score']*100:.0f}%
                </div>
                """, unsafe_allow_html=True)


def main():
    """Main app entry point."""
    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "home"
    
    # Load data
    df = load_market_data()
    
    if df.empty:
        st.error("Unable to load market data. Please ensure MongoDB is running and data pipeline has completed.")
        st.stop()
    
    # Route to pages
    if st.session_state.page == "home":
        show_landing_page()
    elif st.session_state.page == "find_idea":
        show_find_idea_page(df)
    elif st.session_state.page == "evaluate_idea":
        show_evaluate_idea_page(df)


if __name__ == "__main__":
    main()
