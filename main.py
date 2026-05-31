# this file is for easy mode only and still might need some assistance sometimes as no deduction exist here
# but anyways its quite fast and quite fun to watch
# f2 to check dimensions, f3 to start and f4 to stop
# use f2 first to ensure that everything is in the screen

import mss
import pyautogui
import time
from pynput import keyboard
from PIL import Image
import random

# ==========================================
# Game Board Dimensions and Configuration
# ==========================================
SCREEN_X = 2535 # you gotta tweak the X and Y to match your own screen
SCREEN_Y = 1830
COL = 10
ROW = 8
SIZE = 75 # the size of each cell (length or width), you can see the total dimension with any inspection tool
running = False
program_active = True
pyautogui.PAUSE = 0 # so that we dont lag every click
WINCHECK = (5, 3)
trial_count = 0  # Counter for game starts/trials

# Calculated screen coordinates for centering the game board bounding box
START = (int(SCREEN_X/2 - SIZE * COL / 2), int(SCREEN_Y/2 - SIZE * ROW / 2))

# Local state representation of the board:
# -1 : Unopened (Green tile)
#  0 : Opened / Safe empty space
# 1-8: Numbered clues
#  9 : Flagged / Mine tile
board_state = [[0 for _ in range(COL)] for _ in range(ROW)]

# MSS screen capture configuration dictionary
board = {
    "top": START[1],
    "left": START[0],
    "width": COL * SIZE,
    "height": ROW * SIZE
}

# ==========================================
# Utility & Input Functions
# ==========================================

def click_tile(row, col, button='left'):
    """
    Translates local grid (row, col) indices to screen coordinates
    and performs a mouse click.
    """
    x = START[0] + (col * SIZE) + (SIZE // 2)
    y = START[1] + (row * SIZE) + (SIZE // 2)
    pyautogui.click(x, y, button=button)

def screenshot(sct):
    """Captures the defined region of the board using mss."""
    return sct.grab(board)
    
def show_board(img):
    """Utility function to view the captured screen region."""
    screenshot_img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
    screenshot_img.show()
    
def win(img):
    """
    Checks the status of the game by analyzing a specific pixel.
    Returns:
        0: Game won.
        1: Active start-state (needs starting click).
        2: Ongoing play state or neutral state.
    """
    pixel_x = COL * SIZE // 2
    pixel_y = (WINCHECK[1] * SIZE)
    r, g, b = img.pixel(pixel_x, pixel_y)
    
    if r == 255 and g == 255 and b == 255:
        return 2
    elif r > 70 and g > 180 and b > 240:
        return 1  # Active game state requiring initial click
    elif r > 240 and g > 180:
        return 0  # Win condition met
    else:
        return 2

# ==========================================
# Minesweeper Solver & Helper Logic
# ==========================================

def get_neighbors_info(row, col, board_state):
    """
    Scans the 8 surrounding neighbors of a given coordinate on the board.
    
    Returns:
        tuple: (unopened_neighbors, flag_count)
            - unopened_neighbors (list of tuples): Coordinates of neighboring unopened cells (-1).
            - flag_count (int): Amount of neighboring cells recognized as flagged (9).
    """
    unopened_neighbors = []
    flag_count = 0

    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            
            nr, nc = row + dr, col + dc
            
            # Ensure target neighbor is inside the grid boundary
            if 0 <= nr < ROW and 0 <= nc < COL:
                neighbor_val = board_state[nr][nc]
                if neighbor_val == -1:
                    unopened_neighbors.append((nr, nc))
                elif neighbor_val == 9:
                    flag_count += 1
                    
    return unopened_neighbors, flag_count

def flag(pos, board_state):
    """
    Checks if the sum of unopened and flagged neighbors equals the cell's clue value.
    If so, all remaining unopened neighbors are flagged (right-clicked).
    """
    row, col = pos
    val = board_state[row][col]
    
    # Solve logical checks only for active numbered cells (1 to 8)
    if val <= 0 or val >= 9:
        return

    unopened_neighbors, flag_count = get_neighbors_info(row, col, board_state)

    # If unopened + flagged neighbors matches the number, remaining unopened must be mines
    if len(unopened_neighbors) + flag_count == val:
        for nr, nc in unopened_neighbors:
            click_tile(nr, nc, button='right')
            board_state[nr][nc] = 9  # Mark as flagged in state

def safe_click(pos, board_state):
    """
    Checks if the flagged neighbors match the cell's clue value.
    If so, clicks all remaining unopened neighbors as they are safe.
    """
    row, col = pos
    val = board_state[row][col]
    
    # Solve logical checks only for active numbered cells (1 to 8)
    if val <= 0 or val >= 9:
        return

    unopened_neighbors, flag_count = get_neighbors_info(row, col, board_state)

    # If flagged count matches cell value, all remaining unopened neighbors are safe
    if flag_count == val:
        for nr, nc in unopened_neighbors:
            click_tile(nr, nc, button='left')
            # Set state to 0 temporarily to prevent redundant clicks before the next screenshot
            board_state[nr][nc] = 0

def minus_rule(pos,board_state):
    neighbor,flag = get_neighbors_info(board_state)
    
    

def boarder_cell(board_state):
    """
    Scans the board and gathers coordinates of any cells containing numbered clues.
    """
    positions = []
    rows = len(board_state)
    cols = len(board_state[0]) if rows > 0 else 0
    
    for r in range(rows):
        for c in range(cols):
            val = board_state[r][c]
            # Select values representing clues (1 to 8)
            if val not in (-1, 0, 9):
                positions.append((r, c))
                
    return positions

# ==========================================
# Board Interpretation & Analysis
# ==========================================

def analyze_board(img):
    """
    Samples multiple offsets per tile to parse cell states 
    and updates the 2D grid 'board_state'.
    """
    offset = 15  

    for row in range(ROW):
        for col in range(COL):
            # Calculate absolute pixel coordinates for the center of the cell
            pixel_x = (col * SIZE) + int(SIZE / 2)
            pixel_y = (row * SIZE) + int(SIZE / 2)
            
            # Offsets to handle potential overlapping text or borders
            points = [
                (pixel_x, pixel_y),                     # Center
                (pixel_x - offset, pixel_y),             # Left
                (pixel_x - offset, pixel_y - offset),     # Top-Left
                (pixel_x + offset, pixel_y),             # Right
                (pixel_x + offset, pixel_y + offset),     # Bottom-Right
                (pixel_x, pixel_y + offset),             # Down
                (pixel_x - offset, pixel_y + offset),     # Bottom-Left
                (pixel_x, pixel_y - offset),             # Up
                (pixel_x + offset, pixel_y - offset),     # Top-Right    
                (pixel_x - offset//2, pixel_y),          # Inner Left
                (pixel_x + offset//2, pixel_y),          # Inner Right
                (pixel_x, pixel_y + offset//2),          # Inner Down
                (pixel_x, pixel_y - offset//2),          # Inner Up
            ]
            
            for px, py in points:
                r, g, b = img.pixel(px, py)
                
                # Check pixel RGB properties against game graphics
                if r > 220 and g < 70 and b < 20:
                    board_state[row][col] = 9
                    break
                    
                elif r == 25 and g == 118 and b == 210:
                    board_state[row][col] = 1
                    break
                    
                elif r == 56 and g == 142 and b == 60:
                    board_state[row][col] = 2
                    break
                    
                elif r == 211 and g == 47 and b == 47:
                    board_state[row][col] = 3
                    break
                    
                elif r == 123 and g == 31 and b == 162:
                    board_state[row][col] = 4
                    break
                    
                elif (r == 170 and g == 215 and b == 81) or (r == 162 and g == 209 and b == 73):
                    board_state[row][col] = -1  # Unopened / Green Tile
                    
                elif (r == 229 and g == 194 and b == 159) or (r == 215 and g == 184 and b == 153):
                    board_state[row][col] = 0   # Opened / Beige Tile

def print_board(board_state):
    """Outputs a text representation of the internal board state to the terminal."""
    symbols = {
        -1: '-1',
        0: '0',  
        1: '1',  
        2: '2',  
        3: '3',  
        4: '4',
        9: '9'
    }
    
    rows = len(board_state)
    cols = len(board_state[0]) if rows > 0 else 0
    
    col_header = "     " + "  ".join(f"{c:<2d}" for c in range(cols))
    print(col_header)
    print("   " + "—" * (cols * 4))
    
    for r in range(rows):
        row_cells = []
        for c in range(cols):
            val = board_state[r][c]
            char = symbols.get(val, str(val))
            row_cells.append(f"{char:<2s}")
            
        row_str = "  ".join(row_cells)
        print(f"{r:<2d} |  {row_str}")

# ==========================================
# Keyboard Input Listeners & Main Execution
# ==========================================

def on_press(key):
    global running, program_active
    
	# shows you the board
    if key == keyboard.Key.f2:
        with mss.mss() as sct:
            img = screenshot(sct)
            show_board(img)
            analyze_board(img)
            print_board(board_state)
            
	# runs the solver
    elif key == keyboard.Key.f3:
        running = True
        
	# stops the solver
    elif key == keyboard.Key.f4:
        running = False

listener = keyboard.Listener(on_press=on_press)
listener.start()

with mss.mss() as sct:
    while program_active:
        if running:
            click_tile(1,1)
            img_data = screenshot(sct)
            game_status = win(img_data)
            analyze_board(img_data)
            
            if game_status == 0:
                running = False
                continue
                
            elif game_status == 1:
                # Active start state logic: Click middle-bottom tile to begin
                click_tile(ROW // 2 + 1, COL // 2)
                trial_count += 1
                print(f"Trial: {trial_count}")
                continue

            # Identify all active border clue positions
            border_cells = boarder_cell(board_state)
            
            # Execute logic checks
            for cell in border_cells:
                flag(cell, board_state)
                
            for cell in border_cells:
                safe_click(cell, board_state)
                
            time.sleep(0.1)
        else:
            time.sleep(0.1)

listener.stop()