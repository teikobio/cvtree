"""
Chart visualization components for the cell population calculator
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from config.settings import CHART_HEIGHT, GAUGE_HEIGHT

def create_cv_bar_chart(leaf_df):
    """Create a bar chart of CVs for leaf populations"""
    fig = px.bar(
        leaf_df,
        x="Population",
        y="CV Value",
        color="CV Quality",
        title="Coefficient of Variation by Cell Population (Leaf Nodes Only)",
        labels={"CV Value": "Coefficient of Variation (%)"},
        hover_data=["Cell Count", "% of Parent"]
    )
    
    fig.update_layout(
        xaxis={'categoryorder':'total ascending'},
        height=CHART_HEIGHT
    )
    
    return fig

def create_cell_distribution_treemap(df, input_cells):
    """Create a treemap of the cell distribution"""
    fig = px.treemap(
        df,
        path=['Parent', 'Population'],
        values='Cell Count',
        color='CV Value',
        color_continuous_scale='RdYlGn_r',
        title=f"Cell Distribution for {input_cells/1000:.1f}K Input Cells",
        hover_data=['CV (%)', 'CV Quality']
    )
    
    fig.update_layout(height=CHART_HEIGHT)
    return fig

def create_processing_waterfall_chart(cell_counts_waterfall, processing_steps):
    """Create a bar chart showing cell counts through processing steps"""
    fig = px.bar(
        x=list(cell_counts_waterfall.keys()),
        y=list(cell_counts_waterfall.values()),
        labels={"x": "Processing Step", "y": "Cell Count"},
        title="Cell Counts Through Processing Steps",
        text=[f"{count:,}" for count in cell_counts_waterfall.values()]
    )
    
    # Add step recovery percentages to the hover text
    hover_text = []
    for i, step in enumerate(cell_counts_waterfall.keys()):
        if step == "Pre-Stain":
            hover_text.append(f"{step}<br>Count: {cell_counts_waterfall[step]:,}<br>Starting Point (100%)")
        else:
            prev_step = list(processing_steps.keys())[i-1]
            pct = (cell_counts_waterfall[step] / cell_counts_waterfall[prev_step]) * 100
            hover_text.append(f"{step}<br>Count: {cell_counts_waterfall[step]:,}<br>Recovery: {pct:.1f}% of {prev_step}")
    
    fig.update_traces(
        textposition="outside",
        marker_color="#1f77b4",
        hovertext=hover_text,
        hoverinfo="text"
    )
    
    fig.update_layout(
        height=CHART_HEIGHT,
        yaxis_title="Cell Count",
    )
    
    return fig

def create_retention_gauge(final_retention):
    """Create a gauge chart to visualize final retention percentage"""
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=final_retention,
        title={"text": "Overall Cell Retention"},
        domain={"x": [0, 1], "y": [0, 1]},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "darkblue"},
            "bar": {"color": "royalblue"},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": "gray",
            "steps": [
                {"range": [0, 10], "color": "firebrick"},
                {"range": [10, 25], "color": "darkorange"},
                {"range": [25, 40], "color": "gold"},
                {"range": [40, 100], "color": "forestgreen"}
            ],
        }
    ))
    
    gauge.update_layout(
        height=GAUGE_HEIGHT,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    
    return gauge 