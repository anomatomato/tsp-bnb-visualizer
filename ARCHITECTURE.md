# BnB Visualizer Architecture

## Overview

This document details the technical architecture of the BnB Visualizer project.

---

## Core Principles

1. **Separation of Concerns**: Backend (Python) handles computation, Frontend (Vue) handles visualization
2. **Reusability**: Framework works with ANY BnB algorithm (TSP, Knapsack, etc.)
3. **AI-Friendly**: All technologies chosen for Claude AI compatibility
4. **No Jinja**: Pure Vue frontend, no template mixing
5. **Type Safety**: Consistent types between Python and TypeScript

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              RESEARCHER                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Vue + D3)                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  Single Vue app handles BOTH modes:                                   │ │
│  │                                                                      │ │
│  │  ┌─────────────┐      ┌─────────────┐      ┌─────────────────────┐  │ │
│  │  │  Static     │      │   Live      │      │   Analysis Tools     │  │ │
│  │  │  Mode       │      │   Mode      │      │   (common to both)   │  │ │
│  │  └─────────────┘      └─────────────┘      └─────────────────────┘  │ │
│  │        │                   │                     │                │ │
│  │        ▼                   ▼                     ▼                │ │
│  │  ┌─────────────────────────────────────────────────────────────┐  │ │
│  │  │                    D3.js Visualization                        │  │ │
│  │  │                    (same code for both modes)                 │  │ │
│  │  └─────────────────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────────────┘
               │                              │
               ▼                              ▼
┌─────────────────────────┐      ┌────────────────────────────────┐
│   Static Files           │      │      FastAPI Server               │
│   (JSON/JSONL only)       │      │      (WebSocket + REST)           │
│                          │      │                                    │
│  - bnb_tree.json         │      │  - /ws/{run_id} (WebSocket)       │
│  - bnb_tree.jsonl        │      │  - /api/run (start algorithm)     │
│  - metadata.json         │      │  - /api/status (check status)     │
└─────────────────────────┘      └────────────────────────────────┘
               │                              │
               ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         BACKEND (Pure Python)                                │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  BnB Framework (NO FastAPI dependency)                                │ │
│  │                                                                      │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │ │
│  │  │  Core       │  │ Algorithms  │  │   Visualization Exporters     │  │ │
│  │  │  Classes    │  │ (TSP, etc.) │  │   (JSON/JSONL only)          │  │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Generic Architecture

bnb-visualizer/
├── pyproject.toml # ✅ UV configuration
├── uv.lock # ✅ UV lockfile
│
├── bnb_framework/
│ ├── **init**.py
│ ├── core/
│ │ ├── bnb_base.py
│ │ └── node.py
│ ├── types.py # ✅ Pydantic models (source of truth)
│ ├── algorithms/
│ │ └── tsp/
│ └── visualization/
│ ├── exporters.py # ✅ JSON/JSONL only (no HTML)
│ └── schemas/ # ✅ Generated JSON Schemas
│
├── scripts/
│ └── generate_schema.py # ✅ Generate JSON Schema from Pydantic
│
├── server/
│ └── main.py # FastAPI (live mode only)
│
├── frontend/
│ ├── package.json
│ ├── schemas/ # ✅ JSON Schemas (from Python)
│ ├── src/
│ │ ├── types/
│ │ │ └── bnb.ts # ✅ Generated from JSON Schema
│ │ ├── components/
│ │ │ └── BnBTreeVisualization.vue
│ │ ├── composables/
│ │ │ └── useBnBData.ts # ✅ Auto-detects static/live mode
│ │ └── App.vue
│ └── dist/ # ✅ Built static files
│
├── examples/
│ ├── tsp_instance.json
│ └── run_static.py # ✅ Generates JSON/JSONL + copies Vue dist
│
└── output/ # Generated output
├── app/ # Vue static files
├── bnb_tree.json # Data only
└── bnb_tree.jsonl # Data only

## Component Details

### 1. Backend: Pure Python BnB Framework

**Location**: `bnb_framework/`

#### Core Classes

```python
# bnb_framework/core/bnb_base.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from pydantic import BaseModel

T_Instance = TypeVar('T_Instance')
T_Solution = TypeVar('T_Solution')

class BnBAlgorithm(ABC, Generic[T_Instance, T_Solution]):
    """Abstract base class for all BnB algorithms."""

    def __init__(self, instance: T_Instance):
        self.instance = instance
        self.root: Optional[BnBNode] = None
        self.nodes: dict[int, BnBNode] = {}
        self.solutions: list[T_Solution] = []
        self.metrics: dict = {...}

    @abstractmethod
    def relax(self, node: BnBNode) -> tuple[float, float]:
        """Calculate lower and upper bounds."""
        pass

    @abstractmethod
    def branch(self, node: BnBNode) -> list[BnBNode]:
        """Generate child nodes."""
        pass

    @abstractmethod
    def is_solution(self, node: BnBNode) -> bool:
        """Check if node is a complete solution."""
        pass

    @abstractmethod
    def get_solution_value(self, node: BnBNode) -> float:
        """Get objective value."""
        pass

    def search(self) -> T_Solution:
        """Main BnB search algorithm."""
        # Standard BnB loop
        pass
```

#### Node Representation

```python
# bnb_framework/core/node.py
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class NodeStatus(str, Enum):
    ACTIVE = "active"
    PRUNED = "pruned"
    SOLVED = "solved"
    EXPANDED = "expanded"

class BnBNode(BaseModel):
    """Universal BnB node - works for any problem type."""
    node_id: int = Field(..., description="Unique node identifier")
    parent_id: Optional[int] = Field(None, description="Parent node ID")
    depth: int = Field(0, description="Depth in tree")
    lower_bound: Optional[float] = Field(None, description="Lower bound")
    upper_bound: Optional[float] = Field(None, description="Upper bound")
    status: NodeStatus = Field(NodeStatus.ACTIVE)
    branching_decision: Optional[dict] = Field(None)
    created_at: float = Field(default_factory=lambda: time.time())
    processed_at: Optional[float] = Field(None)
    children: list['BnBNode'] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
```

#### Algorithm Implementations

```
bnb_framework/algorithms/
├── __init__.py
├── tsp/
│   ├── __init__.py
│   ├── instance.py      # TSPInstance (Pydantic model)
│   ├── solution.py      # TSPSolution (Pydantic model)
│   └── tsp_bnb.py       # TSPBnBAlgorithm
├── knapsack/
│   ├── __init__.py
│   ├── instance.py
│   ├── solution.py
│   └── knapsack_bnb.py
└── custom/
    └── template.py      # Template for new algorithms
```

#### Visualization Exporters

```python
# bnb_framework/visualization/exporters.py
import json
from pathlib import Path
from ..core.bnb_base import BnBAlgorithm

class BnBExporter:
    """Export BnB state to JSON/JSONL formats."""

    @staticmethod
    def to_json(bnb: BnBAlgorithm, path: str | Path) -> None:
        """Export complete state as JSON."""
        data = bnb.to_dict()
        Path(path).write_text(json.dumps(data, indent=2))

    @staticmethod
    def to_jsonl(bnb: BnBAlgorithm, path: str | Path) -> None:
        """Export event stream as JSONL."""
        events = BnBExporter._generate_events(bnb)
        with open(path, 'w') as f:
            for event in events:
                f.write(json.dumps(event) + '\n')

    @staticmethod
    def _generate_events(bnb: BnBAlgorithm) -> list[dict]:
        """Generate event stream from BnB state."""
        events = []
        # ... generate events
        return events
```

---

### 2. Backend: FastAPI Server (Live Mode Only)

**Location**: `server/`

#### Main Server

```python
# server/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from bnb_framework.core.bnb_base import BnBAlgorithm
from bnb_framework.visualization.exporters import BnBExporter
import importlib
import asyncio

app = FastAPI(title="BnB Visualization Server")

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active connections
active_connections: dict[str, WebSocket] = {}

@app.websocket("/ws/{run_id}")
async def websocket_endpoint(websocket: WebSocket, run_id: str):
    """WebSocket for streaming BnB progress."""
    await websocket.accept()
    active_connections[run_id] = websocket

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        del active_connections[run_id]

@app.post("/api/run")
async def run_algorithm(algorithm: str, instance: dict, parameters: dict = None):
    """Start a BnB algorithm run."""
    run_id = f"run_{len(active_connections) + 1}"

    # Import and instantiate algorithm
    module_path, class_name = algorithm.rsplit(".", 1)
    module = importlib.import_module(module_path)
    AlgorithmClass = getattr(module, class_name)

    # Create instance and algorithm
    instance_obj = AlgorithmClass.Instance(**instance)
    bnb = AlgorithmClass(instance_obj)

    # Run in background
    asyncio.create_task(_run_and_stream(bnb, run_id))

    return {"run_id": run_id, "status": "started"}

# Serve static files
app.mount("/static", StaticFiles(directory="output/app"), name="static")
```

---

### 3. Frontend: Vue + D3

**Location**: `frontend/`

#### Project Structure

```
frontend/
├── package.json
├── vite.config.ts
├── schemas/                    # JSON Schemas from Python
│   └── bnb.json
├── src/
│   ├── types/
│   │   └── bnb.ts             # Generated from JSON Schema
│   ├── components/
│   │   ├── BnBTreeVisualization.vue
│   │   ├── NodeDetailsPanel.vue
│   │   ├── ProgressControls.vue
│   │   └── AlgorithmSelector.vue
│   ├── composables/
│   │   ├── useBnBData.ts       # Auto-detects static/live mode
│   │   ├── useD3Tree.ts       # D3 integration
│   │   └── useWebSocket.ts    # WebSocket connection
│   ├── views/
│   │   ├── HomeView.vue
│   │   ├── LiveViewer.vue
│   │   └── StaticViewer.vue
│   ├── App.vue
│   └── main.ts
└── dist/                      # Built static files
```

#### Key Composables

```typescript
// frontend/src/composables/useBnBData.ts
import { ref, onMounted } from "vue";
import type { BnBNode, BnBEvent } from "@/types/bnb";

export function useBnBData() {
  const treeData = ref<BnBNode | null>(null);
  const events = ref<BnBEvent[]>([]);
  const isLiveMode = ref(false);
  const error = ref<string | null>(null);

  // Try WebSocket first (live mode)
  const tryWebSocket = async () => {
    try {
      const ws = new WebSocket("ws://localhost:8000/ws/run_1");
      ws.onopen = () => {
        isLiveMode.value = true;
      };
      ws.onerror = () => loadStaticData();
      // ... setup handlers
    } catch {
      loadStaticData();
    }
  };

  // Load static JSON/JSONL files
  const loadStaticData = async () => {
    try {
      const jsonResponse = await fetch("bnb_tree.json");
      if (jsonResponse.ok) {
        const data = await jsonResponse.json();
        treeData.value = data.tree;
        return;
      }

      const jsonlResponse = await fetch("bnb_tree.jsonl");
      if (jsonlResponse.ok) {
        const text = await jsonlResponse.text();
        events.value = text
          .split("\n")
          .filter((l) => l.trim())
          .map((l) => JSON.parse(l));
        treeData.value = reconstructTreeFromEvents(events.value);
      }
    } catch (e) {
      error.value = `Failed to load data: ${e}`;
    }
  };

  onMounted(tryWebSocket);

  return { treeData, events, isLiveMode, error };
}
```

```typescript
// frontend/src/composables/useD3Tree.ts
import { ref, watch, onMounted, onUnmounted } from "vue";
import * as d3 from "d3";
import type { BnBNode } from "@/types/bnb";

export function useD3Tree(container: Ref<HTMLElement | null>, treeData: Ref<BnBNode | null>) {
  const svg = ref<SVGSVGElement | null>(null);
  const selectedNode = ref<BnBNode | null>(null);

  const nodeColors = {
    active: "#007bff",
    pruned: "#dc3545",
    solved: "#20c997",
    expanded: "#6c757d",
  };

  const renderTree = () => {
    if (!container.value || !treeData.value) return;

    const width = container.value.clientWidth;
    const height = container.value.clientHeight;

    // Clear previous
    d3.select(container.value).selectAll("*").remove();

    // Create SVG and tree layout
    const svgElement = d3
      .select(container.value)
      .append("svg")
      .attr("width", width)
      .attr("height", height)
      .node() as SVGSVGElement;

    svg.value = svgElement;

    const root = d3.hierarchy(treeData.value);
    const treeLayout = d3.tree<BnBNode>().size([width, height]);
    treeLayout(root);

    // Draw links
    d3.select(svgElement)
      .selectAll(".link")
      .data(root.links())
      .enter()
      .append("path")
      .attr("class", "link")
      .attr(
        "d",
        d3
          .linkHorizontal<BnBNode, BnBNode>()
          .x((d) => d.y || 0)
          .y((d) => d.x || 0),
      )
      .attr("fill", "none")
      .attr("stroke", "#ccc")
      .attr("stroke-width", 1.5);

    // Draw nodes
    const nodeGroups = d3
      .select(svgElement)
      .selectAll(".node")
      .data(root.descendants())
      .enter()
      .append("g")
      .attr("class", "node")
      .attr("transform", (d) => `translate(${d.y},${d.x})`)
      .on("click", (_, d) => {
        selectedNode.value = d.data;
      });

    nodeGroups
      .append("circle")
      .attr("r", 10)
      .attr("fill", (d) => nodeColors[d.data.status] || "#ccc")
      .attr("stroke", "#fff")
      .attr("stroke-width", 2);

    nodeGroups
      .append("text")
      .attr("dy", "0.31em")
      .attr("x", (d) => (d.children ? -13 : 13))
      .style("text-anchor", (d) => (d.children ? "end" : "start"))
      .text((d) => d.data.node_id)
      .style("font-size", "12px");
  };

  onMounted(renderTree);
  watch(treeData, renderTree, { deep: true });

  return { svg, selectedNode };
}
```

#### Main App

```vue
<!-- frontend/src/App.vue -->
<template>
  <div class="app">
    <nav class="navbar">
      <div class="navbar-brand">BnB Visualizer</div>
      <div class="navbar-links">
        <router-link to="/">Home</router-link>
        <router-link to="/live">Live Mode</router-link>
        <router-link to="/static">Static Mode</router-link>
        <router-link to="/docs">Documentation</router-link>
      </div>
    </nav>
    <div class="content">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterView, RouterLink } from "vue-router";
</script>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  background: #2c3e50;
  color: white;
}
.navbar-brand {
  font-size: 1.5rem;
  font-weight: bold;
}
.navbar-links {
  display: flex;
  gap: 20px;
}
.navbar-links a {
  color: white;
  text-decoration: none;
}
.content {
  flex: 1;
  overflow: auto;
}
</style>
```

---

## Type Consistency System

### Workflow

```
Python Pydantic Models
        │
        ▼
  JSON Schema (generated by pydantic-jsonschema)
        │
        ▼
  TypeScript Types (generated by json-schema-to-typescript)
```

### Step 1: Define Pydantic Models

```python
# bnb_framework/types.py
from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum

class NodeStatus(str, Enum):
    ACTIVE = "active"
    PRUNED = "pruned"
    SOLVED = "solved"
    EXPANDED = "expanded"

class BnBNode(BaseModel):
    node_id: int = Field(..., description="Unique node identifier")
    parent_id: Optional[int] = Field(None, description="Parent node ID")
    depth: int = Field(0, description="Depth in tree")
    lower_bound: Optional[float] = Field(None, description="Lower bound")
    upper_bound: Optional[float] = Field(None, description="Upper bound")
    status: NodeStatus = Field(NodeStatus.ACTIVE)
    branching_decision: Optional[dict] = Field(None)
    created_at: float = Field(default_factory=lambda: time.time())
    processed_at: Optional[float] = Field(None)
    children: list['BnBNode'] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

class BnBTree(BaseModel):
    root: BnBNode
    metadata: dict

class BnBEvent(BaseModel):
    type: Literal['metadata', 'node_created', 'node_processed', 'solution_found', 'search_completed']
    timestamp: float
```

### Step 2: Generate JSON Schema

```python
# scripts/generate_schema.py
from pydantic_jsonschema import GenerateJsonSchema
from bnb_framework.types import BnBNode, BnBTree, BnBEvent
import json
from pathlib import Path

def generate_schemas():
    generator = GenerateJsonSchema()

    schemas = {
        "BnBNode": generator.generate(schema=BnBNode),
        "BnBTree": generator.generate(schema=BnBTree),
        "BnBEvent": generator.generate(schema=BnBEvent),
    }

    # Save individual schemas
    for name, schema in schemas.items():
        Path(f"schemas/{name}.json").write_text(json.dumps(schema, indent=2))

    # Save combined schema
    combined = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "definitions": schemas
    }
    Path("schemas/bnb.json").write_text(json.dumps(combined, indent=2))

if __name__ == "__main__":
    generate_schemas()
```

### Step 3: Generate TypeScript Types

```bash
# In frontend/ directory
npx json-schema-to-typescript ../schemas/bnb.json -o src/types/bnb.ts
```

### Step 4: Use Generated Types

```typescript
// frontend/src/types/bnb.ts (generated)
export interface BnBNode {
  node_id: number;
  parent_id: number | null;
  depth: number;
  lower_bound: number | null;
  upper_bound: number | null;
  status: "active" | "pruned" | "solved" | "expanded";
  branching_decision: Record<string, any> | null;
  created_at: number;
  processed_at: number | null;
  children: BnBNode[];
  metadata: Record<string, any>;
}

// Use in components
import type { BnBNode } from "@/types/bnb";
```

---

## Data Flow

### Static Mode

```
┌─────────────────────────────────────────────────────────────┐
│  RESEARCHER                                                  │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  RUN SCRIPT                                                 │
│  python examples/run_static.py --algorithm tsp --instance ... │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  PYTHON BNB FRAMEWORK                                       │
│  - Runs algorithm                                           │
│  - Generates JSON/JSONL files                               │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  OUTPUT DIRECTORY                                            │
│  output/                                                    │
│  ├── app/ (Vue static files)                               │
│  │   ├── index.html                                        │
│  │   └── assets/                                           │
│  ├── bnb_tree.json                                         │
│  ├── bnb_tree.jsonl                                        │
│  └── metadata.json                                         │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  BROWSER                                                   │
│  - Opens output/app/index.html                             │
│  - Vue app loads JSON/JSONL files                           │
│  - Renders visualization                                   │
└─────────────────────────────────────────────────────────────┘
```

### Live Mode

```
┌─────────────────────────────────────────────────────────────┐
│  RESEARCHER                                                  │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  START SERVERS                                              │
│  Terminal 1: uv run uvicorn server.main:app --reload        │
│  Terminal 2: cd frontend && npm run dev                      │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  FASTAPI SERVER                                             │
│  - WebSocket endpoint: /ws/{run_id}                          │
│  - REST endpoint: /api/run                                  │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  VUE APP (Live Mode)                                        │
│  - Connects to WebSocket                                    │
│  - Receives real-time updates                               │
│  - Renders visualization                                    │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  BROWSER                                                   │
│  - Opens http://localhost:5173/live                         │
│  - Shows real-time BnB tree growth                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Summary

| Aspect         | Technology                          | Purpose                 |
| -------------- | ----------------------------------- | ----------------------- |
| Frontend       | Vue 3 + TypeScript + D3.js          | Visualization UI        |
| Backend Core   | Pure Python + Pydantic              | BnB algorithm framework |
| Backend Server | FastAPI (optional)                  | Live mode WebSocket     |
| Build (Python) | UV                                  | Package management      |
| Build (JS)     | Vite                                | Frontend bundling       |
| Type System    | Pydantic → JSON Schema → TypeScript | Consistency             |
| Data Format    | JSON/JSONL                          | Serialization           |
| Modes          | Static + Live                       | Flexibility             |

This architecture provides:

- ✅ Clean separation of concerns
- ✅ Reusability across BnB algorithms
- ✅ AI-friendly codebase
- ✅ Type safety across language boundary
- ✅ Flexible deployment (static files or live server)
- ✅ Research-focused features
