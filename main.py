import sys
import json
import os
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QStackedWidget, QMessageBox, QTextEdit,
                             QListWidget, QComboBox, QSlider, QLineEdit, QTableWidget,
                             QTableWidgetItem, QHeaderView, QDialog, QFormLayout, QTabWidget)

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush
import firebase_admin
from firebase_admin import credentials, db, auth
import requests
import pyrebase

FIREBASE_API_KEY = "AIzaSyBslVrw8gUYRkjpGHKWeftbvDp0-oBa9w0"  
FIREBASE_DB_URL = "https://csgame-f1969-default-rtdb.firebaseio.com" 
import random

import requests
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTabWidget, QWidget, 
                            QFormLayout, QLineEdit, QPushButton, QMessageBox)

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login / Register")
        self.setModal(True)
        self.setFixedSize(400, 350)
        
        # Firebase configuration
        self.FIREBASE_API_KEY = FIREBASE_API_KEY
        self.FIREBASE_DB_URL = FIREBASE_DB_URL
        
        layout = QVBoxLayout()
        
        self.tabs = QTabWidget()
        self.login_tab = QWidget()
        self.register_tab = QWidget()
        
        # Login Tab
        login_layout = QFormLayout()
        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("Email")
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Password")
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.login)
        
        login_layout.addRow("Email:", self.login_email)
        login_layout.addRow("Password:", self.login_password)
        login_layout.addRow(login_btn)
        self.login_tab.setLayout(login_layout)
        
        # Register Tab
        register_layout = QFormLayout()
        self.register_email = QLineEdit()
        self.register_email.setPlaceholderText("Email")
        self.register_password = QLineEdit()
        self.register_password.setPlaceholderText("Password (min 6 chars)")
        self.register_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.register_name = QLineEdit()
        self.register_name.setPlaceholderText("Full Name")
        register_btn = QPushButton("Register")
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
            QMessageBox.warning(self, "Error", "Please enter both email and password")
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
            
            if self.parent():  # Check if parent exists
                try:
                    self.parent().user_logged_in(self.local_id, self.id_token)
                except AttributeError:
                    # Fallback if parent doesn't have the method
                    print("Login successful, but parent window doesn't handle logins")
            else:
                print("Login successful, but no parent window to notify")
            
            self.accept()
            
            
        
        except Exception as e:
            QMessageBox.warning(self, "Login Failed", str(e))
    
    def register(self):
        email = self.register_email.text().strip()
        password = self.register_password.text().strip()
        name = self.register_name.text().strip()

        if not email or not password or not name:
            QMessageBox.warning(self, "Error", "Please fill all fields")
            return

        if len(password) < 6:
            QMessageBox.warning(self, "Error", "Password must be at least 6 characters")
            return

        try:
            # Step 1: Create user account
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

            # Step 2: Save user data to Realtime DB
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

            QMessageBox.information(self, "Success", "Registration successful! Please login.")
            
            # Clear fields and switch to login tab
            self.register_email.clear()
            self.register_password.clear()
            self.register_name.clear()
            self.tabs.setCurrentIndex(0)
            
        except Exception as e:
            QMessageBox.warning(self, "Registration Failed", str(e))

class AdminQuestionDialog(QDialog):
    def __init__(self, parent=None, question_data=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Question")
        self.setModal(True)
        self.setFixedSize(500, 400)
        
        layout = QFormLayout()
        
        self.statement = QTextEdit()
        self.statement.setPlaceholderText("Statement (e.g., \"If I don't get a perfect score...\")")
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["negative", "positive"])
        
        self.explanation = QTextEdit()
        self.explanation.setPlaceholderText("Explanation for why this is negative/positive")
        
        self.category = QLineEdit()
        self.category.setPlaceholderText("Cognitive distortion category (e.g., Black-and-White Thinking)")
        
        self.alternative = QTextEdit()
        self.alternative.setPlaceholderText("Alternative positive thought")
        
        save_btn = QPushButton("Save Question")
        save_btn.clicked.connect(self.accept)
        
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
        layout.addRow(save_btn)
        
        self.setLayout(layout)
    
    def get_question_data(self):
        return {
            "statement": self.statement.toPlainText(),
            "type": self.type_combo.currentText(),
            "explanation": self.explanation.toPlainText(),
            "category": self.category.text(),
            "alternative": self.alternative.toPlainText()
        }

class ThoughtGame(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize Firebase
        self.initialize_firebase()
        self.journal_entries = []
        self.setWindowTitle("Thought Bubble - Mental Well-being Game")
        self.setGeometry(100, 100, 1000, 700)
        
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
    
    def initialize_firebase(self):
        try:
            # Initialize Firebase Admin SDK for server-side operations
            cred = credentials.Certificate("csgame-f1969-firebase-adminsdk-fbsvc-a042dd397c.json")
            firebase_admin.initialize_app(cred, {
                'databaseURL': FIREBASE_DB_URL
            })
            
            # Initialize Pyrebase for client-side operations
            firebase_config = {
                "apiKey": "AIzaSyBslVrw8gUYRkjpGHKWeftbvDp0-oBa9w0",
                "authDomain": "csgame-f1969.firebaseapp.com",
                "databaseURL": "https://csgame-f1969-default-rtdb.firebaseio.com",
                "projectId": "csgame-f1969",
                "storageBucket": "csgame-f1969.firebasestorage.app",
                "messagingSenderId": "235095144063",
                "appId": "1:235095144063:web:e271e1fcb09d11b9eaf14a",
                "measurementId": "G-HDW13ZD2VZ"
            }

            
            self.pyrebase = pyrebase.initialize_app(firebase_config)
            self.db = self.pyrebase.database()  # For client-side database operations
            self.auth = self.pyrebase.auth()    # For client-side authentication
            
            # Server-side references (if needed)
            self.admin_db = db    # Firebase Admin database reference
            self.admin_auth = auth # Firebase Admin auth reference
            
        except FileNotFoundError:
            QMessageBox.critical(self, "Firebase Error", 
                                "Firebase credentials file not found.\n"
                                "Please ensure 'csgame-f1969-firebase-adminsdk-fbsvc-a042dd397c.json' exists.")
        except Exception as e:
            QMessageBox.critical(self, "Firebase Error", 
                                f"Failed to initialize Firebase: {str(e)}\n"
                                f"Check your Firebase configuration and internet connection.")
    def create_login_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("Thought Bubble")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 36px; font-weight: bold; margin-bottom: 30px;")
        
        login_btn = QPushButton("Login / Register")
        login_btn.setStyleSheet("font-size: 18px; padding: 10px;")
        login_btn.clicked.connect(self.show_login_dialog)
        
        layout.addWidget(title)
        layout.addStretch(1)
        layout.addWidget(login_btn)
        layout.addStretch(1)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)
    
    def show_login_dialog(self):
        dialog = LoginDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get the current user
            self.user = self.auth.current_user
            if self.user:
                # Check if user is admin
                user_data = self.db.child("users").child(self.user['localId']).get().val()
                self.is_admin = user_data.get("is_admin", False)
                
                # Move to main menu
                self.stacked_widget.setCurrentIndex(1)
    
    def create_main_menu(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("Thought Bubble")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 36px; font-weight: bold; margin-bottom: 30px;")
        self.welcome_label = QLabel()
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_label.setStyleSheet("font-size: 18px; margin-bottom: 20px;")
        layout.addWidget(self.welcome_label)
        play_btn = QPushButton("Play Game")
        play_btn.setStyleSheet("font-size: 18px; padding: 10px;")
        play_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        
        journal_btn = QPushButton("My Journal")
        journal_btn.setStyleSheet("font-size: 18px; padding: 10px;")
        journal_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        
        leaderboard_btn = QPushButton("Leaderboard")
        leaderboard_btn.setStyleSheet("font-size: 18px; padding: 10px;")
        leaderboard_btn.clicked.connect(lambda: self.show_leaderboard())
        
        settings_btn = QPushButton("Settings")
        settings_btn.setStyleSheet("font-size: 18px; padding: 10px;")
        settings_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(4))
        
        if self.is_admin:
            admin_btn = QPushButton("Admin Panel")
            admin_btn.setStyleSheet("font-size: 18px; padding: 10px; background-color: #FF5722; color: white;")
            admin_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(6))
            layout.addWidget(admin_btn)
        
        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet("font-size: 18px; padding: 10px;")
        logout_btn.clicked.connect(self.logout)
        
        quit_btn = QPushButton("Quit")
        quit_btn.setStyleSheet("font-size: 18px; padding: 10px;")
        quit_btn.clicked.connect(self.close)
        
        layout.addWidget(title)
        layout.addStretch(1)
        layout.addWidget(play_btn)
        layout.addWidget(journal_btn)
        layout.addWidget(leaderboard_btn)
        layout.addWidget(settings_btn)
        layout.addStretch(1)
        layout.addWidget(logout_btn)
        layout.addWidget(quit_btn)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)

    def create_game_page(self):
        self.game_page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.game_page.setStyleSheet("background-color: #f0f2f5;")

        # Top bar
        top_bar = QHBoxLayout()
        
        self.score_label = QLabel(f"Score: {self.score}")
        self.score_label.setStyleSheet("font-size: 18px; font-weight: 600;")

        self.difficulty_label = QLabel(f"Difficulty: {self.current_difficulty}")
        self.difficulty_label.setStyleSheet("font-size: 18px;")

        self.timer_label = QLabel("Time: --")
        self.timer_label.setStyleSheet("font-size: 18px; color: #e53935; font-weight: 600;")

        top_bar.addWidget(self.score_label)
        top_bar.addStretch()
        top_bar.addWidget(self.difficulty_label)
        top_bar.addStretch()
        top_bar.addWidget(self.timer_label)

        # Scenario section
        self.scenario_label = QLabel()
        self.scenario_label.setWordWrap(True)
        self.scenario_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scenario_label.setStyleSheet("""
            font-size: 20px;
            padding: 20px;
            border-radius: 15px;
            background-color: #ffffff;
            border: 1px solid #ccc;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
        """)

        # Character
        bubble = QWidget()
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
            border-radius: 15px;
            background-color: #fffde7;
            border: 1px solid #fbc02d;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.04);
        """)

        # Accept/Reject Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(30)

        accept_btn = QPushButton("✔ Accept Thought")
        accept_btn.setStyleSheet("""
            font-size: 16px;
            padding: 12px 20px;
            background-color: #4caf50;
            color: white;
            border: none;
            border-radius: 8px;
        """)
        accept_btn.clicked.connect(lambda: self.evaluate_thought("accept"))

        reject_btn = QPushButton("✘ Reject Thought")
        reject_btn.setStyleSheet("""
            font-size: 16px;
            padding: 12px 20px;
            background-color: #f44336;
            color: white;
            border: none;
            border-radius: 8px;
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
            font-size: 14px;
            padding: 10px 18px;
            background-color: #1976d2;
            color: white;
            border: none;
            border-radius: 6px;
        """)
        menu_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        journal_btn = QPushButton("📝 Add to Journal")
        journal_btn.setStyleSheet("""
            font-size: 14px;
            padding: 10px 18px;
            background-color: #fb8c00;
            color: white;
            border: none;
            border-radius: 6px;
        """)
        journal_btn.clicked.connect(self.add_current_to_journal)

        nav_layout.addWidget(menu_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(journal_btn)

        # Add to main layout
        layout.addLayout(top_bar)
        layout.addWidget(self.scenario_label)
        layout.addWidget(bubble)
        layout.addWidget(self.thought_label)
        layout.addLayout(button_layout)
        layout.addLayout(nav_layout)

        self.game_page.setLayout(layout)
        self.stacked_widget.addWidget(self.game_page)

        # Timer setup
        self.game_timer = QTimer(self)
        self.game_timer.timeout.connect(self.update_timer)

        # Load game data
        self.load_questions_from_firebase()
        self.load_next_scenario()

        
    def create_journal_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("My Journal")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        
        self.journal_list = QListWidget()
        self.journal_list.itemDoubleClicked.connect(self.view_journal_entry)
        
        self.journal_text = QTextEdit()
        self.journal_text.setReadOnly(True)
        
        button_layout = QHBoxLayout()
        
        back_btn = QPushButton("Back to Menu")
        back_btn.setStyleSheet("font-size: 14px; padding: 5px;")
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        delete_btn = QPushButton("Delete Entry")
        delete_btn.setStyleSheet("font-size: 14px; padding: 5px;")
        delete_btn.clicked.connect(self.delete_journal_entry)
        
        button_layout.addWidget(back_btn)
        button_layout.addStretch()
        button_layout.addWidget(delete_btn)
        
        layout.addWidget(title)
        layout.addWidget(self.journal_list)
        layout.addWidget(self.journal_text)
        layout.addLayout(button_layout)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)
        
        self.update_journal_list()
    
    def create_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("Settings")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        
        # Difficulty selection
        difficulty_layout = QHBoxLayout()
        difficulty_label = QLabel("Difficulty:")
        difficulty_label.setStyleSheet("font-size: 16px;")
        
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Easy", "Medium", "Hard"])
        self.difficulty_combo.setCurrentText(self.current_difficulty)
        self.difficulty_combo.currentTextChanged.connect(self.change_difficulty)
        
        difficulty_layout.addWidget(difficulty_label)
        difficulty_layout.addWidget(self.difficulty_combo)
        
        # Time pressure mode
        time_pressure_layout = QHBoxLayout()
        time_pressure_label = QLabel("Time Pressure Mode:")
        time_pressure_label.setStyleSheet("font-size: 16px;")
        
        self.time_pressure_toggle = QSlider(Qt.Orientation.Horizontal)
        self.time_pressure_toggle.setMinimum(0)
        self.time_pressure_toggle.setMaximum(1)
        self.time_pressure_toggle.setValue(1 if self.time_pressure_mode else 0)
        self.time_pressure_toggle.valueChanged.connect(self.toggle_time_pressure)
        
        self.time_pressure_status = QLabel("On" if self.time_pressure_mode else "Off")
        
        time_pressure_layout.addWidget(time_pressure_label)
        time_pressure_layout.addWidget(self.time_pressure_toggle)
        time_pressure_layout.addWidget(self.time_pressure_status)
        
        # Time limit slider
        time_limit_layout = QHBoxLayout()
        time_limit_label = QLabel("Time Limit (seconds):")
        time_limit_label.setStyleSheet("font-size: 16px;")
        
        self.time_limit_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_limit_slider.setMinimum(10)
        self.time_limit_slider.setMaximum(60)
        self.time_limit_slider.setValue(self.time_left)
        self.time_limit_slider.valueChanged.connect(self.change_time_limit)
        
        self.time_limit_value = QLabel(str(self.time_left))
        
        time_limit_layout.addWidget(time_limit_label)
        time_limit_layout.addWidget(self.time_limit_slider)
        time_limit_layout.addWidget(self.time_limit_value)
        
        # Back button
        back_btn = QPushButton("Back to Menu")
        back_btn.setStyleSheet("font-size: 16px; padding: 10px;")
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        layout.addWidget(title)
        layout.addLayout(difficulty_layout)
        layout.addLayout(time_pressure_layout)
        layout.addLayout(time_limit_layout)
        layout.addStretch()
        layout.addWidget(back_btn)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)
   
    def update_welcome_message(self):
        """Update the welcome message with user's name and score"""
        if hasattr(self, 'welcome_label') and self.user_data:
            name = self.user_data.get("name", "Player")
            score = self.user_data.get("score", 0)
            self.welcome_label.setText(f"Welcome back, {name}!\nYour current score: {score}")
    def load_next_scenario(self):
        if not self.questions:
            return

        question = self.questions[self.current_question_index]

        # Show the main statement
        self.scenario_label.setText(question["statement"])

        # Show the alternative (could be thought / answer)
        alt = question["alternative"]
        if alt:
            self.thought_label.setText(alt)
        else:
            self.thought_label.setText("")

        # Increment index for next call (loop back)
        self.current_question_index += 1
        if self.current_question_index >= len(self.questions):
            self.current_question_index = 0

    def load_questions_from_firebase(self):
        ref = db.reference('questions')
        data = ref.get()

        self.questions = []

        if data:
            for key, question in data.items():
                # Make sure the question has a 'statement' (or any other field you want to show)
                statement = question.get("statement", "")
                alternative = question.get("alternative", "")
                category = question.get("category", "")
                explanation = question.get("explanation", "")
                qtype = question.get("type", "")

                # Append a dict with all relevant fields you want to use later
                self.questions.append({
                    "key": key,
                    "statement": statement,
                    "alternative": alternative,
                    "category": category,
                    "explanation": explanation,
                    "type": qtype,
                })

        else:
            print("⚠️ No questions found in Firebase.")

        if self.questions:
            self.current_question_index = 0
            self.load_next_scenario()
        else:
            # fallback UI update if no questions loaded
            self.scenario_label.setText("No questions available.")


    def user_logged_in(self, local_id, id_token):
        """Handle successful login from LoginDialog"""
        self.user = {
            'localId': local_id,
            'idToken': id_token
        }
        
        # Get additional user data from database
        try:
            user_data = self.db.child("users").child(local_id).get(token=id_token).val()
            if user_data:
                self.user_data = user_data
                self.is_admin = user_data.get("is_admin", False)
                
                # Update UI
                self.update_welcome_message()  # This will now work
                self.load_journal(id_token)
                
                # Switch to main menu
                self.stacked_widget.setCurrentIndex(1)
                
                # Update last played time
                self.db.child("users").child(local_id).update({
                    "last_played": datetime.now().isoformat()
                }, token=id_token)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load user data: {str(e)}")

    def create_leaderboard_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("Leaderboard")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Fix for PyQt6
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        
        self.leaderboard_table = QTableWidget()
        self.leaderboard_table.setColumnCount(4)
        self.leaderboard_table.setHorizontalHeaderLabels(["Rank", "Name", "Score", "Games Played"])
        self.leaderboard_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)  # PyQt6 fix
        self.leaderboard_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # PyQt6 fix
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.update_leaderboard)
        
        back_btn = QPushButton("Back to Menu")
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        layout.addWidget(title)
        layout.addWidget(self.leaderboard_table)
        layout.addWidget(refresh_btn)
        layout.addWidget(back_btn)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)

    
    def create_admin_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("Admin Panel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        
        self.questions_table = QTableWidget()
        self.questions_table.setColumnCount(5)
        self.questions_table.setHorizontalHeaderLabels(["Statement", "Type", "Category", "Actions"])
        self.questions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.questions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        add_btn = QPushButton("Add New Question")
        add_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        add_btn.clicked.connect(self.add_question)
        
        refresh_btn = QPushButton("Refresh Questions")
        refresh_btn.clicked.connect(self.load_questions)
        
        back_btn = QPushButton("Back to Menu")
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        layout.addWidget(title)
        layout.addWidget(self.questions_table)
        layout.addWidget(add_btn)
        layout.addWidget(refresh_btn)
        layout.addWidget(back_btn)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)
    
    def show_leaderboard(self):
        self.update_leaderboard()
        self.stacked_widget.setCurrentIndex(5)
    
    def update_leaderboard(self):
        try:
            users = self.db.child("users").order_by_child("score").limit_to_last(10).get().val()
            
            sorted_users = sorted(users.items(), key=lambda x: x[1].get("score", 0), reverse=True)
            
            self.leaderboard_table.setRowCount(len(sorted_users))
            
            for i, (user_id, user_data) in enumerate(sorted_users):
                self.leaderboard_table.setItem(i, 0, QTableWidgetItem(str(i+1)))
                self.leaderboard_table.setItem(i, 1, QTableWidgetItem(user_data.get("name", "Anonymous")))
                self.leaderboard_table.setItem(i, 2, QTableWidgetItem(str(user_data.get("score", 0))))
                self.leaderboard_table.setItem(i, 3, QTableWidgetItem(str(user_data.get("games_played", 0))))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load leaderboard: {str(e)}")
    
    def load_questions(self):
        try:
            questions = self.db.child("questions").get().val() or {}
            
            self.questions_table.setRowCount(len(questions))
            
            for i, (qid, question_data) in enumerate(questions.items()):
                self.questions_table.setItem(i, 0, QTableWidgetItem(question_data.get("statement", "")[:50] + "..."))
                self.questions_table.setItem(i, 1, QTableWidgetItem(question_data.get("type", "")))
                self.questions_table.setItem(i, 2, QTableWidgetItem(question_data.get("category", "")))
                
                # Add action buttons
                widget = QWidget()
                layout = QHBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)
                
                edit_btn = QPushButton("Edit")
                edit_btn.setFixedSize(60, 30)
                edit_btn.clicked.connect(lambda _, qid=qid: self.edit_question(qid))
                
                delete_btn = QPushButton("Delete")
                delete_btn.setFixedSize(60, 30)
                delete_btn.setStyleSheet("background-color: #F44336; color: white;")
                delete_btn.clicked.connect(lambda _, qid=qid: self.delete_question(qid))
                
                layout.addWidget(edit_btn)
                layout.addWidget(delete_btn)
                widget.setLayout(layout)
                
                self.questions_table.setCellWidget(i, 3, widget)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load questions: {str(e)}")
    
    def add_question(self):
        dialog = AdminQuestionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                question_data = dialog.get_question_data()
                self.db.child("questions").push(question_data)
                self.load_questions()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to add question: {str(e)}")
    
    def edit_question(self, qid):
        try:
            question_data = self.db.child("questions").child(qid).get().val()
            dialog = AdminQuestionDialog(self, question_data)
            if dialog.exec_() == QDialog.Accepted:
                updated_data = dialog.get_question_data()
                self.db.child("questions").child(qid).update(updated_data)
                self.load_questions()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to edit question: {str(e)}")
    
    def delete_question(self, qid):
        confirm = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this question?",
                                     QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            try:
                self.db.child("questions").child(qid).remove()
                self.load_questions()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete question: {str(e)}")
    
    def logout(self):
        self.user = None
        self.is_admin = False
        self.stacked_widget.setCurrentIndex(0)
    
    def update_user_score(self):
        if self.user:
            try:
                self.db.child("users").child(self.user['localId']).update({
                    "score": self.score,
                    "games_played": firebase_admin.db.Increment(1)
                })
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to update score: {str(e)}")
  
    def start_game(self):
        if not self.user:
            QMessageBox.warning(self, "Error", "Please login to play")
            return
        
        self.score = 0
        self.correct_streak = 0
        self.wrong_streak = 0
        self.update_score()
        self.load_scenario()
        
        # Initialize timer properly
        if self.time_pressure_mode:
            self.time_left = self.time_limit_slider.value()
            self.timer_label.setText(f"Time: {self.time_left}")
            self.timer_label.setStyleSheet("font-size: 16px; color: black;")
            self.game_timer.start(1000)
        else:
            self.timer_label.setText("Time: --")
        
        self.stacked_widget.setCurrentIndex(2)
        
    def load_scenario(self):
        try:
            # Get questions from Firebase
            questions = self.db.child("questions").order_by_child("difficulty").equal_to(self.current_difficulty).get().val()
            
            if not questions:
                QMessageBox.warning(self, "Error", "No questions found for this difficulty level")
                self.return_to_menu()
                return
            
            # Convert to list and select random scenario
            questions_list = list(questions.values())
            self.current_scenario = random.choice(questions_list)
            
            # Debug print to verify thought loading
            print(self.current_scenario)

            print(f"Loaded scenario: {self.current_scenario.get('scenario')}")
            print(f"Thought: {self.current_scenario.get('statement')}")
            
            self.current_thoughts = [{
                "text": self.current_scenario.get("statement", ""),
                "type": self.current_scenario.get("type", "unrealistic negative"),
                "explanation": self.current_scenario.get("explanation", ""),
                "category": self.current_scenario.get("category", ""),
                "alternative": self.current_scenario.get("alternative", "")
            }]
            
            self.current_thought_index = 0
            
            self.scenario_label.setText(self.current_scenario.get("scenario", "No scenario text"))
            self.thought_label.setText(self.current_thoughts[0]["text"])  # Explicitly set text
            self.show_next_thought()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load scenario: {str(e)}")
            self.return_to_menu()
    
    def show_next_thought(self):
        if self.current_thought_index < len(self.current_thoughts):
            thought = self.current_thoughts[self.current_thought_index]
            self.thought_label.setText(thought["text"])
        else:
            # No more thoughts in this scenario
            self.load_scenario()
    
    def evaluate_thought(self, action):
        if self.current_thought_index >= len(self.questions):
            return
            
        thought = self.questions[self.current_thought_index]
        correct = False
        
        if (action == "accept" and thought["type"] == "realistic positive") or \
           (action == "reject" and thought["type"] == "unrealistic negative"):
            # Correct classification
            self.score += 10
            self.correct_streak += 1
            self.wrong_streak = 0
            correct = True
            feedback = "Correct! "
            
            if thought["type"] == "realistic positive":
                feedback += "This is a healthy, realistic thought."
            else:
                feedback += "This is indeed an unrealistic negative thought."
        else:
            # Incorrect classification
            self.score -= 5
            self.wrong_streak += 1
            self.correct_streak = 0
            feedback = "Not quite. "
            
            if thought["type"] == "realistic positive":
                feedback += f"This was actually a realistic positive thought. {thought['text']} is a healthy way to look at this situation."
            else:
                feedback += f"This was an unrealistic negative thought. A more balanced perspective might be: {self.get_alternative_thought(thought)}"
        
        # Update character emotion
        self.update_character_emotion()
        
        # Show feedback
        QMessageBox.information(self, "Feedback", feedback)
        
        # Update game state
        self.update_score()
        self.current_thought_index += 1
        self.show_next_thought()
        
        # Reset timer in time pressure mode
        if self.time_pressure_mode:
            self.time_left = self.time_limit_slider.value()
            self.timer_label.setText(f"Time: {self.time_left}")
    
    def get_alternative_thought(self, thought):
        # Find a realistic positive alternative for the given negative thought
        for t in self.current_scenario["thoughts"]:
            if t["type"] == "realistic positive":
                return t["text"]
        return "There might be other explanations for this situation."
    
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
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush
        from PyQt6.QtCore import Qt
        pixmap = QPixmap(100, 100)
        if pixmap.isNull():
            print("Failed to create pixmap!")
            return QPixmap()  # Return empty pixmap on failure

        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        if not painter.isActive():
            print("Painter not active!")
            return pixmap

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor(255, 218, 185)))  # Peach color
        painter.drawEllipse(10, 10, 80, 80)
        
        painter.setBrush(QBrush(Qt.GlobalColor.black))
        painter.drawEllipse(30, 30, 15, 15)
        painter.drawEllipse(55, 30, 15, 15)
        
        if emotion == "happy":
            painter.drawArc(25, 40, 50, 30, 0, -180 * 16)
        elif emotion == "sad":
            painter.drawArc(25, 60, 50, 30, 0, 180 * 16)
        else:  # neutral
            painter.drawLine(30, 60, 70, 60)
        
        painter.end()
        return pixmap

    def add_current_to_journal(self):
        if self.current_thought_index < len(self.current_thoughts):
            thought = self.current_thoughts[self.current_thought_index]
            if thought["type"] == "realistic positive":
                self.journal_entries.append(thought["text"])
                self.save_journal()
                self.update_journal_list()
                QMessageBox.information(self, "Journal", "Thought added to your journal!")
            else:
                QMessageBox.warning(self, "Journal", "Only realistic positive thoughts can be added to the journal.")
    
    def update_journal_list(self):
        self.journal_list.clear()
        self.journal_list.addItems(self.journal_entries)
    
    def view_journal_entry(self, item):
        text = item.text()
        self.journal_text.setPlainText(text)
    
    def delete_journal_entry(self):
        current_row = self.journal_list.currentRow()
        if current_row >= 0:
            self.journal_entries.pop(current_row)
            self.save_journal()
            self.update_journal_list()
            self.journal_text.clear()
    
    def save_journal(self):
        with open("thought_journal.json", "w") as f:
            json.dump(self.journal_entries, f)

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
                self.timer_label.setStyleSheet("font-size: 16px; color: red; font-weight: bold;")
            else:
                self.timer_label.setStyleSheet("font-size: 16px; color: black;")
        else:
            self.game_timer.stop()
            QMessageBox.warning(self, "Time's Up!", "You ran out of time! Moving to next thought.")
            self.score = max(0, self.score - 5)
            self.wrong_streak += 1
            self.correct_streak = 0
            self.update_score()
            self.update_character_emotion()
            self.current_thought_index += 1
            self.show_next_thought()
            
            if self.time_pressure_mode:
                self.time_left = self.time_limit_slider.value()
                self.timer_label.setText(f"Time: {self.time_left}")
                self.game_timer.start(1000)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = ThoughtGame()
    game.show()
    sys.exit(app.exec())