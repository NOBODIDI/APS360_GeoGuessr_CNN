import requests
import os
import urllib.parse
import pandas as pd
import numpy as np
import folium
from dotenv import load_dotenv
from tqdm import tqdm

from api_request_signature import sign_url


def generate_random_locations(geocell, seed, limit_factor):

    span_lat = abs(geocell['lat_top'] - geocell['lat_bottom'])
    span_lon = abs(geocell['lon_right'] - geocell['lon_left'])

    np.random.seed(seed)
    images_lat = np.random.rand(images_per_geocell * limit_factor)  # random values between 0 and 1
    images_lat = (images_lat * span_lat + geocell['lat_bottom']).round(6)  # stretch and shift to match cell bounds
    images_lon = np.random.rand(images_per_geocell * limit_factor)
    images_lon = (images_lon * span_lon + geocell['lon_left']).round(6)

    images_loc = list(zip(images_lat, images_lon))  # list of tuples of (lat, lon)

    return images_loc


def query_metadata_api(location: tuple[float, float], search_radius: int) -> (tuple[float, float], str):

    # print(f'querying metadata api for location {location}')

    params = {
        'location': f'{location[0]},{location[1]}',
        'key': api_key,
        'radius': search_radius
    }

    url = 'https://maps.googleapis.com/maps/api/streetview/metadata?' + urllib.parse.urlencode(params)
    url = sign_url(url, secret)
    r = requests.get(url)
    r_content = r.json()

    if r_content['status'] == 'ZERO_RESULTS':
        # print(f'no imagery found')
        return None, None

    if r_content['status'] != 'OK':
        print(f'Warning: API error: {r_content["status"]}')
        return None, None

    # response status is OK, imagery found
    # print(r_content['copyright'])
    # imagery must originate from Google official coverage
    if 'Google' in r_content['copyright'] and len(r_content['copyright'].split(' ')) <= 2:
        lat = round(float(r_content['location']['lat']), 6)
        lon = round(float(r_content['location']['lng']), 6)
        return (lat, lon), r_content['pano_id']
    else:
        return None, None


def process_locations(images_loc: list[tuple[float, float]], search_radius):

    valid_loc_count = 0
    processed_img_loc = []

    for loc in images_loc:
        actual_img_loc, pano_id = query_metadata_api(loc, search_radius)  # query metadata api to search for valid image nearby
        if actual_img_loc is None:  # if no valid image found within search radius, skip to next location
            continue
        processed_img_loc.append((actual_img_loc[0], actual_img_loc[1], pano_id))  # record actual image location
        valid_loc_count += 1
        if valid_loc_count >= images_per_geocell:  # if enough valid images have been found, stop the search
            break

    if valid_loc_count < images_per_geocell:
        return processed_img_loc, False  # did not find enough valid images after trying all provided locations
    else:
        return processed_img_loc, True  # enough valid images found


def main():

    geocells = pd.read_csv(os.path.join('data', 'geocell_coordinates_v3_cleaned.csv'))
    print(f'{len(geocells)} total geocells provided in input')

    geocells = geocells[geocells['include'] == 1].reset_index(drop=True)  # exclude ones manually labelled to be dropped
    print(f'Generating {images_per_geocell} sample locations for each of the {len(geocells)} included geocells')

    np.random.seed(50)
    random_seeds = (np.random.rand(len(geocells)) * 1000).astype(int)  # generate a random seed between 0 and 1000 for every geocell

    m = folium.Map(location=[44.967243, -103.771556], zoom_start=3)
    geocells['valid_loc_count'] = 0
    final_locations = pd.DataFrame(columns=['geocell_id', 'pano_id', 'img_lat', 'img_lon'])

    progress = tqdm(total=len(geocells))

    for i, geocell in geocells.iterrows():

        geocell_id = int(geocell['geocell_id'])

        if geocell_id in [39, 40, 65, 67, 71, 113, 149, 150, 169, 187, 224]:
            search_radius = 15000
            limit_factor = 5
        else:
            search_radius = 5000
            limit_factor = 5

        cell_colour = 'green'

        init_img_loc = generate_random_locations(geocell, random_seeds[i], limit_factor)
        proc_img_loc, valid = process_locations(init_img_loc, search_radius)
        geocells.loc[i, 'valid_loc_count'] = len(proc_img_loc)
        if not valid:
            cell_colour = 'red'
            # raise Exception(f'geocell {geocell_id} not valid, count {len(proc_img_loc)}')
            print(f'Warning: geocell {geocell_id} only has {len(proc_img_loc)} valid locations')

        folium.vector_layers.Rectangle(bounds=[
            (geocell['lat_top'], geocell['lon_left']),
            (geocell['lat_top'], geocell['lon_right']),
            (geocell['lat_bottom'], geocell['lon_right']),
            (geocell['lat_bottom'], geocell['lon_left'])
        ], popup=f'ID: {geocell_id}', tooltip=f'Valid: {len(proc_img_loc)}',
            fill=True, fill_color=cell_colour).add_to(m)

        if valid:
            # store the processed imagery locations
            img_loc_df = pd.DataFrame(proc_img_loc, columns=['img_lat', 'img_lon', 'pano_id'])
            img_loc_df['geocell_id'] = geocell_id
            final_locations = pd.concat([final_locations, img_loc_df], ignore_index=True)
            # plot the imagery locations on the map
            for lat, lon, pano_id in proc_img_loc:
                sv_url = f'<a href=http://maps.google.com/maps?q=&layer=c&cbll={lat},{lon} target=_blank>' \
                         f'{lat},{lon}</a>'
                folium.vector_layers.CircleMarker(location=(lat, lon), popup=sv_url, tooltip=pano_id, radius=3,
                                                  stroke=False, fill_color='green', fill_opacity=0.8).add_to(m)

        progress.update()

    progress.close()

    print('Saving files')
    m.save(os.path.join('data', 'imagery_locations.html'))
    geocells.to_csv(os.path.join('data', 'processed_geocells.csv'), index=False)
    final_locations.to_csv(os.path.join('data', 'imagery_locations.csv'), index=False)

    print('Done')


if __name__ == '__main__':
    # load environment variables
    load_dotenv()
    api_key = os.getenv('API_KEY')
    secret = os.getenv('SECRET')
    # define global parameter variables
    images_per_geocell = 100
    main()
