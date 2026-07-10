# BnB Visualizer Project Plan

## Project Overview

**Project**: General Branch-and-Bound Visualization Framework  
**Location**: `/home/an/Repositories/alg/bnb-visualizer`  
**Timeline**: Until end of july
**Purpose**: Research tool for visualizing BnB algorithms (TSP, Knapsack, etc.)  
**Target Users**: Researchers, university hiwi work, AI continuation (Claude)

---

## Architecture Decisions

### Frontend

- **Framework**: Vue 3 + TypeScript (user wants to learn Vue)
- **Build Tool**: Vite
- **Visualization**: D3.js (user has experience from knapsack project)
- **State Management**: Pinia (optional, for complex state)
- **Styling**: Tailwind CSS or Bootstrap (user's choice)

### Backend

- **Language**: Python 3.10+
- **Package Manager**: UV (faster than pip)
- **Web Framework**: FastAPI (only for live mode, optional)
  - Native WebSocket support
  - Async/await
  - Auto-generated API docs (Swagger)
  - Pydantic for data validation
- **Pure Python**: Core BnB framework has NO FastAPI dependency

### Communication

- **Static Mode**: JSON/JSONL files only (no HTML generation from Python)
- **Live Mode**: WebSocket streaming + REST API
- **Data Formats**:
  - `bnb_tree.json`: Complete tree snapshot
  - `bnb_tree.jsonl`: Event stream (node_created, node_processed, etc.)
  - `metadata.json`: Algorithm and instance info

### Modes

1. **Static Mode** (No server required)
   - Python generates JSON/JSONL files
   - Vue app (built as static files) loads and visualizes data
   - Can be opened directly in browser
   - Portable, shareable

2. **Live Mode** (Requires FastAPI server)
   - Real-time WebSocket streaming
   - Interactive controls (pause, resume, step)
   - Best for algorithm development

---

## Technology Stack

| Layer                    | Technology                          | Purpose                    |
| ------------------------ | ----------------------------------- | -------------------------- |
| Backend Framework        | FastAPI                             | Live mode WebSocket + REST |
| Backend Core             | Pure Python                         | BnB algorithm framework    |
| Frontend Framework       | Vue 3 + TypeScript                  | User interface             |
| Frontend Build           | Vite                                | Fast development           |
| Visualization            | D3.js                               | Tree rendering             |
| Package Manager (Python) | UV                                  | Dependency management      |
| Package Manager (JS)     | npm                                 | Frontend dependencies      |
| Type Consistency         | Pydantic → JSON Schema → TypeScript | Shared types               |

---

## Project Structure

```
tsp-visualizer/
├── pyproject.toml              # UV configuration
├── uv.lock                    # UV lockfile
│
├── bnb_framework/              # Pure Python BnB framework
│   ├── __init__.py
│   ├── types.py                # Pydantic models (source of truth)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── bnb_base.py         # BnBAlgorithm abstract base class
│   │   ├── node.py            # BnBNode definition
│   │   └── progress.py         # Progress tracking
│   ├── algorithms/
│   │   ├── __init__.py
│   │   ├── tsp/
│   │   │   ├── __init__.py
│   │   │   ├── instance.py     # TSPInstance
│   │   │   └── tsp_bnb.py      # TSPBnBAlgorithm
│   │   └── knapsack/           # Knapsack implementation
│   │       └── ...
│   └── visualization/
│       ├── __init__.py
│       ├── exporters.py        # JSON/JSONL export (no HTML)
│       └── schemas/            # Generated JSON Schemas
│
├── scripts/
│   └── generate_schema.py      # Generate JSON Schema from Pydantic
│
├── server/                    # FastAPI server (live mode only)
│   └── main.py
│
├── frontend/                  # Vue frontend
│   ├── package.json
│   ├── vite.config.ts
│   ├── schemas/               # JSON Schemas (from Python)
│   └── src/
│       ├── types/
│       │   └── bnb.ts         # Generated from JSON Schema
│       ├── components/
│       │   ├── BnBTreeVisualization.vue
│       │   ├── NodeDetailsPanel.vue
│       │   └── ProgressControls.vue
│       ├── composables/
│       │   ├── useBnBData.ts    # Auto-detects static/live mode
│       │   ├── useD3Tree.ts    # D3 integration
│       │   └── useWebSocket.ts # WebSocket connection
│       ├── views/
│       │   ├── HomeView.vue
│       │   ├── LiveViewer.vue
│       │   └── StaticViewer.vue
│       ├── App.vue
│       └── main.ts
│
├── examples/
│   ├── tsp_instance.json
│   ├── knapsack_instance.json
│   └── run_static.py          # Generate static files
│
├── output/                   # Generated output (gitignored)
│   ├── app/                   # Vue static files
│   ├── bnb_tree.json
│   ├── bnb_tree.jsonl
│   └── metadata.json
│
├── PLAN.md                   # This file
├── ARCHITECTURE.md            # Detailed architecture
└── README.md
```

---

## Implementation Roadmap (4 Weeks)

### Week 1: Foundation

**Goal**: Core BnB framework + basic visualization

| Day | Task               | Details                                      | Status |
| --- | ------------------ | -------------------------------------------- | ------ |
| 1   | Project setup      | Git repo, UV, Python env, Vue project        | ⬜     |
| 1   | Define types       | Pydantic models in `bnb_framework/types.py`  | ⬜     |
| 2   | BnB base classes   | `BnBAlgorithm`, `BnBNode`, `ProgressTracker` | ⬜     |
| 2   | TSP implementation | Basic TSP BnB algorithm                      | ⬜     |
| 3   | JSON exporter      | `BnBExporter.to_json()` and `to_jsonl()`     | ⬜     |
| 4   | Vue setup          | Vite + TypeScript + D3                       | ⬜     |
| 5   | D3 tree component  | Basic tree visualization                     | ⬜     |
| 6   | Static viewer      | Load JSON, display tree                      | ⬜     |
| 7   | Test & debug       | Try with TSP instance                        | ⬜     |

**Deliverable**: Can generate static JSON from TSP BnB and view it in browser

---

### Week 2: Static Mode Polish

**Goal**: Complete static mode with analysis features

| Day | Task                | Details                              | Status |
| --- | ------------------- | ------------------------------------ | ------ |
| 8   | JSONL viewer        | Load and reconstruct tree from JSONL | ⬜     |
| 9   | Node details panel  | Click node → show details            | ⬜     |
| 10  | Progress controls   | Slider to step through iterations    | ⬜     |
| 11  | Zoom/pan            | D3 zoom behavior                     | ⬜     |
| 12  | Multiple algorithms | Add knapsack example                 | ⬜     |
| 13  | Instance config     | UI to configure instances            | ⬜     |
| 14  | Export options      | Save tree as PNG, PDF, CSV           | ⬜     |

**Deliverable**: Full static mode with analysis tools

---

### Week 3: Live Mode

**Goal**: Real-time WebSocket streaming

| Day | Task                 | Details                         | Status |
| --- | -------------------- | ------------------------------- | ------ |
| 15  | FastAPI setup        | WebSocket endpoint              | ⬜     |
| 15  | WebSocket composable | Vue WebSocket integration       | ⬜     |
| 16  | Live tree updates    | Stream nodes as they're created | ⬜     |
| 17  | Live metrics         | Update metrics in real-time     | ⬜     |
| 18  | Live controls        | Pause, resume, step             | ⬜     |
| 19  | Algorithm selection  | UI to choose algorithm          | ⬜     |
| 20  | Error handling       | WebSocket errors, reconnection  | ⬜     |
| 21  | Test live mode       | End-to-end test                 | ⬜     |

**Deliverable**: Real-time visualization with WebSocket

---

### Week 4: Polish & Research Features

**Goal**: Research-ready tool

| Day | Task                | Details                    | Status |
| --- | ------------------- | -------------------------- | ------ |
| 22  | Plugin system       | Easy to add new algorithms | ⬜     |
| 22  | Documentation       | How to implement new BnB   | ⬜     |
| 23  | Solution comparison | Compare multiple runs      | ⬜     |
| 24  | Bottleneck analysis | Identify slow nodes        | ⬜     |
| 25  | Performance metrics | Time per node, etc.        | ⬜     |
| 26  | Export reports      | Generate analysis reports  | ⬜     |
| 27  | Final testing       | All features working       | ⬜     |
| 28  | Cleanup & docs      | README, examples           | ⬜     |

**Deliverable**: Complete research tool

---

## Key Design Decisions

### 1. No Jinja Templates

- **Problem**: Previous alglab project used Jinja, user found it "scuffed"
- **Solution**: Vue handles all frontend rendering
- **Benefit**: Single codebase, no template duplication, AI-friendly

### 2. Vue for Both Static and Live Modes

- **How**: Same Vue app detects mode automatically
  - Tries WebSocket first (live mode)
  - Falls back to loading JSON/JSONL files (static mode)
- **Benefit**: Single codebase, maximum reusability

### 3. Type Consistency: Pydantic → TypeScript

- **Source of Truth**: Python Pydantic models
- **Workflow**:
  1. Define Pydantic models in `bnb_framework/types.py`
  2. Generate JSON Schema: `python scripts/generate_schema.py`
  3. Generate TypeScript: `npx json-schema-to-typescript schemas/bnb.json -o frontend/src/types/bnb.ts`
- **Benefit**: Automatic type consistency, reduces bugs

### 4. UV for Python Package Management

- **Why**: Faster than pip, better dependency resolution
- **Commands**:
  - Install: `uv pip install`
  - Run: `uv run python script.py`
  - Add dependency: `uv pip add package`

### 5. FastAPI Only for Live Mode

- **Core framework**: Pure Python, no FastAPI dependency
- **Live mode**: FastAPI adds WebSocket + REST
- **Benefit**: Researchers can use core framework without web dependencies

---

## Data Formats

### JSON (Complete Tree Snapshot)

```json
{
  "tree": {
    "node_id": 0,
    "parent_id": null,
    "depth": 0,
    "lower_bound": 0.0,
    "upper_bound": 100.0,
    "status": "active",
    "branching_decision": null,
    "created_at": 1234567890.0,
    "processed_at": null,
    "children": [...]
  },
  "solutions": [...],
  "metrics": {
    "nodes_created": 100,
    "nodes_processed": 80,
    "nodes_pruned": 20,
    "start_time": 1234567890.0
  },
  "metadata": {
    "algorithm": "tsp_bnb",
    "instance_id": "berlin52",
    "timestamp": "2026-07-10T12:00:00Z"
  }
}
```

### JSONL (Event Stream)

```jsonl
{"type": "metadata", "algorithm": "tsp_bnb", "timestamp": 1234567890.0}
{"type": "node_created", "node": {...}, "timestamp": 1234567890.1}
{"type": "node_processed", "node_id": 1, "bounds": {"lower": 0, "upper": 50}, "timestamp": 1234567890.2}
{"type": "solution_found", "solution": {...}, "timestamp": 1234567890.5}
{"type": "search_completed", "metrics": {...}, "timestamp": 1234567891.0}
```

---

## Research Workflow

### For Researchers

1. **Implement Algorithm**

   ```python
   # my_bnb.py
   from bnb_framework.core.bnb_base import BnBAlgorithm
   from bnb_framework.types import BnBNode

   class MyBnB(BnBAlgorithm):
       def relax(self, node: BnBNode) -> tuple[float, float]:
           # Your relaxation
           return lb, ub

       def branch(self, node: BnBNode) -> list[BnBNode]:
           # Your branching
           return children

       # ... other methods
   ```

2. **Run Static Mode**

   ```bash
   python examples/run_static.py --algorithm my_bnb.MyBnB --instance my_instance.json
   ```

   Output: `output/` directory with JSON/JSONL + Vue static files

3. **View Results**

   ```bash
   open output/app/index.html
   ```

4. **Run Live Mode**

   ```bash
   # Terminal 1: Start FastAPI
   uv run uvicorn server.main:app --reload

   # Terminal 2: Start Vue dev server
   cd frontend && npm run dev

   # Open http://localhost:5173/live
   ```

---

## AI Continuation (Claude)

### AI-Friendly Design Choices

| Choice           | Why AI-Friendly                     |
| ---------------- | ----------------------------------- |
| Vue + TypeScript | Most popular, best documentation    |
| FastAPI          | Modern, clear structure             |
| Pydantic         | Explicit types, auto-docs           |
| Vite             | Simple build tool                   |
| D3.js            | Well-documented visualization       |
| JSON Schema      | Standard format, easy to understand |

### Tips for Claude

1. **TypeScript**: Always use types, prefer Composition API
2. **Python**: Use Pydantic models, type hints
3. **Documentation**: Add docstrings, comments
4. **Structure**: Keep components focused, single responsibility
5. **Testing**: Include example instances for validation

---

## Dependencies

### Python (pyproject.toml)

```toml
[project]
name = "bnb-visualizer"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-jsonschema>=1.0.0",
    "websockets>=12.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "black>=24.0.0",
    "ruff>=0.1.0",
]
```

### JavaScript (frontend/package.json)

```json
{
  "name": "bnb-visualizer-frontend",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "generate-types": "json-schema-to-typescript ../schemas/bnb.json -o src/types/bnb.ts"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "d3": "^7.9.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0",
    "json-schema-to-typescript": "^13.0.0"
  }
}
```

---

## File Templates

### Python BnB Algorithm Template

```python
# bnb_framework/algorithms/custom/template.py
from typing import Optional
from bnb_framework.core.bnb_base import BnBAlgorithm
from bnb_framework.types import BnBNode
from pydantic import BaseModel

class MyInstance(BaseModel):
    """Your problem instance type."""
    # Define your instance fields
    pass

class MySolution(BaseModel):
    """Your solution type."""
    # Define your solution fields
    pass

class MyBnB(BnBAlgorithm[MyInstance, MySolution]):
    """Your Branch and Bound implementation."""

    def relax(self, node: BnBNode) -> tuple[float, float]:
        """Calculate lower and upper bounds."""
        # Your relaxation logic
        lb = 0.0
        ub = 100.0
        return lb, ub

    def branch(self, node: BnBNode) -> list[BnBNode]:
        """Generate child nodes."""
        # Your branching logic
        children = []
        return children

    def is_solution(self, node: BnBNode) -> bool:
        """Check if node is a complete solution."""
        # Your logic
        return False

    def get_solution_value(self, node: BnBNode) -> float:
        """Get objective value for a solution node."""
        return node.upper_bound or 0.0

    def _solution_to_dict(self, solution: MySolution) -> dict:
        return solution.model_dump()

    def _instance_to_dict(self, instance: MyInstance) -> dict:
        return instance.model_dump()
```

### Vue Component Template

```vue
<!-- frontend/src/components/MyComponent.vue -->
<template>
  <div class="my-component">
    <!-- Your template -->
  </div>
</template>

<script setup lang="ts">
// Import types
import type { BnBNode } from "@/types/bnb";

// Define props
const props = defineProps<{
  data: BnBNode;
}>();

// Define emits
const emit = defineEmits<{
  (e: "node-clicked", node: BnBNode): void;
}>();

// Reactive state
const count = ref(0);

// Methods
const handleClick = () => {
  emit("node-clicked", props.data);
};

// Lifecycle
onMounted(() => {
  // Initialization
});
</script>

<style scoped>
/* Your styles */
</style>
```

---

## Success Criteria

- [ ] Researchers can implement new BnB algorithms with minimal code
- [ ] Visualization works for any BnB algorithm (TSP, Knapsack, etc.)
- [ ] Both static and live modes work correctly
- [ ] Type consistency between Python and TypeScript
- [ ] AI (Claude) can understand and extend the codebase
- [ ] Good performance with large trees (10,000+ nodes)
- [ ] Clear documentation for researchers

---

## Open Questions

1. **Instance format**: Should we standardize instance JSON format across algorithms?
2. **Visualization options**: Should we support multiple visualization styles (tree, graph, etc.)?
3. **Export formats**: Which export formats are most useful for researchers?
4. **Performance**: What's the maximum tree size we need to support?

---

_Last updated: 2026-07-10_
_Project: BnB Visualizer_
