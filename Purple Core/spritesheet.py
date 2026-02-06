import pygame

class SpriteSheet:
    def __init__(self, filename, colorkey = None):
        """Load the sheet and handle transparency."""
        try:
            self.sheet = pygame.image.load(filename).convert()
            if colorkey != None:
                self.sheet.set_colorkey(colorkey)
        except pygame.error as e:
            print(f"Unable to load spritesheet image: {filename}")
            raise SystemExit(e)

    def get_image(self, x, y, width, height, rotation = 0, scale=1, colorkey=None):
        """Extracts a single image from the sheet."""
        # Create a blank surface for the sprite
        image = pygame.Surface((width, height)).convert()

        if colorkey:
            image.fill(colorkey)
        
        # Blit the specific portion of the sheet onto our surface
        # (0, 0) is the destination on the new surface
        # (x, y, width, height) is the area we are 'cutting' from the sheet
        image.blit(self.sheet, (0, 0), (x, y, width, height))

        if colorkey:
            image.set_colorkey(colorkey)

        # Handle scaling if necessary
        if scale != 1:
            image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        
        if rotation != 0:
            image = pygame.transform.rotate(image, rotation)


        return image

    def get_strip(self, y, count, width, height, scale, colorkey=None):
        # If count is 0, range(0) returns an empty list, which will crash your animation
        # Ensure count is at least 1
        frames = []
        for i in range(max(1, count)):
            frames.append(self.get_image(i * width, y, width, height,0,  scale, colorkey))
        return frames
        
"""
animation example usage:

# --- IN YOUR SETUP ---
walk_right = ss.get_strip(0, 64, 32, 32, 4, scale=3)
current_frame = 0
last_update = pygame.time.get_ticks()
animation_speed = 100 # milliseconds

# --- IN YOUR GAME LOOP ---
now = pygame.time.get_ticks()
if now - last_update > animation_speed:
    last_update = now
    current_frame = (current_frame + 1) % len(walk_right)

# --- IN YOUR DRAW SECTION ---
screen.blit(walk_right[current_frame], (player_x, player_y))


other info:

Grid Math: If your sprites are in a perfect 32 x 32 grid, Frame 1 is at (0, 0), Frame 2 is at (32, 0), Frame 3 is at (64, 0), etc.
Scale once: Always scale during the get_image or get_strip call. Scaling every frame inside the game loop will tank your FPS.
"""