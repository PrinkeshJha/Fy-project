import os
import cv2
import numpy as np
from pathlib import Path

try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

from ml.cnn.predict import model as cnn_model, preprocess_image

EXPLANATIONS_DIR = Path(__file__).parent.parent / "generated" / "explanations"
# Ensure the directory exists
EXPLANATIONS_DIR.mkdir(parents=True, exist_ok=True)

# The last conv layer in MobileNetV2 before pooling is usually 'out_relu'
TARGET_LAYER_NAME = "out_relu" 

def generate_gradcam(image_path: str) -> str:
    """
    Generates a Grad-CAM heatmap for the given image, overlays it on the original,
    and saves the result.
    
    Returns:
        The relative path to the generated heatmap image.
    """
    if not TF_AVAILABLE:
        raise RuntimeError("TensorFlow is not available.")
    
    if cnn_model is None:
        raise RuntimeError("CNN model is not loaded.")
        
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at {image_path}")

    # 1. Preprocess image using existing logic
    # preprocess_image returns shape (1, 224, 224, 3)
    img_array = preprocess_image(image_path)
    
    # Extract the base model from the full model
    # Our model architecture in train.py was: base_model + GlobalAveragePooling2D + Dense
    # The first layer is the base_model (Functional API). We need to access its internal layer.
    base_model = cnn_model.layers[0]
    
    try:
        target_layer = base_model.get_layer(TARGET_LAYER_NAME)
    except ValueError:
        raise ValueError(f"Could not find layer '{TARGET_LAYER_NAME}' in base model.")
        
    # 2. Create a model that maps the input image to the activations of the target layer 
    # as well as the output predictions.
    # Note: We need the full model's prediction, but the intermediate activations come from the base model.
    # Since base_model is a layer in the full model, we build a gradient model across both.
    
    # We create a new model whose inputs are the base_model's inputs
    # and whose outputs are both the target layer's output AND the final model's output
    # Since our full model wraps the base model, we can just use the base_model input directly.
    grad_model = tf.keras.models.Model(
        inputs=[base_model.inputs],
        outputs=[target_layer.output, cnn_model.output]
    )
    
    # 3. Compute gradients
    with tf.GradientTape() as tape:
        # Cast image to float32 just in case
        inputs = tf.cast(img_array, tf.float32)
        conv_outputs, predictions = grad_model(inputs)
        
        # We only have one output unit (binary classification), so we compute gradients of this unit
        # w.r.t the feature map
        loss = predictions[:, 0]
        
    # Extract gradients and feature maps
    grads = tape.gradient(loss, conv_outputs)
    
    # Average gradients spatially
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    
    # Weight the feature maps by the gradients
    conv_outputs = conv_outputs[0]
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    
    # Apply ReLU (discard negative values)
    heatmap = tf.maximum(heatmap, 0)
    
    # Normalize heatmap
    max_val = tf.math.reduce_max(heatmap)
    if max_val != 0:
        heatmap /= max_val
    heatmap = heatmap.numpy()
    
    # 4. Generate the overlay image
    # Load original image using OpenCV
    original_img = cv2.imread(image_path)
    if original_img is None:
        raise ValueError(f"Could not read image file {image_path} with cv2")
        
    # Resize heatmap to match original image dimensions
    heatmap_resized = cv2.resize(heatmap, (original_img.shape[1], original_img.shape[0]))
    
    # Convert heatmap to RGB mapping
    heatmap_uint8 = np.uint8(255 * heatmap_resized)
    heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    
    # Blend: 60% original, 40% heatmap
    overlay = cv2.addWeighted(original_img, 0.6, heatmap_colored, 0.4, 0)
    
    # 5. Save the result
    filename = Path(image_path).stem + "_gradcam.jpg"
    out_path = EXPLANATIONS_DIR / filename
    
    cv2.imwrite(str(out_path), overlay)
    
    # Return relative path to backend root
    root_dir = Path(__file__).parent.parent
    return out_path.relative_to(root_dir).as_posix()
