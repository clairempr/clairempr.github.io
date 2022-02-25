def parse_markdown_file(filename):
    """
    Read <filename> and parse contents
    """

    elements = {}
    markdown = ''

    with open(filename, 'r') as markdown_file:
        # Use a generator so code block lines can be consumed without going through the main loop
        markdown = (line for line in markdown_file.readlines())

    # These are the only elements that can be expected
    markdown_mapping = {
        '# ': 'story_title',            # h1
        '## ': 'posted',                # h2
        '### ': 'references',           # h3
        '#### ': 'story_list_title',    # h4
        '> ': 'blockquote',
        '```': 'code',
        '!': 'image',
        '- ': 'li',
    }

    for line in markdown:

        line = line.rstrip()
        if line:
            paragraph = True

            for key in markdown_mapping:

                if line.startswith(key):

                    if markdown_mapping[key] == 'code':
                        if line.startswith(key):
                            code_block = []
                            line = ''

                            while not line.startswith(key):
                                line = next(markdown)
                                if not line.startswith(key):
                                    code_block.append(line)

                            if 'story_content' not in elements:
                                elements['story_content'] = []
                            elements['story_content'].append((markdown_mapping[key], '\n'.join(code_block)))

                    elif markdown_mapping[key] in ['story_title', 'posted']:
                        elements[markdown_mapping[key]] = line.lstrip(key)
                    elif markdown_mapping[key] in ['story_list_title']:
                        elements[markdown_mapping[key]] = line[len(key):]
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
