from tools import analyze_blood_smear
import os
import glob

def test_model():
    # Check for specific image.png first
    if os.path.exists("0f735cca-051c-4048-a1fa-cb36f389e12f.png"):
        image_paths = ["0f735cca-051c-4048-a1fa-cb36f389e12f.png"]
    else:
        image_paths = glob.glob("*.png")
    
    if not image_paths:
        print("No images found.")
        return

    print(f"Found {len(image_paths)} images. Testing with analyze_blood_smear tool...")
    
    for img_path in image_paths:
        print(f"\n--- Testing {img_path} ---")
        try:
            # Use the tool function directly
            result = analyze_blood_smear(os.path.abspath(img_path))
            print(result)
        except Exception as e:
            print(f"Error processing {img_path}: {e}")

if __name__ == "__main__":
    test_model()
