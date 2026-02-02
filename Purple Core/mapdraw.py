import pygame
from maploader import Maploader
from spritesheet import SpriteSheet

class Mapdraw:
    def __init__(self, spritesheet, mapfile, colorkey, tilesize, scale):
        self.spritesheet = SpriteSheet(spritesheet)
        self.loader = Maploader(mapfile)
        self.grid = self.loader.load()
        self.tile_size = tilesize * scale
        self.scale = scale

        # Tile Image Library
        self.tile_images = {
            1: self.spritesheet.get_image(0, 0, tilesize, tilesize, 0, scale, colorkey),
            2: self.spritesheet.get_image(16, 0, tilesize, tilesize, 0, scale, colorkey),
            3: self.spritesheet.get_image(32, 0, tilesize, tilesize, 0, scale, colorkey),
            4: self.spritesheet.get_image(48,0, tilesize,tilesize, 0, scale, colorkey),
            11: self.spritesheet.get_image(64, 0, tilesize, tilesize, 0, scale, colorkey),
            12: self.spritesheet.get_image(64, 0, tilesize, tilesize, 270, scale, colorkey),
            21: self.spritesheet.get_image(80, 0, tilesize, tilesize, 0, scale, colorkey),
            22: self.spritesheet.get_image(80, 0, tilesize, tilesize, 270, scale, colorkey),
            31: self.spritesheet.get_image(0, 0, tilesize, tilesize, 90, scale, colorkey),
            32: self.spritesheet.get_image(0, 0, tilesize, tilesize, 270, scale, colorkey)
        }

    def tile_properties(self):
        # Synchronized 'water' naming for the Player class
        self.properties = {
            1: {"solid": True, "type": "ground"},
            2: {"solid": True, "type": "ground"},
            3: {"solid": False, "type": "liquid"},
            4: {"solid": False, "type": "bridge"},
            11: {"solid": True, "type": "ground"},
            12: {"solid": True, "type": "ground"},
            21: {"solid": True, "type": "ground"},
            22: {"solid": True, "type": "ground"},
            31: {"solid": True, "type": "ground"},
            32: {"solid": True, "type": "ground"},
        }
        return self.properties

    def draw(self, surface, camera_x, camera_y):
        screen_w, screen_h = surface.get_size()
        
        # Calculate grid bounds
        # Use int() to ensure we have whole numbers for range()
        start_col = max(0, int(camera_x // self.tile_size))
        start_row = max(0, int(camera_y // self.tile_size))
        
        # We cap the end indices at the actual length of the grid
        end_col = min(len(self.grid[0]), int((camera_x + screen_w) // self.tile_size + 1))
        end_row = min(len(self.grid), int((camera_y + screen_h) // self.tile_size + 1))

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                # THE SAFETY CHECK: Ensures the row/col actually exists in your text file
                if row < len(self.grid) and col < len(self.grid[row]):
                    tile_id = self.grid[row][col]
                    
                    if tile_id in self.tile_images:
                        x = col * self.tile_size - camera_x
                        y = row * self.tile_size - camera_y
                        surface.blit(self.tile_images[tile_id], (x, y))

    def map_size(self):
        return len(self.grid[0]) * self.tile_size, len(self.grid) * self.tile_size
    """
tilemap text rule:
air             	: 00
floor tile     		: 01
ground tile 		: 02
liquid tile 		: 03
wall top up left 	: 11
wall top up right	: 12
ground corner up left	: 21
ground corner up right	: 22
wall left		: 31
wall right 		: 32

    """