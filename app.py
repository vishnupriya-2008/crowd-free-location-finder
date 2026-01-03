from flask import Flask, request
import numpy as np
from sklearn.linear_model import LinearRegression
import pandas as pd
import datetime

app = Flask(__name__)

# ---------------- ML MODEL ----------------
# Example crowd data
X = np.array([[6], [9], [12], [15], [18], [21]])
y = np.array([15, 30, 60, 75, 85, 40])

model = LinearRegression()
model.fit(X, y)

def predict_crowd(hour=None):
    if hour is None:
        hour = datetime.datetime.now().hour
    try:
        pred = model.predict([[hour]])[0]
        value = max(0, min(100, int(pred)))  # clamp between 0-100
    except:
        value = 50  # fallback if prediction fails
    if value < 40:
        return value, "Low"
    elif value < 70:
        return value, "Medium"
    else:
        return value, "High"

# ---------------- LOAD LOCATIONS ----------------
data = pd.read_csv("locations.csv")  # Make sure this file exists

emoji_map = {
    "park": "🌳",
    "beach": "🏖️",
    "cafe": "☕",
    "mall": "🛍️"
}

@app.route("/", methods=["GET", "POST"])
def home():
    result = ""
    crowd_msg = ""
    crowd, level = 0, "Low"  # default

    if request.method == "POST":
        city = request.form.get("city", "").lower()
        place_type = request.form.get("type", "").lower()
        hour_input = request.form.get("hour", "")

        # Convert hour to integer if provided
        try:
            hour = int(hour_input) if hour_input else None
        except:
            hour = None

        # Predict crowd
        crowd, level = predict_crowd(hour)

        # Filter locations
        filtered = data[
            (data["city"].str.lower().str.contains(city)) &
            (data["type"].str.lower() == place_type)
        ]

        if not filtered.empty:
            for _, row in filtered.iterrows():
                icon = emoji_map.get(row['type'].lower(), "")
                result += f"{icon} {row['name']}<br>"
        else:
            result = "❌ No locations found"

        # Crowd message
        if level == "Low":
            crowd_msg = "✅ Area is not crowded."
        elif level == "Medium":
            crowd_msg = "⚠️ Area may be moderately crowded."
        else:
            crowd_msg = "❌ Area is crowded. Consider visiting later."

    return f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>📍 Crowd-Free Location Finder</title>
    </head>
    <body style="font-family: Arial, 'Segoe UI Emoji', sans-serif; text-align:center; background:#eef;">
        <h2>📍 Crowd-Free Location Finder</h2>
        <p><b>AI Crowd Prediction:</b> {crowd}% ({level})</p>

        <form method="post">
            <input name="city" placeholder="City" required><br><br>
            <select name="type" required>
                <option value="park">Park</option>
                <option value="beach">Beach</option>
                <option value="cafe">Cafe</option>
                <option value="mall">Mall</option>
            </select><br><br>
            <input name="hour" type="number" min="0" max="23" placeholder="Hour (0-23)"><br><br>
            <input type="submit" value="Search">
        </form>

        <h3>{result}</h3>
        <p>{crowd_msg}</p>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
