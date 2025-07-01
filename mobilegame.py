# thought_bubble_mobile.py
import sys
import os
import json
import random
import requests
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QMessageBox, QTextEdit,
    QListWidget, QComboBox, QSlider, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QFormLayout, QTabWidget,
    QProgressBar, QGraphicsOpacityEffect, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve, QPoint, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush, QFont, QFontDatabase, QImage
import pyrebase
from PyQt6.QtMultimedia import QSoundEffect, QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl

# Firebase Configuration
FIREBASE_API_KEY = "AIzaSyBslVrw8gUYRkjpGHKWeftbvDp0-oBa9w0"
FIREBASE_DB_URL = "https://csgame-f1969-default-rtdb.firebaseio.com"

# Character images (replace with your actual image paths)
CHARACTER_IMAGES = {
    "happy": "assets/images/happy.png",
    "neutral": "assets/images/neutral.png",
    "sad": "assets/images/sad.png",
    "thinking": "assets/images/thinking.png"
}

class MobileBackgroundWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #FFF0F5;")

class StyledMessageBox(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QMessageBox {
                background-color: #FFFFFF;
                font-family: 'Poppins';
                border-radius: 12px;
                padding: 20px;
                border: 1px solid #FFB6C1;
            }
            QMessageBox QLabel {
                color: #333333;
                font-size: 14px;
                font-weight: normal;
            }
            QMessageBox QPushButton {
                background-color: #FF69B4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #FF1493;
            }
        """)

class MobileLoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login / Register")
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                font-family: 'Poppins';
                border-radius: 12px;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
            }
            QLineEdit {
                padding: 12px;
                border: 1px solid #FFB6C1;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #FF69B4;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QTabWidget::pane {
                border: none;
                background-color: #FFF0F5;
                border-radius: 8px;
            }
            QTabBar::tab {
                padding: 12px;
                background: #FFB6C1;
                border: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                color: #FFFFFF;
            }
            QTabBar::tab:selected {
                background: #FF69B4;
                color: white;
            }
        """)

        self.setup_ui()
        self.setup_sounds()
        
    def setup_sounds(self):
        self.click_sound = QSoundEffect()
        self.click_sound.setSource(QUrl.fromLocalFile("assets/sounds/click.wav"))
        self.click_sound.setVolume(0.3)
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Thought Bubble")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #FF69B4;")
        
        self.tabs = QTabWidget()
        self.setup_login_tab()
        self.setup_register_tab()
        
        layout.addWidget(title)
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
    def setup_login_tab(self):
        tab = QWidget()
        layout = QFormLayout()
        
        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("Email")
        
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Password")
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.login)
        
        layout.addRow("Email:", self.login_email)
        layout.addRow("Password:", self.login_password)
        layout.addRow(login_btn)
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Login")
        
    def setup_register_tab(self):
        tab = QWidget()
        layout = QFormLayout()
        
        self.register_name = QLineEdit()
        self.register_name.setPlaceholderText("Full Name")
        
        self.register_email = QLineEdit()
        self.register_email.setPlaceholderText("Email")
        
        self.register_password = QLineEdit()
        self.register_password.setPlaceholderText("Password (min 6 chars)")
        self.register_password.setEchoMode(QLineEdit.EchoMode.Password)
        
        register_btn = QPushButton("Register")
        register_btn.clicked.connect(self.register)
        
        layout.addRow("Name:", self.register_name)
        layout.addRow("Email:", self.register_email)
        layout.addRow("Password:", self.register_password)
        layout.addRow(register_btn)
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Register")
        
    def login(self):
        self.click_sound.play()
        email = self.login_email.text().strip()
        password = self.login_password.text().strip()

        if not email or not password:
            self.show_error("Please enter both email and password")
            return

        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
            response = requests.post(url, json={
                "email": email,
                "password": password,
                "returnSecureToken": True
            })
            data = response.json()

            if "error" in data:
                error_msg = data["error"]["message"]
                if "INVALID_EMAIL" in error_msg:
                    raise Exception("Invalid email address")
                elif "INVALID_PASSWORD" in error_msg:
                    raise Exception("Incorrect password")
                else:
                    raise Exception(error_msg)

            self.id_token = data["idToken"]
            self.local_id = data["localId"]
            self.accept()
            
        except Exception as e:
            self.show_error(str(e))
            
    def register(self):
        self.click_sound.play()
        email = self.register_email.text().strip()
        password = self.register_password.text().strip()
        name = self.register_name.text().strip()

        if not email or not password or not name:
            self.show_error("Please fill all fields")
            return

        if len(password) < 6:
            self.show_error("Password must be at least 6 characters")
            return

        try:
            # Create user
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
            response = requests.post(url, json={
                "email": email,
                "password": password,
                "returnSecureToken": True
            })
            data = response.json()

            if "error" in data:
                raise Exception(data["error"]["message"])

            # Save user data
            user_data = {
                "name": name,
                "email": email,
                "score": 0,
                "games_played": 0,
                "last_played": "",
                "is_admin": False
            }
            
            db_url = f"{FIREBASE_DB_URL}/users/{data['localId']}.json?auth={data['idToken']}"
            requests.put(db_url, json=user_data)
            
            self.show_success("Registration successful! Please login.")
            self.register_email.clear()
            self.register_password.clear()
            self.register_name.clear()
            self.tabs.setCurrentIndex(0)
            
        except Exception as e:
            self.show_error(str(e))
            
    def show_error(self, message):
        msg = StyledMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Error")
        msg.setText(message)
        msg.exec()
        
    def show_success(self, message):
        msg = StyledMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Success")
        msg.setText(message)
        msg.exec()

class MobileThoughtGame(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thought Bubble")
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
                font-family: 'Poppins';
            }
        """)
        
        # Initialize Firebase
        self.initialize_firebase()
        
        # User data
        self.user = None
        self.is_admin = False
        
        # Game data
        self.score = 0
        self.correct_streak = 0
        self.wrong_streak = 0
        self.current_difficulty = "Easy"
        
        # Create main stacked widget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create pages
        self.create_login_page()
        self.create_main_menu()
        self.create_game_page()
        self.create_journal_page()
        
        # Start with login page
        self.stacked_widget.setCurrentIndex(0)
        
    def initialize_firebase(self):
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
    
    def create_login_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        background = MobileBackgroundWidget()
        layout.addWidget(background)
        
        self.show_login_dialog()
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)
    
    def show_login_dialog(self):
        dialog = MobileLoginDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.user_logged_in(dialog.local_id, dialog.id_token)
    
    def user_logged_in(self, local_id, id_token):
        try:
            # Load user data
            user_data = self.db.child("users").child(local_id).get(token=id_token).val()
            if user_data:
                self.user = {
                    'localId': local_id,
                    'idToken': id_token,
                    'data': user_data
                }
                self.is_admin = user_data.get("is_admin", False)
                
                # Update last played
                self.db.child("users").child(local_id).update({
                    "last_played": datetime.now().isoformat()
                }, token=id_token)
                
                # Switch to main menu
                self.stacked_widget.setCurrentIndex(1)
        except Exception as e:
            self.show_error_message("Login Error", str(e))
    
    def create_main_menu(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        background = MobileBackgroundWidget()
        layout.addWidget(background)
        
        title = QLabel("Thought Bubble")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #FF69B4;")
        
        self.welcome_label = QLabel()
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn_style = """
            QPushButton {
                background-color: #FF69B4;
                color: white;
                border: none;
                padding: 16px;
                border-radius: 12px;
                font-size: 16px;
                margin: 8px;
            }
        """
        
        play_btn = QPushButton("Play Game")
        play_btn.setStyleSheet(btn_style)
        play_btn.clicked.connect(self.start_game)
        
        journal_btn = QPushButton("My Journal")
        journal_btn.setStyleSheet(btn_style.replace("#FF69B4", "#FF82AB"))
        journal_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        
        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet(btn_style.replace("#FF69B4", "#FFB6C1"))
        logout_btn.clicked.connect(self.logout)
        
        layout.addWidget(title)
        layout.addWidget(self.welcome_label)
        layout.addWidget(play_btn)
        layout.addWidget(journal_btn)
        layout.addWidget(logout_btn)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)
    
    def create_game_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        self.score_label = QLabel("Score: 0")
        self.score_label.setStyleSheet("font-size: 16px; color: #FF69B4;")
        
        self.scenario_label = QLabel()
        self.scenario_label.setWordWrap(True)
        
        self.thought_label = QLabel()
        self.thought_label.setWordWrap(True)
        
        accept_btn = QPushButton("Accept Thought")
        accept_btn.setStyleSheet("background-color: #FF82AB; color: white;")
        accept_btn.clicked.connect(lambda: self.evaluate_thought("accept"))
        
        reject_btn = QPushButton("Reject Thought")
        reject_btn.setStyleSheet("background-color: #FFB6C1; color: white;")
        reject_btn.clicked.connect(lambda: self.evaluate_thought("reject"))
        
        menu_btn = QPushButton("Back to Menu")
        menu_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        layout.addWidget(self.score_label)
        layout.addWidget(self.scenario_label)
        layout.addWidget(self.thought_label)
        layout.addWidget(accept_btn)
        layout.addWidget(reject_btn)
        layout.addWidget(menu_btn)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)
    
    def create_journal_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("My Journal")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #FF69B4;")
        
        self.journal_list = QListWidget()
        
        back_btn = QPushButton("Back to Menu")
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        layout.addWidget(title)
        layout.addWidget(self.journal_list)
        layout.addWidget(back_btn)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)
    
    def start_game(self):
        if not self.user:
            self.show_error_message("Error", "Please login to play")
            return
        
        self.score = 0
        self.correct_streak = 0
        self.wrong_streak = 0
        self.update_score()
        
        # Load questions from Firebase
        try:
            questions_snapshot = self.db.child("questions").get()
            self.questions = [q.val() for q in questions_snapshot.each()] if questions_snapshot.each() else []
            
            if not self.questions:
                self.show_error_message("Error", "No questions available")
                return
                
            self.current_question_index = 0
            self.load_next_question()
            self.stacked_widget.setCurrentIndex(2)
            
        except Exception as e:
            self.show_error_message("Error", str(e))
    
    def load_next_question(self):
        if not self.questions:
            return
            
        question = self.questions[self.current_question_index]
        self.scenario_label.setText(question.get("category", "No scenario"))
        self.thought_label.setText(question.get("statement", "No thought"))
        
        self.current_question_index += 1
        if self.current_question_index >= len(self.questions):
            self.current_question_index = 0
    
    def evaluate_thought(self, action):
        if not hasattr(self, 'questions') or not self.questions:
            return
            
        question = self.questions[self.current_question_index - 1]
        correct = False
        
        if (action == "accept" and question.get("type") == "positive") or \
           (action == "reject" and question.get("type") == "negative"):
            self.score += 10
            self.correct_streak += 1
            self.wrong_streak = 0
            correct = True
            feedback = "✅ Correct! "
        else:
            self.score = max(0, self.score - 5)
            self.wrong_streak += 1
            self.correct_streak = 0
            feedback = "❌ Not quite. "
            
        self.update_score()
        self.load_next_question()
        
        msg = StyledMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Feedback")
        msg.setText(feedback)
        msg.exec()
    
    def update_score(self):
        self.score_label.setText(f"Score: {self.score}")
        
    def logout(self):
        self.user = None
        self.stacked_widget.setCurrentIndex(0)
    
    def show_error_message(self, title, message):
        msg = StyledMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec()

def main():
    app = QApplication(sys.argv)
    game = MobileThoughtGame()
    
    # Adjust window size for mobile
    screen_geometry = app.primaryScreen().availableGeometry()
    game.resize(int(screen_geometry.width() * 0.9), int(screen_geometry.height() * 0.9))
    
    game.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()