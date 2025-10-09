from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static
from tentacle.git_status_sidebar import CommitInfo
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict
import math


class CommitNode:
    """Represents a commit node in the graph with position and type information."""
    def __init__(self, commit_info: CommitInfo, i: int = 0, j: int = 0):
        self.commit_info = commit_info
        self.i = i  # Row position (time)
        self.j = j  # Column position (branch)
        

class CommitGraphWidget(Widget):
    """A widget that displays git commit history as a visual graph similar to GitKraken."""
    
    DEFAULT_CSS = """
    CommitGraphWidget {
        width: 100%;
        height: 100%;
        overflow: auto;
    }
    
    CommitGraphWidget Static {
        height: 1;
    }
    """
    
    def __init__(self, commits: List[CommitInfo], **kwargs):
        super().__init__(**kwargs)
        self.commits = commits
        self.nodes: Dict[str, CommitNode] = {}
        self.edges: List[Tuple[str, str, str]] = []  # (child_sha, parent_sha, edge_type)
        self.max_columns = 0
        
    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        self.compute_graph_positions()
        
    def compute_graph_positions(self) -> None:
        """Compute positions for commits in the graph layout using an algorithm similar to GitKraken."""
        if not self.commits:
            return
            
        # Create nodes for all commits
        self.nodes = {}
        self.edges = []
        
        # Initialize data structures
        branch_columns: List[Optional[str]] = [None] * max(10, len(self.commits))  # Start with reasonable size
        active_nodes: Dict[str, Set[int]] = defaultdict(set)
        
        # Process commits in chronological order (oldest first)
        for i, commit in enumerate(reversed(self.commits)):
            # Create node for this commit
            node = CommitNode(commit, i, 0)
            self.nodes[commit.sha] = node
            
            # Get children of this commit (commits that have this commit as parent)
            children = self._get_children(commit.sha)
            
            # Get direct lineage children (first parent matches this commit)
            branch_children = [child for child in children if self._is_first_parent(child, commit.sha)]
            
            # Get merge children (this commit is not the first parent)
            merge_children = [child for child in children if not self._is_first_parent(child, commit.sha)]
            
            # Compute forbidden indices (positions where merges occur)
            forbidden_indices = self._get_forbidden_indices(merge_children, active_nodes)
            
            # Find a commit to replace
            commit_to_replace, j_commit_to_replace = self._find_commit_to_replace(commit, branch_children, forbidden_indices)
            
            # Insert the commit in the active branches
            if commit_to_replace is not None:
                node.j = j_commit_to_replace
            else:
                if children:
                    child_sha = children[0]
                    if child_sha in self.nodes:
                        j_child = self.nodes[child_sha].j
                        node.j = self._insert_commit(commit.sha, j_child, forbidden_indices, branch_columns)
                else:
                    node.j = self._insert_commit(commit.sha, 0, set(), branch_columns)
            
            # Update active nodes with positions they occupy
            self._update_active_nodes(active_nodes, node.j, branch_children, commit.sha)
            
            # Remove children from active branches (except the one being replaced)
            self._remove_children_from_active_branches(branch_children, commit_to_replace, branch_columns)
            
            # Update branch column with this commit
            while len(branch_columns) <= node.j:
                branch_columns.append(None)
            branch_columns[node.j] = commit.sha
            
            # Add edges for visualization
            for parent_sha in commit.parents:
                edge_type = "merge" if commit.parents.index(parent_sha) > 0 else "normal"
                self.edges.append((commit.sha, parent_sha, edge_type))
                
        # Calculate maximum columns needed
        self.max_columns = max((node.j for node in self.nodes.values()), default=0) + 1
        
    def _get_children(self, parent_sha: str) -> List[str]:
        """Get all commits that have the given commit as a parent."""
        children = []
        for commit in self.commits:
            if parent_sha in commit.parents:
                children.append(commit.sha)
        return children
        
    def _is_first_parent(self, child_sha: str, parent_sha: str) -> bool:
        """Check if the parent is the first parent of the child commit."""
        child_commit = next((commit for commit in self.commits if commit.sha == child_sha), None)
        if child_commit and child_commit.parents:
            return child_commit.parents[0] == parent_sha
        return False
        
    def _get_forbidden_indices(self, merge_children: List[str], active_nodes: Dict[str, Set[int]]) -> Set[int]:
        """Compute forbidden indices where merges occur."""
        if not merge_children:
            return set()
            
        # Find the highest child (with minimum index)
        highest_child = None
        i_min = float('inf')
        
        for child_sha in merge_children:
            if child_sha in self.nodes:
                i_child = self.nodes[child_sha].i
                if i_child < i_min:
                    i_min = i_child
                    highest_child = child_sha
                    
        return active_nodes[highest_child] if highest_child is not None else set()
        
    def _find_commit_to_replace(self, commit: CommitInfo, branch_children: List[str], forbidden_indices: Set[int]) -> Tuple[Optional[str], int]:
        """Find a commit that can be replaced by this commit."""
        commit_to_replace = None
        j_commit_to_replace = float('inf')
        
        # The commit can only replace a child whose first parent is this commit
        for child_sha in branch_children:
            if child_sha in self.nodes:
                j_child = self.nodes[child_sha].j
                if j_child not in forbidden_indices and j_child < j_commit_to_replace:
                    commit_to_replace = child_sha
                    j_commit_to_replace = j_child
                    
        return (commit_to_replace, int(j_commit_to_replace)) if j_commit_to_replace != float('inf') else (None, 0)
        
    def _insert_commit(self, commit_sha: str, j: int, forbidden_indices: Set[int], branch_columns: List[Optional[str]]) -> int:
        """Try to insert commit as close as possible to position j."""
        # Try to find an available position near j
        dj = 0
        while j - dj >= 0 or j + dj < len(branch_columns):
            if j + dj < len(branch_columns) and branch_columns[j + dj] is None and (j + dj) not in forbidden_indices:
                while len(branch_columns) <= j + dj:
                    branch_columns.append(None)
                branch_columns[j + dj] = commit_sha
                return j + dj
            elif j - dj >= 0 and branch_columns[j - dj] is None and (j - dj) not in forbidden_indices:
                while len(branch_columns) <= j - dj:
                    branch_columns.append(None)
                branch_columns[j - dj] = commit_sha
                return j - dj
            dj += 1
            
        # If no position found, extend the branch columns
        branch_columns.append(commit_sha)
        return len(branch_columns) - 1
        
    def _update_active_nodes(self, active_nodes: Dict[str, Set[int]], j: int, branch_children: List[str], commit_sha: str) -> None:
        """Update the active nodes with new position information."""
        # Add this position to all active nodes
        for active_set in active_nodes.values():
            active_set.add(j)
            
        # Add children positions
        for child_sha in branch_children:
            if child_sha in self.nodes:
                active_nodes[commit_sha].add(self.nodes[child_sha].j)
                
        # Add this commit as an active node
        active_nodes[commit_sha].add(j)
        
    def _remove_children_from_active_branches(self, branch_children: List[str], commit_to_replace: Optional[str], branch_columns: List[Optional[str]]) -> None:
        """Remove children from active branches except the one being replaced."""
        for child_sha in branch_children:
            if child_sha != commit_to_replace and child_sha in self.nodes:
                j = self.nodes[child_sha].j
                # Clear the branch column for this child
                if j < len(branch_columns):
                    branch_columns[j] = None
                    
    def compose(self) -> ComposeResult:
        """Create the commit graph visualization."""
        # Compute graph positions if not already done
        if not self.nodes and self.commits:
            self.compute_graph_positions()
            
        # Create a Static widget for each commit row
        for i in range(len(self.commits)):
            graph_line = self._create_graph_line(i)
            yield Static(graph_line, expand=True)
            
    def _create_graph_line(self, y: int) -> str:
        """Create a string representation of the graph for a specific row."""
        # Create a list to hold the characters for this line
        # Calculate appropriate line width based on terminal size and graph layout
        # Try to get the actual terminal width, but fall back to a reasonable default
        try:
            # Import here to avoid circular imports
            from textual.app import App
            app = App.get_current_app()
            if app:
                # Get the available width accounting for padding and borders
                terminal_width = app.size.width
                # Reserve space for borders, padding, and ensure we don't overflow
                line_width = max(50, terminal_width - 10)  # Leave some margin
            else:
                line_width = 120  # Reasonable fallback
        except:
            line_width = 120  # Fallback if we can't get terminal size
        line_chars = [' '] * line_width
        
        # Draw vertical lines for each branch column
        for j in range(self.max_columns):
            x = j * 5 + 1  # Maintain spacing between columns
            if 0 <= x < line_width:
                line_chars[x] = '│'
                
        # Draw nodes
        for node in self.nodes.values():
            if node.i == y:  # Only draw nodes on this row
                x = node.j * 5 + 1  # Maintain spacing between columns
                if 0 <= x < line_width:
                    line_chars[x] = '●'
                    
        # Draw connections
        for child_sha, parent_sha, edge_type in self.edges:
            if child_sha in self.nodes and parent_sha in self.nodes:
                child_node = self.nodes[child_sha]
                parent_node = self.nodes[parent_sha]
                
                # Draw vertical connection if nodes are in the same column
                if child_node.j == parent_node.j and min(child_node.i, parent_node.i) <= y <= max(child_node.i, parent_node.i):
                    x = child_node.j * 5 + 1  # Maintain spacing between columns
                    if 0 <= x < line_width and y != child_node.i and y != parent_node.i:
                        line_chars[x] = '│'
                        
                # Draw merge connections
                if edge_type == "merge" and child_node.i == y:
                    parent_x = parent_node.j * 5 + 1  # Maintain spacing between columns
                    child_x = child_node.j * 5 + 1  # Maintain spacing between columns
                    
                    if 0 <= child_x < line_width and 0 <= parent_x < line_width:
                        # Draw corner connector
                        if child_x < parent_x:
                            line_chars[child_x] = '└' if child_node.i > parent_node.i else '┌'
                        else:
                            line_chars[child_x] = '┘' if child_node.i > parent_node.i else '┐'
                            
                        # Draw horizontal line
                        start_x = min(child_x, parent_x) + 1
                        end_x = max(child_x, parent_x)
                        for x in range(start_x, end_x):
                            if 0 <= x < line_width:
                                line_chars[x] = '─'
                                
                        # Draw parent connector
                        line_chars[parent_x] = '◉'
                        
        # Add commit info to the right of the graph with adequate spacing
        info_start_x = self.max_columns * 5 + 5  # Start after graph area with buffer
        
        # Find the commit for this row (accounting for reversed order in display)
        if y < len(self.commits):
            commit_index = len(self.commits) - 1 - y
            if 0 <= commit_index < len(self.commits):
                commit = self.commits[commit_index]
                # Format commit info with message that respects line boundaries
                # Preserve multi-line commit messages better by limiting to first line for display
                message_lines = commit.message.split('\n')
                display_message = message_lines[0] if message_lines else commit.message
                # Remove extra whitespace but keep the core message
                display_message = display_message.strip().replace('\r', '')
                
                # Calculate base info length (SHA + space + author + space)
                base_info = f"{commit.sha[:8]} {commit.author[:20]:<20} "
                base_length = len(base_info)
                
                # Calculate available space for message more conservatively
                available_space = max(10, line_width - info_start_x - base_length - 5)  # -5 for safety margin
                
                # Only process if we have reasonable space available
                if available_space > 20 and len(display_message) > available_space:
                    display_message = display_message[:available_space - 3] + "..."
                elif available_space <= 20:
                    # If very little space, just show a minimal indicator
                    display_message = "..." if len(display_message) > 3 else display_message
                
                info_text = f"{base_info}{display_message}"
                
                # Place commit info characters with strict boundary checking
                for i, char in enumerate(info_text):
                    x = info_start_x + i
                    # Strict boundary checking - only place characters within safe bounds
                    if 0 <= x < line_width:
                        line_chars[x] = char
                    # Stop immediately if we're at or beyond the line boundary
                    if x >= line_width - 1:
                        break
                        
        return ''.join(line_chars)
