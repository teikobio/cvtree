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

def create_processing_waterfall_chart(cell_counts):
    """Create a bar chart showing cell counts through processing steps"""
    steps = list(cell_counts.keys())
    counts = list(cell_counts.values())
    
    # Create color scheme - processing steps in blue, population path in green
    colors = ['#1f77b4' if 'Stain' in step or 'Events' in step or 'Cells' in step 
              else '#2ca02c' for step in steps]
    
    fig = go.Figure()
    
    # Add bars
    fig.add_trace(go.Bar(
        x=steps,
        y=counts,
        marker_color=colors,
        text=[f"{count:,}" for count in counts],
        textposition="outside",
        hovertemplate="%{x}<br>Count: %{y:,}<extra></extra>"
    ))
    
    # Update layout
    fig.update_layout(
        title="Cell Counts Through Processing Steps",
        height=CHART_HEIGHT,
        yaxis_title="Cell Count",
        showlegend=False,
        # Rotate x-axis labels if we have many steps
        xaxis_tickangle=-45 if len(steps) > 6 else 0
    )
    
    # Format y-axis to use comma separator for thousands
    fig.update_layout(yaxis=dict(
        tickformat=",",
    ))
    
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