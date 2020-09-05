# -*- coding: utf-8 -*-


import datetime
import json
import logging
import argparse
import pathlib
import concurrent.futures
from video_client import VideoClient

logger = logging.getLogger('validate')
logging.basicConfig(level=logging.INFO, format='[*] %(message)s')


# the metadata format is:
# dept num: {course num: {course name, course num}}

# desired format is
# dept num: {
#   text: dept name,
#   thumbnail: dep thumb,
#   courses: {course num: {
#       text: course name,
#       thumbnail: course thumb,
#       videos: { id : {url, data} }
# }}}
# because this will be yamled easily

def parsed_date(date):
    if date == "00-00-0000":
        return datetime.datetime(1,1,1)

    return datetime.datetime.strptime(date, "%d-%m-%Y")


def validate_thumbnail(client, thumbnail):
    return client.head(thumbnail.replace('http', 'https')) == 200

def validate_course(cache, data, client):
    valid_data = data.copy()
    valid_data['videos'] = {}

    next_cache = set()

    for v in data['videos']:
        key = int(v)
        thumbnail = data['videos'][v]['thumbnail']

        if key in cache:
            valid_data['videos'][v] = data['videos'][v]

        elif validate_thumbnail(client, thumbnail):
            valid_data['videos'][v] = data['videos'][v]
            next_cache.add(key)

    if len(valid_data['videos']) == 0:
        return False, next_cache, valid_data

    newest = max(valid_data['videos'], key=lambda v: parsed_date(valid_data['videos'][v]['date']))
    valid_data['thumbnail'] = valid_data['videos'][newest]['thumbnail']
    valid_data['last_update'] = valid_data['videos'][newest]['date']
    return True, next_cache, valid_data


def validate_dep(cache, data, client):
    valid_data = data.copy()
    valid_data['courses'] = {}

    next_cache = set()

    for c in data['courses']:
        logging.info("    Validating Course %s", c)
        valid, cache_item, clean_data = validate_course(cache, data['courses'][c], client)
        next_cache |= cache_item
        if valid:
            valid_data['courses'][c] = clean_data

    if len(valid_data['courses']) == 0:
        return False, next_cache, valid_data

    newest = max(valid_data['courses'], key=lambda c: parsed_date(valid_data['courses'][c]['last_update']))
    valid_data['thumbnail'] = valid_data['courses'][newest]['thumbnail']
    valid_data['last_update'] = valid_data['courses'][newest]['last_update']
    return True, next_cache, valid_data


def validate(cache, data, cachefile):
    valid_deps = {}
    next_cache = list(cache)

    clients = [VideoClient() for i in range(len(data.keys()))]

    def f(dep, client):
        valid, next_cache, clean_data = validate_dep(cache, data[dep], client)
        return dep, valid, next_cache, clean_data

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(data.keys())) as executor:
        futures = executor.map(f, data.keys(), clients)
        for dep, valid, cache_item, clean_data in futures:
                if valid:
                    valid_deps[dep] = clean_data

                logging.info("Validated Department %s", dep)

                next_cache += list(cache_item)
                with cachefile.open('w', encoding='utf-8') as f:
                    json.dump(next_cache, f)

                logging.info("Updated Cache")


    return next_cache, valid_deps

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('data', type=pathlib.Path)
    parser.add_argument('cache', type=pathlib.Path)
    args = parser.parse_args()

    with args.data.open('r', encoding='utf-8') as f:
        data = json.load(f)

    if args.cache.exists():
        with args.cache.open('r', encoding='utf-8') as f:
            cache = set(json.load(f))
    else:
        cache = set()

    cache, data = validate(cache, data, args.cache)

    with args.data.open('w', encoding='utf-8') as f:
        json.dump(data, f)

    with args.cache.open('w', encoding='utf-8') as f:
        json.dump(list(cache), f)



if __name__ == '__main__':
    main()