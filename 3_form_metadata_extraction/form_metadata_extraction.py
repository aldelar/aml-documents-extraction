from azureml_user.parallel_run import EntryScript
from azureml.core import Run
from azure.cosmos import CosmosClient

import argparse
import json
import os

from PIL import Image

import form_recognizer_helper_SDK

#
def init():

    global logger
    global png_folder
    global metadata_folder
    global documents_container
    global mapping
    
    logger = EntryScript().logger
    logger.info("==> form_metadata_extraction init()")
    parser = argparse.ArgumentParser()
    parser.add_argument('--png-folder', type=str, dest='png_folder', help='png folder')
    parser.add_argument('--metadata-folder', type=str, dest='metadata_folder', help='metadata folder')
    args, unknown_args = parser.parse_known_args()
    
    png_folder = args.png_folder
    metadata_folder = args.metadata_folder
    print("png_folder:", png_folder)
    print("metadata_folder:", metadata_folder)
    
    ws = Run.get_context().workspace
    keyvault = ws.get_default_keyvault()
    form_recognizer_helper_SDK.init(keyvault)
    
    url = keyvault.get_secret(name='COSMOSDB-URI')
    key = keyvault.get_secret(name='COSMOSDB-KEY')
    cosmos_client = CosmosClient(url, credential=key)
    
    database = cosmos_client.get_database_client('curation_docs')
    documents_container = database.get_container_client('documents')
    mappings_container = database.get_container_client('mappings')

    for item in mappings_container.query_items(query='SELECT * FROM c WHERE c.id = "form_recognizer_mapping"', enable_cross_partition_query=True):
        mapping=item
#
def run(mini_batch):
    
    logger.info("==> form_metadata_extraction run({}).".format(mini_batch))
    
    results = []
    for form_json_path in mini_batch:
        form_json = json.load(form_json_path)
        image_file_name = form_json['image_file_name']
        top1_prediction = form_json['classification'][0]['tag_name']
        results.append(image_file_name + ',' + top1_prediction)
        
        if(top1_prediction != 'other_docs'):
            model_id = mapping[top1_prediction]
            recognize_form(image_file_name,model_id,form_json['id'])
        
    return results
    
#
def recognize_form(image_file_name,model_id,document_id):
    image_file_path = os.join(png_folder,image_file_name)
    image_data = Image.open(image_file_path, 'r')
    
    form_recognizer_output = form_recognizer_helper_SDK.recognize_forms(model_id,image_data)
    print(f"   > classify_form, item: ({item_info})")

    # store form metadata to Cosmos DB
    cosmosdb_item = {}
    cosmosdb_item['id'] = document_id
    cosmosdb_item['forms'] = form_recognizer_output
    documents_container.upsert_item(func.Document.from_json(json.dumps(cosmosdb_item)))
    
    output_file_name = os.path.join(metadata_folder,image_file_name + '.json')
    with open(output_file_name,'w') as output_file:
        json.dump(cosmosdb_item,output_file)