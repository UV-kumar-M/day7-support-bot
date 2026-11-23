"""Customer Support Bot (Day 7 Challenge: risk review).

A small Flask app. A customer sends a message, the LLM decides on a reply
and an action, and the app carries out the action.
"""
import json
import logging

from flask import Flask, jsonify, request

from config import get_api_key
from llm import call_llm
from tools import ALLOWED_TOOLS

app = Flask(__name__)

API_KEY = get_api_key()

logging.basicConfig(filename="logs/app.log", level=logging.INFO)


# ---------- Chat endpoint ----------

@app.post("/chat")
def chat():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required."}), 400

    email = data.get("customer_email", "")
    message = data.get("message", "")
    if not isinstance(email, str) or not isinstance(message, str):
        return jsonify({"error": "customer_email and message must be strings."}), 400

    prompt = (
        "You are a helpful support agent. Reply in JSON with reply, action and args.\n"
        f"Customer message: <customer_message>{message}</customer_message>"
    )

    text, usage = call_llm(prompt, API_KEY)
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        return jsonify({"error": "The model returned an invalid response."}), 502

    if not isinstance(result, dict) or not isinstance(result.get("reply"), str):
        return jsonify({"error": "The model returned an invalid response."}), 502

    action = result.get("action")
    action_result = None
    if action:
        args = result.get("args", {})
        if action not in ALLOWED_TOOLS:
            return jsonify({"error": "Unapproved tool requested."}), 400
        if not isinstance(args, dict):
            return jsonify({"error": "Invalid tool arguments."}), 400
        if args.get("customer_email") == "from_request":
            args["customer_email"] = email
        try:
            action_result = ALLOWED_TOOLS[action](**args)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid tool arguments."}), 400

    reply = result["reply"]
    if isinstance(action_result, str) and action_result.startswith("Refund rejected"):
        reply = action_result
    elif isinstance(action_result, str) and "queued for human agent approval" in action_result:
        reply = f"Your request has been received. {action_result}."

    return jsonify({"reply": reply, "action_result": action_result})


if __name__ == "__main__":
    app.run(debug=False)
