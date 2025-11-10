"""Data structures for commit graph visualization.

This module defines the core data structures used to represent
a Git repository's commit graph, including commits, branches, tags,
and their relationships.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict, Tuple
from datetime import datetime
from enum import Enum


class CommitType(Enum):
    """Type of commit in the graph."""
    NORMAL = "normal"          # Regular commit
    MERGE = "merge"            # Merge commit (2+ parents)
    INITIAL = "initial"        # Initial commit (no parents)
    HEAD = "head"              # Current HEAD position


class RefType(Enum):
    """Type of git reference."""
    BRANCH = "branch"
    TAG = "tag"
    REMOTE_BRANCH = "remote"
    HEAD = "head"


@dataclass
class GitRef:
    """Represents a Git reference (branch, tag, etc.)."""
    name: str
    ref_type: RefType
    commit_sha: str
    is_current: bool = False  # True if this is the current HEAD
    
    def short_name(self) -> str:
        """Get shortened reference name (remove refs/heads/, etc.)."""
        if self.name.startswith('refs/heads/'):
            return self.name[11:]
        elif self.name.startswith('refs/tags/'):
            return self.name[10:]
        elif self.name.startswith('refs/remotes/'):
            return self.name[13:]
        return self.name
    
    def display_name(self) -> str:
        """Get display name with appropriate prefix."""
        short = self.short_name()
        if self.ref_type == RefType.TAG:
            return f"🏷️  {short}"
        elif self.ref_type == RefType.REMOTE_BRANCH:
            return f"🌐 {short}"
        elif self.ref_type == RefType.HEAD:
            return f"➤ {short}"
        else:
            return f"🌿 {short}"


@dataclass
class CommitNode:
    """Represents a single commit in the graph."""
    sha: str                           # Full commit SHA
    short_sha: str                     # Abbreviated SHA (7-8 chars)
    message: str                       # Commit message (first line)
    full_message: str                  # Full commit message
    author: str                        # Author name
    author_email: str                  # Author email
    committer: str                     # Committer name
    date: datetime                     # Commit date
    
    parent_shas: List[str] = field(default_factory=list)  # Parent commit SHAs
    child_shas: List[str] = field(default_factory=list)   # Child commit SHAs
    
    refs: List[GitRef] = field(default_factory=list)      # Branches/tags pointing here
    
    commit_type: CommitType = CommitType.NORMAL
    
    # Layout information (set by layout algorithm)
    lane: int = 0                      # Visual column position
    row: int = 0                       # Visual row position
    color_index: int = 0               # Color for this commit's branch
    
    # Enhanced layout for continuous branch visualization
    active_lanes: Set[int] = field(default_factory=set)      # All lanes active at this commit
    merge_source_lanes: List[int] = field(default_factory=list)  # Lanes merging into this commit
    continues_down: bool = True         # Whether this lane continues to children
    
    def is_merge(self) -> bool:
        """Check if this is a merge commit."""
        return len(self.parent_shas) > 1
    
    def is_initial(self) -> bool:
        """Check if this is an initial commit."""
        return len(self.parent_shas) == 0
    
    def short_message(self, max_length: int = 60) -> str:
        """Get truncated commit message."""
        if len(self.message) <= max_length:
            return self.message
        return self.message[:max_length - 3] + "..."
    
    def has_ref(self, ref_type: Optional[RefType] = None) -> bool:
        """Check if commit has any refs (optionally filter by type)."""
        if ref_type is None:
            return len(self.refs) > 0
        return any(ref.ref_type == ref_type for ref in self.refs)


@dataclass
class GraphEdge:
    """Represents an edge between two commits in the graph."""
    from_sha: str      # Parent commit SHA
    to_sha: str        # Child commit SHA
    from_lane: int     # Starting lane
    to_lane: int       # Ending lane
    is_merge: bool     # True if this edge is part of a merge
    color_index: int   # Color for this edge
    
    def is_straight(self) -> bool:
        """Check if edge goes straight down (same lane)."""
        return self.from_lane == self.to_lane
    
    def is_crossing(self) -> bool:
        """Check if edge crosses lanes."""
        return not self.is_straight()


@dataclass
class CommitGraph:
    """Complete commit graph data structure."""
    commits: Dict[str, CommitNode] = field(default_factory=dict)  # SHA -> CommitNode
    edges: List[GraphEdge] = field(default_factory=list)
    refs: Dict[str, GitRef] = field(default_factory=dict)         # ref name -> GitRef
    
    head_sha: Optional[str] = None     # SHA of current HEAD
    current_branch: Optional[str] = None
    
    # Layout metadata
    max_lanes: int = 0                 # Maximum number of lanes used
    max_rows: int = 0                  # Total number of rows
    
    # Color palette for branches (indices map to colors)
    colors: List[str] = field(default_factory=lambda: [
        "#bb9af7",  # Purple
        "#9ece6a",  # Green
        "#7dcfff",  # Blue
        "#f7768e",  # Red
        "#ff9e64",  # Orange
        "#e0af68",  # Yellow
        "#73daca",  # Cyan
        "#c0caf5",  # Light blue
    ])
    
    def add_commit(self, commit: CommitNode) -> None:
        """Add a commit to the graph."""
        self.commits[commit.sha] = commit
        self.max_rows = max(self.max_rows, commit.row + 1)
        self.max_lanes = max(self.max_lanes, commit.lane + 1)
    
    def add_edge(self, edge: GraphEdge) -> None:
        """Add an edge to the graph."""
        self.edges.append(edge)
    
    def add_ref(self, ref: GitRef) -> None:
        """Add a reference (branch/tag) to the graph."""
        self.refs[ref.name] = ref
        
        # Add ref to the commit it points to
        if ref.commit_sha in self.commits:
            self.commits[ref.commit_sha].refs.append(ref)
    
    def get_commit(self, sha: str) -> Optional[CommitNode]:
        """Get a commit by SHA (supports partial SHAs)."""
        # Try exact match first
        if sha in self.commits:
            return self.commits[sha]
        
        # Try partial SHA match
        for full_sha, commit in self.commits.items():
            if full_sha.startswith(sha):
                return commit
        
        return None
    
    def get_commits_in_order(self) -> List[CommitNode]:
        """Get commits sorted by row (topological order)."""
        return sorted(self.commits.values(), key=lambda c: c.row)
    
    def get_branches_at_commit(self, sha: str) -> List[GitRef]:
        """Get all branches pointing to a commit."""
        commit = self.get_commit(sha)
        if not commit:
            return []
        return [ref for ref in commit.refs if ref.ref_type == RefType.BRANCH]
    
    def get_tags_at_commit(self, sha: str) -> List[GitRef]:
        """Get all tags pointing to a commit."""
        commit = self.get_commit(sha)
        if not commit:
            return []
        return [ref for ref in commit.refs if ref.ref_type == RefType.TAG]
    
    def get_color_for_lane(self, lane: int) -> str:
        """Get color for a given lane."""
        return self.colors[lane % len(self.colors)]


@dataclass
class GraphFilter:
    """Filtering options for the commit graph."""
    search_text: Optional[str] = None       # Search in commit messages
    author_filter: Optional[str] = None     # Filter by author
    branch_filter: Optional[str] = None     # Show only specific branch
    date_from: Optional[datetime] = None    # Filter by date range
    date_to: Optional[datetime] = None
    show_merges: bool = True                # Show/hide merge commits
    show_tags: bool = True                  # Show/hide tags
    show_remote_branches: bool = True       # Show/hide remote branches
    max_commits: int = 100                  # Maximum commits to show
    
    def matches(self, commit: CommitNode) -> bool:
        """Check if a commit matches the filter criteria."""
        # Search text filter
        if self.search_text:
            search_lower = self.search_text.lower()
            if not (search_lower in commit.message.lower() or
                    search_lower in commit.author.lower() or
                    search_lower in commit.sha.lower()):
                return False
        
        # Author filter
        if self.author_filter:
            if self.author_filter.lower() not in commit.author.lower():
                return False
        
        # Date filter
        if self.date_from and commit.date < self.date_from:
            return False
        if self.date_to and commit.date > self.date_to:
            return False
        
        # Merge filter
        if not self.show_merges and commit.is_merge():
            return False
        
        return True
