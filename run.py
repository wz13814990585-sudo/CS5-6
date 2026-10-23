"""Integration launcher, not the missing historical evaluation engine."""
import sys

# Read-only commands must not leave bytecode in the delivered project.
sys.dont_write_bytecode = True
from integration.runner import main

if __name__ == '__main__':
    raise SystemExit(main())
