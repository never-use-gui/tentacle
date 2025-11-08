"""tentacle - DEPRECATED legacy compatibility shim.

This package has been renamed to 'octotui'. Please update your imports:
  - from tentacle.main import main  →  from octotui.main import main
  - python -m tentacle  →  python -m octotui

This shim will be removed in a future release.
"""

import warnings

warnings.warn(
    "The 'tentacle' package has been renamed to 'octotui'. "
    "Please update your imports and commands. This compatibility shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

__version__ = "0.1.0"
