"""
Component for displaying Reverse Analysis settings and calculations in the sidebar.
"""

import streamlit as st
from cell_database import CellHierarchyDB
from config.settings import (
    DEFAULT_POST_STAIN_PCT,
    DEFAULT_EVENTS_ACQUIRED_PCT,
    DEFAULT_VIABLE_CELLS_PCT,
    MIN_STARTING_CELLS,
    DEFAULT_STARTING_CELLS
)

def get_cumulative_proportion(population, db, hierarchy):
    """Calculate the cumulative proportion of a population relative to the root."""
    proportion = 1.0
    current = population
    parent = db.get_parent(current)
    while parent is not None:
        if current in hierarchy:
            if "proportion" in hierarchy[current]:
                 proportion *= hierarchy[current]["proportion"]
            else:
                 st.error(f"Error: Node {current} missing 'proportion' in hierarchy definition.")
                 return 0.0
        else:
            st.error(f"Error: Node {current} not found in hierarchy definition.")
            return 0.0
        current = parent
        parent = db.get_parent(current)
    return proportion


def display_reverse_analysis_sidebar(db: CellHierarchyDB):
    """
    Displays the Target Population (using st.selectbox) and CV settings,
    performs calculations, and returns a dictionary containing calculated values.
    """
    st.sidebar.subheader("Target Population Settings")

    # Get all cell types and sort them for the dropdown
    all_cell_types = sorted(db.get_all_cell_types())

    # Initialize session state for target population if it doesn't exist
    if 'reverse_target_population' not in st.session_state:
        # Default to first leaf node, or first node if no leaves
        leaf_populations = [cell for cell in db.get_hierarchy() if not db.get_children(cell)]
        default_pop = leaf_populations[0] if leaf_populations else (all_cell_types[0] if all_cell_types else None)
        st.session_state.reverse_target_population = default_pop

    # Get the *current* value from session state before rendering the selectbox
    # This avoids potential issues with selectbox returning old value during rerun
    current_selection_in_state = st.session_state.reverse_target_population
    current_selection_index = all_cell_types.index(current_selection_in_state) if current_selection_in_state in all_cell_types else 0

    # Use st.selectbox with all cell types
    new_selection = st.sidebar.selectbox(
        "Target Population",
        options=all_cell_types,
        index=current_selection_index, # Set index based on current session state
        help="Select the population you want to analyze (leaves and intermediate nodes)"
    )

    # Update session state if the selection changed
    if new_selection and new_selection != st.session_state.reverse_target_population:
        st.session_state.reverse_target_population = new_selection
        # Clear the slider value when population changes
        cv_slider_key = f"target_cv_{st.session_state.reverse_target_population}"
        if cv_slider_key in st.session_state:
             del st.session_state[cv_slider_key]
        # Rerun might not be strictly necessary with selectbox, but can ensure consistency
        st.rerun()

    # Use the persisted target population from session state for all subsequent logic
    target_population = st.session_state.reverse_target_population

    # --- Rest of the function remains the same (calculations, results dict) ---
    # Ensure target_population is valid before proceeding
    if not target_population or target_population not in all_cell_types:
         st.error("Invalid target population selected.")
         # Return default results dictionary
         return {
             "target_population": None, "target_cv": 20.0, "population_frequency": 0.0,
             "required_events": 0, "required_input_cells": MIN_STARTING_CELLS,
             "total_efficiency": 0.0, "starting_cells": MIN_STARTING_CELLS
         }

    # Initialize return dictionary
    results = {
        "target_population": target_population,
        "target_cv": 20.0, # Default CV
        "population_frequency": 0.0,
        "required_events": 0,
        "required_input_cells": MIN_STARTING_CELLS,
        "total_efficiency": 0.0,
        "starting_cells": MIN_STARTING_CELLS # Default starting cells
    }

    # --- Calculations Section ---
    hierarchy = db.get_hierarchy()
    cv_slider_key = f"target_cv_{target_population}"
    target_cv = st.sidebar.number_input(
        f"Target CV (%) for {target_population}", # Dynamic label
        min_value=0.1,
        max_value=100.0,
        value=st.session_state.get(cv_slider_key, 20.0), # Default to 20 if key not set
        step=0.1,
        help="Desired coefficient of variation for the target population",
        key=cv_slider_key # Unique key per population
    )
    results["target_cv"] = target_cv

    population_frequency = get_cumulative_proportion(target_population, db, hierarchy)
    results["population_frequency"] = population_frequency

    if population_frequency is None or population_frequency < 0:
         st.error("Could not determine population frequency.")
         return results # Return current results

    # Calculate required events
    required_events = float('inf')
    if population_frequency > 0:
        # Calculate target events needed using Keeney's formula r = (100/CV)²
        target_events_required = int((100/target_cv)**2)
        # Calculate total Leukocyte events needed to achieve the target events
        total_events_needed = int(target_events_required / population_frequency)
        results["target_events_required"] = target_events_required
        results["total_events_needed"] = total_events_needed
    else:
        # Only show error if CV is not already inf (avoids duplicate message)
        if target_cv != float('inf'):
             st.error(f"Cannot calculate required events for {target_population} with zero frequency.")
        results["target_events_required"] = 0
        results["total_events_needed"] = 0

    # Get current processing efficiencies
    post_stain_pct_rev = st.session_state.get("post_stain_pct", DEFAULT_POST_STAIN_PCT)
    events_acquired_pct_rev = st.session_state.get("events_acquired_pct", DEFAULT_EVENTS_ACQUIRED_PCT)
    viable_cells_pct_rev = st.session_state.get("viable_cells_pct", DEFAULT_VIABLE_CELLS_PCT)
    total_efficiency = (post_stain_pct_rev/100) * (events_acquired_pct_rev/100) * (viable_cells_pct_rev/100)
    results["total_efficiency"] = total_efficiency

    # Calculate required input cells based on total events needed
    required_input_cells = float('inf')
    if results["total_events_needed"] > 0 and total_efficiency > 0:
        required_input_cells = int(results["total_events_needed"] / total_efficiency)
        # Display success message here
        st.sidebar.success(f"""
        **Results for {target_population} (Target CV: {target_cv:.1f}%)**
        - Population Frequency: {population_frequency:.4%}
        - {target_population} Events Required (r = (100/CV)²): {results["target_events_required"]:,}
        - Total Leukocyte Events Needed: {results["total_events_needed"]:,}
        - Required Input Cells (Pre-Stain): {required_input_cells:,}
        - Overall Efficiency Used: {total_efficiency:.1%}
        """)
    elif total_efficiency <= 0:
        st.error("Cannot calculate required input cells with zero processing efficiency.")
    else:
         st.error("An error occurred during input cell calculation.")

    # Store final calculated values
    results["required_input_cells"] = required_input_cells if required_input_cells != float('inf') else 0
    results["starting_cells"] = required_input_cells if required_input_cells != float('inf') else MIN_STARTING_CELLS

    return results 