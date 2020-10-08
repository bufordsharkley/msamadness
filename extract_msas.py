
import bs4
import cairosvg
import svgpathtools

STATES = {1: 'AL', 2: 'AK', 4: 'AZ', 5: 'AR', 6: 'CA', 8: 'CO', 9: 'CT',
    10: 'DE', 11: 'DC', 12: 'FL', 13: 'GA', 15: 'HI', 16: 'ID', 17: 'IL',
    18: 'IN', 19: 'IA', 20: 'KS', 21: 'KY', 22: 'LA', 23: 'ME', 24: 'MD',
    25: 'MA', 26: 'MI', 27: 'MN', 28: 'MS', 29: 'MO', 30: 'MT', 31: 'NE',
    32: 'NV', 33: 'NH', 34: 'NJ', 35: 'NM', 36: 'NY', 37: 'NC', 38: 'ND',
    39: 'OH', 40: 'OK', 41: 'OR', 42: 'PA', 44: 'RI', 45: 'SC', 46: 'SD',
    47: 'TN', 48: 'TX', 49: 'UT', 50: 'VT', 51: 'VA', 53: 'WA', 54: 'WV',
    55: 'WI', 56: 'WY', 72: 'PR', }


def expand_bbox(bbox, margin, max_width, max_height):
    return (bbox[0] - margin, bbox[1] - margin,
            bbox[2] + margin * 2, bbox[3] + margin * 2)
    return (max(bbox[0] - margin, 0), max(bbox[1] - margin, 0),
            bbox[2] + margin * 2, bbox[3] + margin * 2)


def main():
    #cairosvg.svg2png(url="/tmp/outfile3.svg", write_to="/tmp/output.png")
    msas, misas = fetch_cbsas()
    ordered = fetch_ordered_msas()
    #for idx in range(42):
    for idx, msa in enumerate(ordered):
        #if idx < 30:
        #    continue
        states = msa.split(', ')[1].split('-')
        if 'AK' in states or 'HI' in states:
            continue
        counties = msas[msa.replace('–', '--')]
        with open('/tmp/outfile2.svg') as f:
            soup = bs4.BeautifulSoup(f.read(), "lxml")
            svg = soup.svg
        ocean = svg.find('rect', attrs={'id': 'ocean'})
        cty_group = svg.find('g', attrs={'inkscape:label': 'counties'})
        d_paths = []
        paths = []
        county_set = set(counties)
        for tag in svg.find_all("path"):
            if tag['id'] in counties:
                path = svgpathtools.parse_path(tag['d'])
                d_paths.append(path)
                paths.append(tag)
                county_set.remove(tag['id'])
        if county_set:
            print('ERROR >>> {} {}'.format(county_set, msa))
        d_all = ' '.join(path.d() for path in d_paths)
        new_tag = soup.new_tag("path")
        new_tag['d'] = d_all
        new_tag['id'] = msa
        new_tag['stroke'] = '#29a449'
        new_tag['stroke-width'] = '2.0'
        new_tag['fill'] = 'none'
        path = svgpathtools.parse_path(d_all)
        bbox = path.bbox()
        bbox = (bbox[0], bbox[2], bbox[1] - bbox[0], bbox[3] - bbox[2])
        bbox = expand_bbox(bbox, 100, float(ocean['width']), float(ocean['height']))
        #raise Exception([x['id'] for x in canvas_min])
        viewbox = " ".join(str(x) for x in bbox)
        svg['viewBox'] = viewbox
        #157 302 500 500
        #svg['viewBox'] = "200 300 400 500"
        svg['height'] = 800
        svg['width'] = 800
        cty_group.append(new_tag)
        for path in paths:
            path['style'] = "clip-rule:evenodd;fill:#9fd08a;fill-opacity:1;fill-rule:evenodd;stroke:#999999;stroke-width:0.2;stroke-miterlimit:4;stroke-dasharray:none"
            cty_group.append(path)
        """
        start = paths[0]
        for path in paths[1:]:
            start = path_union(start, path)
        raise Exception(start)
        new_tag = soup.new_tag("path")
        print(dir(start))
        new_tag['d'] = start.d()
        new_tag['id'] = msa
        #svg.append(new_tag)
        """
        with open('/tmp/outfile3.svg', 'w') as f:
            f.write(svg.prettify())
        cairosvg.svg2png(url="/tmp/outfile3.svg", write_to="/tmp/{:03}.png".format(idx))
    """
    if tag.name != 'path':
        continue
    style = tag.attrs['style']
    if '#999999' not in style:  # Counties, based upon stroke edge
        continue
    tag_id = tag.attrs['id']
    if '_' not in tag_id:
        continue
    new_tag = soup.new_tag("title")
    new_tag.string = tag_id
    tag.append(new_tag)
    """



def fetch_cbsas():
    msas = {}
    misas = {}
    for ii, line in enumerate(open('msa_def.csv')):
        if ii < 3:
            continue
        line = line.split('\t')
        if len(line) != 12:
            raise Exception
        if not line[0].strip():
            continue
        if line[0].startswith('Note: The 2010 OMB Standards for'):
            continue
        if line[0].startswith('Source:'):
            continue
        if line[0].startswith('Internet Release Date:'):
            continue
        _, _, _, cbsa, cbsa_type, _, _, county, _, state_code, *_ = line
        state_code = int(state_code)
        if state_code in (72, 2):
            continue
        if cbsa_type.startswith('Metropolitan'):
            cb_dict = msas
        elif cbsa_type.startswith('Micropolitan'):
            cb_dict = misas
        else:
            raise Exception(cbsa_type)
        key = get_key(county, state_code)
        if cbsa in cb_dict:
            cb_dict[cbsa].add(key)
        else:
            cb_dict[cbsa] = {key}
    return msas, misas


def get_key(county, state_code):
    if any(county.endswith(x) for x in (' County', ' Parish', ' city')):
        county = county.rsplit(' ', 1)[0]
    return '{}_{}'.format(STATES[state_code], county.upper())


def fetch_ordered_msas():
    resp = []
    for line in open('msa.txt'):
        line = line.split('\t')
        _, msa, *_ = line
        msa, state = msa.rsplit(', ', 1)
        state = state.split()[0]
        msa = msa + ', ' + state
        resp.append(msa)
    return resp

if __name__ == "__main__":
    main()
