from __future__ import annotations

from typing import ClassVar

from pyfiglet import Figlet
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class OctotuiLogo(Widget):
    """Big, stylish Octotui logo using pyfiglet with the pagga font."""

    DEFAULT_CSS = """
    OctotuiLogo {
        height: auto;
        width: 1fr;
        content-align: center middle;
        background: transparent;
        align: center middle;
    }

    OctotuiLogo .logo-text {
        text-style: bold;
        color: #bb9af7;
        text-align: center;
        margin: 0;
    }
    """

    LOGO_TEXT: ClassVar[str] = "OCTOTUI"
    FONT_NAME: ClassVar[str] = "pagga"

    def compose(self) -> ComposeResult:
        """Create a stylish FIGlet logo using the pagga font."""
        logo_lines = self._generate_logo()

        yield Static("", classes="logo-text")
        for line in logo_lines:
            yield Static(line, classes="logo-text")
        yield Static("", classes="logo-text")

    def on_resize(self) -> None:
        """Handle resize events to maintain proper sizing."""
        self.refresh()

    @classmethod
    def _generate_logo(cls) -> list[str]:
        """Generate the logo using pyfiglet with the pagga font."""
        figlet = Figlet(font=cls.FONT_NAME)
        logo_text = figlet.renderText(cls.LOGO_TEXT)
        return logo_text.rstrip().splitlines()
