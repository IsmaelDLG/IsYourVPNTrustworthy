#! /bin/bash

export FLASK_APP=server.py
# --host=0.0.0.0 will make sure other hosts can see the server in the network
flask run --host=0.0.0.0