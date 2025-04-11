import argparse
import csv
from enum import Enum
import requests
import os
from typing import List
from pydantic import BaseModel, TypeAdapter


parser = argparse.ArgumentParser(
    prog="prompt-runner",
    description="Runs a prompt against an LLM server using values from a CSV file"
)

parser.add_argument("--server", help="Endpoint URL of the LLM server", required=True)
parser.add_argument("--prompt-template", help="JSON array of the messages sent for the LLM server with variables enclosed in double curly braces; or local path or URL of file containing such", required=True)
parser.add_argument("--values", help="CSV file in which column headers correspond to variables in the prompt, and each row contains the value assignment to these variables for one execution", required=True)
args = parser.parse_args()

class Role(str, Enum):
    assistant = "assistant"
    system = "system"
    user = "user"

class Message(BaseModel):
    role: Role
    content: str

messages_type = TypeAdapter(List[Message])

def get_prompt_template(prompt_template = args.prompt_template):
    if prompt_template.endswith(".json"):
        try:
            prompt_template = requests.get(prompt_template).content
        except ValueError: # Error parsing URL => try as filename
            if os.path.isfile(prompt_template):
                with open(prompt_template, "r") as prompt_file:
                    prompt_template = prompt_file.read()
            # else: # Not a file => try as JSON array
    messages_type.validate_json(prompt_template)
    return prompt_template

def get_values(values_path = args.values):
    try:
        for row in csv.DictReader(requests.get(values_path).content):
            yield row
    except ValueError: # Error parsing URL => try as filename
        with open(values_path, "r", newline="") as values_file:
            for row in csv.DictReader(values_file):
                yield row

def get_prompts(values, prompt_template):
    for row in values:
        prompt = prompt_template
        for key in row:
            prompt = prompt.replace(f'{{{key}}}', str(row[key]))
        yield messages_type.validate_json(prompt)

for prompt in get_prompts(get_values(), get_prompt_template()):
    print(messages_type.dump_json(prompt))


