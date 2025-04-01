"""
Cell population hierarchy database

This module provides the cell hierarchy structure for PBMC samples
based on the flow cytometry standard 25 hierarchy.
"""

import json
import os

# Default cell hierarchy with proportions (% of parent population)
DEFAULT_HIERARCHY = {
    "non-Granulocytes": {
        "proportion": 1.0,
        "parent": None,
        "children": ["T cell", "B cell", "Natural Killer (NK) cells", "Monocytes", "Dendritic Cells"]
    },
    "T cell": {
        "proportion": 0.4467,
        "parent": "non-Granulocytes",
        "children": ["Gamma Delta T cell", "Natural Killer T cell", "CD4 T cell", "CD8 T cell", "CD4/CD8 Double-Negative T cells (DNT)", "CD4/CD8 Double-Positive T cells (DPT)"]
    },
    "Gamma Delta T cell": {
        "proportion": 0.0174,
        "parent": "T cell",
        "children": []
    },
    "Natural Killer T cell": {
        "proportion": 0.0102,
        "parent": "T cell",
        "children": []
    },
    "CD4 T cell": {
        "proportion": 0.3262,
        "parent": "T cell",
        "children": ["Regulatory T cells (Treg)", "nonTreg"]
    },
    "Regulatory T cells (Treg)": {
        "proportion": 0.0227,
        "parent": "CD4 T cell",
        "children": []
    },
    "nonTreg": {
        "proportion": 0.3035,
        "parent": "CD4 T cell",
        "children": ["CD4 Naive", "CD4 Central Memory (TCM)", "CD4 Effector Memory (TEM)", "CD4 CD45RA+ Effector Memory (TEMRA)"]
    },
    "CD4 Naive": {
        "proportion": 0.1716,
        "parent": "nonTreg",
        "children": ["CD4 CD27+CD28+ Naive"]
    },
    "CD4 CD27+CD28+ Naive": {
        "proportion": 0.1712,
        "parent": "CD4 Naive",
        "children": []
    },
    "CD4 Central Memory (TCM)": {
        "proportion": 0.112,
        "parent": "nonTreg",
        "children": ["CD4 CD27+CD28+ TCM"]
    },
    "CD4 CD27+CD28+ TCM": {
        "proportion": 0.104,
        "parent": "CD4 Central Memory (TCM)",
        "children": []
    },
    "CD4 Effector Memory (TEM)": {
        "proportion": 0.0191,
        "parent": "nonTreg",
        "children": ["CD4 Early-like Effector Memory (TELEM)", "CD4 Early Effector Memory (TEEM)", "CD4 Terminal Effector Memory (TTEM)"]
    },
    "CD4 Early-like Effector Memory (TELEM)": {
        "proportion": 0.0062,
        "parent": "CD4 Effector Memory (TEM)",
        "children": []
    },
    "CD4 Early Effector Memory (TEEM)": {
        "proportion": 0.0129,
        "parent": "CD4 Effector Memory (TEM)",
        "children": []
    },
    "CD4 Terminal Effector Memory (TTEM)": {
        "proportion": 0.0122,
        "parent": "CD4 Effector Memory (TEM)",
        "children": []
    },
    "CD4 CD45RA+ Effector Memory (TEMRA)": {
        "proportion": 0.0267,
        "parent": "nonTreg",
        "children": ["CD4 CD27-CD28- TEMRA"]
    },
    "CD4 CD27-CD28- TEMRA": {
        "proportion": 0.0264,
        "parent": "CD4 CD45RA+ Effector Memory (TEMRA)",
        "children": []
    },
    "CD8 T cell": {
        "proportion": 0.0821,
        "parent": "T cell",
        "children": ["CD8 Naive", "CD8 Central Memory (TCM)", "CD8 Effector Memory (TEM)", "CD8 CD45RA+ Effector Memory (TEMRA)"]
    },
    "CD8 Naive": {
        "proportion": 0.0427,
        "parent": "CD8 T cell",
        "children": ["CD8 CD27+CD28+ Naive"]
    },
    "CD8 CD27+CD28+ Naive": {
        "proportion": 0.0423,
        "parent": "CD8 Naive",
        "children": []
    },
    "CD8 Central Memory (TCM)": {
        "proportion": 0.0144,
        "parent": "CD8 T cell",
        "children": ["CD8 CD27+CD28+ TCM"]
    },
    "CD8 CD27+CD28+ TCM": {
        "proportion": 0.0129,
        "parent": "CD8 Central Memory (TCM)",
        "children": []
    },
    "CD8 Effector Memory (TEM)": {
        "proportion": 0.0198,
        "parent": "CD8 T cell",
        "children": ["CD8 Early-like Effector Memory (TELEM)", "CD8 Early Effector Memory (TEEM)", "CD8 Terminal Effector Memory (TTEM)", "CD8 Intermediate Effector Memory (TIEM)"]
    },
    "CD8 Early-like Effector Memory (TELEM)": {
        "proportion": 0.0062,
        "parent": "CD8 Effector Memory (TEM)",
        "children": []
    },
    "CD8 Early Effector Memory (TEEM)": {
        "proportion": 0.0051,
        "parent": "CD8 Effector Memory (TEM)",
        "children": []
    },
    "CD8 Terminal Effector Memory (TTEM)": {
        "proportion": 0.0132,
        "parent": "CD8 Effector Memory (TEM)",
        "children": []
    },
    "CD8 Intermediate Effector Memory (TIEM)": {
        "proportion": 0.0043,
        "parent": "CD8 Effector Memory (TEM)",
        "children": []
    },
    "CD8 CD45RA+ Effector Memory (TEMRA)": {
        "proportion": 0.0052,
        "parent": "CD8 T cell",
        "children": ["CD8 CD27-CD28- TEMRA"]
    },
    "CD8 CD27-CD28- TEMRA": {
        "proportion": 0.0012,
        "parent": "CD8 CD45RA+ Effector Memory (TEMRA)",
        "children": []
    },
    "B cell": {
        "proportion": 0.0893,
        "parent": "non-Granulocytes",
        "children": ["Naive B cell", "Memory B cell", "Marginal Zone-like B cell", "Plasmablast"]
    },
    "Naive B cell": {
        "proportion": 0.0709,
        "parent": "B cell",
        "children": []
    },
    "Memory B cell": {
        "proportion": 0.0083,
        "parent": "B cell",
        "children": []
    },
    "Marginal Zone-like B cell": {
        "proportion": 0.0051,
        "parent": "B cell",
        "children": []
    },
    "Plasmablast": {
        "proportion": 0.0005,
        "parent": "B cell",
        "children": []
    },
    "Natural Killer (NK) cells": {
        "proportion": 0.1267,
        "parent": "non-Granulocytes",
        "children": ["CD16+", "CD16-", "CD56hi"]
    },
    "CD16+": {
        "proportion": 0.035,
        "parent": "Natural Killer (NK) cells",
        "children": []
    },
    "CD16-": {
        "proportion": 0.0845,
        "parent": "Natural Killer (NK) cells",
        "children": []
    },
    "CD56hi": {
        "proportion": 0.0065,
        "parent": "Natural Killer (NK) cells",
        "children": []
    },
    "Monocytes": {
        "proportion": 0.2761,
        "parent": "non-Granulocytes",
        "children": ["Classical (cMono)", "Intermediate (inMono)", "Non-Classical (ncMono)"]
    },
    "Classical (cMono)": {
        "proportion": 0.2726,
        "parent": "Monocytes",
        "children": []
    },
    "Intermediate (inMono)": {
        "proportion": 0.0031,
        "parent": "Monocytes",
        "children": []
    },
    "Non-Classical (ncMono)": {
        "proportion": 0.0004,
        "parent": "Monocytes",
        "children": []
    },
    "Dendritic Cells": {
        "proportion": 0.0271,
        "parent": "non-Granulocytes",
        "children": ["Classical (cDC)", "Plasmacytoid (pDC)", "Transitional (tDC)"]
    },
    "Classical (cDC)": {
        "proportion": 0.022,
        "parent": "Dendritic Cells",
        "children": ["Type 1 (cDC1)", "Type 2 (cDC2)"]
    },
    "Type 1 (cDC1)": {
        "proportion": 0.0006,
        "parent": "Classical (cDC)",
        "children": []
    },
    "Type 2 (cDC2)": {
        "proportion": 0.005,
        "parent": "Classical (cDC)",
        "children": []
    },
    "Plasmacytoid (pDC)": {
        "proportion": 0.0051,
        "parent": "Dendritic Cells",
        "children": []
    },
    "Transitional (tDC)": {
        "proportion": 0.0003,
        "parent": "Dendritic Cells",
        "children": []
    },
    "CD4/CD8 Double-Negative T cells (DNT)": {
        "proportion": 0.0095,
        "parent": "T cell",
        "children": []
    },
    "CD4/CD8 Double-Positive T cells (DPT)": {
        "proportion": 0.0012,
        "parent": "T cell",
        "children": []
    }
}

class CellHierarchyDB:
    """Database class for cell hierarchy and proportions"""
    
    def __init__(self, filepath=None):
        """
        Initialize the cell hierarchy database
        
        Args:
            filepath: Optional path to JSON file with cell hierarchy data
        """
        self.hierarchy = DEFAULT_HIERARCHY
        
        if filepath and os.path.exists(filepath):
            self.load_from_file(filepath)
    
    def load_from_file(self, filepath):
        """Load cell hierarchy from JSON file"""
        try:
            with open(filepath, 'r') as f:
                self.hierarchy = json.load(f)
            print(f"Loaded cell hierarchy from {filepath}")
        except Exception as e:
            print(f"Error loading from {filepath}: {e}")
            print("Using default hierarchy instead")
    
    def save_to_file(self, filepath):
        """Save current hierarchy to JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.hierarchy, f, indent=2)
            print(f"Saved cell hierarchy to {filepath}")
            return True
        except Exception as e:
            print(f"Error saving to {filepath}: {e}")
            return False
    
    def get_hierarchy(self):
        """Return the full cell hierarchy"""
        return self.hierarchy
    
    def get_cell_info(self, cell_type):
        """Get information for a specific cell type"""
        if cell_type in self.hierarchy:
            return self.hierarchy[cell_type]
        return None
    
    def update_proportion(self, cell_type, proportion):
        """Update the proportion for a specific cell type"""
        if cell_type in self.hierarchy:
            self.hierarchy[cell_type]["proportion"] = proportion
            return True
        return False
    
    def get_all_cell_types(self):
        """Return a list of all cell types in the hierarchy"""
        return list(self.hierarchy.keys())
    
    def get_root_node(self):
        """Return the root node of the hierarchy"""
        for cell_type, info in self.hierarchy.items():
            if info["parent"] is None:
                return cell_type
        return None
    
    def get_children(self, cell_type):
        """Get direct children of a cell type"""
        if cell_type in self.hierarchy:
            return self.hierarchy[cell_type]["children"]
        return []
    
    def get_parent(self, cell_type):
        """Get the parent of a cell type"""
        if cell_type in self.hierarchy:
            return self.hierarchy[cell_type]["parent"]
        return None