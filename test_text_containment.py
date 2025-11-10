#!/usr/bin/env python3
"""Test text containment in commit graph."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    import git
    from tentacle.graph_layout import GraphLayoutEngine, GraphRenderer
    from rich.console import Console
    
    def test_text_containment():
        """Test that text doesn't leak through graph."""
        console = Console()
        
        try:
            repo = git.Repo(".")
            
            console.print("[bold green]Testing text containment...[/bold green]\n")
            
            engine = GraphLayoutEngine(repo)
            graph = engine.build_graph(max_commits=20)
            
            console.print(f"[bold blue]Graph: {len(graph.commits)} commits, {graph.max_lanes} lanes[/bold blue]\n")
            
            renderer = GraphRenderer(graph)
            
            console.print("[bold yellow]Commit Graph (with fixed-width layout):[/bold yellow]\n")
            
            for commit in graph.get_commits_in_order()[:20]:
                line = renderer.render_row(commit, show_details=True)
                console.print(line)
            
            console.print("\n[bold green]✓ Text containment test complete![/bold green]")
            console.print("\n[dim]Graph area should have fixed width, text should not overlap.[/dim]")
            
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
            import traceback
            traceback.print_exc()
            return 1
        
        return 0
    
    if __name__ == "__main__":
        sys.exit(test_text_containment())

except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)
