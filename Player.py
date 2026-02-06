import pygame
from spritesheet import SpriteSheet
from player_platform import SummonedPlatform

class Player:
    def __init__(self, x, y, spritesheet, colorkey=None, scale=4, tilesize=16):
        img = SpriteSheet(spritesheet)
        self.spritesheet = img
        self.scale, self.tilesize = scale, tilesize
        
        # --- Hitboxes ---
        self.width_standing, self.height_standing = 32, 80
        self.width_sliding, self.height_sliding = 48, 36
        
        # --- Physics ---
        self.pos_x, self.pos_y = float(x), float(y)
        self.vel_x, self.vel_y = 0, 0
        self.hitbox = pygame.Rect(int(self.pos_x), int(self.pos_y), self.width_standing, self.height_standing)
        self.respawn_point = (float(x), float(y))

        # --- Constants ---
        self.speed, self.accel, self.friction = 7, 0.8, 0.86
        self.gravity, self.water_gravity = 0.8, 0.25
        self.jump_power = -15
        self.dash_speed = 32   
        self.max_vel_x = 28    
        
        # --- Health System ---
        self.max_hearts, self.current_hearts = 5, 5
        self.invincible, self.invincibility_timer = False, 0
        self.invincibility_duration = 1200 
        
        # --- State ---
        self.on_ground = False
        self.on_solid_ground = False 
        self.is_sliding = False
        self.is_dashing = False
        self.in_water = False
        self.facing_right = True
        
        # --- Platform & Jump System ---
        self.jumps_left = 2 
        self.has_platform_charge = True 
        self.active_platform = None
        
        # --- Timers ---
        self.current_time = 0
        self.dash_timer = 0
        self.dash_duration, self.dash_cooldown = 180, 600
        self.last_dash_time = 0
        self.coyote_timer, self.jump_buffer_timer = 0, 0
        self.last_jump_time = 0 
        self.last_a_time, self.last_d_time = 0, 0
        self.double_tap_threshold = 250

        # --- Visuals ---
        self.state, self.frame_index = "idle", 0
        self.last_anim_update, self.anim_speed = 0, 100
        self.ghosts = [] 
        
        self.animations = {
            "idle":  self.spritesheet.get_strip(0, 10, tilesize, tilesize, scale, colorkey),
            "run":   self.spritesheet.get_strip(48, 8,  tilesize, tilesize, scale, colorkey),
            "jump":  self.spritesheet.get_strip(96, 1,  tilesize, tilesize, scale, colorkey),
            "fall":  self.spritesheet.get_strip(144, 1,  tilesize, tilesize, scale, colorkey),
            "slide": self.spritesheet.get_strip(192, 1,  tilesize, tilesize, scale, colorkey),
            "dash":  self.spritesheet.get_strip(240, 1,  tilesize, tilesize, scale, colorkey),
            "swim":  self.spritesheet.get_strip(336, 1,  tilesize, tilesize, scale, colorkey) 
        }
        self.image = self.animations["idle"][0]
        self.prev_keys = pygame.key.get_pressed()

    def update(self, grid, tile_size, properties, SH, moving_platforms=[]):
        self.current_time = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()
        
        # 1. Update active magic platform
        if self.active_platform:
            if not self.active_platform.update(): self.active_platform = None

        # 2. Status timers
        if self.invincible and self.current_time - self.invincibility_timer > self.invincibility_duration:
            self.invincible = False

        self.check_liquid(grid, tile_size, properties)
        self.check_hazards(grid, tile_size, properties)

        if keys[pygame.K_w] and not self.prev_keys[pygame.K_w]:
            self.jump_buffer_timer = self.current_time

        # 3. Horizontal Movement
        move_dir = keys[pygame.K_d] - keys[pygame.K_a]
        self.handle_horizontal_inputs(keys, move_dir)
        
        if self.is_dashing:
            self.vel_x = self.dash_speed * (1 if self.facing_right else -1)
            self.vel_y = 0
            if self.current_time - self.dash_timer > self.dash_duration:
                self.is_dashing = False
            self.create_ghost()
        elif self.is_sliding:
            self.vel_x *= 0.985 
            if self.is_ceiling_above(grid, tile_size, properties):
                if abs(self.vel_x) < 4.0: self.vel_x = 4.0 if self.facing_right else -4.0
            else:
                if not keys[pygame.K_LSHIFT] or abs(self.vel_x) < 1.5: self.is_sliding = False
        else:
            target_vel = move_dir * (self.speed * 0.5 if self.in_water else self.speed)
            if move_dir != 0:
                accel_rate = self.accel if self.on_ground else self.accel * 0.4
                self.vel_x += (target_vel - self.vel_x) * accel_rate
            else:
                self.vel_x *= self.friction if self.on_ground else 0.7
            if abs(self.vel_x) < 0.1: self.vel_x = 0

        if abs(self.vel_x) > self.max_vel_x:
            self.vel_x = self.max_vel_x if self.vel_x > 0 else -self.max_vel_x

        # Apply Horizontal Position
        self.pos_x += self.vel_x
        self.hitbox.x = round(self.pos_x)
        self.check_collisions(grid, tile_size, properties, 'x')

        # 4. Vertical Movement
        self.handle_platform_placement(keys)

        if not self.is_dashing:
            self.vel_y += self.water_gravity if self.in_water else self.gravity
            
            # Jump Logic
            if (self.current_time - self.jump_buffer_timer < 150):
                if not self.is_ceiling_above(grid, tile_size, properties):
                    is_on_magic = self.active_platform and self.hitbox.colliderect(self.active_platform.rect) and self.vel_y >= 0
                    
                    if (self.current_time - self.coyote_timer < 150) and self.jumps_left == 2:
                        power = self.jump_power - (abs(self.vel_x) * 0.6) if self.is_sliding else self.jump_power
                        self.execute_jump(max(power, -28))
                        self.coyote_timer = 0
                    elif is_on_magic or self.jumps_left > 0:
                        self.execute_jump(self.jump_power * 0.85)
                else:
                    self.jump_buffer_timer = 0

        # Apply Vertical Position
        self.pos_y += self.vel_y
        self.hitbox.y = round(self.pos_y)
        
        # Reset ground state before checks
        self.on_ground = False 
        self.on_solid_ground = False 
        
        # 5. COLLISION PRIORITY
        self.check_collisions(grid, tile_size, properties, 'y')
        self.check_platform_collision() # Magic platform
        self.check_moving_platforms(moving_platforms) # Moving tiles

        # 6. Recharge Resources
        if self.on_solid_ground:
            self.has_platform_charge = True
            self.jumps_left = 2
            self.coyote_timer = self.current_time
        elif self.on_ground: 
            self.coyote_timer = self.current_time

        # Death / Visuals
        if self.hitbox.top > max(SH, len(grid) * tile_size): self.respawn()
        self.update_visual_state()
        self.animate()
        self.prev_keys = keys

    def check_moving_platforms(self, moving_platforms):
        """Specifically handles the 'sticky' collision for platforms with velocity."""
        for plat in moving_platforms:
            # We only collide if falling or standing (one-way platform logic)
            if self.vel_y >= 0:
                if self.hitbox.colliderect(plat.rect):
                    # Tolerance check: only snap if player was above the platform top
                    if (self.hitbox.bottom - self.vel_y) <= plat.rect.top + 15:
                        # SNAP to top
                        self.hitbox.bottom = plat.rect.top
                        self.pos_y = float(self.hitbox.y)
                        self.vel_y = 0
                        self.on_ground = True
                        self.coyote_timer = self.current_time # Add this line

                        # INHERIT MOTION: This is what prevents 'sliding off' or jittering
                        self.pos_x += plat.velocity.x
                        self.pos_y += plat.velocity.y
                        
                        # Sync hitbox to the float positions immediately
                        self.hitbox.x = round(self.pos_x)
                        self.hitbox.y = round(self.pos_y)
                        
                        # Recharge
                        self.has_platform_charge = True
                        self.jumps_left = 2

    def check_collisions(self, grid, tile_size, properties, axis):
        start_col, end_col = self.hitbox.left // tile_size, self.hitbox.right // tile_size
        start_row, end_row = self.hitbox.top // tile_size, self.hitbox.bottom // tile_size
        
        for r in range(int(start_row), int(end_row) + 1):
            for c in range(int(start_col), int(end_col) + 1):
                if not (0 <= r < len(grid) and 0 <= c < len(grid[0])): continue
                tid = grid[r][c]
                if tid is None: continue
                
                props = properties.get(int(tid), {})
                tile_rect = pygame.Rect(c * tile_size, r * tile_size, tile_size, tile_size)
                
                if not self.hitbox.colliderect(tile_rect): continue

                if axis == 'x' and props.get("solid"):
                    if self.vel_x > 0: self.hitbox.right = tile_rect.left
                    else: self.hitbox.left = tile_rect.right
                    self.vel_x, self.pos_x = 0, float(self.hitbox.x)
                
                elif axis == 'y':
                    if props.get("solid"):
                        if self.vel_y > 0: 
                            self.hitbox.bottom = tile_rect.top
                            self.on_ground = True
                            self.on_solid_ground = True 
                        else: 
                            self.hitbox.top = tile_rect.bottom
                        self.vel_y, self.pos_y = 0, float(self.hitbox.y)
                        
                    elif props.get("type") == "bridge" and self.vel_y > 0 and not pygame.key.get_pressed()[pygame.K_s]:
                        if (self.hitbox.bottom - self.vel_y) <= tile_rect.top + 10:
                            self.hitbox.bottom = tile_rect.top
                            self.on_ground = True
                            
                            # --- ADD THESE LINES TO REFRESH JUMPS ---
                            self.jumps_left = 2
                            self.coyote_timer = self.current_time
                            # ----------------------------------------
                            
                            self.vel_y, self.pos_y = 0, float(self.hitbox.y)

    def execute_jump(self, power):
        self.vel_y = power
        self.jumps_left -= 1
        self.on_ground = self.is_sliding = False
        self.jump_buffer_timer = 0
        self.last_jump_time = self.current_time

    def handle_platform_placement(self, keys):
        if keys[pygame.K_s] and not self.prev_keys[pygame.K_s]:
            if not self.on_ground and self.has_platform_charge:
                self.active_platform = SummonedPlatform(self.hitbox.centerx - 40, self.hitbox.bottom + 5)
                self.has_platform_charge = False 
                if self.vel_y > 0: self.vel_y = 0

    def check_platform_collision(self):
        if self.active_platform and self.vel_y >= 0 and self.current_time - self.last_jump_time > 100:
            if self.hitbox.colliderect(self.active_platform.rect) and (self.hitbox.bottom - self.vel_y) <= self.active_platform.rect.top + 15:
                self.hitbox.bottom = self.active_platform.rect.top
                self.pos_y, self.vel_y, self.on_ground = float(self.hitbox.y), 0, True
                if self.jumps_left == 0: self.jumps_left = 1

    def is_ceiling_above(self, grid, tile_size, properties):
        # A virtual rect to check if there is room to stand up
        check_rect = pygame.Rect(self.hitbox.x, self.hitbox.bottom - self.height_standing, 
                                 self.width_standing, self.height_standing - self.height_sliding - 2)
        for r in range(int(check_rect.top // tile_size), int(check_rect.bottom // tile_size) + 1):
            for c in range(int(check_rect.left // tile_size), int(check_rect.right // tile_size) + 1):
                if 0 <= r < len(grid) and 0 <= c < len(grid[0]):
                    tid = grid[r][c]
                    if tid is not None and properties.get(int(tid), {}).get("solid"): return True
        return False

    def check_liquid(self, grid, tile_size, properties):
        self.in_water = False
        cx, cy = self.hitbox.centerx // tile_size, self.hitbox.centery // tile_size
        if 0 <= cy < len(grid) and 0 <= cx < len(grid[0]):
            tid = grid[cy][cx]
            if tid is not None and properties.get(int(tid), {}).get("type") == "liquid": self.in_water = True

    def check_hazards(self, grid, tile_size, properties):
        for pt in [self.hitbox.center, self.hitbox.midbottom]:
            cx, cy = int(pt[0] // tile_size), int(pt[1] // tile_size)
            if 0 <= cy < len(grid) and 0 <= cx < len(grid[0]):
                tid = grid[cy][cx]
                if tid is not None and properties.get(int(tid), {}).get("damage", 0) > 0:
                    self.take_damage(properties[int(tid)]["damage"], (cx * tile_size) + (tile_size // 2))
                    break

    def take_damage(self, amount, source_x):
        if not self.invincible:
            self.current_hearts -= amount
            self.invincible = True
            self.invincibility_timer = pygame.time.get_ticks()
            self.vel_y, self.vel_x = -10, (12 if self.hitbox.centerx > source_x else -12)
            if self.current_hearts <= 0: self.respawn()

    def handle_horizontal_inputs(self, keys, move_dir):
        if move_dir != 0 and not self.is_dashing:
            self.facing_right = (move_dir > 0)
        
        if keys[pygame.K_d] and not self.prev_keys[pygame.K_d]:
            if self.current_time - self.last_d_time < self.double_tap_threshold: self.start_dash(1)
            self.last_d_time = self.current_time
        if keys[pygame.K_a] and not self.prev_keys[pygame.K_a]:
            if self.current_time - self.last_a_time < self.double_tap_threshold: self.start_dash(-1)
            self.last_a_time = self.current_time
        
        if keys[pygame.K_LSHIFT] and self.on_ground and not self.in_water:
            if not self.is_sliding and (self.is_dashing or abs(self.vel_x) > 0.5 or move_dir != 0):
                boost_dir = move_dir if move_dir != 0 else (1 if self.facing_right else -1)
                self.vel_x = boost_dir * (self.speed * 2.5) 
                self.is_dashing, self.is_sliding = False, True

    def start_dash(self, direction):
        if self.current_time - self.last_dash_time > self.dash_cooldown:
            self.is_dashing, self.dash_timer = True, self.current_time
            self.last_dash_time, self.facing_right = self.current_time, (direction == 1)

    def update_visual_state(self):
        if self.is_sliding: new_state = "slide"
        elif self.in_water: new_state = "swim"
        elif self.is_dashing: new_state = "dash"
        elif not self.on_ground: new_state = "jump" if self.vel_y < 0 else "fall"
        elif abs(self.vel_x) > 0.1: new_state = "run"
        else: new_state = "idle"

        if new_state != self.state:
            old_b, old_cx = self.hitbox.bottom, self.hitbox.centerx
            self.state, self.frame_index = new_state, 0
            self.hitbox.size = (self.width_sliding, self.height_sliding) if self.state == "slide" else (self.width_standing, self.height_standing)
            self.hitbox.bottom, self.hitbox.centerx = old_b, old_cx
            self.pos_x, self.pos_y = float(self.hitbox.x), float(self.hitbox.y)

    def animate(self):
        frames = self.animations.get(self.state, self.animations["idle"])
        if self.current_time - self.last_anim_update > self.anim_speed:
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.last_anim_update = self.current_time
        self.image = frames[self.frame_index % len(frames)]

    def create_ghost(self):
        if self.current_time % 60 < 20:
            self.ghosts.append([self.hitbox.x, self.hitbox.y, self.image.copy(), 150, 1 if self.facing_right else -1])

    def draw(self, screen, camera_x, camera_y):
        if self.active_platform: self.active_platform.draw(screen, camera_x, camera_y)
        for g in self.ghosts[:]:
            g[3] -= 12
            if g[3] <= 0: self.ghosts.remove(g)
            else:
                img = pygame.transform.flip(g[2], g[4] == -1, False)
                img.set_alpha(g[3]); screen.blit(img, (g[0] - camera_x, g[1] - camera_y))
        
        if self.invincible and (self.current_time // 100) % 2 == 0: return

        draw_img = pygame.transform.flip(self.image, not self.facing_right, False)
        screen.blit(draw_img, (self.hitbox.centerx - draw_img.get_width()//2 - camera_x, 
                               self.hitbox.bottom - draw_img.get_height() - camera_y))

    def respawn(self):
        self.pos_x, self.pos_y = self.respawn_point
        self.hitbox.topleft = (int(self.pos_x), int(self.pos_y))
        self.vel_x, self.vel_y = 0, 0
        self.current_hearts = self.max_hearts
        self.is_dashing = self.is_sliding = False
        self.has_platform_charge = True