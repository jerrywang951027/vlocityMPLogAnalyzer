"""
Chart Generator Module
Creates visualizations for performance log analysis
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
import seaborn as sns
from typing import List, Optional
import numpy as np


class ChartGenerator:
    """Generates charts for performance analysis"""
    
    def __init__(self, df: pd.DataFrame, parser):
        """
        Initialize chart generator
        
        Args:
            df: DataFrame with method call data
            parser: LogParser instance with method call tree
        """
        self.df = df
        self.parser = parser
        
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.dpi'] = 100
        
    def create_timeline_chart(self, figsize=(14, 8), max_methods=50) -> Figure:
        """
        Create a Gantt-style timeline chart showing method execution
        
        Args:
            figsize: Figure size (width, height)
            max_methods: Maximum number of methods to display
            
        Returns:
            Matplotlib Figure object
        """
        if self.df.empty:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, 'No data to display', 
                   ha='center', va='center', fontsize=12)
            return fig
        
        # Get critical path
        critical_path = self.parser.get_critical_path()
        critical_ids = {call.call_id for call in critical_path}
        
        # Strategy: Focus on critical path and longest methods
        # Get critical path methods first
        critical_df = self.df[self.df['call_id'].isin(critical_ids)]
        
        # Get top methods by duration (that aren't already in critical path)
        remaining_df = self.df[~self.df['call_id'].isin(critical_ids)]
        df_by_duration = remaining_df.nlargest(max_methods - len(critical_df), 'duration')
        
        # Combine
        df_combined = pd.concat([critical_df, df_by_duration])
        
        # Sort by start time for proper display
        df_sorted = df_combined.sort_values('start_time').copy()
        
        # Normalize timestamps relative to the FIRST method's start time
        # This shows the actual execution timeline
        min_time = df_sorted['start_time'].min()
        df_sorted['start_norm'] = df_sorted['start_time'] - min_time
        df_sorted['end_norm'] = df_sorted['end_time'] - min_time
        
        # Calculate the actual timeline span (when last method finishes)
        max_end_time = df_sorted['end_norm'].max()
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Color map
        colors = sns.color_palette("husl", n_colors=df_sorted['level'].max() + 1)
        
        # Plot each method as a horizontal bar
        for idx, row in df_sorted.iterrows():
            color = colors[row['level']]
            
            # Highlight critical path
            if row['call_id'] in critical_ids:
                color = 'red'
                alpha = 0.9
                linewidth = 2
            else:
                alpha = 0.7
                linewidth = 0.5
            
            # Draw bar
            ax.barh(y=idx, width=row['duration'], left=row['start_norm'],
                   height=0.8, color=color, alpha=alpha, 
                   edgecolor='black', linewidth=linewidth)
            
            # Add method name - only if bar is wide enough
            method_name = row['method_name']
            
            # Simplify method name for display
            if '.' in method_name:
                parts = method_name.split('.')
                if len(parts) > 2:
                    # Show last class.method
                    method_name = '...' + '.'.join(parts[-2:])
            
            if len(method_name) > 35:
                method_name = method_name[:32] + '...'
            
            # Only show text if bar is wide enough (relative to plot scale)
            duration_ratio = row['duration'] / max(max_end_time, 1)
            if duration_ratio > 0.015:  # Only if bar is > 1.5% of total width
                ax.text(row['start_norm'] + row['duration']/2, idx, 
                       f"{method_name}\n{row['duration']:.0f}ms",
                       ha='center', va='center', fontsize=6, 
                       bbox=dict(boxstyle='round,pad=0.2', 
                                facecolor='white', alpha=0.8, edgecolor='none'))
        
        # Customize plot
        ax.set_xlabel('Time from Start (milliseconds)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Method Calls', fontsize=12, fontweight='bold')
        title = f'Performance Timeline - Top {len(df_sorted)} Methods\n'
        title += f'Timeline Span: {max_end_time:.0f}ms ({max_end_time/1000:.0f}s)'
        if len(critical_path) > 0:
            title += f' | Critical Path: {len(critical_path)} calls'
        ax.set_title(title, fontsize=13, fontweight='bold', pad=20)
        
        # Create legend
        legend_elements = [
            mpatches.Patch(facecolor='red', alpha=0.9, 
                          label='Critical Path', edgecolor='black'),
            mpatches.Patch(facecolor='gray', alpha=0.7, 
                          label='Other Methods', edgecolor='black')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
        
        # Set y-axis with method names
        ax.set_yticks(range(len(df_sorted)))
        y_labels = []
        for _, row in df_sorted.iterrows():
            name = row['method_name']
            # Extract just the method name (last part after final dot)
            if '(' in name:
                name = name.split('(')[0]  # Remove parameters
            if '.' in name:
                name = name.split('.')[-1]  # Get last part
            if len(name) > 25:
                name = name[:22] + '...'
            y_labels.append(f"{name} ({row['duration']:.0f}ms)")
        ax.set_yticklabels(y_labels, fontsize=7)
        ax.invert_yaxis()
        
        # Grid
        ax.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        return fig
    
    def create_duration_chart(self, figsize=(12, 8), top_n=20) -> Figure:
        """
        Create a bar chart showing method durations
        
        Args:
            figsize: Figure size
            top_n: Number of top methods to show
            
        Returns:
            Matplotlib Figure object
        """
        if self.df.empty:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, 'No data to display', 
                   ha='center', va='center', fontsize=12)
            return fig
        
        # Get critical path
        critical_path = self.parser.get_critical_path()
        critical_ids = {call.call_id for call in critical_path}
        
        # Filter methods: >= 100ms OR leaf methods OR critical path
        def is_filtered_method(name):
            """Check if method should be filtered out (hidden)"""
            return name.startswith('System.') or 'vlocity_cmt' in name
        
        def should_include(row):
            # First check if method should be filtered out
            if is_filtered_method(row['method_name']):
                return False
            if row['call_id'] in critical_ids:
                return True
            if row['duration'] >= 100:
                return True
            # Check if leaf - for this we need to check num_children
            if row['num_children'] == 0 or (row['num_children'] > 0 and row['duration'] >= 10):
                # Include leaves or methods with some significance
                return row['duration'] >= 10
            return False
        
        df_filtered = self.df[self.df.apply(should_include, axis=1)].copy()
        
        # Get top N methods by duration
        df_top = df_filtered.nlargest(top_n, 'duration').copy()
        df_top['is_critical'] = df_top['call_id'].isin(critical_ids)
        df_top = df_top.sort_values('duration', ascending=True)
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize)
        
        # Create bars
        colors = ['red' if critical else 'steelblue' 
                 for critical in df_top['is_critical']]
        
        bars = ax.barh(range(len(df_top)), df_top['duration'], color=colors, alpha=0.8)
        
        # Add value labels
        for i, (bar, duration) in enumerate(zip(bars, df_top['duration'])):
            ax.text(duration, i, f' {duration:.0f}ms', 
                   va='center', fontsize=9)
        
        # Customize plot
        ax.set_yticks(range(len(df_top)))
        method_labels = []
        for name in df_top['method_name']:
            # Strip method signature (everything after and including '(')
            if '(' in name:
                name = name.split('(')[0]
            if len(name) > 50:
                name = name[:47] + '...'
            method_labels.append(name)
        ax.set_yticklabels(method_labels, fontsize=9)
        
        ax.set_xlabel('Duration (milliseconds)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Method Name', fontsize=12, fontweight='bold')
        ax.set_title(f'Top {top_n} Methods by Execution Time', 
                    fontsize=14, fontweight='bold', pad=20)
        
        # Legend
        legend_elements = [
            mpatches.Patch(facecolor='red', alpha=0.8, label='Critical Path'),
            mpatches.Patch(facecolor='steelblue', alpha=0.8, label='Other Methods')
        ]
        ax.legend(handles=legend_elements, loc='lower right', fontsize=10)
        
        ax.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        return fig
    
    def create_hierarchy_chart(self, figsize=(12, 10)) -> Figure:
        """
        Create a tree-like hierarchy chart
        
        Args:
            figsize: Figure size
            
        Returns:
            Matplotlib Figure object
        """
        if self.df.empty:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, 'No data to display', 
                   ha='center', va='center', fontsize=12)
            return fig
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Get critical path
        critical_path = self.parser.get_critical_path()
        critical_ids = {call.call_id for call in critical_path}
        
        # Draw tree recursively
        root_calls = self.parser.get_call_tree()
        
        if not root_calls:
            ax.text(0.5, 0.5, 'No hierarchical data to display', 
                   ha='center', va='center', fontsize=12)
            return fig
        
        # Calculate positions
        y_pos = [0]
        
        def draw_node(call, x, y, ax):
            """Recursively draw nodes"""
            # Determine color
            if call.call_id in critical_ids:
                color = 'red'
                alpha = 0.9
            else:
                color = 'lightblue'
                alpha = 0.7
            
            # Draw node
            circle = plt.Circle((x, y), 0.3, color=color, alpha=alpha, 
                              edgecolor='black', linewidth=2)
            ax.add_patch(circle)
            
            # Add label
            label = call.method_name
            if len(label) > 30:
                label = label[:27] + '...'
            
            ax.text(x, y, f"{label}\n{call.duration:.0f}ms", 
                   ha='center', va='center', fontsize=7,
                   bbox=dict(boxstyle='round,pad=0.2', 
                            facecolor='white', alpha=0.8))
            
            # Draw children
            if call.children:
                child_y = y - 2
                child_x_start = x - len(call.children) * 0.5
                
                for i, child in enumerate(call.children):
                    child_x = child_x_start + i * 1.5
                    
                    # Draw line to child
                    ax.plot([x, child_x], [y - 0.3, child_y + 0.3], 
                           'k-', linewidth=1, alpha=0.5)
                    
                    # Draw child
                    draw_node(child, child_x, child_y, ax)
        
        # Draw root nodes
        for i, root in enumerate(root_calls[:5]):  # Limit to first 5 roots
            draw_node(root, i * 3, 0, ax)
        
        ax.set_xlim(-2, max(5, len(root_calls)) * 3)
        ax.set_ylim(-10, 2)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title('Method Call Hierarchy (Top 5 Root Calls)', 
                    fontsize=14, fontweight='bold', pad=20)
        
        # Legend
        legend_elements = [
            mpatches.Patch(facecolor='red', alpha=0.9, label='Critical Path'),
            mpatches.Patch(facecolor='lightblue', alpha=0.7, label='Other Methods')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
        
        plt.tight_layout()
        return fig
    
    def create_call_tree_view(self, figsize=(14, 10)) -> Figure:
        """
        Create a Chrome DevTools-style hierarchical tree view
        Shows method calls with indentation, duration, and children time
        
        Args:
            figsize: Figure size
            
        Returns:
            Matplotlib Figure object with text-based tree
        """
        if self.df.empty:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, 'No data to display', 
                   ha='center', va='center', fontsize=12)
            return fig
        
        fig, ax = plt.subplots(figsize=figsize)
        ax.axis('off')
        
        # Get critical path
        critical_path = self.parser.get_critical_path()
        critical_ids = {call.call_id for call in critical_path}
        
        # Build tree text
        tree_lines = []
        tree_lines.append("Call Hierarchy Tree (Critical Path in RED)")
        tree_lines.append("=" * 120)
        tree_lines.append("")
        
        def format_method_name(name, max_len=80):
            """Format method name for display"""
            if len(name) > max_len:
                return name[:max_len-3] + "..."
            return name
        
        def is_filtered_method(method_name):
            """Check if method should be filtered out (hidden)"""
            return method_name.startswith('System.') or 'vlocity_cmt' in method_name
        
        def should_include_method(call):
            """
            Filter methods: include if:
            - Duration >= 100ms, OR
            - It's a leaf method (no non-filtered children), OR  
            - It's on the critical path
            """
            if call.call_id in critical_ids:
                return True
            if call.duration >= 100:
                return True
            # Check if it's a leaf (no non-filtered children)
            non_filtered_children = [c for c in call.children if not is_filtered_method(c.method_name)]
            return len(non_filtered_children) == 0
        
        def build_tree_text(call, indent=0, is_last=False, max_depth=15):
            """Recursively build tree text with filtering"""
            if indent > max_depth:
                return
            
            if not should_include_method(call):
                # Still process children even if we skip this one
                for child in call.children:
                    build_tree_text(child, indent, is_last, max_depth)
                return
            
            # Calculate children time
            children_time = sum(child.duration for child in call.children)
            
            # Create indent string
            if indent == 0:
                prefix = "root@0 "
            else:
                # Use tree characters
                if is_last:
                    prefix = "  " * (indent - 1) + "└─ "
                else:
                    prefix = "  " * (indent - 1) + "├─ "
            
            # Format the line
            method_display = format_method_name(call.method_name, 70)
            line = f"{prefix}[{call.duration:.0f}ms] {method_display}"
            
            if call.children:
                line += f" (time in children: {children_time:.0f}ms)"
            
            # Mark critical path
            is_critical = call.call_id in critical_ids
            tree_lines.append((line, is_critical))
            
            # Filter and process children
            filtered_children = [c for c in call.children if should_include_method(c)]
            for i, child in enumerate(filtered_children):
                is_last_child = (i == len(filtered_children) - 1)
                build_tree_text(child, indent + 1, is_last_child, max_depth)
        
        # Get root calls and build tree for each
        root_calls = self.parser.get_call_tree()
        
        # Limit to top 3 root calls by duration to avoid overcrowding
        root_calls_sorted = sorted(root_calls, key=lambda x: x.duration, reverse=True)[:3]
        
        for root in root_calls_sorted:
            build_tree_text(root)
            tree_lines.append(("", False))  # Empty line between roots
        
        # Calculate total children time for root
        if root_calls:
            total_children = sum(root.duration for root in root_calls)
            tree_lines.append("")
            tree_lines.append(("=" * 120, False))
            tree_lines.append((f"Total execution time (root level): {total_children:.0f}ms ({total_children/1000:.0f}s)", False))
            tree_lines.append((f"Number of method calls: {len(self.df)}", False))
            tree_lines.append((f"Critical path length: {len(critical_path)} calls", False))
        
        # Render text
        y_pos = 0.95
        line_height = 0.015
        
        for item in tree_lines:
            if isinstance(item, tuple):
                line, is_critical = item
            else:
                line = item
                is_critical = False
            
            if not line:  # Skip empty lines at the end
                continue
                
            color = 'red' if is_critical else 'black'
            fontweight = 'bold' if is_critical else 'normal'
            fontsize = 8 if is_critical else 7
            
            ax.text(0.01, y_pos, line, 
                   fontfamily='monospace',
                   fontsize=fontsize,
                   fontweight=fontweight,
                   color=color,
                   verticalalignment='top',
                   horizontalalignment='left',
                   transform=ax.transAxes)
            
            y_pos -= line_height
            
            if y_pos < 0.01:
                break  # Stop if we run out of space
        
        ax.set_title('Method Call Tree - Hierarchical View', 
                    fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        return fig
    
    def create_summary_stats(self, figsize=(10, 6)) -> Figure:
        """
        Create a summary statistics visualization
        
        Args:
            figsize: Figure size
            
        Returns:
            Matplotlib Figure object
        """
        if self.df.empty:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, 'No data to display', 
                   ha='center', va='center', fontsize=12)
            return fig
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=figsize)
        
        # 1. Duration distribution
        ax1.hist(self.df['duration'], bins=30, color='steelblue', alpha=0.7, edgecolor='black')
        ax1.set_xlabel('Duration (ms)', fontweight='bold')
        ax1.set_ylabel('Frequency', fontweight='bold')
        ax1.set_title('Duration Distribution', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # 2. Methods by level
        level_counts = self.df['level'].value_counts().sort_index()
        ax2.bar(level_counts.index, level_counts.values, color='coral', alpha=0.7, edgecolor='black')
        ax2.set_xlabel('Nesting Level', fontweight='bold')
        ax2.set_ylabel('Number of Methods', fontweight='bold')
        ax2.set_title('Method Calls by Nesting Level', fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        
        # 3. Self time vs total time (top 10)
        df_top = self.df.nlargest(10, 'duration')
        x = np.arange(len(df_top))
        width = 0.35
        ax3.bar(x - width/2, df_top['duration'], width, label='Total Time', 
               color='steelblue', alpha=0.7)
        ax3.bar(x + width/2, df_top['self_time'], width, label='Self Time', 
               color='orange', alpha=0.7)
        ax3.set_xlabel('Method Index', fontweight='bold')
        ax3.set_ylabel('Time (ms)', fontweight='bold')
        ax3.set_title('Total vs Self Time (Top 10)', fontweight='bold')
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')
        
        # 4. Summary statistics text
        ax4.axis('off')
        stats_text = f"""
        PERFORMANCE SUMMARY
        {'=' * 40}
        
        Total Method Calls: {len(self.df)}
        Total Execution Time: {self.df['duration'].sum():.0f} ms
        
        Average Duration: {self.df['duration'].mean():.0f} ms
        Median Duration: {self.df['duration'].median():.0f} ms
        Max Duration: {self.df['duration'].max():.0f} ms
        Min Duration: {self.df['duration'].min():.0f} ms
        
        Max Nesting Level: {self.df['level'].max()}
        
        Critical Path Length: {len(self.parser.get_critical_path())} calls
        Critical Path Time: {sum(c.duration for c in self.parser.get_critical_path()):.0f} ms
        """
        
        ax4.text(0.1, 0.9, stats_text, fontsize=10, family='monospace',
                va='top', ha='left')
        
        plt.suptitle('Performance Analysis Summary', 
                    fontsize=14, fontweight='bold', y=0.98)
        plt.tight_layout()
        return fig

