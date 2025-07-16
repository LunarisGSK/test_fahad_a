import os
import re

# Read the current settings.py file
with open('pet_face_id/settings.py', 'r') as f:
    content = f.read()

# Add environment variable loading after the imports
env_loading_code = '''
# Load environment variables from .env file
def load_env_file():
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key, value)

load_env_file()
'''

# Insert the environment loading code after the BASE_DIR line
base_dir_pattern = r'(BASE_DIR = Path\(__file__\)\.resolve\(\)\.parent\.parent)'
replacement = r'\1\n' + env_loading_code

content = re.sub(base_dir_pattern, replacement, content)

# Update SECRET_KEY to use environment variable
secret_key_pattern = r"SECRET_KEY = '[^']*'"
secret_key_replacement = "SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-!6^(l9ek#s4ngn_hn3gn(#586n!ho17^n_mnvsw-wj9&2ce&mj')"
content = re.sub(secret_key_pattern, secret_key_replacement, content)

# Update DEBUG to use environment variable
debug_pattern = r'DEBUG = True'
debug_replacement = "DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'"
content = re.sub(debug_pattern, debug_replacement, content)

# Update YOLO_MODEL_PATH to use environment variable
yolo_pattern = r"YOLO_MODEL_PATH = BASE_DIR / 'ai_models' / 'yolov8l_pet_faces\.pt'"
yolo_replacement = "YOLO_MODEL_PATH = os.getenv('YOLO_MODEL_PATH', str(BASE_DIR / 'ai_models' / 'yolov8l_pet_faces.pt'))"
content = re.sub(yolo_pattern, yolo_replacement, content)

# Write the updated settings.py file
with open('pet_face_id/settings.py', 'w') as f:
    f.write(content)

print("✅ Settings.py updated successfully!")
print("✅ Now environment variables will be loaded from .env file")
print("✅ YOLO_MODEL_PATH will use:", os.getenv('YOLO_MODEL_PATH', 'default path'))
