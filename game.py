import pygame
import random
import sys
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from opensimplex import OpenSimplex

# Initialize pygame
pygame.init()
pygame.font.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
FONT = pygame.font.Font(None, 32)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (100, 100, 255)
RED = (255, 100, 100)
GRAY = (100, 100, 100)

class Biome(Enum):
    SERENE_FOREST = {"color": (100, 200, 100), "mood": "Calm"}
    ANXIETY_SWAMP = {"color": (70, 90, 70), "mood": "Anxious"}
    DEPRESSION_TUNDRA = {"color": (200, 200, 255), "mood": "Depressed"}

@dataclass
class WorldChunk:
    biome: Biome
    height: float
    objects: List = field(default_factory=list)

class WorldGenerator:
    def __init__(self):
        self.noise = OpenSimplex(seed=42)
    
    def generate_chunk(self, x: int, y: int) -> WorldChunk:
        height = self.noise.noise2(x/50, y/50)
        moisture = self.noise.noise2(x/30+100, y/30+100)
        
        if height < -0.2:
            return WorldChunk(Biome.DEPRESSION_TUNDRA, height)
        elif moisture > 0.3:
            return WorldChunk(Biome.ANXIETY_SWAMP, height)
        else:
            return WorldChunk(Biome.SERENE_FOREST, height)

@dataclass 
class Player:
    pos: Tuple[float, float] = (0, 0)
    health: float = 100.0
    skills: Dict[str, int] = field(default_factory=lambda: {
        "Mindfulness": 1,
        "Cognitive Restructuring": 1
    })

class ThoughtEnemy:
    def __init__(self, negative_thought: str, pos: Tuple[float, float]):
        self.thought = negative_thought
        self.pos = pos
        self.solution = self._generate_solution()
        self.health = 100
    
    def _generate_solution(self) -> str:
        solutions = {
            "I'm worthless": "I have value",
            "I can't do this": "I can try",
            "Nobody cares": "People care"
        }
        return solutions.get(self.thought, "I accept myself")

class MentalStateRenderer:
    def __init__(self):
        self.shaders = {
            "Calm": self._render_calm,
            "Anxious": self._render_anxious,
            "Depressed": self._render_depressed
        }
    
    def _render_calm(self, surface):
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((*BLUE, 30))
        surface.blit(overlay, (0, 0))
        for _ in range(5):
            x, y = random.randint(0, surface.get_width()), random.randint(0, surface.get_height())
            pygame.draw.circle(surface, (*BLUE, 50), (x, y), 2)
    
    def _render_anxious(self, surface):
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((*RED, 40))
        surface.blit(overlay, (0, 0))
        for _ in range(15):
            x, y = random.randint(0, surface.get_width()), random.randint(0, surface.get_height())
            pygame.draw.circle(surface, (*RED, 100), (x, y), 3)
    
    def _render_depressed(self, surface):
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((*GRAY, 60))
        surface.blit(overlay, (0, 0))
        for _ in range(8):
            x, y = random.randint(0, surface.get_width()), random.randint(0, surface.get_height())
            pygame.draw.circle(surface, (*GRAY, 150), (x, y), 4)
    
    def apply(self, mood: str, surface):
        if mood in self.shaders:
            self.shaders[mood](surface)

class ThoughtScapeGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("ThoughtScape")
        self.clock = pygame.time.Clock()
        
        self.world = WorldGenerator()
        self.player = Player()
        self.renderer = MentalStateRenderer()
        self.current_chunk = self.world.generate_chunk(0, 0)
        self.enemies = []
        self.current_mood = "Calm"
        self.typed_text = ""

    def _handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and self.enemies:
                    for enemy in self.enemies[:]:
                        if self.typed_text.lower() == enemy.solution.lower():
                            self.enemies.remove(enemy)
                    self.typed_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    self.typed_text = self.typed_text[:-1]
                else:
                    self.typed_text += event.unicode

    def _update(self):
        # Spawn enemies randomly
        if random.random() < 0.01 and not self.enemies:
            thoughts = ["I'm worthless", "I can't do this", "Nobody cares"]
            self.enemies.append(ThoughtEnemy(
                random.choice(thoughts),
                (random.randint(100, SCREEN_WIDTH-100), random.randint(100, SCREEN_HEIGHT-100))
            ))
        
        # Update mood based on game state
        if self.player.health < 40 or self.enemies:
            self.current_mood = "Anxious"
        else:
            self.current_mood = "Calm"

    def _render(self):
        self.screen.fill(BLACK)
        
        # Draw world background
        pygame.draw.rect(self.screen, self.current_chunk.biome.value["color"], (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Draw player
        pygame.draw.circle(self.screen, WHITE, (int(SCREEN_WIDTH/2), int(SCREEN_HEIGHT/2)), 20)
        
        # Draw enemies
        for enemy in self.enemies:
            pygame.draw.circle(self.screen, RED, (int(enemy.pos[0]), int(enemy.pos[1])), 30)
            thought_text = FONT.render(enemy.thought, True, WHITE)
            solution_text = FONT.render(f"Type: {enemy.solution}", True, WHITE)
            self.screen.blit(thought_text, (enemy.pos[0] - thought_text.get_width()/2, enemy.pos[1] - 50))
            self.screen.blit(solution_text, (enemy.pos[0] - solution_text.get_width()/2, enemy.pos[1] - 80))
        
        # Apply mood effects
        self.renderer.apply(self.current_mood, self.screen)
        
        # Draw UI
        health_text = FONT.render(f"Health: {self.player.health}", True, WHITE)
        self.screen.blit(health_text, (20, 20))
        
        if self.enemies:
            input_rect = pygame.Rect(SCREEN_WIDTH/2 - 200, SCREEN_HEIGHT - 60, 400, 40)
            pygame.draw.rect(self.screen, WHITE, input_rect, 2)
            text_surface = FONT.render(self.typed_text, True, WHITE)
            self.screen.blit(text_surface, (input_rect.x + 10, input_rect.y + 10))
        
        pygame.display.flip()

    def run(self):
        while True:
            self._handle_input()
            self._update()
            self._render()
            self.clock.tick(60)

if __name__ == "__main__":
    game = ThoughtScapeGame()
    game.run()