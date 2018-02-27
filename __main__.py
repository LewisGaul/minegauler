import sys
from os.path import join, dirname
# Change base import directory to 'src'.
sys.path[0] = join(dirname(__file__), 'src')

# Run the main function.
from main import main
main()
