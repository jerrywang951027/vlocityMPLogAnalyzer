# 🚀 Jupyter Notebook Quick Start Guide

## ✅ Installation Complete!
Jupyter has been successfully installed in your virtual environment.

---

## 📝 How to Launch Jupyter

### Option 1: Launch from Terminal
```bash
cd /Users/jin.wang/workspace/tools/perfLogAnalyzer1
source venv/bin/activate
jupyter notebook
```

This will:
1. Start the Jupyter server
2. Open your default web browser
3. Show the file explorer at `http://localhost:8888`

### Option 2: Launch JupyterLab (Modern Interface)
```bash
cd /Users/jin.wang/workspace/tools/perfLogAnalyzer1
source venv/bin/activate
jupyter lab
```

JupyterLab provides a more modern, IDE-like interface.

---

## 🎯 Getting Started

### Quick Start: Use the Template Script

I've created a template script with all the analysis code ready to use:

**File:** `jupyter_analysis.py`

1. Launch Jupyter: `jupyter notebook`
2. In the browser, create a new Python 3 notebook
3. Open `jupyter_analysis.py` in a text editor
4. Copy sections (marked as CELL 1, CELL 2, etc.) into separate notebook cells
5. Run cells with `Shift+Enter`

### Alternative: Create Your Own Notebook

1. Launch Jupyter: `jupyter notebook`
2. Click "New" → "Python 3"
3. Start with this first cell:

```python
# Setup
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'source'))

from parser.log_parser import LogParser
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

%matplotlib inline  # Display plots inline

print("✅ Ready!")
```

4. Run it with `Shift+Enter`
5. Add a new cell to load your log:

```python
# Parse log
parser = LogParser()
parser.parse_file('logs/apex-07LU900000K1FuZMAV.log')
df = pd.DataFrame([call.to_dict() for call in parser.method_calls])

print(f"Loaded {len(df)} method calls")
df.head()
```

---

## 🎨 Jupyter Interface Basics

### Keyboard Shortcuts (Command Mode - press `Esc` first)
- `A` - Insert cell **above**
- `B` - Insert cell **below**
- `M` - Convert to **Markdown** (for text/documentation)
- `Y` - Convert to **Code**
- `DD` - **Delete** cell
- `Z` - **Undo** delete

### Keyboard Shortcuts (Edit Mode - press `Enter` to enter)
- `Shift+Enter` - **Run** cell and move to next
- `Ctrl+Enter` - **Run** cell and stay
- `Tab` - **Auto-complete** (type `df.` then Tab)
- `Shift+Tab` - Show **function documentation**

### Toolbar Buttons
- ▶️ Run - Execute current cell
- ⏸️ Stop - Interrupt running cell
- 🔄 Restart - Restart Python kernel
- 💾 Save - Save notebook

---

## 📊 What You Can Do in Jupyter (vs Desktop App)

| Task | Desktop App | Jupyter |
|------|-------------|---------|
| **Load & view logs** | ✅ Easy | ✅ Code required |
| **Pre-built charts** | ✅ Automatic | ⚠️ Manual |
| **Custom queries** | ❌ Limited | ✅ Unlimited |
| **Filter data** | ✅ 2 checkboxes | ✅ Any SQL-like filter |
| **Export results** | ⚠️ Screenshots | ✅ CSV, HTML, PDF |
| **Advanced stats** | ❌ None | ✅ Full Python/pandas |
| **Machine Learning** | ❌ No | ✅ Yes (sklearn, etc.) |
| **Documentation** | ❌ No | ✅ Inline markdown |
| **Share analysis** | ⚠️ Manual | ✅ Share .ipynb file |

---

## 💡 Example Analyses You Can Do

### 1. Find Methods Taking > 1 Second
```python
slow = df[df['duration'] > 1000]
slow[['method_name', 'duration', 'self_time']].sort_values('duration', ascending=False)
```

### 2. Filter by Class Name
```python
cpq_methods = df[df['method_name'].str.contains('CpqAppHandler')]
cpq_methods[['method_name', 'duration']].sort_values('duration', ascending=False)
```

### 3. Statistical Summary
```python
df[['duration', 'self_time']].describe()
```

### 4. Custom Visualization
```python
import matplotlib.pyplot as plt

top_10 = df.nlargest(10, 'duration')
plt.barh(top_10['method_name'], top_10['duration'])
plt.xlabel('Duration (ms)')
plt.title('Top 10 Slowest Methods')
plt.show()
```

### 5. Calculate Time Percentage
```python
total_time = df['duration'].max()
df['pct_of_total'] = (df['duration'] / total_time * 100).round(2)
df[['method_name', 'duration', 'pct_of_total']].nlargest(20, 'duration')
```

### 6. Find Outliers
```python
mean = df['duration'].mean()
std = df['duration'].std()
outliers = df[df['duration'] > mean + 2*std]
print(f"Found {len(outliers)} outliers (> 2 std dev)")
```

---

## 🔗 Combining Desktop App + Jupyter

**Best Practice:** Use both!

### Desktop App - For:
- ✅ Quick daily checks
- ✅ Non-technical stakeholders
- ✅ Standard reports
- ✅ Visual tree exploration

### Jupyter - For:
- ✅ Deep investigations
- ✅ Custom queries ("show me all methods in class X that take > 500ms")
- ✅ Advanced statistics (outlier detection, correlations)
- ✅ Machine learning (predict performance issues)
- ✅ Comparing multiple log files
- ✅ Creating custom reports

---

## 📖 Learning Resources

### Jupyter Basics
- Official Jupyter Docs: https://jupyter.org/documentation
- Keyboard shortcuts: Press `H` in Jupyter

### pandas (Data Analysis)
- pandas docs: https://pandas.pydata.org/docs/
- 10 minutes to pandas: https://pandas.pydata.org/docs/user_guide/10min.html

### Matplotlib (Plotting)
- Matplotlib gallery: https://matplotlib.org/stable/gallery/

### Common pandas Operations
```python
# Filter rows
df[df['duration'] > 1000]

# Select columns
df[['method_name', 'duration']]

# Sort
df.sort_values('duration', ascending=False)

# Group by
df.groupby('level')['duration'].mean()

# Top N
df.nlargest(10, 'duration')

# String contains
df[df['method_name'].str.contains('Cpq')]

# Statistical summary
df.describe()
```

---

## 🛑 Stopping Jupyter

When you're done:
1. Close browser tabs
2. In terminal where Jupyter is running, press `Ctrl+C` twice
3. Or just close the terminal

---

## 🎉 Next Steps

1. **Launch Jupyter**: `source venv/bin/activate && jupyter notebook`
2. **Create a new notebook** or copy from `jupyter_analysis.py`
3. **Load your log file**
4. **Experiment!** Try different queries, filters, visualizations

**Remember:** Jupyter is for **exploration** and **custom analysis**.  
Your desktop app is still great for **quick standard reports**!

---

## ❓ Troubleshooting

### "jupyter: command not found"
Make sure you activated the venv:
```bash
source venv/bin/activate
# You should see (venv) in your prompt
```

### "No module named 'parser'"
Make sure you're in the correct directory:
```bash
cd /Users/jin.wang/workspace/tools/perfLogAnalyzer1
```

### Plots not showing
Add this to the top of your notebook:
```python
%matplotlib inline
```

### Kernel died / Memory issues
Large log files may need more memory. Try:
1. Filter data early: `df = df[df['duration'] > 100]`
2. Restart kernel: Kernel menu → Restart

---

**Happy Analyzing! 🚀📊**

