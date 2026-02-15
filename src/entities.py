import pygame
import random
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
        self.speed = 200  # Pixels per second

    def update(self, dt):
        self.pos += self.vel * dt
        self.rect.topleft = (round(self.pos.x), round(self.pos.y))


class Character(Entity):
    def __init__(self, x, y, color, size):
        super().__init__(x, y, color, size)
        self.on_ground = False
        self.direction = 1  # 1: Right, -1: Left
        self.stance = "HIGH"
        self.is_attacking = False
        self.is_dead = False
        self.attack_timer = 0
        self.health = 4
        self.max_health = 4
        self.invincible_timer = 0
        self.friction = 50
        self.stun_timer = 0  # New variable

    def apply_physics(self, dt, platforms):

        # Horizontal Movement
        self.pos.x += self.vel.x * dt
        self.rect.x = round(self.pos.x)

        # Check horizontal hits
        hits = pygame.sprite.spritecollide(self, platforms, False)
        for plat in hits:
            if self.vel.x > 0:  # Moving right
                self.rect.right = plat.rect.left
            elif self.vel.x < 0:  # Moving left
                self.rect.left = plat.rect.right

            # Sync float position with the corrected rect position
            self.pos.x = float(self.rect.x)
            self.vel.x = 0  # Optional: stop momentum on impact

        # Apply Gravity
        self.vel.y += GRAVITY * dt
        if self.vel.y > TERMINAL_VELOCITY:
            self.vel.y = TERMINAL_VELOCITY

        # Vertical Movement & Platform Collision
        self.pos.y += self.vel.y * dt
        self.rect.y = round(self.pos.y)

        # Floor Y Check
        if self.rect.bottom >= FLOOR_Y:
            self.rect.bottom = FLOOR_Y
            self.pos.y = float(self.rect.y)
            self.vel.y = 0
            self.on_ground = True

        # Platform Check
        if self.vel.y > 0:
            hits = pygame.sprite.spritecollide(self, platforms, False)
            for plat in hits:
                if self.rect.bottom <= plat.rect.top + 15:
                    self.rect.bottom = plat.rect.top
                    self.pos.y = float(self.rect.y)
                    self.vel.y = 0
                    self.on_ground = True

        if self.stun_timer > 0:
            self.stun_timer -= dt

    def apply_friction(self, dt):
        if self.vel.x > 0:
            self.vel.x = max(0, self.vel.x - FRICTION * dt)
        elif self.vel.x < 0:
            self.vel.x = min(0, self.vel.x + FRICTION * dt)

    def take_damage(self, amount):
        if self.invincible_timer > 0 or self.is_dead:
            return

        self.health -= amount
        self.invincible_timer = 1.0
        print(f"Ouch, HP: {self.health}")

        if self.health <= 0:
            self.health = 0
            self.is_dead = True

    def get_shield_rect(self):
        """Returns the rectangle where the character is currently blocking."""
        # Shield is a vertical sliver on the front edge
        shield_w, shield_h = 10, 32
        x = self.rect.right - 5 if self.direction == 1 else self.rect.left - (shield_w / 2)
        y = self.rect.top if self.stance == "HIGH" else self.rect.bottom - shield_h

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

class Platform(Entity):
    def __init__(self, x, y, width, height, color=(100, 100, 100)):
        super().__init__(x, y, color, size=(width, height))
        # No physics needed for static platforms, just the rect

class Player(Character):
    def __init__(self, x, y):
        super().__init__(x, y, color=(0, 255, 0), size=(32, 64)) # Taller Sprite
        # Pre-create surfaces to prevent flickering/memory leaks
        self.surface_high = pygame.Surface((32, 64))
        self.surface_high.fill((0, 255, 0))

        self.surface_low = pygame.Surface((32, 64))
        self.surface_low.fill((0, 255, 0))

    def update(self, dt, keys, platforms):
        if self.is_dead:
            return

        # Decrement invincibility
        if self.invincible_timer > 0:
            self.invincible_timer -= dt

            # Optional: Visual flicker effect
            if int(self.invincible_timer * 20) % 2 == 0:
                self.image.set_alpha(128)  # Semi-transparent
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)  # Ensure full visibility

        # Stance Logic
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

        move_input = 0
        if self.stance == "HIGH":
            if keys[pygame.K_LEFT]:  move_input -= 1
            if keys[pygame.K_RIGHT]: move_input += 1

        # 2. Update Direction (only when moving)
        if move_input < 0: self.direction = -1
        if move_input > 0: self.direction = 1

        # Apply Acceleration
        if self.stun_timer <= 0 and move_input != 0:
            self.vel.x += move_input * ACCELERATION * dt
            # Clamp to Max Speed
            if abs(self.vel.x) > MAX_SPEED:
                self.vel.x = MAX_SPEED if self.vel.x > 0 else -MAX_SPEED
        else:
            self.apply_friction(dt)

        # Gravity & Vertical Movement
        self.apply_physics(dt, platforms)

        # Attack Timer
        if self.is_attacking:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.is_attacking = False

class IronKnuckle(Character):
    def __init__(self, x, y):
        super().__init__(x, y, color=RED, size=(32, 64))
        self.state = "CHASE"  # RECOVER, CHASE, ATTACK, COOLDOWN

    def update(self, dt, player, platforms):
        if self.is_dead:
            return

        # Decrement invincibility
        if self.invincible_timer > 0:
            self.invincible_timer -= dt

            # Optional: Visual flicker effect
            if int(self.invincible_timer * 20) % 2 == 0:
                self.image.set_alpha(128)  # Semi-transparent
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)  # Ensure full visibility

        # Calculate distance to player
        dist_x = player.rect.centerx - self.rect.centerx
        dist_abs = abs(dist_x)

        # Always face the player
        self.direction = 1 if dist_x > 0 else -1

        # State Machine
        if self.stun_timer <= 0:  #
            if self.state == "CHASE":
                if dist_abs > 75:  # If further than 75px, walk forward
                    self.vel.x += self.direction * ACCELERATION * dt
                    if abs(self.vel.x) > MAX_SPEED:
                        self.vel.x = MAX_SPEED if self.vel.x > 0 else -MAX_SPEED
                else:
                    self.apply_friction(dt)
                    if abs(self.vel.x) < 25:  # If nearly stopped, attack
                        self.state = "ATTACK"
                        self.attack_timer = 0.5
                        # 70% chance to match player stance, 30% to do the opposite
                        self.stance = player.stance if random.random() < 0.7 else ("LOW" if player.stance == "HIGH" else "HIGH")

            elif self.state == "ATTACK":
                self.attack_timer -= dt
                if self.attack_timer <= 0:
                    self.is_attacking = True
                    self.attack_timer = 0.3
                    self.state = "RECOVER"

            elif self.state == "RECOVER":
                self.attack_timer -= dt
                if self.attack_timer <= 0:
                    self.is_attacking = False
                    self.state = "COOLDOWN"
                    self.cooldown_timer = 1.0  # Wait before chasing again

            elif self.state == "COOLDOWN":
                self.cooldown_timer -= dt
                if self.cooldown_timer <= 0:
                    self.state = "CHASE"
        else:
            self.apply_friction(dt)

        self.apply_physics(dt, platforms)


