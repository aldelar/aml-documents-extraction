from azureml_user.parallel_run import EntryScript
from azureml.core import Run
from azure.cosmos import CosmosClient

import argparse
import os
import json

import form_recognizer_helper_SDK
#import form_recognizer_helper_REST # consider using the REST api when you need to access the very latest versions of the APIs which may not be rolled into the SDK yet (like a beta version test)

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
    
    ws = Run.get_context().experiment.workspace
    keyvault = ws.get_default_keyvault()
    #form_recognizer_helper_SDK.init(keyvault)
    form_recognizer_helper_REST.init(keyvault)

    # Cosmos
    uri = keyvault.get_secret(name='COSMOSDB-URI')
    key = keyvault.get_secret(name='COSMOSDB-KEY')
    cosmos_client = CosmosClient(uri, credential=key)
    database = cosmos_client.get_database_client('curation_docs')
    documents_container = database.get_container_client('documents')
    mappings_container = database.get_container_client('mappings')

    for item in mappings_container.query_items(query='SELECT * FROM c WHERE c.id = "form_recognizer_mapping"', enable_cross_partition_query=True):
        mapping=item['mappings']

#
def run(mini_batch):
    
    logger.info("==> form_metadata_extraction run({}).".format(mini_batch))
    
    results = []
    
    for file_path in mini_batch:
        file_name = os.path.split(file_path)[1]
        file_extension = os.path.splitext(file_name)[1]
        result = file_name + ','
        if file_extension == '.json':
            try:
                form_json = json.load(open(file_path))
                image_file_name = form_json['image_file_name']
                classification = form_json['classification']
                top1_prediction = classification[0]['tag_name']
                if(top1_prediction != 'other_docs'):
                    model_id = mapping[top1_prediction]
                    form_recognizer_output = recognize_form(image_file_name,model_id)

                    # store form metadata to Cosmos DB
                    cosmosdb_item = {}
                    cosmosdb_item['id'] = form_json['id']
                    cosmosdb_item['pdf_name'] = form_json['pdf_name']
                    cosmosdb_item['pdf_page_number'] = form_json['pdf_page_number']
                    cosmosdb_item['image_file_name'] = image_file_name
                    cosmosdb_item['classification'] = classification
                    cosmosdb_item['forms'] = form_recognizer_output
                    documents_container.upsert_item(cosmosdb_item)

                    # save FR output
                    output_file_name = os.path.join(metadata_folder,image_file_name + '.json')
                    with open(output_file_name,'w') as output_file:
                        json.dump(cosmosdb_item,output_file)
                result += top1_prediction
            except Exception as e:
                result += "failed"
                raise e
        else:
            result += 'skipped'
        results.append(result)
    
    return results
    
#
def recognize_form(image_file_name,model_id):

    # read image and call FR
    image_file_path = os.path.join(png_folder,image_file_name)
    with open(image_file_path, "rb") as image_file:
        image_data = image_file.read()
    return form_recognizer_helper_SDK.recognize_forms(model_id,image_data)
    #return form_recognizer_helper_REST.recognize_forms(model_id,image_data)