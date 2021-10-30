from typing import Match
from helper_functions import normalize_metric
from api import API
import os
import helper_functions as help
import datetime
import dateutil.relativedelta
import subprocess
import difflib
import json

class Metric:

    MAX_README_SIZE = 10000
    MAX_REPO_SIZE = 100000
    MAX_NUMBER_COMMITS = 10000

    #this number of stars of the repo: https://github.com/freeCodeCamp/freeCodeCamp (highest in the world)
    MAX_STARS = 332690

    MAX_ISSUES = 10000
    MAX_CONTRIBUTORS = 50
    
    MAX_UPDATE_TIME = datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, 1)

    def __init__(self, ghub_token, repos, log):
        self.ghub = API(ghub_token, log)
        self.ghub.fetch_repos(repos)
        self.log = log


    def get_ghub(self):
        return self.ghub


    #### START METRIC FUNCTIONS #####
    # All metric functions should return a value between 0 and 1


    def maintainer(self, repo_name):
        #number of contributors
        #how recent changes were made
        #consistency of update
        # lots of commits
        # lots of maintainers

        commits = self.ghub.get_repo_commit_statuses(repo_name)

        norm_commits = normalize_metric(commits.totalCount, Metric.MAX_NUMBER_COMMITS)
        self.log.info("norm commits: " + str(norm_commits))


        #get number of contributors
        contributors = self.ghub.get_repo_contributors(repo_name)
        contributors_count = contributors.totalCount

        # normalize contributers count to one
        norm_contributors_count = normalize_metric(contributors_count, Metric.MAX_CONTRIBUTORS)
        self.log.info("norm norm_contributors_count: " + str(norm_contributors_count))

        # get the last update time of the repo
        last_update = self.ghub.get_repo_lastupdate(repo_name)

        # if repo was updated this month its score is 1, if updated last month score is 0.8, if updated 2 months ago score is 0.6, and so on...
        if last_update > Metric.MAX_UPDATE_TIME:
            norm_update_time = 1
        elif last_update > Metric.MAX_UPDATE_TIME - dateutil.relativedelta.relativedelta(months=1):
            norm_update_time = 0.8
        elif last_update > Metric.MAX_UPDATE_TIME - dateutil.relativedelta.relativedelta(months=2):
            norm_update_time = 0.6
        elif last_update > Metric.MAX_UPDATE_TIME - dateutil.relativedelta.relativedelta(months=6):
            norm_update_time = 0.4
        elif last_update > Metric.MAX_UPDATE_TIME - dateutil.relativedelta.relativedelta(years=1):
            norm_update_time = 0.2
        else:
            norm_update_time = 0

        self.log.info("norm norm_update_time:" + str(norm_update_time))
        maintain_score = (norm_update_time + norm_contributors_count + norm_commits) / 3

        return maintain_score


    def correctness(self, repo_name):
        #lots of issues opened and resolved, 
        # number of github stars

        star_count = self.ghub.get_repo_stars(repo_name)
        norm_star_count = normalize_metric(star_count, Metric.MAX_STARS)

        open_issues = self.ghub.get_repo_open_issues(repo_name)
        norm_open_issues = normalize_metric(open_issues.totalCount, Metric.MAX_ISSUES)

        correctness = (0.7 * (1 - norm_open_issues)) + (0.3 * norm_star_count)
        # closed_issues = self.ghub.get_repo_closed_issues(repo_name)

        return correctness


    def ramp_up(self, repo_name):
        # Get readme size
        readme = self.ghub.get_repo_readme(repo_name)
        readme_size = readme.size

        # Get repository size
        repo_size = self.ghub.get_repo_size(repo_name)

        # Normalize both sizes to max of 1
        norm_readme_size = normalize_metric(readme_size, Metric.MAX_README_SIZE)

        norm_repo_size = normalize_metric(repo_size, Metric.MAX_REPO_SIZE)

        # Calculate ramp up score
        ramp_up_score = (0.8 * norm_readme_size) + (0.2 * (1 - norm_repo_size))

        return ramp_up_score

    
    LICENSE_COMPATIBILITY = {
        "apgl-3.0": False,
        "apache-2.0": False,
        "bsd-2-clause": False, # Simplified BSD or Free BSD
        "bsd-3-clause": True, # BSD NEW
        "bsl-1.0": False,
        "cc0-1.0": False,
        "epl-2.0": False,
        "gpl-2.0": False,
        "gpl-3.0": False,
        "lgpl-2.1": True,
        "mit": True,
        "mpl-2.0": False,
        "unlicense": True
    }


    # UNUSED
    def get_all_licenses(self):
        if hasattr(self, "licenses"):
            return self.licenses
        else:
            self.licenses = list(self.ghub.get_licenses())
            return self.licenses


    def check_for_license(self, content):
        content = content.lower()
        for license in Metric.LICENSE_COMPATIBILITY.keys():
            for match in difflib.get_close_matches(license, content.split(), n=1, cutoff=0.8):
                if match in Metric.LICENSE_COMPATIBILITY and Metric.LICENSE_COMPATIBILITY[match]:
                    return 1
                elif Metric.LICENSE_COMPATIBILITY[license]:
                    return 0.5 # License has a close match mentioned in content, but may not be exactly compatibile
                else:
                    return 0 # License may have a close match, but it is not compatible
        return 0 # No close matches found in readme


    def check_repo_readme_license(self, repo_name):
        readme = self.ghub.get_repo_readme(repo_name).decoded_content.decode("utf-8")
        return self.check_for_license(readme)

    
    def check_repo_license_file(self, root_dir):
        repo_files = os.listdir(root_dir)
        for file in repo_files:
            if "license" in file.lower():
                with open(os.path.join(root_dir, file), "r") as license_file:
                    licence_file_content = license_file.read()
                    return self.check_for_license(licence_file_content)
        return 0 # No license file found


    def license(self, repo_name):
        # Get license of repo
        repo_license = self.ghub.get_repo_license(repo_name)

        # No license or license not recognized by Github API
        if isinstance(repo_license, Exception):
            # Search for license keyword match in readme instead
            readme_score = self.check_repo_readme_license(repo_name)
            if (readme_score == 0.5): # Close match, but may not be compatible - try license file
                return max([readme_score, self.check_repo_license_file(repo_name)])
            else:
                return readme_score

        else: # License recognized by Github API
            license = repo_license.license
            if license.key == "other":
                return max([0.5, self.check_repo_license_file(help.repo_clone_folder)])
            elif license.key in Metric.LICENSE_COMPATIBILITY and Metric.LICENSE_COMPATIBILITY[license.key]:
                return 1
            else:
                return 0


    def bus_factor(self, repo_name):
        # Use git shortlog to compare number of commits per author
        shortlog = subprocess.check_output("cd " + help.repo_clone_folder + " && git shortlog -n -s -- . && cd ..", shell=True).decode("utf-8")
        
        # Process shortlog output
        if shortlog != '':
            shortlog_lines = shortlog.split("\n")
            if (shortlog_lines[-1] == ''):
                shortlog_lines.pop()
            contributors = [dict() for i in range(len(shortlog_lines))]
            for line in range(len(shortlog_lines)):
                num_commits, contributor_name = shortlog_lines[line].strip().split("\t")
                contributors[line]["name"] = contributor_name
                contributors[line]["commits"] = int(num_commits)

            # Need to find proportion of total commits per contributor
            # To start, find total number of commits
            total_commits = 0
            for contributor in contributors:
                total_commits += contributor["commits"]

            # Then, find proportion of total commits each contributor has made
            for contributor in range(len(contributors)):
                contributors[contributor]["proportion"] = contributors[contributor]["commits"] / total_commits

            # Finally, calcalate bus score by comparing max individual proportion with most ideal proportion
            num_contributors = len(contributors)
            ideal_proportion = 1 / num_contributors
            bus_factor_score = 1 - (contributors[0]["proportion"] - ideal_proportion)

            return bus_factor_score
        else:
            # No contributors - no bus factor score
            return 0


    METRICS = {
        "RAMP_UP_SCORE": {
            "func": ramp_up,
            "weight": 2
        },
        "CORRECTNESS_SCORE": {
            "func": correctness,
            "weight": 2
        },
        "BUS_FACTOR_SCORE": {
            "func": bus_factor,
            "weight": 1
        },
        "RESPONSIVE_MAINTAINER_SCORE": {
            "func": maintainer,
            "weight": 3
        },
        "LICENSE_SCORE": {
            "func": license,
            "weight": 1
        }
    }

    #### END METRIC FUNCTIONS ####

    def calc_all(self):
        # For each repository
        all_scores = dict()
        for repo_name in self.ghub.get_repos():
            # First, clone repository for metrics that need it
            clone_path = help.clone_repo(API.PREFIX + repo_name, self.log)

            # Calculate each individual score
            repo_scores = dict()
            # Insert NET_SCORE = 0 here to ensure it is printed out in proper order in print_all_scores
            repo_scores["NET_SCORE"] = 0
            for metric in Metric.METRICS:
                repo_scores[metric] = Metric.METRICS[metric]["func"](self, repo_name)

            # Finally calculate net score
            total = 0
            for metric in repo_scores:
                if metric != "NET_SCORE":
                    total += repo_scores[metric] * Metric.METRICS[metric]["weight"]
            max = 0
            for metric in Metric.METRICS:
                max += Metric.METRICS[metric]["weight"]
            repo_scores["NET_SCORE"] = total / max

            all_scores[repo_name] = repo_scores

            # Finally. remove local clone of repo
            help.remove_repo(clone_path, self.log)

        return all_scores


    # TODO This function relies on the preservation of insertion order in python dictionaries
    # This preservation is only guaranteed in Python 3.7 and later
    # If python 3.6 or earlier, this function would not be guaranteed to print things in the right format
    def print_all_scores(self, all_scores):
        # Separate from previous output
        print()

        # Ignore empty dict
        if not all_scores:
            return
        
        # Header line
        header = "URL"
        for metric in all_scores[list(all_scores.keys())[0]]:
            header += " " + metric
        print(header)

        # Generate score lines for each repo
        score_lines = []
        for repo_name in all_scores:
            repo_scores = API.PREFIX + repo_name
            for metric in all_scores[repo_name]:
                repo_scores += " " + str(round(all_scores[repo_name][metric], 2))
            score_lines.append(repo_scores)

        # Print score lines in order of net score
        split_score_lines = [score.split() for score in score_lines]
        split_score_lines.sort(key = lambda x: float(x[1]), reverse=True)
        final_print = ""
        for line in split_score_lines:
            line = [" " + line[i] if i > 0 else line[i] for i in range(len(line))]
            final_print = final_print + "".join(line) + "\n"
        print(final_print)

        return final_print
