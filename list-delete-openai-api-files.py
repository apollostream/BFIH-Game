import os
import sys
import json
from pathlib import Path
from typing import Optional, List

from openai import OpenAI
from dotenv import load_dotenv, set_key


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY not found in .env")
    print("Please set your OpenAI API key first")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)
flist = client.files.list()
#print(flist)

print("**DELETING FILES AT OPENAI FILE API:**")
for fobj in flist:
    print(f"- {fobj.filename}")
    client.files.delete(fobj.id)
  
print(client.files.list())

