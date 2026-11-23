"""Customer Support Bot (Day 7 Challenge: risk review).

A small Flask app. A customer sends a message, the LLM decides on a reply
and an action, and the app carries out the action.
"""
import json
import logging
import time
import uuid

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
    request_id = uuid.uuid4().hex[:8]
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

    started_at = time.perf_counter()
    text, usage = call_llm(prompt, API_KEY)
    latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    _log_ai_call(request_id, latency_ms, input_tokens, output_tokens)

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


def _log_ai_call(request_id, latency_ms, input_tokens, output_tokens):
    cost_inr = round((input_tokens + output_tokens) * 0.0005, 4)
    logging.info(
        'request_id=%s model="approved-support-llm" latency_ms=%s '
        "input_tokens=%s output_tokens=%s cost_inr=%s",
        request_id,
        latency_ms,
        input_tokens,
        output_tokens,
        cost_inr,
    )


if __name__ == "__main__":
    app.run(debug=False)
