#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request
from flask_cors import CORS

# Builtins
import json
import os
import time

# Local
from Classes import auth as Auth
from Classes import chat as Chat
from Classes import spinner as Spinner

# Fancy stuff
import colorama
from colorama import Fore

colorama.init(autoreset=True)

# Check if config.json exists
if not os.path.exists("config.json"):
    print(">> config.json is missing. Please create it.")
    print(f"{Fore.RED}>> Exiting...")
    exit(1)

# Read config.json
with open("config.json", "r") as f:
    config = json.load(f)
    # Check if email & password are in config.json
    if "email" not in config or "password" not in config:
        print(">> config.json is missing email or password. Please add them.")
        print(f"{Fore.RED}>> Exiting...")
        exit(1)

    # Get email & password
    email = config["email"]
    password = config["password"]

app = Flask(__name__)
CORS(app)

previous_convo_id = None
conversation_id = None
access_token = ''

def init_chat():
    global access_token

    expired_creds = Auth.expired_creds()
    print(f"{Fore.GREEN}>> Checking if credentials are expired...")
    if expired_creds:
        print(f"{Fore.RED}>> Your credentials are expired." + f" {Fore.GREEN}Attempting to refresh them...")
        open_ai_auth = Auth.OpenAIAuth(email_address=email, password=password)

        print(f"{Fore.GREEN}>> Credentials have been refreshed.")
        open_ai_auth.begin()
        time.sleep(3)
        is_still_expired = Auth.expired_creds()
        if is_still_expired:
            print(f"{Fore.RED}>> Failed to refresh credentials. Please try again.")
            exit(1)
        else:
            print(f"{Fore.GREEN}>> Successfully refreshed credentials.")
    else:
        print(f"{Fore.GREEN}>> Your credentials are valid.")
    print(f"{Fore.GREEN}>> Starting chat..." + Fore.RESET)
    access_token = Auth.get_access_token()

@app.route('/query', methods=['POST'])
def query_chatgpt():
    global access_token
    global conversation_id
    global previous_convo_id

    if access_token == "":
        print(f"{Fore.RED}>> Access token is missing in /Classes/auth.json.")
        exit(1)

    user_input = request.json['query']

    spinner = Spinner.Spinner()
    spinner.start(Fore.YELLOW + "Chat GPT is typing...")

    answer, previous_convo, convo_id = Chat.ask(auth_token=access_token,
            prompt=user_input,
            conversation_id=conversation_id,
            previous_convo_id=previous_convo_id)

    if answer == "400" or answer == "401":
        print(f"{Fore.RED}>> Your token is invalid. Attempting to refresh..")
        open_ai_auth = Auth.OpenAIAuth(email_address=email, password=password)
        open_ai_auth.begin()
        time.sleep(3)
        access_token = Auth.get_access_token()
    else:
        if previous_convo is not None:
            previous_convo_id = previous_convo

    if convo_id is not None:
        conversation_id = convo_id

    print(f"Chat GPT: {answer}")

    return answer

if __name__ == "__main__":
    init_chat()
    app.run(port=9090, debug=True)
