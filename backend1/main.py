from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import networkx as nx

# --------------------------
# Data Models
# --------------------------

class Node(BaseModel):
    id: str
    type: Optional[str] = None
    data: Optional[dict] = None

class Edge(BaseModel):
    source: str
    target: str
    type: Optional[str] = None

class Pipeline(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

# --------------------------
# App Initialization
# --------------------------

app = FastAPI(
    title="Pipeline Parser API",
    description="Parses pipeline nodes and edges to return node/edge count and DAG check.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify allowed origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------
# API Endpoints
# --------------------------

@app.get("/")
async def health_check():
    return {"status": "ok"}

@app.post("/pipelines/parse")
async def parse_pipeline(pipeline: Pipeline):
    # Validate duplicate node IDs
    node_ids = [node.id for node in pipeline.nodes]
    if len(node_ids) != len(set(node_ids)):
        return {"error": "Duplicate node IDs found"}

    # Validate edges refer to existing nodes
    node_id_set = set(node_ids)
    invalid_edges = [
        {"source": edge.source, "target": edge.target}
        for edge in pipeline.edges
        if edge.source not in node_id_set or edge.target not in node_id_set
    ]
    if invalid_edges:
        return {
            "error": "Invalid edges found: edges refer to nonexistent nodes",
            "invalid_edges": invalid_edges,
        }

    # Build graph
    G = nx.DiGraph()
    G.add_nodes_from(node_ids)
    G.add_edges_from([(edge.source, edge.target) for edge in pipeline.edges])

    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    is_dag = nx.is_directed_acyclic_graph(G)

    cycle_path = []
    if not is_dag:
        try:
            cycle_path = nx.find_cycle(G)
        except nx.NetworkXNoCycle:
            cycle_path = []

    return {
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "is_dag": is_dag,
        "cycle_path": cycle_path,
    }
