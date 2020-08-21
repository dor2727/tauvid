# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup as BS
# import youtube_dl
import datetime
import json
import urllib.parse
import re
import logging
import html
import tau_login
import concurrent.futures

logger = logging.getLogger('scrape_videos')
logging.basicConfig(level=logging.INFO, format='[*] %(message)s')

BASE_URL = "http://video.tau.ac.il"
LOGIN_URL = "http://video.tau.ac.il/index.php"
VIDEO_LIST_URL = "http://video.tau.ac.il/index.php?option=com_videos&Itemid=53&lang=he"
VIDEO_VIEW_URL = "http://video.tau.ac.il/index.php?option=com_videos&Itemid=53&lang=he&view=video&id={video_id}"


class Video(object):
    def __init__(self, bs_obj, s):
        self.bs_obj = bs_obj

        #todo: try and construct url from thumbnail
        # if the url is valid, cache it?
        req = s.get(self.page_url)
        if len(re.findall("'file': '(http://.*?\\.m3u8)'", req.content.decode())) == 0:
            self.url = ''
        else:
            self.url = re.findall("'file': '(http://.*?\\.m3u8)'", req.content.decode())[0]

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

    login_bs = BS(login.content, features="html.parser")
    login_bs_form = login_bs.find("form")
    login_url = login_bs_form.get("action")

    inputs = login_bs_form.find_all("input")
    post_data = {
        i["name"]: i["value"]
        for i in inputs
        if i.has_attr("value") and i.has_attr("name")
    }

    # if the login fails, the "print inputs" and check the name of the username and password inputs
    post_data.update({
        "username": username,
        "passwd": password
    })

    # assuming login_bs_form.method is POST
    logger.info("Logging in")
    s.post(login_url, post_data)

    return s

def video_post_data(s):
    logger.debug("Sending request to get form for getting videos")
    main_page = s.get(VIDEO_LIST_URL)
    main_page_bs = BS(main_page.content, features="html.parser")
    main_page_form = main_page_bs.find("form", id="adminForm") 
    inputs = main_page_form.find_all("input")

    return {
        i["name"]: i["value"]
        for i in inputs
        if i.has_attr("value") and i.has_attr("name")
    }


def get_videos(s, post_data, dep, course):
    # get items for course post request
    logger.info("Getting metadata for %s-%s", dep, course)

    post_data.update({
        "dep_id": dep,
        "course_id": course,
    })

    # get list of courses
    logger.debug("Getting course page")
    course_main_page = s.post(VIDEO_LIST_URL, post_data)
    course_main_page_bs = BS(course_main_page.content, features="html.parser")

    videos = course_main_page_bs.find_all("div", {"class": "video_item"})

    logger.debug("Getting video URLs")
    videos = [Video(v, s) for v in videos]
    logger.debug("Got video URLs")

    if len(videos) == 0:
        return None, None, None

    lecture_data = {}
    for v in videos:
        lecture_data[v.video_id] = {
            "name": html.unescape(v.name),
            "date": html.unescape(v.date),
            "url": v.url,
            "thumbnail": v.thumbnail,
            "description": html.unescape(v.description),
        }

    newest = max(videos, key=lambda v: v.parsed_date)

    return lecture_data, newest.thumbnail, newest.parsed_date


def get_metadata(s):
    logger.info("Getting metadata")
    vid_list = s.get(VIDEO_LIST_URL)
    vid_list_bs = BS(vid_list.content, features="html.parser")

    logger.info("Parsing department list")
    dept_select = vid_list_bs.find("select", id="dep_id").findAll("option")
    dept_names = { el["value"] : el.text for el in dept_select if el["value"] }  # get rid of empty dept

    logger.info("Parsing course list JSON")
    metadata = vid_list_bs.findAll("script", type="text/javascript", src=None)
    metadata = ''.join(i.text for i in metadata)  # resistant to extra <script> tags
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

    def get_department(dep):
        if dep not in dept_names:
            dept_names[dep] = f"{dep} - Uncategorized"
        courses = metadata[dep]

        thumbs = {}
        course_metadata = {}
        for c in courses:
            videos, thumbnail, thumb_date = get_videos(s, video_data, dep, c)
            if videos == None:
                continue

            course_metadata[c] = {
                "text": html.unescape(courses[c]["text"]),
                "videos": videos,
                "thumbnail": thumbnail,
            }

            thumbs[thumb_date] = thumbnail

        return {
            "text": html.unescape(dept_names[dep]),
            "courses": course_metadata,
            "thumbnail": thumbs[max(thumbs)],
        }


    sane_data = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {dep: executor.submit(get_department, dep) for dep in metadata}

        for dep in concurrent.futures.as_completed(futures):
                f = futures[dep]
                try:
                    data = f.result()
                except Exception as exc:
                    logging.exception("Exception scraping %u", dep, exc_info=exc)
                else:
                    logging.info("Done scraping %u", dep)
                    sane_data[dep] = data

    return sane_data


def main():
    # login
    s = login(*tau_login.creds)

    metadata = get_metadata(s)
    with open('videos.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(metadata))

    return

if __name__ == '__main__':
    main()