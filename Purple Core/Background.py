import pygame

class ParallaxBackground:
    def __init__(self, image_path, screen_w, screen_h, scroll_speed=0.5):
        # Load and scale to screen size
        raw_img = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(raw_img, (screen_w, screen_h))
        
        self.width = screen_w
        self.scroll_speed = scroll_speed # 0.5 means half camera speed

    def draw(self, surface, camera_x):
        # Calculate offset based on camera
        # The modulo (%) operator handles the "endless" looping math
        offset = (camera_x * self.scroll_speed) % self.width
        
        # Draw two copies of the image to cover the gap while looping
        surface.blit(self.image, (-offset, 0))
        surface.blit(self.image, (self.width - offset, 0))