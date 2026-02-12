import pygame
import sys
from settings import *
from entities import Entity, Player, IronKnuckle

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        self.state = "MENU" # MENU, PLAYING, PAUSED, GAME_OVER

        # Game Objects
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.all_sprites.add(self.player)

        # Spawn our first enemy
        self.knuckle = IronKnuckle(200, FLOOR_Y - 64)
        self.all_sprites.add(self.knuckle)
        self.enemies.add(self.knuckle)  # Add to both groups!

        # Font (Default system font)
        self.font = pygame.font.SysFont("arial", 32)

    def change_state(self, new_state):
        """Handles all one-time transitions."""
        if self.state == new_state:
            return

        prev_state = self.state
        self.state = new_state

        # --- TRANSITION LOGIC ---
        if new_state == "PLAYING":
            if prev_state == "MENU":
                print("Starting New Game...")
                # Reset logic goes here
            elif prev_state == "PAUSED":
                print("Resuming...")

        elif new_state == "PAUSED":
            print("Game Paused")

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Global Toggles
            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_z:  # Attack key
                    if not self.player.is_attacking:
                        self.player.is_attacking = True
                        self.player.attack_timer = 0.15  # Fast Zelda-style thrust

                if event.key == pygame.K_UP or event.key == pygame.K_x:
                    if self.player.on_ground:
                        self.player.vel.y = JUMP_FORCE
                        self.player.on_ground = False

                if event.key == pygame.K_z:  # Attack Key
                    self.player.is_attacking = True
                    self.player.attack_timer = 0.2  # Swords are fast!
                    self.check_combat_collision()


                if event.key == pygame.K_ESCAPE:
                    if self.state == "PLAYING":
                        self.change_state("PAUSED")
                    elif self.state == "PAUSED":
                        self.change_state("PLAYING")

                if event.key == pygame.K_SPACE and self.state == "MENU":
                    self.change_state("PLAYING")

    def update(self, dt):
        if self.state == "PLAYING":
            # Input Handling
            keys = pygame.key.get_pressed()
            self.player.vel.x = 0
            if keys[pygame.K_LEFT]:  self.player.vel.x = -self.player.speed
            if keys[pygame.K_RIGHT]: self.player.vel.x = self.player.speed

            self.all_sprites.update(dt, keys=keys)

            self.resolve_combat()

    def check_combat_collision(self):
        # Define a small rectangle in front of the player
        sword_rect = pygame.Rect(0, 0, 40, 10)
        if self.player.direction == 1:
            sword_rect.midleft = self.player.rect.midright
        else:
            sword_rect.midright = self.player.rect.midleft

        # Offset for high/low
        if self.player.stance == "LOW":
            sword_rect.y += 20

        # Check against enemies
        for enemy in self.enemies:
            self.resolve_combat()

    def trigger_knockback(self, entity, direction_vector):
        """
        Pushes an entity back.
        direction_vector: 1 for right, -1 for left.
        """
        knockback_distance = 50
        entity.pos.x += direction_vector * knockback_distance
        # Immediately sync the rect so the change is visible this frame
        entity.rect.x = round(entity.pos.x)

        # Optional: Set velocity to 0 to stop current movement
        entity.vel.x = 0

    def resolve_combat(self):
        sword = self.player.get_sword_rect()
        if sword is None:
            return

        for enemy in self.enemies:
            shield = enemy.get_shield_rect()

            # 1. Did we hit the shield?
            if sword.colliderect(shield):
                print("CLINK! Blocked!")
                # Push player back (Knockback)
                self.trigger_knockback(self.player, -self.player.direction)
                self.player.is_attacking = False  # End attack on block
                return

            # 2. Did we hit the body?
            if sword.colliderect(enemy.rect):
                print("HIT!")
                enemy.take_damage(1)
                self.trigger_knockback(enemy, self.player.direction)
                self.player.is_attacking = False

    def draw(self):
        self.screen.fill(BLACK)

        if self.state == "MENU":
            text = self.font.render("PRESS SPACE TO START", True, WHITE)
            rect = text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
            self.screen.blit(text, rect)

        elif self.state == "PLAYING" or self.state == "PAUSED":
            self.all_sprites.draw(self.screen)

            # Temporarily draw the hitboxes so you can see them!
            shield = self.player.get_shield_rect()
            pygame.draw.rect(self.screen, (0, 0, 255), shield, 2)  # Blue outline for shield

            # Debug Drawing
            for enemy in self.enemies:
                # Draw Enemy Shield in Blue
                pygame.draw.rect(self.screen, CYAN, enemy.get_shield_rect(), 2)

            # Draw Player Sword in White when attacking
            sword = self.player.get_sword_rect()
            if sword is not None:
                pygame.draw.rect(self.screen, WHITE, sword)

            if self.state == "PAUSED":
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 128))  # Semi-transparent black
                self.screen.blit(overlay, (0, 0))

                pause_text = self.font.render("PAUSED", True, WHITE)
                self.screen.blit(pause_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2))


        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()