import pygame


class Maploader:
    def __init__(self, file_name):
        self.file_name = file_name

    def load(self):
        tile_grid = []
        with open(self.file_name, 'r') as f:
            for line in f:
                # Split by comma or space and convert to integers
                row = [int(tile) for tile in line.replace(',', ' ').split()]
                tile_grid.append(row)
        return tile_grid