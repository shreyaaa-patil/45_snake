from array import array
import math

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

        self.difficulty_speeds = {"Easy": 5, "Medium": 8, "Hard": 12}
        self.game_over_options = ("Easy", "Medium", "Hard", "Exit")
        self.font = pygame.font.SysFont("Arial", 30)
        self.game_over_font = pygame.font.SysFont("Arial", 52, bold=True)
        self.menu_font = pygame.font.SysFont("Arial", 26)
        self.prompt_font = pygame.font.SysFont("Arial", 20)
        self.eat_sound = None
        self.game_over_sound = None
        self._load_sound_effects()

        self.game_over_selection = 1
        self.game_over = False
        self.paused = False
        self.reset_game("Medium")

    def _load_sound_effects(self):
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            self.eat_sound = self._create_tone(650, 1050, 0.12, 0.2)
            self.game_over_sound = self._create_tone(420, 110, 0.45, 0.25)
        except pygame.error:
            self.eat_sound = None
            self.game_over_sound = None

    @staticmethod
    def _create_tone(start_frequency, end_frequency, duration, volume):
        sample_rate, _, channels = pygame.mixer.get_init()
        frame_count = int(sample_rate * duration)
        samples = array("h")
        phase = 0.0

        for frame in range(frame_count):
            progress = frame / max(1, frame_count - 1)
            frequency = start_frequency + (end_frequency - start_frequency) * progress
            attack = min(1.0, frame / max(1, int(sample_rate * 0.01)))
            release = min(1.0, (frame_count - frame) / max(1, int(sample_rate * 0.04)))
            value = int(32767 * volume * min(attack, release) * math.sin(phase))
            samples.extend([value] * channels)
            phase += 2 * math.pi * frequency / sample_rate

        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _play_sound(self, sound):
        if sound is not None:
            sound.play()

    def _end_game(self):
        self.game_over = True
        self._play_sound(self.game_over_sound)

    def reset_game(self, difficulty):
        self.difficulty = difficulty
        self.snake = Snake(self.grid_width // 2, self.grid_height // 2, self.cell_size)
        self._last_move_direction = self.snake.direction
        self.food = Food(self.grid_width, self.grid_height, self.cell_size)
        self.food.respawn(self.snake.body)
        self.score = 0
        self.moves_per_second = self.difficulty_speeds[difficulty]
        self._frame_counter = 0
        self.game_over = False
        self.paused = False
        self.game_over_selection = self.game_over_options.index(difficulty)

    def handle_keydown(self, key):
        if self.game_over:
            if key in (pygame.K_UP, pygame.K_w):
                self.game_over_selection = (self.game_over_selection - 1) % len(self.game_over_options)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.game_over_selection = (self.game_over_selection + 1) % len(self.game_over_options)
            elif key == pygame.K_ESCAPE:
                return "exit"
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                selection = self.game_over_options[self.game_over_selection]
                if selection == "Exit":
                    return "exit"
                self.reset_game(selection)
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
            self._end_game()
            return

        if self.snake.collides_with_self():
            self._end_game()
            return

        if self.snake.head_rect().colliderect(self.food.rect()):
            self._play_sound(self.eat_sound)
            self.snake.grow()
            self.score += 1
            self.food.respawn(self.snake.body)

    def render(self, screen):
        if self.game_over:
            screen.fill(BLACK)
            title = self.game_over_font.render("Game Over", True, RED)
            score = self.font.render(f"Final Score: {self.score}", True, WHITE)
            heading = self.menu_font.render("Choose difficulty", True, WHITE)
            screen.blit(title, title.get_rect(center=(self.width // 2, 90)))
            screen.blit(score, score.get_rect(center=(self.width // 2, 155)))
            screen.blit(heading, heading.get_rect(center=(self.width // 2, 225)))

            for index, option in enumerate(self.game_over_options):
                color = GREEN if index == self.game_over_selection else WHITE
                if option == "Exit":
                    label = option
                else:
                    label = f"{option} ({self.difficulty_speeds[option]} moves/sec)"
                if index == self.game_over_selection:
                    label = f"> {label} <"
                option_text = self.menu_font.render(label, True, color)
                screen.blit(option_text, option_text.get_rect(center=(self.width // 2, 285 + index * 48)))

            prompt = self.prompt_font.render("Up/Down: choose   Enter: confirm   Esc: exit", True, WHITE)
            screen.blit(prompt, prompt.get_rect(center=(self.width // 2, self.height - 35)))
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
