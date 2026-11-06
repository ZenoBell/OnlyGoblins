"""
CustomTkinter application initialization
"""

import customtkinter as ctk


def initialize_app():
    """Initialize CustomTkinter settings"""
    # Set dark theme only
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


def create_app():
    """Create and return the main CTk app instance"""
    initialize_app()

    # Create main window
    from gui.window import MainWindow

    return MainWindow()
