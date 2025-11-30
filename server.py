from flask import Flask, request, jsonify
import base64
import subprocess
import tempfile

app = Flask(__name__)

@app.route("/ocr", methods=["POST"])
def ocr():
    try:
        data = request.json
        if "image" not in data:
            return jsonify({"error": "Missing image"}), 400

        img_data = base64.b64decode(data["image"])

        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        temp.write(img_data)
        temp.close()

        output = temp.name + "_out"

        cmd = [
            "tesseract",
            temp.name,
            output,
            "-l", "ben+eng",
            "--psm", "7"
        ]

        subprocess.run(cmd, check=True)
        text = open(output + ".txt").read()

        return jsonify({"text": text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return "OCR API Running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
