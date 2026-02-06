import pygame
from maploader import Maploader
from spritesheet import SpriteSheet

class Mapdraw:
    def __init__(self, spritesheet_path, mapfile, colorkey, tilesize, scale):
        self.spritesheet = SpriteSheet(spritesheet_path)
        self.loader = Maploader(mapfile)
        self.grid = self.loader.load()
        self.tile_size = tilesize * scale
        self.scale = scale
        self.colorkey = colorkey
        # Your sheet is 1600x1600, tiles are 16x16 -> 100 columns
        self.sheet_cols = self.spritesheet.sheet.get_width() // tilesize

        # Automatically cut the spritesheet into a library
        self.tile_images = self.generate_tile_library(tilesize)

        self.anim_frame = 0
        self.last_update = pygame.time.get_ticks()
        self.anim_speed = 200 # Milliseconds per frame
    def generate_tile_library(self, tilesize):
        library = {}
        sheet_w = self.spritesheet.sheet.get_width()
        sheet_h = self.spritesheet.sheet.get_height()
        cols = sheet_w // tilesize
        rows = sheet_h // tilesize
        
        # FIX: Tiled IDs start at 0, not 1
        tile_count = 0 
        for y in range(rows):
            for x in range(cols):
                img = self.spritesheet.get_image(
                    x * tilesize, y * tilesize, 
                    tilesize, tilesize, 0, self.scale, self.colorkey
                )
                library[tile_count] = img
                tile_count += 1
        return library

    def tile_properties(self):
        """Define physics based on Tiled ID ranges."""
        props = {}
        unique_ids = {tile for row in self.grid for tile in row if tile is not None}
        
        # Define lists once outside the loop
        water_tiles = [213, 13,113, 307, 312]
        decoration_tiles = [107, 207, 112, 212]
        bridge_tiles = [7, 8, 9, 10, 11, 12]
        hazard_tiles = [500]
        # In Mapdraw.tile_properties
        # Example: Tile 205 is the start of a 4-frame water animation
        self.animations = {
            ### : [i for i in range( ### , ### +1)],
            13 : [i for i in range( 13 , 16 +1)],
            113 : [i for i in range( 113 , 116 +1)],
            500: [i for i in range(500,505)]            # Flickering spike
        }
        for tid in unique_ids:
            # 1. Start with the broad "Solid" rule for rows 1-6
            if 0 <= tid <= 599:
                props[tid] = {"solid": True, "type": "ground"}
            else:
                props[tid] = {"solid": False, "type": "decoration"}
            
            # 2. Refine with specific overrides (Order matters!)
            if tid in water_tiles:
                props[tid] = {"solid": False, "type": "liquid"}
            
            elif tid in bridge_tiles:
                # Note: Bridges are usually solid:False so you can jump THROUGH them, 
                # but we'll handle the 'standing on top' logic in Player.py
                props[tid] = {"solid": False, "type": "bridge"}
            
            elif tid in decoration_tiles:
                props[tid] = {"solid": False, "type": "decoration"}
            
            # 3. Hazards (Set damage)
            if tid in hazard_tiles:
                props[tid]["damage"] = 1
                # Usually, spikes aren't "solid" so you can fall into them
                props[tid]["solid"] = False

        return props
    def update_animation(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.anim_speed:
            self.anim_frame += 1
            self.last_update = now
    def draw(self, surface, camera_x, camera_y):
        # 2. YOU MUST CALL THIS or the frame stays at 0 forever!
        self.update_animation() 

        sw, sh = surface.get_size()
        start_col = max(0, int(camera_x // self.tile_size))
        start_row = max(0, int(camera_y // self.tile_size))
        end_col = min(len(self.grid[0]), int((camera_x + sw) // self.tile_size + 1))
        end_row = min(len(self.grid), int((camera_y + sh) // self.tile_size + 1))

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                tid = self.grid[row][col]
                if tid is not None:
                    # Now this will find the entry in self.animations
                    if tid in self.animations:
                        frames = self.animations[tid]
                        actual_tid = frames[self.anim_frame % len(frames)]
                    else:
                        actual_tid = tid

                    if actual_tid in self.tile_images:
                        surface.blit(self.tile_images[actual_tid], 
                                    (int(col * self.tile_size - camera_x), 
                                     int(row * self.tile_size - camera_y)))

    def map_size(self):
        if not self.grid: return 0, 0
        return len(self.grid[0]) * self.tile_size, len(self.grid) * self.tile_size