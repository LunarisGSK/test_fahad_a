#!/usr/bin/env python3
"""
Script to upgrade ultralytics to the correct version (8.2.103)
"""

import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and return True if successful"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"Running: {cmd}")
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def main():
    print("🔄 Upgrading ultralytics to version 8.2.103...")
    
    # First, uninstall the current version
    print("\n1. Uninstalling current ultralytics version...")
    run_command("pip uninstall ultralytics -y")
    
    # Install the specific version
    print("\n2. Installing ultralytics==8.2.103...")
    if run_command("pip install ultralytics==8.2.103"):
        print("✅ Successfully installed ultralytics==8.2.103")
    else:
        print("❌ Failed to install ultralytics==8.2.103")
        return False
    
    # Verify installation
    print("\n3. Verifying installation...")
    if run_command("pip show ultralytics"):
        print("✅ ultralytics installation verified")
    else:
        print("❌ Failed to verify ultralytics installation")
        return False
    
    print("\n✅ ultralytics upgrade completed!")
    print("Now restart your Django server to use the new version.")
    
    return True

if __name__ == "__main__":
    main()
