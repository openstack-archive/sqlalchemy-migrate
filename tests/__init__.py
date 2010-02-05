# make this package available during imports as long as we support <python2.5
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
