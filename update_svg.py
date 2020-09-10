import sys

import bs4


def main():
    update_labels()
    update_titles_with_label()
    return
    if len(sys.argv) > 1:
        update_titles_with_label()
    else:
        update_labels()


def update_titles_with_label():
    with open('/tmp/outfile.svg') as f:
        soup = bs4.BeautifulSoup(f.read(), "lxml")
        svg = soup.svg
    for tag in svg:
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
    with open('/tmp/outfile2.svg', 'w') as f:
        f.write(soup.prettify())


def update_labels():
    with open('usa_counties.svg') as f:
        soup = bs4.BeautifulSoup(f.read(), "lxml")
        svg = soup.svg
    for ii, line in enumerate(open('prelim_counties.txt')):
        if line.startswith("#"):
            if len(line.strip()) == 1:
                break
            continue
        cty, path, score = line.rsplit(maxsplit=2)
        tag = svg.find(id=path)
        #assert len(tags) == 1
        #tag = tags[0]
        tag['id'] = cty
        style = tag['style']
        assert "fill:#ffffff" in style
        state = cty.split('_')[0]
        newcolor = get_color(state)
        tag['style'] = style.replace("fill:#ffffff",
                                     "fill:#{}".format(newcolor))
        if ii % 10 == 0:
            print(ii)
    with open('/tmp/outfile.svg', 'w') as f:
        f.write(soup.prettify())


def get_color(state):
    try:
        newcolor = {'TN': 'ffd5f6',
                    'IN': 'e3dbde',
                    'NH': 'e3dbdf',
                    'AL': 'eeaaee',
                    'GA': 'e5d5ff',
                    'NM': 'ffaaee',
                    'ME': 'aaeeff',
                    'MO': 'afe9c6',
                    'NC': 'afe9c7',
                    'NJ': 'afe9c8',
                }[state]
    except KeyError:
        newcolor = "d5ff" + hex((sum(ord(x) for x in state) - 130) * 5)[-2:]
    return newcolor


if __name__ == "__main__":
    main()
