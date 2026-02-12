import pygame
from settings import *

class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, color, size=(32, 32)):
        super().__init__()
        self.image = pygame.Surface(size)
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))

        # Exact position for physics
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.speed = 300  # Pixels per second

    def update(self, dt):
        self.pos += self.vel * dt
        self.rect.topleft = (round(self.pos.x), round(self.pos.y))

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, color=(0, 255, 0), size=(32, 64)) # Taller Sprite
        self.state = "IDLE"     # IDLE, MOVING, ATTACKING, CROUCHING
        self.stance = "HIGH"    # HIGH or LOW
        self.direction = 1      # 1 for Right, -1 for Left

        # Pre-create surfaces to prevent flickering/memory leaks
        self.surface_high = pygame.Surface((32, 64))
        self.surface_high.fill((0, 255, 0))

        self.surface_low = pygame.Surface((32, 32))
        self.surface_low.fill((0, 255, 0))

        # Combat Stats
        self.is_attacking = False
        self.attack_timer = 0
        self.hp = 10
        self.on_ground=False

    def apply_gravity(self, dt):
        # Apply downward force
        self.vel.y += GRAVITY * dt

        # Cap falling speed (Terminal Velocity)
        if self.vel.y > TERMINAL_VELOCITY:
            self.vel.y = TERMINAL_VELOCITY

    def get_shield_rect(self):
        """Returns the rectangle where the player is currently blocking."""
        # Shield is a vertical sliver on the front edge
        shield_w, shield_h = 10, 32

        x = self.rect.right - 5 if self.direction == 1 else self.rect.left - 5
        if self.stance == "HIGH":
            y = self.rect.top
        else:
            y = self.rect.bottom - shield_h

        return pygame.Rect(x, y, shield_w, shield_h)

    def get_sword_rect(self):
        """Returns the current rectangle of the sword thrust based on stance."""
        if not self.is_attacking:
            return None

        # Sword is 40px wide, 10px tall
        sword_w, sword_h = 40, 10
        x = self.rect.right if self.direction == 1 else self.rect.left - sword_w
        y = self.rect.top



        # Position it in front of the player based on direction
        if self.direction == 1:  # Right
            x = self.rect.right
        else:  # Left
            x = self.rect.left - sword_w

        # Position it vertically based onz stance
        # If HIGH, stab at chest level. If LOW, stab at knee level.
        # HIGH: Stab at chest height | LOW: Stab at knee height
        if self.stance == "HIGH":
            y = self.rect.top + 20
        else:
            y = self.rect.bottom - 15

        return pygame.Rect(x, y, sword_w, sword_h)

    def update(self, dt, keys):
        # 1. Stance Logic
        if keys[pygame.K_DOWN] and self.on_ground:
            if self.stance != "LOW":  # Only swap if state changes
                self.stance = "LOW"
                self.image = self.surface_low
                # Important: Sync the Rect and the Float Position immediately
                self.rect = self.image.get_rect(bottomleft=self.rect.bottomleft)
                self.pos.y = float(self.rect.y)
        else:
            if self.stance != "HIGH":
                self.stance = "HIGH"
                self.image = self.surface_high
                self.rect = self.image.get_rect(bottomleft=self.rect.bottomleft)
                self.pos.y = float(self.rect.y)

        # 2. Gravity & Vertical Movement
        self.apply_gravity(dt)
        self.pos.y += self.vel.y * dt
        self.rect.y = round(self.pos.y)

        # 3. Floor Collision
        if self.rect.bottom >= FLOOR_Y:
            self.rect.bottom = FLOOR_Y
            self.pos.y = float(self.rect.y)  # Keep float in sync with snapped rect
            self.vel.y = 0
            self.on_ground = True
        else:
            self.on_ground = False

        # 4. Horizontal Movement
        self.pos.x += self.vel.x * dt
        self.rect.x = round(self.pos.x)

        # 5. Direction Logic
        if self.vel.x > 0:
            self.direction = 1
        elif self.vel.x < 0:
            self.direction = -1

        # 6. Attack Timer
        if self.is_attacking:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.is_attacking = False


class IronKnuckle(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, color=RED, size=(32, 64))
        self.health = 3
        self.stance = "HIGH"
        self.direction = -1  # Start moving left
        self.speed = 100

        # AI Timers
        self.stance_timer = 2.0  # Change stance every 2 seconds

    def take_damage(self, amount):
        self.health -= amount
        # You could add a 'flash red' effect here later!
        if self.health <= 0:
            self.kill()

    def update(self, dt, keys):
        # 1. Simple Pacing AI
        self.pos.x += (self.speed * self.direction) * dt
        self.rect.x = round(self.pos.x)

        # 2. Change Stance
        self.stance_timer -= dt
        if self.stance_timer <= 0:
            self.stance = "LOW" if self.stance == "HIGH" else "HIGH"
            self.stance_timer = 2.0  # Reset

        # 3. Simple Screen Boundary Bounce
        if self.rect.right > SCREEN_WIDTH or self.rect.left < 0:
            self.direction *= -1

    def get_shield_rect(self):
        # Similar to player, shield is on their leading edge
        shield_w = 12
        shield_h = 32

        x = self.rect.left if self.direction == -1 else self.rect.right - shield_w

        if self.stance == "HIGH":
            y = self.rect.top
        else:
            y = self.rect.bottom - shield_h

        return pygame.Rect(x, y, shield_w, shield_h)

