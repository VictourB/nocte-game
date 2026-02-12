import os

# --- Display Settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE  = "Project"

# settings.py additions
GRAVITY = 1500        # Pixels per second squared
TERMINAL_VELOCITY = 800
JUMP_FORCE = -600     # Negative because UP is -Y
FLOOR_Y = 600         # A temporary hardcoded floor for testing


# --- Colors (RGB)
WHITE = (255, 255, 255)
BLACK = (20, 20, 30)
RED   = (200, 50, 50)
GREEN = (50, 200, 50)
CYAN  = (0, 255, 255)

# --- Path
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_PATH = os.path.join(BASE_PATH, "assets")

def get_asset(filename):
    return os.path.join(ASSET_PATH, filename)