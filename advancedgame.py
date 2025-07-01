import pygame
import random
import sys
import math
from opensimplex import OpenSimplex
from pygame.locals import *
from enum import Enum
from collections import defaultdict

# Initialize Pygame
pygame.init()
pygame.font.init()
pygame.mixer.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
TILE_SIZE = 64
PLAYER_SPEED = 10
FONT = pygame.font.Font(None, 32)
LARGE_FONT = pygame.font.Font(None, 48)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

class GameState(Enum):
    EXPLORE = 0
    COMBAT = 1
    MENU = 2
    DIALOGUE = 3

class Biome(Enum):
    FOREST = {"color": (34, 139, 34), "mood": "Calm"}
    DESERT = {"color": (210, 180, 140), "mood": "Isolated"}
    MOUNTAINS = {"color": (139, 137, 137), "mood": "Achievement"}
    SWAMP = {"color": (47, 79, 79), "mood": "Anxiety"}

class ParticleSystem:
    def __init__(self):
        self.particles = []
    
    def add_particle(self, x, y, color, velocity, lifetime):
        self.particles.append({
            "x": x, "y": y,
            "color": color,
            "vx": velocity[0], "vy": velocity[1],
            "lifetime": lifetime,
            "age": 0
        })
    
    def update(self):
        for p in self.particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["age"] += 1
            if p["age"] >= p["lifetime"]:
                self.particles.remove(p)
    
    def draw(self, screen):
        for p in self.particles:
            alpha = 255 * (1 - p["age"] / p["lifetime"])
            color = (*p["color"], int(alpha))
            s = pygame.Surface((5, 5), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (2, 2), 2)
            screen.blit(s, (p["x"], p["y"]))

class Player:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.speed = PLAYER_SPEED
        self.health = 100
        self.mental_energy = 100
        self.skills = {
            "Mindfulness": 0,
            "Perspective": 0,
            "Resilience": 0
        }
        self.inventory = {
            "Positive Thoughts": [],
            "Coping Skills": ["Breathe", "Challenge", "Reframe"]
        }
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.current_skill = 0
        self.unlocked_biomes = [Biome.FOREST]
    
    def move(self, dx, dy, world):
        new_x = self.x + dx * self.speed
        new_y = self.y + dy * self.speed
        
        # Check world boundaries
        if 0 <= new_x < world.width * TILE_SIZE and 0 <= new_y < world.height * TILE_SIZE:
            self.x, self.y = new_x, new_y
            self.rect.x, self.rect.y = self.x, self.y
    
    def use_skill(self):
        skill = self.inventory["Coping Skills"][self.current_skill]
        if self.mental_energy >= 20:
            self.mental_energy -= 20
            return skill
        return None
    
    def level_up(self, skill):
        if skill in self.skills:
            self.skills[skill] += 1
            return True
        return False

class ThoughtEnemy:
    def __init__(self, x, y, negative_thought):
        self.x, self.y = x, y
        self.thought = negative_thought
        self.solution = self._generate_solution(negative_thought)
        self.health = 100
        self.attack_power = 10
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
    
    def _generate_solution(self, thought):
        solutions = {
            "I'm a failure": "I am learning",
            "I can't do this": "I will try",
            "Nobody likes me": "I am valued",
            "I'm worthless": "I have worth",
            "I'll never improve": "Growth takes time"
        }
        return solutions.get(thought, "I accept myself")
    
    def take_damage(self, typed_text):
        if typed_text.lower() == self.solution.lower():
            self.health = 0
            return True
        return False
    
    def draw(self, screen, camera_x, camera_y):
        screen_x, screen_y = self.x - camera_x, self.y - camera_y
        pygame.draw.rect(screen, RED, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
        
        # Render thought and solution
        thought_text = FONT.render(self.thought, True, WHITE)
        solution_text = FONT.render(f"Type: {self.solution}", True, GREEN)
        
        screen.blit(thought_text, (screen_x, screen_y - 30))
        screen.blit(solution_text, (screen_x, screen_y - 60))

class World:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.tiles = [[0 for _ in range(width)] for _ in range(height)]
        self._generate_terrain()
        self.thought_zones = []
        self._generate_thought_zones()
    
    def _generate_terrain(self):
        # Use OpenSimplex noise for natural biome distribution
        noise_gen = OpenSimplex(seed=42)
        for y in range(self.height):
            for x in range(self.width):
                n = noise_gen.noise2(x / 20.0, y / 20.0)
                if n < -0.2:
                    self.tiles[y][x] = Biome.SWAMP
                elif n < 0.2:
                    self.tiles[y][x] = Biome.FOREST
                elif n < 0.5:
                    self.tiles[y][x] = Biome.DESERT
                else:
                    self.tiles[y][x] = Biome.MOUNTAINS
    
    def _generate_thought_zones(self):
        for _ in range(10):
            x, y = random.randint(0, self.width-1), random.randint(0, self.height-1)
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
                biome = self.tiles[y][x]
                pygame.draw.rect(screen, biome.value["color"], rect)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Thought Bubble: Open World")
        self.clock = pygame.time.Clock()
        self.world = World(100, 100)
        self.player = Player(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
        self.camera_x, self.camera_y = 0, 0
        self.state = GameState.EXPLORE
        self.enemies = []
        self.particles = ParticleSystem()
        self.typed_text = ""
        self.message = ""
        self.message_timer = 0
    
    def run(self):
        while True:
            self._handle_input()
            self._update()
            self._render()
            self.clock.tick(60)
    
    def _handle_input(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.state = GameState.MENU
                
                # Combat typing
                if self.state == GameState.COMBAT:
                    if event.key == K_RETURN:
                        for enemy in self.enemies[:]:
                            if enemy.take_damage(self.typed_text):
                                self.enemies.remove(enemy)
                                self.particles.add_particle(
                                    enemy.x, enemy.y, 
                                    GREEN, 
                                    (random.uniform(-1, 1), random.uniform(-1, 1)), 
                                    30
                                )
                                self.player.mental_energy = min(100, self.player.mental_energy + 10)
                        if not self.enemies:
                            self.state = GameState.EXPLORE
                        self.typed_text = ""
                    
                    elif event.key == K_BACKSPACE:
                        self.typed_text = self.typed_text[:-1]
                    else:
                        self.typed_text += event.unicode
                
                # Movement in explore mode
                elif self.state == GameState.EXPLORE:
                    if event.key == K_TAB:
                        self.player.current_skill = (self.player.current_skill + 1) % len(self.player.inventory["Coping Skills"])
                    elif event.key == K_e:
                        skill = self.player.use_skill()
                        if skill:
                            self.message = f"Used {skill} skill!"
                            self.message_timer = 120
        
        # Continuous movement
        if self.state == GameState.EXPLORE:
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
    
    def _update(self):
        # Update camera
        self.camera_x = self.player.x - SCREEN_WIDTH//2
        self.camera_y = self.player.y - SCREEN_HEIGHT//2
        
        # Spawn enemies in thought zones
        if self.state == GameState.EXPLORE:
            tile_x, tile_y = int(self.player.x / TILE_SIZE), int(self.player.y / TILE_SIZE)
            if self.world.is_in_thought_zone(tile_x, tile_y) and random.random() < 0.01 and not self.enemies:
                self._start_combat(tile_x, tile_y)
        
        # Update particles
        self.particles.update()
        
        # Update message timer
        if self.message_timer > 0:
            self.message_timer -= 1
        else:
            self.message = ""
    
    def _render(self):
        self.screen.fill(BLACK)
        
        # Draw world
        self.world.draw(self.screen, self.camera_x, self.camera_y)
        
        # Draw player
        pygame.draw.rect(
            self.screen, 
            BLUE, 
            (self.player.x - self.camera_x, self.player.y - self.camera_y, TILE_SIZE, TILE_SIZE)
        )
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera_x, self.camera_y)
        
        # Draw particles
        self.particles.draw(self.screen)
        
        # Draw UI
        self._render_ui()
        
        pygame.display.flip()
    
    def _render_ui(self):
        # Health and energy bars
        pygame.draw.rect(self.screen, RED, (10, 10, 200, 20))
        pygame.draw.rect(self.screen, GREEN, (10, 10, 200 * (self.player.health / 100), 20))
        
        pygame.draw.rect(self.screen, BLUE, (10, 40, 200, 20))
        pygame.draw.rect(self.screen, YELLOW, (10, 40, 200 * (self.player.mental_energy / 100), 20))
        
        health_text = FONT.render(f"Health: {self.player.health}", True, WHITE)
        energy_text = FONT.render(f"Energy: {self.player.mental_energy}", True, WHITE)
        self.screen.blit(health_text, (220, 10))
        self.screen.blit(energy_text, (220, 40))
        
        # Current skill
        skill_text = FONT.render(f"Skill: {self.player.inventory['Coping Skills'][self.player.current_skill]} (TAB)", True, WHITE)
        self.screen.blit(skill_text, (10, 70))
        
        # Combat UI
        if self.state == GameState.COMBAT:
            input_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT - 50, 400, 40)
            pygame.draw.rect(self.screen, WHITE, input_rect, 2)
            typed_surface = FONT.render(self.typed_text, True, WHITE)
            self.screen.blit(typed_surface, (input_rect.x + 5, input_rect.y + 5))
            
            prompt = FONT.render("Type the positive thought and press ENTER", True, YELLOW)
            self.screen.blit(prompt, (SCREEN_WIDTH//2 - prompt.get_width()//2, SCREEN_HEIGHT - 80))
        
        # Message
        if self.message:
            msg_surface = FONT.render(self.message, True, YELLOW)
            self.screen.blit(msg_surface, (SCREEN_WIDTH//2 - msg_surface.get_width()//2, 100))
    
    def _start_combat(self, x, y):
        self.state = GameState.COMBAT
        thoughts = [
            "I'm a failure", "I can't do this", 
            "Nobody likes me", "I'm worthless"
        ]
        for _ in range(random.randint(1, 3)):
            ex = x * TILE_SIZE + random.randint(-100, 100)
            ey = y * TILE_SIZE + random.randint(-100, 100)
            self.enemies.append(ThoughtEnemy(ex, ey, random.choice(thoughts)))
        self.message = "Negative thoughts appear! Type the positive alternatives."
        self.message_timer = 120

if __name__ == "__main__":
    game = Game()
    game.run()