#!//usr/bin/env python

import argparse
import datetime
import os
import os.path
import requests
import re
import time
import urllib.request, urllib.parse, urllib.error
import urllib.parse
from subprocess import check_call

def utc_mktime(utc_tuple):
    """Returns number of seconds elapsed since epoch
    Note that no timezone are taken into consideration.
    utc tuple must be: (year, month, day, hour, minute, second)
    """

    if len(utc_tuple) == 6:
        utc_tuple += (0, 0, 0)
    return time.mktime(utc_tuple) - time.mktime((1970, 1, 1, 0, 0, 0, 0, 0, 0))

def datetime_to_timestamp(dt):
    """Converts a datetime object to UTC timestamp"""
    return int(utc_mktime(dt.timetuple()))

def parse_thing_ids(text):
    pattern = "thing:(\d{5,7})"
    matched = re.findall(pattern, text)
    return [int(val) for val in matched]

def parse_file_ids(text):
    pattern = "download:(\d{5,7})"
    matched = re.findall(pattern, text)
    return [int(val) for val in matched]

known_licenses = [
        ("Creative Commons - Attribution",
        re.compile("http://creativecommons.org/licenses/by/\d(.\d)?/")),

        ("Creative Commons - Attribution - Share Alike",
        re.compile("http://creativecommons.org/licenses/by-sa/\d(.\d)?/")),

        ("Creative Commons - Attribution - No Derivatives",
        re.compile("http://creativecommons.org/licenses/by-nd/\d(.\d)?/")),

        ("Creative Commons - Attribution - Non-Commercial",
        re.compile("http://creativecommons.org/licenses/by-nc/\d(.\d)?/")),

        ("Attribution - Non-Commercial - Share Alike",
        re.compile("http://creativecommons.org/licenses/by-nc-sa/\d(.\d)?/")),

        ("Attribution - Non-Commercial - No Derivatives",
        re.compile("http://creativecommons.org/licenses/by-nc-nd/\d(.\d)?/")),

        ("Creative Commons - Public Domain Dedication",
        re.compile("http://creativecommons.org/publicdomain/zero/\d(.\d)?/")),

        ("GNU - GPL",
        re.compile("http://creativecommons.org/licenses/GPL/\d(.\d)?/")),

        ("GNU - LGPL",
        re.compile("http://creativecommons.org/licenses/LGPL/\d(.\d)?/")),

        ("BSD License",
        re.compile("http://creativecommons.org/licenses/BSD/")),

        ("Nokia",
        re.compile("http://www.developer.nokia.com/Terms_and_conditions/3d-printing.xhtml")),

        ("Public Domain",
        re.compile("http://creativecommons.org/licenses/publicdomain/")),
        ]

def parse_license(text):
    for name, pattern in known_licenses:
        if pattern.search(text):
            return name
    return "unknown_license"

def crawl_thing_ids(N, end_date=None):
    """ This method extract N things that were uploaded to thingiverse.com
    before end_date.  If end_date is None, use today's date.
    """
    baseurl = "http://www.thingiverse.com/search/recent/things/page:{}?q=&start_date=&stop_date={}&search_mode=advanced&description=&username=&tags=&license="

    end_date = datetime_to_timestamp(end_date)
    thing_ids = set()
    for i in range(N/12 + 1):
        url = baseurl.format(i, end_date)
        r = requests.get(url)
        assert(r.status_code==200)
        thing_ids.update(parse_thing_ids(r.text))
        if len(thing_ids) > N:
            break

        # Sleep a bit to avoid being mistaken as DoS.
        time.sleep(0.5)

    return thing_ids

def crawl_collection(user, collection, output_dir):
    url_prefix = "https://www.thingiverse.com/{}/collections/{}/".format(user, collection)
    baseurl = url_prefix + "page:{}"

    return crawl_things_internal(None, output_dir, baseurl, None)

def crawl_things(N, output_dir, term=None, category=None, source=None, organize=False):
    #baseurl = "http://www.thingiverse.com/newest/page:{}"
    #baseurl = "http://www.thingiverse.com/explore/popular/page:{}"

    key = None
    if term is None:
        assert(source is not None);
        url_prefix= "http://www.thingiverse.com/explore/{}/".format(source);

        if category is None:
            baseurl = url_prefix + "page:{}"
        else:
            baseurl = url_prefix + urllib.parse.quote_plus(category) + "/page:{}"
            key = category
    else:
        baseurl = "http://www.thingiverse.com/search/page:{}?type=things&q=" + urllib.parse.quote_plus(term)
        key = term

    return crawl_things_internal(N, output_dir, baseurl, key, organize)

things_crawled = 0

def get_things_crawled():
    return things_crawled

def crawl_things_internal(N, output_dir, baseurl, key, organize=False, download_zip=False):
    global things_crawled

    things_crawled = 0

    thing_ids = set()
    file_ids = set()
    records = []
    num_files = 0
    page = 0
    previous_path = ''

    while True:
        url = baseurl.format(page+1)
        contents = get_url(url)
        page += 1

        # If the previous url ends up being the same as the old one, we should stop as there are no more pages
        current_path = urllib.parse.urlparse(contents.url).path
        if previous_path == current_path:
            return records
        else:
            previous_path = current_path

        for thing_id in parse_thing_ids(contents.text):
            if download_zip:
                download_zip_file(thing_id, output_dir)
                things_crawled += 1
                continue

            if thing_id in thing_ids:
                continue
            print(("thing id: {}".format(thing_id)))
            thing_ids.add(thing_id)
            things_crawled += 1
            license, thing_files = get_thing(thing_id)
            for file_id in thing_files:
                if file_id in file_ids:
                    continue
                file_ids.add(file_id)
                print(("  file id: {}".format(file_id)))
                result = download_file(file_id, thing_id, output_dir, organize)
                if result is None: continue
                filename, link = result
                if filename is not None:
                    records.append((thing_id, file_id, filename, license, link))
                    if N is not None and len(records) >= N:
                        return records

            # Sleep a bit to avoid being mistaken as DoS.
            time.sleep(0.5)
            save_records(records, key)

def get_thing(thing_id):
    base_url = "http://www.thingiverse.com/{}:{}/files"
    file_ids = []

    url = base_url.format("thing", thing_id)
    print(url)
    contents = get_url(url).text
    license = parse_license(contents)
    return license, parse_file_ids(contents)

def get_url(url, time_out=600):
    r = requests.get(url)
    sleep_time = 1.0
    while r.status_code != 200:
        print(("sleep {}s".format(sleep_time)))
        print(url)
        time.sleep(sleep_time)
        r = requests.get(url)
        sleep_time += 2
        if (sleep_time > time_out):
            # We have sleeped for over 10 minutes, the page probably does
            # not exist.
            break
    if r.status_code != 200:
        print(("failed to retrieve {}".format(url)))
    else:
        return r
        # return r.text

def get_download_link(file_id):
    base_url = "https://www.thingiverse.com/{}:{}"
    url = base_url.format("download", file_id)
    r = requests.head(url)
    link = r.headers.get("Location", None)
    if link is not None:
        __, ext = os.path.splitext(link)
        if ext.lower() not in [".stl", ".obj", ".ply", ".off"]:
            return None
        return link

def download_file(file_id, thing_id, output_dir, organize):
    link = get_download_link(file_id)
    if link is None:
        return None
    __, ext = os.path.splitext(link)
    output_file = "{}{}".format(file_id, ext.lower())
    if organize:
        output_file = os.path.join(str(thing_id), output_file)
    output_file = os.path.join(output_dir, output_file)
    command = "wget -q --tries=20 --waitretry 20 -O {} {}".format(output_file, link)

    if output_dir is not None:
        print(command)
        check_call(command.split())

    return output_file, link

def download_zip_file(thing_id, output_dir, collection_name=None, thing_name=None):
    url = "https://www.thingiverse.com/thing:{}/zip".format(thing_id)

    print(url)
    out_filepath = os.path.join(output_dir, "{}.zip".format(thing_id))
    print(out_filepath)

    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(out_filepath, "wb+") as out_f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    out_f.write(chunk)

def save_records(records, key=None):
    # Enforce kebab case file name
    output_name = re.sub('(\w) (\w)', r'\1-\2', key).lower()+"-" if key else ""
    output_name += "summary"
    with open(output_name+".csv", 'w') as fout:
        fout.write("thing_id, file_id, file, license, link\n")
        for entry in records:
            fout.write(",".join([str(val) for val in entry]) + "\n")

def parse_args():
    parser = argparse.ArgumentParser(
            description="Crawl data from thingiverse",
            epilog="Written by Qingnan Zhou <qnzhou at gmail dot com> Modified by Mike Gleason")
    parser.add_argument("--output-dir", "-o", help="output directories",
            default=".")
    parser.add_argument("--number", "-n", type=int,
            help="how many files to crawl", default=None)
    parser.add_argument("--user", "-u", type=str,
            help="user that owns collection (only for use with --collection)", default=None)
    parser.add_argument("--collection", "-cl", type=str,
            help="collection name", default=None)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--search-term", "-s", type=str, default=None,
            help="term to search for")
    group.add_argument("--category", "-c", type=str, default=None,
            help="catergory to search for")
    parser.add_argument('--organize', dest='organized', default=False, action='store_true',
            help="organize files by their main category")
    parser.add_argument("--source", choices=("newest", "featured", "popular",
        "verified", "made-things", "derivatives", "customizable",
        "random-things", "firehose"), default="featured");
    return parser

def main():
    parser = parse_args()
    args = parser.parse_args()

    if args.number is None and (args.search_term is None and args.category is None and args.user is None and args.collection):
        parser.error('Number OR Search/Category Term OR User+Collection required')

    output_dir = args.output_dir
    number = args.number
    
    if args.user is not None and args.collection is not None:
        records = crawl_collection(args.user, args.collection, output_dir)
    else:
        records = crawl_things(
                args.number,
                output_dir,
                args.search_term,
                args.category,
                args.source,
                args.organized)

    if args.search_term:
        save_records(records, args.search_term)
    elif args.category:
        save_records(records, args.category)
    else:
        save_records(records)

if __name__ == "__main__":
    main()
