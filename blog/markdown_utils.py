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
            paragraph = True

            for key in markdown_mapping:

                if line.startswith(key):

                    if markdown_mapping[key] == 'code':
                        if line.startswith(key):
                            code_block = [line]
                            line = ''
                            while not line.startswith(key):
                                line = next(markdown)
                                code_block.append(line)
                            append_story_content(elements=elements, content_type=markdown_mapping[key],
                                                 content='\n'.join(code_block))

                    elif markdown_mapping[key] in ['story_title', 'story_list_title', 'date_posted']:
                        elements[markdown_mapping[key]] = line.lstrip(key)
                    elif markdown_mapping[key] == 'references':
                        elements['references'] = []
                    elif markdown_mapping[key] == 'li' and 'references' in elements:
                        elements['references'].append(line.lstrip(key))
                    elif markdown_mapping[key] in ['blockquote', 'image']:
                        append_story_content(elements=elements, content_type=markdown_mapping[key],
                                             content=line.lstrip(key))
                    elif markdown_mapping[key] in ['h1', 'h2', 'h3', 'bold', 'italic']:
                        # Don't strip the markdown from elements that can be handled by real formatter
                        append_story_content(elements=elements, content_type=markdown_mapping[key],
                                             content=line)

                    paragraph = False

            if paragraph:
                append_story_content(elements=elements, content_type='p', content=line)

    return elements


def append_story_content(elements, content_type, content):
    """
    Append content to story_content list in markdown elements
    """
    if 'story_content' not in elements:
        elements['story_content'] = []

    elements['story_content'].append((content_type, content))
    return elements
