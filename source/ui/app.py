"""
Desktop Application UI
Tkinter-based GUI for performance log analysis
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser.log_parser import LogParser
from visualization.chart_generator import ChartGenerator


class PerfLogAnalyzerApp:
    """Main application class"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("8x8 Performance Log Analyzer -Standard Cart Api")
        self.root.geometry("1400x900")
        
        # Data
        self.df = None
        self.parser = None
        self.chart_generator = None
        self.current_file = None
        
        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the user interface"""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Log File", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top frame - file selection and controls
        top_frame = ttk.Frame(main_container)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(top_frame, text="Log File:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.file_label = ttk.Label(top_frame, text="No file selected", 
                                     foreground="gray", font=('Arial', 10))
        self.file_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(top_frame, text="Browse...", command=self.open_file).pack(side=tk.LEFT, padx=5)
        
        self.analyze_btn = ttk.Button(top_frame, text="Analyze", 
                                      command=self.analyze_file, state=tk.DISABLED)
        self.analyze_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress indicator
        self.progress_label = ttk.Label(top_frame, text="", foreground="blue")
        self.progress_label.pack(side=tk.LEFT, padx=20)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.tab_tree = ttk.Frame(self.notebook)
        self.tab_timeline = ttk.Frame(self.notebook)
        self.tab_duration = ttk.Frame(self.notebook)
        self.tab_hierarchy = ttk.Frame(self.notebook)
        self.tab_summary = ttk.Frame(self.notebook)
        self.tab_data = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_tree, text="📊 Call Tree")
        self.notebook.add(self.tab_timeline, text="Timeline")
        self.notebook.add(self.tab_duration, text="Duration Analysis")
        self.notebook.add(self.tab_hierarchy, text="Hierarchy Graph")
        self.notebook.add(self.tab_summary, text="Summary Stats")
        self.notebook.add(self.tab_data, text="Raw Data")
        
        # Initialize tab contents
        self._init_tree_tab()
        self._init_timeline_tab()
        self._init_duration_tab()
        self._init_hierarchy_tab()
        self._init_summary_tab()
        self._init_data_tab()
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def _init_tree_tab(self):
        """Initialize tree view tab with treeview widget"""
        # Top control frame
        control_frame = ttk.Frame(self.tab_tree)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Checkbox for filtering
        self.hide_fast_methods = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, 
                       text="Hide methods < 100ms (except critical path)",
                       variable=self.hide_fast_methods,
                       command=self._refresh_tree_view).pack(side=tk.LEFT, padx=5)
        
        # Checkbox for expand all
        self.expand_all = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, 
                       text="Expand All",
                       variable=self.expand_all,
                       command=self._toggle_expand_all).pack(side=tk.LEFT, padx=5)
        
        # Frame for tree
        frame = ttk.Frame(self.tab_tree)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbars
        vsb = ttk.Scrollbar(frame, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        hsb = ttk.Scrollbar(frame, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview widget
        self.call_tree = ttk.Treeview(frame, 
                                      columns=('duration', 'self_time', 'children_time'),
                                      yscrollcommand=vsb.set,
                                      xscrollcommand=hsb.set)
        self.call_tree.pack(fill=tk.BOTH, expand=True)
        
        vsb.config(command=self.call_tree.yview)
        hsb.config(command=self.call_tree.xview)
        
        # Configure columns
        self.call_tree.heading('#0', text='Method Name', anchor=tk.W)
        self.call_tree.heading('duration', text='Duration (ms)', anchor=tk.E)
        self.call_tree.heading('self_time', text='Self Time (ms)', anchor=tk.E)
        self.call_tree.heading('children_time', text='Children Time (ms)', anchor=tk.E)
        
        # Make method name column wider with NO stretch to enable horizontal scrolling
        # With stretch=False, the horizontal scrollbar will appear when content is wider than visible area
        self.call_tree.column('#0', width=1200, minwidth=400, stretch=False)
        self.call_tree.column('duration', width=120, anchor=tk.E, stretch=False)
        self.call_tree.column('self_time', width=120, anchor=tk.E, stretch=False)
        self.call_tree.column('children_time', width=150, anchor=tk.E, stretch=False)
        
    def _init_timeline_tab(self):
        """Initialize timeline tab"""
        label = ttk.Label(self.tab_timeline, text="Timeline chart will appear here after analysis", 
                         font=('Arial', 12))
        label.pack(expand=True)
        
    def _init_duration_tab(self):
        """Initialize duration tab with filter checkbox"""
        # Top control frame
        control_frame = ttk.Frame(self.tab_duration)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Checkbox for filtering
        self.hide_vlocity_methods = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, 
                       text="Hide vlocity_cmt methods",
                       variable=self.hide_vlocity_methods,
                       command=self._refresh_duration_chart).pack(side=tk.LEFT, padx=5)
        
        # Content frame for the chart
        self.duration_content_frame = ttk.Frame(self.tab_duration)
        self.duration_content_frame.pack(fill=tk.BOTH, expand=True)
        
    def _init_hierarchy_tab(self):
        """Initialize hierarchy tab"""
        label = ttk.Label(self.tab_hierarchy, text="Hierarchy chart will appear here after analysis", 
                         font=('Arial', 12))
        label.pack(expand=True)
        
    def _init_summary_tab(self):
        """Initialize summary tab"""
        label = ttk.Label(self.tab_summary, text="Summary statistics will appear here after analysis", 
                         font=('Arial', 12))
        label.pack(expand=True)
        
    def _init_data_tab(self):
        """Initialize data tab with treeview"""
        # Frame for treeview and scrollbar
        frame = ttk.Frame(self.tab_data)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbars
        vsb = ttk.Scrollbar(frame, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        hsb = ttk.Scrollbar(frame, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview
        self.tree = ttk.Treeview(frame, yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
    def open_file(self):
        """Open file dialog to select log file"""
        filename = filedialog.askopenfilename(
            title="Select Performance Log File",
            filetypes=[
                ("Text files", "*.txt"),
                ("Log files", "*.log"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            self.current_file = filename
            # Truncate long filenames for display
            display_name = filename
            if len(display_name) > 80:
                display_name = "..." + display_name[-77:]
            self.file_label.config(text=display_name, foreground="black")
            self.analyze_btn.config(state=tk.NORMAL)
            self.status_bar.config(text=f"File selected: {filename}")
            
    def analyze_file(self):
        """Analyze the selected log file"""
        if not self.current_file:
            messagebox.showerror("Error", "Please select a log file first")
            return
        
        try:
            self.progress_label.config(text="Analyzing...")
            self.root.update()
            
            # Parse log file
            self.parser = LogParser()
            self.df = self.parser.parse_file(self.current_file)
            
            if self.df.empty:
                messagebox.showwarning("Warning", 
                    "No data could be parsed from the log file.\n\n"
                    "Please ensure the log file has the correct format:\n"
                    "timestamp | ENTER/EXIT | MethodName")
                self.progress_label.config(text="")
                return
            
            # Create chart generator
            self.chart_generator = ChartGenerator(self.df, self.parser)
            
            # Update all visualizations
            self._update_tree_chart()
            self._update_timeline_chart()
            self._update_duration_chart()
            self._update_hierarchy_chart()
            self._update_summary_chart()
            self._update_data_table()
            
            self.progress_label.config(text="Analysis complete!")
            self.status_bar.config(text=f"Analyzed {len(self.df)} method calls")
            
            # Switch to tree tab (most useful view)
            self.notebook.select(self.tab_tree)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to analyze log file:\n\n{str(e)}")
            self.progress_label.config(text="Analysis failed")
            import traceback
            traceback.print_exc()
            
    def _refresh_tree_view(self):
        """Refresh tree view when filter changes"""
        if hasattr(self, 'parser') and self.parser:
            self._update_tree_chart()
    
    def _toggle_expand_all(self):
        """Expand or collapse all tree items"""
        def expand_recursive(item):
            """Recursively expand or collapse an item and its children"""
            self.call_tree.item(item, open=self.expand_all.get())
            for child in self.call_tree.get_children(item):
                expand_recursive(child)
        
        # Apply to all top-level items
        for item in self.call_tree.get_children():
            expand_recursive(item)
    
    def _update_tree_chart(self):
        """Update call tree view - follow ACTUAL tree structure from parser"""
        # Clear existing items
        for item in self.call_tree.get_children():
            self.call_tree.delete(item)
        
        # Get critical path for highlighting
        critical_path = self.parser.get_critical_path()
        critical_ids = {call.call_id for call in critical_path}
        
        # Get filter setting
        hide_fast = self.hide_fast_methods.get()
        min_duration = 100 if hide_fast else 0
        
        def add_node(call, parent=''):
            """Simply add nodes following the actual tree structure"""
            # Apply simple filter: only skip if < threshold AND not critical path
            if hide_fast:
                if call.duration < min_duration and call.call_id not in critical_ids:
                    # But still recurse to children - they might be significant
                    for child in call.children:
                        add_node(child, parent)
                    return
            
            # Calculate children time
            children_time = sum(child.duration for child in call.children)
            
            # Format the display name - strip method signature (everything after last dot + parens)
            # e.g., "Class.method(String, Int)" -> "Class.method"
            method_display = call.method_name
            if '(' in method_display:
                # Find last dot before the opening paren
                paren_pos = method_display.find('(')
                method_display = method_display[:paren_pos]
            
            display_name = f"[{call.duration:.0f}ms] {method_display}"
            
            # Add to treeview
            item_id = self.call_tree.insert(
                parent, 
                'end',
                text=display_name,
                values=(
                    f"{call.duration:.0f}",
                    f"{call.self_time:.0f}" if call.self_time else "0",
                    f"{children_time:.0f}"
                ),
                tags=('critical',) if call.call_id in critical_ids else ()
            )
            
            # Add all children - let recursion handle filtering
            for child in call.children:
                add_node(child, item_id)
        
        # Get root calls
        root_calls = self.parser.get_call_tree()
        
        # Sort by duration
        root_calls_sorted = sorted(root_calls, key=lambda x: x.duration, reverse=True)
        
        # Add summary header
        total_time = sum(root.duration for root in root_calls)
        header = self.call_tree.insert('', 'end', 
                                       text=f"root@0",
                                       values=('', '', ''),
                                       tags=('header',))
        
        # Add top roots (show top 5 to avoid clutter)
        for root in root_calls_sorted[:5]:
            add_node(root, header)
        
        # Configure tags for styling
        self.call_tree.tag_configure('critical', foreground='red', font=('TkDefaultFont', 10, 'bold'))
        self.call_tree.tag_configure('header', font=('TkDefaultFont', 10, 'bold'))
        
        # Expand the header
        self.call_tree.item(header, open=True)
        
    def _update_timeline_chart(self):
        """Update timeline chart"""
        # Clear existing widgets
        for widget in self.tab_timeline.winfo_children():
            widget.destroy()
        
        # Create chart
        fig = self.chart_generator.create_timeline_chart()
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.tab_timeline)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        toolbar = NavigationToolbar2Tk(canvas, self.tab_timeline)
        toolbar.update()
        
    def _refresh_duration_chart(self):
        """Refresh duration chart when filter changes"""
        if hasattr(self, 'chart_generator') and self.chart_generator:
            self._update_duration_chart()
    
    def _update_duration_chart(self):
        """Update duration chart with optional filtering"""
        # Clear existing widgets in content frame only
        for widget in self.duration_content_frame.winfo_children():
            widget.destroy()
        
        # Get filter setting and apply it
        hide_vlocity = self.hide_vlocity_methods.get()
        
        # Filter dataframe if needed
        if hide_vlocity:
            filtered_df = self.df[~self.df['method_name'].str.startswith('vlocity_cmt')]
            # Create a temporary chart generator with filtered data
            from visualization.chart_generator import ChartGenerator
            temp_generator = ChartGenerator(filtered_df, self.parser)
            fig = temp_generator.create_duration_chart()
        else:
            fig = self.chart_generator.create_duration_chart()
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.duration_content_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        toolbar = NavigationToolbar2Tk(canvas, self.duration_content_frame)
        toolbar.update()
        
    def _update_hierarchy_chart(self):
        """Update hierarchy chart"""
        # Clear existing widgets
        for widget in self.tab_hierarchy.winfo_children():
            widget.destroy()
        
        # Create chart
        fig = self.chart_generator.create_hierarchy_chart()
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.tab_hierarchy)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        toolbar = NavigationToolbar2Tk(canvas, self.tab_hierarchy)
        toolbar.update()
        
    def _update_summary_chart(self):
        """Update summary statistics"""
        # Clear existing widgets
        for widget in self.tab_summary.winfo_children():
            widget.destroy()
        
        # Create chart
        fig = self.chart_generator.create_summary_stats()
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.tab_summary)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        toolbar = NavigationToolbar2Tk(canvas, self.tab_summary)
        toolbar.update()
        
    def _update_data_table(self):
        """Update raw data table"""
        # Clear existing items
        self.tree.delete(*self.tree.get_children())
        
        # Setup columns
        columns = list(self.df.columns)
        self.tree['columns'] = columns
        self.tree['show'] = 'headings'
        
        # Format column headings
        for col in columns:
            self.tree.heading(col, text=col.replace('_', ' ').title())
            # Make method_name column wider and stretchable for long names
            if col == 'method_name':
                self.tree.column(col, width=500, minwidth=300, anchor=tk.W, stretch=True)
            else:
                self.tree.column(col, width=120, anchor=tk.W, stretch=False)
        
        # Add data rows
        for idx, row in self.df.iterrows():
            values = []
            for col in columns:
                val = row[col]
                # Format floats
                if isinstance(val, float):
                    values.append(f"{val:.3f}")
                else:
                    values.append(str(val))
            self.tree.insert('', tk.END, values=values)
            
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About",
            "Performance Log Analyzer v1.0\n\n"
            "Analyzes Salesforce Industries CPQ Quoting performance logs\n\n"
            "Features:\n"
            "- Parse nested method calls\n"
            "- Visualize execution timeline\n"
            "- Identify critical path\n"
            "- Performance statistics\n\n"
            "© 2025"
        )
        
    def run(self):
        """Start the application"""
        self.root.mainloop()

