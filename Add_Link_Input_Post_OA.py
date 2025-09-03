from flask import Flask, request, jsonify
import json, os
from datetime import datetime
from filelock import FileLock

app = Flask(__name__)

# --- Path Configurations ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_LINKS_DIR = os.path.join(BASE_DIR, "InputLinks")
LINKS_FILE = os.path.join(INPUT_LINKS_DIR, "links.json")

# Ensure InputLinks directory exists
os.makedirs(INPUT_LINKS_DIR, exist_ok=True)

@app.route('/add-link', methods=['POST'])
def add_link():
    # Ưu tiên lấy từ JSON, nếu không có thì lấy từ form-data
    data = request.get_json(silent=True)
    if data and "link" in data:
        link = data["link"]
    elif "link" in request.form:
        link = request.form["link"]
    else:
        return jsonify({"error": "Thiếu biến 'link'"}), 400

    if not os.path.exists(LINKS_FILE):
        os.makedirs(os.path.dirname(LINKS_FILE), exist_ok=True)
        with open(LINKS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

    with FileLock(LINKS_FILE + ".lock"):
        with open(LINKS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        for entry in data:
            if entry["url"] == link:
                if entry["status"] == "pending":
                    return jsonify({"status": "đã tồn tại, chưa đến lượt đăng"})
                elif entry["status"] == "posted":
                    return jsonify({"status": "đã tồn tại, đã đăng"})
                elif entry["status"] == "in_progress":
                    return jsonify({"status": "đã tồn tại, đang xử lý"})

        new_entry = {
            "url": link,
            "status": "pending",
            "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "posted_at": None
        }
        data.append(new_entry)

        with open(LINKS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    return jsonify({"status": "thêm thành công", "link": link})


if __name__ == '__main__':
    app.run(port=5467, debug=True)
