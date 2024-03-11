import argparse
import requests
import json
import sys
from cvsslib import cvss2, cvss31, calculate_vector

HEADER = """
z/OS Open Tools Vulnerability JSON Generator

This tool fetches z/OS Open Tools releases and generates a list of tools and their associated CVEs using the osv.dev API.
"""

def calculate_severity(cvss_score):
    if cvss_score >= 9.0:
        return "CRITICAL"
    elif cvss_score >= 7.0:
        return "HIGH"
    elif cvss_score >= 4.0:
        return "MEDIUM"
    else:
        return "LOW"

parser = argparse.ArgumentParser(description=HEADER)
parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
parser.add_argument('--output-file', dest='output_file', required=True, help='The full path to store the JSON file to')
args = parser.parse_args()

# Use the zopen_releases.json cache to iterate on releases
url = "https://raw.githubusercontent.com/ZOSOpenTools/meta/main/docs/api/zopen_releases.json"
if args.verbose:
    print("Fetching data from:", url)

# Use the OSV API: 
def fetch_cves(commit):
    url = "https://api.osv.dev/v1/query"
    data = {"commit": commit}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        cve_data = response.json()
        return cve_data.get("vulns", [])
    else:
        print("Failed to fetch CVEs for commit:", commit)
        return []

response = requests.get(url)
if response.status_code == 200:
    if args.verbose:
        print("Data fetched successfully.")
    data = response.json()
    releases_data = data.get("release_data", {})

    project_info = {}
    if args.verbose:
        print("Processing releases...")

    for project, releases in releases_data.items():
        project_info[project] = []
        for release in releases:
            for asset in release.get("assets", []):
                community_commitsha = asset.get("community_commitsha")
                if community_commitsha:
                    cves = fetch_cves(community_commitsha)
                    if cves:
                        for cve in cves:
                            cvss_vector = cve.get("severity")[0].get("score")
                            cvss_score = calculate_vector(cvss_vector, cvss31) 
                            severity = calculate_severity(cvss_score[0])
                            cve_info = {
                                "id": cve["id"],
                                "details": cve["details"],
                                "published": cve["published"],
                                "severity": severity
                            }
                            release_info = {
                                "name": release["name"],
                                "commit_sha": community_commitsha,
                                "CVEs": cve_info
                            }
                            project_info[project].append(release_info)

    #TODO: Remove after validation - adding a dummy with a known CVE
    dummy_commit_sha = "564d0252ca632e0264ed670534a51d18a689ef5d"
    dummy_cves = fetch_cves(dummy_commit_sha)
    if dummy_cves:
        for cve in dummy_cves:
            cvss_vector = cve.get("severity")[0].get("score")
            cvss_score = calculate_vector(cvss_vector, cvss31) 
            severity = calculate_severity(cvss_score[0])
            cve_info = {
                "id": cve["id"],
                "details": cve["details"],
                "published": cve["published"],
                "severity": severity
            }
            dummy_release_info = {
                "name": "Git Dummy Release",
                "commit_sha": dummy_commit_sha,
                "CVEs": cve_info
            }
            project_info["gitdummy"] = [dummy_release_info]

    with open(args.output_file, "w") as f:
        json.dump(project_info, f, indent=4)
    if args.verbose:
        print("New JSON file created:", args.output_file)

    if args.verbose:
        print("Printing JSON to stdout...")
    json.dump(project_info, sys.stdout, indent=4)
    if args.verbose:
        print("\nDone.")

else:
    print("Failed to fetch data from the URL.")
