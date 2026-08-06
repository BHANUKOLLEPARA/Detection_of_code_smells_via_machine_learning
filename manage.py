#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import threading
import webbrowser
import time
from django.core.management.commands.runserver import Command as runserver


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    
    # Add custom startup message
    if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
        print("""
        ╔══════════════════════════════════════════════════════════╗
        ║                                                          ║
        ║     ██████╗ ██████╗ ██████╗ ███████╗███████╗███╗   ███╗ ║
        ║    ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝████╗ ████║ ║
        ║    ██║     ██║   ██║██║  ██║█████╗  ███████╗██╔████╔██║ ║
        ║    ██║     ██║   ██║██║  ██║██╔══╝  ╚════██║██║╚██╔╝██║ ║
        ║    ╚██████╗╚██████╔╝██████╔╝███████╗███████║██║ ╚═╝ ██║ ║
        ║     ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚══════╝╚═╝     ╚═╝ ║
        ║                                                          ║
        ║              CodeSmell Detector v1.0                     ║
        ║         AI-Powered Code Quality Analysis                 ║
        ║                                                          ║
        ╚══════════════════════════════════════════════════════════╝
        """)
        
        # Auto-open browser in development
        def open_browser():
            """Wait a bit and then open the browser."""
            wait_time = 1.5
            time.sleep(wait_time)
            webbrowser.open_new('http://127.0.0.1:8000/')
        
        threading.Timer(1, open_browser).start()
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: CodeSmell Detector requires Python 3.8 or higher.")
        sys.exit(1)
    
    # Check Django version and dependencies
    try:
        import django
        print(f"✓ Django version: {django.get_version()}")
    except ImportError:
        print("✗ Django not found. Please run: pip install -r requirements.txt")
        sys.exit(1)
    
    try:
        import sklearn
        print(f"✓ scikit-learn version: {sklearn.__version__}")
    except ImportError:
        print("⚠ scikit-learn not found. ML features may not work.")
    
    try:
        import pandas
        print(f"✓ pandas version: {pandas.__version__}")
    except ImportError:
        print("⚠ pandas not found. Dataset features may not work.")
    
    print(f"\n🚀 Starting development server at http://127.0.0.1:8000/")
    print("⏎ Press CTRL+BREAK to quit\n")
    
    # Run the command
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()