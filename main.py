"""
=============================================================================
                       FLAPPY ROCKET - SPACE ADVENTURE
=============================================================================
A beginner-friendly Flappy Bird style game in Python using Pygame.

Controls:
  - SPACE, UP ARROW, or TAP SCREEN : Fire thrusters (Jump) / Launch / Retry
  - M                             : Toggle Audio ON/OFF (Mute / Unmute)
  - H                             : Toggle Hitbox Debug Mode (visualize bug!)
  - R                             : Restart when Game Over
  - ESC                           : Quit game
=============================================================================
"""

import os
import sys
import math
import random
import pygame

# -----------------------------------------------------------------------------
# 1. GAME CONSTANTS & CONFIGURATION
# -----------------------------------------------------------------------------
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
FPS = 60

# Physics constants
GRAVITY = 0.42
THRUST_IMPULSE = -7.4
MAX_FALL_SPEED = 9.5

# Obstacle settings
OBSTACLE_SPEED = 2.8
OBSTACLE_GAP = 160
OBSTACLE_WIDTH = 68
OBSTACLE_FREQUENCY = 1500

# Color Palette
COLOR_WHITE = (255, 255, 255)
COLOR_TEXT_DARK = (24, 32, 58)
COLOR_GOLD = (255, 205, 30)
COLOR_CYAN = (0, 185, 235)
COLOR_RED = (235, 50, 65)
COLOR_GREEN = (40, 195, 80)
COLOR_CARD_BG = (20, 26, 46, 215)


# -----------------------------------------------------------------------------
# 2. AUDIO & SOUND MANAGER
# -----------------------------------------------------------------------------
class SoundManager:
    """Handles sound effects and background music for the game."""
    def __init__(self):
        self.sounds_enabled = False
        self.muted = False
        self.lose_sound = None
        self.sounds = {}
        self.gameplay_music_file = None

        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
            pygame.mixer.init()
            self.sounds_enabled = True
        except Exception:
            return

        self.load_sounds()

    def toggle_mute(self, is_playing=False):
        """Toggles sound on and off."""
        self.muted = not self.muted
        if self.muted:
            self.stop_gameplay_music()
            self.stop_lose()
        else:
            if is_playing:
                self.play_gameplay_music()
        return not self.muted

    def load_sounds(self):
        sound_files = {
            "thrust": "assets/sounds/thrust.wav",
            "score": "assets/sounds/score.wav",
            "crash": "assets/sounds/crash.wav",
            "lose": "assets/sounds/lose-2.wav"
        }

        for name, path in sound_files.items():
            if os.path.exists(path):
                try:
                    snd = pygame.mixer.Sound(path)
                    if name == "thrust":
                        snd.set_volume(0.35)
                    elif name == "score":
                        snd.set_volume(0.50)
                    elif name == "lose":
                        snd.set_volume(0.70)
                        self.lose_sound = snd
                    self.sounds[name] = snd
                except Exception:
                    pass

        # Music file (ob-1)
        music_path = "assets/sounds/ob-1.wav"
        if os.path.exists(music_path):
            self.gameplay_music_file = music_path

    def play_gameplay_music(self):
        self.stop_lose()
        if self.sounds_enabled and not self.muted and self.gameplay_music_file:
            try:
                pygame.mixer.music.load(self.gameplay_music_file)
                pygame.mixer.music.set_volume(0.65)
                pygame.mixer.music.play(-1)
            except Exception:
                pass

    def stop_gameplay_music(self):
        if self.sounds_enabled:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

    def play_lose(self):
        self.stop_gameplay_music()
        if self.muted:
            return
        if self.lose_sound:
            try:
                self.lose_sound.play()
            except Exception:
                pass
        elif "crash" in self.sounds:
            self.sounds["crash"].play()

    def stop_lose(self):
        if self.lose_sound:
            try:
                self.lose_sound.stop()
            except Exception:
                pass

    def play_thrust(self):
        if self.sounds_enabled and not self.muted and "thrust" in self.sounds:
            self.sounds["thrust"].play()

    def play_score(self):
        if self.sounds_enabled and not self.muted and "score" in self.sounds:
            self.sounds["score"].play()


# -----------------------------------------------------------------------------
# 3. MOTION STARS & PARALLAX BACKGROUND
# -----------------------------------------------------------------------------
class MotionStar:
    """A dynamic star that drifts across the sky with twinkling luminescence."""
    def __init__(self, x=None, y=None):
        self.x = random.uniform(0, SCREEN_WIDTH) if x is None else x
        self.y = random.uniform(0, SCREEN_HEIGHT) if y is None else y
        
        self.layer = random.choices([1, 2, 3], weights=[0.5, 0.35, 0.15])[0]
        if self.layer == 1:
            self.speed = random.uniform(0.6, 1.2)
            self.size = random.uniform(1.5, 2.2)
            self.color = (255, 255, 255)
        elif self.layer == 2:
            self.speed = random.uniform(1.4, 2.2)
            self.size = random.uniform(2.5, 3.4)
            self.color = (255, 225, 120)
        else:
            self.speed = random.uniform(2.4, 3.4)
            self.size = random.uniform(3.8, 5.0)
            self.color = (255, 240, 160)
            
        self.twinkle_offset = random.uniform(0, math.pi * 2)

    def update(self, speed_multiplier=1.0):
        self.x -= self.speed * speed_multiplier
        if self.x < -10:
            self.x = SCREEN_WIDTH + random.uniform(5, 25)
            self.y = random.uniform(0, SCREEN_HEIGHT)

    def draw(self, surface):
        t = pygame.time.get_ticks() * 0.003 + self.twinkle_offset
        alpha = int(170 + 80 * math.sin(t))
        alpha = max(80, min(255, alpha))

        if self.layer == 3:
            radius = int(self.size)
            star_surf = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
            cx, cy = radius + 1, radius + 1
            col = (*self.color, alpha)
            pygame.draw.line(star_surf, col, (cx - radius, cy), (cx + radius, cy), 2)
            pygame.draw.line(star_surf, col, (cx, cy - radius), (cx, cy + radius), 2)
            surface.blit(star_surf, (self.x - cx, self.y - cy))
        else:
            radius = max(1, int(self.size))
            star_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
            cx, cy = radius * 2, radius * 2
            pygame.draw.circle(star_surf, (*self.color, int(alpha * 0.4)), (cx, cy), radius * 2)
            pygame.draw.circle(star_surf, (*self.color, alpha), (cx, cy), radius)
            surface.blit(star_surf, (self.x - cx, self.y - cy))


class ShootingStar:
    """A celestial shooting star that streaks across the upper sky."""
    def __init__(self):
        self.active = False
        self.reset_timer()

    def reset_timer(self):
        self.next_spawn_time = pygame.time.get_ticks() + random.randint(4000, 9000)

    def spawn(self):
        self.active = True
        self.x = random.uniform(SCREEN_WIDTH * 0.4, SCREEN_WIDTH + 50)
        self.y = random.uniform(20, 180)
        self.vx = -random.uniform(7.0, 11.0)
        self.vy = random.uniform(3.0, 6.0)
        self.length = random.uniform(35, 65)
        self.life = 1.0

    def update(self):
        now = pygame.time.get_ticks()
        if not self.active and now > self.next_spawn_time:
            self.spawn()

        if self.active:
            self.x += self.vx
            self.y += self.vy
            self.life -= 0.025
            if self.life <= 0 or self.x < -100 or self.y > SCREEN_HEIGHT:
                self.active = False
                self.reset_timer()

    def draw(self, surface):
        if self.active and self.life > 0:
            tail_x = self.x - self.vx * (self.length / 10.0)
            tail_y = self.y - self.vy * (self.length / 10.0)
            alpha = int(self.life * 230)
            surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(surf, (255, 255, 230, alpha), (int(self.x), int(self.y)), (int(tail_x), int(tail_y)), 2)
            pygame.draw.circle(surf, (255, 255, 255, min(255, alpha + 25)), (int(self.x), int(self.y)), 3)
            surface.blit(surf, (0, 0))


# -----------------------------------------------------------------------------
# 4. PARTICLES
# -----------------------------------------------------------------------------
class Particle:
    """Glowing engine flame particle."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3.5, -1.2)
        self.vy = random.uniform(-1.2, 1.2)
        self.radius = random.uniform(2.5, 5.0)
        self.life = 1.0
        self.decay = random.uniform(0.04, 0.08)
        self.color = random.choice([
            (255, 90, 30),
            (255, 185, 40),
            (255, 245, 160)
        ])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.radius = max(0.5, self.radius - 0.1)
        self.life -= self.decay

    def draw(self, surface):
        if self.life > 0:
            alpha = int(self.life * 255)
            part_surf = pygame.Surface((int(self.radius * 2 + 2), int(self.radius * 2 + 2)), pygame.SRCALPHA)
            pygame.draw.circle(part_surf, (*self.color, alpha), (int(self.radius + 1), int(self.radius + 1)), int(self.radius))
            surface.blit(part_surf, (self.x - self.radius, self.y - self.radius))


# -----------------------------------------------------------------------------
# 5. ROCKET CHARACTER (PLAYER)
# -----------------------------------------------------------------------------
class Rocket:
    """Player rocket character."""
    def __init__(self, x, y, sprite=None):
        self.x = x
        self.y = y
        self.velocity_y = 0.0
        self.width = 52
        self.height = 36
        self.raw_sprite = sprite
        self.angle = 0.0

    def thrust(self, sound_manager):
        self.velocity_y = THRUST_IMPULSE
        sound_manager.play_thrust()

    def update(self):
        self.velocity_y += GRAVITY
        if self.velocity_y > MAX_FALL_SPEED:
            self.velocity_y = MAX_FALL_SPEED
        self.y += self.velocity_y

        target_angle = -self.velocity_y * 3.5
        self.angle = max(-30.0, min(70.0, target_angle))

    def get_hitbox(self):
        # =========================================================================
        # TODO: Fix collision/physics bug here
        # -------------------------------------------------------------------------
        # STUDENT BUG-HUNT EXERCISE:
        # The rocket crashes prematurely! Look at the extra offset (+18px) and height (+16px).
        # Fix this method so the collision box fits the actual rocket sprite:
        #   return pygame.Rect(self.x, self.y, self.width, self.height)
        # =========================================================================
        buggy_forward_offset = 0
        buggy_extra_height = 0

        return pygame.Rect(
            int(self.x + buggy_forward_offset),
            int(self.y - buggy_extra_height // 2),
            self.width,
            self.height + buggy_extra_height
        )

    def get_visual_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def draw(self, surface):
        if self.raw_sprite:
            rotated_image = pygame.transform.rotate(self.raw_sprite, self.angle)
            orig_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            rot_rect = rotated_image.get_rect(center=orig_rect.center)
            surface.blit(rotated_image, rot_rect.topleft)
        else:
            pygame.draw.ellipse(surface, (240, 245, 255), (self.x, self.y, self.width, self.height))
            pygame.draw.circle(surface, (50, 180, 255), (self.x + 36, self.y + 14), 6)


# -----------------------------------------------------------------------------
# 6. OBSTACLES
# -----------------------------------------------------------------------------
class Obstacle:
    def __init__(self, x, custom_obstacle_surf=None):
        self.x = x
        self.width = OBSTACLE_WIDTH
        self.custom_obstacle_surf = custom_obstacle_surf
        self.passed = False

        margin = 60
        self.gap_y = random.randint(margin, SCREEN_HEIGHT - margin - OBSTACLE_GAP)
        self.top_height = self.gap_y
        self.bottom_y = self.gap_y + OBSTACLE_GAP
        self.bottom_height = SCREEN_HEIGHT - self.bottom_y

    def update(self):
        self.x -= OBSTACLE_SPEED

    def is_off_screen(self):
        return self.x + self.width < 0

    def get_top_rect(self):
        return pygame.Rect(int(self.x), 0, self.width, self.top_height)

    def get_bottom_rect(self):
        return pygame.Rect(int(self.x), self.bottom_y, self.width, self.bottom_height)

    def draw(self, surface):
        top_rect = self.get_top_rect()
        bottom_rect = self.get_bottom_rect()

        if self.custom_obstacle_surf:
            bot_img = self.custom_obstacle_surf
            top_img = pygame.transform.flip(bot_img, False, True)

            surface.blit(top_img, (top_rect.x, self.top_height - SCREEN_HEIGHT))
            surface.blit(bot_img, (bottom_rect.x, self.bottom_y))

            pygame.draw.rect(surface, (255, 100, 60), (top_rect.x, self.top_height - 6, self.width, 6))
            pygame.draw.rect(surface, (255, 100, 60), (bottom_rect.x, self.bottom_y, self.width, 6))
        else:
            pygame.draw.rect(surface, (70, 85, 110), top_rect)
            pygame.draw.rect(surface, (70, 85, 110), bottom_rect)
            pygame.draw.rect(surface, COLOR_CYAN, (top_rect.x, top_rect.bottom - 8, self.width, 8))
            pygame.draw.rect(surface, COLOR_CYAN, (bottom_rect.x, bottom_rect.y, self.width, 8))


# -----------------------------------------------------------------------------
# 7. MAIN GAME CONTROLLER
# -----------------------------------------------------------------------------
class FlappyRocketGame:
    STATE_START = "START"
    STATE_PLAYING = "PLAYING"
    STATE_GAME_OVER = "GAME_OVER"

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Flappy Rocket")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.SysFont("Arial", 36, bold=True)
        self.font_main = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_hud = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 16, bold=True)

        self.audio = SoundManager()
        self.load_assets()

        self.stars = [MotionStar() for _ in range(50)]
        self.shooting_star = ShootingStar()
        self.debug_hitbox = False
        self.highscore = 0

        # On-screen toggle buttons (Sound at top-left, Hitbox at top-right)
        self.btn_sound_rect = pygame.Rect(10, 10, 105, 28)
        self.btn_hitbox_rect = pygame.Rect(SCREEN_WIDTH - 115, 10, 105, 28)

        self.reset_game()
        self.state = self.STATE_START

    def load_assets(self):
        obs_path = "assets/images/obstacle.png"
        self.custom_obstacle_surf = None
        if os.path.exists(obs_path):
            try:
                raw_obs = pygame.image.load(obs_path).convert_alpha()
                self.custom_obstacle_surf = pygame.transform.smoothscale(raw_obs, (OBSTACLE_WIDTH, SCREEN_HEIGHT))
            except Exception:
                pass

        try:
            self.img_rocket = pygame.image.load("assets/images/rocket.png").convert_alpha()
        except Exception:
            self.img_rocket = None

        try:
            self.img_background = pygame.image.load("assets/images/background.png").convert()
        except Exception:
            self.img_background = None

    def reset_game(self):
        self.rocket = Rocket(80, SCREEN_HEIGHT // 2 - 20, self.img_rocket)
        self.obstacles = []
        self.particles = []
        self.score = 0
        self.last_spawn_time = pygame.time.get_ticks()

    def spawn_obstacle(self):
        self.obstacles.append(Obstacle(SCREEN_WIDTH + 10, self.custom_obstacle_surf))

    def start_gameplay(self):
        self.state = self.STATE_PLAYING
        self.rocket.thrust(self.audio)
        self.audio.play_gameplay_music()

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.audio.stop_gameplay_music()
                self.audio.stop_lose()
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.audio.stop_gameplay_music()
                    self.audio.stop_lose()
                    pygame.quit()
                    sys.exit()

                # Toggle Hitbox Debug Mode with 'H'
                if event.key == pygame.K_h:
                    self.debug_hitbox = not self.debug_hitbox

                # Toggle Audio Sound ON/OFF with 'M'
                if event.key == pygame.K_m:
                    self.audio.toggle_mute(self.state == self.STATE_PLAYING)

                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    if self.state == self.STATE_START:
                        self.start_gameplay()
                    elif self.state == self.STATE_PLAYING:
                        self.rocket.thrust(self.audio)
                        for _ in range(5):
                            self.particles.append(Particle(self.rocket.x + 2, self.rocket.y + self.rocket.height // 2))
                    elif self.state == self.STATE_GAME_OVER:
                        self.reset_game()
                        self.start_gameplay()

                if event.key == pygame.K_r and self.state == self.STATE_GAME_OVER:
                    self.reset_game()
                    self.start_gameplay()

            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                else:
                    pos = (int(event.x * SCREEN_WIDTH), int(event.y * SCREEN_HEIGHT))

                # Check if player tapped top buttons
                if self.btn_sound_rect.collidepoint(pos):
                    self.audio.toggle_mute(self.state == self.STATE_PLAYING)
                    continue

                if self.btn_hitbox_rect.collidepoint(pos):
                    self.debug_hitbox = not self.debug_hitbox
                    continue

                if self.state == self.STATE_START:
                    self.start_gameplay()
                elif self.state == self.STATE_PLAYING:
                    self.rocket.thrust(self.audio)
                    for _ in range(5):
                        self.particles.append(Particle(self.rocket.x + 2, self.rocket.y + self.rocket.height // 2))
                elif self.state == self.STATE_GAME_OVER:
                    self.reset_game()
                    self.start_gameplay()

    def check_collisions(self):
        if self.rocket.y < -10 or self.rocket.y + self.rocket.height > SCREEN_HEIGHT:
            return True

        hitbox = self.rocket.get_hitbox()
        for obs in self.obstacles:
            if hitbox.colliderect(obs.get_top_rect()) or hitbox.colliderect(obs.get_bottom_rect()):
                return True

        return False

    def update(self):
        star_speed = 1.0 if self.state == self.STATE_PLAYING else 0.45
        for s in self.stars:
            s.update(star_speed)
        self.shooting_star.update()

        if self.state == self.STATE_START:
            t = pygame.time.get_ticks() / 320.0
            self.rocket.y = (SCREEN_HEIGHT // 2 - 20) + math.sin(t) * 8

        elif self.state == self.STATE_PLAYING:
            self.rocket.update()

            if random.random() < 0.65:
                self.particles.append(Particle(self.rocket.x + 4, self.rocket.y + self.rocket.height // 2))

            now = pygame.time.get_ticks()
            if now - self.last_spawn_time > OBSTACLE_FREQUENCY:
                self.spawn_obstacle()
                self.last_spawn_time = now

            for obs in self.obstacles:
                obs.update()

                if not obs.passed and (obs.x + obs.width) < self.rocket.x:
                    obs.passed = True
                    self.score += 1
                    self.audio.play_score()
                    if self.score > self.highscore:
                        self.highscore = self.score

            self.obstacles = [obs for obs in self.obstacles if not obs.is_off_screen()]

            if self.check_collisions():
                self.audio.play_lose()
                self.state = self.STATE_GAME_OVER

        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]

    def render_text_with_shadow(self, text, font, color, pos, shadow_color=(15, 20, 35), offset=(2, 2), center=True):
        shadow_surf = font.render(text, True, shadow_color)
        text_surf = font.render(text, True, color)

        if center:
            rect = text_surf.get_rect(center=pos)
            shadow_rect = shadow_surf.get_rect(center=(pos[0] + offset[0], pos[1] + offset[1]))
        else:
            rect = text_surf.get_rect(topleft=pos)
            shadow_rect = shadow_surf.get_rect(topleft=(pos[0] + offset[0], pos[1] + offset[1]))

        self.screen.blit(shadow_surf, shadow_rect)
        self.screen.blit(text_surf, rect)

    def draw(self):
        if self.img_background:
            self.screen.blit(self.img_background, (0, 0))
        else:
            self.screen.fill((210, 225, 245))

        for s in self.stars:
            s.draw(self.screen)
        self.shooting_star.draw(self.screen)

        for obs in self.obstacles:
            obs.draw(self.screen)

        for p in self.particles:
            p.draw(self.screen)

        self.rocket.draw(self.screen)

        # Draw Hitbox Debug Outlines
        if self.debug_hitbox:
            pygame.draw.rect(self.screen, COLOR_GREEN, self.rocket.get_visual_rect(), 2)
            pygame.draw.rect(self.screen, COLOR_RED, self.rocket.get_hitbox(), 2)
            for obs in self.obstacles:
                pygame.draw.rect(self.screen, (255, 230, 0), obs.get_top_rect(), 1)
                pygame.draw.rect(self.screen, (255, 230, 0), obs.get_bottom_rect(), 1)

            debug_surf = pygame.Surface((SCREEN_WIDTH, 42), pygame.SRCALPHA)
            debug_surf.fill((10, 15, 25, 210))
            self.screen.blit(debug_surf, (0, 42))
            lbl1 = self.font_small.render("[DEBUG] GREEN: Sprite | RED: Active Hitbox", True, (240, 240, 240))
            lbl2 = self.font_small.render("Notice the offset bug! Press 'H' to hide", True, COLOR_GOLD)
            self.screen.blit(lbl1, (12, 46))
            self.screen.blit(lbl2, (12, 63))

        # --- On-Screen Buttons (Sound & Hitbox) ---
        # Sound Button (Top-Left)
        snd_surf = pygame.Surface((self.btn_sound_rect.width, self.btn_sound_rect.height), pygame.SRCALPHA)
        if not self.audio.muted:
            snd_surf.fill((20, 28, 50, 195))
            pygame.draw.rect(snd_surf, (0, 185, 235), (0, 0, self.btn_sound_rect.width, self.btn_sound_rect.height), 1, border_radius=6)
            self.screen.blit(snd_surf, self.btn_sound_rect.topleft)
            self.render_text_with_shadow("SOUND: ON", self.font_small, COLOR_WHITE, (self.btn_sound_rect.centerx, self.btn_sound_rect.centery))
        else:
            snd_surf.fill((45, 18, 22, 215))
            pygame.draw.rect(snd_surf, COLOR_RED, (0, 0, self.btn_sound_rect.width, self.btn_sound_rect.height), 1, border_radius=6)
            self.screen.blit(snd_surf, self.btn_sound_rect.topleft)
            self.render_text_with_shadow("SOUND: OFF", self.font_small, COLOR_RED, (self.btn_sound_rect.centerx, self.btn_sound_rect.centery))

        # Hitbox Button (Top-Right)
        hit_surf = pygame.Surface((self.btn_hitbox_rect.width, self.btn_hitbox_rect.height), pygame.SRCALPHA)
        if self.debug_hitbox:
            hit_surf.fill((20, 48, 30, 215))
            pygame.draw.rect(hit_surf, COLOR_GREEN, (0, 0, self.btn_hitbox_rect.width, self.btn_hitbox_rect.height), 1, border_radius=6)
            self.screen.blit(hit_surf, self.btn_hitbox_rect.topleft)
            self.render_text_with_shadow("HITBOX: ON", self.font_small, COLOR_GREEN, (self.btn_hitbox_rect.centerx, self.btn_hitbox_rect.centery))
        else:
            hit_surf.fill((20, 28, 50, 195))
            pygame.draw.rect(hit_surf, (255, 255, 255, 70), (0, 0, self.btn_hitbox_rect.width, self.btn_hitbox_rect.height), 1, border_radius=6)
            self.screen.blit(hit_surf, self.btn_hitbox_rect.topleft)
            self.render_text_with_shadow("HITBOX: OFF", self.font_small, (220, 225, 240), (self.btn_hitbox_rect.centerx, self.btn_hitbox_rect.centery))

        if self.state == self.STATE_START:
            badge_surf = pygame.Surface((310, 56), pygame.SRCALPHA)
            badge_surf.fill((20, 28, 50, 190))
            pygame.draw.rect(badge_surf, (0, 185, 235), (0, 0, 310, 56), 2, border_radius=12)
            self.screen.blit(badge_surf, (SCREEN_WIDTH // 2 - 155, 135))
            self.render_text_with_shadow("FLAPPY ROCKET", self.font_title, COLOR_WHITE, (SCREEN_WIDTH // 2, 163))

            btn_surf = pygame.Surface((260, 40), pygame.SRCALPHA)
            btn_surf.fill((20, 28, 50, 180))
            pygame.draw.rect(btn_surf, (255, 255, 255), (0, 0, 260, 40), 1, border_radius=8)
            self.screen.blit(btn_surf, (SCREEN_WIDTH // 2 - 130, 345))
            self.render_text_with_shadow("TAP or SPACE to Launch", self.font_main, COLOR_GOLD, (SCREEN_WIDTH // 2, 365))

            self.render_text_with_shadow("Press 'M' or tap Sound button to Mute", self.font_small, COLOR_TEXT_DARK, (SCREEN_WIDTH // 2, 415), shadow_color=(255, 255, 255, 180), offset=(1, 1))

        elif self.state == self.STATE_PLAYING:
            hud_w, hud_h = 130, 32
            hud_x = SCREEN_WIDTH // 2 - hud_w // 2
            hud_y = 88 if self.debug_hitbox else 8
            hud_surf = pygame.Surface((hud_w, hud_h), pygame.SRCALPHA)
            hud_surf.fill((20, 28, 50, 195))
            pygame.draw.rect(hud_surf, COLOR_GOLD, (0, 0, hud_w, hud_h), 2, border_radius=8)
            self.screen.blit(hud_surf, (hud_x, hud_y))
            self.render_text_with_shadow(f"SCORE: {self.score}", self.font_hud, COLOR_WHITE, (SCREEN_WIDTH // 2, hud_y + hud_h // 2))

        elif self.state == self.STATE_GAME_OVER:
            card_w, card_h = 320, 250
            card_x = SCREEN_WIDTH // 2 - card_w // 2
            card_y = 175
            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            card_surf.fill(COLOR_CARD_BG)
            pygame.draw.rect(card_surf, (90, 110, 160), (0, 0, card_w, card_h), 2, border_radius=14)
            self.screen.blit(card_surf, (card_x, card_y))

            self.render_text_with_shadow("MISSION FAILED", self.font_title, COLOR_RED, (SCREEN_WIDTH // 2, card_y + 40))
            self.render_text_with_shadow(f"Score: {self.score}", self.font_main, COLOR_WHITE, (SCREEN_WIDTH // 2, card_y + 90))
            self.render_text_with_shadow(f"High Score: {self.highscore}", self.font_main, COLOR_GOLD, (SCREEN_WIDTH // 2, card_y + 125))
            self.render_text_with_shadow("TAP, 'R', or SPACE to Retry", self.font_small, COLOR_CYAN, (SCREEN_WIDTH // 2, card_y + 175))
            self.render_text_with_shadow("Press 'H' to inspect collision hitbox", self.font_small, (180, 195, 220), (SCREEN_WIDTH // 2, card_y + 205))

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":
    game = FlappyRocketGame()
    game.run()
