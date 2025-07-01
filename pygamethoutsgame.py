import pygame
import random
import sys
from pygame.locals import *

# Initialize pygame
pygame.init()
pygame.font.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 500
TILE_SIZE = 64
PLAYER_SPEED = 5
FONT = pygame.font.SysFont('Arial', 24)
LARGE_FONT = pygame.font.SysFont('Arial', 32)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

# Game states
STATE_EXPLORE = 0
STATE_COMBAT = 1

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = PLAYER_SPEED
        self.health = 100
        self.mental_energy = 100
        self.coping_skills = ["Breathe", "Challenge", "Reframe"]
        self.current_skill = 0
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        
    def move(self, dx, dy, world):
        new_x = self.x + dx * self.speed
        new_y = self.y + dy * self.speed
        
        # Check boundaries
        if 0 <= new_x < world.width * TILE_SIZE and 0 <= new_y < world.height * TILE_SIZE:
            self.x = new_x
            self.y = new_y
            self.rect.x = self.x
            self.rect.y = self.y
            
    def use_coping_skill(self):
        if self.mental_energy >= 20:
            self.mental_energy -= 20
            return self.coping_skills[self.current_skill]
        return None
    
    def draw(self, screen):
        pygame.draw.rect(screen, BLUE, self.rect)
        health_text = FONT.render(f"Health: {self.health}", True, WHITE)
        energy_text = FONT.render(f"Energy: {self.mental_energy}", True, WHITE)
        screen.blit(health_text, (10, 10))
        screen.blit(energy_text, (10, 40))

class ThoughtEnemy:
    def __init__(self, x, y, negative_thought):
        self.x = x
        self.y = y
        self.negative_thought = negative_thought
        self.positive_solution = self.generate_solution(negative_thought)
        self.health = 100
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.text_surface = FONT.render(negative_thought, True, RED)
        self.solution_surface = FONT.render(f"Type: {self.positive_solution}", True, GREEN)
        
    def generate_solution(self, thought):
        solutions = {
            "I'm a failure": "I'm learning",
            "I can't do this": "I'll try my best",
            "Nobody likes me": "I am valued",
            "I'm worthless": "I have worth",
            "I'll never improve": "Growth takes time"
        }
        return solutions.get(thought, "I accept myself")
    
    def take_damage(self, typed_text):
        if typed_text.lower() == self.positive_solution.lower():
            self.health = 0
            return True
        return False
    
    def draw(self, screen):
        pygame.draw.rect(screen, RED, self.rect)
        screen.blit(self.text_surface, (self.x, self.y - 30))
        screen.blit(self.solution_surface, (self.x, self.y - 60))

class World:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = [[0 for _ in range(width)] for _ in range(height)]
        self.generate_world()
        self.thought_zones = []
        self.generate_thought_zones()
        
    def generate_world(self):
        # Simple world generation - 0=grass, 1=water, 2=forest
        for y in range(self.height):
            for x in range(self.width):
                if random.random() < 0.1:
                    self.tiles[y][x] = 1  # Water
                elif random.random() < 0.2:
                    self.tiles[y][x] = 2  # Forest
                else:
                    self.tiles[y][x] = 0  # Grass
                    
    def generate_thought_zones(self):
        # Create areas where negative thoughts appear
        for _ in range(5):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            radius = random.randint(3, 8)
            self.thought_zones.append((x, y, radius))
            
    def is_in_thought_zone(self, x, y):
        for (zx, zy, radius) in self.thought_zones:
            if (zx - radius) <= x <= (zx + radius) and (zy - radius) <= y <= (zy + radius):
                return True
        return False
    
    def draw(self, screen, camera_x, camera_y):
        for y in range(self.height):
            for x in range(self.width):
                rect = pygame.Rect(
                    x * TILE_SIZE - camera_x, 
                    y * TILE_SIZE - camera_y, 
                    TILE_SIZE, 
                    TILE_SIZE
                )
                
                if self.tiles[y][x] == 0:  # Grass
                    pygame.draw.rect(screen, (34, 139, 34), rect)
                elif self.tiles[y][x] == 1:  # Water
                    pygame.draw.rect(screen, (0, 105, 148), rect)
                else:  # Forest
                    pygame.draw.rect(screen, (0, 100, 0), rect)
                    
                # Draw grid
                pygame.draw.rect(screen, (50, 50, 50), rect, 1)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Thought Bubble: Open World")
        self.clock = pygame.time.Clock()
        self.world = World(50, 50)
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.camera_x = 0
        self.camera_y = 0
        self.game_state = STATE_EXPLORE
        self.current_enemies = []
        self.typed_text = ""
        self.typing_active = False
        self.message = ""
        self.message_timer = 0
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == KEYDOWN:
                if self.game_state == STATE_COMBAT:
                    if event.key == K_RETURN:
                        # Check typed text against enemy solutions
                        for enemy in self.current_enemies[:]:
                            if enemy.take_damage(self.typed_text):
                                self.current_enemies.remove(enemy)
                                self.show_message(f"Defeated thought: {enemy.negative_thought}")
                                self.player.mental_energy = min(100, self.player.mental_energy + 10)
                                
                        if not self.current_enemies:
                            self.game_state = STATE_EXPLORE
                            self.show_message("All negative thoughts defeated!")
                        self.typed_text = ""
                        self.typing_active = False
                        
                    elif event.key == K_BACKSPACE:
                        self.typed_text = self.typed_text[:-1]
                    else:
                        self.typed_text += event.unicode
                        
                elif event.key == K_SPACE and self.game_state == STATE_EXPLORE:
                    self.typing_active = not self.typing_active
                    if not self.typing_active:
                        self.typed_text = ""
                        
                elif event.key == K_TAB:
                    self.player.current_skill = (self.player.current_skill + 1) % len(self.player.coping_skills)
                    self.show_message(f"Selected: {self.player.coping_skills[self.player.current_skill]}")
                    
                elif event.key == K_e and self.game_state == STATE_EXPLORE:
                    skill = self.player.use_coping_skill()
                    if skill:
                        self.show_message(f"Used {skill} skill!")
                    else:
                        self.show_message("Not enough energy!")
        
        if self.game_state == STATE_EXPLORE and not self.typing_active:
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[K_LEFT] or keys[K_a]:
                dx = -1
            if keys[K_RIGHT] or keys[K_d]:
                dx = 1
            if keys[K_UP] or keys[K_w]:
                dy = -1
            if keys[K_DOWN] or keys[K_s]:
                dy = 1
                
            self.player.move(dx, dy, self.world)
            
            # Update camera to follow player
            self.camera_x = self.player.x - SCREEN_WIDTH // 2
            self.camera_y = self.player.y - SCREEN_HEIGHT // 2
            
            # Check for entering thought zones
            tile_x = int(self.player.x / TILE_SIZE)
            tile_y = int(self.player.y / TILE_SIZE)
            
            if self.world.is_in_thought_zone(tile_x, tile_y) and random.random() < 0.02 and not self.current_enemies:
                self.start_combat(tile_x, tile_y)
                
    def start_combat(self, x, y):
        self.game_state = STATE_COMBAT
        negative_thoughts = [
            "I'm a failure",
            "I can't do this",
            "Nobody likes me",
            "I'm worthless",
            "I'll never improve"
        ]
        
        num_enemies = random.randint(1, 3)
        for _ in range(num_enemies):
            enemy_x = x * TILE_SIZE + random.randint(-100, 100)
            enemy_y = y * TILE_SIZE + random.randint(-100, 100)
            thought = random.choice(negative_thoughts)
            self.current_enemies.append(ThoughtEnemy(enemy_x, enemy_y, thought))
            
        self.show_message("Negative thoughts appear! Type the positive alternatives.")
        
    def show_message(self, msg):
        self.message = msg
        self.message_timer = 180  # 3 seconds at 60 FPS
        
    def update(self):
        if self.message_timer > 0:
            self.message_timer -= 1
        else:
            self.message = ""
            
    def draw(self):
        self.screen.fill(BLACK)
        
        # Draw world
        self.world.draw(self.screen, self.camera_x, self.camera_y)
        
        # Draw player
        player_screen_x = self.player.x - self.camera_x
        player_screen_y = self.player.y - self.camera_y
        pygame.draw.rect(
            self.screen, 
            BLUE, 
            (player_screen_x, player_screen_y, TILE_SIZE, TILE_SIZE)
        )
        
        # Draw enemies in combat
        if self.game_state == STATE_COMBAT:
            for enemy in self.current_enemies:
                enemy_screen_x = enemy.x - self.camera_x
                enemy_screen_y = enemy.y - self.camera_y
                enemy.rect.x = enemy_screen_x
                enemy.rect.y = enemy_screen_y
                enemy.draw(self.screen)
        
        # Draw UI
        self.player.draw(self.screen)
        
        # Draw current skill
        skill_text = FONT.render(
            f"Current Skill: {self.player.coping_skills[self.player.current_skill]} (TAB to change)", 
            True, 
            WHITE
        )
        self.screen.blit(skill_text, (SCREEN_WIDTH - 400, 10))
        
        # Draw typing input
        if self.typing_active or self.game_state == STATE_COMBAT:
            input_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT - 50, 400, 40)
            pygame.draw.rect(self.screen, WHITE, input_rect, 2)
            typed_surface = FONT.render(self.typed_text, True, WHITE)
            self.screen.blit(typed_surface, (input_rect.x + 5, input_rect.y + 5))
            
            if self.game_state == STATE_COMBAT:
                prompt = FONT.render("Type the positive thought and press ENTER", True, YELLOW)
                self.screen.blit(prompt, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 80))
        
        # Draw message
        if self.message:
            msg_surface = FONT.render(self.message, True, YELLOW)
            self.screen.blit(msg_surface, (SCREEN_WIDTH // 2 - msg_surface.get_width() // 2, 100))
        
        pygame.display.flip()
        
    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

if __name__ == "__main__":
    game = Game()
    game.run()