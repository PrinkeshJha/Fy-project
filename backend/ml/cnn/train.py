import os
import json
from pathlib import Path

# Fallback wrapper around tensorflow imports for testing environments
try:
    import tensorflow as tf
    from tensorflow.keras.applications import MobileNetV2
    from tensorflow.keras.layers import GlobalAveragePooling2D, Dense, Input
    from tensorflow.keras.models import Model
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    from tensorflow.keras.callbacks import EarlyStopping
    from PIL import Image, ImageDraw
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

CNN_DIR = Path(__file__).parent
DATASET_DIR = CNN_DIR.parent.parent / "dataset" / "cnn dataset"
MODEL_PATH = CNN_DIR / "model.keras"

def train():
    if not TF_AVAILABLE:
        print("TensorFlow is not installed. Skipping training.")
        return
        
    print("Training on real screenshot dataset...")

    # Data generators
    datagen = ImageDataGenerator(rescale=1./255, validation_split=0.2)
    
    train_generator = datagen.flow_from_directory(
        DATASET_DIR,
        target_size=(224, 224),
        batch_size=8,
        class_mode='categorical',
        subset='training'
    )
    
    val_generator = datagen.flow_from_directory(
        DATASET_DIR,
        target_size=(224, 224),
        batch_size=8,
        class_mode='categorical',
        subset='validation'
    )

    # Build model using Transfer Learning
    base_model = MobileNetV2(weights='imagenet', include_top=False, input_tensor=Input(shape=(224, 224, 3)))
    base_model.trainable = False  # Freeze base layers
    
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    predictions = Dense(3, activation='softmax')(x)
    
    model = Model(inputs=base_model.input, outputs=predictions)
    
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    
    early_stop = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)
    
    print("Starting training...")
    model.fit(
        train_generator,
        validation_data=val_generator,
        epochs=10,
        callbacks=[early_stop]
    )
    
    model.save(MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    train()
