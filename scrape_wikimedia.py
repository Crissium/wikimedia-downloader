#!/usr/bin/env python3

"""
Download files from a category and its subcategories of Wikimedia Commons.
"""

import os
import requests
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor


endpoint = 'https://commons.wikimedia.org/w/api.php'
headers = {
	'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
	'Accept-Language': 'en-GB,en;q=0.5',
	'DNT': '1',
	'Connection': 'keep-alive',
	'Upgrade-Insecure-Requests': '1',
	'Sec-Fetch-Dest': 'document',
	'Sec-Fetch-Mode': 'navigate',
	'Sec-Fetch-Site': 'none',
	'Sec-Fetch-User': '?1'
}


def get_files_and_subcats(cat: str) -> tuple[list[str], list[str]]:
	response = requests.get(
		endpoint,
		{
			'action': 'query',
			'format': 'json',
			'list': 'categorymembers',
			'cmtitle': cat,
			'cmprop': 'title|type',
			'cmlimit': 'max'
		}
	)

	members = response.json()['query']['categorymembers']
	return (
		[member['title'] for member in members if member['type'] == 'file'],
		[member['title'] for member in members if member['type'] == 'subcat']
	)


def get_files(cat: str) -> set[str]:
	files, subcats = get_files_and_subcats(cat)
	files = set(files)
	with ThreadPoolExecutor(min(32, len(subcats) + 1)) as executor:
		files.update(*executor.map(get_files, subcats))
	return files


def get_url_of_file(title: str) -> str:
	response = requests.get(
		endpoint,
		{
			'action': 'query',
			'format': 'json',
			'prop': 'imageinfo',
			'iiprop': 'url',
			'titles': title
		}
	)

	return list(response.json()['query']['pages'].values())[0]['imageinfo'][0]['url']


def download(url: str) -> None:
	filename = urllib.parse.unquote(url.split('/')[-1])
	if os.path.isfile(filename):
		print(f'{filename} already exists.')
		return

	response = requests.get(url, headers=headers)
	with open(filename, 'wb') as file:
		file.write(response.content)


def main(cat: str) -> int:
	files = get_files(cat)
	urls = set()
	with ThreadPoolExecutor(min(32, len(files))) as executor:
		urls.update(executor.map(get_url_of_file, files))
	with ThreadPoolExecutor(min(32, len(urls))) as executor:
		executor.map(download, urls)
	return len(urls)


if __name__ == '__main__':
	if len(sys.argv) != 2:
		print('Usage: python scrape_wikimedia.py <category>')
		sys.exit(1)
	arg = sys.argv[1]
	if arg.startswith('https://'):
		arg = arg.split('/')[-1]
	elif not arg.startswith('Category:'):
		arg = 'Category:' + arg
	
	count = main(arg)
	print(f'Downloaded {count} files from {arg}.')
