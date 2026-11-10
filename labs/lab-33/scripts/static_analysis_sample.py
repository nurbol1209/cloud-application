import sys, os
from pathlib import Path

def build_message( name ):
    unused_value = 10
    if name == None:
        return "Unknown"
    return "Service: " + name

print(build_message("notification"))
