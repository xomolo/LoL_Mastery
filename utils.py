from datetime import datetime


def convert_timestamp_to_data(ts):
    ts /= 1000
    return str(datetime.fromtimestamp(ts))


def path_to_image_html(path):
    return '<img src="' + path + '" width="60">'
