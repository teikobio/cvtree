"""
Main Streamlit application for Flow Cytometry Cell Population Calculator

This app allows users to select an input cell count and calculates expected 
cell numbers and CV values for each population in the hierarchy.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

# Add the current directory to the path to import custom modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import custom modules
from cell_database import CellHierarchyDB
from cv_calculator import calculate_cv, categorize_cv, generate_keeney_table

# Initialize the cell database
db = CellHierarchyDB()

def calculate_cell_counts(input_cells, hierarchy=None):
    """
    Calculate cell counts for each population based on input cells and hierarchy
    
    Args:
        input_cells: Number of input cells
        hierarchy: Optional custom hierarchy (uses database if None)
        
    Returns:
        Dictionary with cell counts for each population
    """
    if hierarchy is None:
        hierarchy = db.get_hierarchy()
    
    cell_counts = {}
    
    # First, calculate cell count for the root node (typically Leukocytes)
    root_node = db.get_root_node()
    cell_counts[root_node] = input_cells
    
    # Helper function to recursively calculate cell counts
    def calculate_children(node):
        if node in hierarchy:
            parent_count = cell_counts[node]
            
            for child in hierarchy[node]["children"]:
                # Calculate cell count based on proportion of parent
                child_proportion = hierarchy[child]["proportion"]
                cell_counts[child] = parent_count * child_proportion
                
                # Recursively calculate for this child's children
                calculate_children(child)
    
    # Start calculation from the root
    calculate_children(root_node)
    
    return cell_counts

def main():
    st.set_page_config(
        page_title="Flow Cytometry Cell Population Calculator",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Title and description
    st.title("Flow Cytometry Cell Population Calculator")
    
    with st.expander("About this app", expanded=False):
        st.markdown("""
        This app estimates the number of cells in each population based on the initial input cell count
        and calculates the expected coefficient of variation (CV) using Keeney's formula: r = (100/CV)².
        
        **Key features:**
        - Select input cell count
        - View estimated cell counts for each population in the hierarchy
        - Analyze expected CV for each population
        - Identify populations with potentially unreliable measurements (high CV)
        
        **References:**
        - Keeney et al. formula for CV calculation: r = (100/CV)²
        - Hierarchy based on Peripheral Blood Mononuclear Cell (PBMC) standard
        """)
    
    # Sidebar controls
    with st.sidebar:
        st.header("Input Settings")
        
        # Slider to select input cells starting at 10K with no upper limit
        input_cells = st.number_input(
            "Input Cells:",
            min_value=10000,
            value=500000,
            step=10000,
            format="%d",
            key="input_cell_input"
        )
        
        # Display in K format for readability
        st.write(f"Using {input_cells/1000:.1f}K cells as input")
        
        st.write(f"Selected: {input_cells/1000:.0f}K cells")
        
        # Add Keeney's table reference
        st.subheader("Keeney's Reference Table")
        st.markdown("""
        This table shows the total number of events needed to achieve specific CV percentages
        for populations occurring at different frequencies.
        """)
        
        # Generate and display Keeney's table
        keeney_df = generate_keeney_table(
            desired_cvs=[1, 5, 10, 20],
            frequencies=[0.1, 0.01, 0.001, 0.0001]
        )
        
        # Format the table for display
        keeney_display = keeney_df.copy()
        keeney_display['Fraction'] = keeney_display['Fraction'].apply(lambda x: f"{x:.4f}")
        keeney_display = keeney_display.rename(columns={
            'Fraction': 'Frequency',
            '1:n': 'Ratio',
            'CV 1%': 'For 1% CV',
            'CV 5%': 'For 5% CV',
            'CV 10%': 'For 10% CV',
            'CV 20%': 'For 20% CV'
        })
        
        st.dataframe(keeney_display, use_container_width=True)
    
    # Calculate results
    cell_counts = calculate_cell_counts(input_cells)
    
    # Create dataframe with results
    results = []
    for cell_type, count in cell_counts.items():
        parent = db.get_parent(cell_type)
        parent_count = cell_counts[parent] if parent else None
        
        cv = calculate_cv(count)
        frequency = (count / parent_count if parent_count else 1.0) * 100
        
        results.append({
            "Population": cell_type,
            "Parent": parent if parent else "None",
            "Cell Count": int(count),
            "% of Parent": f"{frequency:.2f}%",
            "CV (%)": f"{cv:.2f}%", 
            "CV Value": cv,  # Raw value for sorting
            "CV Quality": categorize_cv(cv)
        })
    
    df = pd.DataFrame(results)
    
    # Sort by CV value for some displays
    df_sorted = df.sort_values(by="CV Value")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "Table View", 
        "Tree View", 
        "CV Analysis",
        "Cell Distribution"
    ])
    
    with tab1:
        st.subheader("Estimated Cell Counts and CV")
        
        # Filter controls
        col1, col2 = st.columns(2)
        with col1:
            min_cv = st.slider("Min CV (%)", 0.0, 50.0, 0.0)
        with col2:
            max_cv = st.slider("Max CV (%)", 0.0, 50.0, 50.0)
        
        # Apply filters
        filtered_df = df[
            (df["CV Value"] >= min_cv) & 
            (df["CV Value"] <= max_cv)
        ].sort_values(by="CV Value")
        
        # Display columns needed for the table view
        display_df = filtered_df[["Population", "Parent", "Cell Count", "% of Parent", "CV (%)", "CV Quality"]]
        
        st.dataframe(display_df, use_container_width=True)
        
        # Allow downloading as CSV
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name=f"cell_counts_{input_cells/1000:.0f}K.csv",
            mime="text/csv"
        )
    
    with tab2:
        st.subheader("Cell Population Hierarchy")
        
        # Create a tree-like layout
        tree_data = []
        
        def add_to_tree(node, level=0, path=""):
            current_path = f"{path}/{node}" if path else node
            count = int(cell_counts[node])
            cv = calculate_cv(count)
            tree_data.append({
                "Level": level,
                "Path": current_path,
                "Population": node,
                "Cell Count": count,
                "CV (%)": f"{cv:.2f}%",
                "CV Quality": categorize_cv(cv)
            })
            
            for child in db.get_children(node):
                add_to_tree(child, level+1, current_path)
        
        # Start from the root node
        root_node = db.get_root_node()
        add_to_tree(root_node)
        tree_df = pd.DataFrame(tree_data)
        
        # CSS for the tree view
        st.markdown("""
        <style>
        .tree-node {
            margin-bottom: 3px;
            font-family: monospace;
        }
        .tree-node-content {
            display: inline-block;
        }
        .node-name {
            font-weight: bold;
        }
        .excellent-cv { color: green; }
        .good-cv { color: lightgreen; }
        .fair-cv { color: orange; }
        .poor-cv { color: red; }
        .very-poor-cv { color: darkred; }
        </style>
        """, unsafe_allow_html=True)
        
        # Build and display tree with better visualization
        last_level = -1
        indent_guides = []
        
        for i, row in tree_df.iterrows():
            level = row["Level"]
            is_last_in_level = i == len(tree_df) - 1 or tree_df.iloc[i + 1]["Level"] <= level
            
            # Adjust indent guides
            if level > last_level:
                # We're going deeper
                indent_guides.extend([True] * (level - last_level))
            elif level < last_level:
                # We're going back up
                indent_guides = indent_guides[:level]
            
            if is_last_in_level and level > 0:
                indent_guides[level - 1] = False
            
            # Create the tree branch
            branch = ""
            for j in range(level):
                if j == level - 1:
                    branch += "└─── " if is_last_in_level else "├─── "
                else:
                    branch += "│    " if indent_guides[j] else "     "
            
            # Color code based on CV quality
            cv_quality = row["CV Quality"]
            if "Excellent" in cv_quality:
                quality_class = "excellent-cv"
            elif "Good" in cv_quality:
                quality_class = "good-cv"
            elif "Fair" in cv_quality:
                quality_class = "fair-cv"
            elif "Poor" in cv_quality:
                quality_class = "poor-cv"
            else:
                quality_class = "very-poor-cv"
                
            # Create the node text with proper highlighting
            node_text = f"""
            <div class="tree-node">
                <span class="tree-branch">{branch}</span>
                <span class="tree-node-content">
                    <span class="node-name">{row['Population']}</span>: {row['Cell Count']} cells 
                    (CV: {row['CV (%)']}, <span class="{quality_class}">{row['CV Quality']}</span>)
                </span>
            </div>
            """
            
            st.markdown(node_text, unsafe_allow_html=True)
            
            last_level = level
    
    with tab3:
        st.subheader("CV Analysis")
        
        # Filter for leaf nodes (populations with no children)
        leaf_nodes = [cell for cell in db.get_hierarchy() if not db.get_children(cell)]
        leaf_df = df[df["Population"].isin(leaf_nodes)].sort_values(by="CV Value")
        
        # Create a bar chart of CVs for leaf populations
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
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Show table of populations with poor CV
        st.subheader("Populations with Higher CV (>10%)")
        high_cv_df = df[df["CV Value"] > 10].sort_values(by="CV Value", ascending=False)
        
        if not high_cv_df.empty:
            st.dataframe(high_cv_df[["Population", "Cell Count", "% of Parent", "CV (%)", "CV Quality"]])
            
            st.info("""
            💡 **Tip:** Populations with high CV values may have unreliable measurements. 
            Consider increasing the total input cells or pooling samples if precise measurements 
            of these populations are important.
            """)
        else:
            st.success("No populations with CV >10% found with current input cells")
    
    with tab4:
        st.subheader("Cell Distribution")
        
        # Create a treemap of the cell distribution
        fig = px.treemap(
            df,
            path=['Parent', 'Population'],
            values='Cell Count',
            color='CV Value',
            color_continuous_scale='RdYlGn_r',
            title=f"Cell Distribution for {selected_option} Input Cells",
            hover_data=['CV (%)', 'CV Quality']
        )
        
        fig.update_layout(height=700)
        st.plotly_chart(fig, use_container_width=True)
        
        # Also add a sunburst chart as an alternative visualization
        fig2 = px.sunburst(
            df,
            path=['Parent', 'Population'],
            values='Cell Count',
            color='CV Value',
            color_continuous_scale='RdYlGn_r',
            title=f"Sunburst Chart of Cell Distribution",
            hover_data=['CV (%)', 'CV Quality']
        )
        
        fig2.update_layout(height=700)
        st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    main()