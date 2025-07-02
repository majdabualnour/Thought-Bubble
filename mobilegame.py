from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.switch import Switch
from kivy.uix.image import Image
# from kivy.uix.listview import ListView, ListItemButton
# from kivy.adapters.listadapter import ListAdapter
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.graphics import Color, Rectangle
from kivy.uix.modalview import ModalView
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior

import json
import requests
from datetime import datetime
import random

# Firebase Configuration
FIREBASE_API_KEY = "AIzaSyBslVrw8gUYRkjpGHKWeftbvDp0-oBa9w0"
FIREBASE_DB_URL = "https://csgame-f1969-default-rtdb.firebaseio.com"

class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior,
                                RecycleBoxLayout):
    pass

class SelectableLabel(RecycleDataViewBehavior, Label):
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        return super(SelectableLabel, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if super(SelectableLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        self.selected = is_selected

class RV(RecycleView):
    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)
        self.data = []

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=40, spacing=20)
        
        # Title
        title = Label(text='Thought Bubble', font_size=36, bold=True, color=(1, 0.41, 0.71, 1))
        subtitle = Label(text='Cultivate mindful thinking', font_size=18, color=(0.53, 0.53, 0.53, 1))
        
        # Tabs
        self.tabs = TabbedPanel(do_default_tab=False, size_hint=(1, 0.8))
        
        # Login Tab
        login_tab = TabbedPanelItem(text='Login')
        login_layout = BoxLayout(orientation='vertical', spacing=20, padding=20)
        
        self.login_email = TextInput(hint_text='Email', multiline=False)
        self.login_password = TextInput(hint_text='Password', password=True, multiline=False)
        login_btn = Button(text='Login', size_hint_y=None, height=50)
        login_btn.bind(on_press=self.login)
        
        login_layout.add_widget(self.login_email)
        login_layout.add_widget(self.login_password)
        login_layout.add_widget(login_btn)
        login_tab.content = login_layout
        self.tabs.add_widget(login_tab)
        
        # Register Tab
        register_tab = TabbedPanelItem(text='Register')
        register_layout = BoxLayout(orientation='vertical', spacing=20, padding=20)
        
        self.register_name = TextInput(hint_text='Full Name', multiline=False)
        self.register_email = TextInput(hint_text='Email', multiline=False)
        self.register_password = TextInput(hint_text='Password (min 6 chars)', password=True, multiline=False)
        register_btn = Button(text='Register', size_hint_y=None, height=50)
        register_btn.bind(on_press=self.register)
        
        register_layout.add_widget(self.register_name)
        register_layout.add_widget(self.register_email)
        register_layout.add_widget(self.register_password)
        register_layout.add_widget(register_btn)
        register_tab.content = register_layout
        self.tabs.add_widget(register_tab)
        
        layout.add_widget(title)
        layout.add_widget(subtitle)
        layout.add_widget(self.tabs)
        
        self.add_widget(layout)
    
    def login(self, instance):
        email = self.login_email.text.strip()
        password = self.login_password.text.strip()
        
        if not email or not password:
            self.show_error("Please enter both email and password")
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
            
            # Login successful
            self.manager.get_screen('main').user_logged_in(data["localId"], data["idToken"])
            self.manager.current = 'main'
            
        except Exception as e:
            self.show_error(str(e))
    
    def register(self, instance):
        email = self.register_email.text.strip()
        password = self.register_password.text.strip()
        name = self.register_name.text.strip()
        
        if not email or not password or not name:
            self.show_error("Please fill all fields")
            return
        
        if len(password) < 6:
            self.show_error("Password must be at least 6 characters")
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
            
            # Registration successful, switch to login tab
            self.tabs.switch_to(self.tabs.tab_list[0])
            self.register_email.text = ""
            self.register_password.text = ""
            self.register_name.text = ""
            
            self.show_message("Registration successful! Please login.")
            
        except Exception as e:
            self.show_error(str(e))
    
    def show_error(self, message):
        popup = Popup(title='Error', content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()
    
    def show_message(self, message):
        popup = Popup(title='Success', content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()

class MainScreen(Screen):
    user_id = StringProperty("")
    id_token = StringProperty("")
    is_admin = BooleanProperty(False)
    user_data = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # Title
        title = Label(text='Thought Bubble', font_size=36, bold=True, color=(1, 0.41, 0.71, 1))
        self.welcome_label = Label(text='Welcome back, Player!', font_size=18, color=(0.53, 0.53, 0.53, 1))
        
        # Buttons
        btn_layout = BoxLayout(orientation='vertical', spacing=15, size_hint_y=0.6)
        
        play_btn = Button(text='Play Game', background_color=(1, 0.41, 0.71, 1))
        play_btn.bind(on_press=self.start_game)
        
        journal_btn = Button(text='My Journal', background_color=(1, 0.71, 0.76, 1))
        journal_btn.bind(on_press=lambda x: self.manager.current == 'journal' or self.show_journal())
        
        leaderboard_btn = Button(text='Leaderboard', background_color=(1, 0.51, 0.67, 1))
        leaderboard_btn.bind(on_press=lambda x: self.manager.current == 'leaderboard' or self.show_leaderboard())
        
        settings_btn = Button(text='Settings', background_color=(1, 0.75, 0.8, 1))
        settings_btn.bind(on_press=lambda x: self.manager.current == 'settings' or self.manager.current == 'settings')
        
        self.admin_btn = Button(text='Admin Panel', background_color=(0.86, 0.44, 0.58, 1))
        self.admin_btn.bind(on_press=lambda x: self.manager.current == 'admin' or self.manager.current == 'admin')
        self.admin_btn.opacity = 0
        
        logout_btn = Button(text='Logout', size_hint_y=None, height=50)
        logout_btn.bind(on_press=self.logout)
        
        btn_layout.add_widget(play_btn)
        btn_layout.add_widget(journal_btn)
        btn_layout.add_widget(leaderboard_btn)
        btn_layout.add_widget(settings_btn)
        btn_layout.add_widget(self.admin_btn)
        btn_layout.add_widget(logout_btn)
        
        layout.add_widget(title)
        layout.add_widget(self.welcome_label)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
    
    def user_logged_in(self, user_id, id_token):
        self.user_id = user_id
        self.id_token = id_token
        
        # Load user data
        try:
            url = f"{FIREBASE_DB_URL}/users/{user_id}.json?auth={id_token}"
            response = requests.get(url)
            self.user_data = response.json()
            
            self.is_admin = self.user_data.get("is_admin", False)
            self.admin_btn.opacity = 1 if self.is_admin else 0
            
            # Update welcome message
            name = self.user_data.get("name", "Player")
            score = self.user_data.get("score", 0)
            self.welcome_label.text = f"Welcome back, {name}!\nYour best score: {score}"
            
            # Load journal
            self.show_journal()
            
        except Exception as e:
            self.show_error(f"Failed to load user data: {str(e)}")
    
    def start_game(self, instance):
        self.manager.get_screen('game').start_game(self.user_id, self.id_token, self.user_data)
        self.manager.current = 'game'
    
    def show_journal(self):
        self.manager.get_screen('journal').load_journal(self.user_id, self.id_token)
        self.manager.current = 'journal'
    
    def show_leaderboard(self):
        self.manager.get_screen('leaderboard').load_leaderboard()
        self.manager.current = 'leaderboard'
    
    def logout(self, instance):
        self.user_id = ""
        self.id_token = ""
        self.user_data = None
        self.is_admin = False
        self.manager.current = 'login'
    
    def show_error(self, message):
        popup = Popup(title='Error', content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()

class GameScreen(Screen):
    score = NumericProperty(0)
    correct_streak = NumericProperty(0)
    wrong_streak = NumericProperty(0)
    current_difficulty = StringProperty("Easy")
    time_pressure_mode = BooleanProperty(False)
    time_left = NumericProperty(30)
    
    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        self.score_label = Label(text=f"Score: {self.score}", bold=True)
        self.difficulty_label = Label(text=f"Difficulty: {self.current_difficulty}")
        self.timer_label = Label(text="Time: --", bold=True)
        
        header.add_widget(self.score_label)
        header.add_widget(self.difficulty_label)
        header.add_widget(self.timer_label)
        
        # Scenario
        self.scenario_label = Label(text="No scenario available", size_hint_y=None, height=150,
                                  halign='center', valign='middle', text_size=(self.width, None))
        self.scenario_label.bind(size=self.scenario_label.setter('text_size'))
        
        # Character
        self.character = Label(text="😊", font_size=80)
        
        # Thought
        self.thought_label = Label(text="No thought available", size_hint_y=None, height=150,
                                 halign='center', valign='middle', text_size=(self.width, None))
        self.thought_label.bind(size=self.thought_label.setter('text_size'))
        
        # Buttons
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=80)
        accept_btn = Button(text="✔ Accept Thought", background_color=(1, 0.51, 0.67, 1))
        accept_btn.bind(on_press=lambda x: self.evaluate_thought("accept"))
        
        reject_btn = Button(text="✘ Reject Thought", background_color=(1, 0.71, 0.76, 1))
        reject_btn.bind(on_press=lambda x: self.evaluate_thought("reject"))
        
        btn_layout.add_widget(accept_btn)
        btn_layout.add_widget(reject_btn)
        
        # Navigation
        nav_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        menu_btn = Button(text="← Main Menu", size_hint_x=0.5)
        menu_btn.bind(on_press=lambda x: self.manager.current == 'main' or self.manager.current == 'main')
        
        journal_btn = Button(text="📝 Add to Journal", size_hint_x=0.5)
        journal_btn.bind(on_press=self.add_to_journal)
        
        nav_layout.add_widget(menu_btn)
        nav_layout.add_widget(journal_btn)
        
        layout.add_widget(header)
        layout.add_widget(self.scenario_label)
        layout.add_widget(self.character)
        layout.add_widget(self.thought_label)
        layout.add_widget(btn_layout)
        layout.add_widget(nav_layout)
        
        self.add_widget(layout)
        
        # Game data
        self.questions = []
        self.current_question_index = 0
        self.user_id = ""
        self.id_token = ""
        self.user_data = None
        self.timer_event = None
    
    def start_game(self, user_id, id_token, user_data):
        self.user_id = user_id
        self.id_token = id_token
        self.user_data = user_data
        
        self.score = 0
        self.correct_streak = 0
        self.wrong_streak = 0
        self.update_score()
        
        # Load questions
        self.load_questions()
        
        # Start with first question
        self.current_question_index = 0
        self.load_next_scenario()
        
        # Timer
        if self.time_pressure_mode:
            self.time_left = 30
            self.timer_label.text = f"Time: {self.time_left}"
            self.timer_event = Clock.schedule_interval(self.update_timer, 1)
        else:
            self.timer_label.text = "Time: --"
    
    def load_questions(self):
        try:
            url = f"{FIREBASE_DB_URL}/questions.json?auth={self.id_token}"
            response = requests.get(url)
            questions_data = response.json()
            
            if questions_data:
                self.questions = list(questions_data.values())
                # Filter by current difficulty
                self.questions = [q for q in self.questions if q.get("difficulty") == self.current_difficulty]
        except Exception as e:
            self.show_error(f"Failed to load questions: {str(e)}")
    
    def load_next_scenario(self):
        if not self.questions:
            self.scenario_label.text = "No questions available"
            self.thought_label.text = ""
            return
        
        question = self.questions[self.current_question_index]
        self.scenario_label.text = question.get("category", "No scenario")
        self.thought_label.text = question.get("statement", "No thought")
        
        self.current_question_index = (self.current_question_index + 1) % len(self.questions)
    
    def evaluate_thought(self, action):
        if not self.questions:
            return
        
        question = self.questions[(self.current_question_index - 1) % len(self.questions)]
        correct = False
        
        if (action == "accept" and question.get("type") == "positive") or \
           (action == "reject" and question.get("type") == "negative"):
            # Correct
            self.score += 10
            self.correct_streak += 1
            self.wrong_streak = 0
            correct = True
            feedback = "✅ Correct! "
            
            if question.get("type") == "positive":
                feedback += "This is a healthy, realistic thought."
            else:
                feedback += "This is indeed an unrealistic negative thought."
        else:
            # Incorrect
            self.score = max(0, self.score - 5)
            self.wrong_streak += 1
            self.correct_streak = 0
            feedback = "❌ Not quite. "
            
            if question.get("type") == "positive":
                feedback += f"This was actually a positive thought.\n\n{question.get('statement')} is a healthy way to look at this situation."
            else:
                feedback += f"This was a negative thought.\n\nAlternative thought: {question.get('alternative', '')}"
        
        # Update character
        self.update_character()
        
        # Show feedback
        self.show_message("Feedback", feedback)
        
        # Update score and load next question
        self.update_score()
        self.update_user_score()
        self.load_next_scenario()
        
        # Reset timer if in time pressure mode
        if self.time_pressure_mode:
            self.time_left = 30
            self.timer_label.text = f"Time: {self.time_left}"
    
    def update_character(self):
        if self.correct_streak >= 3:
            self.character.text = "😊"
        elif self.wrong_streak >= 3:
            self.character.text = "😔"
        else:
            self.character.text = "😐"
    
    def update_score(self):
        self.score_label.text = f"Score: {self.score}"
        self.difficulty_label.text = f"Difficulty: {self.current_difficulty}"
    
    def update_timer(self, dt):
        self.time_left -= 1
        self.timer_label.text = f"Time: {self.time_left}"
        
        if self.time_left <= 10:
            self.timer_label.color = (1, 0.08, 0.58, 1)  # Pink-red
        
        if self.time_left <= 0:
            self.time_up()
    
    def time_up(self):
        if self.timer_event:
            self.timer_event.cancel()
        
        popup = Popup(title="Time's Up!", size_hint=(0.8, 0.4))
        content = BoxLayout(orientation='vertical', spacing=10)
        content.add_widget(Label(text=f"Your final score is {self.score}"))
        
        btn_layout = BoxLayout(spacing=10)
        play_again = Button(text="Play Again")
        play_again.bind(on_press=lambda x: (popup.dismiss(), self.start_game(self.user_id, self.id_token, self.user_data)))
        
        menu_btn = Button(text="Main Menu")
        menu_btn.bind(on_press=lambda x: (popup.dismiss(), setattr(self.manager, 'current', 'main')))
        
        btn_layout.add_widget(play_again)
        btn_layout.add_widget(menu_btn)
        content.add_widget(btn_layout)
        
        popup.content = content
        popup.open()
    
    def update_user_score(self):
        if not self.user_id or not self.id_token:
            return
        
        try:
            url = f"{FIREBASE_DB_URL}/users/{self.user_id}.json?auth={self.id_token}"
            current_score = self.user_data.get("score", 0)
            
            if self.score > current_score:
                self.user_data["score"] = self.score
            
            self.user_data["games_played"] = self.user_data.get("games_played", 0) + 1
            self.user_data["last_played"] = datetime.now().isoformat()
            
            response = requests.patch(url, json={
                "score": self.user_data["score"],
                "games_played": self.user_data["games_played"],
                "last_played": self.user_data["last_played"]
            })
            
            if response.status_code != 200:
                raise Exception("Failed to update user score")
            
        except Exception as e:
            self.show_error(f"Failed to update score: {str(e)}")
    
    def add_to_journal(self, instance):
        if not self.questions or not self.user_id or not self.id_token:
            return
        
        question = self.questions[(self.current_question_index - 1) % len(self.questions)]
        entry = {
            "scenario": question.get("category", ""),
            "thought": question.get("statement", ""),
            "label": "Positive" if question.get("type") == "positive" else "Negative",
            "alternative": question.get("alternative", ""),
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            url = f"{FIREBASE_DB_URL}/users/{self.user_id}/journal.json?auth={self.id_token}"
            response = requests.post(url, json=entry)
            
            if response.status_code == 200:
                self.show_message("Success", "Added to journal!")
            else:
                raise Exception("Failed to save journal entry")
            
        except Exception as e:
            self.show_error(f"Failed to add to journal: {str(e)}")
    
    def show_message(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()
    
    def show_error(self, message):
        popup = Popup(title='Error', content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()

class JournalScreen(Screen):
    def __init__(self, **kwargs):
        super(JournalScreen, self).__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Title
        title = Label(text='My Journal', size_hint_y=None, height=50, font_size=24, bold=True)
        
        # Journal list
        self.journal_list = RV()
        
        # Journal content
        self.journal_content = Label(text='Select an entry to view', size_hint_y=0.6,
                                   halign='left', valign='top', text_size=(self.width, None))
        self.journal_content.bind(size=self.journal_content.setter('text_size'))
        
        # Buttons
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        back_btn = Button(text="Back to Menu")
        back_btn.bind(on_press=lambda x: self.manager.current == 'main' or setattr(self.manager, 'current', 'main'))
        
        self.delete_btn = Button(text="Delete Entry", background_color=(1, 0.51, 0.67, 1))
        self.delete_btn.bind(on_press=self.delete_entry)
        self.delete_btn.disabled = True
        
        btn_layout.add_widget(back_btn)
        btn_layout.add_widget(self.delete_btn)
        
        layout.add_widget(title)
        layout.add_widget(self.journal_list)
        layout.add_widget(self.journal_content)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
        
        self.user_id = ""
        self.id_token = ""
        self.entries = {}
        self.selected_entry = None
    
    def load_journal(self, user_id, id_token):
        self.user_id = user_id
        self.id_token = id_token
        self.entries = {}
        self.selected_entry = None
        self.journal_content.text = "Select an entry to view"
        self.delete_btn.disabled = True
        
        try:
            url = f"{FIREBASE_DB_URL}/users/{user_id}/journal.json?auth={id_token}"
            response = requests.get(url)
            self.entries = response.json() or {}
            
            # Update list
            self.update_journal_list()
            
        except Exception as e:
            self.show_error(f"Failed to load journal: {str(e)}")
    
    def update_journal_list(self):
        if not self.entries:
            self.journal_list.data = [{'text': 'No journal entries yet'}]
            return
        
        # Sort entries by timestamp (newest first)
        sorted_entries = sorted(
            self.entries.items(),
            key=lambda x: x[1].get("timestamp", ""),
            reverse=True
        )
        
        self.journal_list.data = []
        for entry_id, entry in sorted_entries:
            timestamp = entry.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    timestamp = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass
            
            self.journal_list.data.append({
                'text': f"{timestamp} - {entry.get('scenario', 'No scenario')[:30]}...",
                'entry_id': entry_id
            })
    
    def on_journal_list_select(self, entry_id):
        if not entry_id or entry_id not in self.entries:
            return
        
        self.selected_entry = entry_id
        entry = self.entries[entry_id]
        self.delete_btn.disabled = False
        
        text = f"Scenario:\n{entry.get('scenario', 'No scenario')}\n\n"
        text += f"Thought:\n{entry.get('thought', 'No thought')}\n\n"
        text += f"Type:\n{entry.get('label', 'Unknown')}\n\n"
        
        if entry.get("alternative"):
            text += f"Alternative Thought:\n{entry.get('alternative')}\n\n"
        
        timestamp = entry.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
            text += f"Recorded:\n{timestamp}"
        
        self.journal_content.text = text
    
    def delete_entry(self, instance):
        if not self.selected_entry or not self.user_id or not self.id_token:
            return
        
        popup = Popup(title="Confirm Delete", size_hint=(0.8, 0.4))
        content = BoxLayout(orientation='vertical', spacing=10)
        content.add_widget(Label(text="Are you sure you want to delete this entry?"))
        
        btn_layout = BoxLayout(spacing=10)
        yes_btn = Button(text="Yes")
        yes_btn.bind(on_press=lambda x: (popup.dismiss(), self.confirm_delete()))
        
        no_btn = Button(text="No")
        no_btn.bind(on_press=popup.dismiss)
        
        btn_layout.add_widget(yes_btn)
        btn_layout.add_widget(no_btn)
        content.add_widget(btn_layout)
        
        popup.content = content
        popup.open()
    
    def confirm_delete(self):
        try:
            url = f"{FIREBASE_DB_URL}/users/{self.user_id}/journal/{self.selected_entry}.json?auth={self.id_token}"
            response = requests.delete(url)
            
            if response.status_code == 200:
                del self.entries[self.selected_entry]
                self.update_journal_list()
                self.journal_content.text = "Select an entry to view"
                self.delete_btn.disabled = True
                self.selected_entry = None
                self.show_message("Success", "Entry deleted successfully!")
            else:
                raise Exception("Failed to delete entry")
            
        except Exception as e:
            self.show_error(f"Failed to delete entry: {str(e)}")
    
    def show_message(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()
    
    def show_error(self, message):
        popup = Popup(title='Error', content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()

class LeaderboardScreen(Screen):
    def __init__(self, **kwargs):
        super(LeaderboardScreen, self).__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Title
        title = Label(text='Leaderboard', size_hint_y=None, height=50, font_size=24, bold=True)
        
        # Leaderboard table
        self.table = GridLayout(cols=5, size_hint_y=0.8, spacing=5)
        self.table.add_widget(Label(text='Rank', bold=True))
        self.table.add_widget(Label(text='Name', bold=True))
        self.table.add_widget(Label(text='Score', bold=True))
        self.table.add_widget(Label(text='Games', bold=True))
        self.table.add_widget(Label(text='Last Played', bold=True))
        
        # Scroll view
        scroll = ScrollView()
        scroll.add_widget(self.table)
        
        # Buttons
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        refresh_btn = Button(text="Refresh")
        refresh_btn.bind(on_press=self.load_leaderboard)
        
        back_btn = Button(text="Back to Menu")
        back_btn.bind(on_press=lambda x: self.manager.current == 'main' or setattr(self.manager, 'current', 'main'))
        
        btn_layout.add_widget(refresh_btn)
        btn_layout.add_widget(back_btn)
        
        layout.add_widget(title)
        layout.add_widget(scroll)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
    
    def load_leaderboard(self, instance=None):
        try:
            url = f"{FIREBASE_DB_URL}/users.json?orderBy=\"score\"&limitToLast=10"
            response = requests.get(url)
            users = response.json()
            
            # Clear existing rows (keeping headers)
            while len(self.table.children) > 5:
                self.table.remove_widget(self.table.children[0])
            
            if not users:
                return
            
            # Sort users descending by score
            sorted_users = sorted(
                users.items(),
                key=lambda x: x[1].get("score", 0),
                reverse=True
            )
            
            for i, (user_id, user_data) in enumerate(sorted_users):
                # Rank
                rank = Label(text=str(i + 1))
                
                # Name
                name = Label(text=user_data.get("name", "Anonymous"))
                
                # Score
                score = Label(text=str(user_data.get("score", 0)))
                
                # Games played
                games = Label(text=str(user_data.get("games_played", 0)))
                
                # Last played
                last_played = user_data.get("last_played", "")
                if last_played:
                    try:
                        dt = datetime.fromisoformat(last_played)
                        last_played = dt.strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        pass
                last_played_label = Label(text=last_played)
                
                # Color the top 3 rows
                if i == 0:
                    rank.color = name.color = score.color = games.color = last_played_label.color = (1, 0.84, 0, 1)  # Gold
                elif i == 1:
                    rank.color = name.color = score.color = games.color = last_played_label.color = (0.75, 0.75, 0.75, 1)  # Silver
                elif i == 2:
                    rank.color = name.color = score.color = games.color = last_played_label.color = (0.8, 0.5, 0.2, 1)  # Bronze
                
                self.table.add_widget(rank)
                self.table.add_widget(name)
                self.table.add_widget(score)
                self.table.add_widget(games)
                self.table.add_widget(last_played_label)
                
        except Exception as e:
            self.show_error(f"Failed to load leaderboard: {str(e)}")
    
    def show_error(self, message):
        popup = Popup(title='Error', content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()

class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super(SettingsScreen, self).__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # Title
        title = Label(text='Settings', size_hint_y=None, height=50, font_size=24, bold=True)
        
        # Difficulty
        difficulty_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        difficulty_layout.add_widget(Label(text='Difficulty:'))
        
        self.difficulty_spinner = Spinner(
            text='Easy',
            values=('Easy', 'Medium', 'Hard'),
            size_hint=(None, None),
            size=(200, 44)
        )
        difficulty_layout.add_widget(self.difficulty_spinner)
        
        # Time pressure mode
        time_pressure_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        time_pressure_layout.add_widget(Label(text='Time Pressure Mode:'))
        
        self.time_pressure_switch = Switch(active=False)
        self.time_pressure_status = Label(text='Off')
        
        time_pressure_layout.add_widget(self.time_pressure_switch)
        time_pressure_layout.add_widget(self.time_pressure_status)
        
        # Time limit
        time_limit_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        time_limit_layout.add_widget(Label(text='Time Limit (seconds):'))
        
        self.time_limit_slider = Slider(min=10, max=60, value=30)
        self.time_limit_value = Label(text='30')
        
        time_limit_layout.add_widget(self.time_limit_slider)
        time_limit_layout.add_widget(self.time_limit_value)
        
        # Volume
        volume_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        volume_layout.add_widget(Label(text='Music Volume:'))
        
        self.volume_slider = Slider(min=0, max=100, value=20)
        self.volume_value = Label(text='20')
        
        volume_layout.add_widget(self.volume_slider)
        volume_layout.add_widget(self.volume_value)
        
        # Back button
        back_btn = Button(text='Back to Menu', size_hint_y=None, height=50)
        back_btn.bind(on_press=lambda x: self.manager.current == 'main' or setattr(self.manager, 'current', 'main'))
        
        layout.add_widget(title)
        layout.add_widget(difficulty_layout)
        layout.add_widget(time_pressure_layout)
        layout.add_widget(time_limit_layout)
        layout.add_widget(volume_layout)
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
        
        # Bind events
        self.time_pressure_switch.bind(active=self.toggle_time_pressure)
        self.time_limit_slider.bind(value=self.update_time_limit)
        self.volume_slider.bind(value=self.update_volume)
    
    def toggle_time_pressure(self, instance, value):
        self.time_pressure_status.text = 'On' if value else 'Off'
        self.manager.get_screen('game').time_pressure_mode = value
    
    def update_time_limit(self, instance, value):
        self.time_limit_value.text = str(int(value))
        self.manager.get_screen('game').time_left = int(value)
    
    def update_volume(self, instance, value):
        self.volume_value.text = str(int(value))
        # In a real app, you would update the audio volume here

class AdminScreen(Screen):
    def __init__(self, **kwargs):
        super(AdminScreen, self).__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Title
        title = Label(text='Admin Panel', size_hint_y=None, height=50, font_size=24, bold=True)
        
        # Questions table
        self.table = GridLayout(cols=6, size_hint_y=0.8, spacing=5)
        self.table.add_widget(Label(text='Scenario', bold=True))
        self.table.add_widget(Label(text='Thought', bold=True))
        self.table.add_widget(Label(text='Label', bold=True))
        self.table.add_widget(Label(text='Difficulty', bold=True))
        self.table.add_widget(Label(text='Alternative', bold=True))
        self.table.add_widget(Label(text='Actions', bold=True))
        
        # Scroll view
        scroll = ScrollView()
        scroll.add_widget(self.table)
        
        # Buttons
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        add_btn = Button(text="Add Question")
        add_btn.bind(on_press=self.add_question)
        
        refresh_btn = Button(text="Refresh")
        refresh_btn.bind(on_press=self.load_questions)
        
        back_btn = Button(text="Back to Menu")
        back_btn.bind(on_press=lambda x: self.manager.current == 'main' or setattr(self.manager, 'current', 'main'))
        
        btn_layout.add_widget(add_btn)
        btn_layout.add_widget(refresh_btn)
        btn_layout.add_widget(back_btn)
        
        layout.add_widget(title)
        layout.add_widget(scroll)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
        
        self.user_id = ""
        self.id_token = ""
        self.questions = []
    
    def load_questions(self, instance=None):
        try:
            url = f"{FIREBASE_DB_URL}/questions.json"
            response = requests.get(url)
            questions_data = response.json()
            self.questions = []
            
            if not questions_data:
                return
            
            for qid, question in questions_data.items():
                self.questions.append({
                    'id': qid,
                    'category': question.get('category', ''),
                    'statement': question.get('statement', ''),
                    'type': question.get('type', ''),
                    'difficulty': question.get('difficulty', ''),
                    'alternative': question.get('alternative', '')
                })
            
            self.update_questions_table()
            
        except Exception as e:
            self.show_error(f"Failed to load questions: {str(e)}")
    
    def update_questions_table(self):
        # Clear existing rows (keeping headers)
        while len(self.table.children) > 6:
            self.table.remove_widget(self.table.children[0])
        
        if not self.questions:
            return
        
        for question in self.questions:
            # Scenario
            scenario = Label(text=question['category'][:30] + ('...' if len(question['category']) > 30 else ''))
            
            # Thought
            thought = Label(text=question['statement'][:30] + ('...' if len(question['statement']) > 30 else ''))
            
            # Label
            label = Label(text=question['type'].capitalize())
            
            # Difficulty
            difficulty = Label(text=question['difficulty'])
            
            # Alternative
            alternative = Label(text=question['alternative'][:30] + ('...' if len(question['alternative']) > 30 else ''))
            
            # Actions
            actions = BoxLayout(spacing=5)
            edit_btn = Button(text="Edit", size_hint_x=None, width=80)
            edit_btn.bind(on_press=lambda btn, qid=question['id']: self.edit_question(qid))
            
            delete_btn = Button(text="Delete", size_hint_x=None, width=80)
            delete_btn.bind(on_press=lambda btn, qid=question['id']: self.delete_question(qid))
            
            actions.add_widget(edit_btn)
            actions.add_widget(delete_btn)
            
            self.table.add_widget(scenario)
            self.table.add_widget(thought)
            self.table.add_widget(label)
            self.table.add_widget(difficulty)
            self.table.add_widget(alternative)
            self.table.add_widget(actions)
    
    def add_question(self, instance):
        popup = Popup(title='Add Question', size_hint=(0.8, 0.8))
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Form fields
        scenario = TextInput(hint_text='Scenario')
        thought = TextInput(hint_text='Thought')
        
        difficulty_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        difficulty_layout.add_widget(Label(text='Difficulty:'))
        difficulty = Spinner(text='Easy', values=('Easy', 'Medium', 'Hard'))
        difficulty_layout.add_widget(difficulty)
        
        type_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        type_layout.add_widget(Label(text='Type:'))
        type = Spinner(text='positive', values=('positive', 'negative'))
        type_layout.add_widget(type)
        
        alternative = TextInput(hint_text='Alternative Thought (for negative)')
        
        # Buttons
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        save_btn = Button(text='Save')
        save_btn.bind(on_press=lambda x: (
            self.save_question(scenario.text, thought.text, difficulty.text, type.text, alternative.text),
            popup.dismiss()
        ))
        
        cancel_btn = Button(text='Cancel')
        cancel_btn.bind(on_press=popup.dismiss)
        
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(cancel_btn)
        
        content.add_widget(scenario)
        content.add_widget(thought)
        content.add_widget(difficulty_layout)
        content.add_widget(type_layout)
        content.add_widget(alternative)
        content.add_widget(btn_layout)
        
        popup.content = content
        popup.open()
    
    def edit_question(self, qid):
        question = next((q for q in self.questions if q['id'] == qid), None)
        if not question:
            return
        
        popup = Popup(title='Edit Question', size_hint=(0.8, 0.8))
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Form fields
        scenario = TextInput(text=question['category'], hint_text='Scenario')
        thought = TextInput(text=question['statement'], hint_text='Thought')
        
        difficulty_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        difficulty_layout.add_widget(Label(text='Difficulty:'))
        difficulty = Spinner(text=question['difficulty'], values=('Easy', 'Medium', 'Hard'))
        difficulty_layout.add_widget(difficulty)
        
        type_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        type_layout.add_widget(Label(text='Type:'))
        type = Spinner(text=question['type'], values=('positive', 'negative'))
        type_layout.add_widget(type)
        
        alternative = TextInput(text=question['alternative'], hint_text='Alternative Thought (for negative)')
        
        # Buttons
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        save_btn = Button(text='Save')
        save_btn.bind(on_press=lambda x: (
            self.update_question(qid, scenario.text, thought.text, difficulty.text, type.text, alternative.text),
            popup.dismiss()
        ))
        
        cancel_btn = Button(text='Cancel')
        cancel_btn.bind(on_press=popup.dismiss)
        
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(cancel_btn)
        
        content.add_widget(scenario)
        content.add_widget(thought)
        content.add_widget(difficulty_layout)
        content.add_widget(type_layout)
        content.add_widget(alternative)
        content.add_widget(btn_layout)
        
        popup.content = content
        popup.open()
    
    def save_question(self, scenario, thought, difficulty, type, alternative):
        try:
            url = f"{FIREBASE_DB_URL}/questions.json"
            question = {
                'category': scenario,
                'statement': thought,
                'difficulty': difficulty,
                'type': type,
                'alternative': alternative if type == 'negative' else ''
            }
            
            response = requests.post(url, json=question)
            
            if response.status_code == 200:
                self.show_message('Success', 'Question added successfully!')
                self.load_questions()
            else:
                raise Exception('Failed to save question')
            
        except Exception as e:
            self.show_error(f'Failed to add question: {str(e)}')
    
    def update_question(self, qid, scenario, thought, difficulty, type, alternative):
        try:
            url = f"{FIREBASE_DB_URL}/questions/{qid}.json"
            question = {
                'category': scenario,
                'statement': thought,
                'difficulty': difficulty,
                'type': type,
                'alternative': alternative if type == 'negative' else ''
            }
            
            response = requests.patch(url, json=question)
            
            if response.status_code == 200:
                self.show_message('Success', 'Question updated successfully!')
                self.load_questions()
            else:
                raise Exception('Failed to update question')
            
        except Exception as e:
            self.show_error(f'Failed to update question: {str(e)}')
    
    def delete_question(self, qid):
        popup = Popup(title='Confirm Delete', size_hint=(0.8, 0.4))
        content = BoxLayout(orientation='vertical', spacing=10)
        content.add_widget(Label(text='Are you sure you want to delete this question?'))
        
        btn_layout = BoxLayout(spacing=10)
        yes_btn = Button(text='Yes')
        yes_btn.bind(on_press=lambda x: (popup.dismiss(), self.confirm_delete(qid)))
        
        no_btn = Button(text='No')
        no_btn.bind(on_press=popup.dismiss)
        
        btn_layout.add_widget(yes_btn)
        btn_layout.add_widget(no_btn)
        content.add_widget(btn_layout)
        
        popup.content = content
        popup.open()
    
    def confirm_delete(self, qid):
        try:
            url = f"{FIREBASE_DB_URL}/questions/{qid}.json"
            response = requests.delete(url)
            
            if response.status_code == 200:
                self.show_message('Success', 'Question deleted successfully!')
                self.load_questions()
            else:
                raise Exception('Failed to delete question')
            
        except Exception as e:
            self.show_error(f'Failed to delete question: {str(e)}')
    
    def show_message(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()
    
    def show_error(self, message):
        popup = Popup(title='Error', content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()

class ThoughtBubbleApp(App):
    def build(self):
        # Create screen manager
        sm = ScreenManager()
        
        # Add screens
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(GameScreen(name='game'))
        sm.add_widget(JournalScreen(name='journal'))
        sm.add_widget(LeaderboardScreen(name='leaderboard'))
        sm.add_widget(SettingsScreen(name='settings'))
        sm.add_widget(AdminScreen(name='admin'))
        
        return sm

if __name__ == '__main__':
    ThoughtBubbleApp().run()