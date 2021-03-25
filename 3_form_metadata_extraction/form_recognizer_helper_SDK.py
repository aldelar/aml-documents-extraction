from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import FormRecognizerClient, FormRecognizerApiVersion

import os

def init(keyvault):
    
    global form_recognizer_client
    
    # initialize client
    endpoint   = keyvault.get_secret(name='FORM-RECOGNIZER-ENDPOINT')
    credential = AzureKeyCredential(keyvault.get_secret(name='FORM-RECOGNIZER-SUBSCRIPTION-KEY'))
    api_version = "2.1-preview.2" # TODO: define secret and use this code --> keyvault.get_secret(name='FORM-RECOGNIZER-API-VERSION')
    form_recognizer_client = FormRecognizerClient(endpoint, credential, api_version=api_version)

# recognize_forms
def recognize_forms(model_id, form):
    poller = form_recognizer_client.begin_recognize_custom_forms(model_id=model_id, form=form)
    results = poller.result()
    recognized_output = []
    for recognized_form in results:
        recognized_fields = []
        for field_name, field in recognized_form.fields.items():
            if field.value_data:
                recognized_fields.append({ "name": field_name, "type": field.value_type, "text": field.value_data.text, "value": str(field.value), "confidence": field.confidence })
        recognized_output.append({ "form_type": recognized_form.form_type, "fields": recognized_fields})
    return recognized_output