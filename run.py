#!/usr/bin/env python3

import os
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Import and run the main function
from image_resizer.main import main

if __name__ == "__main__":
    main()