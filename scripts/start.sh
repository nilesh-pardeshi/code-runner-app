#!/bin/bash

pkill gunicorn || true

cd /home/ubuntu/code-runner-app

source venv/bin/activate

nohup gunicorn -w 2 -b 0.0.0.0:5000 app:app &