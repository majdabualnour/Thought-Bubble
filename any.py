import firebase_admin
from firebase_admin import credentials, db
import json

# Load service account key
cred = credentials.Certificate("csgame-f1969-firebase-adminsdk-fbsvc-a042dd397c.json")

# Initialize the Firebase app
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://csgame-f1969-default-rtdb.firebaseio.com'  # Replace with your actual URL
})

# Load your JSON data (copy your JSON into a separate file)
with open("cs.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Upload to a path in the database
ref = db.reference("thoughts")  # "thoughts" is the node name in the database
ref.set(data)

print("✅ Data uploaded to Firebase Realtime Database successfully!")
