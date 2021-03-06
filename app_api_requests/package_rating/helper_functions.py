import os
import shutil

def url_handler(url):
    pass

def normalize_metric(raw_score, max_score):
    return min(raw_score / max_score, 1) 

# if we are running LOCALLY :  repo_clone_folder = "/tmp/repo_clone"  
    # then all the tests pass
# if we are running IN PRODUCTION :  repo_clone_folder = "/temp/repo_clone"
    # then all the manualy tests with the ACTUAL "appspot.com" endpoint work
repo_clone_folder = "/tmp/repo_clone"

def clone_repo(url, log):
    # Clone repo to local folder
    # if: it exsts -- > remove it
    if ( os.path.isdir(repo_clone_folder) ):
        shutil.rmtree(repo_clone_folder)
    
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
