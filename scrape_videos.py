# -*- coding: utf-8 -*-

import requests as requests

from bs4 import BeautifulSoup as BS
import datetime
import json
import urllib.parse
import logging
import html
import tau_login
import argparse
import pathlib
import concurrent.futures
from video_client import VideoClient

logger = logging.getLogger('scrape_videos')
logging.basicConfig(level=logging.INFO, format='[*] %(message)s')

LOGIN_URL = "http://video.tau.ac.il/index.php"
VIDEO_LIST_URL = "http://video.tau.ac.il/index.php?option=com_videos&Itemid=53&lang=he"
VIDEO_VIEW_URL = "http://video.tau.ac.il/index.php?option=com_videos&Itemid=53&lang=he&view=video&id={video_id}"

BASE_URL = "https://video.tau.ac.il"
IMAGE_TEMPLATE = ("https://video.tau.ac.il/files/", ".jpg")
VIDEO_TEMPLATE = ("https://vod.tau.ac.il/Courses/_definst_/mp4:", ".mp4/playlist.m3u8")

class Video(object):
    def __init__(self, bs_obj):
        self.bs_obj = bs_obj

    @property
    def date(self):
        raw_date = self.bs_obj.find("span").text.split(' ')[2]
        return raw_date

    @property
    def parsed_date(self):
        if self.date == "00-00-0000":
            return datetime.datetime(1,1,1)

        return datetime.datetime.strptime(self.date, "%d-%m-%Y")

    @property
    def page_url(self):
        return BASE_URL + self.bs_obj.find('a').get("href")

    @property
    def video_id(self):
        query = urllib.parse.urlparse(self.page_url).query
        query_string = urllib.parse.parse_qs(query)
        return query_string["id"][0]

    @property
    def thumbnail(self):
        return BASE_URL + self.bs_obj.find('img').get("src")

    @property
    def url(self):
        uri = self.thumbnail.replace(IMAGE_TEMPLATE[0], '').replace(IMAGE_TEMPLATE[-1], '')
        return VIDEO_TEMPLATE[0] + uri + VIDEO_TEMPLATE[1]

    @property
    def name(self):
        return self.__str__().split(' [')[0]

    @property
    def description(self):
        return self.bs_obj.find('div', {"class": "video_details"}).find('p').text

    def __repr__(self):
        return ' '.join(self.bs_obj.text.split())
    def __str__(self):
        return ' '.join(self.bs_obj.text.split())


def login(username, password):
    s = requests.session()
    logger.info("Parsing login form")
    login = s.get(LOGIN_URL)

    login_bs = BS(login.content, features="lxml")
    login_bs_form = login_bs.find("form")
    login_url = login_bs_form.get("action")

    inputs = login_bs_form.find_all("input")
    post_data = {
        i["name"]: i["value"]
        for i in inputs
        if i.has_attr("value") and i.has_attr("name")
    }

    # if the login fails, then "print inputs" and check the name of the username and password inputs
    post_data.update({
        "username": username,
        "passwd": password
    })

    # assuming login_bs_form.method is POST
    logger.info("Logging in")
    res = s.post(login_url, post_data)
    return res.request.headers

def get_videos(s, post_data_base, dep, course):
    # get items for course post request
    logger.info("Getting metadata for %s-%s", dep, course)

    post_data = {**post_data_base, **{"dep_id": dep, "course_id": course}}
    post_data = urllib.parse.urlencode(post_data)
    # post_data = "dep_id=0341&course_id=2008&option=com_videos&view=videos&task=&d5165fce86105a4395f8363f3a80aa90=1"
    # get list of courses
    logger.debug("Getting course page")
    course_main_page = s.post(VIDEO_LIST_URL, bytes(post_data, 'ascii'))
    course_main_page_bs = BS(course_main_page, features="lxml")

    videos = course_main_page_bs.find_all("div", {"class": "video_item"})

    if len(videos) == 0:
        return None

    videos = [Video(v) for v in videos]

    lecture_data = {}
    for v in videos:
        lecture_data[v.video_id] = {
            "name": html.unescape(v.name),
            "date": html.unescape(v.date),
            "url": v.url,
            "thumbnail": v.thumbnail,
            "description": html.unescape(v.description),
        }

    return lecture_data


def video_post_data(s):
    logger.debug("Sending request to get form for getting videos")
    main_page = s.get(VIDEO_LIST_URL)
    main_page_bs = BS(main_page, features="lxml")
    main_page_form = main_page_bs.find("form", id="adminForm") 
    inputs = main_page_form.find_all("input")

    return {
        i["name"]: i["value"]
        for i in inputs
        if i.has_attr("value") and i.has_attr("name")
    }


def get_metadata(headers, departments):
    s = VideoClient(headers)
    logger.info("Getting metadata")
    vid_list = s.get(VIDEO_LIST_URL)
    vid_list_bs = BS(vid_list, features="lxml")

    logger.info("Parsing department list")
    dept_select = vid_list_bs.find("select", id="dep_id").findAll("option")
    dept_names = { el["value"] : el.text for el in dept_select if el["value"] }  # get rid of empty dept

    logger.info("Parsing course list JSON")
    metadata = vid_list_bs.findAll("script", type="text/javascript", src=None)
    metadata = '\n'.join(str(i) for i in metadata)  # resistant to extra <script> tags
    metadata = [i for i in metadata.splitlines() if "JSON.decode" in i][0]

    metadata = metadata[metadata.index("{") : metadata.rindex("}") + 1]  # bounds of actual json
    metadata = json.loads(metadata)

    logger.info("Scraping Video List Request Format")
    video_data = video_post_data(s)


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

    def get_department(dep, client):
        if dep not in dept_names:
            dept_names[dep] = f"{dep} - Uncategorized"
        courses = metadata[dep]

        # thumbs = {}
        course_metadata = {}
        for c in courses:
            videos = get_videos(client, video_data, dep, c)
            if videos == None:
                continue

            course_metadata[c] = {
                "text": html.unescape(courses[c]["text"]),
                "videos": videos,
                # "thumbnail": thumbnail,
            }

            # thumbs[thumb_date] = thumbnail
        data = {
            "text": html.unescape(dept_names[dep]),
            "courses": course_metadata,
            # "thumbnail": thumbs[max(thumbs)],
        }
        return dep, data

    logging.info("Departments: %s", sorted(metadata.keys()))

    if departments == []:
        departments = metadata

    departments = [i for i in departments if i in metadata]
    clients = [VideoClient(headers) for i in range(len(departments))]

    sane_data = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(departments) + 4) as executor:
        futures = executor.map(get_department, departments, clients)
        for dep, data in futures:
                logging.info("Done scraping %s", dep)
                sane_data[dep] = data

    return sane_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('outfile', type=pathlib.Path)
    parser.add_argument('departments', nargs='*')
    args = parser.parse_args()

    headers = login(*tau_login.creds)
    metadata = get_metadata(headers, args.departments)

    if args.outfile.exists():
        with args.outfile.open('r+', encoding='utf-8') as f:
            old_metadata = json.load(f)
            old_metadata.update(metadata)
            f.seek(0)
            json.dump(metadata,  f)
            f.truncate()

    else:
        with args.outfile.open('w', encoding='utf-8') as f:
            json.dump(metadata,  f)


if __name__ == '__main__':
    main()