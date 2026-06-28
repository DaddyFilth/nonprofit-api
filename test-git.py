import git
try:
    print(f"GitPython version: {git.__version__}")
    print("Import successful!")
except ImportError:
    print("Import failed. Please check your Python environment.")
