# project-1-team24
project-1-team24 created by GitHub Classroom

Group 1 for Project 2 ---------------------------------------------------------

This is the Project 1 implementation that we inherited from a previous team to 
use in our Project 2.

It originally only passed 15/20 of their test cases.
Now at 16/20.
We are endeavoring to change that to 20/20.

It currently requires you to have 3 Environmental variables set in your .env

These can be manually set in a unix enviroment via the export command.

The 3 variables are
GITHUB_TOKEN
LOG_LEVEL
LOG_FILE

The commands to set these variables are:

export GITHUB_TOKEN=<your_token_here>
export LOG_LEVEL=2
export LOG_FILE=project-1-24.log

Changelog:

The Shebang was changed from '#!/usr/bin/bash' to '#!/bin/bash' to work on my 
Ubuntu machine

If you do not have your environmental variables set, and you attempt 
"./run test". You will hit an error with a traceback to print_tests.py

To pass one test, all that was needed was specifying the exact LOG_FILE as the 
one Team24 used: project-1-24.log

