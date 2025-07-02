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
from PyQt6.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve, QPoint, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush, QFont, QFontDatabase, QImage
import firebase_admin
from firebase_admin import credentials, db, auth
import pyrebase
from PyQt6.QtMultimedia import QSoundEffect, QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl




import os
import sys

def resource_path(relative_path):
    """ Get path to resource, works for dev and for PyInstaller .exe """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)
# Firebase Configuration
FIREBASE_API_KEY = "AIzaSyBslVrw8gUYRkjpGHKWeftbvDp0-oBa9w0"
FIREBASE_DB_URL = "https://csgame-f1969-default-rtdb.firebaseio.com"

# Character images (replace with your actual image paths)
CHARACTER_IMAGES = {
    "happy": resource_path("assets/images/happy.png"),
    "neutral": resource_path("assets/images/neutral.png"),
    "sad": resource_path("assets/images/sad.png"),
    "thinking": resource_path("assets/images/thinking.png")
}

# Background image
BACKGROUND_IMAGE = "background.jpg"
# Load custom font
def load_fonts():
    QFontDatabase.addApplicationFont("assets/fonts/SuperPixel.ttf")
    QFontDatabase.addApplicationFont("assets/fonts/SuperPixel.ttf")

class BackgroundWidget(QLabel):  # Using QLabel instead of QWidget for easier image handling
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(1, 1)  # Ensure it takes space even if empty
        self.setScaledContents(False)  # Important for proper scaling
        
        # Load the background image
        self.background = None
        try:
            image_path = os.path.join(os.path.dirname(__file__), "assets", "images", "background.jpg")
            if os.path.exists(image_path):
                self.background = QPixmap(image_path)
                self.setPixmap(self.background)
        except Exception as e:
            print(f"Error loading background: {e}")

    def resizeEvent(self, event):
        """Scale the background image when widget is resized"""
        if self.background:
            # Scale the image while maintaining aspect ratio
            scaled = self.background.scaled(
                self.size(), 
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled)
        super().resizeEvent(event)

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
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
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
                font-family: 'Poppins';
                min-width: 80px;
                transition: all 0.2s ease;
            }
            QMessageBox QPushButton:hover {
                background-color: #FF1493;
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
                background-color: #FFFFFF;
                font-family: 'Poppins';
                border-radius: 12px;
                border: 1px solid #FFB6C1;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
                font-weight: normal;
            }
            QLineEdit {
                padding: 12px;
                border: 1px solid #FFB6C1;
                border-radius: 8px;
                font-size: 14px;
                background-color: #FFFFFF;
                color: #333333;
                font-family: 'Poppins';
            }
            QLineEdit:focus {
                border: 1px solid #FF69B4;
                box-shadow: 0 0 0 2px rgba(255, 105, 180, 0.3);
            }
            QPushButton {
                background-color: #FF69B4;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                font-family: 'Poppins';
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF1493;
            }
            QTabWidget::pane {
                border: none;
                background-color: #FFF0F5;
                border-radius: 8px;
                margin-top: 10px;
            }
            QTabBar::tab {
                padding: 12px 24px;
                background: #FFB6C1;
                border: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                color: #FFFFFF;
                font-family: 'Poppins';
            }
            QTabBar::tab:selected {
                background: #FF69B4;
                color: white;
            }
            QTabBar::tab:hover {
                background: #FF82AB;
            }
        """)

        # Setup sounds
        self.click_sound = QSoundEffect()
        self.click_sound.setSource(QUrl.fromLocalFile(resource_path("assets/sounds/click.wav")))
        self.click_sound.setVolume(0.3)
        
        self.success_sound = QSoundEffect()
        self.success_sound.setSource(QUrl.fromLocalFile(resource_path("assets/sounds/success.mp3")))
        self.success_sound.setVolume(0.3)
        
        self.error_sound = QSoundEffect()
        self.error_sound.setSource(QUrl.fromLocalFile(resource_path("assets/sounds/error.mp3")))
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
            color: #FF69B4;
            margin-bottom: 10px;
            font-family: 'Poppins';
        """)
        
        # Add a subtitle
        subtitle = QLabel("Cultivate mindful thinking")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 16px;
            color: #888888;
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
            background-color: #FF69B4;
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
            background-color: #FFB6C1;
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
            
            # Fixed parent handling
            parent = self.parent()
            if parent and hasattr(parent, 'user_logged_in'):
                try:
                    parent.user_logged_in(self.local_id, self.id_token)
                    self.success_sound.play()
                except Exception as e:
                    print(f"Error notifying parent: {e}")
            
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
                self.dot1.setStyleSheet("background-color: #FF69B4; border-radius: 4px;")
                
                self.dot2 = QWidget(self.loading_dots)
                self.dot2.setFixedSize(8, 8)
                self.dot2.setStyleSheet("background-color: #FF69B4; border-radius: 4px;")
                
                self.dot3 = QWidget(self.loading_dots)
                self.dot3.setFixedSize(8, 8)
                self.dot3.setStyleSheet("background-color: #FF69B4; border-radius: 4px;")
                
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

class FirebaseWorker(QThread):
    data_loaded = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    operation_complete = pyqtSignal(str, bool)

    def __init__(self, operation, user_id=None, id_token=None, data=None, parent=None):
        super().__init__(parent)
        self.operation = operation
        self.user_id = user_id
        self.id_token = id_token
        self.data = data

    def run(self):
        try:
            if self.operation == "load_journal":
                self.load_journal()
            elif self.operation == "save_journal":
                self.save_journal()
            elif self.operation == "delete_journal":
                self.delete_journal()
            elif self.operation == "update_score":
                self.update_score()
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.quit()

    # ... rest of your FirebaseWorker methods ...

# When using the worker:


    def load_journal(self):
        try:
            url = f"{FIREBASE_DB_URL}/users/{self.user_id}/journal.json?auth={self.id_token}"
            response = requests.get(url)
            if response.status_code == 200:
                journal_data = response.json() or {}
                if isinstance(journal_data, list) :
                    temp = {}
                    for i , j in enumerate(journal_data):
                        temp[f'{i}'] = j
                    journal_data = temp
                    del temp
                self.data_loaded.emit(journal_data)
            else:
                self.error_occurred.emit("Failed to load journal")
        except Exception as e:
            self.error_occurred.emit(str(e))

    def save_journal(self):
        try:
            url = f"{FIREBASE_DB_URL}/users/{self.user_id}/journal.json?auth={self.id_token}"
            response = requests.post(url, json=self.data)
            if type(response) == list:
                temp = {}
                for i , j in enumerate(response):
                    response[f'{i}'] = j
                response = temp
            if response.status_code == 200:
                self.operation_complete.emit("Journal entry saved", True)
            else:
                self.error_occurred.emit("Failed to save journal entry")
        except Exception as e:
            self.error_occurred.emit(str(e))

    def delete_journal(self):
        try:
            url = f"{FIREBASE_DB_URL}/users/{self.user_id}/journal/{self.data}.json?auth={self.id_token}"

            response = requests.delete(url)
            if response.status_code == 200:
                self.operation_complete.emit("Journal entry deleted", True)
            else:
                self.error_occurred.emit("Failed to delete journal entry")
        except Exception as e:
            self.error_occurred.emit(str(e))

    # def update_score(self):
    #     try:
    #         url = f"{FIREBASE_DB_URL}/users/{self.user_id}.json?auth={self.id_token}"
    #         response = requests.patch(url, json=self.data)
    #         if response.status_code == 200:
    #             self.operation_complete.emit("Score updated", True)
    #         else:
    #             self.error_occurred.emit("Failed to update score")
    #     except Exception as e:
    #         self.error_occurred.emit(str(e))
    def update_score(self):
        try:
            # Step 1: Get current score from Firebase
            get_url = f"{FIREBASE_DB_URL}/users/{self.user_id}.json?auth={self.id_token}"
            get_response = requests.get(get_url)
            if get_response.status_code != 200:
                self.error_occurred.emit("Failed to fetch current score")
                return

            user_data = get_response.json()
            current_score = user_data.get("score", 0)

            # Step 2: Get the new score from self.data
            new_score = self.data.get("score", 0)

            # Step 3: Compare and update only if higher
            if new_score > current_score:
                patch_response = requests.patch(get_url, json={"score": new_score})
                if patch_response.status_code == 200:
                    self.operation_complete.emit("Score updated", True)
                else:
                    self.error_occurred.emit("Failed to update score")
            else:
                self.operation_complete.emit("New score not higher. No update.", False)

        except Exception as e:
            self.error_occurred.emit(str(e))


class ThoughtGame(QMainWindow):
    def __init__(self):
        super().__init__()
        load_fonts()
        
        # Setup sound effects
        self.click_sound = QSoundEffect()
        self.click_sound.setSource(QUrl.fromLocalFile(resource_path("assets/sounds/click.wav")))
        self.click_sound.setVolume(0.3)
        
        self.correct_sound = QSoundEffect()
        self.correct_sound.setSource(QUrl.fromLocalFile(resource_path("assets/sounds/correct.wav")))
        self.correct_sound.setVolume(0.3)
        
        self.wrong_sound = QSoundEffect()
        self.wrong_sound.setSource(QUrl.fromLocalFile(resource_path("assets/sounds/wrong.wav")))
        self.wrong_sound.setVolume(0.3)
        
        self.page_turn_sound = QSoundEffect()
        self.page_turn_sound.setSource(QUrl.fromLocalFile(resource_path("assets/sounds/page-flip.mp3")))
        self.page_turn_sound.setVolume(0.3)
        
        self.notification_sound = QSoundEffect()
        self.notification_sound.setSource(QUrl.fromLocalFile(resource_path("assets/sounds/notification.wav")))
        self.notification_sound.setVolume(0.3)
        
        # Background music
        self.audio_output = QAudioOutput()
        self.background_music = QMediaPlayer()
        self.background_music.setAudioOutput(self.audio_output)
        self.background_music.setSource(QUrl.fromLocalFile(resource_path("assets/sounds/background.mp3")))
        self.audio_output.setVolume(0.2)
        self.background_music.setLoops(QMediaPlayer.Loops.Infinite)

        # Initialize Firebase
        self.initialize_firebase()
        self.journal_entries = []
        self.setWindowTitle("Thought Bubble - Mental Well-being Game")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
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
        # self.create_main_menu()
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
            cred = credentials.Certificate(resource_path("assets/csgame-f1969-firebase-adminsdk-fbsvc-a042dd397c.json"))
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
        
        # Main layout with no margins
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. First add the background widget
        # background = BackgroundWidget(page)
        # main_layout.addWidget(background)
        
        # 2. Create a container for the overlay content
        overlay = QWidget(page)
        overlay.setStyleSheet("background-color: rgba(255, 255, 255, 0.8);")
        
        # Use a vertical layout for the overlay content
        overlay_layout = QVBoxLayout(overlay)
        overlay_layout.setContentsMargins(40, 40, 40, 40)  # Add some padding
        
        # Add your content to the overlay
        title = QLabel("Thought Bubble")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 48px;
            font-weight: bold;
            color: #FF69B4;
            margin-bottom: 10px;
            font-family: 'Poppins';
        """)
        
        subtitle = QLabel("Cultivate mindful thinking")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 18px;
            color: #888888;
            margin-bottom: 40px;
            font-family: 'Poppins';
        """)
        
        login_btn = QPushButton("Login / Register")
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF69B4;
                color: white;
                border: none;
                padding: 16px;
                border-radius: 12px;
                font-size: 18px;
                font-weight: bold;
                min-width: 240px;
                font-family: 'Poppins';
            }
            QPushButton:hover {
                background-color: #FF1493;
            }
        """)
        login_btn.clicked.connect(self.show_login_dialog)
        
        # Center the button
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.addStretch()
        btn_layout.addWidget(login_btn)
        btn_layout.addStretch()
        
        footer = QLabel("© 2025 Thought Bubble. All rights reserved.")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("""
            font-size: 12px;
            color: #888888;
            margin-top: 20px;
            font-family: 'Poppins';
        """)
        
        # Add widgets to overlay layout
        overlay_layout.addWidget(title)
        overlay_layout.addWidget(subtitle)
        overlay_layout.addStretch()
        overlay_layout.addWidget(btn_container)
        overlay_layout.addStretch()
        overlay_layout.addWidget(footer)
        
        # 3. Add the overlay to main layout (on top of background)
        main_layout.addWidget(overlay)
        
        # Make sure overlay expands to fill available space
        main_layout.setStretch(1, 1)
        
        self.stacked_widget.addWidget(page)
        return page
    
    
    def show_login_dialog(self):
        self.play_click_sound()
        dialog = LoginDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.user = {
                'localId': dialog.local_id,
                'idToken': dialog.id_token
            }
            self.user_logged_in(dialog.local_id, dialog.id_token)
    
    def create_main_menu(self):
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        # Background
        background = BackgroundWidget()
        layout.addWidget(background)
        
        # Overlay widget for content
        overlay = QWidget()
        overlay.setStyleSheet("background-color: rgba(255, 255, 255, 0.9); border-radius: 20px;")
        overlay_layout = QVBoxLayout()
        overlay_layout.setContentsMargins(30, 30, 30, 30)
        overlay_layout.setSpacing(30)
        
        # Title
        title = QLabel("Thought Bubble")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #FF69B4;
            margin-bottom: 10px;
            font-family: 'Poppins';
        """)
        
        # Welcome message
        self.welcome_label = QLabel()
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_label.setStyleSheet("""
            font-size: 18px;
            color: #888888;
            margin-bottom: 40px;
            font-family: 'Poppins';
        """)
        
        # Button styles
        btn_style = """
            QPushButton {
                background-color: #FF69B4;
                color: white;
                border: none;
                padding: 16px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                min-width: 240px;
                font-family: 'Poppins';
            }
            QPushButton:hover {
                background-color: #FF1493;
            }
        """
        
        play_btn = QPushButton("Play Game")
        play_btn.setStyleSheet(btn_style)
        play_btn.clicked.connect(self.start_game)
        
        journal_btn = QPushButton("My Journal")
        journal_btn.setStyleSheet(btn_style.replace("#FF69B4", "#FFB6C1"))
        journal_btn.clicked.connect(lambda: self.switch_page(2))
        
        leaderboard_btn = QPushButton("Leaderboard")
        leaderboard_btn.setStyleSheet(btn_style.replace("#FF69B4", "#FF82AB"))
        leaderboard_btn.clicked.connect(lambda: self.show_leaderboard())
        
        settings_btn = QPushButton("Settings")
        settings_btn.setStyleSheet(btn_style.replace("#FF69B4", "#FFC0CB"))
        settings_btn.clicked.connect(lambda: self.switch_page(3))
        
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
            admin_btn.setStyleSheet(btn_style.replace("#FF69B4", "#DB7093"))
            admin_btn.clicked.connect(lambda: self.switch_page(5))
            btn_layout.addWidget(admin_btn)
        
        btn_container.setLayout(btn_layout)
        
        # Bottom buttons
        bottom_btn_layout = QHBoxLayout()
        
        # logout_btn = QPushButton("Logout")
        # logout_btn.setStyleSheet("""
        #     QPushButton {
        #         background-color: #FF69B4;
        #         color: white;
        #         border: none;
        #         padding: 12px;
        #         border-radius: 8px;
        #         font-size: 14px;
        #         font-family: 'Poppins';
        #     }
        #     QPushButton:hover {
        #         background-color: #FF1493;
        #     }
        # """)
        # logout_btn.clicked.connect(self.logout)
        
        quit_btn = QPushButton("Quit")
        quit_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFC0CB;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                font-family: 'Poppins';
            }
            QPushButton:hover {
                background-color: #FFB6C1;
            }
        """)
        quit_btn.clicked.connect(self.close)
        
        bottom_btn_layout.addStretch()
        # bottom_btn_layout.addWidget(logout_btn)
        bottom_btn_layout.addWidget(quit_btn)
        
        overlay_layout.addWidget(title)
        overlay_layout.addWidget(self.welcome_label)
        overlay_layout.addStretch()
        overlay_layout.addWidget(btn_container)
        overlay_layout.addStretch()
        overlay_layout.addLayout(bottom_btn_layout)
        
        overlay.setLayout(overlay_layout)
        layout.addWidget(overlay)
        
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
        opacity_effect_out = QGraphicsOpacityEffect(current_widget)
        current_widget.setGraphicsEffect(opacity_effect_out)

        # Fade out animation for the current widget
        fade_out = QPropertyAnimation(opacity_effect_out, b"opacity")
        fade_out.setDuration(200)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.OutQuad)

        # Create opacity effect for the *next* widget
        opacity_effect_in = QGraphicsOpacityEffect(next_widget)
        next_widget.setGraphicsEffect(opacity_effect_in)

        # Fade in animation for the next widget (starts from invisible)
        fade_in = QPropertyAnimation(opacity_effect_in, b"opacity")
        fade_in.setDuration(200)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.InQuad)

        # Connect animations
        fade_out.finished.connect(lambda: self._perform_switch_and_fade_in(
            self.stacked_widget, index, current_widget, next_widget, 
            opacity_effect_out, opacity_effect_in, fade_in))

        # Store references
        self._current_fade_out_animation = fade_out
        self._current_fade_in_animation = fade_in
        self._current_opacity_effect_out = opacity_effect_out
        self._current_opacity_effect_in = opacity_effect_in

        fade_out.start()

    def _perform_switch_and_fade_in(self, stacked_widget, new_index, old_widget, new_widget,
                                    old_effect, new_effect, fade_in_animation):
        # Clean up the effect on the old widget first
        if old_widget and old_effect:
            old_widget.setGraphicsEffect(None)

        # Perform the actual page switch
        stacked_widget.setCurrentIndex(new_index)

        # Start the fade-in animation for the new widget
        fade_in_animation.start()

        # Once the fade-in animation completes, remove its effect for performance
        fade_in_animation.finished.connect(lambda: new_widget.setGraphicsEffect(None))

    def create_game_page(self):
        self.game_page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # # Background
        # background = BackgroundWidget()
        # layout.addWidget(background)
        
        # Overlay widget for content
        overlay = QWidget()
        overlay.setStyleSheet("background-color: transparent; border-radius: 20px;")
        overlay_layout = QVBoxLayout()
        overlay_layout.setContentsMargins(20, 20, 20, 20)
        overlay_layout.setSpacing(20)
        
        # Top bar with score, difficulty and timer
        top_bar = QWidget()
        top_bar.setStyleSheet("""
            background-color: #FFF0F5;
            border-radius: 12px;
            padding: 16px;
            border: 1px solid #FFB6C1;
        """)
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(10, 5, 10, 5)
        
        self.score_label = QLabel(f"Score: {self.score}")
        self.score_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #FF69B4;
            font-family: 'Poppins';
        """)
        
        self.difficulty_label = QLabel(f"Difficulty: {self.current_difficulty}")
        self.difficulty_label.setStyleSheet("""
            font-size: 16px;
            color: #FF82AB;
            font-family: 'Poppins';
        """)
        
        self.timer_label = QLabel("Time: --")
        self.timer_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #FF69B4;
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
            background-color: #FFF0F5;
            border-radius: 16px;
            border: 1px solid #FFB6C1;
            min-height: 120px;
            color: #333333;
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
            background-color: #FFF0F5;
            border-radius: 16px;
            border: 1px solid #FF69B4;
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
            color: #333333;
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
                background-color: #FF82AB;
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
                font-family: 'Poppins';
            }
            QPushButton:hover {
                background-color: #FF69B4;
            }
        """)
        accept_btn.clicked.connect(lambda: self.evaluate_thought("accept"))
        
        reject_btn = QPushButton("✘ Reject Thought")
        reject_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 16px 32px;
                background-color: #FFB6C1;
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
                font-family: 'Poppins';
            }
            QPushButton:hover {
                background-color: #FF82AB;
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
                background-color: #FF69B4;
                color: white;
                border: none;
                border-radius: 8px;
                font-family: 'Poppins';
            }
            QPushButton:hover {
                background-color: #FF1493;
            }
        """)
        menu_btn.clicked.connect(lambda: self.switch_page(6))
        
        journal_btn = QPushButton("📝 Add to Journal")
        journal_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 12px 24px;
                background-color: #FFB6C1;
                color: white;
                border: none;
                border-radius: 8px;
                font-family: 'Poppins';
            }
            QPushButton:hover {
                background-color: #FF82AB;
            }
        """)
        journal_btn.clicked.connect(self.add_current_to_journal)
        
        nav_layout.addWidget(menu_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(journal_btn)
        
        # Add to main layout
        overlay_layout.addWidget(top_bar)
        overlay_layout.addWidget(self.scenario_label)
        overlay_layout.addWidget(self.character_label, 0, Qt.AlignmentFlag.AlignHCenter)
        overlay_layout.addWidget(self.thought_bubble)
        overlay_layout.addLayout(button_layout)
        overlay_layout.addLayout(nav_layout)
        
        overlay.setLayout(overlay_layout)
        layout.addWidget(overlay)
        
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
                    color: #FF69B4;
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
                color: #FF69B4;
            """)

    def create_journal_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Background
        background = BackgroundWidget()
        layout.addWidget(background)
        
        # Overlay widget for content
        overlay = QWidget()
        overlay.setStyleSheet("background-color: rgba(255, 255, 255, 0.9); border-radius: 20px;")
        overlay_layout = QVBoxLayout()
        overlay_layout.setContentsMargins(30, 30, 30, 30)
        overlay_layout.setSpacing(20)
        
        title = QLabel("My Journal")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #FF69B4;
            margin-bottom: 20px;
            font-family: 'Poppins';
        """)
        
        # Journal list with scroll area
        self.journal_list = QListWidget()
        self.journal_list.setStyleSheet("""
            QListWidget {
                background-color: #FFF0F5;
                border: 1px solid #FFB6C1;
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
                font-family: 'Poppins';
                color: #333333;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #FFB6C1;
                font-family: 'Poppins';
            }
            QListWidget::item:hover {
                background-color: rgba(255, 182, 193, 0.3);
            }
            QListWidget::item:selected {
                background-color: #FF69B4;
                color: white;
            }
        """)
        self.journal_list.itemDoubleClicked.connect(self.view_journal_entry)
        
        # Journal entry view
        self.journal_text = QTextEdit()
        self.journal_text.setReadOnly(True)
        self.journal_text.setStyleSheet("""
            QTextEdit {
                background-color: #FFF0F5;
                border: 1px solid #FFB6C1;
                border-radius: 12px;
                padding: 16px;
                font-size: 14px;
                font-family: 'Poppins';
                color: #333333;
            }
        """)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        back_btn = QPushButton("Back to Menu")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF69B4;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                font-family: 'Poppins';
            }
            QPushButton:hover {
                background-color: #FF1493;
            }
        """)
        back_btn.clicked.connect(lambda: self.switch_page(6))
        
        delete_btn = QPushButton("Delete Entry")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF82AB;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                font-family: 'Poppins';
            }
            QPushButton:hover {
                background-color: #FF69B4;
            }
        """)
        delete_btn.clicked.connect(self.delete_journal_entry)
        
        button_layout.addWidget(back_btn)
        button_layout.addStretch()
        button_layout.addWidget(delete_btn)
        
        overlay_layout.addWidget(title)
        overlay_layout.addWidget(self.journal_list, 1)
        overlay_layout.addWidget(self.journal_text, 1)
        overlay_layout.addLayout(button_layout)
        
        overlay.setLayout(overlay_layout)
        layout.addWidget(overlay)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)
        
        self.update_journal_list()

    def create_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Background
        background = BackgroundWidget()
        layout.addWidget(background)
        
        # Overlay widget for content
        overlay = QWidget()
        overlay.setStyleSheet("background-color: rgba(255, 255, 255, 0.9); border-radius: 20px;")
        overlay_layout = QVBoxLayout()
        overlay_layout.setContentsMargins(40, 40, 40, 40)
        overlay_layout.setSpacing(30)
        
        title = QLabel("Settings")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #FF69B4;
            margin-bottom: 20px;
            font-family: 'Poppins';
        """)
        
        # Difficulty selection
        difficulty_group = QWidget()
        difficulty_group.setStyleSheet("""
            background-color: #FFF0F5;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #FFB6C1;
        """)
        difficulty_layout = QHBoxLayout()
        difficulty_layout.setContentsMargins(0, 0, 0, 0)
        
        difficulty_label = QLabel("Difficulty:")
        difficulty_label.setStyleSheet("""
            font-size: 16px;
            color: #333333;
            font-family: 'Poppins';
        """)
        
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Easy", "Medium", "Hard"])
        self.difficulty_combo.setCurrentText(self.current_difficulty)
        self.difficulty_combo.setStyleSheet("""
            QComboBox {
                padding: 12px;
                border: 1px solid #FFB6C1;
                border-radius: 8px;
                min-width: 200px;
                background-color: #FFF0F5;
                color: #333333;
                font-family: 'Poppins';
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #FFF0F5;
                border: 1px solid #FFB6C1;
                color: #333333;
                selection-background-color: #FF69B4;
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
            background-color: #FFF0F5;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #FFB6C1;
        """)
        time_pressure_layout = QHBoxLayout()
        time_pressure_layout.setContentsMargins(0, 0, 0, 0)
        
        time_pressure_label = QLabel("Time Pressure Mode:")
        time_pressure_label.setStyleSheet("""
            font-size: 16px;
            color: #333333;
            font-family: 'Poppins';
        """)
        
        self.time_pressure_toggle = QSlider(Qt.Orientation.Horizontal)
        self.time_pressure_toggle.setMinimum(0)
        self.time_pressure_toggle.setMaximum(1)
        self.time_pressure_toggle.setValue(1 if self.time_pressure_mode else 0)
        self.time_pressure_toggle.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #FFB6C1;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 24px;
                height: 24px;
                background: #FF69B4;
                border-radius: 12px;
            }
            QSlider::sub-page:horizontal {
                background: #FF69B4;
                border-radius: 4px;
            }
        """)
        self.time_pressure_toggle.valueChanged.connect(self.toggle_time_pressure)
        
        self.time_pressure_status = QLabel("On" if self.time_pressure_mode else "Off")
        self.time_pressure_status.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #FF69B4;
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
            background-color: #FFF0F5;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #FFB6C1;
        """)
        time_limit_layout = QHBoxLayout()
        time_limit_layout.setContentsMargins(0, 0, 0, 0)
        
        time_limit_label = QLabel("Time Limit (seconds):")
        time_limit_label.setStyleSheet("""
            font-size: 16px;
            color: #333333;
            font-family: 'Poppins';
        """)
        
        self.time_limit_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_limit_slider.setMinimum(10)
        self.time_limit_slider.setMaximum(60)
        self.time_limit_slider.setValue(self.time_left)
        self.time_limit_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #FFB6C1;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 24px;
                height: 24px;
                background: #FF82AB;
                border-radius: 12px;
            }
            QSlider::sub-page:horizontal {
                background: #FF82AB;
                border-radius: 4px;
            }
        """)
        self.time_limit_slider.valueChanged.connect(self.change_time_limit)
        
        self.time_limit_value = QLabel(str(self.time_left))
        self.time_limit_value.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #FF82AB;
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
            background-color: #FFF0F5;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #FFB6C1;
        """)
        music_layout = QHBoxLayout()
        music_layout.setContentsMargins(0, 0, 0, 0)
        
        music_label = QLabel("Music Volume:")
        music_label.setStyleSheet("""
            font-size: 16px;
            color: #333333;
            font-family: 'Poppins';
        """)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(20)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #FFB6C1;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 24px;
                height: 24px;
                background: #FFB6C1;
                border-radius: 12px;
            }
            QSlider::sub-page:horizontal {
                background: #FFB6C1;
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
                background-color: #FF69B4;
                color: white;
                border: none;
                padding: 16px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Poppins';
            }
            QPushButton:hover {
                background-color: #FF1493;
            }
        """)
        back_btn.clicked.connect(lambda: self.switch_page(6))
        
        overlay_layout.addWidget(title)
        overlay_layout.addWidget(difficulty_group)
        overlay_layout.addWidget(time_pressure_group)
        overlay_layout.addWidget(time_limit_group)
        overlay_layout.addWidget(music_group)
        overlay_layout.addStretch()
        overlay_layout.addWidget(back_btn)
        
        overlay.setLayout(overlay_layout)
        layout.addWidget(overlay)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)
   
    def update_welcome_message(self):
    
        name = self.user['data'].get("name", "Player")
        score = self.user['data'].get("score", 0)
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
            questions_snapshot = self.db.child("questions").get()  # Use your actual token

            if questions_snapshot.each():
                questions_data = []

                for item in questions_snapshot.each():
                    q = item.val()

                    mapped_question = {
                        "Difficulty": q.get("difficulty"),
                        "Scenario": q.get("category"),  # or "statement" if that's more relevant
                        "Thought": q.get("statement"),
                        "label": q.get("type").capitalize(),
                        "Alternative": q.get("alternative")
                    }

                    questions_data.append(mapped_question)

                self.questions = questions_data
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
        try:
            # Load user data
            user_data = self.db.child("users").child(local_id).get(token=id_token).val()
            if user_data:
                self.user = {
                    'localId': local_id,
                    'idToken': id_token,
                    'data': user_data
                }
                self.is_admin = user_data.get("is_admin")
                
                # Update UI based on login
                self.load_journal(id_token)
                
                # Recreate the main menu now that we know the user's admin status
                self.create_main_menu()
                self.update_welcome_message()


                # Switch to main menu
                self.stacked_widget.setCurrentIndex(6)
                # Update last played
                self.db.child("users").child(local_id).update({
                    "last_played": datetime.now().isoformat()
                }, token=id_token)
        except Exception as e:
            print(f"Error in user_logged_in: {e}")
            self.show_error_message("Login Error", "Failed to load user data")
    def create_leaderboard_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Background
        background = BackgroundWidget()
        layout.addWidget(background)
        
        # Overlay widget for content
        overlay = QWidget()
        overlay.setStyleSheet("background-color: rgba(255, 255, 255, 0.9); border-radius: 20px;")
        overlay_layout = QVBoxLayout()
        overlay_layout.setContentsMargins(30, 30, 30, 30)
        overlay_layout.setSpacing(20)
        
        title = QLabel("Leaderboard")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #FF69B4;
            margin-bottom: 20px;
            font-family: 'Poppins';
        """)
        
        self.leaderboard_table = QTableWidget()
        self.leaderboard_table.setColumnCount(5)
        self.leaderboard_table.setHorizontalHeaderLabels(["Rank", "Name", "Score", "Games Played", "Last Played"])
        self.leaderboard_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.leaderboard_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.leaderboard_table.setStyleSheet("""
            QTableView {
                background-color: #FFF0F5;
                border: 1px solid #FFB6C1;
                border-radius: 12px;
                font-family: 'Poppins';
            }
            QHeaderView::section {
                background-color: #FF69B4;
                color: white;
                padding: 12px;
                border: none;
                font-family: 'Poppins';
            }
            QTableView::item {
                padding: 12px;
                border-bottom: 1px solid #FFB6C1;
                color: #333333;
                font-family: 'Poppins';
            }
            QTableView::item:selected {
                background-color: #FF69B4;
                color: white;
            }
        """)
        
        refresh_btn = QPushButton("Refresh Leaderboard")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF82AB;
                color: white;
                border: none;
                padding: 16px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Poppins';
            }
            QPushButton:hover {
                background-color: #FF69B4;
            }
        """)
        refresh_btn.clicked.connect(self.update_leaderboard)
        
        back_btn = QPushButton("Back to Menu")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF69B4;
                color: white;
                border: none;
                padding: 16px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Poppins';
            }
            QPushButton:hover {
                background-color: #FF1493;
            }
        """)
        back_btn.clicked.connect(lambda: self.switch_page(6))
        
        overlay_layout.addWidget(title)
        overlay_layout.addWidget(self.leaderboard_table, 1)
        overlay_layout.addWidget(refresh_btn)
        overlay_layout.addWidget(back_btn)
        
        overlay.setLayout(overlay_layout)
        layout.addWidget(overlay)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)

    def create_admin_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Background
        background = BackgroundWidget()
        layout.addWidget(background)
        
        # Overlay widget for content
        overlay = QWidget()
        overlay.setStyleSheet("background-color: rgba(255, 255, 255, 0.9); border-radius: 20px;")
        overlay_layout = QVBoxLayout()
        overlay_layout.setContentsMargins(30, 30, 30, 30)
        overlay_layout.setSpacing(20)
        
        title = QLabel("Admin Panel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #FF69B4;
            margin-bottom: 20px;
            font-family: 'Poppins';
        """)
        
        self.questions_table = QTableWidget()
        self.questions_table.setColumnCount(6)
        self.questions_table.setHorizontalHeaderLabels(["Scenario", "Thought", "Label", "Difficulty", "Alternative", "Actions"])
        self.questions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.questions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.questions_table.setStyleSheet("""
            QTableView {
                background-color: #FFF0F5;
                border: 1px solid #FFB6C1;
                border-radius: 12px;
                font-family: 'Poppins';
            }
            QHeaderView::section {
                background-color: #DB7093;
                color: white;
                padding: 12px;
                border: none;
                font-family: 'Poppins';
            }
            QTableView::item {
                padding: 12px;
                border-bottom: 1px solid #FFB6C1;
                color: #333333;
                font-family: 'Poppins';
            }
            QTableView::item:selected {
                background-color: #DB7093;
                color: white;
            }
        """)
        
        add_btn = QPushButton("Add New Question")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF82AB;
                color: white;
                border: none;
                padding: 16px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Poppins';
            }
            QPushButton:hover {
                background-color: #FF69B4;
            }
        """)
        add_btn.clicked.connect(self.add_question)
        
        refresh_btn = QPushButton("Refresh Questions")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF69B4;
                color: white;
                border: none;
                padding: 16px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Poppins';
            }
            QPushButton:hover {
                background-color: #FF1493;
            }
        """)
        refresh_btn.clicked.connect(self.load_questions)
        
        back_btn = QPushButton("Back to Menu")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFC0CB;
                color: white;
                border: none;
                padding: 16px;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Poppins';
            }
            QPushButton:hover {
                background-color: #FFB6C1;
            }
        """)
        back_btn.clicked.connect(lambda: self.switch_page(6))
        
        overlay_layout.addWidget(title)
        overlay_layout.addWidget(self.questions_table, 1)
        overlay_layout.addWidget(add_btn)
        overlay_layout.addWidget(refresh_btn)
        overlay_layout.addWidget(back_btn)
        
        overlay.setLayout(overlay_layout)
        layout.addWidget(overlay)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)
    
    def show_leaderboard(self):
        self.play_click_sound()
        self.notification_sound.play()
        self.update_leaderboard()
        self.stacked_widget.setCurrentIndex(4)
    
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
                    color = QColor(255, 240, 245)  # Pink background
                
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
            # Step 1: Get questions from Firebase
            questions_snapshot = self.db.child("questions").get()

            if not questions_snapshot.each():
                raise Exception("No questions found in Firebase.")

            questions_data = []
            self.question_keys = []  # Store question keys (like "q1", "q2", ...) to track Firebase entries

            for item in questions_snapshot.each():
                q = item.val()
                key = item.key()

                # Transform Firebase format to your internal format
                mapped_question = {
                    "Difficulty": q.get("difficulty"),
                    "Scenario": q.get("category"),
                    "Thought": q.get("statement"),
                    "label": q.get("type").capitalize(),
                    "Alternative": q.get("alternative")
                }

                questions_data.append(mapped_question)
                self.question_keys.append(key)

            # Step 2: Populate the QTableWidget
            self.questions_table.setRowCount(len(questions_data))

            for i, question in enumerate(questions_data):
                self.questions_table.setItem(i, 0, QTableWidgetItem(question["Scenario"][:50] + "..." if len(question["Scenario"]) > 50 else question["Scenario"]))
                self.questions_table.setItem(i, 1, QTableWidgetItem(question["Thought"][:50] + "..." if len(question["Thought"]) > 50 else question["Thought"]))
                self.questions_table.setItem(i, 2, QTableWidgetItem(question["label"]))
                self.questions_table.setItem(i, 3, QTableWidgetItem(question["Difficulty"]))
                self.questions_table.setItem(i, 4, QTableWidgetItem(str(question["Alternative"])[:50] + "..." if question["Alternative"] and len(str(question["Alternative"])) > 50 else str(question["Alternative"])))

                # Action buttons
                widget = QWidget()
                layout = QHBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(5)

                edit_btn = QPushButton("Edit")
                edit_btn.setFixedSize(60, 30)
                edit_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FF69B4;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-size: 12px;
                        font-family: 'Poppins';
                    }
                    QPushButton:hover {
                        background-color: #FF1493;
                    }
                """)
                edit_btn.clicked.connect(lambda _, qid=i: self.edit_question_fi(qid))

                delete_btn = QPushButton("Delete")
                delete_btn.setFixedSize(60, 30)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FF82AB;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-size: 12px;
                        font-family: 'Poppins';
                    }
                    QPushButton:hover {
                        background-color: #FF69B4;
                    }
                """)
                delete_btn.clicked.connect(lambda _, qid=i: self.delete_question_from_firebase(qid))

                layout.addWidget(edit_btn)
                layout.addWidget(delete_btn)
                widget.setLayout(layout)

                self.questions_table.setCellWidget(i, 5, widget)

            self.questions = questions_data  # Store for use in other parts (edit, etc.)

        except Exception as e:
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Error")
            msg.setText(f"Failed to load questions: {str(e)}")
            msg.exec()

    def delete_question_from_firebase(self, index):
        try:
            key = self.question_keys[index]
            self.db.child("questions").child(key).remove()

            QMessageBox.information(self, "Deleted", "Question deleted successfully.")
            self.load_questions()  # Reload to refresh table

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to delete question: {str(e)}")


    # def add_question(self):
    #     self.play_click_sound()
    #     dialog = AdminQuestionDialog(self)
    #     if dialog.exec() == QDialog.DialogCode.Accepted:
    #         try:
    #             question_data = dialog.get_question_data()
    #             # In a real app, you would push to Firebase here
    #             # self.db.child("questions").push(question_data)
    #             self.load_questions()
    #             self.load_questions_from_firebase()  # Refresh game questions
    #         except Exception as e:
    #             msg = StyledMessageBox(self)
    #             msg.setIcon(QMessageBox.Icon.Warning)
    #             msg.setWindowTitle("Error")
    #             msg.setText(f"Failed to add question: {str(e)}")
    #             msg.exec()
    def add_question(self):
        self.play_click_sound()
        dialog = AdminQuestionDialog(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                question_data = dialog.get_question_data()

                def convert_to_image_format(data):
                    return {
                        "alternative": data.get("Alternative", ""),
                        "category": data.get("Scenario", ""),
                        "difficulty": data.get("Difficulty", ""),
                        "explanation": data.get("Alternative", ""),
                        "statement": data.get("Thought", ""),
                        "type": data.get("label", "").lower(),
                    }

                formatted_data = convert_to_image_format(question_data)

                # 1. Get existing questions
                existing_data = self.db.child("questions").get().val() or {}

                # 2. Find max existing index (e.g., from keys like 'q0', 'q1', ...)
                existing_indices = [
                    int(key[1:]) for key in existing_data.keys() if key.startswith("q") and key[1:].isdigit()
                ]
                next_index = max(existing_indices) + 1 if existing_indices else 0
                new_key = f"q{next_index}"

                # 3. Add new question at next 'qN' key
                self.db.child("questions").child(new_key).set(formatted_data)

                # 4. Refresh UI
                self.load_questions()
                self.load_questions_from_firebase()

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
    def edit_question_fi(self, qid):
        def convert_to_image_format(data):
            """
            Converts a dictionary into a format that matches the structure shown in the image.

            Args:
                data (dict): The input dictionary with keys like 'Difficulty', 'Scenario',
                            'Thought', 'label', and 'Alternative'.

            Returns:
                dict: A dictionary formatted to match the image structure.
            """
            return {
                "alternative": data.get("Alternative", ""),
                "category": data.get("Scenario", ""),  # Mapping 'Scenario' to 'category'
                "difficulty": data.get("Difficulty", ""),
                "explanation": data.get("Alternative", ""), # Default explanation
                "statement": data.get("Thought", ""),  # Mapping 'Thought' to 'statement'
                "type": data.get("label", "").lower(), # Ensure 'positive' or 'negative'
            }


# Convert the data

        self.play_click_sound()
        try:

            question_data = self.questions[qid]
            dialog = AdminQuestionDialog(self, question_data)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_data = dialog.get_question_data()

                # Fix: use Firebase key instead of index
                firebase_key = self.question_keys[qid]
                updated_data = convert_to_image_format(updated_data)
                self.db.child("questions").child(firebase_key).update(updated_data)

                self.load_questions()                # Refresh table
                self.load_questions_from_firebase()  # Refresh game logic
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
            # Create a worker thread to handle the Firebase operation
            worker = FirebaseWorker(
                operation="update_score",
                user_id=self.user['localId'],
                id_token=self.user['idToken'],
                data={
                    "score": self.score,
                    "games_played": self.user['data'].get("games_played", 0) + 1,
                    "last_played": datetime.now().isoformat()
                }
            )
            
            # Connect signals
            worker.operation_complete.connect(self.handle_operation_complete)
            worker.error_occurred.connect(self.handle_operation_error)
            
            # Start the worker
            worker.run()
    
    def handle_operation_complete(self, message, success):
        if success:
            print(message)
    
    def handle_operation_error(self, error_message):
        msg = StyledMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Error")
        msg.setText(error_message)
        msg.exec()
    
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
            self.timer_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FF69B4;")
            self.game_timer.start(1000)
        else:
            self.timer_label.setText("Time: --")
        
        self.stacked_widget.setCurrentIndex(1)
    
    def evaluate_thought(self, action):
        if not hasattr(self, 'current_questions') or self.current_question_index >= len(self.current_questions):
            return
            
        question = self.current_questions[self.current_question_index-1]
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
                color: #FF1493;
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
            self.switch_page(6)
    
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
        
        if self.user:
            # Create a worker thread to handle the Firebase operation
            worker = FirebaseWorker(
                operation="save_journal",
                user_id=self.user['localId'],
                id_token=self.user['idToken'],
                data=entry
            )
            
            # Connect signals
            worker.operation_complete.connect(self.handle_journal_saved)
            worker.error_occurred.connect(self.handle_operation_error)
            
            # Start the worker
            worker.run()
    
    def handle_journal_saved(self, message, success):
        if success:
            self.notification_sound.play()
            msg = StyledMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Success")
            msg.setText(message)
            msg.exec()
            
            # Reload the journal
            self.load_journal(self.user['idToken'])
    
    # def load_journal(self, id_token):
    #     if self.user:
    #         # Create a worker thread to handle the Firebase operation
    #         worker = FirebaseWorker(
    #             operation="load_journal",
    #             user_id=self.user['localId'],
    #             id_token=id_token
    #         )
    #         print('heresssd')
            
    #         # Connect signals
    #         worker.data_loaded.connect(self.handle_journal_loaded)
    #         worker.error_occurred.connect(self.handle_operation_error)
    #         print('heresssd2')

            
    #         # Start the worker
    #         worker.run()

    def load_journal(self, id_token):
        if self.user:
            self.worker = FirebaseWorker(
                operation="load_journal",
                user_id=self.user['localId'],
                id_token=id_token,
                parent=self
            )
            self.worker.data_loaded.connect(self.handle_journal_loaded)
            self.worker.error_occurred.connect(self.handle_operation_error)
            self.worker.finished.connect(self.worker.deleteLater)
            self.worker.run()

    def handle_journal_loaded(self, journal_data):
        self.journal_entries = journal_data or {}
        self.update_journal_list()
    
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
            # Create a worker thread to handle the Firebase operation
            worker = FirebaseWorker(
                operation="delete_journal",
                user_id=self.user['localId'],
                id_token=self.user['idToken'],
                data=entry_id
            )
            
            # Connect signals
            worker.operation_complete.connect(self.handle_journal_deleted)
            worker.error_occurred.connect(self.handle_operation_error)
            
            # Start the worker
            worker.run()
    
    def handle_journal_deleted(self, message, success):
        if success:
            self.notification_sound.play()
            
            # Remove from local data
            current_item = self.journal_list.currentItem()
            if current_item:
                entry_id = current_item.data(Qt.ItemDataRole.UserRole)
                self.journal_entries.pop(entry_id, None)
                
            # Update UI
            self.update_journal_list()
            self.journal_text.clear()

class AdminQuestionDialog(QDialog):
    def __init__(self, parent=None, question_data=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Question" if question_data else "Add Question")
        self.setModal(True)
        self.setFixedSize(600, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                font-family: 'Poppins';
                border-radius: 12px;
                border: 1px solid #FFB6C1;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
                font-weight: normal;
            }
            QLineEdit, QTextEdit, QComboBox {
                padding: 12px;
                border: 1px solid #FFB6C1;
                border-radius: 8px;
                font-size: 14px;
                background-color: #FFFFFF;
                color: #333333;
                font-family: 'Poppins';
            }
            QPushButton {
                background-color: #FF69B4;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                font-size: 14px;
                font-family: 'Poppins';
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF1493;
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
            "Alternative": self.alternative_edit.toPlainText() if self.label_combo.currentText() == "Negative" else ""
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