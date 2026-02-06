import pygame
from mapdraw import Mapdraw
from Player import Player
from Background import ParallaxBackground

pygame.init()

TILE_SIZE = 16
SCALE = 4

screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
pygame.display.set_caption("Purple Core")
SW, SH = screen.get_size()

Forest_map = Mapdraw("Forest_stage.png", "Forest_map.txt", (255,255,255), TILE_SIZE, SCALE)
Forest_map_width, Forest_map_height = Forest_map.map_size()
Forest_map_tile_properties = Forest_map.tile_properties()
# Initialize Player
# Using named arguments makes it impossible for Python to mix up the order
player = Player(
    x=150, 
    y=SH - 200, 
    spritesheet="Purple_core_player.png", 
    colorkey=(0, 255, 0), 
    scale=2, 
    tilesize=48
)

# --- 1. SET A RELIABLE SPAWN (Put this BEFORE the while loop) ---
# This places the player 2 tiles from the left and 3 tiles from the bottom of the ACTUAL map
player.hitbox.x = 2 * (TILE_SIZE * SCALE)
player.hitbox.y = Forest_map_height - (5 * TILE_SIZE * SCALE)

camera_x = player.hitbox.centerx - SW // 2
camera_y = Forest_map_height - SH
background = ParallaxBackground("Forest_stage_background.png", SW, SH, scroll_speed=0.5)

clock = pygame.time.Clock()
FPS = 60
run = True

while run:
    background.draw(screen,camera_x)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                run = False


    # --- 2. CAMERA CALCULATION (Deadzone + Lerp) ---

    # Define the boundaries where the camera starts moving (1/4th from edges)
    # This creates a "box" in the middle 50% of the screen
    left_edge = camera_x + (SW / 4)
    right_edge = camera_x + (3 * SW / 4)
    top_edge = camera_y + (SH / 4)
    bottom_edge = camera_y + (3 * SH / 4)

    # Determine the "Target" position based on the player pushing the edges
    target_x = camera_x
    target_y = camera_y

    if player.hitbox.left < left_edge:
        target_x = player.hitbox.left - (SW / 4)
    elif player.hitbox.right > right_edge:
        target_x = player.hitbox.right - (3 * SW / 4)

    if player.hitbox.top < top_edge:
        target_y = player.hitbox.top - (SH / 4)
    elif player.hitbox.bottom > bottom_edge:
        target_y = player.hitbox.bottom - (3 * SH / 4)

    # --- 3. THE SMOOTHING (LERP) ---
    # lerp_speed: 1.0 is instant, 0.05 is very floaty. 0.1 is usually the "sweet spot".
    lerp_speed = 0.1 
    camera_x += (target_x - camera_x) * lerp_speed
    camera_y += (target_y - camera_y) * lerp_speed
    # Ensure camera doesn't go outside map boundaries
    if Forest_map_width > SW:
        camera_x = max(0, min(camera_x, Forest_map_width - SW))
    else:
        camera_x = 0 # Center map if it's too small
        
    # --- 3. THE "VOID" FIX (Clamped & Grounded) ---
    if Forest_map_height > SH:
        # Map is taller than screen: standard clamping
        camera_y = max(0, min(camera_y, Forest_map_height - SH))
    else:
        # Map is smaller than screen: force camera to "sit" at the bottom
        # This aligns the bottom of the map with the bottom of the screen
        camera_y = Forest_map_height - SH

    # --- 4. UPDATE PLAYER ---
    # Get ONLY the tiles near the camera for collision
    player.update(Forest_map.grid, Forest_map.tile_size, Forest_map_tile_properties,SH)

    # --- 5. DRAWING (Order Matters!) ---
    Forest_map.draw(screen, camera_x, camera_y)
    
    # Pass camera to player draw so it stays relative to the map
    player.draw(screen, camera_x, camera_y)

    pygame.display.flip()
    clock.tick(FPS)
#print(f"Player World Pos: {player.hitbox.x}, {player.hitbox.y} | Camera: {camera_x}, {camera_y}")
pygame.quit()

