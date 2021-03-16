from azureml_user.parallel_run import EntryScript
from azureml.core import Run

import argparse
import os
import time
import json
from PIL import Image

import custom_vision_helper_SDK

#
def init():

    global documents_folder
    global logger

    logger = EntryScript().logger
    logger.info("==> document_classification init()")
    parser = argparse.ArgumentParser()
    parser.add_argument('--documents-folder', type=str, dest='documents_folder', help='documents folder')
    
    args, unknown_args = parser.parse_known_args()
    
    documents_folder = args.documents_folder
    print("documents_folder:", documents_folder)
    
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
            classify_document(file_path)
            result += "classified"
        else:
            result += "skipped"
        results.append(result)

    return results
    
def classify_document(png_file_path):
    # run Custom Vision model to identify form type
    start_time = time.time()
    im = Image.open(png_file_path)
    cv_results = custom_vision_helper_SDK.predict_form(im)
    runtime = round(time.time() - start_time,2)
    print(f"   > classify_form, item: ({item_info}) -> Custom Vision execution: {runtime} seconds")
    
    image_file_name = os.path.basename(png_file_path)
    json_file_name = os.path.split(image_file_name)[0]+'.json'
    
    classified_document = {"id": pdf_name+'-'+pdf_page_number, "pdf_name": pdf_name, "pdf_page_number": pdf_page_number, "image_file_name" : image_file_name, "classification": cv_results }
    output_file_name = os.path.join(documents_folder, json_file_name)
        
    with open(output_file_name,'w') as output_file:
        json.dump(classified_document,output_file)