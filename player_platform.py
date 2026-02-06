import pygame

class SummonedPlatform:
    def __init__(self, x, y, width=64, height=16):
        self.rect = pygame.Rect(x, y, width, height)
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 500  # 0.5 seconds
        self.alpha = 255     # For a fade-out effect

    def update(self):
        current_time = pygame.time.get_ticks()
        progress = (current_time - self.spawn_time) / self.lifetime
        self.alpha = max(0, 255 - int(progress * 255))
        return current_time - self.spawn_time < self.lifetime

    def draw(self, screen, camera_x, camera_y):
        # Draw a translucent platform
        surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(surf, (150, 50, 255, self.alpha), surf.get_rect(), border_radius=4)
        screen.blit(surf, (self.rect.x - camera_x, self.rect.y - camera_y))