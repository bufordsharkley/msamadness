import math

import bs4
import numpy as np
import svgpathtools
from sklearn.linear_model import LinearRegression

# micropolitan color: cde5c1ff


def get_bounding(path):
    position, path = get_initial(path)
    min_xy = position
    max_xy = position
    while True:
        try:
            if path[0] == 'l':
                new_position, path = add_line(position, path)
            elif path[0] == 'c':
                new_position, path = add_curve(position, path)
            elif path[0] == 'h':
                new_position, path = add_horizontal(position, path)
            elif path[0] == 'v':
                new_position, path = add_vertical(position, path)
            elif path[0] == 'L':
                new_position, path = add_cap_line(path)
            else:
                print(path[0])
                print('need to')
                print(min_xy, max_xy)
                raise Exception
        except FinishedError:
            break
        min_xy, max_xy = update_for_new_extremes(new_position, min_xy, max_xy)
        position = new_position
    return min_xy, max_xy


def update_for_new_extremes(position, min_xy, max_xy):
    new_minx, new_miny = min_xy
    new_maxx, new_maxy = max_xy
    if position[0] < new_minx:
        new_minx = position[0]
    if position[0] > new_maxx:
        new_maxx = position[0]
    if position[1] < new_miny:
        new_miny = position[1]
    if position[1] > new_maxy:
        new_maxy = position[1]
    return (new_minx, new_miny), (new_maxx, new_maxy)


def add_cap_line(path):
    ii = get_current_path_segment(path)
    raise Exception(path[1:ii])


class FinishedError(Exception):
    pass


def get_current_path_segment(path):
    for ii, char in enumerate(path):
        if ii > 1 and char.isalpha():
            return unfuck_negatives(path[1:ii]), path[ii:]
    else:
        raise FinishedError


def add_vertical(position, path):
    path_segment, remainder = get_current_path_segment(path)
    return (position[0], position[1] + float(path_segment)), remainder


def add_horizontal(position, path):
    path_segment, remainder = get_current_path_segment(path)
    return (position[0] + float(path_segment), position[1]), remainder


def unfuck_negatives(path):
    resp = []
    for char in path:
        if char == '-':
            if resp and resp[-1].isdigit():
                resp.append(',')
        resp.append(char)
    return ''.join(resp)


def add_curve(position, path):
    path_segment, remainder = get_current_path_segment(path)
    path_segment = unfuck_negatives(path_segment)
    _, _, _, _, x, y = path_segment.split(',')
    #print(path_segment, unfuck_negatives(path_segment))
    return (position[0] + float(x), position[1] + float(y)), remainder


def add_line(position, path):
    path_segment, remainder = get_current_path_segment(path)
    increment = resolve_xy(path_segment)
    return (position[0] + increment[0], position[1] + increment[1]), remainder


def resolve_xy(text):
    if ',' in text:
        text = text.split(',')
    elif '-' in text[1:]:
        poz = text[1:].find('-')
        text = [text[:poz + 1], text[poz + 1:]]
    else:
        text = text.split()
    assert len(text) == 2
    return tuple(float(x) for x in text)


def get_initial(path):
    assert path[0] == 'M'
    path_segment, remainder = get_current_path_segment(path)
    initial = resolve_xy(path_segment)
    return initial, remainder


def fetch_svg_data():
    with open('usa_counties.svg') as f:
        soup = bs4.BeautifulSoup(f.read(), "lxml").svg
    counties = {}
    for tag in soup:
        if type(tag) == bs4.element.NavigableString:
            if not tag.strip():
                continue
        elif tag.name == 'metadata':
            continue
        # Examine these:
        elif tag.name == 'sodipodi:namedview':
            continue
        elif tag.name == 'defs':
            continue
        elif tag.name == 'rect':
            continue
        elif tag.name == 'polyline':
            continue
        elif tag.name == 'line':
            continue
        elif tag.name == 'image':
            continue
        try:
            assert tag.name == 'path'
        except AssertionError:
            raise Exception(tag.name)
        tag_id = tag.attrs['id']
        try:
            style = tag.attrs['style']
        except KeyError:
            raise
        if '#999999' in style:  # Counties, based upon stroke edge
            path = tag.attrs['d']
            xmin, xmax, ymin, ymax = svgpathtools.parse_path(path).bbox()
            xx, yy, width, height = (xmin, 1981 - ymax,
                                     xmax - xmin, ymax - ymin)

            counties[tag_id] = (xx, yy, width, height)
            #bounding = get_bounding(path)
            #print(bounding)
    with open('all_county_paths.txt', 'w') as f:
        for cty in counties:
            f.write(cty + '\n')
    return counties


def lambert_to_xy(lon, lat, n=0.6304777, F=1.9550002, rho0=1.5071429, lon0=-96):
    rho = F / math.tan(math.pi / 4 + math.radians(lat) / 2) ** n
    theta = math.radians(n * (lon - lon0))
    x = rho * math.sin(theta)
    y = rho0 - rho * math.cos(theta)
    return x, y


def projection():
    """Testbed for getting info on how to project..."""
    test_data = """37	-94.618	1775.95	886.79
37	-103.002	1252.37	880.639
37	-109.045	875.627	904.484
37	-114.05	565.25	942.5
41.002	-104.053	1200.29	1200.56
43.001	-104.053	1207.04	1358.87
44.997	-104.057	1213.51	1516.51
45.945	-104.045	1217.39	1591.1
49	-104.049	1227.37	1829.97
33.425888	-117.676286	295.92099999999976	668.425000000004
45.010956	-69.833105	3062.3110000000006	1781.35
39.021534	-84.820305	2355.1859999999974	1116.7060000000001
"""
    latlon = []
    svgxy = []
    for line in test_data.splitlines():
        if not line.strip():
            continue
        lat, lon, x0, y0 = (float(x) for x in line.split('\t'))
        print('Lat/lon:')
        print(lat, lon)
        print('svg position (pre-projection):')
        print(x0, y0)
        x, y = lambert_to_xy(lat=lat, lon=lon)
        latlon.append((x, y))
        svgxy.append((x0, y0))
        print('svg position (post-projection):')
        print(x, y)
        print()
    latlon = np.array(latlon)
    svgxy = np.array(svgxy)
    model = LinearRegression().fit(latlon, svgxy)
    print(model.score(latlon, svgxy))
    print(model.intercept_)
    print(model.coef_)


    """
[1741.54382573 -249.69360205]
[[4468.12948234 -220.12499425]
 [ 218.0429939  4573.71039625]]
 
 # old version...
    [1740.3726504  -236.52944716]
    [[4500.20543145 -205.14614155]
    [ 210.99624672 4544.52603886]]
    """
    """
    for (x, y), (x0, y0) in zip(latlon, svgxy):
        print(linear_transform(x, y))
        print(x0, y0)
    """

    # testing lambert against test data from textbook:
    #x, y = lambert_to_xy(lon=-75, lat=35)
    #print((x, y))
    #print((.2966785, .2462112))

    # riverside
    lon, lat, _, _ = (-117.676286, 33.425888, 3.2413370000000015, 0.6539959999999994)
    x, y = lambert_to_xy(lat=lat, lon=lon)
    print(linear_transform(x, y))
    x, y, _, _ = (295.92099999999976, 668.425000000004, 210.4990000000006, 79.05399999999872)
    print(x, y)
    ('ME_PISCATAQUIS', 'path78')
    lon, lat, _, _ = (-69.833105, 45.010956, 1.0570440000000048, 1.563096999999999)
    x, y = lambert_to_xy(lat=lat, lon=lon)
    print(linear_transform(x, y))
    x, y, _, _ = (3062.3110000000006, 1781.35, 82.67900000000327, 130.53100000000052)
    print(x, y)
    ('OH_HAMILTON', 'path2894')
    lon, lat, _, _ = (-84.820305, 39.021534, 0.5640660000000111, 0.29052199999999573)
    x, y = lambert_to_xy(lat=lat, lon=lon)
    print(linear_transform(x, y))
    x, y, _, _ = (2355.1859999999974, 1116.7060000000001, 34.02400000000216, 21.454378253216305)
    print(x, y)


def linear_transform(x, y):
    """Based upon fit of post-lambert lat-lon to svg x y"""
    return (1741.54 + 4468.13 * x - 220.12 * y,
            -249.69 + 218.04 * x + 4573.71 * y)


def get_corners(ll_data):
    lon, lat, w, h = ll_data
    lon2, lat2 = lon + w, lat + h
    return (linear_transform(*lambert_to_xy(lat=lat, lon=lon)),
            linear_transform(*lambert_to_xy(lat=lat2, lon=lon2)))


def main():
    preliminary_match_stuff()
    return
    all_paths = set(x.strip() for x in open('all_county_paths.txt'))
    print(len(all_paths))
    matched_paths = []
    for line in open('prelim_counties.txt'):
        cty, path, score = line.rsplit(maxsplit=2)
        matched_paths.append(path)
    print(len(matched_paths))
    print(len(set(matched_paths)))
    for cty in all_paths - set(matched_paths):
        print(cty)


def preliminary_match_stuff():
    """Stuff to extract data, transform data, and eventually compile matches"""
    #projection()
    start_src = set()
    start_path = set()
    svg_counties = fetch_svg_data()
    lat_counties = fetch_ll_data()
    match_file = open('prelim_counties.txt', 'w')
    PRE_BUILD = True
    if PRE_BUILD is True:
        for line in open('start_counties.txt'):
            match_file.write(line)
            if line.startswith('#'):
                if len(line.strip()) == 1:
                    break
                continue
            cty, path, _ = line.rsplit(maxsplit=2)
            start_src.add(cty)
            start_path.add(path)
        svg_counties = {k: v for k, v in svg_counties.items()
                        if k not in start_path}
        lat_counties = {k: v for k, v in lat_counties.items()
                        if k not in start_src}
    threshold = 60
    matches = print_all_best_matches(lat_counties, svg_counties)
    while matches:
        print(len(matches))
        cty, path, score, margin = get_widest_margin(matches)
        line_to_write = '{} {} {}/{}'.format(cty, path, score, margin)
        print(line_to_write)
        matches = filter_matches(matches, cty, path)
        match_file.write(line_to_write + '\n')


def filter_matches(matches, filter_cty, filter_path):
    resp = {}
    for cty, scores in matches.items():
        if cty == filter_cty:
            continue
        resp[cty] = [x for x in scores if x[1] != filter_path]
    return resp



def get_widest_margin(matches):

    def calc_margin(scores):
        if len(scores) == 1:
            return 999999
        return (scores[1][0] - scores[0][0])/scores[0][0]


    margins = [(calc_margin(scores), cty, scores[0][1], scores[0][0])
            for cty, scores in matches.items()]
    margins.sort(reverse=True)
    margin, cty, path, score = margins[0]
    return cty, path, score, margin
    #raise StopIteration("You're done now")


def print_all_best_matches(lat_counties, svg_counties):
                           #threshold=None, fname=None, verbose=False):
    resp = {}
    for cty, ll_data in lat_counties.items():
        corners = get_corners(ll_data)
        scores = []
        for cty2, svg_data in svg_counties.items():
            dist = calc_dist(corners, svg_data)
            scores.append((dist, cty2))
        scores.sort()
        if scores[0][0] > 150:
            print("Probable error", cty, scores[:5])
        resp[cty] = scores
    return resp
    # Original stuff... need to delete
    matched_src = set()
    matched_paths = []
    margins = []
    for cty, ll_data in lat_counties.items():
        corners = get_corners(ll_data)
        new_min = 999999999
        min_cty = None
        scores = []
        for cty2, svg_data in svg_counties.items():
            dist = calc_dist(corners, svg_data)
            if verbose and dist < 50:
                print(cty2, dist)
            scores.append((dist, cty2))
            if dist < new_min:
                min_cty = cty2
                new_min = dist
        scores.sort()
        # Something must be wrong if this is the case:
        if scores[0][0] > 150:
            print(cty, scores[:5])
        margin = scores[1][0] - scores[0][0]
        if threshold is not None and margin > threshold:
            line_to_write = '{} {} {}/{}\n'.format(
                    cty, min_cty, new_min, margin)
            print(line_to_write)
            matched_src.add(cty)
            matched_paths.append(min_cty)
        else:
            margins.append(margin)
    if len(matched_paths) != len(set(matched_paths)):
        for path in matched_paths:
            if matched_paths.count(path) > 1:
                print(path)
        raise Exception(sorted(matched_paths))
    print(np.histogram(margins))
    return matched_src, matched_paths, max(margins)


def calc_dist(corners, svg_data):
    x1, y1, w, h = svg_data
    x2, y2 = x1 + w, y1 + h
    dist = 0
    for (xl, yl), (xs, ys) in zip(corners, ((x1, y1), (x2, y2))):
        dist += math.sqrt((xl-xs) ** 2 +  (yl-ys) ** 2)
    return dist


def fetch_ll_data():
    resp = {}
    with open('us-county-boundaries.csv') as f:
        for ii, line in enumerate(f):
            if ii == 0:
                continue
            data = line.split(';')
            assert len(data) == 21
            _, geo, _, _, _, _, name, _, state, *_ = data
            if state in ('PR', 'HI', 'VI', 'AK', 'GU', 'AS', 'MP'):
                continue
            name = name.upper()
            xmin, ymin, xmax, ymax = parse_geo(geo)
            resp["{}_{}".format(state, name)] = (xmin, ymin, xmax - xmin, ymax - ymin)
    return resp


def parse_geo(geo):
    xmin, ymin, xmax, ymax = [None] * 4
    for chunk in (geo.split('[[[', 1)[1].rsplit(']]]', 1)[0].split('], [')):
        try:
            x, y = (float(x) for x in chunk.split(', '))
        except ValueError:
            continue
        if xmin is None or x < xmin:
            xmin = x
        if xmax is None or x > xmax:
            xmax = x
        if ymin is None or y < ymin:
            ymin = y
        if ymax is None or y > ymax:
            ymax = y
    return xmin, ymin, xmax, ymax


if __name__ == "__main__":
    main()
