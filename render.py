# -*- coding: utf-8 -*-
import sys
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os
import logging

logger = logging.getLogger('render')
logging.basicConfig(level=logging.INFO, format='[*] %(message)s')

def gen_main(metadata, env):
    # template requires [{url, thumbnail, text}]

    breadcrumbs = [('tauvid', '/')]

    department_data = []
    for dep in metadata:
        department_data.append({
            'url': f'/{dep}',
            'thumbnail': f'/{dep}/thumb.jpg',
            'text': metadata[dep]['text']
        })
        gen_department(dep, metadata[dep], breadcrumbs, env)

    logger.info("Rendering Main Page")
    rendered = env.get_template('main.html').render(departments=department_data, breadcrumbs=breadcrumbs)
    with open('output/index.html', 'w', encoding='utf-8') as f:
        f.write(rendered)

def gen_department(dep_id, metadata, breadcrumbs, env):
    # template requires [{url, thumbnail, text}]

    item_uri = f'{dep_id}'
    os.makedirs(f'output/{item_uri}', exist_ok=True)
    
    breadcrumbs = [i for i in breadcrumbs] + [(metadata['text'], f'/{item_uri}')]

    courses = []
    for course_id in metadata['courses']:
        courses.append({
            'url': f'/{item_uri}/{course_id}',
            'thumbnail': f'/{item_uri}/{course_id}/thumb.jpg',
            'text': metadata['courses'][course_id]['text']
        })
        gen_course(dep_id, course_id, metadata['courses'][course_id], breadcrumbs, env)

    logger.info("  Rendering Department %s", dep_id)
    rendered = env.get_template('department.html').render(text=metadata['text'], courses=courses, breadcrumbs=breadcrumbs)
    with open(f'output/{item_uri}/index.html', 'w', encoding='utf-8') as f:
        f.write(rendered)

def gen_course(dep_id, course_id, metadata, breadcrumbs, env):
    # template requires [{url, thumbnail, name, date, description}]

    item_uri = f'{dep_id}/{course_id}'
    os.makedirs(f'output/{item_uri}', exist_ok=True)

    breadcrumbs = [i for i in breadcrumbs] + [(metadata['text'], f'/{item_uri}')]
    
    videos = []
    for vid_id in metadata['videos']:
        vid_s = metadata['videos'][vid_id]

        videos.append({
            'url': f'/{item_uri}/{vid_id}',
            'thumbnail': vid_s['thumbnail'],
            'name': vid_s['name'],
            'date': vid_s['date'],
            'description': vid_s['description']
        })
        gen_video(dep_id, course_id, vid_id, vid_s, breadcrumbs, env)

    logger.info("    Rendering Course %s-%s", dep_id, course_id)
    rendered = env.get_template('course.html').render(text=metadata['text'], videos=videos, breadcrumbs=breadcrumbs)
    with open(f'output/{item_uri}/index.html', 'w', encoding='utf-8') as f:
        f.write(rendered)

def gen_video(dep_id, course_id, vid_id, metadata, breadcrumbs, env):
    # template requires [{url, thumbnail, text}]

    item_uri = f'{dep_id}/{course_id}/{vid_id}'
    os.makedirs(f'output/{item_uri}', exist_ok=True)

    breadcrumbs = [i for i in breadcrumbs] + [(metadata['name'], f'/{item_uri}')]
    
    logger.info("      Rendering Video %s-%s-%s", dep_id, course_id, vid_id)
    rendered = env.get_template('video.html').render(**metadata, breadcrumbs=breadcrumbs)
    with open(f'output/{item_uri}/index.html', 'w', encoding='utf-8') as f:
        f.write(rendered)


def main(argv):
    logger.info("Loading JSON")
    metadata = json.loads(open(argv[1], 'r', encoding='utf-8').read())
    os.makedirs('output', exist_ok=True)

    logger.info("Loading Templates")
    env = Environment(
        loader=FileSystemLoader('templates/'),
        autoescape=select_autoescape(['html', 'xml'])
    )



    gen_main(metadata, env)
    logger.info("Rendering Complete")



if __name__ == '__main__':
    main(sys.argv)