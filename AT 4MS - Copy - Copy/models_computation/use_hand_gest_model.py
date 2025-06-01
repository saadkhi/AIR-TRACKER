import tensorflow as tf
import numpy as np
import argparse
import sys
import os
from PIL import Image
import matplotlib.pyplot as plt

def load_model():
    model_path = "models_computation/Hand_Gest_Model.keras"
    """Load a Keras model from file."""
    try:
        model = tf.keras.models.load_model(model_path)
        print(f"Model loaded from {model_path}")
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        sys.exit(1)

def preprocess_image(image_path, target_size=(64, 64)):
    """
    Load and preprocess an image for the model.
    Args:
        image_path (str): Path to the image file.
        target_size (tuple): Desired image size (width, height).
    Returns:
        np.ndarray: Preprocessed image array.
    """
    try:
        img = Image.open(image_path).convert('RGB')
        img = img.resize(target_size)
        img_array = np.array(img) / 255.0  # Normalize to [0,1]
        img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
        print(f"Image loaded and preprocessed: {image_path}")
        return img_array
    except Exception as e:
        print(f"Error processing image: {e}")
        sys.exit(1)

def predict(model, img_array):
    """Run prediction on the preprocessed image."""
    prediction = model.predict(img_array)
    print("Raw prediction:", prediction)
    return prediction

def visualize(image_path, prediction, class_names=None):
    """Display the image and prediction result."""
    img = Image.open(image_path)
    plt.imshow(img)
    plt.axis('off')
    if class_names is not None:
        pred_label = class_names[np.argmax(prediction)]
        plt.title(f"Prediction: {pred_label}")
    else:
        plt.title(f"Prediction: {np.argmax(prediction)}")
    plt.show()

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Hand Gesture Model Inference")
    parser.add_argument('--image', type=str, required=True, help='Path to input image')
    parser.add_argument('--model', type=str, default='Hand_Gest_Model.keras', help='Path to model file')
    parser.add_argument('--classes', type=str, default='', help='Comma-separated class names')
    return parser.parse_args()

def main():
    args = parse_args()
    if not os.path.exists(args.image):
        print(f"Image file not found: {args.image}")
        sys.exit(1)
    if not os.path.exists(args.model):
        print(f"Model file not found: {args.model}")
        sys.exit(1)

    class_names = args.classes.split(',') if args.classes else None

    model = load_model(args.model)
    img_array = preprocess_image(args.image, target_size=(64, 64))
    prediction = predict(model, img_array)
    visualize(args.image, prediction, class_names)

if __name__ == "__main__":
    main()