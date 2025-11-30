from flask import Flask, request, jsonify
import base64
import subprocess
import tempfile
import cv2
import numpy as np

app = Flask(__name__)

def preprocess(image_bytes):
    # Convert to OpenCV array
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # Resize (Tesseract works better with large text)
    img = cv2.resize(img, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)

    # Convert to Gray
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Remove noise
    gray = cv2.medianBlur(gray, 3)

    # Binary thresholding
    _, thresh = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY_INV)

    # Remove thin lines (CAPTCHA lines)
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)

    # Convert clean image back to bytes
    _, processed_bytes = cv2.imencode(".png", cleaned)

    return processed_bytes.tobytes()

@app.route("/ocr", methods=["POST"])
def ocr():
    try:
        data = request.json
        if "image" not in data:
            return jsonify({"error": "Missing image"}), 400

        # Decode base64
        img_data = base64.b64decode(data["image"])

        # Preprocess image
        processed = preprocess(img_data)

        # Save image
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        temp.write(processed)
        temp.close()

        # Output path
        output = temp.name + "_out"

        # Run Tesseract
        cmd = [
            "tesseract",
            temp.name,
            output,
            "-l", "ben+eng",
            "--oem", "1",
            "--psm", "7"
        ]

        subprocess.run(cmd, check=True)
        text = open(output + ".txt").read().strip()

        return jsonify({"text": text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return "OCR API Running Perfectly with Advanced Preprocessing!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
