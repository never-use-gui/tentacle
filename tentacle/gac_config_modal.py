"""GAC Configuration Modal - UI for configuring GAC settings.

This module provides a Textual modal screen for configuring GAC (Git Auto Commit)
settings, including provider selection, model configuration, and API key management.
"""

import os
import stat
import tempfile
import shutil
from pathlib import Path
from textual.screen import ModalScreen
from textual.widgets import Static, Button, Input, Select, Label
from textual.containers import Horizontal, Container, VerticalScroll
from textual.app import ComposeResult
from textual import on
from typing import Optional, Dict

# TODO: Add unit tests for configuration modal
# TODO: Test GAC availability detection in UI
# TODO: Add tests for form validation

from tentacle.gac_provider_registry import GACProviderRegistry, GAC_AVAILABLE


class GACConfigModal(ModalScreen):
    """Modal screen for configuring GAC settings with dynamic provider discovery."""
    
    DEFAULT_CSS = """
    GACConfigModal {
        align: center middle;
    }
    
    #gac-container {
        border: solid #6c7086;
        background: #00122f;
        width: 60%;
        height: 70%;
        margin: 1;
        padding: 0;
    }
    
    #gac-container > VerticalScroll {
        height: 1fr;
        padding: 1;
        overflow-y: auto;
        scrollbar-size: 1 1;
        scrollbar-color: #9399b2;
    }
    
    .gac-input {
        margin: 1 0;
        width: 100%;
    }
    
    .gac-select {
        margin: 1 0;
        width: 100%;
    }
    
    .gac-buttons {
        align: center bottom;
        height: auto;
        margin: 2 0 0 0;
    }
    
    .gac-label {
        margin: 1 0 0 0;
        color: #bb9af7;
        text-style: bold;
    }
    """
    
    # Provider registry (dynamically discovered)
    _provider_registry = GACProviderRegistry()
    
    def __init__(self):
        super().__init__()
        self.current_config = self._load_current_config()
        
    def _load_current_config(self) -> Dict[str, str]:
        """Load current GAC configuration from environment or config file."""
        config = {}
        
        # Try to load from GAC config
        gac_env_file = Path.home() / ".gac.env"
        if gac_env_file.exists():
            try:
                with open(gac_env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip().strip('"\'')
            except Exception:
                pass
                
        # Also check environment variables for all known providers
        providers = self._provider_registry.get_supported_providers()
        for provider in providers.keys():
            api_key_var = f"{provider.upper().replace('-', '_')}_API_KEY"
            if api_key_var in os.environ:
                config[api_key_var] = os.environ[api_key_var]
                
        return config
        
    def compose(self) -> ComposeResult:
        """Create the modal content with dynamic provider list."""
        with Container(id="gac-container"):
            yield Static("🤖 Configure GAC (Git Auto Commit)", classes="panel-header")
            
            # Wrap everything in VerticalScroll for scrollability
            with VerticalScroll():
                # Show warning if GAC is not installed
                if not GAC_AVAILABLE:
                    yield Static(
                        "⚠️  GAC package not installed!\n"
                        "Install with: uv pip install 'gac>=0.18.0'\n\n"
                        "You can still configure settings, but commit message generation won't work.",
                        classes="gac-label"
                    )
                
                yield Label("Provider (21+ supported):", classes="gac-label")
                # Get all providers dynamically
                providers = self._provider_registry.get_supported_providers()
                provider_options = [(f"{info[0]} ({provider})", provider) 
                                  for provider, info in sorted(providers.items())]
                current_provider = self._detect_current_provider()
                yield Select(provider_options, value=current_provider, id="provider-select", classes="gac-select")
                
                yield Label("Model (select suggested or type custom):", classes="gac-label")
                # Get suggested models for current provider
                initial_models = self._provider_registry.get_suggested_models(current_provider)
                model_options = [(model, model) for model in initial_models]
                # Add "Custom..." option
                model_options.insert(0, ("Custom (type below)...", "__custom__"))
                yield Select(model_options, id="model-select", classes="gac-select")
                
                yield Label("Custom Model Name (or select from dropdown):", classes="gac-label")
                default_model = self._provider_registry.get_default_model(current_provider)
                yield Input(
                    value=default_model,
                    placeholder="e.g., claude-sonnet-4-5, gpt-4o-mini, llama3.2...",
                    id="model-input",
                    classes="gac-input"
                )
                
                yield Label("API Key (not needed for local providers):", classes="gac-label")
                current_key = self._get_current_api_key(current_provider)
                yield Input(
                    value=current_key, 
                    password=True, 
                    placeholder="Enter your API key...",
                    id="api-key-input",
                    classes="gac-input"
                )
                
                with Horizontal(classes="gac-buttons"):
                    yield Button("Cancel", id="gac-cancel", classes="cancel-button")
                    yield Button("Test", id="gac-test", classes="test-button")
                    yield Button("Save", id="gac-save", classes="save-button")
                
    def _detect_current_provider(self) -> str:
        """Detect the current provider from config."""
        # First check if GAC_MODEL is set (most reliable)
        if "GAC_MODEL" in self.current_config:
            gac_model = self.current_config["GAC_MODEL"]
            if ':' in gac_model:
                provider = gac_model.split(':', 1)[0]
                # Validate it's a known provider
                providers = self._provider_registry.get_supported_providers()
                if provider in providers:
                    return provider
        
        # Fall back to checking for API keys in config
        providers = self._provider_registry.get_supported_providers()
        for provider in providers.keys():
            api_key_var = f"{provider.upper().replace('-', '_')}_API_KEY"
            if api_key_var in self.current_config:
                return provider
        
        # Default to OpenAI
        return "openai"
        
    def _get_current_api_key(self, provider: str) -> str:
        """Get the current API key for the provider."""
        api_key_var = f"{provider.upper()}_API_KEY"
        return self.current_config.get(api_key_var, "")
        
    @on(Select.Changed, "#provider-select")
    def on_provider_changed(self, event: Select.Changed) -> None:
        """Update model options when provider changes."""
        provider = str(event.value)
        model_select = self.query_one("#model-select", Select)
        model_input = self.query_one("#model-input", Input)
        api_key_input = self.query_one("#api-key-input", Input)
        
        # Update model options with suggestions for this provider
        suggested_models = self._provider_registry.get_suggested_models(provider)
        model_options = [("Custom (type below)...", "__custom__")]
        model_options.extend([(model, model) for model in suggested_models])
        model_select.set_options(model_options)
        
        # Update model input with default
        default_model = self._provider_registry.get_default_model(provider)
        model_input.value = default_model
        
        # Update API key
        current_key = self._get_current_api_key(provider)
        api_key_input.value = current_key
        
        # Show info for local providers
        if provider in ["ollama", "lm-studio"]:
            self.app.notify(f"ℹ️  {provider} is a local provider - no API key needed!", severity="information")
    
    @on(Select.Changed, "#model-select")
    def on_model_changed(self, event: Select.Changed) -> None:
        """Update model input when selection changes."""
        selected = str(event.value)
        if selected != "__custom__":
            model_input = self.query_one("#model-input", Input)
            model_input.value = selected
        
    @on(Button.Pressed, "#gac-cancel")
    def on_cancel(self, event: Button.Pressed) -> None:
        """Cancel configuration."""
        self.app.pop_screen()
        
    @on(Button.Pressed, "#gac-test")
    def on_test(self, event: Button.Pressed) -> None:
        """Test the GAC configuration."""
        if not GAC_AVAILABLE:
            self.app.notify(
                "❌ GAC package not installed. Install with: uv pip install 'gac>=0.18.0'",
                severity="error"
            )
            return
        
        config = self._get_form_config()
        if not config:
            return
            
        # TODO: Implement a test commit message generation
        # For now, just validate the configuration
        self.app.notify("🧪 Testing GAC configuration... (Feature coming soon!)", severity="information")
        
    @on(Button.Pressed, "#gac-save")
    def on_save(self, event: Button.Pressed) -> None:
        """Save the GAC configuration."""
        config = self._get_form_config()
        if not config:
            return
        
        # Warn if GAC is not available (but still allow saving)
        if not GAC_AVAILABLE:
            self.app.notify(
                "⚠️  GAC not installed - config saved but won't work until you install GAC",
                severity="warning"
            )
            
        try:
            self._save_config(config)
            self.app.notify("✅ GAC configuration saved successfully!", severity="information")
            self.app.pop_screen()
        except Exception as e:
            self.app.notify(f"❌ Failed to save GAC config: {e}", severity="error")
            
    def _get_form_config(self) -> Optional[Dict[str, str]]:
        """Get configuration from form fields with validation."""
        provider_select = self.query_one("#provider-select", Select)
        model_input = self.query_one("#model-input", Input)
        api_key_input = self.query_one("#api-key-input", Input)
        
        provider = str(provider_select.value)
        model = model_input.value.strip()
        api_key = api_key_input.value.strip()
        
        if not provider:
            self.app.notify("❌ Please select a provider", severity="error")
            return None
        
        if not model:
            self.app.notify("❌ Please enter a model name", severity="error")
            return None
        
        # Validate provider is known
        providers = self._provider_registry.get_supported_providers()
        if provider not in providers:
            self.app.notify(f"⚠️  Unknown provider '{provider}' - GAC may not support it", severity="warning")
        
        # Check if API key is needed (not for local providers)
        local_providers = ["ollama", "lm-studio"]
        if not api_key and provider not in local_providers:
            self.app.notify("❌ Please enter an API key (or use a local provider like ollama/lm-studio)", severity="error")
            return None
        
        return {
            "provider": provider,
            "model": model,
            "api_key": api_key
        }
        
    def _save_config(self, config: Dict[str, str]) -> None:
        """Save configuration to GAC config file with secure permissions."""
        gac_env_file = Path.home() / ".gac.env"
        provider = config["provider"]
        gac_model = f"{provider}:{config['model']}"
        
        # Validate model format
        is_valid, error_msg = self._provider_registry.validate_model_format(gac_model)
        if not is_valid:
            raise ValueError(error_msg)
        
        out_config = dict()
        out_config["GAC_MODEL"] = gac_model
        
        # Only add API key if it's provided (local providers don't need it)
        if config["api_key"]:
            api_key_var = f"{provider.upper().replace('-', '_')}_API_KEY"
            out_config[api_key_var] = config["api_key"]
        
        # Write to temporary file first (atomic operation)
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            dir=gac_env_file.parent,
            delete=False
        ) as tmp:
            tmp.write("# GAC Configuration (Generated by Tentacle)\n")
            tmp.write(f"# Provider: {provider}\n")
            tmp.write(f"# Model: {config['model']}\n\n")
            for key, value in out_config.items():
                tmp.write(f"{key}='{value}'\n")
            tmp_path = Path(tmp.name)
        
        # Set restrictive permissions (owner read/write only - 0o600)
        os.chmod(tmp_path, stat.S_IRUSR | stat.S_IWUSR)
        
        # Backup existing config if it exists
        if gac_env_file.exists():
            backup = gac_env_file.with_suffix('.env.backup')
            shutil.copy2(gac_env_file, backup)
        
        # Atomic move (rename is atomic on POSIX systems)
        shutil.move(str(tmp_path), str(gac_env_file))
