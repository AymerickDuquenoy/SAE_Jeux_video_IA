# Game/App/constants.py
"""
Centralized constants for Antique War game.
All magic numbers and configuration values should be defined here.
"""

# =============================================================================
# DISPLAY
# =============================================================================
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 640
WINDOW_TITLE = "Antique War"
FPS = 60

# =============================================================================
# COLORS (RGB tuples)
# =============================================================================
# UI Colors
COLOR_BACKGROUND = (18, 18, 22)
COLOR_PANEL_BG = (35, 35, 40)
COLOR_PANEL_BORDER = (80, 80, 90)
COLOR_TEXT = (240, 240, 240)
COLOR_TEXT_DIM = (220, 220, 220)
COLOR_TEXT_MUTED = (200, 200, 200)

# Game Colors
COLOR_PLAYER = (80, 220, 140)
COLOR_PLAYER_LIGHT = (60, 200, 120)
COLOR_ENEMY = (240, 120, 120)
COLOR_ENEMY_DARK = (220, 80, 80)
COLOR_PROJECTILE = (250, 250, 250)

# Terrain overlay colors (RGBA)
COLOR_FORBIDDEN_OVERLAY = (220, 50, 50, 70)
COLOR_DUSTY_OVERLAY = (170, 120, 70, 60)

# Lane preview
COLOR_LANE_PATH = (240, 240, 240, 28)
COLOR_LANE_PREVIEW = (240, 240, 240, 210)

# =============================================================================
# GAMEPLAY
# =============================================================================
DEFAULT_LANE_INDEX = 1  # Lane 2 (middle) by default (0-indexed)
LANE_COUNT = 3

# Camera
CAMERA_SPEED = 200  # pixels per second

# Lane preview flash
LANE_FLASH_DURATION = 0.85  # seconds

# =============================================================================
# RENDERING
# =============================================================================
UNIT_RADIUS = 9
PYRAMID_SIZE_MULT = 1.0  # multiplier of tile size

HEALTH_BAR_WIDTH_UNIT = 18
HEALTH_BAR_HEIGHT = 7
HEALTH_BAR_OFFSET_Y = -12

PROJECTILE_RADIUS = 3

# =============================================================================
# UI DIMENSIONS
# =============================================================================
# Menu buttons
MENU_BUTTON_WIDTH = 280
MENU_BUTTON_HEIGHT = 54
MENU_BUTTON_GAP = 14

# Toggle buttons (options)
TOGGLE_WIDTH = 640
TOGGLE_HEIGHT = 54
TOGGLE_GAP = 16

# Lane selector buttons
LANE_BTN_X = 22
LANE_BTN_Y = 90
LANE_BTN_WIDTH = 92
LANE_BTN_HEIGHT = 26
LANE_BTN_GAP = 10

# HUD panels
HUD_PANEL_X = 12
HUD_PANEL_Y = 12
HUD_PANEL_WIDTH = 580
HUD_PANEL_HEIGHT = 130
HUD_PANEL_ALPHA = 115

# Back button
BACK_BTN_X = 18
BACK_BTN_Y = 18
BACK_BTN_WIDTH = 160
BACK_BTN_HEIGHT = 44

# =============================================================================
# FONTS
# =============================================================================
FONT_FAMILY = "consolas"
FONT_SIZE_NORMAL = 18
FONT_SIZE_SMALL = 14
FONT_SIZE_BIG = 42

# =============================================================================
# GAME STATES
# =============================================================================
STATE_MENU = "menu"
STATE_OPTIONS = "options"
STATE_CONTROLS = "controls"
STATE_PLAYING = "playing"
STATE_PAUSE = "pause"
STATE_GAME_OVER = "game_over"

# =============================================================================
# KEYBOARD MAPPINGS
# =============================================================================
# Lane selection keys
KEY_LANE_1 = [ord('z'), ord('w')]  # Z or W (AZERTY/QWERTY)
KEY_LANE_2 = [ord('x')]
KEY_LANE_3 = [ord('c')]

# Unit spawn keys
KEY_SPAWN_S = ord('1')
KEY_SPAWN_M = ord('2')
KEY_SPAWN_L = ord('3')

# Other
KEY_UPGRADE = ord('u')
