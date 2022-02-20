def parse_markdown_file(filename):
    """
    Read <filename> and parse contents
    """

    elements = {}
    markdown = ''

    with open(filename, 'r') as markdown_file:
        markdown = markdown_file.readlines()

    # These are the only elements that can be expected
    markdown_mapping = {
        '# ': 'story_title',    # h1
        '## ': 'posted',        # h2
        '### ': 'references',   # h3
        '**': 'story_list_title',  # Actually Markdown bold, misused here for alternate title casing for TOC
        '> ': 'blockquote',
        '!': 'image',
        '- ': 'li',
    }

    for line in markdown:

        line = line.rstrip()
        if line:
            paragraph = True

            for key in markdown_mapping:

                if line.startswith(key):
                    if markdown_mapping[key] in ['story_title', 'posted']:
                        elements[markdown_mapping[key]] = line.lstrip(key)
                    elif markdown_mapping[key] in ['story_list_title']:
                        elements[markdown_mapping[key]] = line[len(key):-len(key)]
                    elif markdown_mapping[key] == 'references':
                        elements['references'] = []
                    elif markdown_mapping[key] == 'li' and 'references' in elements:
                        elements['references'].append(line.lstrip(key))
                    elif markdown_mapping[key] in ['blockquote', 'image']:
                        if 'story_content' not in elements:
                            elements['story_content'] = []
                        elements['story_content'].append((markdown_mapping[key], line.lstrip(key)))

                    paragraph = False

            if paragraph:
                if 'story_content' not in elements:
                    elements['story_content'] = []
                elements['story_content'].append(('p', line))

    return elements
