import requests
import os
import urllib.parse
import shutil
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

from api_request_signature import sign_url


def download_image_from_api(pano_id: str, output_path: str, progress: tqdm) -> None:

    # if this image file already exists, don't do anything
    if os.path.exists(os.path.join(output_path, f'{pano_id}.png')):
        # print('image exists')
        progress.update()
        return

    params = {
        'pano': pano_id,
        'size': '640x640',
        'key': api_key,
        'fov': 90,
        'pitch': 0,
        'return_error_code': 'true',
        # 'source': 'outdoor'
    }

    url = 'https://maps.googleapis.com/maps/api/streetview?' + urllib.parse.urlencode(params)
    url = sign_url(url, secret)
    r = requests.get(url, stream=True)

    if r.status_code != requests.codes.ok:
        print(f'Warning: image {pano_id} produced error with response status code {r.status_code}')
        progress.update()
        return

    with open(os.path.join(output_path, f'{pano_id}.png'), 'wb') as f:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, f)

    progress.update()

    return


def main():

    imagery_locations = pd.read_csv(os.path.join('data', 'imagery_locations.csv'))

    print(f'Downloading images for {len(imagery_locations)} locations')

    images_path = 'images'
    if not os.path.exists(images_path):
        os.mkdir(images_path)

    progress = tqdm(total=len(imagery_locations))

    for geocell_id, geocell_imagery in imagery_locations.groupby('geocell_id'):

        geocell_img_path = os.path.join(images_path, str(geocell_id))
        if not os.path.exists(geocell_img_path):
            os.mkdir(geocell_img_path)

        for pano_id in geocell_imagery['pano_id']:
            # print(f'{geocell_id}, {pano_id}')
            download_image_from_api(pano_id, geocell_img_path, progress)

    progress.close()

    print('Done')


if __name__ == '__main__':
    # load environment variables
    load_dotenv()
    api_key = os.getenv('API_KEY')
    secret = os.getenv('SECRET')
    main()
