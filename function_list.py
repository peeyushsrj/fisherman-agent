import requests
import os
from urllib.parse import urlparse

def greet(name:str):
    str = "Hello,  "+ name + "!"
    return str 

def download_link(url,fileNameToBeSavedAs):
    if not url:
        print('url is empty')
        return -1
    try:
        parsed_url = urlparse(url)
        if not fileNameToBeSavedAs:
            filename = parsed_url.path.split("/")[-1]
        else:
            filename = fileNameToBeSavedAs
        filepath = os.path.join(os.getcwd(), filename)  # use relative file path
        chunk_size = 1024 * 1024 # 1 MB

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    f.write(chunk)
        return filename
    except:
        print('unable to download')
        return -1
