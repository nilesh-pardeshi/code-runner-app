#!/bin/bash

cd /home/ubuntu/code-runner-app

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt