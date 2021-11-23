import os
import shutil

def url_handler(url):
    pass

def normalize_metric(raw_score, max_score):
    return min(raw_score / max_score, 1) 
    
repo_clone_folder = "repo_clone"
def clone_repo(url, log):
    # Clone repo to local folder
    log.info("Cloning repo " + url + " to local folder " + repo_clone_folder)
    os.system("git clone " + url + " " + repo_clone_folder)
    return repo_clone_folder

def remove_repo(repo_path, log):
    if (repo_path == repo_clone_folder):
        try:
            log.info("Removing local git clone!")
            shutil.rmtree(repo_path)
        except OSError as err:
            log.error("ERROR: " + str(err))
    else:
        log.error("Folder to remove must be the cloning folder!")
