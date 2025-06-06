# +
import subprocess
import argparse
import json
import os
import sys
import time
from argparse import Namespace
from urllib.parse import quote, urlencode
import argparse
import webbrowser

import requests
from base.alfred import Alfred


# +
def open_obsidian_vault(vault_name):
    # Path to the AppleScript
    script_path = "./open_ob.scpt"  # Change this to the actual path

    # Call the AppleScript with the vault name as parameter
    subprocess.run(["osascript", script_path, vault_name])

def open_uri(uri):
    webbrowser.open(uri)


# -

parser = argparse.ArgumentParser()
parser.add_argument("--arg", type=str, help="increase output verbosity")
args = parser.parse_args()
vault, path = args.arg.split("|||||")

Alfred.log_info(args)

uri = "obsidian://open?file={}".format(quote(path))
open_obsidian_vault(vault_name=vault)
open_uri(uri)
