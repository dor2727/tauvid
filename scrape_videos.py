import requests
from bs4 import BeautifulSoup as BS
# import youtube_dl
import datetime
import json
import urllib
import re
import os
import logging
import tau_login

logger = logging.getLogger('scrape_videos')
logging.basicConfig(level=logging.INFO, format='[*] %(message)s')

BASE_URL = "http://video.tau.ac.il"
VIDEO_LIST_URL = "http://video.tau.ac.il/index.php?option=com_videos&Itemid=53&lang=he"
VIDEO_VIEW_URL = "http://video.tau.ac.il/index.php?option=com_videos&Itemid=53&lang=he&view=video&id={video_id}"


class Video(object):
    def __init__(self, bs_obj, s):
        self.bs_obj = bs_obj

        req = s.get(self.page_url)
        self.url = re.findall("'file': '(http://.*?\\.m3u8)'", req.content.decode())[0]

    @property
    def date(self):
        raw_date = self.bs_obj.find("span").text.split(' ')[2]

        if raw_date == "00-00-0000":
            return datetime.datetime(1,1,1)

        return datetime.datetime.strptime(raw_date, "%d-%m-%Y")

    @property
    def page_url(self):
        return BASE_URL + self.bs_obj.find('a').get("href")

    @property
    def video_id(self):
        query = urllib.urlparse(self.page_url).query
        query_string = urllib.parse_qs(query)
        return query_string["id"]

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
    login = s.get(BASE_URL)

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
    post_login = s.post(login_url, post_data)

    return s


def get_videos(s, dep, course):
    # get items for course post request
    logger.info("Getting metadata for %s-%s", dep, course)
    logger.debug("Sending request to get form for getting videos")
    main_page = s.get(VIDEO_LIST_URL)
    main_page_bs = BS(main_page.content, features="html.parser")
    main_page_form = main_page_bs.find("form", id="adminForm") 
    inputs = main_page_form.find_all("input")

    post_data = {
        i["name"]: i["value"]
        for i in inputs
        if i.has_attr("value") and i.has_attr("name")
    }
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

    lecture_data = {}
    for v in videos:
        lecture_data[v.video_id] = {
            "name": v.name,
            "date": v.date,
            "url": v.url,
            "thumbnail": v.thumbnail,
            "description": v.description
        }
    return lecture_data

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

    # the metadata format is:
    # dept num: {course num: {course name, course num}}

    # desired format is
    # dept num: {
    #   text: dept name,
    #   courses: {course num: {
    #       text: course name,
    #       videos: { id : {urlm data} }
    # }}}
    # because this will be yamled easily

    sane_data = {}

    for dep in ['0104']:  # metadata:
        if dep not in dept_names:
            dept_names[dep] = f"{dep} - Uncategorized"
        courses = metadata[dep]
        sane_data[dep] = {
            "text": dept_names[dep],
            "courses": {
                c: { "text": courses[c]["text"], "videos": get_videos(s, dep, c) } for c in courses
            }
        }
        break

    return sane_data



BASE_URL = "http://video.tau.ac.il"


def main():
    # login
    s = login(*tau_login.creds)

    metadata = get_metadata(s)

    #todo: yamlize page for each dept, then for each course, then for each video... or template direct from json?
    return

    logger.info("getting videos")
    videos = get_video_list(s)

    v = [Video(i, s) for i in videos]

    logger.info(f"found {len(v)} videos")

    for i in v:
        i.download()


if __name__ == '__main__':
    main()