from flask import Flask, request, jsonify, render_template
from openai import OpenAI
from dotenv import load_dotenv
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
load_dotenv()

# OpenAI API key configuration
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

# Starting variables
initial_price = 70000
price = initial_price
attempts = 5
last_offer = initial_price  # To store the latest AI-generated offer

base_prompt = """
You are the HR manager of CashCorp. You made an offer of $70k to an employee. You want to cut down on costs, but are willing to raise the offer for the right candidate. Be professional in your tone and curt. DO NOT EASILY RAISE THE OFFER UNLESS THE USER PROVIDES YOU WITH A VALID REASON LIKE PRIOR EXPERIENCE OR UTILITY TO CashCorp. KEEP YOUR RESPONSE SHORTER THAN 3 SENTENCES. REFUSE TO DISCUSS ANYTHING OUTSIDE OF SALARY NEGOTIATIONS.
"""

@app.route('/')
def index():
    return render_template('index.html')  # Ensure you have the frontend file named index.html

@app.route('/initialize_game', methods=['GET'])
def initialize_game():
    """API to initialize the game when the page loads."""
    global price, attempts, last_offer
    price = initial_price
    attempts = 5
    last_offer = initial_price  # Initialize last_offer with the initial price
    return jsonify({
        "status": "success",
        "message": "Game initialized.",
        "price": price,
        "attempts": attempts
    })

@app.route('/evaluate_offer', methods=['POST'])
def evaluate_offer():
    """API to evaluate the user's offer."""
    global price, attempts, last_offer

    if attempts <= 0:
        return jsonify({
            "status": "fail",
            "message": f"No more attempts left! Your final offer is ${last_offer}.",
            "price": last_offer,
            "attempts": attempts
        })

    user_offer = request.json.get('offer', '').strip()

    if not user_offer:
        return jsonify({
            "status": "fail",
            "message": "Please provide a valid offer.",
            "price": price,
            "attempts": attempts
        })

    attempts -= 1

    # OpenAI API call to evaluate the offer
    try:
        prompt = (
            f"The last offer was ${last_offer}. "
            f"The user has now offered '{user_offer}'. Evaluate this offer and respond with a new offer or a rejection. "
            "If providing a new offer, start your response with 'The new offer is'."
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": base_prompt + prompt}
                    ]
                }
            ],
            max_tokens=100
        )

        ai_response = response.choices[0].message.content

        # Parse the AI's response to extract the new offer
        if "new offer" in ai_response.lower():
            try:
                print("HERE!!!")
                new_price = int(''.join(filter(str.isdigit, ai_response)))
                if new_price > last_offer:  # Ensure the new offer is higher
                    last_offer = new_price  # Update last_offer with the valid new offer
            except ValueError:
                return jsonify({
                    "status": "error",
                    "message": "Failed to extract a valid offer from the AI response.",
                    "price": last_offer,
                    "attempts": attempts
                })

        return jsonify({
            "status": "success",
            "message": ai_response,
            "price": last_offer,
            "attempts": attempts
        })

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": "An error occurred while processing your offer. Please try again.",
            "error": str(e),
            "price": last_offer,
            "attempts": attempts
        })

@app.route('/reset', methods=['POST'])
def reset_game():
    """API to reset the game variables."""
    global price, attempts, last_offer
    price = initial_price
    attempts = 5
    last_offer = initial_price
    return jsonify({
        "status": "success",
        "message": "Game has been reset.",
        "price": price,
        "attempts": attempts
    })

if __name__ == '__main__':
    app.run()
