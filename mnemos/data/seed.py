"""
MNEMOS: Seed Script
====================
Run this to populate the Neo4j knowledge graph and vector index
with the five core seed failure records + Kerala demo project.

Usage:
    python -m mnemos.data.seed              # uses env vars from .env
    python -m mnemos.data.seed --dry-run    # print records, no DB writes
"""

import argparse
import sys

from loguru import logger
from rich.console import Console
from rich.table import Table

from mnemos.data.seed_data import ALL_SEED_RECORDS

console = Console()


def seed(dry_run: bool = False) -> None:
    """Seed all failure records into the knowledge graph."""

    if dry_run:
        console.rule("[bold yellow]KARMA-OMEGA MNEMOS — Dry Run")
        table = Table(title="Seed Records Preview")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Location")
        table.add_column("Type")
        table.add_column("Severity", style="red")
        table.add_column("Causes #", justify="right")

        for rec in ALL_SEED_RECORDS:
            table.add_row(
                rec.id or "—",
                rec.title,
                rec.location,
                rec.failure_type.value,
                rec.severity.value,
                str(len(rec.root_causes)),
            )
        console.print(table)
        console.print("\n[green]✓ Dry run complete. No DB writes performed.[/green]")
        return

    console.rule("[bold red]KARMA-OMEGA MNEMOS — Seeding Knowledge Graph")

    # Lazy imports to avoid startup cost when doing dry-run
    from mnemos.graph.client import GraphClient
    from mnemos.embeddings.pipeline import EmbeddingPipeline
    from mnemos.ingestion.service import DocumentIngestionService

    graph = GraphClient.get_instance()
    embeddings = EmbeddingPipeline.get_instance()
    ingestion = DocumentIngestionService(
        graph_client=graph,
        embedding_pipeline=embeddings,
    )

    records_dict = [r.model_dump() for r in ALL_SEED_RECORDS]
    responses = ingestion.batch_ingest(records_dict, compute_similarities=True)

    console.print("\n[bold green]✅ Seeding Complete[/bold green]\n")
    table = Table(title="Ingestion Results")
    table.add_column("Title", style="white")
    table.add_column("Document ID", style="cyan")
    table.add_column("Nodes", justify="right")
    table.add_column("Edges", justify="right")
    table.add_column("Embedding", style="green")
    table.add_column("Time (ms)", justify="right")

    for resp in responses:
        table.add_row(
            resp.failure_record.title[:40],
            resp.document_id[:8] + "...",
            str(resp.nodes_created),
            str(resp.edges_created),
            "✓" if resp.embedding_stored else "✗",
            f"{resp.processing_time_ms:.0f}",
        )
    console.print(table)

    node_count = graph.get_node_count()
    edge_count = graph.get_edge_count()
    console.print(
        f"\n[bold]Graph Stats:[/bold] {node_count} nodes | {edge_count} relationships"
    )
    console.print(
        "[bold cyan]MNEMOS is ready. Run the API:[/bold cyan] "
        "uvicorn mnemos.api.main:app --reload --port 8001"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed MNEMOS knowledge graph")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no DB writes")
    args = parser.parse_args()
    seed(dry_run=args.dry_run)
