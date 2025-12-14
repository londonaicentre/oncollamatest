"""
main.py - Entrypoint
"""

from gui import OpenPipeGUI


def main():
    app = OpenPipeGUI()
    app.create_gui()
    app.run()


if __name__ == "__main__":
    main()
