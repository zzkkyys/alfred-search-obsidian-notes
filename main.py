# %%
# %load_ext autoreload
# %autoreload 2

# %%
import argparse
import json
import os
import sys
import time
from argparse import Namespace
from urllib.parse import quote, urlencode

import sys

print("Python Version:", file=sys.stderr)
print(sys.executable, file=sys.stderr)



import requests

# %%
from base.alfred import Alfred, Alfred_Item

# %%
query_ports = os.environ["query_ports"]
if ',' in query_ports:
    query_ports = query_ports.split(',')


# %% [markdown]
# <!-- url = f"http://localhost:51361/search?q=rar"
# response = requests.get(url)
# data = eval(response.text)
#
# obsidian_url = "obsidian://open?valut={}&file={}"
# obsidian_url.format(quote(data[0]['vault']), quote(data[0]['path'])) -->

# %%
def get_obsidian_URI_from_query_res(query_res:list):
    obsidian_url = "obsidian://advanced-uri?valut={}&filepath={}"
    # obsidian_url = "obsidian://advanced-uri?valut={}"
    for res in query_res:
        res['URI'] = obsidian_url.format(quote(res['vault']), quote(res['path']))   
        res['arg'] = f"{res['vault']}|||||{res['path']}"



# %%
def query_multiple_vault(query, query_ports):
    res = []
    if not isinstance(query_ports, list):
        query_ports = [query_ports]
        
    for port in query_ports:
        url = f"http://localhost:{port}/search?q={query}"
        response = requests.get(url)
        data = eval(response.text)
        res += data
    get_obsidian_URI_from_query_res(res)
    return res


# %%

# %% tags=[]
def main(args):
    data = query_multiple_vault(args.query, query_ports)
    
    items = []
    for _d in data:
        _d = Namespace(**_d)
        _item = Alfred_Item(
            title=_d.basename,
            subtitle=_d.excerpt,
            # arg=_d.URI,
            arg=_d.arg,
        )
        items.append(_item)

    alfred = Alfred(items)
    alfred.output_items()


# %% tags=[]
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str)
    args = parser.parse_args()
    main(args)

