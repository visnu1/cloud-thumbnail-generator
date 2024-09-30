import json
import os
import math
import urllib.parse
import datetime
import tempfile
import random
import subprocess

from google.cloud import storage
from wand.image import Image
from PIL import Image as PILImage


import ffmpeg
from datetime import timedelta

from flask import Flask, request

app = Flask(__name__)

# Dummy credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"credia-696ea-ac31aa925d46.json"

video_file_types = ['mp4', 'avi', 'mpeg', 'mov', 'wmv', 'flv', 'avchd', 'webm', 'mkv', 'mpeg4', '3gpp',
                    'mpegps', 'ogg', 'm4v', 'mts/m2ts', 'mts', 'm2ts', 'mxf', 'HEVC', 'MOV', 'MP4', 'AVI', 'MPEG']

image_file_types = ['jpeg', 'png', 'jpg', 'gif', 'tiff', 'tif', 'pict',
                    'pic', 'qtif', 'psd', 'bmp', 'sgi', 'webp', 'heic', 'heif', "pvt"]

orientations = {"3": 180, "6": 90, "8": -90 }


def get_file_name(file_ext):
    file_name = (datetime.datetime.now()).strftime('%Y%m%d%H%M%S%f')[:-3]
    file_name = '/tmp/' + str(file_name) + file_ext
    return file_name


def get_bucket_and_path_from_url(url):
    url_object = urllib.parse.urlparse(url)
    path_arr = url_object.path[1:].split("/")
    bucket_name = path_arr[0]
    o_path = "/".join(url_object.path[1:].split("/")[1:])
    return bucket_name, o_path


def download_file_from_storage(bucket_name, o_path, file_ext):
    storage_client = storage.Client()
    blob = storage_client.bucket(bucket_name).blob(o_path)
    _, temp_local_filename = tempfile.mkstemp(suffix=file_ext)

    with open(temp_local_filename, 'wb') as file_obj:
        blob.download_to_file(file_obj)

    print(f"File {o_path} was downloaded to {temp_local_filename}.")
    return temp_local_filename


def is_format_supported(file_path):
    try:
        output = subprocess.check_output(
            ["identify", "-format", "%m", file_path], universal_newlines=True)
    except subprocess.CalledProcessError:
        return False
    format = output.strip()
    return format

def resize_img(lib, dimension):
    width, height = lib.size
    new_width  = width
    new_height = height
    if width > dimension or height > dimension:
        if width > height:
            new_width = dimension
            new_height = int(height * new_width / width)
        else:
            new_height = dimension
            new_width = int(width * new_height / height)
    return {"width": new_width, "height": new_height}

def thumbnail(file_name, file_format, bucket_name, o_file_name, dimension=1080):
    c_file_name = f"{os.path.splitext(file_name)[0]}.webp"
    quality = 80
    supported = is_format_supported(file_name)
    if supported is not None and supported is not False:
        with open(file_name, 'rb') as f:
            image_bytes = f.read()

        if supported in ('heif','heic'):
            temp = f"{os.path.splitext(file_name)[0]}.jpg"
            with Image(blob=image_bytes) as img2:
                img2.format = 'jpg'
                img2.save(filename=temp)
            upload_file_to_storage(bucket_name, temp, o_file_name + 'jpg', 'image/jpg')

            
        with Image(blob=image_bytes) as img:
            img.compression_quality = quality
            img.format = 'webp'
            dimensions = resize_img(img, dimension)
            img.resize(dimensions['width'], dimensions['height'])
            meta_data = img.metadata
            orientation = meta_data.get('exif:Orientation', None)
            if orientation and orientation in ["3", "6", "8"]:
                    img.rotate(orientations[orientation])
            img.save(filename=c_file_name)
    else:
        with PILImage.open(file_name) as im:
            dimensions = resize_img(im, dimension)
            im.resize((dimensions['width'], dimensions['height']))
            im.save(c_file_name, format='WebP',
                    quality=quality, optimize=True)
    return c_file_name


def upload_file_to_storage(bucket_name, webp_file_name, o_path, content_type):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(o_path)
    with open(webp_file_name, 'rb') as f:
        blob.upload_from_file(f, content_type=content_type)
    blob.make_public()
    blob.cache_control = "public, max-age=604800"
    blob.patch()
    return blob.public_url


def video_length(file_name):
    metadata = ffmpeg.probe(file_name)
    duration = float(metadata['format']['duration'])
    duration_td = str(timedelta(seconds=duration)).split(".")[0]
    # print("duration_td = timedelta(seconds=duration)",  duration_td)
    return {"duration_secs": duration, "duration_td": duration_td}


def video_thumbnail(file_name, time_sec=5):
    c_file_name = f"{os.path.splitext(file_name)[0]}.jpg"
    (
        ffmpeg
        .input(file_name, ss=time_sec)
        .filter('scale', 1080, -1)
        .filter('select', 'gte(n,0)')
        .output(c_file_name, vframes=1, update=True)
        .overwrite_output()
        .run()
    )
    return c_file_name


@app.route('/thumbnail', methods=['POST'])
def main():
    request_json = request.get_json()
    if request_json and 'file_urls' in request_json:
        file_urls = request_json['file_urls']
    else:
        return json.dumps({'message': 'Invalid request', 'success': False, 'result': None}), 400, {'Content-Type': 'application/json'}

    resized_obj_urls = []

    for file_url in file_urls:

        bucket_name, o_path = get_bucket_and_path_from_url(file_url)
        file_name, file_ext = os.path.splitext(o_path)
        file_format = file_ext[1:].lower()
        c_path = file_name + '_thumbxLg.webp'
        content_type = 'image/webp'
        duration_obj = {"duration_td": None}

        if file_format in image_file_types or file_format in video_file_types:
            tmp_file_name = download_file_from_storage(
                bucket_name, o_path, file_ext)
            if file_format in video_file_types:
                duration_obj = video_length(tmp_file_name)
                webp_file_name = video_thumbnail(
                    tmp_file_name, random.randint(2, math.floor(duration_obj['duration_secs'])))
                c_path = file_name + '_thumbxLg.jpg'
                content_type = 'image/jpeg'
            else:
                webp_file_name = thumbnail(tmp_file_name, file_format, bucket_name, file_name)
            c_url = upload_file_to_storage(bucket_name, webp_file_name, c_path, content_type)
            try:
                os.remove(tmp_file_name)
                os.remove(webp_file_name)
            except Exception as e:
                print(f"An error occurred while removing files: {e}")

            resized_obj_urls.append(
                {"thumbnail": c_url, "file": file_url, "duration": duration_obj['duration_td']})
        else:
            resized_obj_urls.append(
                {"thumbnail": None, "file": file_url})

    return json.dumps({'message': 'Success', 'success': True, 'result': resized_obj_urls}), 200, {'Content-Type': 'application/json'}


@app.route('/ping', methods=['GET'])
def server_status():
    return json.dumps({'message': 'App running'}), 200, {'Content-Type': 'application/json'}

if __name__ == '__main__':
    app.run(host='0.0.0.0')
