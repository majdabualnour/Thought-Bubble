import sys
import json
import os
import random
import requests
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QMessageBox, QTextEdit,
    QListWidget, QComboBox, QSlider, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QFormLayout, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush, QFont
import firebase_admin
from firebase_admin import credentials, db, auth
import pyrebase
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl

# Firebase Configuration
FIREBASE_API_KEY = "AIzaSyBslVrw8gUYRkjpGHKWeftbvDp0-oBa9w0"
FIREBASE_DB_URL = "https://csgame-f1969-default-rtdb.firebaseio.com"

class StyledMessageBox(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QMessageBox {
                background-color: #f5f5f5;
                font-family: 'Segoe UI';
            }
            QMessageBox QLabel {
                color: #333;
                font-size: 14px;
            }
            QMessageBox QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QMessageBox QPushButton:hover {
                background-color: #45a049;
            }
        """)

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login / Register")
        self.setModal(True)
        self.setFixedSize(450, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                font-family: 'Segoe UI';
            }
            QLabel {
                color: #333;
                font-size: 14px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QTabWidget::pane {
                border: none;
            }
            QTabBar::tab {
                padding: 8px 16px;
                background: #e0e0e0;
                border: 1px solid #ddd;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #f5f5f5;
                border-bottom: 2px solid #4CAF50;
            }
        """)
        self.sign = QSoundEffect()
        self.sign.setSource(QUrl.fromLocalFile("sign.wav"))
        self.sign.setVolume(0.5)  # Volume: 0.0 (mute) to 1.0 (max)


        self.FIREBASE_API_KEY = FIREBASE_API_KEY
        self.FIREBASE_DB_URL = FIREBASE_DB_URL
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Add a title label
        title = QLabel("Thought Bubble")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin-bottom: 20px;
        """)
        layout.addWidget(title)
        
        self.tabs = QTabWidget()
        self.login_tab = QWidget()
        self.register_tab = QWidget()
        
        # Login Tab
        login_layout = QFormLayout()
        login_layout.setSpacing(15)
        login_layout.setContentsMargins(20, 20, 20, 20)
        
        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("Email")
        
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Password")
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        
        login_btn = QPushButton("Login")
        login_btn.setStyleSheet("""
            background-color: #2196F3;
            font-weight: bold;
        """)
        login_btn.clicked.connect(self.login)
        
        login_layout.addRow("Email:", self.login_email)
        login_layout.addRow("Password:", self.login_password)
        login_layout.addRow(login_btn)
        self.login_tab.setLayout(login_layout)
        
        # Register Tab
        register_layout = QFormLayout()
        register_layout.setSpacing(15)
        register_layout.setContentsMargins(20, 20, 20, 20)
        
        self.register_email = QLineEdit()
        self.register_email.setPlaceholderText("Email")
        
        self.register_password = QLineEdit()
        self.register_password.setPlaceholderText("Password (min 6 chars)")
        self.register_password.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.register_name = QLineEdit()
        self.register_name.setPlaceholderText("Full Name")
        
        register_btn = QPushButton("Register")
        register_btn.setStyleSheet("""
            background-color: #FF9800;
            font-weight: bold;
        """)
        register_btn.clicked.connect(self.register)
        
        register_layout.addRow("Name:", self.register_name)
        register_layout.addRow("Email:", self.register_email)
        register_layout.addRow("Password:", self.register_password)
        register_layout.addRow(register_btn)
        self.register_tab.setLayout(register_layout)
        
        self.tabs.addTab(self.login_tab, "Login")
        self.tabs.addTab(self.register_tab, "Register")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
        # User credentials
        self.id_token = None
        self.local_id = None
    
    def login(self):
        email = self.login_email.text().strip()
        password = self.login_password.text().strip()

        if not email or not password:
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Error")
            msg.setText("Please enter both email and password")
            msg.exec()
            return

        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.FIREBASE_API_KEY}"
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

            self.id_token = data["idToken"]
            self.local_id = data["localId"]
            
            if self.parent():
                try:
                    self.parent().user_logged_in(self.local_id, self.id_token)
                    self.sign.play()
                except AttributeError:
                    print("Login successful, but parent window doesn't handle logins")
            else:
                print("Login successful, but no parent window to notify")
            
            self.accept()
            
        except Exception as e:
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Login Failed")
            msg.setText(str(e))
            msg.exec()
    
    def register(self):
        email = self.register_email.text().strip()
        password = self.register_password.text().strip()
        name = self.register_name.text().strip()

        if not email or not password or not name:
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Error")
            msg.setText("Please fill all fields")
            msg.exec()
            return

        if len(password) < 6:
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Error")
            msg.setText("Password must be at least 6 characters")
            msg.exec()
            return

        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={self.FIREBASE_API_KEY}"
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
            db_url = f"{self.FIREBASE_DB_URL}/users/{local_id}.json?auth={id_token}"
            db_response = requests.put(db_url, json=user_data)

            if db_response.status_code != 200:
                raise Exception("Failed to write user data to database")

            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Success")
            msg.setText("Registration successful! Please login.")
            self.sign.play()
            msg.exec()
            
            self.register_email.clear()
            self.register_password.clear()
            self.register_name.clear()
            self.tabs.setCurrentIndex(0)
            
        except Exception as e:
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Registration Failed")
            msg.setText(str(e))
            msg.exec()

class AdminQuestionDialog(QDialog):
    def __init__(self, parent=None, question_data=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Question")
        self.setModal(True)
        self.setFixedSize(600, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                font-family: 'Segoe UI';
            }
            QLabel {
                color: #333;
                font-size: 14px;
            }
            QLineEdit, QTextEdit, QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        layout = QFormLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        self.statement = QTextEdit()
        self.statement.setPlaceholderText("Thought statement (e.g., \"I'm a failure if I don't get perfect grades\")")
        self.statement.setMinimumHeight(80)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["negative", "positive"])
        
        self.explanation = QTextEdit()
        self.explanation.setPlaceholderText("Explanation for why this is negative/positive")
        self.explanation.setMinimumHeight(80)
        
        self.category = QLineEdit()
        self.category.setPlaceholderText("Cognitive distortion category (e.g., Black-and-White Thinking)")
        
        self.alternative = QTextEdit()
        self.alternative.setPlaceholderText("Alternative positive thought")
        self.alternative.setMinimumHeight(80)
        
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Question")
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #f44336;")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        if question_data:
            self.statement.setText(question_data.get("statement", ""))
            self.type_combo.setCurrentText(question_data.get("type", "negative"))
            self.explanation.setText(question_data.get("explanation", ""))
            self.category.setText(question_data.get("category", ""))
            self.alternative.setText(question_data.get("alternative", ""))
        
        layout.addRow("Statement:", self.statement)
        layout.addRow("Type:", self.type_combo)
        layout.addRow("Explanation:", self.explanation)
        layout.addRow("Category:", self.category)
        layout.addRow("Alternative Thought:", self.alternative)
        layout.addRow(button_layout)
        
        self.setLayout(layout)
    
    def get_question_data(self):
        return {
            "statement": self.statement.toPlainText(),
            "type": self.type_combo.currentText(),
            "explanation": self.explanation.toPlainText(),
            "category": self.category.text(),
            "alternative": self.alternative.toPlainText(),
            "created_at": datetime.now().isoformat()
        }

class ThoughtGame(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Setup sound effect once
        self.click_sound = QSoundEffect()
        self.click_sound.setSource(QUrl.fromLocalFile("click.wav"))
        self.click_sound.setVolume(0.5)  # Volume: 0.0 (mute) to 1.0 (max)

        # Initialize Firebase
        self.initialize_firebase()
        self.journal_entries = []
        self.setWindowTitle("Thought Bubble - Mental Well-being Game")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
                font-family: 'Segoe UI';
            }
        """)
        
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
        self.current_thought_index = 0
        self.questions = []
        self.current_question_index = 0
        
        # Create main stacked widget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create pages
        self.create_login_page()
        self.create_main_menu()
        self.create_game_page()
        self.create_journal_page()
        self.create_settings_page()
        self.create_leaderboard_page()
        self.create_admin_page()
        
        # Start with login page
        self.stacked_widget.setCurrentIndex(0)
    def play_click_sound(self):
        # Play the click sound
        self.click_sound.play()
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
            QMessageBox.critical(self, "Firebase Error", 
                                "Firebase credentials file not found.")
        except Exception as e:
            QMessageBox.critical(self, "Firebase Error", 
                                f"Failed to initialize Firebase: {str(e)}")

    def create_login_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Add a background image or color
        page.setStyleSheet("""
            background-color: #e3f2fd;
        """)
        
        # Add a logo or title
        title = QLabel("Thought Bubble")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #0d47a1;
            margin-top: 50px;
            margin-bottom: 30px;
        """)
        
        # Add a subtitle
        subtitle = QLabel("Improve your mental well-being")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 18px;
            color: #1976d2;
            margin-bottom: 50px;
        """)
        
        login_btn = QPushButton("Login / Register")
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 15px;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        login_btn.clicked.connect(self.show_login_dialog)
        
        # Center the button
        btn_container = QWidget()
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(login_btn)
        btn_layout.addStretch()
        btn_container.setLayout(btn_layout)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()
        layout.addWidget(btn_container)
        layout.addStretch()
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)
    

    def show_login_dialog(self):
        self.play_click_sound()
        dialog = LoginDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.user = {
                'localId': dialog.local_id,
                'idToken': dialog.id_token
            }
            self.user_logged_in(dialog.local_id, dialog.id_token)
    
    def create_main_menu(self):
        page = QWidget()
        page.setStyleSheet("background-color: #f5f5f5;")
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Thought Bubble")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #0d47a1;
            margin-bottom: 10px;
        """)
        
        # Welcome message
        self.welcome_label = QLabel()
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_label.setStyleSheet("""
            font-size: 18px;
            color: #333;
            margin-bottom: 30px;
        """)
        
        # Button styles
        btn_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 15px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """
        
        play_btn = QPushButton("Play Game")
        play_btn.setStyleSheet(btn_style)
        play_btn.clicked.connect(self.start_game)
        
        journal_btn = QPushButton("My Journal")
        journal_btn.setStyleSheet(btn_style.replace("#2196F3", "#4CAF50"))
        journal_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        
        leaderboard_btn = QPushButton("Leaderboard")
        leaderboard_btn.setStyleSheet(btn_style.replace("#2196F3", "#FF9800"))
        leaderboard_btn.clicked.connect(lambda: self.show_leaderboard())
        
        settings_btn = QPushButton("Settings")
        settings_btn.setStyleSheet(btn_style.replace("#2196F3", "#9E9E9E"))
        settings_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(4))
        
        if self.is_admin:
            admin_btn = QPushButton("Admin Panel")
            admin_btn.setStyleSheet(btn_style.replace("#2196F3", "#673AB7"))
            admin_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(6))
            layout.addWidget(admin_btn)
        
        # Button container
        btn_container = QWidget()
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addWidget(play_btn)
        btn_layout.addWidget(journal_btn)
        btn_layout.addWidget(leaderboard_btn)
        btn_layout.addWidget(settings_btn)
        btn_container.setLayout(btn_layout)
        
        # Bottom buttons
        bottom_btn_layout = QHBoxLayout()
        
        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        logout_btn.clicked.connect(self.logout)
        
        quit_btn = QPushButton("Quit")
        quit_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #455A64;
            }
        """)
        quit_btn.clicked.connect(self.close)
        
        bottom_btn_layout.addStretch()
        bottom_btn_layout.addWidget(logout_btn)
        bottom_btn_layout.addWidget(quit_btn)
        
        layout.addWidget(title)
        layout.addWidget(self.welcome_label)
        layout.addStretch()
        layout.addWidget(btn_container)
        layout.addStretch()
        layout.addLayout(bottom_btn_layout)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)

    def create_game_page(self):
        self.game_page = QWidget()
        self.game_page.setStyleSheet("""
            background-color: #f5f5f5;
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Top bar with score, difficulty and timer
        top_bar = QWidget()
        top_bar.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
            padding: 10px;
        """)
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(10, 5, 10, 5)
        
        self.score_label = QLabel(f"Score: {self.score}")
        self.score_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2196F3;
        """)
        
        self.difficulty_label = QLabel(f"Difficulty: {self.current_difficulty}")
        self.difficulty_label.setStyleSheet("""
            font-size: 16px;
            color: #4CAF50;
        """)
        
        self.timer_label = QLabel("Time: --")
        self.timer_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #F44336;
        """)
        
        top_bar_layout.addWidget(self.score_label)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.difficulty_label)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.timer_label)
        top_bar.setLayout(top_bar_layout)
        
        # Scenario display
        self.scenario_label = QLabel()
        self.scenario_label.setWordWrap(True)
        self.scenario_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scenario_label.setStyleSheet("""
            font-size: 20px;
            padding: 20px;
            background-color: white;
            border-radius: 15px;
            border: 1px solid #E0E0E0;
            min-height: 100px;
        """)
        
        # Character bubble
        bubble = QWidget()
        bubble.setStyleSheet("""
            background-color: #E3F2FD;
            border-radius: 100px;
            border: 2px solid #90CAF9;
        """)
        bubble_layout = QVBoxLayout()
        bubble_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.character_label = QLabel()
        self.character_label.setPixmap(self.get_character_emotion("neutral"))
        self.character_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.character_label.setFixedSize(120, 120)
        
        bubble_layout.addWidget(self.character_label)
        bubble.setLayout(bubble_layout)
        
        # Thought display
        self.thought_label = QLabel()
        self.thought_label.setWordWrap(True)
        self.thought_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thought_label.setStyleSheet("""
            font-size: 22px;
            font-style: italic;
            padding: 20px;
            background-color: #FFF9C4;
            border-radius: 15px;
            border: 1px solid #FFEE58;
            min-height: 120px;
        """)
        
        # Accept/Reject Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(30)
        
        accept_btn = QPushButton("✔ Accept Thought")
        accept_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 12px 24px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        accept_btn.clicked.connect(lambda: self.evaluate_thought("accept"))
        
        reject_btn = QPushButton("✘ Reject Thought")
        reject_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 12px 24px;
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        reject_btn.clicked.connect(lambda: self.evaluate_thought("reject"))
        
        button_layout.addStretch()
        button_layout.addWidget(accept_btn)
        button_layout.addWidget(reject_btn)
        button_layout.addStretch()
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        
        menu_btn = QPushButton("← Main Menu")
        menu_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 10px 20px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        menu_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        journal_btn = QPushButton("📝 Add to Journal")
        journal_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 10px 20px;
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        journal_btn.clicked.connect(self.add_current_to_journal)
        
        nav_layout.addWidget(menu_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(journal_btn)
        
        # Add to main layout
        layout.addWidget(top_bar)
        layout.addWidget(self.scenario_label)
        layout.addWidget(bubble, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.thought_label)
        layout.addLayout(button_layout)
        layout.addLayout(nav_layout)
        
        self.game_page.setLayout(layout)
        self.stacked_widget.addWidget(self.game_page)
        
        # Timer setup
        self.game_timer = QTimer(self)
        self.game_timer.timeout.connect(self.update_timer)
        
        # Load initial questions
        self.load_questions_from_firebase()

    def create_journal_page(self):
        page = QWidget()
        page.setStyleSheet("background-color: #f5f5f5;")
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("My Journal")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #0d47a1;
            margin-bottom: 20px;
        """)
        
        # Journal list with scroll area
        self.journal_list = QListWidget()
        self.journal_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #E0E0E0;
            }
            QListWidget::item:hover {
                background-color: #E3F2FD;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
        """)
        self.journal_list.itemDoubleClicked.connect(self.view_journal_entry)
        
        # Journal entry view
        self.journal_text = QTextEdit()
        self.journal_text.setReadOnly(True)
        self.journal_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 10px;
                padding: 15px;
                font-size: 14px;
            }
        """)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        back_btn = QPushButton("Back to Menu")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        delete_btn = QPushButton("Delete Entry")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        delete_btn.clicked.connect(self.delete_journal_entry)
        
        button_layout.addWidget(back_btn)
        button_layout.addStretch()
        button_layout.addWidget(delete_btn)
        
        layout.addWidget(title)
        layout.addWidget(self.journal_list, 1)
        layout.addWidget(self.journal_text, 1)
        layout.addLayout(button_layout)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)
        
        self.update_journal_list()
    
    def create_settings_page(self):
        page = QWidget()
        page.setStyleSheet("background-color: #f5f5f5;")
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("Settings")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #0d47a1;
            margin-bottom: 20px;
        """)
        
        # Difficulty selection
        difficulty_group = QWidget()
        difficulty_group.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
            padding: 15px;
        """)
        difficulty_layout = QHBoxLayout()
        difficulty_layout.setContentsMargins(0, 0, 0, 0)
        
        difficulty_label = QLabel("Difficulty:")
        difficulty_label.setStyleSheet("font-size: 16px;")
        
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Easy", "Medium", "Hard"])
        self.difficulty_combo.setCurrentText(self.current_difficulty)
        self.difficulty_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                min-width: 150px;
            }
        """)
        self.difficulty_combo.currentTextChanged.connect(self.change_difficulty)
        
        difficulty_layout.addWidget(difficulty_label)
        difficulty_layout.addStretch()
        difficulty_layout.addWidget(self.difficulty_combo)
        difficulty_group.setLayout(difficulty_layout)
        
        # Time pressure mode
        time_pressure_group = QWidget()
        time_pressure_group.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
            padding: 15px;
        """)
        time_pressure_layout = QHBoxLayout()
        time_pressure_layout.setContentsMargins(0, 0, 0, 0)
        
        time_pressure_label = QLabel("Time Pressure Mode:")
        time_pressure_label.setStyleSheet("font-size: 16px;")
        
        self.time_pressure_toggle = QSlider(Qt.Orientation.Horizontal)
        self.time_pressure_toggle.setMinimum(0)
        self.time_pressure_toggle.setMaximum(1)
        self.time_pressure_toggle.setValue(1 if self.time_pressure_mode else 0)
        self.time_pressure_toggle.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #E0E0E0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 20px;
                height: 20px;
                background: #2196F3;
                border-radius: 10px;
            }
            QSlider::sub-page:horizontal {
                background: #2196F3;
                border-radius: 4px;
            }
        """)
        self.time_pressure_toggle.valueChanged.connect(self.toggle_time_pressure)
        
        self.time_pressure_status = QLabel("On" if self.time_pressure_mode else "Off")
        self.time_pressure_status.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2196F3;
        """)
        
        time_pressure_layout.addWidget(time_pressure_label)
        time_pressure_layout.addStretch()
        time_pressure_layout.addWidget(self.time_pressure_toggle)
        time_pressure_layout.addWidget(self.time_pressure_status)
        time_pressure_group.setLayout(time_pressure_layout)
        
        # Time limit slider
        time_limit_group = QWidget()
        time_limit_group.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
            padding: 15px;
        """)
        time_limit_layout = QHBoxLayout()
        time_limit_layout.setContentsMargins(0, 0, 0, 0)
        
        time_limit_label = QLabel("Time Limit (seconds):")
        time_limit_label.setStyleSheet("font-size: 16px;")
        
        self.time_limit_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_limit_slider.setMinimum(10)
        self.time_limit_slider.setMaximum(60)
        self.time_limit_slider.setValue(self.time_left)
        self.time_limit_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #E0E0E0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 20px;
                height: 20px;
                background: #4CAF50;
                border-radius: 10px;
            }
            QSlider::sub-page:horizontal {
                background: #4CAF50;
                border-radius: 4px;
            }
        """)
        self.time_limit_slider.valueChanged.connect(self.change_time_limit)
        
        self.time_limit_value = QLabel(str(self.time_left))
        self.time_limit_value.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #4CAF50;
        """)
        
        time_limit_layout.addWidget(time_limit_label)
        time_limit_layout.addStretch()
        time_limit_layout.addWidget(self.time_limit_slider)
        time_limit_layout.addWidget(self.time_limit_value)
        time_limit_group.setLayout(time_limit_layout)
        
        # Back button
        back_btn = QPushButton("Back to Menu")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        layout.addWidget(title)
        layout.addWidget(difficulty_group)
        layout.addWidget(time_pressure_group)
        layout.addWidget(time_limit_group)
        layout.addStretch()
        layout.addWidget(back_btn)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)
   
    def update_welcome_message(self):
        if hasattr(self, 'welcome_label') and self.user_data:
            name = self.user_data.get("name", "Player")
            score = self.user_data.get("score", 0)
            self.welcome_label.setText(f"Welcome back, {name}!\nYour best score: {score}")

    def load_next_scenario(self):
        if not self.questions:
            self.scenario_label.setText("No questions available.")
            self.thought_label.setText("")
            return

        question = self.questions[self.current_question_index]

        # Show the scenario and thought
        self.scenario_label.setText(question.get("scenario", "No scenario available"))
        self.thought_label.setText(question.get("statement", "No thought available"))

        # Increment index for next call (loop back)
        self.current_question_index += 1
        if self.current_question_index >= len(self.questions):
            self.current_question_index = 0

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

            if self.questions:
                self.current_question_index = 0
                self.load_next_scenario()
            else:
                self.scenario_label.setText("No questions available.")
                self.thought_label.setText("")

        except Exception as e:
            print(f"Error loading questions: {str(e)}")
            self.scenario_label.setText("Error loading questions")
            self.thought_label.setText("Please try again later")

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
                
                self.update_welcome_message()
                self.load_journal(id_token)
                self.stacked_widget.setCurrentIndex(1)
                
                self.db.child("users").child(local_id).update({
                    "last_played": datetime.now().isoformat()
                }, token=id_token)
        except Exception as e:
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Error")
            msg.setText(f"Failed to load user data: {str(e)}")
            msg.exec()

    def create_leaderboard_page(self):
        page = QWidget()
        page.setStyleSheet("background-color: #f5f5f5;")
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("Leaderboard")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #0d47a1;
            margin-bottom: 20px;
        """)
        
        self.leaderboard_table = QTableWidget()
        self.leaderboard_table.setColumnCount(5)
        self.leaderboard_table.setHorizontalHeaderLabels(["Rank", "Name", "Score", "Games Played", "Last Played"])
        self.leaderboard_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.leaderboard_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.leaderboard_table.setStyleSheet("""
            QTableView {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 10px;
            }
            QHeaderView::section {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                border: none;
            }
            QTableView::item {
                padding: 8px;
                border-bottom: 1px solid #E0E0E0;
            }
            QTableView::item:selected {
                background-color: #E3F2FD;
                color: black;
            }
        """)
        
        refresh_btn = QPushButton("Refresh Leaderboard")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        refresh_btn.clicked.connect(self.update_leaderboard)
        
        back_btn = QPushButton("Back to Menu")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        layout.addWidget(title)
        layout.addWidget(self.leaderboard_table, 1)
        layout.addWidget(refresh_btn)
        layout.addWidget(back_btn)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)

    def create_admin_page(self):
        page = QWidget()
        page.setStyleSheet("background-color: #f5f5f5;")
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("Admin Panel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #0d47a1;
            margin-bottom: 20px;
        """)
        
        self.questions_table = QTableWidget()
        self.questions_table.setColumnCount(6)
        self.questions_table.setHorizontalHeaderLabels(["Scenario", "Statement", "Type", "Category", "Difficulty", "Actions"])
        self.questions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.questions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.questions_table.setStyleSheet("""
            QTableView {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 10px;
            }
            QHeaderView::section {
                background-color: #673AB7;
                color: white;
                padding: 8px;
                border: none;
            }
            QTableView::item {
                padding: 8px;
                border-bottom: 1px solid #E0E0E0;
            }
            QTableView::item:selected {
                background-color: #D1C4E9;
                color: black;
            }
        """)
        
        add_btn = QPushButton("Add New Question")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        add_btn.clicked.connect(self.add_question)
        
        refresh_btn = QPushButton("Refresh Questions")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        refresh_btn.clicked.connect(self.load_questions)
        
        back_btn = QPushButton("Back to Menu")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #455A64;
            }
        """)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        layout.addWidget(title)
        layout.addWidget(self.questions_table, 1)
        layout.addWidget(add_btn)
        layout.addWidget(refresh_btn)
        layout.addWidget(back_btn)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)
    
    def show_leaderboard(self):
        self.play_click_sound()
        self.update_leaderboard()
        self.stacked_widget.setCurrentIndex(5)
    def update_leaderboard(self):
        try:
            # Fetch last 10 users ordered by score from your database
            users_snapshot = self.db.child("users").order_by_child("score").limit_to_last(10).get()
            users = users_snapshot.val()

            if not users:
                self.leaderboard_table.setRowCount(0)
                return
            
            # Sort users descending by score (limit_to_last may return ascending)
            sorted_users = sorted(users.items(), key=lambda x: x[1].get("score", 0), reverse=True)
            
            self.leaderboard_table.setRowCount(len(sorted_users))
            
            for i, (user_id, user_data) in enumerate(sorted_users):
                # Set rank
                self.leaderboard_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                # Set name, default to "Anonymous" if missing
                self.leaderboard_table.setItem(i, 1, QTableWidgetItem(user_data.get("name", "Anonymous")))
                # Set score
                self.leaderboard_table.setItem(i, 2, QTableWidgetItem(str(user_data.get("score", 0))))
                # Set games played
                self.leaderboard_table.setItem(i, 3, QTableWidgetItem(str(user_data.get("games_played", 0))))
                
                # Format last played datetime if present
                last_played = user_data.get("last_played", "")
                if last_played:
                    try:
                        dt = datetime.fromisoformat(last_played)
                        last_played = dt.strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        pass
                self.leaderboard_table.setItem(i, 4, QTableWidgetItem(last_played))
                
                # Color the top 3 rows
                if i == 0:
                    color = QColor(255, 215, 0)  # Gold
                elif i == 1:
                    color = QColor(192, 192, 192)  # Silver
                elif i == 2:
                    color = QColor(205, 127, 50)  # Bronze
                else:
                    color = None
                
                if color:
                    for col in range(5):
                        item = self.leaderboard_table.item(i, col)
                        if item:
                            item.setBackground(color)

        except Exception as e:
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Error")
            msg.setText(f"Failed to load leaderboard: {str(e)}")
            msg.exec()
    def load_questions(self):
        try:
            questions = self.db.child("questions").get().val() or {}
            
            self.questions_table.setRowCount(len(questions))
            
            for i, (qid, question_data) in enumerate(questions.items()):
                self.questions_table.setItem(i, 0, QTableWidgetItem(question_data.get("scenario", "")[:50] + "..."))
                self.questions_table.setItem(i, 1, QTableWidgetItem(question_data.get("statement", "")[:50] + "..."))
                self.questions_table.setItem(i, 2, QTableWidgetItem(question_data.get("type", "")))
                self.questions_table.setItem(i, 3, QTableWidgetItem(question_data.get("category", "")))
                self.questions_table.setItem(i, 4, QTableWidgetItem(question_data.get("difficulty", "Easy")))
                
                # Add action buttons
                widget = QWidget()
                layout = QHBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(5)
                
                edit_btn = QPushButton("Edit")
                edit_btn.setFixedSize(60, 30)
                edit_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #1976D2;
                    }
                """)
                edit_btn.clicked.connect(lambda _, qid=qid: self.edit_question(qid))
                
                delete_btn = QPushButton("Delete")
                delete_btn.setFixedSize(60, 30)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #F44336;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #D32F2F;
                    }
                """)
                delete_btn.clicked.connect(lambda _, qid=qid: self.delete_question(qid))
                
                layout.addWidget(edit_btn)
                layout.addWidget(delete_btn)
                widget.setLayout(layout)
                
                self.questions_table.setCellWidget(i, 5, widget)
                
        except Exception as e:
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Error")
            msg.setText(f"Failed to load questions: {str(e)}")
            msg.exec()
    
    def add_question(self):
        dialog = AdminQuestionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                question_data = dialog.get_question_data()
                self.db.child("questions").push(question_data)
                self.load_questions()
                self.load_questions_from_firebase()  # Refresh game questions
            except Exception as e:
                msg = StyledMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setWindowTitle("Error")
                msg.setText(f"Failed to add question: {str(e)}")
                msg.exec()
    
    def edit_question(self, qid):
        try:
            question_data = self.db.child("questions").child(qid).get().val()
            dialog = AdminQuestionDialog(self, question_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_data = dialog.get_question_data()
                self.db.child("questions").child(qid).update(updated_data)
                self.load_questions()
                self.load_questions_from_firebase()  # Refresh game questions
        except Exception as e:
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Error")
            msg.setText(f"Failed to edit question: {str(e)}")
            msg.exec()
    
    def delete_question(self, qid):
        confirm = QMessageBox.question(
            self, 
            "Confirm Delete", 
            "Are you sure you want to delete this question?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.db.child("questions").child(qid).remove()
                self.load_questions()
                self.load_questions_from_firebase()  # Refresh game questions
            except Exception as e:
                msg = StyledMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setWindowTitle("Error")
                msg.setText(f"Failed to delete question: {str(e)}")
                msg.exec()
    
    def logout(self):
        self.user = None
        self.user_data = None
        self.is_admin = False
        self.stacked_widget.setCurrentIndex(0)
    

    def update_user_score(self):
        if self.user:
            user_ref = self.db.child("users").child(self.user['localId'])

            # Get current games_played value
            current_games_played = user_ref.child("games_played").get().val()
            if current_games_played is None:
                current_games_played = 0

            # Update values in the correct user path
            self.db.child("users").child(self.user['localId']).update({
                "score": self.score,
                "games_played": current_games_played + 1,
                "last_played": datetime.now().isoformat()
            })  # Use keyword argument here



    def start_game(self):
        self.play_click_sound()
        if not self.user:
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Error")
            msg.setText("Please login to play")
            msg.exec()
            return
        
        self.score = 0
        self.correct_streak = 0
        self.wrong_streak = 0
        self.update_score()
        
        # Filter questions by current difficulty
        filtered_questions = [
            q for q in self.questions 
            if q.get("difficulty", "Easy") == self.current_difficulty
        ]
        
        if not filtered_questions:
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Error")
            msg.setText(f"No questions found for {self.current_difficulty} difficulty")
            msg.exec()
            return
        
        self.current_questions = filtered_questions
        self.current_question_index = 0
        self.load_next_scenario()
        
        # Initialize timer
        if self.time_pressure_mode:
            self.time_left = self.time_limit_slider.value()
            self.timer_label.setText(f"Time: {self.time_left}")
            self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: black;")
            self.game_timer.start(1000)
        else:
            self.timer_label.setText("Time: --")
        
        self.stacked_widget.setCurrentIndex(2)
    
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
            
            if question["type"] == "realistic positive":
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
                feedback += f"This was actually a  positive thought.\n\n{question['statement']} is a healthy way to look at this situation."
            else:
                feedback += f"This was a negative thought.\n\nCategory: {question['category']}\n\nExplanation: {question['explanation']}\n\nAlternative thought: {question['alternative']}"
        
        # Update character emotion
        self.update_character_emotion()
        
        # Show feedback
        msg = StyledMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Feedback")
        msg.setText(feedback)
        msg.exec()
        
        # Update game state
        self.update_score()
        self.update_user_score()
        self.current_question_index += 1
        
        # Load next scenario or loop back
        if self.current_question_index >= len(self.current_questions):
            self.current_question_index = 0
        
        self.load_next_scenario()
        
        # Reset timer in time pressure mode
        if self.time_pressure_mode:
            self.time_left = self.time_limit_slider.value()
            self.timer_label.setText(f"Time: {self.time_left}")
            self.game_timer.start(1000)
    
    def update_score(self):
        self.score_label.setText(f"Score: {self.score}")
    
    def update_character_emotion(self):
        if self.correct_streak >= 5:
            self.character_label.setPixmap(self.get_character_emotion("happy"))
        elif self.wrong_streak >= 3:
            self.character_label.setPixmap(self.get_character_emotion("sad"))
        else:
            self.character_label.setPixmap(self.get_character_emotion("neutral"))

    def get_character_emotion(self, emotion):
        pixmap = QPixmap(100, 100)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw face
        painter.setBrush(QBrush(QColor(255, 218, 185)))  # Peach color
        painter.drawEllipse(10, 10, 80, 80)
        
        # Draw eyes
        painter.setBrush(QBrush(Qt.GlobalColor.black))
        painter.drawEllipse(30, 30, 15, 15)
        painter.drawEllipse(55, 30, 15, 15)
        
        # Draw mouth based on emotion
        if emotion == "happy":
            painter.drawArc(25, 40, 50, 30, 0, -180 * 16)
        elif emotion == "sad":
            painter.drawArc(25, 60, 50, 30, 0, 180 * 16)
        else:  # neutral
            painter.drawLine(30, 60, 70, 60)
        
        painter.end()
        return pixmap

    def add_current_to_journal(self):
        if hasattr(self, 'current_questions') and self.current_question_index < len(self.current_questions):
            question = self.current_questions[self.current_question_index]
            if question["type"] == "positive":
                self.journal_entries.append(question["statement"])
                self.save_journal()
                self.update_journal_list()
                
                msg = StyledMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("Journal")
                msg.setText("Thought added to your journal!")
                msg.exec()
            else:
                msg = StyledMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setWindowTitle("Journal")
                msg.setText("Only realistic positive thoughts can be added to the journal.")
                msg.exec()
    
    def update_journal_list(self):
        self.journal_list.clear()
        self.journal_list.addItems(self.journal_entries)
    
    def view_journal_entry(self, item):
        text = item.text()
        self.journal_text.setPlainText(text)
    
    def delete_journal_entry(self):
        current_row = self.journal_list.currentRow()
        if current_row >= 0:
            confirm = QMessageBox.question(
                self, 
                "Confirm Delete", 
                "Are you sure you want to delete this entry?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if confirm == QMessageBox.StandardButton.Yes:
                self.journal_entries.pop(current_row)
                self.save_journal()
                self.update_journal_list()
                self.journal_text.clear()
    
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
                self.update_journal_list()
            except Exception as e:
                print(f"Failed to load journal: {str(e)}")
                self.journal_entries = []

    def change_difficulty(self, difficulty):
        self.current_difficulty = difficulty
        self.difficulty_label.setText(f"Difficulty: {self.current_difficulty}")
    
    def toggle_time_pressure(self, value):
        self.time_pressure_mode = bool(value)
        self.time_pressure_status.setText("On" if self.time_pressure_mode else "Off")
        if not self.time_pressure_mode:
            self.game_timer.stop()
            self.timer_label.setText("Time: --")
    
    def change_time_limit(self, value):
        self.time_left = value
        self.time_limit_value.setText(str(value))
    
    def update_timer(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.timer_label.setText(f"Time: {self.time_left}")
            
            # Change color when time is running low
            if self.time_left <= 10:
                self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: red;")
            else:
                self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: black;")
        else:
            self.game_timer.stop()
            
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Time's Up!")
            msg.setText("You ran out of time! Moving to next thought.")
            msg.exec()
            
            self.score = max(0, self.score - 5)
            self.wrong_streak += 1
            self.correct_streak = 0
            self.update_score()
            self.update_character_emotion()
            
            # Move to next question
            self.current_question_index += 1
            if self.current_question_index >= len(self.current_questions):
                self.current_question_index = 0
            self.load_next_scenario()
            
            if self.time_pressure_mode:
                self.time_left = self.time_limit_slider.value()
                self.timer_label.setText(f"Time: {self.time_left}")
                self.game_timer.start(1000)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show the main window
    game = ThoughtGame()
    game.show()
    
    sys.exit(app.exec())