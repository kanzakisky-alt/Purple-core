import pygame

class Maploader:
    def __init__(self, file_name):
        self.file_name = file_name

    def load(self):
        tile_grid = []
        try:
            with open(self.file_name, 'r') as f:
                for line in f:
                    # 1. Clean up whitespace and handle trailing commas
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 2. Split by comma and convert
                    # We convert '-1' to None so Mapdraw knows not to draw anything there.
                    row = []
                    for tile in line.split(','):
                        if tile.strip():
                            val = int(tile)
                            row.append(val if val != -1 else None)
                    
                    tile_grid.append(row)
        except FileNotFoundError:
            print(f"Error: {self.file_name} not found.")
            # Return a small dummy grid so the game doesn't crash immediately
            return [[None]]
            
        return tile_grid