import pygame
import sys
import random
import json
import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db, auth
import pyrebase

# Initialize pygame
pygame.init()
pygame.font.init()

# Firebase Configuration
FIREBASE_API_KEY = "AIzaSyBslVrw8gUYRkjpGHKWeftbvDp0-oBa9w0"
FIREBASE_DB_URL = "https://csgame-f1969-default-rtdb.firebaseio.com"

# Screen dimensions
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Thought Bubble - Mental Well-being Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (245, 245, 245)
BLUE = (33, 150, 243)
DARK_BLUE = (13, 71, 161)
GREEN = (76, 175, 80)
RED = (244, 67, 54)
ORANGE = (255, 152, 0)
YELLOW = (255, 235, 59)
PURPLE = (103, 58, 183)
PEACH = (255, 218, 185)

# Fonts
TITLE_FONT = pygame.font.SysFont("Segoe UI", 36, bold=True)
HEADER_FONT = pygame.font.SysFont("Segoe UI", 24, bold=True)
BUTTON_FONT = pygame.font.SysFont("Segoe UI", 18)
TEXT_FONT = pygame.font.SysFont("Segoe UI", 16)
SMALL_FONT = pygame.font.SysFont("Segoe UI", 14)

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=WHITE, rounded=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.rounded = rounded
        self.is_hovered = False
        
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        
        if self.rounded:
            pygame.draw.rect(surface, color, self.rect, border_radius=8)
        else:
            pygame.draw.rect(surface, color, self.rect)
            
        text_surf = BUTTON_FONT.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
        
    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False

class InputBox:
    def __init__(self, x, y, width, height, placeholder="", is_password=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = (220, 220, 220)
        self.text = ""
        self.placeholder = placeholder
        self.is_password = is_password
        self.active = False
        self.font = TEXT_FONT
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
        return False
        
    def draw(self, surface):
        pygame.draw.rect(surface, WHITE, self.rect, border_radius=4)
        pygame.draw.rect(surface, self.color if not self.active else BLUE, self.rect, 2, border_radius=4)
        
        if not self.text and not self.active:
            text_surf = self.font.render(self.placeholder, True, (150, 150, 150))
            surface.blit(text_surf, (self.rect.x + 10, self.rect.y + (self.rect.height - text_surf.get_height()) // 2))
        else:
            display_text = "*" * len(self.text) if self.is_password else self.text
            text_surf = self.font.render(display_text, True, BLACK)
            surface.blit(text_surf, (self.rect.x + 10, self.rect.y + (self.rect.height - text_surf.get_height()) // 2))

class ThoughtGame:
    def __init__(self):
        # Initialize Firebase
        self.initialize_firebase()
        
        # Game state
        self.current_screen = "login"
        self.running = True
        
        # User data
        self.user = None
        self.user_data = None
        self.is_admin = False
        
        # Game data
        self.score = 0
        self.correct_streak = 0
        self.wrong_streak = 0
        self.current_difficulty = "Easy"
        self.time_pressure_mode = False
        self.time_left = 30
        self.current_question_index = 0
        self.questions = []
        self.current_questions = []
        
        # Journal
        self.journal_entries = []
        self.selected_journal_entry = -1
        
        # UI elements
        self.create_ui_elements()
        
        # Timer
        self.clock = pygame.time.Clock()
        self.game_timer_event = pygame.USEREVENT + 1
        pygame.time.set_timer(self.game_timer_event, 1000)
        
        # Load initial questions
        self.load_questions_from_firebase()
    
    def initialize_firebase(self):
        try:
            cred = credentials.Certificate("csgame-f1969-firebase-adminsdk-fbsvc-a042dd397c.json")
            firebase_admin.initialize_app(cred, {
                'databaseURL': FIREBASE_DB_URL
            })
            
            firebase_config = {
                "apiKey": FIREBASE_API_KEY,
                "authDomain": "csgame-f1969.firebaseapp.com",
                "databaseURL": FIREBASE_DB_URL,
                "projectId": "csgame-f1969",
                "storageBucket": "csgame-f1969.appspot.com",
                "messagingSenderId": "235095144063",
                "appId": "1:235095144063:web:e271e1fcb09d11b9eaf14a"
            }
            
            self.pyrebase = pyrebase.initialize_app(firebase_config)
            self.db = self.pyrebase.database()
            self.auth = self.pyrebase.auth()
            self.admin_db = db
            self.admin_auth = auth
            
        except FileNotFoundError:
            self.show_message("Firebase Error", "Firebase credentials file not found.")
        except Exception as e:
            self.show_message("Firebase Error", f"Failed to initialize Firebase: {str(e)}")
    
    def create_ui_elements(self):
        # Login screen elements
        self.login_email = InputBox(SCREEN_WIDTH//2 - 150, 200, 300, 40, "Email")
        self.login_password = InputBox(SCREEN_WIDTH//2 - 150, 260, 300, 40, "Password", True)
        self.login_btn = Button(SCREEN_WIDTH//2 - 100, 320, 200, 50, "Login", BLUE, (25, 118, 210), rounded=True)
        self.register_btn = Button(SCREEN_WIDTH//2 - 100, 380, 200, 50, "Register", ORANGE, (245, 124, 0), rounded=True)
        
        # Register screen elements
        self.register_name = InputBox(SCREEN_WIDTH//2 - 150, 180, 300, 40, "Full Name")
        self.register_email = InputBox(SCREEN_WIDTH//2 - 150, 240, 300, 40, "Email")
        self.register_password = InputBox(SCREEN_WIDTH//2 - 150, 300, 300, 40, "Password (min 6 chars)", True)
        self.register_submit_btn = Button(SCREEN_WIDTH//2 - 100, 380, 200, 50, "Register", ORANGE, (245, 124, 0), rounded=True)
        self.register_back_btn = Button(SCREEN_WIDTH//2 - 100, 450, 200, 40, "Back to Login", (150, 150, 150), (180, 180, 180), rounded=True)
        
        # Main menu elements
        self.play_btn = Button(SCREEN_WIDTH//2 - 150, 200, 300, 60, "Play Game", BLUE, (25, 118, 210), rounded=True)
        self.journal_btn = Button(SCREEN_WIDTH//2 - 150, 280, 300, 60, "My Journal", GREEN, (56, 142, 60), rounded=True)
        self.leaderboard_btn = Button(SCREEN_WIDTH//2 - 150, 360, 300, 60, "Leaderboard", ORANGE, (245, 124, 0), rounded=True)
        self.settings_btn = Button(SCREEN_WIDTH//2 - 150, 440, 300, 60, "Settings", (150, 150, 150), (180, 180, 180), rounded=True)
        self.admin_btn = Button(SCREEN_WIDTH//2 - 150, 520, 300, 60, "Admin Panel", PURPLE, (81, 45, 168), rounded=True)
        self.logout_btn = Button(20, SCREEN_HEIGHT - 70, 100, 40, "Logout", RED, (211, 47, 47), rounded=True)
        self.quit_btn = Button(SCREEN_WIDTH - 120, SCREEN_HEIGHT - 70, 100, 40, "Quit", (150, 150, 150), (180, 180, 180), rounded=True)
        
        # Game screen elements
        self.accept_btn = Button(SCREEN_WIDTH//2 - 220, 500, 200, 50, "✔ Accept Thought", GREEN, (56, 142, 60), rounded=True)
        self.reject_btn = Button(SCREEN_WIDTH//2 + 20, 500, 200, 50, "✘ Reject Thought", RED, (211, 47, 47), rounded=True)
        self.game_menu_btn = Button(20, 20, 120, 40, "← Main Menu", BLUE, (25, 118, 210), rounded=True)
        self.journal_add_btn = Button(SCREEN_WIDTH - 170, 20, 150, 40, "📝 Add to Journal", ORANGE, (245, 124, 0), rounded=True)
        
        # Journal screen elements
        self.journal_back_btn = Button(20, 20, 120, 40, "← Main Menu", BLUE, (25, 118, 210), rounded=True)
        self.journal_delete_btn = Button(SCREEN_WIDTH - 120, SCREEN_HEIGHT - 70, 100, 40, "Delete", RED, (211, 47, 47), rounded=True)
        
        # Settings screen elements
        self.difficulty_combo = Button(SCREEN_WIDTH//2 - 50, 150, 200, 40, self.current_difficulty, WHITE, WHITE, BLACK)
        self.time_pressure_toggle = Button(SCREEN_WIDTH//2 - 50, 250, 200, 40, "On" if self.time_pressure_mode else "Off", WHITE, WHITE, BLACK)
        self.time_limit_slider_pos = SCREEN_WIDTH//2 - 100
        self.time_limit_slider = Button(self.time_limit_slider_pos, 350, 200, 20, "", BLUE, BLUE)
        self.time_limit_value = self.time_left
        self.settings_back_btn = Button(SCREEN_WIDTH//2 - 100, 450, 200, 50, "Back to Menu", BLUE, (25, 118, 210), rounded=True)
        
        # Leaderboard screen elements
        self.leaderboard_back_btn = Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 70, 200, 50, "Back to Menu", BLUE, (25, 118, 210), rounded=True)
        self.refresh_leaderboard_btn = Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 130, 200, 50, "Refresh", GREEN, (56, 142, 60), rounded=True)
        
        # Admin screen elements
        self.admin_back_btn = Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 70, 200, 50, "Back to Menu", BLUE, (25, 118, 210), rounded=True)
        self.add_question_btn = Button(SCREEN_WIDTH//2 - 250, SCREEN_HEIGHT - 70, 200, 50, "Add Question", GREEN, (56, 142, 60), rounded=True)
        self.refresh_questions_btn = Button(SCREEN_WIDTH//2 + 50, SCREEN_HEIGHT - 70, 200, 50, "Refresh", BLUE, (25, 118, 210), rounded=True)
    
    def run(self):
        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                if event.type == self.game_timer_event and self.current_screen == "game" and self.time_pressure_mode:
                    self.update_timer()
                
                # Handle screen-specific events
                if self.current_screen == "login":
                    self.handle_login_events(event, mouse_pos)
                elif self.current_screen == "register":
                    self.handle_register_events(event, mouse_pos)
                elif self.current_screen == "menu":
                    self.handle_menu_events(event, mouse_pos)
                elif self.current_screen == "game":
                    self.handle_game_events(event, mouse_pos)
                elif self.current_screen == "journal":
                    self.handle_journal_events(event, mouse_pos)
                elif self.current_screen == "settings":
                    self.handle_settings_events(event, mouse_pos)
                elif self.current_screen == "leaderboard":
                    self.handle_leaderboard_events(event, mouse_pos)
                elif self.current_screen == "admin":
                    self.handle_admin_events(event, mouse_pos)
            
            # Drawing
            screen.fill(LIGHT_GRAY)
            
            if self.current_screen == "login":
                self.draw_login_screen(mouse_pos)
            elif self.current_screen == "register":
                self.draw_register_screen(mouse_pos)
            elif self.current_screen == "menu":
                self.draw_menu_screen(mouse_pos)
            elif self.current_screen == "game":
                self.draw_game_screen(mouse_pos)
            elif self.current_screen == "journal":
                self.draw_journal_screen(mouse_pos)
            elif self.current_screen == "settings":
                self.draw_settings_screen(mouse_pos)
            elif self.current_screen == "leaderboard":
                self.draw_leaderboard_screen(mouse_pos)
            elif self.current_screen == "admin":
                self.draw_admin_screen(mouse_pos)
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()
    
    # Screen event handlers
    def handle_login_events(self, event, mouse_pos):
        self.login_email.handle_event(event)
        self.login_password.handle_event(event)
        
        if self.login_btn.check_hover(mouse_pos):
            if self.login_btn.is_clicked(mouse_pos, event):
                self.login()
        elif self.register_btn.check_hover(mouse_pos):
            if self.register_btn.is_clicked(mouse_pos, event):
                self.current_screen = "register"
    
    def handle_register_events(self, event, mouse_pos):
        self.register_name.handle_event(event)
        self.register_email.handle_event(event)
        self.register_password.handle_event(event)
        
        if self.register_submit_btn.check_hover(mouse_pos):
            if self.register_submit_btn.is_clicked(mouse_pos, event):
                self.register()
        elif self.register_back_btn.check_hover(mouse_pos):
            if self.register_back_btn.is_clicked(mouse_pos, event):
                self.current_screen = "login"
    
    def handle_menu_events(self, event, mouse_pos):
        if self.play_btn.check_hover(mouse_pos):
            if self.play_btn.is_clicked(mouse_pos, event):
                self.start_game()
        elif self.journal_btn.check_hover(mouse_pos):
            if self.journal_btn.is_clicked(mouse_pos, event):
                self.current_screen = "journal"
        elif self.leaderboard_btn.check_hover(mouse_pos):
            if self.leaderboard_btn.is_clicked(mouse_pos, event):
                self.current_screen = "leaderboard"
                self.update_leaderboard()
        elif self.settings_btn.check_hover(mouse_pos):
            if self.settings_btn.is_clicked(mouse_pos, event):
                self.current_screen = "settings"
        elif self.admin_btn.check_hover(mouse_pos) and self.is_admin:
            if self.admin_btn.is_clicked(mouse_pos, event):
                self.current_screen = "admin"
                self.load_questions()
        elif self.logout_btn.check_hover(mouse_pos):
            if self.logout_btn.is_clicked(mouse_pos, event):
                self.logout()
        elif self.quit_btn.check_hover(mouse_pos):
            if self.quit_btn.is_clicked(mouse_pos, event):
                self.running = False
    
    def handle_game_events(self, event, mouse_pos):
        if self.accept_btn.check_hover(mouse_pos):
            if self.accept_btn.is_clicked(mouse_pos, event):
                self.evaluate_thought("accept")
        elif self.reject_btn.check_hover(mouse_pos):
            if self.reject_btn.is_clicked(mouse_pos, event):
                self.evaluate_thought("reject")
        elif self.game_menu_btn.check_hover(mouse_pos):
            if self.game_menu_btn.is_clicked(mouse_pos, event):
                self.current_screen = "menu"
        elif self.journal_add_btn.check_hover(mouse_pos):
            if self.journal_add_btn.is_clicked(mouse_pos, event):
                self.add_current_to_journal()
    
    def handle_journal_events(self, event, mouse_pos):
        if self.journal_back_btn.check_hover(mouse_pos):
            if self.journal_back_btn.is_clicked(mouse_pos, event):
                self.current_screen = "menu"
        elif self.journal_delete_btn.check_hover(mouse_pos):
            if self.journal_delete_btn.is_clicked(mouse_pos, event):
                self.delete_journal_entry()
        
        # Handle journal entry selection
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, entry in enumerate(self.journal_entries):
                entry_rect = pygame.Rect(50, 100 + i * 40, SCREEN_WIDTH - 100, 30)
                if entry_rect.collidepoint(event.pos):
                    self.selected_journal_entry = i
                    break
    
    def handle_settings_events(self, event, mouse_pos):
        if self.difficulty_combo.check_hover(mouse_pos):
            if self.difficulty_combo.is_clicked(mouse_pos, event):
                difficulties = ["Easy", "Medium", "Hard"]
                current_index = difficulties.index(self.current_difficulty)
                new_index = (current_index + 1) % len(difficulties)
                self.current_difficulty = difficulties[new_index]
                self.difficulty_combo.text = self.current_difficulty
        elif self.time_pressure_toggle.check_hover(mouse_pos):
            if self.time_pressure_toggle.is_clicked(mouse_pos, event):
                self.time_pressure_mode = not self.time_pressure_mode
                self.time_pressure_toggle.text = "On" if self.time_pressure_mode else "Off"
        elif self.time_limit_slider.check_hover(mouse_pos):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.dragging_slider = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging_slider = False
        elif self.settings_back_btn.check_hover(mouse_pos):
            if self.settings_back_btn.is_clicked(mouse_pos, event):
                self.current_screen = "menu"
        
        # Handle slider dragging
        if hasattr(self, 'dragging_slider') and self.dragging_slider:
            mouse_x = pygame.mouse.get_pos()[0]
            # Constrain slider position
            mouse_x = max(SCREEN_WIDTH//2 - 100, min(mouse_x, SCREEN_WIDTH//2 + 100))
            self.time_limit_slider_pos = mouse_x
            self.time_limit_slider.rect.x = self.time_limit_slider_pos
            # Calculate value (10-60)
            self.time_limit_value = 10 + int((mouse_x - (SCREEN_WIDTH//2 - 100)) / 2)
            self.time_left = self.time_limit_value
    
    def handle_leaderboard_events(self, event, mouse_pos):
        if self.leaderboard_back_btn.check_hover(mouse_pos):
            if self.leaderboard_back_btn.is_clicked(mouse_pos, event):
                self.current_screen = "menu"
        elif self.refresh_leaderboard_btn.check_hover(mouse_pos):
            if self.refresh_leaderboard_btn.is_clicked(mouse_pos, event):
                self.update_leaderboard()
    
    def handle_admin_events(self, event, mouse_pos):
        if self.admin_back_btn.check_hover(mouse_pos):
            if self.admin_back_btn.is_clicked(mouse_pos, event):
                self.current_screen = "menu"
        elif self.add_question_btn.check_hover(mouse_pos):
            if self.add_question_btn.is_clicked(mouse_pos, event):
                self.add_question()
        elif self.refresh_questions_btn.check_hover(mouse_pos):
            if self.refresh_questions_btn.is_clicked(mouse_pos, event):
                self.load_questions()
    
    # Screen drawing methods
    def draw_login_screen(self, mouse_pos):
        # Title
        title = TITLE_FONT.render("Thought Bubble", True, DARK_BLUE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
        
        subtitle = HEADER_FONT.render("Improve your mental well-being", True, BLUE)
        screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, 140))
        
        # Input boxes
        email_label = TEXT_FONT.render("Email:", True, BLACK)
        screen.blit(email_label, (SCREEN_WIDTH//2 - 150, 180))
        self.login_email.draw(screen)
        
        password_label = TEXT_FONT.render("Password:", True, BLACK)
        screen.blit(password_label, (SCREEN_WIDTH//2 - 150, 240))
        self.login_password.draw(screen)
        
        # Buttons
        self.login_btn.check_hover(mouse_pos)
        self.login_btn.draw(screen)
        
        self.register_btn.check_hover(mouse_pos)
        self.register_btn.draw(screen)
    
    def draw_register_screen(self, mouse_pos):
        # Title
        title = TITLE_FONT.render("Register", True, DARK_BLUE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
        
        # Input boxes
        name_label = TEXT_FONT.render("Name:", True, BLACK)
        screen.blit(name_label, (SCREEN_WIDTH//2 - 150, 160))
        self.register_name.draw(screen)
        
        email_label = TEXT_FONT.render("Email:", True, BLACK)
        screen.blit(email_label, (SCREEN_WIDTH//2 - 150, 220))
        self.register_email.draw(screen)
        
        password_label = TEXT_FONT.render("Password:", True, BLACK)
        screen.blit(password_label, (SCREEN_WIDTH//2 - 150, 280))
        self.register_password.draw(screen)
        
        # Buttons
        self.register_submit_btn.check_hover(mouse_pos)
        self.register_submit_btn.draw(screen)
        
        self.register_back_btn.check_hover(mouse_pos)
        self.register_back_btn.draw(screen)
    
    def draw_menu_screen(self, mouse_pos):
        # Title
        title = TITLE_FONT.render("Thought Bubble", True, DARK_BLUE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 80))
        
        # Welcome message
        if self.user_data:
            name = self.user_data.get("name", "Player")
            score = self.user_data.get("score", 0)
            welcome_text = f"Welcome back, {name}! Your best score: {score}"
            welcome = HEADER_FONT.render(welcome_text, True, BLACK)
            screen.blit(welcome, (SCREEN_WIDTH//2 - welcome.get_width()//2, 140))
        
        # Buttons
        self.play_btn.check_hover(mouse_pos)
        self.play_btn.draw(screen)
        
        self.journal_btn.check_hover(mouse_pos)
        self.journal_btn.draw(screen)
        
        self.leaderboard_btn.check_hover(mouse_pos)
        self.leaderboard_btn.draw(screen)
        
        self.settings_btn.check_hover(mouse_pos)
        self.settings_btn.draw(screen)
        
        if self.is_admin:
            self.admin_btn.check_hover(mouse_pos)
            self.admin_btn.draw(screen)
        
        self.logout_btn.check_hover(mouse_pos)
        self.logout_btn.draw(screen)
        
        self.quit_btn.check_hover(mouse_pos)
        self.quit_btn.draw(screen)
    
    def draw_game_screen(self, mouse_pos):
        # Top bar
        pygame.draw.rect(screen, WHITE, (20, 20, SCREEN_WIDTH - 40, 60), border_radius=10)
        
        # Score
        score_text = TEXT_FONT.render(f"Score: {self.score}", True, BLUE)
        screen.blit(score_text, (40, 40))
        
        # Difficulty
        difficulty_text = TEXT_FONT.render(f"Difficulty: {self.current_difficulty}", True, GREEN)
        screen.blit(difficulty_text, (SCREEN_WIDTH//2 - difficulty_text.get_width()//2, 40))
        
        # Timer
        timer_text = TEXT_FONT.render(f"Time: {self.time_left if self.time_pressure_mode else '--'}", True, RED)
        screen.blit(timer_text, (SCREEN_WIDTH - 120, 40))
        
        # Scenario
        pygame.draw.rect(screen, WHITE, (50, 100, SCREEN_WIDTH - 100, 100), border_radius=15)
        if hasattr(self, 'current_questions') and self.current_question_index < len(self.current_questions):
            scenario = self.current_questions[self.current_question_index].get("scenario", "No scenario available")
            scenario_lines = self.wrap_text(scenario, TEXT_FONT, SCREEN_WIDTH - 140)
            for i, line in enumerate(scenario_lines):
                scenario_text = TEXT_FONT.render(line, True, BLACK)
                screen.blit(scenario_text, (70, 120 + i * 25))
        
        # Character bubble
        pygame.draw.ellipse(screen, (227, 242, 253), (SCREEN_WIDTH//2 - 70, 220, 140, 140))
        pygame.draw.ellipse(screen, (144, 202, 249), (SCREEN_WIDTH//2 - 70, 220, 140, 140), 2)
        
        # Character face
        emotion = "neutral"
        if self.correct_streak >= 5:
            emotion = "happy"
        elif self.wrong_streak >= 3:
            emotion = "sad"
        self.draw_character_face(SCREEN_WIDTH//2, 290, emotion)
        
        # Thought bubble
        pygame.draw.rect(screen, (255, 249, 196), (50, 370, SCREEN_WIDTH - 100, 120), border_radius=15)
        pygame.draw.rect(screen, (255, 238, 88), (50, 370, SCREEN_WIDTH - 100, 120), 2, border_radius=15)
        
        if hasattr(self, 'current_questions') and self.current_question_index < len(self.current_questions):
            thought = self.current_questions[self.current_question_index].get("statement", "No thought available")
            thought_lines = self.wrap_text(thought, TEXT_FONT, SCREEN_WIDTH - 140)
            for i, line in enumerate(thought_lines):
                thought_text = TEXT_FONT.render(line, True, BLACK)
                screen.blit(thought_text, (70, 390 + i * 25))
        
        # Buttons
        self.accept_btn.check_hover(mouse_pos)
        self.accept_btn.draw(screen)
        
        self.reject_btn.check_hover(mouse_pos)
        self.reject_btn.draw(screen)
        
        self.game_menu_btn.check_hover(mouse_pos)
        self.game_menu_btn.draw(screen)
        
        self.journal_add_btn.check_hover(mouse_pos)
        self.journal_add_btn.draw(screen)
    
    def draw_journal_screen(self, mouse_pos):
        # Title
        title = TITLE_FONT.render("My Journal", True, DARK_BLUE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 40))
        
        # Journal entries list
        pygame.draw.rect(screen, WHITE, (50, 100, SCREEN_WIDTH - 100, 300), border_radius=10)
        pygame.draw.rect(screen, (224, 224, 224), (50, 100, SCREEN_WIDTH - 100, 300), 2, border_radius=10)
        
        for i, entry in enumerate(self.journal_entries):
            entry_rect = pygame.Rect(50, 100 + i * 40, SCREEN_WIDTH - 100, 30)
            color = (227, 242, 253) if i == self.selected_journal_entry else WHITE
            pygame.draw.rect(screen, color, entry_rect)
            pygame.draw.rect(screen, (224, 224, 224), entry_rect, 1)
            
            entry_text = SMALL_FONT.render(entry[:60] + "..." if len(entry) > 60 else entry, True, BLACK)
            screen.blit(entry_text, (60, 105 + i * 40))
        
        # Selected entry content
        pygame.draw.rect(screen, WHITE, (50, 420, SCREEN_WIDTH - 100, 200), border_radius=10)
        pygame.draw.rect(screen, (224, 224, 224), (50, 420, SCREEN_WIDTH - 100, 200), 2, border_radius=10)
        
        if 0 <= self.selected_journal_entry < len(self.journal_entries):
            entry = self.journal_entries[self.selected_journal_entry]
            entry_lines = self.wrap_text(entry, TEXT_FONT, SCREEN_WIDTH - 140)
            for i, line in enumerate(entry_lines):
                entry_text = TEXT_FONT.render(line, True, BLACK)
                screen.blit(entry_text, (60, 430 + i * 25))
        
        # Buttons
        self.journal_back_btn.check_hover(mouse_pos)
        self.journal_back_btn.draw(screen)
        
        self.journal_delete_btn.check_hover(mouse_pos)
        self.journal_delete_btn.draw(screen)
    
    def draw_settings_screen(self, mouse_pos):
        # Title
        title = TITLE_FONT.render("Settings", True, DARK_BLUE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 40))
        
        # Difficulty setting
        pygame.draw.rect(screen, WHITE, (50, 120, SCREEN_WIDTH - 100, 80), border_radius=10)
        difficulty_label = TEXT_FONT.render("Difficulty:", True, BLACK)
        screen.blit(difficulty_label, (70, 140))
        
        self.difficulty_combo.check_hover(mouse_pos)
        self.difficulty_combo.draw(screen)
        
        # Time pressure mode
        pygame.draw.rect(screen, WHITE, (50, 220, SCREEN_WIDTH - 100, 80), border_radius=10)
        time_pressure_label = TEXT_FONT.render("Time Pressure Mode:", True, BLACK)
        screen.blit(time_pressure_label, (70, 240))
        
        self.time_pressure_toggle.check_hover(mouse_pos)
        self.time_pressure_toggle.draw(screen)
        
        # Time limit slider
        pygame.draw.rect(screen, WHITE, (50, 320, SCREEN_WIDTH - 100, 80), border_radius=10)
        time_limit_label = TEXT_FONT.render("Time Limit (seconds):", True, BLACK)
        screen.blit(time_limit_label, (70, 340))
        
        # Slider track
        pygame.draw.rect(screen, (224, 224, 224), (SCREEN_WIDTH//2 - 100, 370, 200, 8), border_radius=4)
        pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH//2 - 100, 370, self.time_limit_slider_pos - (SCREEN_WIDTH//2 - 100), 8), border_radius=4)
        
        # Slider handle
        self.time_limit_slider.check_hover(mouse_pos)
        self.time_limit_slider.draw(screen)
        
        # Time limit value
        time_value_text = TEXT_FONT.render(str(self.time_limit_value), True, GREEN)
        screen.blit(time_value_text, (SCREEN_WIDTH//2 + 110, 360))
        
        # Back button
        self.settings_back_btn.check_hover(mouse_pos)
        self.settings_back_btn.draw(screen)
    
    def draw_leaderboard_screen(self, mouse_pos):
        # Title
        title = TITLE_FONT.render("Leaderboard", True, DARK_BLUE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 40))
        
        # Leaderboard table
        pygame.draw.rect(screen, WHITE, (50, 100, SCREEN_WIDTH - 100, 400), border_radius=10)
        pygame.draw.rect(screen, (224, 224, 224), (50, 100, SCREEN_WIDTH - 100, 400), 2, border_radius=10)
        
        # Table headers
        headers = ["Rank", "Name", "Score", "Games", "Last Played"]
        for i, header in enumerate(headers):
            header_text = TEXT_FONT.render(header, True, WHITE)
            header_rect = pygame.Rect(50 + i * (SCREEN_WIDTH - 100) // len(headers), 100, (SCREEN_WIDTH - 100) // len(headers), 40)
            pygame.draw.rect(screen, BLUE, header_rect, border_top_left_radius=10 if i == 0 else 0, 
                            border_top_right_radius=10 if i == len(headers) - 1 else 0)
            screen.blit(header_text, (header_rect.x + 10, header_rect.y + 10))
        
        # Table rows
        if hasattr(self, 'leaderboard_data'):
            for row_idx, (user_id, user_data) in enumerate(self.leaderboard_data):
                for col_idx in range(len(headers)):
                    cell_rect = pygame.Rect(50 + col_idx * (SCREEN_WIDTH - 100) // len(headers), 
                                          140 + row_idx * 40, 
                                          (SCREEN_WIDTH - 100) // len(headers), 
                                          40)
                    
                    # Color top 3 rows
                    if row_idx == 0:
                        cell_color = (255, 215, 0)  # Gold
                    elif row_idx == 1:
                        cell_color = (192, 192, 192)  # Silver
                    elif row_idx == 2:
                        cell_color = (205, 127, 50)  # Bronze
                    else:
                        cell_color = WHITE
                    
                    pygame.draw.rect(screen, cell_color, cell_rect)
                    pygame.draw.rect(screen, (224, 224, 224), cell_rect, 1)
                    
                    # Cell content
                    if col_idx == 0:  # Rank
                        cell_text = str(row_idx + 1)
                    elif col_idx == 1:  # Name
                        cell_text = user_data.get("name", "Anonymous")
                    elif col_idx == 2:  # Score
                        cell_text = str(user_data.get("score", 0))
                    elif col_idx == 3:  # Games Played
                        cell_text = str(user_data.get("games_played", 0))
                    elif col_idx == 4:  # Last Played
                        last_played = user_data.get("last_played", "")
                        if last_played:
                            try:
                                dt = datetime.fromisoformat(last_played)
                                cell_text = dt.strftime("%Y-%m-%d %H:%M")
                            except:
                                cell_text = last_played
                        else:
                            cell_text = ""
                    
                    text_surf = SMALL_FONT.render(cell_text, True, BLACK)
                    screen.blit(text_surf, (cell_rect.x + 10, cell_rect.y + 10))
        
        # Buttons
        self.leaderboard_back_btn.check_hover(mouse_pos)
        self.leaderboard_back_btn.draw(screen)
        
        self.refresh_leaderboard_btn.check_hover(mouse_pos)
        self.refresh_leaderboard_btn.draw(screen)
    
    def draw_admin_screen(self, mouse_pos):
        # Title
        title = TITLE_FONT.render("Admin Panel", True, DARK_BLUE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 40))
        
        # Questions table
        pygame.draw.rect(screen, WHITE, (50, 100, SCREEN_WIDTH - 100, 400), border_radius=10)
        pygame.draw.rect(screen, (224, 224, 224), (50, 100, SCREEN_WIDTH - 100, 400), 2, border_radius=10)
        
        # Table headers
        headers = ["Scenario", "Statement", "Type", "Category", "Difficulty", "Actions"]
        for i, header in enumerate(headers):
            header_text = TEXT_FONT.render(header, True, WHITE)
            header_rect = pygame.Rect(50 + i * (SCREEN_WIDTH - 100) // len(headers), 100, (SCREEN_WIDTH - 100) // len(headers), 40)
            pygame.draw.rect(screen, PURPLE, header_rect, border_top_left_radius=10 if i == 0 else 0, 
                            border_top_right_radius=10 if i == len(headers) - 1 else 0)
            screen.blit(header_text, (header_rect.x + 10, header_rect.y + 10))
        
        # Table rows
        if hasattr(self, 'admin_questions'):
            for row_idx, (qid, question) in enumerate(self.admin_questions):
                for col_idx in range(len(headers)):
                    cell_rect = pygame.Rect(50 + col_idx * (SCREEN_WIDTH - 100) // len(headers), 
                                          140 + row_idx * 40, 
                                          (SCREEN_WIDTH - 100) // len(headers), 
                                          40)
                    
                    pygame.draw.rect(screen, WHITE, cell_rect)
                    pygame.draw.rect(screen, (224, 224, 224), cell_rect, 1)
                    
                    # Cell content
                    if col_idx < 5:  # Data columns
                        if col_idx == 0:  # Scenario
                            cell_text = question.get("scenario", "")[:20] + "..."
                        elif col_idx == 1:  # Statement
                            cell_text = question.get("statement", "")[:20] + "..."
                        elif col_idx == 2:  # Type
                            cell_text = question.get("type", "")
                        elif col_idx == 3:  # Category
                            cell_text = question.get("category", "")
                        elif col_idx == 4:  # Difficulty
                            cell_text = question.get("difficulty", "Easy")
                        
                        text_surf = SMALL_FONT.render(cell_text, True, BLACK)
                        screen.blit(text_surf, (cell_rect.x + 10, cell_rect.y + 10))
                    else:  # Actions column
                        # Edit button
                        edit_btn = Button(cell_rect.x + 10, cell_rect.y + 5, 60, 30, "Edit", BLUE, (25, 118, 210), rounded=True)
                        edit_btn.check_hover(mouse_pos)
                        edit_btn.draw(screen)
                        
                        # Delete button
                        delete_btn = Button(cell_rect.x + 80, cell_rect.y + 5, 60, 30, "Delete", RED, (211, 47, 47), rounded=True)
                        delete_btn.check_hover(mouse_pos)
                        delete_btn.draw(screen)
                        
                        # Handle button clicks
                        if edit_btn.is_clicked(mouse_pos, pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': mouse_pos})):
                            self.edit_question(qid)
                        
                        if delete_btn.is_clicked(mouse_pos, pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': mouse_pos})):
                            self.delete_question(qid)
        
        # Buttons
        self.admin_back_btn.check_hover(mouse_pos)
        self.admin_back_btn.draw(screen)
        
        self.add_question_btn.check_hover(mouse_pos)
        self.add_question_btn.draw(screen)
        
        self.refresh_questions_btn.check_hover(mouse_pos)
        self.refresh_questions_btn.draw(screen)
    
    # Helper methods
    def draw_character_face(self, x, y, emotion="neutral"):
        # Face
        pygame.draw.circle(screen, PEACH, (x, y), 50)
        
        # Eyes
        pygame.draw.circle(screen, BLACK, (x - 20, y - 15), 8)
        pygame.draw.circle(screen, BLACK, (x + 20, y - 15), 8)
        
        # Mouth
        if emotion == "happy":
            pygame.draw.arc(screen, BLACK, (x - 25, y - 10, 50, 30), 0, 3.14, 2)
        elif emotion == "sad":
            pygame.draw.arc(screen, BLACK, (x - 25, y + 10, 50, 30), 3.14, 6.28, 2)
        else:  # neutral
            pygame.draw.line(screen, BLACK, (x - 20, y + 20), (x + 20, y + 20), 2)
    
    def wrap_text(self, text, font, max_width):
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_width = font.size(test_line)[0]
            
            if test_width <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def show_message(self, title, message):
        # Simple message box implementation
        message_box = pygame.Surface((600, 200))
        message_box.fill(WHITE)
        pygame.draw.rect(message_box, BLACK, (0, 0, 600, 200), 2)
        
        title_text = HEADER_FONT.render(title, True, BLACK)
        message_box.blit(title_text, (300 - title_text.get_width()//2, 30))
        
        message_lines = self.wrap_text(message, TEXT_FONT, 560)
        for i, line in enumerate(message_lines):
            line_text = TEXT_FONT.render(line, True, BLACK)
            message_box.blit(line_text, (20, 80 + i * 30))
        
        ok_btn = Button(250, 150, 100, 40, "OK", GREEN, (56, 142, 60), rounded=True)
        
        # Show message box
        waiting = True
        while waiting:
            mouse_pos = pygame.mouse.get_pos()
            rel_pos = (mouse_pos[0] - (SCREEN_WIDTH - 600)//2, mouse_pos[1] - (SCREEN_HEIGHT - 200)//2)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.running = False
                
                ok_btn.check_hover(rel_pos)
                if ok_btn.is_clicked(rel_pos, event):
                    waiting = False
            
            screen.blit(message_box, ((SCREEN_WIDTH - 600)//2, (SCREEN_HEIGHT - 200)//2))
            ok_btn.draw(message_box)
            pygame.display.flip()
            self.clock.tick(60)
    
    # Game logic methods
    def login(self):
        email = self.login_email.text.strip()
        password = self.login_password.text.strip()

        if not email or not password:
            self.show_message("Error", "Please enter both email and password")
            return

        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            response = requests.post(url, json=payload)
            data = response.json()

            if "error" in data:
                error_msg = data["error"]["message"]
                if "INVALID_EMAIL" in error_msg:
                    raise Exception("Invalid email address")
                elif "INVALID_PASSWORD" in error_msg:
                    raise Exception("Incorrect password")
                elif "TOO_MANY_ATTEMPTS" in error_msg:
                    raise Exception("Too many attempts. Try again later.")
                else:
                    raise Exception(error_msg)

            self.user = {
                'localId': data["localId"],
                'idToken': data["idToken"]
            }
            
            # Load user data
            self.user_logged_in(data["localId"], data["idToken"])
            
        except Exception as e:
            self.show_message("Login Failed", str(e))
    
    def register(self):
        email = self.register_email.text.strip()
        password = self.register_password.text.strip()
        name = self.register_name.text.strip()

        if not email or not password or not name:
            self.show_message("Error", "Please fill all fields")
            return

        if len(password) < 6:
            self.show_message("Error", "Password must be at least 6 characters")
            return

        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            response = requests.post(url, json=payload)
            data = response.json()

            if "error" in data:
                error_msg = data["error"]["message"]
                if "EMAIL_EXISTS" in error_msg:
                    raise Exception("Email already registered")
                elif "WEAK_PASSWORD" in error_msg:
                    raise Exception("Password should be at least 6 characters")
                else:
                    raise Exception(error_msg)

            local_id = data["localId"]
            id_token = data["idToken"]

            user_data = {
                "name": name,
                "email": email,
                "score": 0,
                "games_played": 0,
                "last_played": "",
                "is_admin": False
            }
            
            db_url = f"{FIREBASE_DB_URL}/users/{local_id}.json?auth={id_token}"
            db_response = requests.put(db_url, json=user_data)

            if db_response.status_code != 200:
                raise Exception("Failed to write user data to database")

            self.show_message("Success", "Registration successful! Please login.")
            
            self.register_email.text = ""
            self.register_password.text = ""
            self.register_name.text = ""
            self.current_screen = "login"
            
        except Exception as e:
            self.show_message("Registration Failed", str(e))
    
    def user_logged_in(self, local_id, id_token):
        self.user = {
            'localId': local_id,
            'idToken': id_token
        }
        
        try:
            user_data = self.db.child("users").child(local_id).get(token=id_token).val()
            if user_data:
                self.user_data = user_data
                self.is_admin = user_data.get("is_admin", False)
                
                # Update last played time
                self.db.child("users").child(local_id).update({
                    "last_played": datetime.now().isoformat()
                }, token=id_token)
                
                # Load journal
                self.load_journal(id_token)
                
                # Switch to menu screen
                self.current_screen = "menu"
        except Exception as e:
            self.show_message("Error", f"Failed to load user data: {str(e)}")
    
    def logout(self):
        self.user = None
        self.user_data = None
        self.is_admin = False
        self.current_screen = "login"
    
    def start_game(self):
        if not self.user:
            self.show_message("Error", "Please login to play")
            return
        
        self.score = 0
        self.correct_streak = 0
        self.wrong_streak = 0
        
        # Filter questions by current difficulty
        self.current_questions = [
            q for q in self.questions 
            if q.get("difficulty", "Easy") == self.current_difficulty
        ]
        
        if not self.current_questions:
            self.show_message("Error", f"No questions found for {self.current_difficulty} difficulty")
            return
        
        self.current_question_index = 0
        
        # Initialize timer
        if self.time_pressure_mode:
            self.time_left = self.time_limit_value
        else:
            self.time_left = 0
        
        self.current_screen = "game"
    
    def evaluate_thought(self, action):
        if not hasattr(self, 'current_questions') or self.current_question_index >= len(self.current_questions):
            return
            
        question = self.current_questions[self.current_question_index]
        correct = False
        
        if (action == "accept" and question["type"] == "positive") or \
           (action == "reject" and question["type"] == "negative"):
            # Correct classification
            self.score += 10
            self.correct_streak += 1
            self.wrong_streak = 0
            correct = True
            feedback = "✅ Correct! "
            
            if question["type"] == "positive":
                feedback += "This is a healthy, realistic thought."
            else:
                feedback += "This is indeed an unrealistic negative thought."
        else:
            # Incorrect classification
            self.score = max(0, self.score - 5)
            self.wrong_streak += 1
            self.correct_streak = 0
            feedback = "❌ Not quite. "
            
            if question["type"] == "positive":
                feedback += f"This was actually a positive thought.\n\n{question['statement']} is a healthy way to look at this situation."
            else:
                feedback += f"This was a negative thought.\n\nCategory: {question['category']}\n\nExplanation: {question['explanation']}\n\nAlternative thought: {question['alternative']}"
        
        # Show feedback
        self.show_message("Feedback", feedback)
        
        # Update game state
        self.update_user_score()
        self.current_question_index += 1
        
        # Load next scenario or loop back
        if self.current_question_index >= len(self.current_questions):
            self.current_question_index = 0
        
        # Reset timer in time pressure mode
        if self.time_pressure_mode:
            self.time_left = self.time_limit_value
    
    def update_timer(self):
        if self.time_left > 0:
            self.time_left -= 1
            
            # Change color when time is running low
            if self.time_left <= 10:
                pass  # Color change handled in draw method
        else:
            # Time's up
            self.show_message("Time's Up!", "You ran out of time! Moving to next thought.")
            
            self.score = max(0, self.score - 5)
            self.wrong_streak += 1
            self.correct_streak = 0
            self.update_user_score()
            
            # Move to next question
            self.current_question_index += 1
            if self.current_question_index >= len(self.current_questions):
                self.current_question_index = 0
            
            # Reset timer
            if self.time_pressure_mode:
                self.time_left = self.time_limit_value
    
    def update_user_score(self):
        if self.user:
            try:
                # Get current games_played value
                current_games_played = self.db.child("users").child(self.user['localId']).child("games_played").get().val()
                if current_games_played is None:
                    current_games_played = 0

                # Update values
                self.db.child("users").child(self.user['localId']).update({
                    "score": self.score,
                    "games_played": current_games_played + 1,
                    "last_played": datetime.now().isoformat()
                })
            except Exception as e:
                print(f"Failed to update user score: {str(e)}")
    
    def add_current_to_journal(self):
        if hasattr(self, 'current_questions') and self.current_question_index < len(self.current_questions):
            question = self.current_questions[self.current_question_index]
            if question["type"] == "positive":
                self.journal_entries.append(question["statement"])
                self.save_journal()
                self.show_message("Journal", "Thought added to your journal!")
            else:
                self.show_message("Journal", "Only realistic positive thoughts can be added to the journal.")
    
    def save_journal(self):
        if self.user:
            try:
                self.db.child("users").child(self.user['localId']).child("journal").set(self.journal_entries)
            except Exception as e:
                print(f"Failed to save journal: {str(e)}")
    
    def load_journal(self, id_token=None):
        if self.user:
            try:
                journal_data = self.db.child("users").child(self.user['localId']).child("journal").get(token=id_token).val()
                if journal_data:
                    self.journal_entries = list(journal_data.values())
                else:
                    self.journal_entries = []
            except Exception as e:
                print(f"Failed to load journal: {str(e)}")
                self.journal_entries = []
    
    def delete_journal_entry(self):
        if 0 <= self.selected_journal_entry < len(self.journal_entries):
            confirm = self.show_confirmation("Confirm Delete", "Are you sure you want to delete this entry?")
            if confirm:
                self.journal_entries.pop(self.selected_journal_entry)
                self.save_journal()
                self.selected_journal_entry = -1
    
    def show_confirmation(self, title, message):
        # Simple confirmation dialog
        confirm_box = pygame.Surface((600, 200))
        confirm_box.fill(WHITE)
        pygame.draw.rect(confirm_box, BLACK, (0, 0, 600, 200), 2)
        
        title_text = HEADER_FONT.render(title, True, BLACK)
        confirm_box.blit(title_text, (300 - title_text.get_width()//2, 30))
        
        message_lines = self.wrap_text(message, TEXT_FONT, 560)
        for i, line in enumerate(message_lines):
            line_text = TEXT_FONT.render(line, True, BLACK)
            confirm_box.blit(line_text, (20, 80 + i * 30))
        
        yes_btn = Button(150, 150, 100, 40, "Yes", GREEN, (56, 142, 60), rounded=True)
        no_btn = Button(350, 150, 100, 40, "No", RED, (211, 47, 47), rounded=True)
        
        # Show confirmation box
        waiting = True
        result = False
        while waiting:
            mouse_pos = pygame.mouse.get_pos()
            rel_pos = (mouse_pos[0] - (SCREEN_WIDTH - 600)//2, mouse_pos[1] - (SCREEN_HEIGHT - 200)//2)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.running = False
                
                yes_btn.check_hover(rel_pos)
                no_btn.check_hover(rel_pos)
                
                if yes_btn.is_clicked(rel_pos, event):
                    waiting = False
                    result = True
                elif no_btn.is_clicked(rel_pos, event):
                    waiting = False
                    result = False
            
            screen.blit(confirm_box, ((SCREEN_WIDTH - 600)//2, (SCREEN_HEIGHT - 200)//2))
            yes_btn.draw(confirm_box)
            no_btn.draw(confirm_box)
            pygame.display.flip()
            self.clock.tick(60)
        
        return result
    
    def update_leaderboard(self):
        try:
            # Fetch top 10 users ordered by score
            users_snapshot = self.db.child("users").order_by_child("score").limit_to_last(10).get()
            users = users_snapshot.val()

            if not users:
                self.leaderboard_data = []
                return
            
            # Sort users descending by score (limit_to_last may return ascending)
            self.leaderboard_data = sorted(users.items(), key=lambda x: x[1].get("score", 0), reverse=True)
            
        except Exception as e:
            self.show_message("Error", f"Failed to load leaderboard: {str(e)}")
    
    def load_questions_from_firebase(self):
        try:
            ref = db.reference('questions')
            data = ref.get()

            self.questions = []

            if data:
                for key, question in data.items():
                    self.questions.append({
                        "key": key,
                        "scenario": question.get("scenario", ""),
                        "statement": question.get("statement", ""),
                        "alternative": question.get("alternative", ""),
                        "category": question.get("category", ""),
                        "explanation": question.get("explanation", ""),
                        "type": question.get("type", ""),
                        "difficulty": question.get("difficulty", "Easy")
                    })

        except Exception as e:
            print(f"Error loading questions: {str(e)}")
    
    def load_questions(self):
        try:
            questions = self.db.child("questions").get().val() or {}
            self.admin_questions = list(questions.items())
        except Exception as e:
            self.show_message("Error", f"Failed to load questions: {str(e)}")
    
    def add_question(self):
        # In a real implementation, you'd create a form to add a new question
        self.show_message("Info", "In a full implementation, this would open a form to add a new question.")
    
    def edit_question(self, qid):
        # In a real implementation, you'd create a form to edit the question
        self.show_message("Info", f"In a full implementation, this would open a form to edit question {qid}.")
    
    def delete_question(self, qid):
        confirm = self.show_confirmation("Confirm Delete", "Are you sure you want to delete this question?")
        if confirm:
            try:
                self.db.child("questions").child(qid).remove()
                self.load_questions()
                self.load_questions_from_firebase()  # Refresh game questions
            except Exception as e:
                self.show_message("Error", f"Failed to delete question: {str(e)}")

if __name__ == "__main__":
    game = ThoughtGame()
    game.run()