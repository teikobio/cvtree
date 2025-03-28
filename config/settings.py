"""
Configuration settings for the Flow Cytometry Cell Population Calculator
"""

# Default processing efficiency values
DEFAULT_POST_STAIN_PCT = 35
DEFAULT_EVENTS_ACQUIRED_PCT = 95
DEFAULT_VIABLE_CELLS_PCT = 80

# Processing steps configuration
PROCESSING_STEPS = {
    "Pre-Stain": {
        "percent_of_previous": 1.0,
        "description": "Isolated PBMCs"
    },
    "Post-Stain": {
        "percent_of_previous": DEFAULT_POST_STAIN_PCT/100,
        "description": "After staining, antibody binding, and permeabilization"
    },
    "Events Acquired": {
        "percent_of_previous": DEFAULT_EVENTS_ACQUIRED_PCT/100,
        "description": "Cells successfully measured by the flow cytometer"
    },
    "Single, Viable Cells": {
        "percent_of_previous": DEFAULT_VIABLE_CELLS_PCT/100,
        "description": "Final cells after excluding doublets and dead cells"
    }
}

# CV quality categories and colors
CV_QUALITY_COLORS = {
    "Excellent (≤1%)": "#00FF00",  # Green
    "Good (1-5%)": "#90EE90",       # Light green
    "Fair (5-10%)": "#FFA500",      # Orange
    "Poor (10-20%)": "#FF4500",     # Red-Orange
    "Very Poor (>20%)": "#FF0000"   # Red
}

# Keeney table settings
DEFAULT_DESIRED_CVS = [1, 5, 10, 20]
DEFAULT_FREQUENCIES = [0.1, 0.01, 0.001, 0.0001]

# Visualization settings
TREE_VIEW_HEIGHT = 800
CHART_HEIGHT = 600
GAUGE_HEIGHT = 300

# Default starting cells
DEFAULT_STARTING_CELLS = 2500000  # 2.5M cells/ml
MIN_STARTING_CELLS = 1000000      # 1M cells/ml
STEP_STARTING_CELLS = 100000      # 100K cells/ml 