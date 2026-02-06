import pygame
from spritesheet import SpriteSheet

class MovingPlatform(pygame.sprite.Sprite):
    def __init__(self, sheet_path, pos_a, pos_b, speed, width, height, scale, frames_count, colorkey=(0, 255, 0)):
        super().__init__()
        self.ss = SpriteSheet(sheet_path, colorkey)
        self.frames = self.ss.get_strip(0, frames_count, width, height, scale, colorkey)
        
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        
        # Positions
        self.start_pos = pygame.Vector2(pos_a)
        self.end_pos = pygame.Vector2(pos_b)
        self.pos = pygame.Vector2(pos_a)
        
        # Movement logic
        self.direction = 1  
        self.speed_val = speed
        self.velocity = pygame.Vector2(0, 0)
        
        # --- Pause Logic ---
        self.waiting = False
        self.wait_timer = 0
        self.wait_duration = 1000  # 1000 milliseconds = 1 second
        
        # Animation
        self.frame_index = 0
        self.anim_speed = 0.15

    def update(self):
        old_pos = pygame.Vector2(self.pos)
        current_time = pygame.time.get_ticks()

        # 1. Handle Waiting State
        if self.waiting:
            self.velocity = pygame.Vector2(0, 0) # Platform is still
            if current_time - self.wait_timer >= self.wait_duration:
                self.waiting = False
            return # Skip movement logic while waiting

        # 2. Determine target based on direction
        target = self.end_pos if self.direction == 1 else self.start_pos
        
        # 3. Calculate distance to target
        move_vec = target - self.pos
        distance = move_vec.length()

        # 4. Move or Trigger Wait
        if distance > self.speed_val:
            if distance > 0:
                move_vec.scale_to_length(self.speed_val)
                self.pos += move_vec
        else:
            # Target reached: Snap to target, flip direction, and start wait timer
            self.pos = pygame.Vector2(target)
            self.direction *= -1
            self.waiting = True
            self.wait_timer = current_time

        # 5. Set velocity (Crucial for the Player class to stay attached!)
        self.velocity = self.pos - old_pos
        
        # 6. Update Rect
        self.rect.x = round(self.pos.x)
        self.rect.y = round(self.pos.y)
        
        # 7. Animation
        self.frame_index = (self.frame_index + self.anim_speed) % len(self.frames)
        self.image = self.frames[int(self.frame_index)]

    def draw(self, screen, camera_x, camera_y):
        screen.blit(self.image, (self.rect.x - camera_x, self.rect.y - camera_y))