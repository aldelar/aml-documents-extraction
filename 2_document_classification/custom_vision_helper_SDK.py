from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from msrest.authentication import ApiKeyCredentials

import os, requests, json
from PIL import Image
from io import BytesIO

def init(keyvault):
    
    global cv_project_id
    global cv_iteration_published_name
    global ocr_url
    global headers
    global params
    global predictor
    
    # custom vision project
    cv_project_id = keyvault.get_secret(name='CUSTOM-VISION-PROJECT-ID')
    cv_iteration_published_name = keyvault.get_secret(name='CUSTOM-VISION-ITERATION-PUBLISHED-NAME')
  
    # initialize client
    endpoint = keyvault.get_secret(name='COGNITIVE-SERVICES-ENDPOINT')
    ocr_url  = endpoint + "vision/v2.1/ocr"
    apim_key = keyvault.get_secret(name='COGNITIVE-SERVICES-SUBSCRIPTION-KEY')
    headers = { 'Ocp-Apim-Subscription-Key': apim_key, 'Content-Type': 'application/octet-stream' }
    params = {'language': 'unk', 'detectOrientation': 'true'}
    prediction_credentials = ApiKeyCredentials(in_headers={"Prediction-key": apim_key})
    predictor = CustomVisionPredictionClient(endpoint,prediction_credentials)

# image_to_byte_array
def image_to_byte_array(image:Image):
  imgByteArr = BytesIO()
  image.save(imgByteArr, format='PNG')
  imgByteArr = imgByteArr.getvalue()
  return imgByteArr

#
def predict_form(form):

    # ocr to get rotation metadata
    response = requests.post(ocr_url, headers=headers, params=params, data = form)
    response.raise_for_status()
    analysis = response.json()
    
    # get rotation angle and rotate image
    orientation = analysis.get('orientation')
    if(orientation != None): #rotate only if orientation detected        
        if(orientation == 'Left'):
            base_rotate = -90
        elif(orientation == 'Down'):
            base_rotate = -180
        elif(orientation == 'Right'):
            base_rotate = -270
        else:
            base_rotate = 0
        image_angle = analysis.get('textAngle')
        rotation = base_rotate-image_angle*180/3.14159
        image = Image.open(BytesIO(form))
        form_data = image_to_byte_array(image.rotate(rotation))
    image_prediction = predictor.classify_image(cv_project_id, cv_iteration_published_name, form_data)
    predictions = image_prediction.predictions

    # format predictions
    predictions_output = []
    top_prob=None
    top1_prediction='other_docs'
    for p in predictions:
        if not top_prob:
            top_prob = p.probability
            top1_prediction = p.tag_name
        prediction = {}
        prediction['tag_name'] = p.tag_name
        prediction['probability'] = p.probability
        predictions_output.append(prediction)

    return predictions_output

# unit test
if __name__ == '__main__':
    with open("image.png", "rb") as fd:
        form = fd.read()
    predictions_output = predict_form(form=form)
    print(predictions_output)