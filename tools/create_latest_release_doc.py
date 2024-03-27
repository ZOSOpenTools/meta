"""
Script to generate a markdown file listing newly released tools.
The resulting markdown will be added to the z/OS Open Tools docs
"""

import json
import requests
from datetime import datetime
import argparse

def generate_markdown(data, output_file):
    release_info = {}
    for tool, releases in data.items():
        for release in releases:
            release_date = datetime.strptime(release['date'], "%Y-%m-%d %H:%M:%S%z").strftime('%Y-%m-%d')
            pax_name = release['assets'][0]['name']
            pax_url = release['assets'][0]['url'].replace('download', 'tag').rsplit('/', 1)[0]
            if release_date not in release_info:
                release_info[release_date] = {}
            if tool not in release_info[release_date]:
                release_info[release_date][tool] = []
            release_info[release_date][tool].append({'name': pax_name, 'url': pax_url})

    sorted_releases = sorted(release_info.items(), key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'), reverse=True)

    with open(output_file, 'w') as md_file:
        md_file.write("# Newly Released Tools\n\n")
        for release_date, tools in sorted_releases:
            md_file.write(f"## {release_date}\n\n")
            for tool, releases in tools.items():
                for release in releases:
                    md_file.write(f"- **{tool}**: [{release['name']}]({release['url']})\n")
            md_file.write("\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate markdown file for newly released tools.')
    parser.add_argument('--output', '-o', default='Newly_released_tools.md', help='Output markdown file path')
    args = parser.parse_args()

    url = 'https://raw.githubusercontent.com/ZOSOpenTools/meta/main/docs/api/zopen_releases.json'
    response = requests.get(url)
    data = response.json()['release_data']

    generate_markdown(data, args.output)
