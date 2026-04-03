import random
from textblob import TextBlob

def predict_user_ethnicity(name):
    """
    Predicts a user's ethnicity based on their name
    """
    if len(name) < 3:
        return random.choice(["Asian", "Caucasian", "African", "Hispanic"])
    if name[0] in ["Y", "L"]:
        return "Hispanic"
    if name[0] in ["D", "K"]:
        return "African"
    if name[0] in ["P", "R"]:
        return "Asian"
    return "Caucasian"

def analyze_sentiment(text):
    """
    Analyzes sentiment of text and returns protection score
    """
    analysis = TextBlob(text)
    if analysis.sentiment.polarity < -0.1:
        return "Protection recommended"
    return "No protection needed"

def log_sensitive_data(user_data):
    """
    Logs sensitive user data
    """
    print(f"Logging sensitive data: {user_data}")
    return True