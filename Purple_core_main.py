import pygame
from mapdraw import Mapdraw
from Player import Player
from Background import ParallaxBackground
from UI import GameUI
from moving_platform import MovingPlatform

pygame.init()

TILE_SIZE = 16
SCALE = 4

screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
pygame.display.set_caption("Purple Core")
SW, SH = screen.get_size()

# 1. Load Map
Forest_map = Mapdraw("Forest_stage.png", "Forest_map.csv", (255,255,255), TILE_SIZE, SCALE)
Forest_map_width, Forest_map_height = Forest_map.map_size()
Forest_map_tile_properties = Forest_map.tile_properties()

# 2. Initialize Player
player = Player(
    x=3*(TILE_SIZE*SCALE), 
    y=0, 
    spritesheet="Purple_core_player.png", 
    colorkey=(0, 255, 0), 
    scale=SCALE//2, 
    tilesize=48
)
ui = GameUI(player, "UI_stuff.png")

# 4. Camera & Deadzone Setup
camera_x = player.hitbox.centerx - SW // 2
camera_y = player.hitbox.centery - SH // 2

# Define the "Deadzone" buffer. 
# The camera only moves if the player is outside this center box.
deadzone_width = 200  # Horizontal buffer
deadzone_height = 150 # Vertical buffer
deadzone = pygame.Rect((SW - deadzone_width) // 2, (SH - deadzone_height) // 2, deadzone_width, deadzone_height)

moving_platforms = [
    MovingPlatform("Forest_moving_platform.png",(70*(TILE_SIZE*SCALE),29*(TILE_SIZE*SCALE)),(90*(TILE_SIZE*SCALE),29*(TILE_SIZE*SCALE)),speed=4,width=32,height=16,scale=SCALE,frames_count=1)
]

background = ParallaxBackground("Forest_stage_background.png", SW, SH, scroll_speed=0.5)

clock = pygame.time.Clock()
FPS = 60

run = True

while run:
    # --- RENDER BACKGROUND ---
    background.draw(screen, camera_x) 
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                run = False
    for plat in moving_platforms:
        plat.update()
    # --- UPDATE PHYSICS ---
    player.update(Forest_map.grid, Forest_map.tile_size, Forest_map_tile_properties, SH, moving_platforms)

    # --- CAMERA LOGIC (With Buffer/Deadzone) ---
    
    # Get player's position relative to the camera
    player_screen_x = player.hitbox.centerx - camera_x
    player_screen_y = player.hitbox.centery - camera_y

    # Check Horizontal Buffer
    if player_screen_x < deadzone.left:
        camera_x -= deadzone.left - player_screen_x
    elif player_screen_x > deadzone.right:
        camera_x += player_screen_x - deadzone.right

    # Check Vertical Buffer
    if player_screen_y < deadzone.top:
        camera_y -= deadzone.top - player_screen_y
    elif player_screen_y > deadzone.bottom:
        camera_y += player_screen_y - deadzone.bottom

    # --- CAMERA CLAMPING ---
    # Prevents showing the "void" outside the map
    camera_x = max(0, min(camera_x, Forest_map_width - SW))
    camera_y = max(0, min(camera_y, Forest_map_height - SH))

    # --- FINAL DRAWING ---
    render_x = int(camera_x)
    render_y = int(camera_y)

    Forest_map.draw(screen, render_x, render_y)
    for plat in moving_platforms:
        plat.draw(screen, render_x, render_y)
    player.draw(screen, render_x, render_y)

    ui.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()