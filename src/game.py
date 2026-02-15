import pygame
import sys
from settings import *
from entities import *

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.hit_stop_timer = 0

        self.state = "MENU" # MENU, PLAYING, PAUSED, GAME_OVER

        # Game Objects
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.player = Player(SCREEN_WIDTH // 2, 100)
        self.all_sprites.add(self.player)

        # Create Level Geography
        # x, y, width, height
        level_data = [
            (400, 450, 200, 20),
            (900, 550, 400, 20),
            (100, 300, 150, 20)
        ]

        for p in level_data:
            plat = Platform(p[0], p[1], p[2], p[3])
            self.platforms.add(plat)
            self.all_sprites.add(plat)

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

            # --- GAME OVER CONTROLS ---
            if self.state == "GAME_OVER":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                return  # Stop processing other inputs if Game Over

            # --- PLAYING CONTROLS ---
            if self.state == "PLAYING":
                if event.type == pygame.KEYDOWN:
                    # Attack
                    if event.key == pygame.K_z and not self.player.is_attacking:
                        self.player.is_attacking = True
                        self.player.attack_timer = 0.15

                    # Jump
                    if (event.key == pygame.K_UP or event.key == pygame.K_x) and self.player.on_ground:
                        self.player.vel.y = JUMP_FORCE
                        self.player.on_ground = False

                    # Pause
                    if event.key == pygame.K_ESCAPE:
                        self.state = "PAUSED"

            # --- PAUSE CONTROLS ---
            elif self.state == "PAUSED":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = "PLAYING"

            elif self.state == "MENU":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.change_state("PLAYING")

    def update(self, dt):
        if self.hit_stop_timer > 0:
            self.hit_stop_timer -= dt
            return  # Skip the rest of the movement/logic

        if self.state == "PLAYING":
            if self.player.is_dead:
                self.change_state("GAME_OVER")
                return

            # Input Handling
            keys = pygame.key.get_pressed()
            # 1. Update Player explicitly with the platforms group
            self.player.update(dt, keys, self.platforms)

            for enemy in self.enemies:
                enemy.update(dt, self.player, self.platforms)
                if enemy.is_dead:
                    enemy.kill()
                    return

            # 3. Update any other sprites
            self.platforms.update(dt)

            self.resolve_combat()

    def reset_game(self):
        """Clears the board and starts a fresh session."""
        # 1. Clear all Sprite Groups
        self.all_sprites.empty()
        self.enemies.empty()
        self.platforms.empty()

        # 2. Respawn Player
        self.player = Player(SCREEN_WIDTH // 2, 100)
        self.all_sprites.add(self.player)

        # 3. Respawn Level Geometry
        level_data = [
            (400, 450, 200, 20),
            (900, 550, 400, 20),
            (100, 300, 150, 20)
        ]
        for p in level_data:
            plat = Platform(p[0], p[1], p[2], p[3])
            self.platforms.add(plat)
            self.all_sprites.add(plat)

        # 4. Respawn Enemies
        self.knuckle = IronKnuckle(200, FLOOR_Y - 64)
        self.all_sprites.add(self.knuckle)
        self.enemies.add(self.knuckle)

        # 5. Reset State
        self.state = "PLAYING"
        print("Game Reset!")

    def trigger_knockback(self, entity, direction_vector):
        """
        Pushes an entity back using velocity impulse.
        direction_vector: 1 for right, -1 for left.
        """
        # 1. Set a high initial velocity impulse
        knockback_impulse = 600
        entity.vel.x = direction_vector * knockback_impulse

        # 2. Add a vertical "hop" to make hits feel more impactful (optional)
        if entity.on_ground:
            entity.vel.y = -200
            entity.on_ground = False

        # 3. Set a stun timer (e.g., 0.2 seconds)
        # This prevents the player/AI from moving during the slide
        entity.stun_timer = 0.2

        # 4. Sync positions to prevent any 1-frame jitter
        entity.rect.x = round(entity.pos.x)

    def resolve_combat(self):
        if self.player.is_dead:
            return

        sword = self.player.get_sword_rect()
        if sword:
            for enemy in self.enemies:
                # 1. Did we hit the shield?
                if sword.colliderect(enemy.get_shield_rect()):
                    print("CLINK! Blocked!")
                    # Push player back (Knockback)
                    self.trigger_knockback(self.player, -self.player.direction)
                    self.trigger_knockback(enemy, -enemy.direction / 2)
                    self.player.is_attacking = False  # End attack on block

                # 2. Did we hit the body?
                elif sword.colliderect(enemy.rect):
                    print("HIT!")
                    enemy.take_damage(1)
                    self.trigger_knockback(enemy, self.player.direction)
                    self.hit_stop_timer = 0.08
                    self.player.is_attacking = False

        player_shield = self.player.get_shield_rect()
        for enemy in self.enemies:
            # Check Player Body
            hitbox = enemy.rect.inflate(-10, -5)
            if hitbox.colliderect(self.player.rect):
                print("PLAYER HIT!")
                self.player.take_damage(1)
                knock_dir = 1 if self.player.rect.centerx > enemy.rect.centerx else -1
                self.trigger_knockback(self.player, knock_dir)

            # Enemy Attack
            enemy_sword = enemy.get_sword_rect()
            if enemy_sword:
                # 1. Did Player Block it?
                if enemy_sword.colliderect(player_shield):
                    # In Zelda II, blocking only works if stances match
                    if self.player.stance == enemy.stance:
                        print("BLOCKED!")
                        self.trigger_knockback(self.player, -self.player.direction / 2)
                        self.trigger_knockback(enemy, -enemy.direction)
                        # enemy.is_attacking = False
                        continue  # Block successful, exit check

                # 2. Did Enemy Hit Player?
                if enemy_sword.colliderect(self.player.rect):
                    print("STABBED!")
                    self.player.take_damage(1)
                    self.trigger_knockback(self.player, enemy.direction)

    def draw(self):
        self.screen.fill(BLACK)

        if self.state == "GAME_OVER":
            text = self.font.render("GAME OVER - Press SPACE", True, RED)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text, rect)
            pygame.display.flip()
            return

        if self.state == "MENU":
            text = self.font.render("PRESS SPACE TO START", True, WHITE)
            rect = text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
            self.screen.blit(text, rect)

        elif self.state == "PLAYING" or self.state == "PAUSED":
            self.all_sprites.draw(self.screen)

            # Draw UI (Health Bar)
            hp_text = f"LIFE: {'|' * self.player.health}"
            hp_surf = self.font.render(hp_text, True, RED)
            self.screen.blit(hp_surf, (20, 20))

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
                # Draw a bright white/yellow rectangle for the "Swing"
                pygame.draw.rect(self.screen, (255, 255, 100), sword)
                # Add a small border to make it pop
                pygame.draw.rect(self.screen, WHITE, sword, 1)

            for enemy in self.enemies:
                e_sword = enemy.get_sword_rect()
                if e_sword:
                    # Enemy sword is a menacing Red/Orange
                    pygame.draw.rect(self.screen, (255, 100, 0), e_sword)

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