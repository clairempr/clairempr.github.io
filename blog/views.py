import glob
import markdown
import os
import re
import shutil

from datetime import datetime
from os.path import exists

from django.conf import settings
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView, View

from blog.markdown_utils import parse_markdown_file


class HomeView(TemplateView):
    template_name = 'blog/home.html'


class GenerateBlogView(TemplateView):
    """
    Generate index.html and stories

    Show generated index.html
    """

    template_name = "blog/blog_to_generate/index.html"

    # Urls for pages and css files in generated pages need to point to their locations
    # at github.io, and not to local copies
    local_blog = False

    def get(self, request, *args, **kwargs):
        """
        Remove existing output files (html, images, css)

        Create new index page and story pages, and copy css and image files
        from input dirs to output
        """

        # Make sure we're starting with clean output
        self.remove_output_files()

        # Copy static files from input directory to output directory
        self.copy_static_files()

        context = self.get_context_data(**kwargs)

        # Generate index page
        html_string = render_to_string(self.template_name, context)
        self.save_index_page(html=html_string)

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['local_blog'] = self.local_blog
        context['page_title'] = settings.BLOG_TITLE

        stories = self.generate_story_pages()

        context['stories'] = stories

        return context

    def remove_output_files(self):
        """
        Remove certain files from output directory and subdirectories
        """

        # Main index page
        path_to_file = settings.OUTPUT_DIR / 'index.html'
        if exists(path_to_file):
            os.remove(path_to_file)

        # Stylesheets
        stylesheets = glob.glob(str(settings.OUTPUT_DIR) + '/*.css')
        for stylesheet in stylesheets:
            path_to_file = settings.OUTPUT_DIR / stylesheet
            if exists(path_to_file):
                os.remove(path_to_file)

        # Pages
        for file in os.listdir(settings.OUTPUT_PAGES_DIR):
            os.remove(settings.OUTPUT_PAGES_DIR / file)

        # Images
        for file in os.listdir(settings.OUTPUT_IMAGES_DIR):
            os.remove(settings.OUTPUT_IMAGES_DIR / file)

    def copy_static_files(self):
        """
        Copy all files except Markdown files from input directory to output directory
        """

        for root, dirs, files in os.walk(settings.INPUT_DIR):
            for file in files:
                if not file.endswith('.md'):
                    source = os.path.join(root, file)
                    destination = source.replace(str(settings.INPUT_DIR), str(settings.OUTPUT_DIR))
                    shutil.copy(source, destination)

    def generate_story_pages(self):
        """
        Generate stories from markdown files and return list of stories

        A story has a filename, title, and date posted or updated
        """

        stories = []

        markdown_files = self.get_list_of_markdown_files()

        for markdown_file in markdown_files:
            html_filename = os.path.basename(markdown_file).replace('.md', '.html')
            markdown_elements = parse_markdown_file(markdown_file)

            self.generate_story_page(markdown_elements=markdown_elements, html_filename=html_filename)

            story_list_title = get_story_list_title_from_markdown(markdown_elements)
            updated = 'Updated' in get_date_posted_from_markdown(markdown_elements)
            date = datetime.strptime(get_date_posted_from_markdown(markdown_elements).lstrip('Posted ').lstrip('Updated '),
                                     '%b. %d, %Y').date()
            story_elements = (html_filename, story_list_title, date, updated)
            stories.append(story_elements)

        # Sort the list by date posted, in descending order
        stories.sort(key=lambda x: x[2], reverse=True)
        return stories

    def generate_story_page(self, markdown_elements, html_filename):
        """
        Generate a story page using elements from the markdown file to fill the template
        """

        context = {'local_blog': self.local_blog,
                   'story_title': get_story_title_from_markdown(markdown_elements),
                   'date_posted': get_date_posted_from_markdown(markdown_elements),
                   'story_content': render_story_content(get_story_content_from_markdown(markdown_elements)),
                   'html_filename': html_filename,
                   }

        if 'references' in markdown_elements:
            context['references'] = render_references(markdown_elements['references'])

        # If comments are enabled, add comment-related stuff to context
        if settings.STATICMAN_URL:
            context['staticman_url'] = settings.STATICMAN_URL
            context['comments_url'] = settings.COMMENTS_URL
            context['comment_file_type'] = settings.COMMENT_FILE_TYPE
            context['reCaptcha_site_key'] = settings.RECAPTCHA_SITE_KEY
            context['reCaptcha_secret_key'] = settings.RECAPTCHA_SECRET_KEY

        html_string = render_to_string(settings.STORY_TEMPLATE, context)
        html_file_path = settings.OUTPUT_PAGES_DIR / html_filename

        with open(html_file_path, 'w+') as f:
            f.write(html_string)

    def get_list_of_markdown_files(self):
        return glob.glob(str(settings.INPUT_PAGES_DIR) + '/*.md')

    def save_index_page(self, html):
        """
        Save generated page to index.html in output directiry
        """
        filename = settings.OUTPUT_DIR / 'index.html'

        with open(filename, 'w+') as f:
            f.write(html)


class GenerateLocalBlogView(GenerateBlogView):
    """
    The only difference between GenerateLocalBlogView and GenerateBlogView
    is that GenerateLocalBlogView creates pages with paths pointing to local
    copies of pages and css files
    """

    # Urls for pages, images, and css files in generated pages need to point to local copies,
    # not to their locations at github.io
    local_blog = True


class GeneratedIndexView(TemplateView):
    """
    Show generated index.html
    """

    template_name = "blog/blog_to_generate/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['page_title'] = 'This page intentionally left blank'
        context['stories'] = self.get_stories()

        return context

    def get_stories(self):
        """
        Return list of stories

        A story has a filename, title, and date posted
        """

        stories = []

        markdown_files = glob.glob(str(settings.INPUT_PAGES_DIR) + '/*.md')

        for markdown_file in markdown_files:
            html_filename = os.path.basename(markdown_file).replace('.md', '.html')
            markdown_elements = parse_markdown_file(markdown_file)

            date_posted = datetime.strptime(get_date_posted_from_markdown(markdown_elements).lstrip('Posted '), '%b. %d, %Y').date()
            story_elements = (html_filename, get_story_list_title_from_markdown(markdown_elements), date_posted)
            stories.append(story_elements)

        # Sort the list by date posted, in descending order
        stories.sort(key=lambda x: x[2], reverse=True)
        return stories


class GeneratedStoryView(TemplateView):
    """
    Show generated story page
    """

    template_name = settings.STORY_TEMPLATE

    markdown_file = None

    def post(self, request, *args, **kwargs):
        self.markdown_file = request.POST.get('markdown_file', None)
        context = self.get_context_data()

        html_string = render_to_string(self.template_name, context)
        html_filename = settings.OUTPUT_PAGES_DIR / self.markdown_file.replace('.md', '.html')

        with open(html_filename, 'w+') as f:
            f.write(html_string)

        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        markdown_file_path = settings.INPUT_PAGES_DIR / self.markdown_file
        markdown_elements = parse_markdown_file(markdown_file_path)

        context['story_title'] = get_story_title_from_markdown(markdown_elements)
        context['date_posted'] = get_date_posted_from_markdown(markdown_elements)
        context['story_content'] = render_story_content(get_story_content_from_markdown(markdown_elements))
        context['references'] = render_references(markdown_elements['references'])

        return context


def get_date_posted_from_markdown(markdown_elements):
    return markdown_elements['date_posted'] if 'date_posted' in markdown_elements else 'Undated'


def get_story_title_from_markdown(markdown_elements):
    return markdown_elements['story_title'] if 'story_title' in markdown_elements else 'Untitled'


def get_story_list_title_from_markdown(markdown_elements):
    return markdown_elements['story_list_title'] if 'story_list_title' in markdown_elements else 'Untitled'


def get_story_content_from_markdown(markdown_elements):
    return markdown_elements['story_content'] if 'story_content' in markdown_elements else ''


def render_story_content(elements):
    """
    Return story content
    """

    story_content = []
    lead_paragraph = True

    for element_type, element_content in elements:

        html = ''

        if element_type == 'p':
            if lead_paragraph:
                html = render_lead_paragraph(element_content)
                lead_paragraph = False
            else:
                # This is not necessarily a paragraph - it could be anything not specifically
                # recognized by this application
                html = render_paragraph(element_content)
        elif element_type in ['h1', 'h2', 'h3', 'bold', 'italic']:
            html = render_misc_element(element_content)
        elif element_type == 'blockquote':
            html = render_blockquote(element_content)
        elif element_type == 'large_blockquote':
            html = render_large_blockquote(element_content)
        elif element_type == 'image':
            html = render_image(element_content)
        elif element_type == 'code':
            html = render_code(element_content)

        story_content.append(html)

    return story_content


def render_blockquote(element_content):
    html = render_to_string('blog/blog_to_generate/partials/blockquote.html',
                            context={'quote': element_content})
    return html


def render_large_blockquote(element_content):
    html = render_to_string('blog/blog_to_generate/partials/large_blockquote.html',
                            context={'quote': element_content})
    return html


def render_code(element_content):
    # Code block might contain language name for syntax highlighting,
    # so convert it to html with markdown package
    code = markdown.markdown(element_content, extensions=['fenced_code', 'codehilite'])
    # Use mark_safe() instead of format_html() because paragraph may contain curly braces,
    # and that will cause an error with format_html()
    html = render_to_string('blog/blog_to_generate/partials/code_block.html',
                            context={'code_block': mark_safe(code)})
    return html


def render_misc_element(element_content):
    """
    Elements that can be handled by real Markdown formatter
    """
    return format_html(markdown.markdown(element_content))


def render_image(element_content):
    # !["Contrabands"](../images/contrabands_cropped.jpg 'Culpeper, Va. "Contrabands"')
    image_regex = '\[([^\]]*)\]\((.*?)(?=[\"\']|\))([\"\'].*[\"\'])?\)'
    # The Markdown standard doesn't support image sizing, so I just stuck it in there
    # !["Contrabands"](../images/contrabands_cropped.jpg width="500" 'Culpeper, Va. "Contrabands"')
    image_regex_with_width = '\[([^\]]*)\]\((.*?)(?=[\"\']|)\swidth\=[\"\']([0-9]+)[\"\']\s([\"\'].*[\"\'])\)'
    matches = re.search(image_regex_with_width, element_content)
    alt_text = matches.group(1)
    image = matches.group(2)
    width = matches.group(3)
    caption = matches.group(4)
    # Caption match group includes double or single quotes around caption, so remove them
    caption = caption[1:-1]
    html = render_to_string('blog/blog_to_generate/partials/image.html',
                            context={'image': image, 'alt_text': alt_text,
                                     'width': width, 'caption': caption})
    return html


def render_lead_paragraph(element_content):
    # Paragraph might contain links or other inline markdown elements,
    # so convert it to html with markdown package, but strip off outer paragraph tags
    # because they'll show up as text
    first_word = element_content.split(' ')[0]
    rest_of_paragraph = markdown.markdown(element_content.lstrip(first_word)).lstrip('<p>').rstrip('</p>')

    # There's a weird bug where if the first letter of the rest of the paragraph is "p",
    # then it gets cut off. This also happens when the markdown isn't converted into html.
    #
    # Hopefully this is just a temporary hack
    if rest_of_paragraph:
        first_letter_rest_of_paragraph = element_content.lstrip(first_word)[1] if len(first_word) > 1 else ''
        if first_letter_rest_of_paragraph != rest_of_paragraph[0]:
            rest_of_paragraph = '{}{}'.format(first_letter_rest_of_paragraph, rest_of_paragraph)
    # Use mark_safe() instead of format_html() because paragraph may contain curly braces,
    # and that will cause an error with format_html()
    html = render_to_string('blog/blog_to_generate/partials/lead_paragraph.html',
                            context={'first_letter': first_word[0],
                                     'rest_of_first_word': first_word[1:],
                                     'rest_of_paragraph': mark_safe(rest_of_paragraph)})
    return html


def render_paragraph(element_content):
    # Paragraph might contain links or other inline markdown elements,
    # so convert it to html with markdown package, but strip off outer paragraph tags
    # because they'll show up as text
    paragraph = markdown.markdown(element_content)
    # Use mark_safe() instead of format_html() because paragraph may contain curly braces,
    # and that will cause an error with format_html()
    html = render_to_string('blog/blog_to_generate/partials/paragraph.html',
                            context={'paragraph': mark_safe(paragraph)})
    return html


def render_references(element_content):
    rendered_references = []
    for element in element_content:
        if element.rstrip():
            rendered_reference = format_html(element)
            rendered_references.append(rendered_reference)
    return rendered_references
