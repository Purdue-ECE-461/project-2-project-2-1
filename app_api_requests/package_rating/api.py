from github import Github
import requests
import os

class API:
    PREFIX = "https://github.com/"

    def __init__(self, token, log):
        self.g = Github(token)
        self.repos = dict()
        self.log = log

    def fetch_repos(self, repositories):
        self.log.info("repositories: {}\n".format(repositories))
        for repo in repositories:
            self.log.info("repo: {}\n".format(repo))
            if ("npmjs.com" in repo):
                # Get github repo URL using npms api
                url = repo.replace("https://www.npmjs.com/", "https://api.npms.io/v2/")
                payload = {}
                headers = {}
                try:
                    response = dict(requests.request("GET", url, headers=headers, data=payload).json())
                    repo = response["collected"]["metadata"]["repository"]["url"].split("github.com/")[1].replace(".git", "")
                except Exception as error:
                    self.log.error(error)
            else:
                # Strip github prefix to get repo full name
                repo = repo[len(API.PREFIX):]
            try:
                github_repo = self.g.get_repo(repo)
                self.log.info(github_repo)
                self.repos[repo] = github_repo
            except Exception as error:
                self.log.error(error)

    def get_repo(self, repo):
        return self.repos[repo]

    def get_repos(self):
        return self.repos

    def api_request(self, repo, content):
        try:
            if content == "licenses":
                return self.g.get_licenses()
            elif content == "license":
                return self.get_repo(repo).get_license()
            elif content == "size":
                return self.get_repo(repo).size
            elif content == "readme":
                return self.get_repo(repo).get_readme()
            elif content == "commits":
                return self.get_repo(repo).get_commits()
            elif content == "open_issues":
                return self.get_repo(repo).get_issues()
            elif content == "closed_issues":
                return self.get_repo(repo).get_issues(state="closed")
            elif content == "stars":
                return self.get_repo(repo).stargazers_count
            elif content == "contributors":
                return self.get_repo(repo).get_contributors()
            elif content == "updated_time":
                return self.get_repo(repo).updated_at
        except Exception as err:
            return err

    def get_licenses(self):
        return self.api_request(None, "licenses")

    def get_repo_license(self, repo):
        return self.api_request(repo, "license")

    def get_repo_contributors(self, repo):
        return self.api_request(repo, "contributors")

    def get_repo_lastupdate(self, repo):
        return self.api_request(repo, "updated_time")

    def get_repo_readme(self, repo):
        return self.api_request(repo, "readme")

    def get_repo_size(self, repo):
        return self.api_request(repo, "size")

    def get_repo_commit_statuses(self, repo):
        return self.api_request(repo, "commits")

    def get_repo_open_issues(self, repo):
        return self.api_request(repo, "open_issues")

    def get_repo_closed_issues(self, repo):
        return self.api_request(repo, "closed_issues")
    
    def get_repo_stars(self, repo):
        return self.api_request(repo, "stars")
