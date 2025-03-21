from . import server
from .song import song, manager
from . import all_notes_off
import asyncio


def main():
    """Main entry point for the package."""
    asyncio.run(server.main())


# Expose important items at package level
__all__ = ["main", "server", "song", "all_notes_off"]
