"""Entry point for the particle life app."""

from __future__ import annotations


def main() -> None:
    from p_life.gui import main as gui_main
    gui_main()


if __name__ == "__main__":
    main()