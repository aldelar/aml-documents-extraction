from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import FormRecognizerClient, FormRecognizerApiVersion

import os

def init(keyvault):
    
    global form_recognizer_client
    
    # initialize client
    endpoint   = keyvault.get_secret(name='FORM-RECOGNIZER-ENDPOINT')
    credential = keyvault.get_secret(name='FORM-RECOGNIZER-SUBSCRIPTION-KEY')
    form_recognizer_client = FormRecognizerClient(endpoint, credential)

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

# unit test
if __name__ == '__main__':
    for version in FormRecognizerApiVersion:
        print(f"API Version: {version}")
    with open("image.png", "rb") as fd:
        form = fd.read()
    recognized_output = recognize_forms(model_id="1050d11d-06e5-4ae5-a43c-443c6636f5f5",form=form)
    print(recognized_output)