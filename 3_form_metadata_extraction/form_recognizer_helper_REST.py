from azure.core.credentials import AzureKeyCredential

import os,json,time
from requests import get, post

def init(keyvault):
    
    # 
    global apim_key
    global params
    global headers
    global endpoint
    global analyze_url_template

    # initialize client
    apim_key = keyvault.get_secret(name='COGNITIVE-SERVICES-SUBSCRIPTION-KEY')
    print(f"apim_key: {apim_key}")
    params   = { "includeTextDetails": True }
    headers  = { 'Content-Type': 'image/png', 'Ocp-Apim-Subscription-Key': apim_key }
    endpoint = keyvault.get_secret(name='COGNITIVE-SERVICES-ENDPOINT')
    print(f"endpoint: {endpoint}")
    api_version = keyvault.get_secret(name='FORM-RECOGNIZER-API-VERSION')
    analyze_url_template = endpoint + "/formrecognizer/" + api_version + "/custom/models/{model_id}/analyze"


# recognize_forms
def recognize_forms(model_id, form):

    # post form analysis request
    try:
        analyze_url = analyze_url_template.format(model_id=model_id)
        print(f"analyze_url: {analyze_url}")
        resp = post(url = analyze_url, data = form, headers = headers, params = params)
        if resp.status_code != 202:
            raise Exception("POST analyze failed:\n%s" % json.dumps(resp.json()))
        print("POST analyze succeeded:\n%s" % resp.headers)
        analyze_results_url = resp.headers["operation-location"]
        print(f"analyze_results_url: {analyze_results_url}")
    except Exception as e:
        raise Exception("POST analyze failed:\n%s" % str(e))

    # poll until response available
    n_tries = 15
    n_try = 0
    wait_sec = 5
    max_wait_sec = 60
    resp_json = None
    while n_try < n_tries:
        try:
            resp = get(url = analyze_results_url, headers = {"Ocp-Apim-Subscription-Key": apim_key})
            resp_json = resp.json()
            if resp.status_code != 200:
                raise Exception("GET analyze results failed:\n%s" % json.dumps(resp_json))
            status = resp_json["status"]
            if status == "succeeded":
                print("Analysis succeeded")
                break
            if status == "failed":
                raise Exception("Analysis failed:\n%s" % json.dumps(resp_json))
            # Analysis still running. Wait and retry.
            print(f"Waiting for response for {wait_sec} secs...")
            time.sleep(wait_sec)
            n_try += 1
            wait_sec = min(2*wait_sec, max_wait_sec)
        except Exception as e:
            raise Exception("GET analyze results failed:\n%s" % str(e))

    # process response
    recognized_output = []
    if resp_json:
        for recognized_form in resp_json["analyzeResult"]["documentResults"]:
            fields = recognized_form["fields"]
            recognized_fields = []
            for field_name in fields:
                field = fields[field_name]
                if field:
                    value = field['valueString'] if 'valueString' in field else field['text']
                    recognized_fields.append({ "name": field_name, "type": field['type'], "text": field['text'], "value": value, "confidence": field['confidence'] })
        recognized_output.append({ "form_type": recognized_form['docType'], "fields": recognized_fields})
    
    return recognized_output