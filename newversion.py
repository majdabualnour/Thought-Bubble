import sys
import json
import os
import random
import requests
from PyQt6.QtWidgets import QListWidgetItem

from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QMessageBox, QTextEdit,
    QListWidget, QComboBox, QSlider, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QFormLayout, QTabWidget,
    QProgressBar, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush, QFont, QFontDatabase, QImage
import firebase_admin
from firebase_admin import credentials, db, auth
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

# Load custom font
def load_fonts():
    QFontDatabase.addApplicationFont("assets/fonts/SuperPixel.ttf")
    QFontDatabase.addApplicationFont("assets/fonts/SuperPixel.ttf")

class StyledMessageBox(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QMessageBox {
                background-color: #1E293B;
                font-family: 'Poppins';
                border-radius: 12px;
                padding: 20px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }
            QMessageBox QLabel {
                color: #F8FAFC;
                font-size: 14px;
                font-weight: normal;
            }
            QMessageBox QPushButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-family: 'Poppins';
                min-width: 80px;
                transition: all 0.2s ease;
            }
            QMessageBox QPushButton:hover {
                background-color: #6366F1;
                transform: translateY(-1px);
            }
        """)

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login / Register")
        self.setModal(True)
        self.setFixedSize(500, 500)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0F172A, stop:1 #1E293B);
                font-family: 'Poppins';
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }
            QLabel {
                color: #F8FAFC;
                font-size: 14px;
                font-weight: normal;
            }
            QLineEdit {
                padding: 12px;
                border: 1px solid #334155;
                border-radius: 8px;
                font-size: 14px;
                background-color: rgba(30, 41, 59, 0.8);
                color: #F8FAFC;
                font-family: 'Poppins';
                transition: all 0.2s ease;
            }
            QLineEdit:focus {
                border: 1px solid #4F46E5;
                box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.3);
            }
            QPushButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                font-family: 'Poppins';
                font-weight: bold;
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #6366F1;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                transform: translateY(1px);
            }
            QTabWidget::pane {
                border: none;
                background-color: rgba(15, 23, 42, 0.7);
                border-radius: 8px;
                margin-top: 10px;
            }
            QTabBar::tab {
                padding: 12px 24px;
                background: #334155;
                border: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                color: #F8FAFC;
                font-family: 'Poppins';
                transition: all 0.2s ease;
            }
            QTabBar::tab:selected {
                background: #4F46E5;
                color: white;
            }
            QTabBar::tab:hover {
                background: #475569;
            }
        """)

        # Setup sounds
        self.click_sound = QSoundEffect()
        self.click_sound.setSource(QUrl.fromLocalFile("assets/sounds/click.wav"))
        self.click_sound.setVolume(0.3)
        
        self.success_sound = QSoundEffect()
        self.success_sound.setSource(QUrl.fromLocalFile("assets/sounds/success.wav"))
        self.success_sound.setVolume(0.3)
        
        self.error_sound = QSoundEffect()
        self.error_sound.setSource(QUrl.fromLocalFile("assets/sounds/error.wav"))
        self.error_sound.setVolume(0.3)

        self.FIREBASE_API_KEY = FIREBASE_API_KEY
        self.FIREBASE_DB_URL = FIREBASE_DB_URL
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 20, 30, 30)
        layout.setSpacing(20)
        
        # Add a title label
        title = QLabel("Thought Bubble")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #F8FAFC;
            margin-bottom: 10px;
            font-family: 'Poppins';
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        """)
        
        # Add a subtitleH
        subtitle = QLabel("Cultivate mindful thinking")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 16px;
            color: #94A3B8;
            margin-bottom: 40px;
            font-family: 'Poppins';
        """)
        
        self.tabs = QTabWidget()
        self.login_tab = QWidget()
        self.register_tab = QWidget()
        
        # Login Tab
        login_layout = QFormLayout()
        login_layout.setSpacing(20)
        login_layout.setContentsMargins(20, 20, 20, 20)
        
        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("Email")
        self.login_email.setStyleSheet("padding: 12px;")
        
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Password")
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_password.setStyleSheet("padding: 12px;")
        
        login_btn = QPushButton("Login")
        login_btn.setStyleSheet("""
            background-color: #4F46E5;
            font-weight: bold;
            padding: 14px;
        """)
        login_btn.clicked.connect(self.login)
        
        login_layout.addRow("Email:", self.login_email)
        login_layout.addRow("Password:", self.login_password)
        login_layout.addRow(login_btn)
        self.login_tab.setLayout(login_layout)
        
        # Register Tab
        register_layout = QFormLayout()
        register_layout.setSpacing(20)
        register_layout.setContentsMargins(20, 20, 20, 20)
        
        self.register_name = QLineEdit()
        self.register_name.setPlaceholderText("Full Name")
        self.register_name.setStyleSheet("padding: 12px;")
        
        self.register_email = QLineEdit()
        self.register_email.setPlaceholderText("Email")
        self.register_email.setStyleSheet("padding: 12px;")
        
        self.register_password = QLineEdit()
        self.register_password.setPlaceholderText("Password (min 6 chars)")
        self.register_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.register_password.setStyleSheet("padding: 12px;")
        
        register_btn = QPushButton("Register")
        register_btn.setStyleSheet("""
            background-color: #F59E0B;
            font-weight: bold;
            padding: 14px;
        """)
        register_btn.clicked.connect(self.register)
        
        register_layout.addRow("Name:", self.register_name)
        register_layout.addRow("Email:", self.register_email)
        register_layout.addRow("Password:", self.register_password)
        register_layout.addRow(register_btn)
        self.register_tab.setLayout(register_layout)
        
        self.tabs.addTab(self.login_tab, "Login")
        self.tabs.addTab(self.register_tab, "Register")
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
        # User credentials
        self.id_token = None
        self.local_id = None
        self.loading = False
    
    def login(self):
        self.click_sound.play()
        if self.loading:
            return
            
        email = self.login_email.text().strip()
        password = self.login_password.text().strip()

        if not email or not password:
            self.error_sound.play()
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Error")
            msg.setText("Please enter both email and password")
            msg.exec()
            return

        self.loading = True
        self.show_loading(True)
        
        
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
                self.error_sound.play()
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
                    self.success_sound.play()
                except AttributeError:
                    print("Login successful, but parent window doesn't handle logins")
            else:
                print("Login successful, but no parent window to notify")
            
            self.accept()
            
        except Exception as e:
            self.error_sound.play()
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Login Failed")
            msg.setText(str(e))
            msg.exec()
        finally:
            self.loading = False
            self.show_loading(False)
    
    def register(self):
        self.click_sound.play()
        if self.loading:
            return
            
        email = self.register_email.text().strip()
        password = self.register_password.text().strip()
        name = self.register_name.text().strip()

        if not email or not password or not name:
            self.error_sound.play()
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Error")
            msg.setText("Please fill all fields")
            msg.exec()
            return

        if len(password) < 6:
            self.error_sound.play()
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Error")
            msg.setText("Password must be at least 6 characters")
            msg.exec()
            return

        self.loading = True
        self.show_loading(True)
        
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
                self.error_sound.play()
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

            self.success_sound.play()
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Success")
            msg.setText("Registration successful! Please login.")
            msg.exec()
            
            self.register_email.clear()
            self.register_password.clear()
            self.register_name.clear()
            self.tabs.setCurrentIndex(0)
            
        except Exception as e:
            self.error_sound.play()
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Registration Failed")
            msg.setText(str(e))
            msg.exec()
        finally:
            self.loading = False
            self.show_loading(False)
    
    def show_loading(self, show):
        for btn in self.findChildren(QPushButton):
            btn.setEnabled(not show)
        
        if show:
            if not hasattr(self, 'loading_indicator'):
                self.loading_indicator = QWidget(self)
                self.loading_indicator.setFixedHeight(4)
                self.loading_indicator.setStyleSheet("""
                    background-color: transparent;
                    border: none;
                """)
                
                # Create a container for the animated dots
                self.loading_dots = QWidget(self.loading_indicator)
                self.loading_dots.setFixedSize(100, 4)
                
                # Create dot widgets
                self.dot1 = QWidget(self.loading_dots)
                self.dot1.setFixedSize(8, 8)
                self.dot1.setStyleSheet("background-color: #4F46E5; border-radius: 4px;")
                
                self.dot2 = QWidget(self.loading_dots)
                self.dot2.setFixedSize(8, 8)
                self.dot2.setStyleSheet("background-color: #4F46E5; border-radius: 4px;")
                
                self.dot3 = QWidget(self.loading_dots)
                self.dot3.setFixedSize(8, 8)
                self.dot3.setStyleSheet("background-color: #4F46E5; border-radius: 4px;")
                
                # Set up animations
                self.anim1 = QPropertyAnimation(self.dot1, b"pos")
                self.anim1.setDuration(1000)
                self.anim1.setLoopCount(-1)
                self.anim1.setStartValue(QPoint(0, 0))
                self.anim1.setKeyValueAt(0.5, QPoint(50, 0))
                self.anim1.setEndValue(QPoint(100, 0))
                self.anim1.setEasingCurve(QEasingCurve.Type.InOutQuad)
                
                self.anim2 = QPropertyAnimation(self.dot2, b"pos")
                self.anim2.setDuration(1000)
                self.anim2.setLoopCount(-1)
                self.anim2.setStartValue(QPoint(25, 0))
                self.anim2.setKeyValueAt(0.5, QPoint(75, 0))
                self.anim2.setEndValue(QPoint(25, 0))
                self.anim2.setEasingCurve(QEasingCurve.Type.InOutQuad)
                
                self.anim3 = QPropertyAnimation(self.dot3, b"pos")
                self.anim3.setDuration(1000)
                self.anim3.setLoopCount(-1)
                self.anim3.setStartValue(QPoint(50, 0))
                self.anim3.setKeyValueAt(0.5, QPoint(100, 0))
                self.anim3.setEndValue(QPoint(0, 0))
                self.anim3.setEasingCurve(QEasingCurve.Type.InOutQuad)
                
                # Start animations
                self.anim1.start()
                self.anim2.start()
                self.anim3.start()
                
                self.layout().addWidget(self.loading_indicator)
            
            # Center the dots
            self.loading_dots.move(self.width() // 2 - 50, self.height() - 40)
            self.loading_indicator.show()
        else:
            if hasattr(self, 'loading_indicator'):
                self.loading_indicator.hide()
                self.anim1.stop()
                self.anim2.stop()
                self.anim3.stop()

class ThoughtGame(QMainWindow):
    def __init__(self):
        super().__init__()
        load_fonts()
        
        # Setup sound effects
        self.click_sound = QSoundEffect()
        self.click_sound.setSource(QUrl.fromLocalFile("assets/sounds/click.wav"))
        self.click_sound.setVolume(0.3)
        
        self.correct_sound = QSoundEffect()
        self.correct_sound.setSource(QUrl.fromLocalFile("assets/sounds/correct.wav"))
        self.correct_sound.setVolume(0.3)
        
        self.wrong_sound = QSoundEffect()
        self.wrong_sound.setSource(QUrl.fromLocalFile("assets/sounds/wrong.wav"))
        self.wrong_sound.setVolume(0.3)
        
        self.page_turn_sound = QSoundEffect()
        self.page_turn_sound.setSource(QUrl.fromLocalFile("assets/sounds/page_turn.wav"))
        self.page_turn_sound.setVolume(0.3)
        
        self.notification_sound = QSoundEffect()
        self.notification_sound.setSource(QUrl.fromLocalFile("assets/sounds/notification.wav"))
        self.notification_sound.setVolume(0.3)
        
        # Background music
        self.audio_output = QAudioOutput()
        self.background_music = QMediaPlayer()
        self.background_music.setAudioOutput(self.audio_output)
        self.background_music.setSource(QUrl.fromLocalFile("assets/sounds/background.mp3"))
        self.audio_output.setVolume(0.2)
        self.background_music.setLoops(QMediaPlayer.Loops.Infinite)

        # Initialize Firebase
        self.initialize_firebase()
        self.journal_entries = []
        self.setWindowTitle("Thought Bubble - Mental Well-being Game")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0F172A;
                font-family: 'Poppins';
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
        
        # Start background music
        self.background_music.play()
    
    def play_click_sound(self):
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
        
        # Background with gradient
        page.setStyleSheet("""
        background-image: url(background.jpg);
        """)
        
        # Add a logo or title
        title = QLabel("Thought Bubble")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 48px;
            font-weight: bold;
            color: #F8FAFC;
            margin-top: 80px;
            margin-bottom: 10px;
            font-family: 'Poppins';
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        """)
        
        # Add a subtitle
        subtitle = QLabel("Cultivate mindful thinking")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 18px;
            color: #94A3B8;
            margin-bottom: 60px;
            font-family: 'Poppins';
        """)
        
        login_btn = QPushButton("Login / Register")
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                padding: 16px;
                border-radius: 12px;
                font-size: 18px;
                font-weight: bold;
                min-width: 240px;
                font-family: 'Poppins';
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #6366F1;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                transform: translateY(1px);
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
        
        # Add footer
        footer = QLabel("© 2023 Thought Bubble. All rights reserved.")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("""
            font-size: 12px;
            color: #64748B;
            margin-bottom: 20px;
            font-family: 'Poppins';
        """)
        layout.addWidget(footer)
        
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
        page.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0F172A, stop:1 #1E293B);
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        # Title
        title = QLabel("Thought Bubble")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #F8FAFC;
            margin-bottom: 10px;
            font-family: 'Poppins';
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        """)
        
        # Welcome message
        self.welcome_label = QLabel()
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_label.setStyleSheet("""
            font-size: 18px;
            color: #94A3B8;
            margin-bottom: 40px;
            font-family: 'Poppins';
        """)
        
        # Button styles
        btn_style = """
            QPushButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                padding: 16px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                min-width: 240px;
                font-family: 'Poppins';
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #6366F1;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                transform: translateY(1px);
            }
        """
        
        play_btn = QPushButton("Play Game")
        play_btn.setStyleSheet(btn_style)
        play_btn.clicked.connect(self.start_game)
        
        journal_btn = QPushButton("My Journal")
        journal_btn.setStyleSheet(btn_style.replace("#4F46E5", "#10B981"))
        journal_btn.clicked.connect(lambda: self.switch_page(10))
        
        leaderboard_btn = QPushButton("Leaderboard")
        leaderboard_btn.setStyleSheet(btn_style.replace("#4F46E5", "#F59E0B"))
        leaderboard_btn.clicked.connect(lambda: self.show_leaderboard())
        
        settings_btn = QPushButton("Settings")
        settings_btn.setStyleSheet(btn_style.replace("#4F46E5", "#64748B"))
        settings_btn.clicked.connect(lambda: self.switch_page(4))
        
        # Button container
        btn_container = QWidget()
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(20)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addWidget(play_btn)
        btn_layout.addWidget(journal_btn)
        btn_layout.addWidget(leaderboard_btn)
        btn_layout.addWidget(settings_btn)
        
        if self.is_admin:
            admin_btn = QPushButton("Admin Panel")
            admin_btn.setStyleSheet(btn_style.replace("#4F46E5", "#8B5CF6"))
            admin_btn.clicked.connect(lambda: self.switch_page(6))
            btn_layout.addWidget(admin_btn)
        
        btn_container.setLayout(btn_layout)
        
        # Bottom buttons
        bottom_btn_layout = QHBoxLayout()
        
        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                font-family: 'Poppins';
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #DC2626;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                transform: translateY(1px);
            }
        """)
        logout_btn.clicked.connect(self.logout)
        
        quit_btn = QPushButton("Quit")
        quit_btn.setStyleSheet("""
            QPushButton {
                background-color: #64748B;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                font-family: 'Poppins';
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #475569;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                transform: translateY(1px);
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
    
    def switch_page(self, index):
        self.play_click_sound()
        self.page_turn_sound.play()

        if self.stacked_widget.currentIndex() == index:
            return # Do nothing if we're already on the target page

        current_widget = self.stacked_widget.currentWidget()
        next_widget = self.stacked_widget.widget(index)

        if not current_widget or not next_widget:
            # Fallback: if somehow a widget isn't found, just switch directly
            self.stacked_widget.setCurrentIndex(index)
            return

        # Create opacity effect for the *current* widget
        # We create a new effect each time to ensure it's not lingering from previous animations
        opacity_effect_out = QGraphicsOpacityEffect(current_widget)
        current_widget.setGraphicsEffect(opacity_effect_out)

        # Fade out animation for the current widget
        fade_out = QPropertyAnimation(opacity_effect_out, b"opacity")
        fade_out.setDuration(200) # Adjust duration as needed
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.OutQuad)

        # Create opacity effect for the *next* widget
        opacity_effect_in = QGraphicsOpacityEffect(next_widget)
        next_widget.setGraphicsEffect(opacity_effect_in)

        # Fade in animation for the next widget (starts from invisible)
        fade_in = QPropertyAnimation(opacity_effect_in, b"opacity")
        fade_in.setDuration(200) # Should ideally match fade_out duration
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.InQuad)

        # Crucial: Connect fade_out.finished to handle the page switch and fade-in
        # Use a lambda to pass arguments and ensure proper scope
        fade_out.finished.connect(lambda: self._perform_switch_and_fade_in( self.stacked_widget, index, current_widget, next_widget,  opacity_effect_out, opacity_effect_in, fade_in))

        # Store references to prevent animations/effects from being garbage collected prematurely
        # You'll need attributes in your class to store these
        self._current_fade_out_animation = fade_out
        self._current_fade_in_animation = fade_in
        self._current_opacity_effect_out = opacity_effect_out
        self._current_opacity_effect_in = opacity_effect_in

        fade_out.start()


    def _perform_switch_and_fade_in(self, stacked_widget, new_index, old_widget, new_widget,
                                    old_effect, new_effect, fade_in_animation):
        # Clean up the effect on the old widget first
        if old_widget and old_effect:
            old_widget.setGraphicsEffect(None) # Remove effect to restore full rendering

        # Perform the actual page switch
        stacked_widget.setCurrentIndex(new_index)

        # Start the fade-in animation for the new widget
        fade_in_animation.start()

        # Once the fade-in animation completes, remove its effect for performance
        fade_in_animation.finished.connect(lambda: new_widget.setGraphicsEffect(None))


    def create_game_page(self):
        self.game_page = QWidget()
        self.game_page.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0F172A, stop:1 #1E293B);
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Top bar with score, difficulty and timer
        top_bar = QWidget()
        top_bar.setStyleSheet("""
            background-color: rgba(30, 41, 59, 0.8);
            border-radius: 12px;
            padding: 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        """)
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(10, 5, 10, 5)
        
        self.score_label = QLabel(f"Score: {self.score}")
        self.score_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #4F46E5;
            font-family: 'Poppins';
        """)
        
        self.difficulty_label = QLabel(f"Difficulty: {self.current_difficulty}")
        self.difficulty_label.setStyleSheet("""
            font-size: 16px;
            color: #10B981;
            font-family: 'Poppins';
        """)
        
        self.timer_label = QLabel("Time: --")
        self.timer_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #EF4444;
            font-family: 'Poppins';
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
            padding: 24px;
            background-color: rgba(30, 41, 59, 0.8);
            border-radius: 16px;
            border: 1px solid #334155;
            min-height: 120px;
            color: #F8FAFC;
            font-family: 'Poppins';
        """)
        
        # Character display
        self.character_label = QLabel()
        self.character_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.character_label.setFixedSize(200, 200)
        self.update_character_emotion()
        
        # Thought display with speech bubble effect
        self.thought_bubble = QWidget()
        self.thought_bubble.setStyleSheet("""
            background-color: rgba(30, 41, 59, 0.8);
            border-radius: 16px;
            border: 1px solid #4F46E5;
        """)
        thought_bubble_layout = QVBoxLayout()
        thought_bubble_layout.setContentsMargins(20, 20, 20, 20)
        
        self.thought_label = QLabel()
        self.thought_label.setWordWrap(True)
        self.thought_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thought_label.setStyleSheet("""
            font-size: 22px;
            font-style: italic;
            min-height: 140px;
            color: #F8FAFC;
            font-family: 'Poppins';
        """)
        
        thought_bubble_layout.addWidget(self.thought_label)
        self.thought_bubble.setLayout(thought_bubble_layout)
        
        # Accept/Reject Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(30)
        
        accept_btn = QPushButton("✔ Accept Thought")
        accept_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 16px 32px;
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
                font-family: 'Poppins';
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #059669;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                transform: translateY(1px);
            }
        """)
        accept_btn.clicked.connect(lambda: self.evaluate_thought("accept"))
        
        reject_btn = QPushButton("✘ Reject Thought")
        reject_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 16px 32px;
                background-color: #EF4444;
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
                font-family: 'Poppins';
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #DC2626;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                transform: translateY(1px);
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
                padding: 12px 24px;
                background-color: #4F46E5;
                color: white;
                border: none;
                border-radius: 8px;
                font-family: 'Poppins';
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #6366F1;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                transform: translateY(1px);
            }
        """)
        menu_btn.clicked.connect(lambda: self.switch_page(1))
        
        journal_btn = QPushButton("📝 Add to Journal")
        journal_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 12px 24px;
                background-color: #F59E0B;
                color: white;
                border: none;
                border-radius: 8px;
                font-family: 'Poppins';
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #D97706;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                transform: translateY(1px);
            }
        """)
        journal_btn.clicked.connect(self.add_current_to_journal)
        
        nav_layout.addWidget(menu_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(journal_btn)
        
        # Add to main layout
        layout.addWidget(top_bar)
        layout.addWidget(self.scenario_label)
        layout.addWidget(self.character_label, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.thought_bubble)
        layout.addLayout(button_layout)
        layout.addLayout(nav_layout)
        
        self.game_page.setLayout(layout)
        self.stacked_widget.addWidget(self.game_page)
        
        # Timer setup
        self.game_timer = QTimer(self)
        self.game_timer.timeout.connect(self.update_timer)
        
        # Load initial questions
        self.load_questions_from_firebase()

    def update_character_emotion(self):
        """Update the character image based on current game state"""
        if not hasattr(self, 'character_label'):
            return
            
        # Determine emotion based on streaks
        if self.correct_streak >= 3:
            emotion = "happy"
        elif self.wrong_streak >= 3:
            emotion = "sad"
        else:
            emotion = "neutral"
        
        # Try to load the character image
        try:
            pixmap = QPixmap(CHARACTER_IMAGES[emotion])
            if not pixmap.isNull():
                pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.character_label.setPixmap(pixmap)
            else:
                # Fallback to emoji if image fails to load
                emoji_map = {
                    "happy": "😊",
                    "neutral": "😐",
                    "sad": "😔",
                    "thinking": "🤔"
                }
                self.character_label.setText(emoji_map[emotion])
                self.character_label.setStyleSheet("""
                    font-size: 80px;
                    color: #F8FAFC;
                """)
        except Exception as e:
            print(f"Error loading character image: {str(e)}")
            # Fallback to emoji
            emoji_map = {
                "happy": "😊",
                "neutral": "😐",
                "sad": "😔",
                "thinking": "🤔"
            }
            self.character_label.setText(emoji_map[emotion])
            self.character_label.setStyleSheet("""
                font-size: 80px;
                color: #F8FAFC;
            """)

    def create_journal_page(self):
        page = QWidget()
        page.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0F172A, stop:1 #1E293B);
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("My Journal")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #F8FAFC;
            margin-bottom: 20px;
            font-family: 'Poppins';
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        """)
        
        # Journal list with scroll area
        self.journal_list = QListWidget()
        self.journal_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(30, 41, 59, 0.8);
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
                font-family: 'Poppins';
                color: #F8FAFC;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #334155;
                font-family: 'Poppins';
                transition: all 0.2s ease;
            }
            QListWidget::item:hover {
                background-color: rgba(71, 85, 105, 0.5);
            }
            QListWidget::item:selected {
                background-color: #4F46E5;
                color: white;
            }
        """)
        self.journal_list.itemDoubleClicked.connect(self.view_journal_entry)
        
        # Journal entry view
        self.journal_text = QTextEdit()
        self.journal_text.setReadOnly(True)
        self.journal_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(30, 41, 59, 0.8);
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 16px;
                font-size: 14px;
                font-family: 'Poppins';
                color: #F8FAFC;
            }
        """)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        back_btn = QPushButton("Back to Menu")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                font-family: 'Poppins';
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #6366F1;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                transform: translateY(1px);
            }
        """)
        back_btn.clicked.connect(lambda: self.switch_page(1))
        
        delete_btn = QPushButton("Delete Entry")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                font-family: 'Poppins';
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #DC2626;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                transform: translateY(1px);
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
        page.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0F172A, stop:1 #1E293B);
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        title = QLabel("Settings")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #F8FAFC;
            margin-bottom: 20px;
            font-family: 'Poppins';
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        """)
        
        # Difficulty selection
        difficulty_group = QWidget()
        difficulty_group.setStyleSheet("""
            background-color: rgba(30, 41, 59, 0.8);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        """)
        difficulty_layout = QHBoxLayout()
        difficulty_layout.setContentsMargins(0, 0, 0, 0)
        
        difficulty_label = QLabel("Difficulty:")
        difficulty_label.setStyleSheet("""
            font-size: 16px;
            color: #F8FAFC;
            font-family: 'Poppins';
        """)
        
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Easy", "Medium", "Hard"])
        self.difficulty_combo.setCurrentText(self.current_difficulty)
        self.difficulty_combo.setStyleSheet("""
            QComboBox {
                padding: 12px;
                border: 1px solid #334155;
                border-radius: 8px;
                min-width: 200px;
                background-color: rgba(30, 41, 59, 0.8);
                color: #F8FAFC;
                font-family: 'Poppins';
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: rgba(30, 41, 59, 0.8);
                border: 1px solid #334155;
                color: #F8FAFC;
                selection-background-color: #4F46E5;
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
            background-color: rgba(30, 41, 59, 0.8);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        """)
        time_pressure_layout = QHBoxLayout()
        time_pressure_layout.setContentsMargins(0, 0, 0, 0)
        
        time_pressure_label = QLabel("Time Pressure Mode:")
        time_pressure_label.setStyleSheet("""
            font-size: 16px;
            color: #F8FAFC;
            font-family: 'Poppins';
        """)
        
        self.time_pressure_toggle = QSlider(Qt.Orientation.Horizontal)
        self.time_pressure_toggle.setMinimum(0)
        self.time_pressure_toggle.setMaximum(1)
        self.time_pressure_toggle.setValue(1 if self.time_pressure_mode else 0)
        self.time_pressure_toggle.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #334155;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 24px;
                height: 24px;
                background: #4F46E5;
                border-radius: 12px;
            }
            QSlider::sub-page:horizontal {
                background: #4F46E5;
                border-radius: 4px;
            }
        """)
        self.time_pressure_toggle.valueChanged.connect(self.toggle_time_pressure)
        
        self.time_pressure_status = QLabel("On" if self.time_pressure_mode else "Off")
        self.time_pressure_status.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #4F46E5;
            font-family: 'Poppins';
        """)
        
        time_pressure_layout.addWidget(time_pressure_label)
        time_pressure_layout.addStretch()
        time_pressure_layout.addWidget(self.time_pressure_toggle)
        time_pressure_layout.addWidget(self.time_pressure_status)
        time_pressure_group.setLayout(time_pressure_layout)
        
        # Time limit slider
        time_limit_group = QWidget()
        time_limit_group.setStyleSheet("""
            background-color: rgba(30, 41, 59, 0.8);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        """)
        time_limit_layout = QHBoxLayout()
        time_limit_layout.setContentsMargins(0, 0, 0, 0)
        
        time_limit_label = QLabel("Time Limit (seconds):")
        time_limit_label.setStyleSheet("""
            font-size: 16px;
            color: #F8FAFC;
            font-family: 'Poppins';
        """)
        
        self.time_limit_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_limit_slider.setMinimum(10)
        self.time_limit_slider.setMaximum(60)
        self.time_limit_slider.setValue(self.time_left)
        self.time_limit_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #334155;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 24px;
                height: 24px;
                background: #10B981;
                border-radius: 12px;
            }
            QSlider::sub-page:horizontal {
                background: #10B981;
                border-radius: 4px;
            }
        """)
        self.time_limit_slider.valueChanged.connect(self.change_time_limit)
        
        self.time_limit_value = QLabel(str(self.time_left))
        self.time_limit_value.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #10B981;
            font-family: 'Poppins';
        """)
        
        time_limit_layout.addWidget(time_limit_label)
        time_limit_layout.addStretch()
        time_limit_layout.addWidget(self.time_limit_slider)
        time_limit_layout.addWidget(self.time_limit_value)
        time_limit_group.setLayout(time_limit_layout)
        
        # Music volume control
        music_group = QWidget()
        music_group.setStyleSheet("""
            background-color: rgba(30, 41, 59, 0.8);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        """)
        music_layout = QHBoxLayout()
        music_layout.setContentsMargins(0, 0, 0, 0)
        
        music_label = QLabel("Music Volume:")
        music_label.setStyleSheet("""
            font-size: 16px;
            color: #F8FAFC;
            font-family: 'Poppins';
        """)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(20)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #334155;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 24px;
                height: 24px;
                background: #F59E0B;
                border-radius: 12px;
            }
            QSlider::sub-page:horizontal {
                background: #F59E0B;
                border-radius: 4px;
            }
        """)
        self.volume_slider.valueChanged.connect(self.change_volume)
        
        music_layout.addWidget(music_label)
        music_layout.addStretch()
        music_layout.addWidget(self.volume_slider)
        music_group.setLayout(music_layout)
        
        # Back button
        back_btn = QPushButton("Back to Menu")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                padding: 16px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Poppins';
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #6366F1;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                transform: translateY(1px);
            }
        """)
        back_btn.clicked.connect(lambda: self.switch_page(1))
        
        layout.addWidget(title)
        layout.addWidget(difficulty_group)
        layout.addWidget(time_pressure_group)
        layout.addWidget(time_limit_group)
        layout.addWidget(music_group)
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
        self.scenario_label.setText(question.get("Scenario", "No scenario available"))
        self.thought_label.setText(question.get("Thought", "No thought available"))

        # Increment index for next call (loop back)
        self.current_question_index += 1
        if self.current_question_index >= len(self.questions):
            self.current_question_index = 0

    def load_questions_from_firebase(self):
        try:
            # Instead of loading from Firebase, we'll use the provided JSON pattern
            questions_data = [
                {"Difficulty": "Easy", "Scenario": "You forgot your umbrella on a rainy day", "Thought": "Maybe it's a sign I should slow down and take a break.", "label": "Positive", "Alternative": None},
                {"Difficulty": "Easy", "Scenario": "You forgot your umbrella on a rainy day", "Thought": "Now I'm going to get soaked and catch a cold.", "label": "Negative", "Alternative": "I can use a jacket or find shelter until the rain stops"},
                {"Difficulty": "Easy", "Scenario": "You forgot your umbrella on a rainy day", "Thought": "I always forget things like this.", "label": "Negative", "Alternative": "It happens sometimes. I usually remember other things."},
                {"Difficulty": "Easy", "Scenario": "You made a typo in an email", "Thought": "I look careless and unprofessional.", "label": "Negative", "Alternative": "Everyone makes typos sometimes; it doesn't define my professionalism."},
                {"Difficulty": "Easy", "Scenario": "You made a typo in an email", "Thought": "I'll pay attention next time", "label": "Positive", "Alternative": None},
                {"Difficulty": "Easy", "Scenario": "You got stuck in traffic", "Thought": "My whole day is ruined because of this.", "label": "Negative", "Alternative": "Traffic is frustrating, but I can still have a good day"},
                {"Difficulty": "Easy", "Scenario": "You got stuck in traffic", "Thought": "This is a good chance to listen to that podcast I wanted to try.", "label": "Positive", "Alternative": None},
                {"Difficulty": "Medium", "Scenario": "You got passed over for a promotion", "Thought": "They probably had favorites", "label": "Negative", "Alternative": "I'll ask for feedback and use it to improve for next time."},
                {"Difficulty": "Medium", "Scenario": "You got passed over for a promotion", "Thought": "I'm just not good enough.", "label": "Negative", "Alternative": "There's always room to grow—this gives me a clear path to work on."},
                {"Difficulty": "Medium", "Scenario": "You were in a social event, but no one had a conversation with you", "Thought": "Maybe they just had more in common with each other than with me.", "label": "Negative", "Alternative": "Next time, I can look for someone who seems open or shares my interests too."},
                {"Difficulty": "Medium", "Scenario": "You were in a social event, but no one had a conversation with you", "Thought": "I must have said something weird earlier.", "label": "Negative", "Alternative": "People probably weren't focused on what I said"},
                {"Difficulty": "Medium", "Scenario": "You were in a social event, but no one had a conversation with you", "Thought": "Next time, I'll invite a friend so I feel more at ease.", "label": "Positive", "Alternative": None},
                {"Difficulty": "Medium", "Scenario": "You texted a friend yesterday, but they have not responded yet", "Thought": "I don't want to bother them again if they're ignoring me.", "label": "Negative", "Alternative": "They might just be overwhelmed—I can check in later if I still feel unsure"},
                {"Difficulty": "Medium", "Scenario": "You texted a friend yesterday, but they have not responded yet", "Thought": "I guess they've got a lot going on lately", "label": "positive", "Alternative": None},
                {"Difficulty": "Hard", "Scenario": "You gave a compliment to a coworker, but they responded with a short 'Thanks' and quickly moved away.", "Thought": "Maybe they didn't take it seriously or felt uncomfortable", "label": "Negative", "Alternative": "People sometimes react oddly, not because of me but their own mood."},
                {"Difficulty": "Hard", "Scenario": "You noticed a friend sharing a joke that seemed to hint at something personal you told them in confidence.", "Thought": "Humor can be awkward but still shows some connection.", "label": "positive", "Alternative": None},
                {"Difficulty": "Hard", "Scenario": "You offered help on a group project, but your suggestions were mostly ignored. Later, you overheard the team discussing plans that didn't include your ideas.", "Thought": "It feels like my ideas weren't welcome or taken seriously", "label": "Negative", "Alternative": "Sometimes ideas get set aside for reasons unrelated to their value"},
                {"Difficulty": "Hard", "Scenario": "You reached out to a friend to make plans, but they only replied with a vague 'Maybe' and didn't follow up", "Thought": "Their hesitation could indicate distancing, but I don't want to impose my fears on reality.", "label": "Negative", "Alternative": "Maybe I'm interpreting silence through my own insecurities rather than facts"}
            ]

            self.questions = questions_data

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
        page.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0F172A, stop:1 #1E293B);
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("Leaderboard")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #F8FAFC;
            margin-bottom: 20px;
            font-family: 'Poppins';
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        """)
        
        self.leaderboard_table = QTableWidget()
        self.leaderboard_table.setColumnCount(5)
        self.leaderboard_table.setHorizontalHeaderLabels(["Rank", "Name", "Score", "Games Played", "Last Played"])
        self.leaderboard_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.leaderboard_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.leaderboard_table.setStyleSheet("""
            QTableView {
                background-color: rgba(30, 41, 59, 0.8);
                border: 1px solid #334155;
                border-radius: 12px;
                font-family: 'Poppins';
            }
            QHeaderView::section {
                background-color: #4F46E5;
                color: white;
                padding: 12px;
                border: none;
                font-family: 'Poppins';
            }
            QTableView::item {
                padding: 12px;
                border-bottom: 1px solid #334155;
                color: #F8FAFC;
                font-family: 'Poppins';
            }
            QTableView::item:selected {
                background-color: #4F46E5;
                color: white;
            }
        """)
        
        refresh_btn = QPushButton("Refresh Leaderboard")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                padding: 16px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Poppins';
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #059669;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                transform: translateY(1px);
            }
        """)
        refresh_btn.clicked.connect(self.update_leaderboard)
        
        back_btn = QPushButton("Back to Menu")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                padding: 16px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Poppins';
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #6366F1;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                transform: translateY(1px);
            }
        """)
        back_btn.clicked.connect(lambda: self.switch_page(2))
        
        layout.addWidget(title)
        layout.addWidget(self.leaderboard_table, 1)
        layout.addWidget(refresh_btn)
        layout.addWidget(back_btn)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)

    def create_admin_page(self):
        page = QWidget()
        page.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0F172A, stop:1 #1E293B);
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("Admin Panel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #F8FAFC;
            margin-bottom: 20px;
            font-family: 'Poppins';
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        """)
        
        self.questions_table = QTableWidget()
        self.questions_table.setColumnCount(6)
        self.questions_table.setHorizontalHeaderLabels(["Scenario", "Thought", "Label", "Difficulty", "Alternative", "Actions"])
        self.questions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.questions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.questions_table.setStyleSheet("""
            QTableView {
                background-color: rgba(30, 41, 59, 0.8);
                border: 1px solid #334155;
                border-radius: 12px;
                font-family: 'Poppins';
            }
            QHeaderView::section {
                background-color: #8B5CF6;
                color: white;
                padding: 12px;
                border: none;
                font-family: 'Poppins';
            }
            QTableView::item {
                padding: 12px;
                border-bottom: 1px solid #334155;
                color: #F8FAFC;
                font-family: 'Poppins';
            }
            QTableView::item:selected {
                background-color: #8B5CF6;
                color: white;
            }
        """)
        
        add_btn = QPushButton("Add New Question")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                padding: 16px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Poppins';
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #059669;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                transform: translateY(1px);
            }
        """)
        add_btn.clicked.connect(self.add_question)
        
        refresh_btn = QPushButton("Refresh Questions")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                padding: 16px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Poppins';
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #6366F1;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                transform: translateY(1px);
            }
        """)
        refresh_btn.clicked.connect(self.load_questions)
        
        back_btn = QPushButton("Back to Menu")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #64748B;
                color: white;
                border: none;
                padding: 16px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Poppins';
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #475569;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                transform: translateY(1px);
            }
        """)
        back_btn.clicked.connect(lambda: self.switch_page(1))
        
        layout.addWidget(title)
        layout.addWidget(self.questions_table, 1)
        layout.addWidget(add_btn)
        layout.addWidget(refresh_btn)
        layout.addWidget(back_btn)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)
    
    def show_leaderboard(self):
        self.play_click_sound()
        self.notification_sound.play()
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
                    color = QColor(30, 41, 59)  # Dark background
                
                for col in range(5):
                    item = self.leaderboard_table.item(i, col)
                    if item:
                        item.setBackground(color)
                        if i < 3:  # Make text more readable on medal colors
                            item.setForeground(QColor(30, 41, 59))

        except Exception as e:
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Error")
            msg.setText(f"Failed to load leaderboard: {str(e)}")
            msg.exec()
    
    def load_questions(self):
        try:
            # Using our embedded questions data instead of Firebase
            questions_data = [
                {"Difficulty": "Easy", "Scenario": "You forgot your umbrella on a rainy day", "Thought": "Maybe it's a sign I should slow down and take a break.", "label": "Positive", "Alternative": None},
                {"Difficulty": "Easy", "Scenario": "You forgot your umbrella on a rainy day", "Thought": "Now I'm going to get soaked and catch a cold.", "label": "Negative", "Alternative": "I can use a jacket or find shelter until the rain stops"},
                # ... (include all questions from the pattern)
            ]
            
            self.questions_table.setRowCount(len(questions_data))
            
            for i, question in enumerate(questions_data):
                self.questions_table.setItem(i, 0, QTableWidgetItem(question["Scenario"][:50] + "..." if len(question["Scenario"]) > 50 else question["Scenario"]))
                self.questions_table.setItem(i, 1, QTableWidgetItem(question["Thought"][:50] + "..." if len(question["Thought"]) > 50 else question["Thought"]))
                self.questions_table.setItem(i, 2, QTableWidgetItem(question["label"]))
                self.questions_table.setItem(i, 3, QTableWidgetItem(question["Difficulty"]))
                self.questions_table.setItem(i, 4, QTableWidgetItem(str(question["Alternative"])[:50] + "..." if question["Alternative"] and len(question["Alternative"]) > 50 else str(question["Alternative"])))
                
                # Add action buttons
                widget = QWidget()
                layout = QHBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(5)
                
                edit_btn = QPushButton("Edit")
                edit_btn.setFixedSize(60, 30)
                edit_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4F46E5;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-size: 12px;
                        font-family: 'Poppins';
                        transition: all 0.2s ease;
                    }
                    QPushButton:hover {
                        background-color: #6366F1;
                        transform: translateY(-1px);
                    }
                    QPushButton:pressed {
                        transform: translateY(1px);
                    }
                """)
                edit_btn.clicked.connect(lambda _, qid=i: self.edit_question(qid))
                
                delete_btn = QPushButton("Delete")
                delete_btn.setFixedSize(60, 30)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #EF4444;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-size: 12px;
                        font-family: 'Poppins';
                        transition: all 0.2s ease;
                    }
                    QPushButton:hover {
                        background-color: #DC2626;
                        transform: translateY(-1px);
                    }
                    QPushButton:pressed {
                        transform: translateY(1px);
                    }
                """)
                delete_btn.clicked.connect(lambda _, qid=i: self.delete_question(qid))
                
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
        self.play_click_sound()
        dialog = AdminQuestionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                question_data = dialog.get_question_data()
                # In a real app, you would push to Firebase here
                # self.db.child("questions").push(question_data)
                self.load_questions()
                self.load_questions_from_firebase()  # Refresh game questions
            except Exception as e:
                msg = StyledMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setWindowTitle("Error")
                msg.setText(f"Failed to add question: {str(e)}")
                msg.exec()
    
    def edit_question(self, qid):
        self.play_click_sound()
        try:
            # Get question from our embedded data
            question_data = self.questions[qid]
            dialog = AdminQuestionDialog(self, question_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_data = dialog.get_question_data()
                # In a real app, you would update Firebase here
                # self.db.child("questions").child(qid).update(updated_data)
                self.load_questions()
                self.load_questions_from_firebase()  # Refresh game questions
        except Exception as e:
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Error")
            msg.setText(f"Failed to edit question: {str(e)}")
            msg.exec()
    
    def delete_question(self, qid):
        self.play_click_sound()
        confirm = QMessageBox.question(
            self, 
            "Confirm Delete", 
            "Are you sure you want to delete this question?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                # In a real app, you would delete from Firebase here
                # self.db.child("questions").child(qid).remove()
                self.load_questions()
                self.load_questions_from_firebase()  # Refresh game questions
            except Exception as e:
                msg = StyledMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setWindowTitle("Error")
                msg.setText(f"Failed to delete question: {str(e)}")
                msg.exec()
    
    def logout(self):
        self.play_click_sound()
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
            })

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
            if q.get("Difficulty", "Easy") == self.current_difficulty
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
            self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #F8FAFC;")
            self.game_timer.start(1000)
        else:
            self.timer_label.setText("Time: --")
        
        self.stacked_widget.setCurrentIndex(2)
    
    def evaluate_thought(self, action):
        if not hasattr(self, 'current_questions') or self.current_question_index >= len(self.current_questions):
            return
            
        question = self.current_questions[self.current_question_index]
        correct = False
        
        if (action == "accept" and question["label"] == "Positive") or \
           (action == "reject" and question["label"] == "Negative"):
            # Correct classification
            self.score += 10
            self.correct_streak += 1
            self.wrong_streak = 0
            correct = True
            feedback = "✅ Correct! "
            self.correct_sound.play()
            
            if question["label"] == "Positive":
                feedback += "This is a healthy, realistic thought."
            else:
                feedback += "This is indeed an unrealistic negative thought."
        else:
            # Incorrect classification
            self.score = max(0, self.score - 5)
            self.wrong_streak += 1
            self.correct_streak = 0
            feedback = "❌ Not quite. "
            self.wrong_sound.play()
            
            if question["label"] == "Positive":
                feedback += f"This was actually a positive thought.\n\n{question['Thought']} is a healthy way to look at this situation."
            else:
                feedback += f"This was a negative thought.\n\nAlternative thought: {question['Alternative']}"
        
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
    
    def update_score(self):
        self.score_label.setText(f"Score: {self.score}")
        
        # Add animation to score update
        animation = QPropertyAnimation(self.score_label, b"pos")
        animation.setDuration(200)
        animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        current_pos = self.score_label.pos()
        animation.setStartValue(current_pos + QPoint(0, -10))
        animation.setEndValue(current_pos)
        animation.start()
    
    def update_timer(self):
        self.time_left -= 1
        self.timer_label.setText(f"Time: {self.time_left}")
        
        # Change color when time is running low
        if self.time_left <= 10:
            self.timer_label.setStyleSheet("""
                font-size: 16px;
                font-weight: bold;
                color: #EF4444;
                font-family: 'Poppins';
            """)
        
        if self.time_left <= 0:
            self.game_timer.stop()
            self.time_up()
    
    def time_up(self):
        self.notification_sound.play()
        msg = StyledMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Time's Up!")
        msg.setText(f"Your final score is {self.score}\n\nWould you like to play again?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.start_game()
        else:
            self.switch_page(1)
    
    def change_difficulty(self, difficulty):
        self.play_click_sound()
        self.current_difficulty = difficulty
        self.difficulty_label.setText(f"Difficulty: {difficulty}")
    
    def toggle_time_pressure(self, value):
        self.play_click_sound()
        self.time_pressure_mode = bool(value)
        self.time_pressure_status.setText("On" if self.time_pressure_mode else "Off")
    
    def change_time_limit(self, value):
        self.time_left = value
        self.time_limit_value.setText(str(value))
    
    def change_volume(self, value):
        self.audio_output.setVolume(value / 100)
    
    def add_current_to_journal(self):
        self.play_click_sound()
        if not hasattr(self, 'current_questions') or self.current_question_index >= len(self.current_questions):
            return
            
        question = self.current_questions[self.current_question_index]
        entry = {
            "scenario": question["Scenario"],
            "thought": question["Thought"],
            "label": question["label"],
            "alternative": question["Alternative"],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if self.user:
                # Push new entry to Firebase
                self.db.child("users").child(self.user['localId']).child("journal").push(entry, token=self.user['idToken'])
                self.load_journal(self.user['idToken'])
                self.notification_sound.play()
                
                msg = StyledMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("Success")
                msg.setText("Thought added to your journal!")
                msg.exec()
        except Exception as e:
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Error")
            msg.setText(f"Failed to add to journal: {str(e)}")
            msg.exec()
    
    def load_journal(self, id_token):
        try:
            if self.user:
                journal_snapshot = self.db.child("users").child(self.user['localId']).child("journal").get(token=id_token)
                self.journal_entries = journal_snapshot.val() or {}
                self.update_journal_list()
        except Exception as e:
            print(f"Error loading journal: {str(e)}")
    
    def update_journal_list(self):
        self.journal_list.clear()
        
        if not self.journal_entries:
            return
            
        # Sort entries by timestamp (newest first)
        sorted_entries = sorted(
            self.journal_entries.items(),
            key=lambda x: x[1].get("timestamp", ""),
            reverse=True
        )
        
        for entry_id, entry in sorted_entries:
            timestamp = entry.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    timestamp = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass
            
            item_text = f"{timestamp} - {entry.get('scenario', 'No scenario')[:30]}..."
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, entry_id)
            self.journal_list.addItem(item)
    
    def view_journal_entry(self, item):
        entry_id = item.data(Qt.ItemDataRole.UserRole)
        entry = self.journal_entries.get(entry_id, {})
        
        text = f"""
        <h3>Scenario:</h3>
        <p>{entry.get('scenario', 'No scenario')}</p>
        <h3>Thought:</h3>
        <p>{entry.get('thought', 'No thought')}</p>
        <h3>Type:</h3>
        <p>{entry.get('label', 'Unknown')}</p>
        """
        
        if entry.get("alternative"):
            text += f"""
            <h3>Alternative Thought:</h3>
            <p>{entry.get('alternative')}</p>
            """
        
        timestamp = entry.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
            text += f"""
            <h3>Recorded:</h3>
            <p>{timestamp}</p>
            """
        
        self.journal_text.setHtml(text)
    
    def delete_journal_entry(self):
        self.play_click_sound()
        current_item = self.journal_list.currentItem()
        if not current_item:
            return
            
        entry_id = current_item.data(Qt.ItemDataRole.UserRole)
        
        confirm = QMessageBox.question(
            self, 
            "Confirm Delete", 
            "Are you sure you want to delete this journal entry?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes and self.user:
            try:
                # Remove from Firebase
                self.db.child("users").child(self.user['localId']).child("journal").child(entry_id).remove(token=self.user['idToken'])
                # Remove from local data
                self.journal_entries.pop(entry_id, None)
                # Update UI
                self.update_journal_list()
                self.journal_text.clear()
                self.notification_sound.play()
            except Exception as e:
                msg = StyledMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setWindowTitle("Error")
                msg.setText(f"Failed to delete entry: {str(e)}")
                msg.exec()

class AdminQuestionDialog(QDialog):
    def __init__(self, parent=None, question_data=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Question" if question_data else "Add Question")
        self.setModal(True)
        self.setFixedSize(600, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #1E293B;
                font-family: 'Poppins';
                border-radius: 12px;
            }
            QLabel {
                color: #F8FAFC;
                font-size: 14px;
                font-weight: normal;
            }
            QLineEdit, QTextEdit, QComboBox {
                padding: 12px;
                border: 1px solid #334155;
                border-radius: 8px;
                font-size: 14px;
                background-color: #1E293B;
                color: #F8FAFC;
                font-family: 'Poppins';
            }
            QPushButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                font-family: 'Poppins';
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6366F1;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        self.scenario_edit = QTextEdit()
        self.scenario_edit.setPlaceholderText("Enter the scenario...")
        self.scenario_edit.setFixedHeight(80)
        
        self.thought_edit = QTextEdit()
        self.thought_edit.setPlaceholderText("Enter the thought...")
        self.thought_edit.setFixedHeight(80)
        
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Easy", "Medium", "Hard"])
        
        self.label_combo = QComboBox()
        self.label_combo.addItems(["Positive", "Negative"])
        
        self.alternative_edit = QTextEdit()
        self.alternative_edit.setPlaceholderText("Enter alternative thought (for negative thoughts)...")
        self.alternative_edit.setFixedHeight(80)
        
        form_layout.addRow("Scenario:", self.scenario_edit)
        form_layout.addRow("Thought:", self.thought_edit)
        form_layout.addRow("Difficulty:", self.difficulty_combo)
        form_layout.addRow("Label:", self.label_combo)
        form_layout.addRow("Alternative Thought:", self.alternative_edit)
        
        # Pre-fill if editing
        if question_data:
            self.scenario_edit.setText(question_data.get("Scenario", ""))
            self.thought_edit.setText(question_data.get("Thought", ""))
            self.difficulty_combo.setCurrentText(question_data.get("Difficulty", "Easy"))
            self.label_combo.setCurrentText(question_data.get("label", "Positive"))
            self.alternative_edit.setText(question_data.get("Alternative", ""))
        
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def get_question_data(self):
        return {
            "Scenario": self.scenario_edit.toPlainText(),
            "Thought": self.thought_edit.toPlainText(),
            "Difficulty": self.difficulty_combo.currentText(),
            "label": self.label_combo.currentText(),
            "Alternative": self.alternative_edit.toPlainText() if self.label_combo.currentText() == "Negative" else None
        }

def main():
    app = QApplication(sys.argv)
    
    # Set application style for modern look
    app.setStyleSheet("""
        QWidget {
                      
            font-family: 'Poppins';
        }
    """)
    
    game = ThoughtGame()
    game.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()