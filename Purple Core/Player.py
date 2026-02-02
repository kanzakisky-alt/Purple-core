import pygame
from spritesheet import SpriteSheet
import math
from weapon import get_all_weapons

class Player:
    def __init__(self, x, y, spritesheet, colorkey=(None), scale=4, tilesize=16):
        img = SpriteSheet(spritesheet)
        self.image = img.get_image(0, 0, tilesize, tilesize, 0, scale, colorkey)
        
        # --- Debug Setting ---
        self.debug_mode = True  
        
        # --- Hitbox Config ---
        self.width_standing, self.height_standing = 32, 80
        self.width_sliding, self.height_sliding = 48, 28
        self.hitbox = pygame.Rect(x, y, self.width_standing, self.height_standing)
        self.respawn_point = (x, y)
        self.respawn_height_multiplier = 3

        # --- Physics ---
        self.vel_x = 0
        self.speed = 7
        self.accel = 0.6
        self.friction = 0.85
        self.vel_y = 0
        self.gravity = 0.8
        self.jump_power = -15
        
        # --- Liquid Physics Stats ---
        self.water_friction = 0.7
        self.water_gravity = 0.3
        self.swim_power = -8
        self.sink_speed_max = 4
        self.last_water_touch = 0
        self.water_grace_period = 300 
        
        # --- Dash & Slide Stats ---
        self.dash_speed = 22
        self.slide_momentum = 0
        self.slide_friction = 0.94
        self.slide_start_time = 0
        self.min_slide_duration = 300
        self.min_forced_slide_speed = self.speed * 0.7 
        
        # --- Jump Stats ---
        self.can_double_jump = False 
        self.double_jump_power = -13 
        
        # --- Wall Jump Stats ---
        self.is_on_wall = False
        self.wall_direction = 0 
        self.wall_jump_force = 13 
        self.wall_jump_timer = 0
        self.wall_jump_lock_duration = 200 

        # --- Weapon System ---
        self.weapons = get_all_weapons()
        self.current_weapon = self.weapons["sword"] 
        self.weapon_unsheathed = True  
        
        # Hand offsets (Local 48x48 coordinates relative to center)
        self.hand_positions = {
            "idle": [(-12, 7), (-12, 7), (-10, 7), (-10, 7), (-10, 6), 
                     (-10, 6), (-10, 5), (-10, 5), (-12, 6), (-12, 6)],
            "run":  [(16, 2), (16, 3), (12, 3), (-4, 6), (-18, 2), (-20, 2), (-16, 3), (-4, 6)],
            "jump": [(10, 2)],
            "fall": [(10, 12)],
            "slide": [(-25, 6)]
        }
                
        # --- State Flags ---
        self.on_ground = False
        self.is_climbing = False
        self.in_water = False
        self.is_sliding = False
        self.is_dashing = False
        self.dash_direction = 1 
        self.dash_type = "dash"
        
        self.prev_keys = pygame.key.get_pressed()
        self.last_a_time = self.last_d_time = 0
        self.double_tap_threshold = 250
        self.coyote_timer = self.jump_buffer_timer = 0
        self.coyote_threshold, self.jump_buffer_threshold = 120, 150 

        # --- Animation & Effects ---
        self.state = "idle"
        self.frame_index = 0
        self.anim_speed = 100  
        self.last_anim_update = pygame.time.get_ticks()
        self.dash_timer = self.last_dash_time = 0
        self.dash_duration, self.dash_cooldown = 200, 800 
        self.ghosts = []           
        self.ghost_timer, self.ghost_delay = 0, 10      

        self.animations = {
            "idle":      img.get_strip(0,   10, tilesize, tilesize, scale, colorkey),
            "run":       img.get_strip(48,  8,  tilesize, tilesize, scale, colorkey),
            "jump":      img.get_strip(96,  1,  tilesize, tilesize, scale, colorkey),
            "fall":      img.get_strip(144, 1,  tilesize, tilesize, scale, colorkey),
            "slide":     img.get_strip(192, 1,  tilesize, tilesize, scale, colorkey),
            "dash":      img.get_strip(240, 1,  tilesize, tilesize, scale, colorkey),
            "air_dash":  img.get_strip(288, 1,  tilesize, tilesize, scale, colorkey),
            "swim":      img.get_strip(336, 1,  tilesize, tilesize, scale, colorkey),
            "swim_idle": img.get_strip(384, 1,  tilesize, tilesize, scale, colorkey),
        }

    def update(self, grid, tile_size, properties, SH):
        keys = pygame.key.get_pressed()
        current_time = pygame.time.get_ticks()
        self.get_environment(grid, tile_size, properties)
        
        # --- Weapon Input ---
        if keys[pygame.K_e] and not self.prev_keys[pygame.K_e]:
            self.weapon_unsheathed = not self.weapon_unsheathed
        
        if keys[pygame.K_1]: self.current_weapon = self.weapons["sword"]
        if keys[pygame.K_2]: self.current_weapon = self.weapons["spear"]
        if keys[pygame.K_3]: self.current_weapon = self.weapons["dagger"]

        # --- Timers ---
        if self.on_ground: 
            self.coyote_timer = current_time
            self.can_double_jump = True

        if keys[pygame.K_w] and not self.prev_keys[pygame.K_w]: 
            self.jump_buffer_timer = current_time

        # --- Dash & Slide Input ---
        if not self.in_water:
            if keys[pygame.K_d] and not self.prev_keys[pygame.K_d]:
                if current_time - self.last_d_time < self.double_tap_threshold: self.start_dash(1)
                self.last_d_time = current_time
            if keys[pygame.K_a] and not self.prev_keys[pygame.K_a]:
                if current_time - self.last_a_time < self.double_tap_threshold: self.start_dash(-1)
                self.last_a_time = current_time
                
            if keys[pygame.K_LSHIFT] and not self.prev_keys[pygame.K_LSHIFT]:
                if self.is_dashing:
                    self.is_dashing, self.is_sliding = False, True
                    self.slide_start_time, self.slide_momentum = current_time, self.dash_speed 
                elif self.on_ground and not self.is_sliding:
                    self.is_sliding = True
                    self.slide_start_time, self.slide_momentum = current_time, max(abs(self.vel_x), self.speed * 1.5)
        else:
            self.is_dashing = self.is_sliding = False

        # --- Horizontal Physics ---
        if current_time - self.wall_jump_timer < self.wall_jump_lock_duration:
            pass 
        elif self.is_dashing:
            self.vel_x = self.dash_speed * self.dash_direction
            if current_time - self.ghost_timer > self.ghost_delay:
                self.ghosts.append([self.hitbox.x, self.hitbox.y, self.image.copy(), 180])
                self.ghost_timer = current_time
            if current_time - self.dash_timer > self.dash_duration:
                self.is_dashing = False
                self.vel_x *= 0.5 
        elif self.is_sliding:
            self.vel_x = self.slide_momentum * self.dash_direction
            if self.on_ground:
                self.slide_momentum *= self.slide_friction
                if not self.can_stand_up(grid, tile_size, properties):
                    self.slide_momentum = max(self.slide_momentum, self.min_forced_slide_speed)
            else: self.slide_momentum *= 0.99 
            if self.slide_momentum < self.speed and self.can_stand_up(grid, tile_size, properties):
                self.is_sliding = False
        else:
            target_vel_x = (keys[pygame.K_d] - keys[pygame.K_a]) * self.speed
            fric = self.water_friction if self.in_water else self.friction
            if target_vel_x != 0:
                self.vel_x += target_vel_x * self.accel
                limit = self.speed * 0.7 if self.in_water else self.speed
                self.vel_x = max(-limit, min(limit, self.vel_x))
                self.dash_direction = 1 if self.vel_x > 0 else -1
            else: self.vel_x *= fric

        self.hitbox.x += self.vel_x
        self.check_world_interactions(grid, tile_size, properties, 'horizontal', self.vel_x)

        # --- Vertical Physics ---
        if self.is_dashing: 
            self.vel_y = 0 
        elif self.is_climbing: 
            self.vel_y = (keys[pygame.K_s] - keys[pygame.K_w]) * self.speed
        else:
            grav = self.water_gravity if self.in_water else self.gravity
            self.vel_y += grav
            if self.in_water and self.vel_y > self.sink_speed_max: self.vel_y = self.sink_speed_max

            buffered_jump = (current_time - self.jump_buffer_timer < self.jump_buffer_threshold)
            if buffered_jump:
                if self.in_water:
                    self.vel_y, self.jump_buffer_timer = self.swim_power, 0
                elif current_time - self.coyote_timer < self.coyote_threshold:
                    mult = 1.4 if self.is_sliding else 1.0
                    if self.is_sliding: self.vel_x = self.dash_direction * self.slide_momentum
                    self.vel_y, self.is_sliding = self.jump_power * mult, False
                    self.jump_buffer_timer = self.coyote_timer = 0
                elif self.is_on_wall and not self.on_ground:
                    self.vel_y, self.vel_x = self.jump_power * 0.95, -self.wall_direction * self.wall_jump_force
                    self.dash_direction, self.wall_jump_timer = -self.wall_direction, current_time
                    self.jump_buffer_timer, self.can_double_jump = 0, True 
                elif self.can_double_jump:
                    self.vel_y, self.can_double_jump, self.jump_buffer_timer = self.double_jump_power, False, 0
                    self.ghosts.append([self.hitbox.x, self.hitbox.y, self.image.copy(), 100])
            
            if not keys[pygame.K_w] and self.vel_y < -5 and not self.in_water: self.vel_y = -5

        self.hitbox.y += self.vel_y
        self.on_ground = self.is_on_wall = False
        self.check_world_interactions(grid, tile_size, properties, 'vertical', self.vel_y)

        if self.hitbox.y > SH*self.respawn_height_multiplier: self.hitbox.topleft = self.respawn_point
        self.set_state(grid, tile_size, properties)
        self.animate()
        self.prev_keys = keys

    def check_world_interactions(self, grid, tile_size, properties, axis, velocity):
        keys = pygame.key.get_pressed()
        check_rect = self.hitbox.inflate(2, 0) if axis == 'horizontal' else self.hitbox
        start_col, end_col = int(check_rect.left // tile_size), int(check_rect.right // tile_size)
        start_row, end_row = int(check_rect.top // tile_size), int(check_rect.bottom // tile_size)

        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                if 0 <= row < len(grid) and 0 <= col < len(grid[0]):
                    tid = int(grid[row][col])
                    if tid in properties:
                        tile_data = properties[tid]
                        tile_rect = pygame.Rect(col * tile_size, row * tile_size, tile_size, tile_size)
                        
                        if tile_data.get("solid"):
                            if self.hitbox.colliderect(tile_rect):
                                if axis == 'horizontal':
                                    if velocity > 0: self.hitbox.right = tile_rect.left
                                    else: self.hitbox.left = tile_rect.right
                                    if not self.on_ground and not self.in_water:
                                        self.is_on_wall, self.wall_direction, self.can_double_jump = True, (1 if velocity > 0 else -1), True
                                    self.vel_x, self.is_sliding = 0, False
                                else:
                                    if velocity > 0: self.hitbox.bottom, self.vel_y, self.on_ground = tile_rect.top, 0, True
                                    else: self.hitbox.top, self.vel_y = tile_rect.bottom, 0

                        elif tile_data.get("type") == "bridge" and axis == 'vertical' and velocity > 0:
                            if not keys[pygame.K_s] and self.hitbox.bottom <= tile_rect.top + velocity + 2:
                                if self.hitbox.colliderect(tile_rect):
                                    self.hitbox.bottom, self.vel_y, self.on_ground = tile_rect.top, 0, True

    def set_state(self, grid, tile_size, properties):
        curr_t = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()
        is_effectively_swimming = self.in_water or (curr_t - self.last_water_touch < self.water_grace_period)

        if is_effectively_swimming:
            is_moving = any([keys[pygame.K_a], keys[pygame.K_d], keys[pygame.K_w], keys[pygame.K_s]])
            new_state = "swim" if (is_moving or abs(self.vel_x) > 0.5) else "swim_idle"
        elif self.on_ground:
            new_state = "slide" if self.is_sliding else ("run" if abs(self.vel_x) > 0.5 else "idle")
        else:
            new_state = self.dash_type if self.is_dashing else ("jump" if self.vel_y < 0 else "fall")

        # Slide Hitbox Resizing
        if new_state == "slide" and self.state != "slide":
            self.hitbox.height, self.hitbox.width = self.height_sliding, self.width_sliding
            self.hitbox.y += (self.height_standing - self.height_sliding)
        elif new_state != "slide" and self.state == "slide":
            if not self.can_stand_up(grid, tile_size, properties) or (curr_t - self.slide_start_time < self.min_slide_duration and keys[pygame.K_LSHIFT]):
                new_state, self.is_sliding = "slide", True
            else:
                self.hitbox.height, self.hitbox.width = self.height_standing, self.width_standing
                self.hitbox.y -= (self.height_standing - self.height_sliding)
                self.is_sliding = False

        if new_state != self.state:
            self.state, self.frame_index = new_state, 0

    def can_stand_up(self, grid, tile_size, properties):
        test_rect = pygame.Rect(self.hitbox.x, self.hitbox.y - (self.height_standing - self.height_sliding), self.width_standing, self.height_standing)
        for r in range(int(test_rect.top // tile_size), int(test_rect.bottom // tile_size) + 1):
            for c in range(int(test_rect.left // tile_size), int(test_rect.right // tile_size) + 1):
                if 0 <= r < len(grid) and 0 <= c < len(grid[0]):
                    tid = int(grid[r][c])
                    if tid in properties and properties[tid].get("solid") and test_rect.colliderect(pygame.Rect(c*tile_size, r*tile_size, tile_size, tile_size)): return False
        return True

    def start_dash(self, direction):
        now = pygame.time.get_ticks()
        if now - self.last_dash_time > self.dash_cooldown:
            self.is_dashing, self.is_sliding = True, False 
            self.dash_timer = self.last_dash_time = now
            self.dash_direction, self.vel_y = direction, 0
            self.dash_type = "dash" if self.on_ground else "air_dash"

    def animate(self):
        now = pygame.time.get_ticks()
        frames = self.animations.get(self.state, self.animations["idle"])
        if now - self.last_anim_update > self.anim_speed:
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.last_anim_update = now
        self.image = frames[self.frame_index]

    def get_environment(self, grid, tile_size, properties):
        self.in_water = self.is_climbing = False
        check_rect = self.hitbox.inflate(-4, -4)
        for r in range(int(check_rect.top // tile_size), int(check_rect.bottom // tile_size) + 1):
            for c in range(int(check_rect.left // tile_size), int(check_rect.right // tile_size) + 1):
                if 0 <= r < len(grid) and 0 <= c < len(grid[0]):
                    tid = int(grid[r][c])
                    if tid in properties:
                        ttype = properties[tid].get("type")
                        if ttype == "liquid": 
                            self.in_water = True
                            self.last_water_touch = pygame.time.get_ticks()
                        elif ttype == "ladder": self.is_climbing = True

    def draw(self, screen, camera_x, camera_y):
        # 1. Ghosts
        for g in self.ghosts[:]:
            g[3] -= 15
            if g[3] <= 0: self.ghosts.remove(g)
            else:
                img = pygame.transform.flip(g[2], self.dash_direction == -1, False)
                img.set_alpha(g[3]); screen.blit(img, (g[0] - camera_x, g[1] - camera_y))
        
        # 2. Player Sprite
        draw_img = pygame.transform.flip(self.image, self.dash_direction == -1, False)
        screen.blit(draw_img, (self.hitbox.centerx - draw_img.get_width()//2 - camera_x, 
                              self.hitbox.bottom - draw_img.get_height() - camera_y))
        
        # 3. Modular Weapon Drawing
        hidden_states = ["swim", "swim_idle"]
        if self.weapon_unsheathed and self.state not in hidden_states and self.current_weapon:
            hand_frames = self.hand_positions.get(self.state, [(0, 0)])
            hx, hy = hand_frames[self.frame_index % len(hand_frames)]
            
            rot = self.current_weapon.get_rotation(self.state, self.frame_index)
            dir_mult = 1 if self.dash_direction == 1 else -1
            
            wx = (self.hitbox.centerx - camera_x) + (hx * dir_mult)
            wy = (self.hitbox.centery - camera_y) + hy

            angle_rad = math.radians(-rot if dir_mult == 1 else 180 + rot)
            tip_x = wx + self.current_weapon.length * math.cos(angle_rad)
            tip_y = wy + self.current_weapon.length * math.sin(angle_rad)

            pygame.draw.line(screen, (255, 0, 0), (wx, wy), (tip_x, tip_y), 3)

            if self.debug_mode:
                pygame.draw.circle(screen, (0, 255, 0), (int(wx), int(wy)), 3)

        # 4. Debug Hitbox
        if self.debug_mode:
            debug_rect = self.hitbox.copy()
            debug_rect.x -= camera_x; debug_rect.y -= camera_y
            pygame.draw.rect(screen, (255, 0, 0), debug_rect, 2)