"""GAC (Git Auto Commit) integration for Tentacle.

This module provides the main integration class for GAC functionality,
including commit message generation using AI models.
"""

from pathlib import Path
from typing import Optional, Dict

# TODO: Add unit tests for commit message generation
# TODO: Add integration tests for GAC configuration loading
# TODO: Test error handling for missing API keys

# Graceful GAC import handling - app should work even if GAC is not installed
try:
    import gac
    GAC_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    GAC_AVAILABLE = False
    gac = None  # type: ignore

from tentacle.gac_provider_registry import GACProviderRegistry


class GACIntegration:
    """Integration class for GAC (Git Auto Commit) functionality.
    
    This class handles loading GAC configuration and generating commit messages
    using the GAC library with proper validation and error handling.
    """
    
    def __init__(self, git_sidebar):
        """Initialize GAC integration.
        
        Args:
            git_sidebar: GitStatusSidebar instance for accessing git status/diff
        """
        self.git_sidebar = git_sidebar
        self.config = self._load_config()
        
    def _load_config(self) -> Optional[Dict[str, str]]:
        """Load GAC configuration from ~/.gac.env file.
        
        Returns:
            Dict of config values, or None if file doesn't exist
        """
        gac_env_file = Path.home() / ".gac.env"
        if not gac_env_file.exists():
            return None

        config = {}
        try:
            with open(gac_env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip().strip('"\'')
            self.config = config
            return config
        except Exception:
            return None
            
    def is_configured(self) -> bool:
        """Check if GAC is properly configured.
        
        Returns:
            True if configuration exists and is valid
        """
        self.config = self._load_config()
        if not self.config:
            return False
        return True
        
    def generate_commit_message(
        self, 
        staged_only: bool = True, 
        one_liner: bool = False,
        verbose: bool = False,
        hint: str = "", 
        scope: Optional[str] = None
    ) -> Optional[str]:
        """Generate a commit message using GAC with stable tuple-based API.
        
        This method uses GAC's stable public API with tuple-based prompts:
        - gac.build_prompt() returns (system_prompt, user_prompt)
        - gac.generate_commit_message() accepts prompt=(system, user)
        
        Args:
            staged_only: Only include staged changes in the commit
            one_liner: Generate a single-line commit message
            verbose: Generate a more detailed commit message
            hint: Optional hint to guide the AI commit message generation
            scope: Optional scope for the commit (currently unused by GAC)
            
        Returns:
            Generated commit message string, or None if generation fails
            
        Raises:
            ImportError: If GAC package is not installed
            ValueError: If GAC is not configured, no changes exist, or generation fails
        """
        # Check if GAC is available before attempting to use it
        if not GAC_AVAILABLE or gac is None:
            raise ImportError(
                "GAC package not found. Install with: uv pip install 'gac>=0.18.0'\n"
                "GAC provides AI-powered commit message generation."
            )
        
        if not self.is_configured():
            raise ValueError("GAC is not configured. Please configure it first.")
        
        try:
            # Get git status and diff from sidebar
            status = self.git_sidebar.get_git_status()
            if staged_only:
                diff = self.git_sidebar.get_staged_diff()
            else:
                diff = self.git_sidebar.get_full_diff()
            
            if not diff.strip():
                raise ValueError("No changes to commit")
            
            # Get diff stat for file changes summary (required by GAC)
            # This provides a summary like: "file1.py | 10 +++++-----"
            try:
                if staged_only:
                    diff_stat = self.git_sidebar.repo.git.diff('--cached', '--stat') if self.git_sidebar.repo else ""
                else:
                    diff_stat = self.git_sidebar.repo.git.diff('--stat') if self.git_sidebar.repo else ""
            except Exception:
                diff_stat = ""  # Fallback to empty if stat fails
            
            # Build the prompt using GAC's stable API (safe because we checked GAC_AVAILABLE above)
            # Returns tuple: (system_prompt, user_prompt)
            # Note: verbose parameter not supported in GAC 1.4.1 - upgrade GAC to use it:
            #       uv pip install --upgrade gac
            system_prompt, user_prompt = gac.build_prompt(  # type: ignore
                status=status,
                processed_diff=diff,
                diff_stat=diff_stat,  # Required parameter for GAC
                one_liner=one_liner,
                hint=hint,
            )
            
            # Get the configured model
            model = self.config.get("GAC_MODEL")
            if not model:
                raise ValueError("GAC_MODEL not set in configuration")
            
            # Validate model format (provider:model)
            registry = GACProviderRegistry()
            is_valid, error_msg = registry.validate_model_format(model)
            if not is_valid:
                raise ValueError(f"Invalid model format: {error_msg}")
            
            # Generate commit message using tuple-based prompt format
            # This is the stable public API as of GAC latest versions
            commit_message = gac.generate_commit_message(  # type: ignore
                model=model,
                prompt=(system_prompt, user_prompt),
                quiet=True
            )
            
            if not commit_message or not commit_message.strip():
                raise ValueError("GAC returned an empty commit message")
            
            return commit_message.strip()
        
        except ValueError:
            # Re-raise ValueError as-is (these are our validation errors)
            raise
        except Exception as e:
            # Wrap other exceptions with more context
            error_type = type(e).__name__
            raise ValueError(f"GAC generation failed ({error_type}): {str(e)}")
