import pytest
import logging
from app_api_requests.package_rating.api import *
from app_api_requests.package_rating.metrics import Metric
from dotenv import load_dotenv
import os
import app_api_requests.package_rating.helper_functions as help

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
handler = logging.FileHandler(os.environ["LOG_FILE"])
handler.setFormatter(formatter)
log.addHandler(handler)

### SYSTEM TESTS ###
@pytest.mark.log
def test_env_load():
    load_dotenv()
    assert os.environ["LOG_FILE"] != ""
    assert os.environ["LOG_LEVEL"] != ""
    assert os.environ["GITHUB_TOKEN"] != ""

### METRIC TESTS ###

scores = []

@pytest.mark.maintainer
def test_maintainer():
    load_dotenv()

    # url 1
    m = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/cloudinary/cloudinary_npm'], log)
    
    score = m.maintainer("cloudinary/cloudinary_npm")
    assert score >= 0 and score <= 1

    # url 2
    m = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/nullivex/nodist'], log)
    
    score = m.maintainer("nullivex/nodist")
    assert score >= 0 and score <= 1

    # url 3
    m = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/lodash/lodash'], log)
    
    score = m.maintainer("lodash/lodash")
    assert score >= 0 and score <= 1
    return


@pytest.mark.correctness
def test_correctness():
    # url 1
    m = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/cloudinary/cloudinary_npm'], log)
    
    score = m.correctness("cloudinary/cloudinary_npm")
    assert score >= 0 and score <= 1

    # url 2
    m = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/nullivex/nodist'], log)
    
    score = m.correctness("nullivex/nodist")
    assert score >= 0 and score <= 1

    # url 3
    m = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/lodash/lodash'], log)
    
    score = m.correctness("lodash/lodash")
    assert score >= 0 and score <= 1
    return


@pytest.mark.ramp_up
def test_ramp_up():
    # url 1
    m = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/cloudinary/cloudinary_npm'], log)
    
    score = m.ramp_up("cloudinary/cloudinary_npm")
    assert score >= 0 and score <= 1

    # url 2
    m = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/nullivex/nodist'], log)
    
    score = m.ramp_up("nullivex/nodist")
    assert score >= 0 and score <= 1

    # url 3
    m = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/lodash/lodash'], log)
    
    score = m.ramp_up("lodash/lodash")
    assert score >= 0 and score <= 1
    return

@pytest.mark.license
def test_license():
    # url 1
    m1 = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/cloudinary/cloudinary_npm'], log)
    help.clone_repo('https://github.com/cloudinary/cloudinary_npm', log)
    
    score = m1.license("cloudinary/cloudinary_npm")
    assert score >= 0 and score <= 1
    help.remove_repo(help.repo_clone_folder, log)

    # url 2
    m2 = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/nullivex/nodist'], log)
    help.clone_repo('https://github.com/nullivex/nodist', log)
    
    score = m2.license("nullivex/nodist")
    assert score >= 0 and score <= 1
    help.remove_repo(help.repo_clone_folder, log)

    # url 3
    m3 = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/lodash/lodash'], log)
    help.clone_repo('https://github.com/lodash/lodash', log)
    
    score = m3.license("lodash/lodash")
    assert score >= 0 and score <= 1
    help.remove_repo(help.repo_clone_folder, log)

@pytest.mark.bus_factor
def test_bus_factor():
    # url 1
    m = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/cloudinary/cloudinary_npm'], log)
    help.clone_repo('https://github.com/cloudinary/cloudinary_npm', log) #N
    
    score = m.bus_factor("cloudinary/cloudinary_npm")
    assert score >= 0 and score <= 1
    help.remove_repo(help.repo_clone_folder, log) #N
    
    # url 2
    m = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/nullivex/nodist'], log)
    help.clone_repo('https://github.com/nullivex/nodist', log) #N
    
    score = m.bus_factor("nullivex/nodist")
    assert score >= 0 and score <= 1
    help.remove_repo(help.repo_clone_folder, log) #N

    # url 3
    m = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/lodash/lodash'], log)
    help.clone_repo('https://github.com/lodash/lodash', log) #N
    
    score = m.bus_factor("lodash/lodash")
    assert score >= 0 and score <= 1
    help.remove_repo(help.repo_clone_folder, log) #N
    
    return

@pytest.mark.dependency
def test_dependency():
    # url 1
    m = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/cloudinary/cloudinary_npm'], log)
    help.clone_repo('https://github.com/cloudinary/cloudinary_npm', log) #N
    
    score = m.dependency_score("cloudinary/cloudinary_npm")
    assert score == (1 / 4)
    help.remove_repo(help.repo_clone_folder, log) #N
    
    # url 2
    m = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/nullivex/nodist'], log)
    help.clone_repo('https://github.com/nullivex/nodist', log) #N
    
    score = m.dependency_score("nullivex/nodist")
    assert score == (3 / 12)
    help.remove_repo(help.repo_clone_folder, log) #N

    # url 3
    m = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/lodash/lodash'], log)
    help.clone_repo('https://github.com/lodash/lodash', log) #N
    
    score = m.dependency_score("lodash/lodash")
    assert score == (1)
    help.remove_repo(help.repo_clone_folder, log) #N
    
    return
    
def test_calc_all_cloudinary():
    # url 1
    scores = []
    m1 = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/cloudinary/cloudinary_npm'], log)
    
    all_scores = m1.calc_all()
    assert all_scores is not None and len(all_scores) > 0

def test_calc_all_nodist():
    # url 2
    scores = []
    m2 = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/nullivex/nodist'], log)
    
    all_scores = m2.calc_all()
    assert all_scores is not None and len(all_scores) > 0

def test_calc_all_lodash():
    # url 3
    scores = []
    m3 = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/lodash/lodash'], log)
    
    all_scores = m3.calc_all()
    assert all_scores is not None and len(all_scores) > 0

def test_print_all_cloudinary():
    # url 1
    m1 = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/cloudinary/cloudinary_npm'], log)
    all_scores = m1.calc_all()

    assert m1.print_all_scores(all_scores) == "https://github.com/cloudinary/cloudinary_npm " + str(round(all_scores["cloudinary/cloudinary_npm"]["NET_SCORE"],2)) +" "+ str(round(all_scores["cloudinary/cloudinary_npm"]["RAMP_UP_SCORE"],2)) +" "+ str(round(all_scores["cloudinary/cloudinary_npm"]["CORRECTNESS_SCORE"],2)) +" "+ str(round(all_scores["cloudinary/cloudinary_npm"]["BUS_FACTOR_SCORE"],2)) +" "+ str(round(all_scores["cloudinary/cloudinary_npm"]["RESPONSIVE_MAINTAINER_SCORE"],2)) +" "+ str(round(all_scores["cloudinary/cloudinary_npm"]["LICENSE_SCORE"],2)) + " "+ str(round(all_scores["cloudinary/cloudinary_npm"]["GOOD_PINNING_PRACTICE_SCORE"],2)) + "\n"

def test_print_all_nodist():
    # url 2
    m2 = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/nullivex/nodist'], log)
    all_scores = m2.calc_all()
    
    assert m2.print_all_scores(all_scores) == "https://github.com/nullivex/nodist " + str(round(all_scores["nullivex/nodist"]["NET_SCORE"],2)) +" "+ str(round(all_scores["nullivex/nodist"]["RAMP_UP_SCORE"],2)) +" "+ str(round(all_scores["nullivex/nodist"]["CORRECTNESS_SCORE"],2)) +" "+ str(round(all_scores["nullivex/nodist"]["BUS_FACTOR_SCORE"],2)) +" "+ str(round(all_scores["nullivex/nodist"]["RESPONSIVE_MAINTAINER_SCORE"],2)) +" "+ str(round(all_scores["nullivex/nodist"]["LICENSE_SCORE"],2)) +" "+ str(round(all_scores["nullivex/nodist"]["GOOD_PINNING_PRACTICE_SCORE"],2))+ "\n"

def test_print_all_lodash():
    # url 3
    m3 = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/lodash/lodash'], log)
    all_scores = m3.calc_all()
    
    assert m3.print_all_scores(all_scores) == "https://github.com/lodash/lodash " + str(round(all_scores["lodash/lodash"]["NET_SCORE"],2)) +" "+ str(round(all_scores["lodash/lodash"]["RAMP_UP_SCORE"],2)) +" "+ str(round(all_scores["lodash/lodash"]["CORRECTNESS_SCORE"],2)) +" "+ str(round(all_scores["lodash/lodash"]["BUS_FACTOR_SCORE"],2)) +" "+ str(round(all_scores["lodash/lodash"]["RESPONSIVE_MAINTAINER_SCORE"],2)) +" "+ str(round(all_scores["lodash/lodash"]["LICENSE_SCORE"],2)) + " "+ str(round(all_scores["lodash/lodash"]["GOOD_PINNING_PRACTICE_SCORE"],2)) + "\n"

def test_net_cloudinary():
    # url 1
    m1 = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/cloudinary/cloudinary_npm'], log)
    all_scores = m1.calc_all()    
    assert all_scores["cloudinary/cloudinary_npm"]["NET_SCORE"] >= 0

def test_net_nodist():
    # url 2
    m2 = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/nullivex/nodist'], log)
    all_scores = m2.calc_all()    
    assert all_scores["nullivex/nodist"]["NET_SCORE"] >= 0

def test_net_lodash():
    # url 3
    m3 = Metric(os.environ["GITHUB_TOKEN"], ['https://github.com/lodash/lodash'], log)
    all_scores = m3.calc_all()    
    assert all_scores["lodash/lodash"]["NET_SCORE"] >= 0

### API TESTS ###

def test_fetch_repo():
    repos = ["https://github.com/nullivex/nodist"]
    m = Metric(os.environ["GITHUB_TOKEN"], repos, log)
    ghub = m.get_ghub()
    assert ghub is not None and isinstance(ghub, API)
    repos = m.get_ghub().get_repos()
    assert repos is not None and isinstance(repos, dict)
    assert len(repos) > 0
    assert "nullivex/nodist" in repos and repos["nullivex/nodist"].full_name == "nullivex/nodist"
    return

def test_fetch_repo_issues():
    repos = ["https://github.com/lodash/lodash"]
    m = Metric(os.environ["GITHUB_TOKEN"], repos, log)
    ghub = m.get_ghub()
    assert ghub is not None and isinstance(ghub, API)
    repos = m.get_ghub().get_repos()
    assert repos is not None and isinstance(repos, dict)
    assert len(repos) > 0
    assert "lodash/lodash" in repos and repos["lodash/lodash"].full_name == "lodash/lodash"
    issues = ghub.get_repo_closed_issues("lodash/lodash")
    assert issues is not None and issues.totalCount > 0
    return

def test_fetch_repo_commits():
    repos = ["https://github.com/cloudinary/cloudinary_npm"]
    m = Metric(os.environ["GITHUB_TOKEN"], repos, log)
    ghub = m.get_ghub()
    assert ghub is not None and isinstance(ghub, API)
    repos = m.get_ghub().get_repos()
    assert repos is not None and isinstance(repos, dict)
    assert len(repos) > 0
    assert "cloudinary/cloudinary_npm" in repos and repos["cloudinary/cloudinary_npm"].full_name == "cloudinary/cloudinary_npm"
    commits = ghub.get_repo_commit_statuses("cloudinary/cloudinary_npm")
    assert commits is not None and commits.totalCount > 0
    return


### TEST HELPER FUNCTIONS ###

def test_normalize_metric():
    normalized = help.normalize_metric(15, 100)
    assert (normalized == 0.15)

def test_clone_remove_repo():
    help.clone_repo("https://github.com/cloudinary/cloudinary_npm", log)
    assert os.path.isdir(help.repo_clone_folder)
    assert os.path.exists(os.path.join(help.repo_clone_folder, "package.json"))
    help.remove_repo(help.repo_clone_folder, log)
    assert not os.path.isdir(help.repo_clone_folder)
