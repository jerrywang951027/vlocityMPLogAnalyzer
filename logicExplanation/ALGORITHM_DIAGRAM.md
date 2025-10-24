# Visual Algorithm Diagrams

## 1. Overall Parsing Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                     Raw Log File                            │
│  08:58:28.2 (138268661)|METHOD_ENTRY|[117]|methodA()       │
│  08:58:28.2 (151784274)|METHOD_ENTRY|[36]|methodB()        │
│  08:58:34.42 (6702786940)|METHOD_EXIT|[36]|methodB()       │
│  08:58:34.42 (6702786940)|METHOD_EXIT|[117]|methodA()      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────┐
         │   Phase 1: Parse Log Entries         │
         │   - Extract timestamp (nanoseconds)  │
         │   - Extract event type (ENTRY/EXIT)  │
         │   - Extract level number             │
         │   - Clean method name                │
         └──────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              LogEntry Objects (in order)                    │
│  [LogEntry(ts=138ms, type=ENTRY, level=117, name=methodA)] │
│  [LogEntry(ts=151ms, type=ENTRY, level=36, name=methodB)]  │
│  [LogEntry(ts=6702ms, type=EXIT, level=36, name=methodB)]  │
│  [LogEntry(ts=6702ms, type=EXIT, level=117, name=methodA)] │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────┐
         │  Phase 2: Match ENTRY/EXIT Pairs     │
         │  - Use level-specific stacks         │
         │  - Match by level + method name      │
         │  - Calculate duration                │
         └──────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              MethodCall Objects (unsorted)                  │
│  [MethodCall(id=0, methodA, start=138, end=6702)]          │
│  [MethodCall(id=1, methodB, start=151, end=6702)]          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────┐
         │  Phase 3: Handle Unclosed Methods    │
         │  - Keep level-0 CODE_UNITs as roots │
         │  - Remove other unclosed methods     │
         │  - Log exceptions                    │
         └──────────────────────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────┐
         │  Phase 4: Assign Parents             │
         │  - Sort by start time                │
         │  - Use pure time containment         │
         │  - Ignore level numbers              │
         └──────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              MethodCall Objects (with parent_id)            │
│  [MethodCall(id=0, methodA, parent_id=None)]               │
│  [MethodCall(id=1, methodB, parent_id=0)]                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────┐
         │  Phase 5: Build Tree Structure       │
         │  - Create parent → children links    │
         │  - Calculate self-time               │
         └──────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Method Call Tree                          │
│                                                             │
│         methodA [6564ms]                                    │
│            └─ methodB [6551ms]                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Time Containment Algorithm

### Concept: Full Time Containment

```
Timeline:  0ms ─────────────────────────────────────────► 1000ms

Parent:    [════════════════════════════════]  (200ms - 900ms)
              │                              │
              ├──► Child1: [════]  (300ms - 400ms) ✓ Fully contained
              │
              ├──► Child2: [═══════]  (500ms - 700ms) ✓ Fully contained
              │
              └──► Invalid: [════════════] (600ms - 1200ms) ✗ Extends beyond parent
```

### Parent Search Algorithm

For each method, search **backwards** through earlier methods:

```
Sorted by start time:
┌──────────────────────────────────────────────────────────┐
│  Index:  0      1      2      3      4      (current)    │
│          │      │      │      │      │          │        │
│  Time:   100ms  200ms  300ms  400ms  500ms    600ms      │
│  Method: A      B      C      D      E          F        │
│          │      │      │      │      │          │        │
│  Range:  [═══════════════════════════════════════]       │
│                 [════════════════════════]               │
│                        [═══════════════]                 │
│                               [════════]                 │
│                                      [═══]               │
│                                            [══] ← Process F
└──────────────────────────────────────────────────────────┘

Processing method F (start=600ms, end=800ms):
  ◄─── Search backwards

  Check E: Does E contain F?
    E.start (500) ≤ F.start (600)? ✓
    F.end (800) ≤ E.end (850)? ✓
    → E is parent! Stop searching.
```

---

## 3. Why Level Numbers Are Unreliable

### Example from Real Log

```
Time →

100ms  |─────────────────────────────────────────────────────────────| [117] methodA
       |                                                               |
150ms    |─────────────────────────────────────────────────────────|   [36] methodB
         |                                                           |
200ms      |─────────────────────────────────────────────────|         [72] methodC
           |                                                   |
300ms        |───────────────────────────────────────|                 [216] methodD
             |                                       |
             |              ▲                        |
             |              │                        |
             |         Level goes UP!                |
             |         (72 → 216)                    |
             |         But it's deeper!              |
             |                                       |
800ms        |───────────────────────────────────────| EXIT [216] ◄── Exits FIRST (deepest!)
           |                                                   |
900ms      |─────────────────────────────────────────────────| EXIT [72]
         |                                                           |
950ms    |─────────────────────────────────────────────────────────| EXIT [36]
       |                                                               |
1000ms |─────────────────────────────────────────────────────────────| EXIT [117] ◄── Exits LAST (outermost!)
```

**Conclusion:** 
- Level 72 → 216: level increases, but 216 is a child (exits first)
- **Level numbers are NOT depth indicators!**
- **Solution: Use time containment instead**

---

## 4. Level-Specific Stacks for Matching

### Problem: Multiple Methods with Same Name

```
Log:
  METHOD_ENTRY [50] methodA
  METHOD_ENTRY [50] methodA  ← Same level, same name!
  METHOD_EXIT [50] methodA   ← Which ENTRY does this match?
```

### Solution: Stack Per Level

```
┌─────────────────────────────────────────────────────────┐
│  level_stacks = {                                       │
│    50: [stack for level 50],                            │
│    36: [stack for level 36],                            │
│    ...                                                  │
│  }                                                      │
└─────────────────────────────────────────────────────────┘

Event: METHOD_ENTRY [50] methodA
  level_stacks[50].push(methodA_entry_1)
  
Event: METHOD_ENTRY [50] methodA
  level_stacks[50].push(methodA_entry_2)
  
  Stack now: [methodA_entry_1, methodA_entry_2]  ← Most recent on top
  
Event: METHOD_EXIT [50] methodA
  entry = level_stacks[50].pop()  ← Gets methodA_entry_2 (LIFO)
  Match with methodA_entry_2 ✓
```

---

## 5. Handling Unclosed Methods

### Scenario: Constructor Without EXIT

```
Log:
  CODE_UNIT_STARTED [0] Main.execute()
  METHOD_ENTRY [1] Constructor()         ← Missing EXIT!
  METHOD_ENTRY [2] someMethod()
  METHOD_EXIT [2] someMethod()
  CODE_UNIT_FINISHED [0] Main.execute()
```

### Strategy by Level

```
┌─────────────────────────────────────────────────────────┐
│  Level 0 (CODE_UNIT): KEEP AS ROOT                      │
│                                                          │
│  Main.execute() [UNCLOSED]                              │
│    ├─ Duration: last_timestamp - start_time            │
│    └─ Acts as root for entire tree                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Other Levels: REMOVE, LOG EXCEPTION                     │
│                                                          │
│  Constructor() [UNCLOSED]                               │
│    ├─ Removed from tree                                │
│    ├─ Logged in logExceptionRules.txt                  │
│    └─ Children reparented via time containment         │
│                                                          │
│  someMethod()                                           │
│    └─ Will be reparented to Main.execute()             │
│       (nearest closed ancestor containing it)           │
└─────────────────────────────────────────────────────────┘
```

---

## 6. Parent Assignment Example

### Input Methods (after matching)

```
| ID | Method    | Start | End  | Duration | Level |
|----|-----------|-------|------|----------|-------|
| 0  | Root      | 0     | 1000 | 1000     | 0     |
| 1  | MethodA   | 100   | 900  | 800      | 50    |
| 2  | MethodB   | 200   | 400  | 200      | 30    |
| 3  | MethodC   | 500   | 700  | 200      | 80    |
```

### Step-by-Step Assignment

```
Step 1: Process ID=0 (Root)
  ┌─────────────────────────────────────┐
  │ ID=0: Root [0-1000ms] level=0       │
  │ Decision: Level 0 → parent_id=None  │
  └─────────────────────────────────────┘

Step 2: Process ID=1 (MethodA)
  ┌─────────────────────────────────────────────────────┐
  │ ID=1: MethodA [100-900ms] level=50                  │
  │ Search backwards:                                   │
  │   ◄── Check ID=0 (Root):                            │
  │       Root.start (0) ≤ MethodA.start (100)? ✓       │
  │       MethodA.end (900) ≤ Root.end (1000)? ✓        │
  │       → Parent found!                               │
  │ Decision: parent_id=0                               │
  └─────────────────────────────────────────────────────┘

Step 3: Process ID=2 (MethodB)
  ┌─────────────────────────────────────────────────────┐
  │ ID=2: MethodB [200-400ms] level=30                  │
  │ Search backwards:                                   │
  │   ◄── Check ID=1 (MethodA):                         │
  │       MethodA.start (100) ≤ MethodB.start (200)? ✓  │
  │       MethodB.end (400) ≤ MethodA.end (900)? ✓      │
  │       → Parent found! (break immediately)           │
  │ Decision: parent_id=1                               │
  └─────────────────────────────────────────────────────┘
  
  Note: Root also contains MethodB, but we break at first match
        (MethodA is more recent, so it's the immediate parent)

Step 4: Process ID=3 (MethodC)
  ┌─────────────────────────────────────────────────────┐
  │ ID=3: MethodC [500-700ms] level=80                  │
  │ Search backwards:                                   │
  │   ◄── Check ID=2 (MethodB):                         │
  │       MethodB.start (200) ≤ MethodC.start (500)? ✓  │
  │       MethodC.end (700) ≤ MethodB.end (400)? ✗      │
  │       → Not contained, continue search              │
  │   ◄── Check ID=1 (MethodA):                         │
  │       MethodA.start (100) ≤ MethodC.start (500)? ✓  │
  │       MethodC.end (700) ≤ MethodA.end (900)? ✓      │
  │       → Parent found!                               │
  │ Decision: parent_id=1                               │
  └─────────────────────────────────────────────────────┘
```

### Resulting Tree

```
Root [1000ms]
└─ MethodA [800ms]
   ├─ MethodB [200ms]
   └─ MethodC [200ms]
```

---

## 7. Self-Time Calculation

```
Method: MethodA [800ms total]
  └─ MethodB [200ms]
  └─ MethodC [200ms]

Calculation:
  children_time = MethodB.duration + MethodC.duration
                = 200 + 200
                = 400ms
  
  self_time = MethodA.duration - children_time
            = 800 - 400
            = 400ms

Interpretation:
  ┌─────────────────────────────────────────────┐
  │ MethodA [800ms total]                       │
  │  ┌─────────┐                                │
  │  │MethodB  │ [200ms]                        │
  │  └─────────┘                                │
  │  ┌─────────┐                                │
  │  │MethodC  │ [200ms]                        │
  │  └─────────┘                                │
  │  ╔═══════════════════════════╗              │
  │  ║ MethodA self-time         ║ [400ms]     │
  │  ╚═══════════════════════════╝              │
  └─────────────────────────────────────────────┘
  
  Self-time = time MethodA spent NOT calling children
            = time executing its own code
```

---

## 8. Validation Checks

### Check 1: Single Root

```
✓ PASS: roots = [CODE_UNIT with parent_id=None]
✗ FAIL: roots = [method1, method2, ...]
         → Indicates missing parent assignments
```

### Check 2: No Impossible Durations

```
For each method:
  children_time = sum(child.duration for child in children)
  
  ✓ PASS: children_time ≤ method.duration * 1.01  (allow 1% rounding)
  ✗ FAIL: children_time > method.duration
          → Parent-child relationship is wrong!
```

### Check 3: No Negative Self-Time

```
For each method:
  self_time = duration - sum(child.duration)
  
  ✓ PASS: self_time ≥ 0
  ✗ FAIL: self_time < 0
          → Children took more time than parent (impossible!)
```

---

## 9. Complexity Analysis

```
Input: n = number of method calls

Phase 1: Parse Log Entries
  ┌────────────────────────────────────┐
  │ For each line in log:              │
  │   Parse with regex: O(1)           │
  │ Total: O(n)                        │
  └────────────────────────────────────┘

Phase 2: Match ENTRY/EXIT
  ┌────────────────────────────────────┐
  │ For each entry: O(n)               │
  │   Push/pop from stack: O(1)       │
  │ Total: O(n)                        │
  └────────────────────────────────────┘

Phase 3: Handle Unclosed
  ┌────────────────────────────────────┐
  │ Iterate remaining stacks: O(n)     │
  │ Total: O(n)                        │
  └────────────────────────────────────┘

Phase 4: Assign Parents
  ┌────────────────────────────────────┐
  │ Sort by start time: O(n log n)     │
  │ For each method: O(n)              │
  │   Search backwards: O(n) worst     │
  │                     O(d) typical   │
  │   (d = tree depth)                 │
  │ Total: O(n²) worst case            │
  │        O(n × d) typical case       │
  └────────────────────────────────────┘

Phase 5: Build Tree
  ┌────────────────────────────────────┐
  │ For each method:                   │
  │   Add to parent's children: O(1)  │
  │ Total: O(n)                        │
  └────────────────────────────────────┘

Overall: O(n²) worst case, O(n × d) typical
         For d ≈ 10-50, much better than O(n²)
```

---

## Summary

The algorithm successfully constructs a method call tree from Salesforce Apex logs by:

1. ✅ Parsing log entries and matching ENTRY/EXIT pairs
2. ✅ Ignoring unreliable level numbers
3. ✅ Using pure time containment for parent-child relationships
4. ✅ Handling unclosed methods gracefully
5. ✅ Validating the resulting tree structure

**Result:** A correct, validated call tree with no impossible durations or negative self-times.

