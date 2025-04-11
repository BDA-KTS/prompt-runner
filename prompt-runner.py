import argparse
from enum import Enum
import pandas
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
            prompt_template = requests.get(prompt_template).text
        except ValueError: # Error parsing URL => try as filename
            if os.path.isfile(prompt_template):
                with open(prompt_template, "r") as prompt_file:
                    prompt_template = prompt_file.read()
            # else: # Not a file => try as JSON array
    messages_type.validate_json(prompt_template)
    return prompt_template

def get_prompts(prompt_template, values_path = args.values):
    for index, values in pandas.read_csv(values_path).iterrows():
        prompt = prompt_template
        for key, value in values.items():
            prompt = prompt.replace(f'{{{key}}}', str(value))
        yield messages_type.validate_json(prompt), values

for prompt, values in get_prompts(get_prompt_template()):
    print(messages_type.dump_json(prompt))
    print(values)


