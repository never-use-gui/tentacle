import sys

from octotui.git_diff_viewer import GitDiffViewer


def main():
    # Optional repo path argument
    repo_path = sys.argv[1] if len(sys.argv) > 1 else None

    if len(sys.argv) > 2:
        print("Usage: octotui [repo_path]")
        sys.exit(1)

    app = GitDiffViewer(repo_path)
    app.run()
