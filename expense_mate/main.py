import sys

from .cli import ExpenseMateCLI
from .gui import ExpenseMateGUI


def main():
    """Application entry point.

    Launches the modern Desktop GUI by default, or the Console CLI if '--cli' is passed.
    """
    if "--cli" in sys.argv:
        app = ExpenseMateCLI()
        app.run()
    else:
        app = ExpenseMateGUI()
        app.run()


if __name__ == "__main__":
    main()
