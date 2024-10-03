import argparse
import json
import certifi
import aiohttp
import asyncio
import ssl
import sys
from collections import defaultdict
from cvsslib import cvss31, calculate_vector

HEADER = """
zopen community Vulnerability JSON Generator

This tool fetches zopen community releases and generates a list of tools and their associated CVEs using the osv.dev API.
"""

BASE_URL = "https://raw.githubusercontent.com/zopencommunity/meta/main"

parser = argparse.ArgumentParser(description=HEADER)
parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
parser.add_argument('--output-file', dest='output_file', required=True, help='The full path to store the JSON file to')
args = parser.parse_args()

def calculate_severity(cvss_score):
    if cvss_score >= 9.0:
        return "CRITICAL"
    elif cvss_score >= 7.0:
        return "HIGH"
    elif cvss_score >= 4.0:
        return "MEDIUM"
    else:
        return "LOW"

# Helper to fetch json data from URL
async def fetch_json(session, url):
    async with session.get(url) as response:
        if response.status == 200:
            if args.verbose:
                print("Successfully fetched json from:", url)
            text = await response.text()
            return json.loads(text)
        else:
            print("Failed to fetch json from:", url)
            return {}

# Use the OSV API: 
async def fetch_cves(session, commit):
    url = "https://api.osv.dev/v1/query"
    data = {
        "commit": commit
    }
    async with session.post(url, json=data) as response:
        if response.status == 200:
            cve_data = await response.json()
            return cve_data.get("vulns", [])
        else:
            print("Failed to fetch CVEs for commit:", commit)
            return []

async def get_release_cve_info(session, project, release_name, asset):
    commit_sha = asset["community_commitsha"]
    if not commit_sha:
        if args.verbose:
            print(f"No commit hash for {release_name}")
        return (project, release_name, [])
    all_cves = []
    cves = await fetch_cves(session, commit_sha)
    for cve in cves:
        severity = cve.get("severity", [])  # Initialize severity from cve data
        if not severity or not severity[0]:
            continue  # Skip this iteration if severity is None or empty
        cvss_vector = severity[0].get("score")
        cvss_score = calculate_vector(cvss_vector, cvss31) 
        severity = calculate_severity(cvss_score[0])
        cve_info = {
            "id": cve["id"],
            "details": cve["details"],
            "published": cve["published"],
            "severity": severity
        }
        all_cves.append(cve_info)
    return (project, release_name, all_cves)

async def main():
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    conn = aiohttp.TCPConnector(ssl_context=ssl_context)
    async with aiohttp.ClientSession(connector=conn) as session:
        # Fetch releases json and CVE include/exclude list jsons
        releases_url = f"{BASE_URL}/docs/api/zopen_releases.json"
        include_url = f"{BASE_URL}/data/cve_include.json"
        exclude_url = f"{BASE_URL}/data/cve_exclude.json"
        if args.verbose:
            print("Fetching data from:", releases_url)
            print("Fetching data from:", include_url)
            print("Fetching data from:", exclude_url)
        json_tasks = [
            fetch_json(session, releases_url),
            fetch_json(session, include_url),
            fetch_json(session, exclude_url)
        ]
        [releases_json, include_json, exclude_json] = await asyncio.gather(*json_tasks)

        releases_data = releases_json.get("release_data", {})

        # Convert from versions in include json to release names
        if args.verbose:
            print("Converting versions in include json to release names...")
        include_releases = defaultdict(list)
        for pkg, cves in include_json.items():
            for cve in cves:
                versions = set(cve.get("versions", []))
                releases = []
                for release in releases_data.get(pkg, []):
                    if release["assets"][0].get("version", "") in versions:
                        releases.append(release["name"])
                include_releases[pkg].append({
                    "id": cve["id"],
                    "details": cve["details"],
                    "severity": cve["severity"],
                    "releases": releases
                })

        # Convert from versions in exclude json to release names
        if args.verbose:
            print("Converting versions in exclude json to release names...")
        exclude_releases = defaultdict(list)
        for pkg, cves in exclude_json.items():
            for cve in cves:
                versions = set(cve.get("versions", []))
                releases = []
                for release in releases_data.get(pkg, []):
                    if release["assets"][0].get("version", "") in versions:
                        releases.append(release["name"])
                exclude_releases[pkg].append({
                    "id": cve["id"],
                    "releases": releases
                })

        if args.verbose:
            print("Processing releases...")
        tasks = []
        info_map = defaultdict(dict)
        for project, releases in releases_data.items():
            for release in releases:
                for asset in release.get("assets", []):
                    # Create a coroutine for each project to fetch CVEs
                    tasks.append(get_release_cve_info(session, project, release["name"], asset))
                    info_map[release["name"]]["commit_sha"] = asset.get("community_commitsha", None)
                    info_map[release["name"]]["release"] = asset.get("release", None)

        if args.verbose:
            print("Executing tasks...")
        # Wait for all coroutines to finish and create project_info dict
        all_cves = await asyncio.gather(*tasks)
        project_info = defaultdict(dict)

        for project, release_name, cves in all_cves:
            # Filter out CVEs that are in exclude list
            release = info_map[release_name]["release"]
            if release is None:
                continue
            if project in exclude_releases:
                for exclude_cve in exclude_releases[project]:
                    filtered = []
                    for cve in cves:
                        if (cve["id"] != exclude_cve["id"] or
                                release_name not in exclude_cve["releases"]):
                            filtered.append(cve)
                        elif args.verbose:
                            print(f"Exclude list -- ignored {cve['id']} in {release_name}")
                    if len(filtered) > 0:
                        project_info[project][release] = {
                            "release_name": release_name,
                            "commit_sha": info_map[release_name]["commit_sha"],
                            "CVEs": filtered
                        }
            elif len(cves) > 0:
                project_info[project][release] = {
                    "release_name": release_name,
                    "commit_sha": info_map[release_name]["commit_sha"],
                    "CVEs": cves
                }

        # Add CVEs from include list
        for project, cves in include_releases.items():
            for cve in cves:
                for release_name in cve.get("releases", []):
                    if release_name not in info_map:
                        continue
                    release = info_map[release_name]["release"]
                    if release is None:
                        continue
                    if release not in project_info[project]:
                        project_info[project][release] = {
                            "release_name": release_name,
                            "commit_sha": info_map[release_name]["commit_sha"],
                            "CVEs": []
                        }
                    if args.verbose:
                        print(f"Include list -- added {cve['id']} to {release_name}")
                    project_info[project][release]["CVEs"].append({
                        "id": cve["id"],
                        "details": cve["details"],
                        "severity": cve["severity"]
                    })

        with open(args.output_file, "w") as f:
            json.dump(project_info, f, indent=4)
        if args.verbose:
            print("New JSON file created:", args.output_file)

        if args.verbose:
            print("Printing JSON to stdout...")
        json.dump(project_info, sys.stdout, indent=4)
        if args.verbose:
            print("\nDone.")

if __name__ == '__main__':
    asyncio.run(main())
