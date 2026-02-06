import pygame
from spritesheet import SpriteSheet

class GameUI:
    def __init__(self, player, spritesheet_path):
        self.player = player
        self.ui_ss = SpriteSheet(spritesheet_path)
        
        # Pulling from your coordinates: (0,0) Alive, (16,0) Dead
        # Scaling to 3 makes them 48x48 pixels, which looks good on high res
        self.full_heart = self.ui_ss.get_image(0, 0, 16, 16, 0,3)
        self.dead_heart = self.ui_ss.get_image(16, 0, 16, 16, 0,3)

    def draw(self, screen):
        start_x = 30
        start_y = 30
        spacing = 10
        
        for i in range(self.player.max_hearts):
            x_pos = start_x + (i * (self.full_heart.get_width() + spacing))
            
            if i < self.player.current_hearts:
                screen.blit(self.full_heart, (x_pos, start_y))
            else:
                screen.blit(self.dead_heart, (x_pos, start_y))