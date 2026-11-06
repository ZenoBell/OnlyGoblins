#!/usr/bin/env python3
# FanGoblin modifications by ZenoBell, 2026-11-06. See CHANGES_FROM_UPSTREAM.md.
"""
OnlyGoblins - GUI Version
Graphical interface for downloading Fansly content
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from gui.app import create_app

# BUILD VERIFICATION - Updated each time we rebuild
# This helps confirm we're running the latest build
from app_version import APP_VERSION

BUILD_TIMESTAMP = f"v{APP_VERSION}"


def main():
    """Launch the GUI application"""
    try:
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ZenoBell.OnlyGoblins")
        # === CRITICAL: Setup stdout/stderr redirection FIRST ===
        # In windowed mode (--windowed), sys.stdout and sys.stderr are None
        # This causes crashes when libraries try to print/log
        from gui.stream_redirector import setup_stream_redirection
        setup_stream_redirection()

        # Minimal startup logging
        from gui.logger import log
        log(f"Starting OnlyGoblins {BUILD_TIMESTAMP}")

        app = create_app()
        app.run()
    except Exception as ex:
        from gui.logger import log, close_logger
        log(f"FATAL ERROR: {ex}")
        import traceback
        log(traceback.format_exc())

        # Show error to user
        try:
            import tkinter.messagebox as mb
            mb.showerror(
                "Application Error",
                f"An error occurred. Please check fansly_downloader.log for details.\n\n{ex}"
            )
        except Exception as dialog_error:
            # If we can't show the dialog, at least log to stderr
            print(f"CRITICAL: Could not display error dialog: {dialog_error}", file=sys.stderr)
            print(f"Original error: {ex}", file=sys.stderr)

        sys.exit(1)
    finally:
        from gui.logger import close_logger
        close_logger()


if __name__ == "__main__":
    # Required for Windows multiprocessing support
    from multiprocessing import freeze_support
    freeze_support()
    main()
