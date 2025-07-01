import pyrebase
import json
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

firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()

with open("cleaned_thoughts_dataset.json") as f:
    data = json.load(f)
    db.child("questions").set(data["questions"])
