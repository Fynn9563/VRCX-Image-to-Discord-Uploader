import subprocess
import sys

def install_packages(packages):
    subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)

# Install required packages
install_packages(['requests', 'Pillow'])
