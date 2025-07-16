#!/usr/bin/env python3
"""
Test script to verify YOLO model loading
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pet_face_id.settings')
django.setup()

from django.conf import settings
from ultralytics import YOLO

def test_yolo_model():
    """Test loading the YOLO model"""
    print("🧪 Testing YOLO Model Loading...")
    print(f"Model path: {settings.YOLO_MODEL_PATH}")
    print(f"Model exists: {os.path.exists(settings.YOLO_MODEL_PATH)}")
    
    try:
        # Try to load the model
        model = YOLO(settings.YOLO_MODEL_PATH)
        print("✅ Successfully loaded YOLO model!")
        print(f"Model type: {type(model)}")
        
        # Test model info
        print("\n📊 Model Information:")
        print(f"Model names: {model.names}")
        print(f"Device: {model.device}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to load YOLO model: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_ultralytics_version():
    """Check ultralytics version"""
    try:
        import ultralytics
        print(f"🔍 ultralytics version: {ultralytics.__version__}")
        
        # Check if it's the correct version
        if ultralytics.__version__ == "8.2.103":
            print("✅ Correct ultralytics version!")
            return True
        else:
            print("⚠️  Version mismatch! Expected 8.2.103")
            return False
            
    except Exception as e:
        print(f"❌ Error checking ultralytics version: {e}")
        return False

def main():
    print("🚀 YOLO Model Test Script")
    print("=" * 50)
    
    # Check ultralytics version
    version_ok = check_ultralytics_version()
    
    if not version_ok:
        print("\n💡 To fix version issues, run:")
        print("python upgrade_ultralytics.py")
        return
    
    # Test YOLO model loading
    model_ok = test_yolo_model()
    
    if model_ok:
        print("\n✅ All tests passed! YOLO model is ready to use.")
    else:
        print("\n❌ YOLO model test failed. Check the error messages above.")

if __name__ == "__main__":
    main()
