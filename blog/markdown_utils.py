def parse_markdown_file(filename):
    """
    Read <filename> and parse contents
    """

    elements = {}
    markdown = ''

    with open(filename, 'r') as markdown_file:
        # Use a generator so code block lines can be consumed without going through the main loop
        markdown = (line for line in markdown_file.readlines())

    # These are the specific elements that can be expected
    # Anything else is treated as misc. story content and will be converted to html
    # by the real markdown formatter
    markdown_mapping = {
        '_story_title ': 'story_title',
        '_date_posted ': 'date_posted',
        '_references ': 'references',
        '_story_list_title ': 'story_list_title',
        '# ': 'h1',
        '## ': 'h2',
        '### ': 'h3',
        '**': 'bold',
        '*': 'italic',
        '> ': 'blockquote',
        '```': 'code',
        '!': 'image',
        '- ': 'li',
    }

    for line in markdown:

        line = line.rstrip()
        if line:
            misc_element = True

            for key in markdown_mapping:

                if line.startswith(key):

                    if markdown_mapping[key] == 'code':
                        if line.startswith(key):
                            code_block = []
                            code_block.append(line)
                            line = ''

                            while not line.startswith(key):
                                line = next(markdown)
                                code_block.append(line)

                            if 'story_content' not in elements:
                                elements['story_content'] = []
                            elements['story_content'].append((markdown_mapping[key], '\n'.join(code_block)))

                    elif markdown_mapping[key] in ['story_title', 'date_posted']:
                        elements[markdown_mapping[key]] = line.lstrip(key)
                    elif markdown_mapping[key] in ['story_list_title']:
                        elements[markdown_mapping[key]] = line[len(key):]
                    elif markdown_mapping[key] == 'references':
                        elements['references'] = []
                    elif markdown_mapping[key] == 'li' and 'references' in elements:
                        elements['references'].append(line.lstrip(key))
                    elif markdown_mapping[key] in ['h1', 'h2', 'h3', 'bold', 'italic', 'blockquote', 'image']:
                        if 'story_content' not in elements:
                            elements['story_content'] = []
                        if markdown_mapping[key] in ['h1', 'h2', 'h3', 'bold', 'italic']:
                            # Don't strip the markdown from elements that can be handled by real formatter
                            story_content_line = line
                        else:
                            story_content_line = line.lstrip(key)
                        elements['story_content'].append((markdown_mapping[key], story_content_line))

                    misc_element = False

            if misc_element:
                if 'story_content' not in elements:
                    elements['story_content'] = []
                elements['story_content'].append(('p', line))

    return elements
