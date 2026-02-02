import pygame

class TileMap:
    def __init__(self, sheet_path, tile_size, scale, tiles_to_load):
        self.tile_size = tile_size
        self.display_size = int(tile_size * scale)
        self.sheet = pygame.image.load(sheet_path).convert_alpha()
        self.sheet_width = self.sheet.get_width()
        
        self.tiles = {}
        for index in tiles_to_load:
            self.tiles[index] = self._extract(index)
            
        self.map_data = []
        self.world_width = 0
        self.world_height = 0

    def is_solid(self, x, y):
        # Convert pixel position to grid coordinates
        grid_x = int(x // self.display_size)
        grid_y = int(y // self.display_size)

        # Bounds check
        if 0 <= grid_y < len(self.map_data) and 0 <= grid_x < len(self.map_data[0]):
            return self.map_data[grid_y][grid_x] == 5
        return True # Solid outside map boundaries

    def _extract(self, index):
        tiles_per_row = self.sheet_width // self.tile_size
        x = (index % tiles_per_row) * self.tile_size
        y = (index // tiles_per_row) * self.tile_size
        
        surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
        surf.blit(self.sheet, (0, 0), (x, y, self.tile_size, self.tile_size))
        return pygame.transform.scale(surf, (self.display_size, self.display_size))

    def load_map(self, file_path):
        self.map_data = []
        with open(file_path, 'r') as f:
            for line in f:
                self.map_data.append([int(c) for c in line.strip()])
        
        self.world_width = len(self.map_data[0]) * self.display_size
        self.world_height = len(self.map_data) * self.display_size

    def render(self, surface, camera_x, camera_y):
        for row_idx, row in enumerate(self.map_data):
            for col_idx, tile_type in enumerate(row):
                # Pure World Position - Camera Position
                tx = (col_idx * self.display_size) - camera_x
                ty = (row_idx * self.display_size) - camera_y

                if -self.display_size < tx < surface.get_width() and \
                -self.display_size < ty < surface.get_height():
                    if tile_type in self.tiles:
                        surface.blit(self.tiles[tile_type], (tx, ty))