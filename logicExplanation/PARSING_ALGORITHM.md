# Log Parsing Algorithm Explanation

## Overview

This document explains the core algorithm used to parse Salesforce Apex debug logs and construct an accurate method call hierarchy tree. The key challenge is dealing with incomplete/malformed log data while maintaining correct parent-child relationships.

---

## Table of Contents

1. [Log Format](#log-format)
2. [Parsing Strategy](#parsing-strategy)
3. [Key Insight: Inconsistent Level Numbers](#key-insight-inconsistent-level-numbers)
4. [Parent-Child Relationship Algorithm](#parent-child-relationship-algorithm)
5. [Handling Unclosed Methods](#handling-unclosed-methods)
6. [Tree Construction](#tree-construction)
7. [Example Walkthrough](#example-walkthrough)

---

## Log Format

Salesforce Apex debug logs contain multiple types of entries. We focus on these key types:

### CODE_UNIT_STARTED/FINISHED
```
08:58:28.2 (2097211)|CODE_UNIT_STARTED|[EXTERNAL]|01p5j00000Js5WI|vlocity_cmt.APIItemsCartsCpqV2.createCartItems()
08:58:31.3 (3919240262)|CODE_UNIT_FINISHED|vlocity_cmt.CpqApexCallable
```
- Marks the start/end of an execution unit (Apex class/trigger/callout)
- **Can be nested**: Inner CODE_UNITs (e.g., Apex callouts) appear within outer CODE_UNITs
- Top-level CODE_UNIT is treated as the root (level 0)
- Nested CODE_UNITs are assigned incrementing level numbers (1, 2, 3...)
- **Format variation**: STARTED events have `[EXTERNAL]|` prefix, FINISHED events do not

### METHOD_ENTRY/EXIT
```
08:58:28.2 (138268661)|METHOD_ENTRY|[117]|01p5j00000Js6AP|vlocity_cmt.OpenInterfaceSharingWrapper.callOpenInterface2WithAppropriateSharing(...)
08:58:34.42 (6702786940)|METHOD_EXIT|[117]|01p5j00000Js6AP|vlocity_cmt.OpenInterfaceSharingWrapper.callOpenInterface2WithAppropriateSharing(...)
```
- **Timestamp**: Nanoseconds since start (in parentheses)
- **Event Type**: METHOD_ENTRY or METHOD_EXIT
- **Level**: `[117]` - originally thought to indicate nesting depth
- **Method ID**: `01p5j00000Js6AP`
- **Method Name**: Full qualified name with signature

---

## Parsing Strategy

### Phase 1: Parse Log Entries

```python
def _parse_line(self, line):
    # Extract components using regex
    timestamp = int(match.group(1)) / 1000000.0  # Convert nanoseconds to milliseconds
    event_type = 'ENTRY' or 'EXIT'
    level = int(match.group(3))  # For METHOD events
    method_name = match.group(4)  # Cleaned of ID prefix
    
    # For CODE_UNIT events, track nesting depth
    if event_type == 'STARTED':
        level = self.code_unit_depth
        self.code_unit_depth += 1
    elif event_type == 'FINISHED':
        self.code_unit_depth = max(0, self.code_unit_depth - 1)
        level = self.code_unit_depth
```

**Key Steps:**
1. Use regex to extract timestamp, event type, level, and method name
2. Convert nanosecond timestamps to milliseconds
3. Clean method names by removing ID prefixes (e.g., `01p5j00000Js5fA|`)
4. For CODE_UNIT events, assign level based on nesting depth counter
5. Store as `LogEntry` objects

**Regex Pattern for CODE_UNIT:**
```python
# Matches both formats:
# STARTED: 08:58:28.2 (2097211)|CODE_UNIT_STARTED|[EXTERNAL]|vlocity_cmt.APIItemsCartsCpqV2.createCartItems()
# FINISHED: 08:58:31.3 (3919240262)|CODE_UNIT_FINISHED|vlocity_cmt.CpqApexCallable
r'(\d{2}:\d{2}:\d{2}\.\d+)\s*\((\d+)\)\|CODE_UNIT_(STARTED|FINISHED)\|(?:[^\|]*\|)?(.+)$'
#                                                                       ^^^^^^^^^^^
#                                                  Optional [EXTERNAL]| prefix
```

### Phase 2: Match Entry/Exit Pairs

```python
def _build_call_tree(self):
    level_stacks = {}  # Stack per level number
    
    for entry in self.entries:
        if entry.event_type == 'ENTRY':
            # Create MethodCall object
            # Push onto level-specific stack
            level_stacks[entry.level].append(...)
            
        elif entry.event_type == 'EXIT':
            # Find matching ENTRY on the same level stack
            # Pop from stack and add to method_calls list
```

**Why Level-Specific Stacks?**
- Methods at the same level can be siblings (called sequentially)
- Need to match EXIT with the most recent ENTRY at that level
- Prevents mismatching when multiple methods share the same name

### Phase 3: Handle Unclosed Methods

Some methods have `METHOD_ENTRY` but no matching `METHOD_EXIT` (typically constructors or methods that exceeded log limits).

**Strategy:**
- **Level 0 (CODE_UNIT)**: Keep as root, calculate end time from last log entry
- **Other levels**: Remove completely and log as exceptions

```python
if enter_entry.level == 0:
    # Keep as root
    method_call.end_time = self.entries[-1].timestamp
    method_call.duration = method_call.end_time - enter_entry.timestamp
    self.method_calls.append(method_call)
else:
    # Remove - log exception
    self.exceptions_log.append({...})
```

**Why Remove Non-Root Unclosed Methods?**
- Their duration would be incorrect (unknown end time)
- They corrupt parent-child relationships if kept
- Their children can be reparented correctly using time containment

---

## Key Insight: Inconsistent Level Numbers

### The Problem

Initially, we assumed level numbers indicated nesting depth:
- Higher level = outer/parent method
- Lower level = inner/child method

**This assumption was WRONG!**

### Example Showing Inconsistency

```
08:58:28.2 (138268661)|METHOD_ENTRY|[117]|callOpenInterface2WithAppropriateSharing
08:58:28.2 (151784274)|METHOD_ENTRY|[36]|OpenInterfaceWithSharingWrapper.callOpenInterface2
08:58:28.2 (155992486)|METHOD_ENTRY|[72]|InvokeService.invokeAsMap
08:58:28.2 (819615869)|METHOD_ENTRY|[216]|CpqAppHandler.invokeMethod
08:58:34.42 (6196007289)|METHOD_EXIT|[216]|CpqAppHandler.invokeMethod          ← Exits FIRST (deepest)
08:58:34.42 (6702673320)|METHOD_EXIT|[72]|InvokeService.invokeAsMap            ← Exits second
08:58:34.42 (6702786940)|METHOD_EXIT|[117]|callOpenInterface2WithAppropriateSharing ← Exits LAST (outermost)
```

**Observation:**
- Level 117 → Level 36 ✅ (higher to lower)
- Level 36 → Level 72 ❌ (lower to higher!)
- Level 72 → Level 216 ❌ (lower to higher!)

But the EXIT order proves:
- 216 is deepest (exits first)
- 72 contains 216
- 117 is outermost (exits last)

**Conclusion:** Level numbers are NOT consistently hierarchical. They may indicate something else (stack depth at creation time, recursion depth, etc.) but cannot be relied upon for parent-child relationships.

---

## Parent-Child Relationship Algorithm

### Core Principle: Pure Time Containment

**A method is a child of another method if and only if:**
1. Parent starts before or at the same time as the child
2. Parent ends after or at the same time as the child
3. Parent is the **most recent** (closest) method satisfying conditions 1-2

This is called **full time containment**.

### Algorithm Implementation

```python
# Sort all methods by start time
sorted_calls = sorted(self.method_calls, key=lambda x: x.start_time)

for i, call in enumerate(sorted_calls):
    if call.level == 0:
        call.parent_id = None  # Root
        continue
    
    # Search backwards for parent
    best_parent = None
    for j in range(i - 1, -1, -1):
        candidate = sorted_calls[j]
        
        # Check full containment
        if (candidate.start_time <= call.start_time and
            call.end_time <= candidate.end_time):
            # Found immediate parent
            best_parent = candidate
            break  # Stop at first match (most recent)
    
    # Fallback to level-0 root if no parent found
    if best_parent is None and level_0_root:
        if (level_0_root.start_time <= call.start_time < 
            level_0_root.end_time):
            best_parent = level_0_root
    
    call.parent_id = best_parent.call_id if best_parent else None
```

### Why This Works

1. **Sorted by start time**: Processing chronologically ensures we've seen all potential parents before processing a child

2. **Backward search**: Most recent method is the immediate parent, not a grandparent

3. **Full containment**: Ensures logical relationship
   - Parent method's execution completely contains child's execution
   - No overlapping siblings (two methods running at the same time)

4. **Break on first match**: The most recent containing method is the direct parent, not an ancestor further up the tree

### Time Complexity

- **O(n²)** in worst case (deeply nested linear chain)
- **O(n)** in best case (flat structure, all children of root)
- **Typical case**: O(n × d) where d = average tree depth (~10-50), much better than O(n²)

---

## Handling Unclosed Methods

### Why They Exist

1. **Constructors**: Often lack explicit EXIT events
2. **Log Size Limits**: Salesforce truncates logs after a size/time limit
3. **Exceptions**: Uncaught exceptions may prevent EXIT logging
4. **System Methods**: Some framework methods don't log exits

### Detection

After processing all ENTRY/EXIT pairs, remaining entries in `level_stacks` are unclosed:

```python
for level in sorted(level_stacks.keys()):
    for enter_entry, call_id, method_call in level_stacks[level]:
        # This method has ENTRY but no EXIT
```

### Handling Strategy

**Level 0 (CODE_UNIT):**
```python
if enter_entry.level == 0:
    # Use last timestamp in entire log as end time
    method_call.end_time = self.entries[-1].timestamp
    method_call.duration = method_call.end_time - enter_entry.timestamp
    self.method_calls.append(method_call)
```

**Other Levels:**
```python
else:
    # Log as exception
    self.exceptions_log.append({
        'description': 'Missing closing line (METHOD_EXIT)',
        'solution': 'Removed from tree, children reparented to nearest closed ancestor'
    })
    # DO NOT add to method_calls
```

### Why Remove Non-Root Unclosed?

If we kept them with estimated end times:
- **Duration would be wrong**: End time is a guess
- **Children time > Parent time**: Leads to impossible durations
- **Incorrect self-time**: Negative self-time values

By removing them, their children get reparented correctly via time containment to the next ancestor that is properly closed.

---

## Tree Construction

### Building Relationships

After parent_id assignment, we build bidirectional relationships:

```python
def _build_relationships(self):
    # Create lookup map
    call_map = {call.call_id: call for call in self.method_calls}
    
    # Build parent → children links
    for call in self.method_calls:
        if call.parent_id is not None:
            parent = call_map.get(call.parent_id)
            if parent:
                parent.children.append(call)
```

### Calculating Self-Time

Self-time = time spent in the method itself, excluding children:

```python
def calculate_self_time(self):
    children_time = sum(child.duration for child in self.children)
    self.self_time = self.duration - children_time
```

**Important:** With correct parent-child relationships:
- `self_time >= 0` always (no negative values)
- `children_time <= duration` always (no impossible durations)

---

## Example Walkthrough

### Input Log

```
08:58:28.2 (100000000)|CODE_UNIT_STARTED|[EXTERNAL]|Class.Main.execute()
08:58:28.2 (200000000)|METHOD_ENTRY|[50]|methodA()
08:58:28.2 (300000000)|METHOD_ENTRY|[30]|methodB()
08:58:28.2 (400000000)|METHOD_ENTRY|[80]|methodC()
08:58:28.2 (500000000)|METHOD_EXIT|[80]|methodC()
08:58:28.2 (600000000)|METHOD_EXIT|[30]|methodB()
08:58:28.2 (700000000)|METHOD_EXIT|[50]|methodA()
08:58:28.2 (800000000)|CODE_UNIT_FINISHED|[EXTERNAL]|Class.Main.execute()
```

### Step 1: Parse Entries

| Timestamp | Type | Level | Method |
|-----------|------|-------|--------|
| 100ms | ENTRY | 0 | Main.execute() |
| 200ms | ENTRY | 50 | methodA() |
| 300ms | ENTRY | 30 | methodB() |
| 400ms | ENTRY | 80 | methodC() |
| 500ms | EXIT | 80 | methodC() |
| 600ms | EXIT | 30 | methodB() |
| 700ms | EXIT | 50 | methodA() |
| 800ms | EXIT | 0 | Main.execute() |

### Step 2: Match Pairs & Create MethodCalls

| call_id | Method | Start | End | Duration | Level |
|---------|--------|-------|-----|----------|-------|
| 0 | Main.execute() | 100ms | 800ms | 700ms | 0 |
| 1 | methodA() | 200ms | 700ms | 500ms | 50 |
| 2 | methodB() | 300ms | 600ms | 300ms | 30 |
| 3 | methodC() | 400ms | 500ms | 100ms | 80 |

### Step 3: Sort by Start Time (already sorted)

### Step 4: Assign Parents (Time Containment)

**Processing call_id 0 (Main.execute()):**
- Level 0 → Root
- parent_id = None

**Processing call_id 1 (methodA()):**
- Start: 200ms, End: 700ms
- Search backwards from index 0
- Candidate 0 (Main.execute()): start=100 ≤ 200 ✓, 700 ≤ 800 ✓
- **parent_id = 0** ✅

**Processing call_id 2 (methodB()):**
- Start: 300ms, End: 600ms
- Search backwards from index 1
- Candidate 1 (methodA()): start=200 ≤ 300 ✓, 600 ≤ 700 ✓
- **parent_id = 1** ✅
- (Note: Candidate 0 also contains it, but we break at first match)

**Processing call_id 3 (methodC()):**
- Start: 400ms, End: 500ms
- Search backwards from index 2
- Candidate 2 (methodB()): start=300 ≤ 400 ✓, 500 ≤ 600 ✓
- **parent_id = 2** ✅

### Step 5: Final Tree

```
Main.execute() [700ms]
└─ methodA() [500ms]
   └─ methodB() [300ms]
      └─ methodC() [100ms]
```

**Self-Times:**
- Main.execute(): 700 - 500 = 200ms
- methodA(): 500 - 300 = 200ms
- methodB(): 300 - 100 = 200ms
- methodC(): 100 - 0 = 100ms

All values are positive ✅ No impossible durations ✅

---

## Edge Cases Handled

### 1. Methods with Same Name

Multiple calls to the same method are differentiated by:
- Unique `call_id`
- Different start/end times
- Level-specific stacks during matching

### 2. Recursive Methods

A method calling itself is handled correctly:
- Each invocation gets a unique `call_id`
- Time containment establishes parent-child correctly
- Inner recursion is child of outer recursion

### 3. Nested CODE_UNITs (Apex Callouts)

**Example: CpqApexCallable**
```
CPQServicePtc.processInCore [3652ms]  ← METHOD
  └─ CpqApexCallable [2065ms]          ← Nested CODE_UNIT (level 1)
     └─ CustomPricingPlanStepImpl [2059ms]  ← METHOD
```

- Nested CODE_UNITs represent Apex-to-Apex callouts or external invocations
- They have their own CODE_UNIT_STARTED/FINISHED events
- Tracked using `code_unit_depth` counter (incremented on STARTED, decremented on FINISHED)
- FINISHED events may omit `[EXTERNAL]|` prefix - regex handles both formats
- Parented correctly via time containment algorithm

**Why This Was a Bug:**
The original regex required `[EXTERNAL]|` for both STARTED and FINISHED:
```python
# WRONG: Required pipe after [EXTERNAL] or similar prefix
r'...\|CODE_UNIT_(STARTED|FINISHED)\|[^\|]*\|(.+)$'
```

This failed to match FINISHED events like:
```
08:58:31.3 (3919240262)|CODE_UNIT_FINISHED|vlocity_cmt.CpqApexCallable
                                           ^ No [EXTERNAL]| prefix!
```

**Fix:** Made the prefix and pipe optional:
```python
# CORRECT: Optional prefix+pipe
r'...\|CODE_UNIT_(STARTED|FINISHED)\|(?:[^\|]*\|)?(.+)$'
                                      ^^^^^^^^^^^
                                      Optional non-capturing group
```

### 4. Parallel Execution (Not Supported)

Apex is single-threaded, so parallel execution doesn't occur. If it did, time containment would fail (overlapping times).

### 5. Log Truncation

If the log is truncated:
- Recent EXIT events may be missing
- Level 0 root uses last available timestamp as end
- Other unclosed methods are removed and logged as exceptions

---

## Validation

The algorithm ensures:

1. ✅ **Single Root**: Only one method with `parent_id = None` (level 0 CODE_UNIT)
2. ✅ **No Orphans**: All non-root methods have valid `parent_id`
3. ✅ **No Cycles**: Time containment prevents circular relationships
4. ✅ **No Impossible Durations**: `children_time ≤ parent.duration` for all methods
5. ✅ **No Negative Self-Time**: `self_time ≥ 0` for all methods

**Verification Code:**
```python
roots = [c for c in method_calls if c.parent_id is None]
broken = sum(1 for c in method_calls 
             if sum(ch.duration for ch in c.children) > c.duration * 1.01)

print(f'Roots: {len(roots)}')  # Should be 1
print(f'Broken: {broken}')     # Should be 0
```

---

## Performance Characteristics

- **Time Complexity**: O(n²) worst case, O(n × d) typical (d = tree depth)
- **Space Complexity**: O(n) for storing all method calls
- **Typical Runtime**: ~1-2 seconds for 20,000 method calls

---

## Future Improvements

1. **Optimize Parent Search**: Use interval tree for O(n log n) parent assignment
2. **Parallel Processing**: Parse multiple log files concurrently
3. **Streaming Parser**: Handle logs larger than memory
4. **Smart Level Hints**: Use level numbers as hints to narrow search space

---

## Version History

### Version 3.1 (October 22, 2025)
**Fixed: Nested CODE_UNIT Parsing**

- **Issue:** CODE_UNIT_FINISHED events without `[EXTERNAL]|` prefix were not matched by regex
- **Impact:** Nested CODE_UNITs (e.g., `CpqApexCallable` - 2065ms Apex callouts) were missing from tree
  - This caused their children to be incorrectly parented
  - Example: `CustomPricingPlanStepImpl` (2059ms) appeared as direct child of `CPQServicePtc.processInCore` instead of child of `CpqApexCallable`
- **Root Cause:** Original regex pattern required pipe after prefix: `|[^\|]*\|`
  - STARTED format: `CODE_UNIT_STARTED|[EXTERNAL]|methodName` ✓ Matched
  - FINISHED format: `CODE_UNIT_FINISHED|methodName` ✗ Did not match (no pipe!)
- **Solution:** Made prefix+pipe optional: `|(?:[^\|]*\|)?`
- **Result:** All nested CODE_UNITs now correctly parsed and parented
  - Total methods increased from 18,437 to 18,467
  - Hierarchy now shows: `CPQServicePtc.processInCore` → `CpqApexCallable` → `CustomPricingPlanStepImpl`

### Version 3.0 (October 22, 2025)  
**Major Breakthrough: Pure Time Containment**

- **Issue:** Level numbers in Salesforce logs are inconsistent
  - Example: Method at level 72 → child at level 216 (level increased, but child is deeper!)
  - Level-based parent assignment produced: 2,008 roots, 30 broken durations
- **Solution:** Switched to pure time containment algorithm
  - Parent must START before or at child's start time
  - Parent must END after or at child's end time
  - Search backwards to find most recent (immediate) parent
- **Result:** Perfect tree structure
  - 1 root ✅
  - 0 broken durations ✅  
  - All positive self-times ✅
  - Correct nesting matching actual execution flow ✅

### Version 2.x (Earlier Iterations)
- Attempted various level-based parent assignment strategies
- All failed due to inconsistent level numbering in logs

### Version 1.0 (Initial)
- Stack-based parent assignment with level comparison
- Many broken parent-child relationships

---

## Conclusion

The key breakthroughs were:
1. **Recognizing that level numbers are unreliable** and switching to **pure time containment** for parent-child relationships
2. **Handling format variations** in CODE_UNIT events (STARTED vs FINISHED)

These simple principles, combined with careful handling of unclosed methods, produce a correct hierarchical tree even from incomplete/malformed log data.

The algorithm is robust, maintainable, and produces validated results with:
- 1 root
- 0 broken durations
- All positive self-times
- Correct method nesting matching actual execution flow
- Support for nested CODE_UNITs (Apex callouts)

---

## References

- Log Parser Implementation: `source/parser/log_parser.py` (lines 68-71 for CODE_UNIT regex)
- Method Call Model: `source/parser/method_call.py`
- Exception Log: `logExceptionRules.txt`

