import pygame
from .snake import Snake
from .food import Food

# Game Engine

WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
RED = (220, 60, 60)
BLACK = (0, 0, 0)

class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cell_size = 20
        self.grid_width = width // self.cell_size
        self.grid_height = height // self.cell_size

        self.snake = Snake(self.grid_width // 2, self.grid_height // 2, self.cell_size)
        self._last_move_direction = self.snake.direction
        self.food = Food(self.grid_width, self.grid_height, self.cell_size)

        self.score = 0
        self.font = pygame.font.SysFont("Arial", 30)
        self.game_over_font = pygame.font.SysFont("Arial", 52, bold=True)
        self.prompt_font = pygame.font.SysFont("Arial", 22)

        self.moves_per_second = 8
        self._frame_counter = 0

        self.game_over = False
        self.paused = False

    def handle_keydown(self, key):
        if self.game_over:
            return

        directions = {
            pygame.K_UP: (0, -1),
            pygame.K_w: (0, -1),
            pygame.K_DOWN: (0, 1),
            pygame.K_s: (0, 1),
            pygame.K_LEFT: (-1, 0),
            pygame.K_a: (-1, 0),
            pygame.K_RIGHT: (1, 0),
            pygame.K_d: (1, 0),
        }
        direction = directions.get(key)
        if direction is None:
            return

        current_dx, current_dy = self._last_move_direction
        if direction == (-current_dx, -current_dy):
            self.paused = True
            return

        self.snake.set_direction(*direction)
        self.paused = False

    def handle_input(self):
        # Reserved for continuously-held-key input (not used for a
        # grid-based snake, but kept here to mirror the engine's shape).
        pass

    def update(self):
        if self.game_over or self.paused:
            return

        self._frame_counter += 1
        frames_per_move = max(1, 60 // self.moves_per_second)
        if self._frame_counter < frames_per_move:
            return
        self._frame_counter = 0

        self.snake.move()
        self._last_move_direction = self.snake.direction

        if self.snake.collides_with_wall(self.grid_width, self.grid_height):
            self.game_over = True
            return

        if self.snake.collides_with_self():
            self.game_over = True
            return

        if self.snake.head_rect().colliderect(self.food.rect()):
            self.snake.grow()
            self.score += 1
            self.food.respawn(self.snake.body)

    def render(self, screen):
        if self.game_over:
            screen.fill(BLACK)
            title = self.game_over_font.render("Game Over", True, RED)
            score = self.font.render(f"Final Score: {self.score}", True, WHITE)
            prompt = self.prompt_font.render("Press any key to exit", True, WHITE)
            screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 2 - 70)))
            screen.blit(score, score.get_rect(center=(self.width // 2, self.height // 2)))
            screen.blit(prompt, prompt.get_rect(center=(self.width // 2, self.height // 2 + 60)))
            return

        # Draw food
        pygame.draw.rect(screen, RED, self.food.rect())

        # Draw snake
        for rect in self.snake.segment_rects():
            pygame.draw.rect(screen, GREEN, rect)

        # Draw score
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        if self.paused and not self.game_over:
            paused_text = self.font.render("Paused", True, WHITE)
            screen.blit(paused_text, paused_text.get_rect(center=(self.width // 2, self.height // 2)))
