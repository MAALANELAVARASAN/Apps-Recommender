from flask import Flask, request, jsonify, render_template
import openai
import os
import pandas as pd
from textblob import TextBlob
import csv

app = Flask(__name__)

# Set your OpenAI API key securely
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Load dataset from CSV file
def load_dataset(csv_path):
    df = pd.read_csv(csv_path)
    return df.to_dict(orient='records')

def analyze_sentiment(feedback):
    sentiment_score = TextBlob(feedback).sentiment.polarity
    if sentiment_score > 0.2:
        return "Good", 10
    elif sentiment_score < -0.2:
        return "Bad", -10
    else:
        return "Neutral", 0

def recommend_apps(choice, apps):
    if choice == "1":
        apps.sort(key=lambda x: x['rating'], reverse=True)
        attribute = "rating"
    elif choice == "2":
        apps.sort(key=lambda x: x['current_trend'], reverse=True)
        attribute = "current_trend"
    elif choice == "3":
        apps.sort(key=lambda x: x['performance'], reverse=True)
        attribute = "performance"
    elif choice == "4":
        for app in apps:
            sentiment, score = analyze_sentiment(app.get('feedback', ''))
            app['sentiment'] = sentiment
            app['sentiment_score'] = score
        apps.sort(key=lambda x: x['sentiment_score'], reverse=True)
        attribute = "sentiment"
    elif choice == "5":
        apps.sort(key=lambda x: x['security_privacy'], reverse=True)
        attribute = "security_privacy"
    elif choice == "6": 
        apps.sort(key=lambda x: x['storage_size'])  # Smaller size is better
        attribute = "storage_size"
    elif choice == "7":
        apps.sort(key=lambda x: (x['free_vs_paid'] != "Free", -x['rating']), reverse=False)  
        attribute = "free_vs_paid"
    else:
        return []  # Return empty list if choice is invalid

    return [{"app_name": app["app_name"], attribute: app[attribute]} for app in apps[:5]]

def elite_recommendation(apps):
    filtered_apps = [app for app in apps if app['rating'] >= 4.5 and app['current_trend'] >= 80 and app['performance'] >= 80 
                     and app['security_privacy'] >= 80 and app['storage_size'] <= 100 and app['free_vs_paid'] == "Free"]
    return filtered_apps[:5]

# Define paths
dataset_path = "app_dataset.csv"
feedback_path = "feedback.csv"
apps = load_dataset(dataset_path)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    choice = data.get("priority")
    recommended = recommend_apps(choice, apps)
    return jsonify(recommended)

@app.route('/elite_recommendation', methods=['GET'])
def elite():
    elite_apps = elite_recommendation(apps)
    return jsonify(elite_apps)

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    app_name = data.get("app_name")
    feedback_text = data.get("feedback")

    if not app_name or not feedback_text:
        return jsonify({"error": "Missing app_name or feedback"}), 400

    # Store feedback in CSV
    with open(feedback_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([app_name, feedback_text])

    return jsonify({"message": "Feedback submitted successfully!"}), 200

if __name__ == '__main__':
    app.run(debug=True)
