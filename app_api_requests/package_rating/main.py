import sys
import os
import numpy as np
import logging
from metrics import Metric
from dotenv import load_dotenv

if os.path.isfile('project-1-24.log') is False:
    f = open('project-1-24.log', 'w')
    f.close()      

load_dotenv()
log = logging.getLogger()
level = int(os.environ['LOG_LEVEL'])

if(level==1):
    log.setLevel(logging.INFO) 
elif(level==2):
    log.setLevel(logging.DEBUG) 
elif(level==3):
    log.setLevel(logging.WARNING)  
elif(level==4):
    log.setLevel(logging.ERROR) 
elif(level==5):
    log.setLevel(logging.CRITICAL) 

formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s\n')
handler = logging.FileHandler(os.environ['LOG_FILE'])
handler.setFormatter(formatter)
log.addHandler(handler)

if len(sys.argv) > 1:
    if ".txt" in sys.argv[1]:
        # Gather URLs from URL file
        repo_urls = []
        with open(sys.argv[1], "r") as urlfile:
            url = urlfile.readline()
            while url != "":
                url = url.strip().strip("\n")
                repo_urls.append(url)
                url = urlfile.readline()

        # Instantiate metrics instance
        repo_metrics = Metric(os.environ["GITHUB_TOKEN"], repo_urls, log)

        # Calculate scores
        all_scores = repo_metrics.calc_all()

        # Output scores
        repo_metrics.print_all_scores(all_scores)

    else:
        print("Invalid argument!")
        exit(1)

else:
    print("Missing argument!")
    exit(1)

log.info("Repository evaluation complete.")
exit(0)

