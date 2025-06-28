import torch
import torchvision.transforms as transforms
from PIL import Image
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from resnet50_model import resnet50
import io
import os
import random

app = FastAPI()

# Define class names
DATASET_PATH = 'assets/welding-dataset_64x64_resized'
class_names = sorted(os.listdir(DATASET_PATH))


# Load the model
model = resnet50(num_classes=len(class_names))
model.load_state_dict(torch.load('assets/models/trained_resnet50.pth', map_location=torch.device('cpu')))
model.eval()

# Define image transformations
transform = transforms.Compose([
    transforms.Resize((64, 64)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

@app.get("/classes")
async def get_classes():
    """
    Returns a list of all available class names.
    """
    return {"classes": class_names}


@app.get("/example/{class_name}")
async def get_example_image(class_name: str):
    """
    Returns an example image for a given class.
    """
    class_path = os.path.join(DATASET_PATH, class_name)
    if not os.path.isdir(class_path):
        return {"error": "Class not found"}, 404
    
    images = os.listdir(class_path)
    if not images:
        return {"error": "No images found for this class"}, 404
        
    random_image = random.choice(images)
    image_path = os.path.join(class_path, random_image)
    
    return FileResponse(image_path)


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    Receives an image file, makes a prediction, and returns the predicted class.
    """
    # Read image file
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')

    # For debugging: Save the uploaded image temporarily
    temp_image_path = 'assets/temp_uploaded_image.jpg'
    image.save(temp_image_path)

    # Transform the image and add a batch dimension
    image_tensor = transform(image).unsqueeze(0)

    # Make a prediction
    with torch.no_grad():
        outputs = model(image_tensor)
        probabilities = torch.nn.functional.softmax(outputs, dim=1)
        confidence, predicted = torch.max(probabilities, 1)
        predicted_class = class_names[predicted.item()]

    return {"prediction": predicted_class, "confidence": confidence.item() * 100}