#!/usr/bin/env python3
"""
Clean up lock files in the project
"""
import os
import sys

def main():
    """Main entry point"""
    # Change to the project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    
    print("Cleaning up lock files...")
    
    # Remove old lockfile
    if os.path.exists("uv.lock"):
        print("Removing old uv.lock file...")
        os.remove("uv.lock")
        print("Old lockfile removed")
    
    if os.path.exists("uv.lock.old"):
        print("Removing old uv.lock.old file...")
        os.remove("uv.lock.old")
        print("Old backup lockfile removed")
    
    print("\nLockfiles removed; to regenerate the lockfile, run:")
    print("uv pip compile -o uv.lock pyproject.toml")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
