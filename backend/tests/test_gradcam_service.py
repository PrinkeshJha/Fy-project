import pytest
import os
import shutil
from pathlib import Path
from explainability.gradcam_service import generate_gradcam, TF_AVAILABLE

# Assuming there is a synthetic placeholder image created during tests 
# or we generate a 1x1 image here to test the flow
TEST_IMG = "tests/test_gradcam_input.png"

@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup: create a dummy image for testing
    import cv2
    import numpy as np
    
    os.makedirs("tests", exist_ok=True)
    
    # Create a 224x224 green image
    img = np.zeros((224, 224, 3), dtype=np.uint8)
    img[:] = (0, 255, 0)
    cv2.imwrite(TEST_IMG, img)
    
    yield
    
    # Teardown
    if os.path.exists(TEST_IMG):
        os.remove(TEST_IMG)

@pytest.mark.skipif(not TF_AVAILABLE, reason="TensorFlow is not available")
def test_generate_gradcam_success():
    # generate_gradcam requires TF and the model to be loaded.
    # It returns a relative path like "generated/explanations/test_gradcam_input_gradcam.jpg"
    out_path = generate_gradcam(TEST_IMG)
    
    assert out_path is not None
    assert "gradcam" in out_path
    
    # Check that file actually exists on disk
    abs_out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), out_path)
    assert os.path.exists(abs_out_path)
    
    # Clean up the generated file
    if os.path.exists(abs_out_path):
        os.remove(abs_out_path)

@pytest.mark.skipif(not TF_AVAILABLE, reason="TensorFlow is not available")
def test_generate_gradcam_missing_image():
    with pytest.raises(FileNotFoundError):
        generate_gradcam("tests/does_not_exist.png")
