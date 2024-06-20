from flask import Flask, request, jsonify, render_template

import cv2
import os

from ultralytics import YOLO

import pytesseract
import PIL.Image

from pyaadhaar.utils import Qr_img_to_text, isSecureQr
from pyaadhaar.decode import AadhaarSecureQr
from pyaadhaar.decode import AadhaarOldQr

import base64
from io import BytesIO
from PIL import Image
import re
import shutil

MODEL_PATH = './temp/best.pt'
LABEL_PATH = './runs/detect/predict/labels/'

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# Load YOLO model
model = YOLO(MODEL_PATH)

@app.route("/verify_aadhar", methods=["POST"])
def verify_aadhar():
    # Get uploaded file
    base64_data = request.get_json().get("image")

    binary_data = base64.b64decode(base64_data)

    image = Image.open(BytesIO(binary_data))

    temp_dir = './temp'
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    file_path = os.path.join(temp_dir, 'aadhar_img.jpg')
    image.save(file_path)

    # Object detection using YOLO
    model.predict(file_path, save=True, imgsz=640, conf=0.25,save_txt=True)

    class_ids = []
    # checking the class_id
    if os.path.exists(LABEL_PATH):
        txt_files = [os.path.join(LABEL_PATH, file) for file in os.listdir(LABEL_PATH) if file.endswith('.txt')]
        if len(txt_files)==1:
            label_file = txt_files[0]
            with open(label_file,'r') as f:
                for line in f:
                    class_ids.append(line.split()[0])

    detects = []
    #Mapping classes
    if class_ids:
        with open('./temp/classes.txt','r') as f:
            for line in f:
                dat = line.split()
                if dat[0] in class_ids:
                    detects.append(dat[1])
    

    myconfig=r"--psm 6 --oem 3"

    # Extract text using Tesseract OCR
    text=pytesseract.image_to_string(PIL.Image.open(file_path),config=myconfig)

    fields_from_text = extract_fields_from_text(text)

    # Decode QR code
    try:
        isSecure, qr_data = data_from_QR(file_path)
    except qrcode.QRCodeDecodeError:
        qr_data = None

    # Removing temporary files
    #Removing the ./runs/... directory
    try:
        if os.path.exists('./runs') and os.path.isdir('./runs'):
            shutil.rmtree('./runs')
        
        if os.path.exists('./temp/aadhar_img.jpg'):
            os.remove('./temp/aadhar_img.jpg')

        if os.path.exists('QR_img.png'):
            os.remove('QR_img.png')
    except OSError as e:
        pass

    

    # Return result
    return jsonify({
        "status": "valid" if (len(detects)==4 or len(detects)==3) else "invalid",
        "detects": detects,
        "extracted_text": text,
        "fields_from_text":fields_from_text,
        "qr_data": qr_data
    })

def extract_fields_from_text(text):
    # Define regular expressions for extracting fields
    name_pattern = re.compile(r'name: (\w+ \w+)')
    gender_pattern = re.compile(r'gender: (\w+)')
    dob_pattern = re.compile(r'dob: (\d{2}/\d{2}/\d{4})')
    aadhar_pattern = re.compile(r'aadhaar_last_4_digit: (\d{12})')

    # Extract fields from text using regular expressions
    name_match = name_pattern.search(text)
    gender_match = gender_pattern.search(text)
    dob_match = dob_pattern.search(text)
    aadhar_match = aadhar_pattern.search(text)

    # Return a dictionary containing the extracted fields
    fields = {
        'Name': name_match.group(1) if name_match else None,
        'Gender': gender_match.group(1) if gender_match else None,
        'DOB': dob_match.group(1) if dob_match else None,
        'Last4Aadhar': aadhar_match.group(1)[-4:] if aadhar_match else None,
    }

    return fields

def data_from_QR(image_file_name):
    img = cv2.imread(image_file_name, cv2.IMREAD_GRAYSCALE)  # Read image as grayscale.
    img2 = cv2.resize(img, (img.shape[1]*2, img.shape[0]*2), interpolation=cv2.INTER_LANCZOS4)  # Resize by x2 using LANCZOS4 interpolation method.

    cv2.imwrite('QR_img.png', img2)

    #qrData = Qr_img_to_text(image_file_name)
    qrData = Qr_img_to_text('QR_img.png')
    #print(qrData)
    # print(qrData[0])
    isSecureQR = False
    decoded_secure_qr_data = None
    if len(qrData) == 0:
        print(" No QR Code Detected !!")
    else:
        isSecureQR = (isSecureQr(qrData[0]))
        secure_qr = AadhaarSecureQr(int(qrData[0]))
        decoded_secure_qr_data = secure_qr.decodeddata()
        print(decoded_secure_qr_data)
    return isSecureQR,decoded_secure_qr_data

if __name__ == "__main__":
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
