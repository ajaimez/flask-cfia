from flask import Flask, flash, request, redirect, url_for, render_template, json,jsonify
from markupsafe import Markup
import urllib.request
import os
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException
from datetime import timezone 
import datetime 

# import cv2  # OpenCV for image processing
# import matplotlib.pyplot as plt  # Matplotlib for visualization
import numpy as np  # NumPy for numerical operations
import easyocr  # EasyOCR for text extraction from images

import PyPDF2

import xml.etree.ElementTree as ET

import ssl
ssl._create_default_https_context = ssl._create_stdlib_context

import logging
logging.basicConfig(filename="error.log",level=logging.DEBUG)

app = Flask(__name__)
 
UPLOAD_FOLDER = "static/uploads/"
 
app.secret_key = "secret key"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
 
ALLOWED_EXTENSIONS = set(["png", "jpg", "jpeg"])
ALLOWED_EXTENSIONS_PDF = set(["pdf"])
ALLOWED_EXTENSIONS_XML = set(["xml"])

def returnJSON_OK(claveNumerica,nombreArchivo,extension):
    _returnData = { 
                    "data" : {
                            "claveNumerica" : claveNumerica,
                            "fechaConsulta" : datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                            "nombreArchivo" : nombreArchivo,
                            "extension" : extension
                        },
                     "mensaje" : {
                         "codigo" : 1,
                         "descripcion" : ""
                     }
                    }
    return jsonify(_returnData)

def returnJSON_ERROR(erroDescripcion):
    _returnData = { 
            "data" : "",
                     "mensaje" : {
                         "codigo" : -1,
                         "descripcion" : erroDescripcion
                     }
        }
    return jsonify(_returnData)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_file_pdf(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS_PDF
     
def allowed_file_xml(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS_XML
 
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/pdf")
def homepdf():
    return render_template("indexpdf.html")

@app.route("/xml")
def homexml():
    return render_template("indexxml.html")

@app.route("/xml", methods=["POST"])
def upload_xml():
    if "file" not in request.files:
        return returnJSON_ERROR("No file part")
    file = request.files["file"]
    if file.filename == "":
        return returnJSON_ERROR("No XML selected for uploading")
    if file and allowed_file_xml(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        clave = XMLProcess(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        return returnJSON_OK(clave,file.filename,"XML") 
    else:
        return returnJSON_ERROR("ERROR Allowed XML")    

@app.route("/pdf", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:        
        return  returnJSON_ERROR("No file part")
    file = request.files["file"]
    if file.filename == "":
        return returnJSON_ERROR("No PDF selected for uploading")
    if file and allowed_file_pdf(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        clave = PDFProcess(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        return returnJSON_OK(clave , file.filename , "PDF") 
    else:        
        return returnJSON_ERROR("ERROR Allowed PDF") 

@app.route("/image", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return  returnJSON_ERROR("No file part")
    file = request.files["file"]
    if file.filename == "":        
        return returnJSON_ERROR("No image selected for uploading")
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        clave = OCRProces(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        return returnJSON_OK(clave , file.filename , filename.rsplit(".", 1)[1].lower())
    else:        
        return returnJSON_ERROR("ERROR Allowed image types are - png, jpg, jpeg")
 
@app.route("/display/<filename>")
def display_image(filename):
    #print("display_image filename: " + filename)
    return redirect(url_for("static", filename="uploads/" + filename), code=301)


def XMLProcess(xml_path):
    # document = parse(xml_path)
    # print(document.getElementsByTagName("//Clave"))

    root = ET.parse(xml_path)
    parsed_dict = dict()
    for child in root.iter():
        # print(child.text)
        nodetext = str(child.text)
        if nodetext.startswith("506") and len(nodetext) > 45:    
            return nodetext

    return "NO DATA"

def PDFProcess(pdf_payh):
    pdfFileObject = open(pdf_payh,"rb")

    pdfReader = PyPDF2.PdfReader(pdfFileObject)

    page0  = pdfReader.pages[0]

    data = page0.extract_text()

    res = data.split()

    for item in res:
        print(item)
        item = getNumeric(item)
        if item.startswith("506") and len(item) > 45:
            return getNumeric(item)

    return "NO DATA"


def OCRProces(image_path):
    print(image_path)
    # Reading the image
    # image = cv2.imread(image_path)

    # Initializing the EasyOCR reader with English language support and GPU disabled
    reader = easyocr.Reader(["la","es"], gpu=False, model_storage_directory = "easyocr_model",user_network_directory=False)

    # Extracting text from the image
    results = reader.readtext(image_path)

    arr_str = [] 

    # Displaying the extracted results
    for detection in results:
        # if detection[1].startswith("Clave"): #or detection[1].startswith("506") :
        #     print(detection[1])
        #     break
        if "Clave" in detection[1]:
            arr_str.append(detection[1])

        if detection[1].startswith("506"):            
            if(len(detection[1])>45):
                arr_str.append(detection[1])
                break
        print(detection)

    claves = ""

    for item in arr_str:
        claves += item + " "

    if claves == "":
        return "NO DATA"
    else:
        return getNumeric(claves)

def getNumeric(data):
    _data = ""
    for i in data.split():
        #print(i)
        if i.isnumeric():
            _data += str(i)
    return _data


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
