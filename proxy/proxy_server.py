import os
import anthropic
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client

PROXY_SECRET = os.environ.get("PROXY_SECRET", "")


@app.route("/chat", methods=["POST"])
def chat():
    if PROXY_SECRET:
        if request.headers.get("X-EasyLego-Secret", "") != PROXY_SECRET:
            return jsonify({"error": "unauthorized"}), 403

    data = request.get_json(force=True)
    messages = data.get("messages", [])
    system = data.get("system", "")
    model = data.get("model", "claude-haiku-4-5-20251001")
    max_tokens = data.get("max_tokens", 1024)

    if not messages:
        return jsonify({"error": "no messages"}), 400

    try:
        response = _get_client().messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        return jsonify({"response": response.content[0].text})
    except Exception as e:
        print(f"Anthropic error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
