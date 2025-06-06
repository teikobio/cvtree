"""
Tree visualization components for the cell hierarchy
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import igraph as ig
from config.settings import CV_QUALITY_COLORS, TREE_VIEW_HEIGHT
from cv_calculator import calculate_cv, categorize_cv

def create_interactive_tree(cell_counts, db):
    """Create an interactive tree visualization using Plotly"""
    # Build nodes and edges list for tree layout
    root_node = db.get_root_node()
    node_to_index = {root_node: 0}  # Map node names to indices
    current_index = 1
    nodes = []
    edges = []
    
    # First pass to collect nodes and create index mapping
    for cell_type, count in cell_counts.items():
        if cell_type not in node_to_index:
            node_to_index[cell_type] = current_index
            current_index += 1
        nodes.append(cell_type)
        
        parent = db.get_parent(cell_type)
        if parent:
            edges.append((node_to_index[parent], node_to_index[cell_type]))
    
    # Create igraph Graph
    G = ig.Graph(directed=True)
    G.add_vertices(len(nodes))
    G.add_edges(edges)
    
    # Get tree layout with basic tree layout
    layout = G.layout("tree", mode="out")
    
    # Get coordinates from layout and scale them
    coords = layout.coords
    scaled_coords = [[x*3, y] for x, y in coords]  # Triple the horizontal spacing
    
    # Convert scaled coordinates to position dict
    position = {k: scaled_coords[k] for k in range(len(nodes))}
    
    # Calculate Y range for inversion
    Y = [scaled_coords[k][1] for k in range(len(nodes))]
    M = max(Y) if Y else 0
    
    # Prepare node positions
    Xn = [position[k][0] for k in range(len(nodes))]
    Yn = [2*M-position[k][1] for k in range(len(nodes))]
    
    # Prepare edge positions
    Xe = []
    Ye = []
    for edge in edges:
        Xe += [position[edge[0]][0], position[edge[1]][0], None]
        Ye += [2*M-position[edge[0]][1], 2*M-position[edge[1]][1], None]
    
    # Create figure
    fig = go.Figure()
    
    # Add edges
    fig.add_trace(go.Scatter(
        x=Xe,
        y=Ye,
        mode='lines',
        line=dict(color='#888', width=1),
        hoverinfo='none'
    ))
    
    # Prepare node data
    node_colors = []
    node_sizes = []
    node_texts = []
    hover_texts = []
    text_positions = []
    
    for i, node in enumerate(nodes):
        count = cell_counts[node]
        cv = calculate_cv(count)
        cv_quality = categorize_cv(cv)
        
        # Format cell count
        if count >= 1e6:
            count_str = f"{count/1e6:.1f}M"
        else:
            count_str = f"{count/1e3:.1f}K"
        
        # Add percentage if not root
        parent = db.get_parent(node)
        if parent:
            parent_count = cell_counts[parent]
            percentage = (count / parent_count) * 100
            count_str += f" ({percentage:.1f}%)"
        
        node_colors.append(CV_QUALITY_COLORS[cv_quality])
        size = np.clip(np.log10(count) * 10, 20, 50)
        node_sizes.append(size)
        node_texts.append(node)
        hover_texts.append(f"{node}<br>{count_str}<br>CV: {cv:.1f}%")
        
        # Alternate text positions for better spacing
        siblings = [n for n in nodes if db.get_parent(n) == parent]
        if len(siblings) > 1:
            idx = siblings.index(node)
            if idx % 2 == 0:
                text_positions.append("bottom right")
            else:
                text_positions.append("bottom left")
        else:
            text_positions.append("bottom center")
    
    # Add nodes with adjusted text positioning
    fig.add_trace(go.Scatter(
        x=Xn,
        y=Yn,
        mode='markers+text',
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(color='white', width=2)
        ),
        text=node_texts,
        textposition=text_positions,
        hovertext=hover_texts,
        hoverinfo='text'
    ))
    
    # Update layout
    fig.update_layout(
        title="Cell Population Hierarchy Tree",
        showlegend=False,
        hovermode='closest',
        dragmode='pan',
        margin=dict(b=20, l=5, r=5, t=40),
        height=TREE_VIEW_HEIGHT,
        plot_bgcolor='white',
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            scaleanchor="y",
            scaleratio=1,
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
        ),
        font=dict(
            color='black'  # Set text color to black for better visibility
        )
    )
    
    # Update node text color
    fig.update_traces(
        textfont=dict(color='black'),  # Set node label color to black
        selector=dict(type='scatter')
    )
    
    return fig

def create_text_tree(cell_counts, db):
    """Create a text-based tree visualization with collapsible nodes"""
    tree_lines = []
    
    def build_text_tree(node, level=0, is_last=False, prefix=""):
        indent = ""
        if level > 0:
            indent = prefix + ("└── " if is_last else "├── ")
        
        # Get cell count and CV
        count = cell_counts[node]
        cv = calculate_cv(count)
        cv_quality = categorize_cv(cv)
        
        # Format cell count
        if count >= 1e6:
            count_str = f"{count/1e6:.1f}M"
        else:
            count_str = f"{count/1e3:.1f}K"
        
        # Add percentage if not root
        parent = db.get_parent(node)
        if parent:
            parent_count = cell_counts[parent]
            percentage = (count / parent_count) * 100
            percentage_str = f" ({percentage:.1f}%)"
        else:
            percentage_str = ""
        
        # Create colored circle for CV quality
        color = CV_QUALITY_COLORS[cv_quality]
        circle = f'<span style="color:{color}">●</span>'
        
        # Get children
        children = db.get_children(node)
        
        # Create unique ID for this node
        node_id = f"node_{node.replace(' ', '_')}"
        children_id = f"children_{node.replace(' ', '_')}"
        
        # Add expand/collapse button if node has children
        if children:
            button = f'<span class="tree-button" data-node="{node_id}" data-children="{children_id}">-</span>'
        else:
            button = '<span class="tree-spacer">  </span>'
            
        line = f'<div class="tree-line">{indent}{button} {node}: {count_str}{percentage_str} - CV: {cv:.2f}% {circle}</div>'
        
        # Create container for this node and its children
        if children:
            tree_lines.append(f'<div id="{node_id}">')
            tree_lines.append(line)
            tree_lines.append(f'<div id="{children_id}" class="tree-children">')
            
            new_prefix = prefix
            if level > 0:
                new_prefix = prefix + ("    " if is_last else "│   ")
            
            for i, child in enumerate(children):
                is_last_child = (i == len(children) - 1)
                build_text_tree(child, level + 1, is_last_child, new_prefix)
            
            tree_lines.append('</div>')  # Close children container
            tree_lines.append('</div>')  # Close node container
        else:
            tree_lines.append(f'<div id="{node_id}">{line}</div>')
    
    # Start building the tree
    build_text_tree(db.get_root_node())
    
    # Create HTML container with styles and JavaScript
    html = """
    <style>
    .tree-container {
        max-height: 800px;
        overflow-y: auto;
        font-family: monospace;
        white-space: nowrap;
        padding: 10px;
        background-color: #f5f5f5;
        border-radius: 5px;
    }
    .tree-button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
        margin-right: 5px;
        cursor: pointer;
        user-select: none;
        color: #666;
        background: none;
        border: 1px solid #ccc;
        border-radius: 3px;
        font-family: monospace;
        font-size: 14px;
        padding: 0;
        line-height: 1;
    }
    .tree-button:hover {
        color: #000;
        background-color: #e0e0e0;
        border-color: #999;
    }
    .tree-spacer {
        display: inline-block;
        width: 20px;
        margin-right: 5px;
    }
    .tree-children {
        display: block;
    }
    .tree-line {
        padding: 2px 0;
    }
    </style>
    """
    
    # Add tree lines
    html += "<div class='tree-container' id='tree-root'>"
    for line in tree_lines:
        html += line
    html += "</div>"
    
    # Add JavaScript at the end
    html += """
    <script>
    // Wait for the DOM to be fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        // Add click handlers to all tree buttons
        document.querySelectorAll('.tree-button').forEach(function(button) {
            button.addEventListener('click', function(e) {
                const nodeId = this.getAttribute('data-node');
                const childrenId = this.getAttribute('data-children');
                const childrenDiv = document.getElementById(childrenId);
                
                if (childrenDiv.style.display === 'none') {
                    childrenDiv.style.display = 'block';
                    this.textContent = '-';
                } else {
                    childrenDiv.style.display = 'none';
                    this.textContent = '+';
                }
            });
        });
    });
    </script>
    """
    
    # Use st.components.v1.html to properly render the interactive HTML
    st.components.v1.html(html, height=800, scrolling=True)
    
    return None

def display_cv_legend():
    """Display the CV quality legend"""
    st.subheader("CV Quality Legend")
    legend_cols = st.columns(len(CV_QUALITY_COLORS))
    for col, (quality, color) in zip(legend_cols, CV_QUALITY_COLORS.items()):
        col.markdown(f"""
        <div style="
            width: 20px;
            height: 20px;
            background-color: {color};
            display: inline-block;
            margin-right: 5px;
        "></div> {quality}
        """, unsafe_allow_html=True) 