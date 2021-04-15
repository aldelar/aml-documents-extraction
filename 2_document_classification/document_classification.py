from azureml_user.parallel_run import EntryScript
from azureml.core import Run

import argparse
import os
import json

import custom_vision_helper_SDK

from PIL import Image
from io import BytesIO

#
def init():

    global classification_folder
    global logger

    logger = EntryScript().logger
    logger.info("==> document_classification init()")
    parser = argparse.ArgumentParser()
    parser.add_argument('--classification-folder', type=str, dest='classification_folder', help='classification folder')
    
    args, unknown_args = parser.parse_known_args()
    
    classification_folder = args.classification_folder
    print("classification_folder:", classification_folder)
    
    ws = Run.get_context().experiment.workspace
    keyvault = ws.get_default_keyvault()
    custom_vision_helper_SDK.init(keyvault)

#
def run(mini_batch):
    
    logger.info("==> document_classification run({}).".format(mini_batch))
    
    results = []

    for file_path in mini_batch:
        file_name = os.path.split(file_path)[1]
        file_extension = os.path.splitext(file_name)[1]
        result = file_name + ','
        if file_extension == '.png':
            try:
                classify_document(file_path)
                result += "classified"
            except Exception as e:
                result += "failed"
                raise e
        else:
            result += "skipped"
        results.append(result)

    return results
    
def classify_document(png_file_path):
    # run Custom Vision model to identify form type
    
    #Resize image for custom vision if needed
    im = Image.open(png_file_path)
    image_as_bytes = BytesIO()
    im.save(image_as_bytes, 'png')
    image_file_size = image_as_bytes.tell()
    resize = False
    while(image_file_size >= 4000000): #Custom vision has a 4 MB limit for prediction images
        image_as_bytes = BytesIO()
        width, height = im.size
        width = int(0.9*width)
        height = int(0.9*height)
        im = im.resize([width,height])
        im.save(image_as_bytes, 'png')
        image_file_size = image_as_bytes.tell()
        resize = True
    
    image_file_name = os.path.basename(png_file_path)
    json_file_name = os.path.splitext(image_file_name)[0]+'.json'
    
    if resize:
        png_file_path = "downsized_" + image_file_name
        im.save(png_file_path)
    
    with open(png_file_path, "rb") as png_file:
        im = png_file.read()
    
    cv_results = custom_vision_helper_SDK.predict_form(im)

    [pdf_basename,pdf_basepage] = image_file_name.rsplit('_p')
    pdf_name = pdf_basename + '.pdf'
    pdf_page_number = int(pdf_basepage.rsplit('.')[0])
    
    classified_document = {"id": pdf_name+'-p'+str(pdf_page_number), "pdf_name": pdf_name, "pdf_page_number": pdf_page_number, "image_file_name" : image_file_name, "classification": cv_results }
    output_file_name = os.path.join(classification_folder, json_file_name)
       
    with open(output_file_name,'w') as output_file:
        json.dump(classified_document,output_file)