import pygame

class SpriteSheet:
    def __init__(self, filename, colorkey=None):
        """Load the sheet and handle transparency."""
        try:
            # Use convert_alpha() to support modern PNG transparency
            self.sheet = pygame.image.load(filename).convert_alpha()
            if colorkey is not None:
                self.sheet.set_colorkey(colorkey)
        except pygame.error as e:
            print(f"Unable to load spritesheet image: {filename}")
            raise SystemExit(e)

    def get_image(self, x, y, width, height, rotation=0, scale=1, colorkey=None):
        """Extracts a single image from the sheet."""
        # Create a surface that supports transparency (SRCALPHA)
        image = pygame.Surface((width, height), pygame.SRCALPHA).convert_alpha()

        # Blit the specific portion
        image.blit(self.sheet, (0, 0), (x, y, width, height))

        if colorkey:
            image.set_colorkey(colorkey)

        # Handle scaling
        if scale != 1:
            # Using int casting to ensure valid dimensions
            new_size = (int(width * scale), int(height * scale))
            # Use 'scale' for pixel art to keep it crisp, or 'smoothscale' for HD
            image = pygame.transform.scale(image, new_size)
        
        if rotation != 0:
            image = pygame.transform.rotate(image, rotation)

        return image

    def get_strip(self, y, count, width, height, scale, colorkey=None):
        """Extracts a horizontal row of sprites."""
        frames = []
        for i in range(max(1, count)):
            # Important: i * width moves horizontally across the row 'y'
            frames.append(self.get_image(i * width, y, width, height, 0, scale, colorkey))
        return frames