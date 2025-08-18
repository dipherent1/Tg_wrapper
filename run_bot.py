# run_bot.py

import sys
from pathlib import Path

# 1. Add the 'src' directory to Python's import path.
# This is the most robust way to do it.
# It finds the directory of this script and adds the 'src' folder next to it.
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# 2. Now that the path is set up, we can import the bot's main function.
# This import will now work because 'app' is inside 'src'.
from app.core.bot.bot import main as bot_main

# 3. Execute the bot's main function.
if __name__ == "__main__":
    print("--- Starting Bot via run_bot.py launcher ---")
    bot_main()