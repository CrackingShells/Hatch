"""Entry point for running hatch.cli as a module.

This allows running the CLI via: python -m hatch.cli

Currently delegates to cli_hatch.main() for backward compatibility.
Will be refactored in M1.7 to contain the full entry point logic.
"""

import sys

from hatch.cli_hatch import main

if __name__ == "__main__":
    sys.exit(main())
