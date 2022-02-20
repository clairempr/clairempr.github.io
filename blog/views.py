import glob
import os
import re
import shutil

from datetime import datetime

from django.conf import settings
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.html import format_html
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Make sure we're starting with clean output
        self.remove_output_files()

        # Copy static files from input directory to output directory
        self.copy_static_files()

        stories = self.generate_story_pages()

        context['page_title'] = settings.BLOG_TITLE
        context['stories'] = stories

        # Generate index page
        html_string = render_to_string(self.template_name, context)
        self.save_index_page(html=html_string)

        return context

    def remove_output_files(self):
        """
        Remove certain files from output directory and subdirectories
        """

        # Main index page
        print('Removing ', settings.OUTPUT_DIR / 'index.html')
        # os.remove(settings.OUTPUT_DIR / 'index.html')

        # Stylesheet
        print('Removing ', settings.OUTPUT_DIR / 'style.css')
        # os.remove(settings.OUTPUT_DIR / 'style.css')

        # Pages
        for file in os.listdir(settings.OUTPUT_PAGES_DIR):
            print('Removing ', settings.OUTPUT_PAGES_DIR, file)
            # os.remove(settings.OUTPUT_PAGES_DIR, file)

        # Images
        for file in os.listdir(settings.OUTPUT_IMAGES_DIR):
            print('Removing ', settings.OUTPUT_IMAGES_DIR, file)
            # os.remove(settings.OUTPUT_IMAGES_DIR / file)


    def copy_static_files(self):
        """
        Copy all files except Markdown files from input directory to output directory
        """

        for root, dirs, files in os.walk(settings.INPUT_DIR):
            for file in files:
                if not file.endswith('.md'):
                    source = os.path.join(root, file)
                    destination = source.replace(str(settings.INPUT_DIR), str(settings.OUTPUT_DIR))
                    print('Copying {} to {}'.format(source, destination))
                    # shutil.copy(source, destination)

    def generate_story_pages(self):
        """
        Generate stories from markdown files and return list of stories

        A story has a filename, title, and date posted
        """

        stories = []

        markdown_files = self.get_list_of_markdown_files()

        for markdown_file in markdown_files:
            html_filename = os.path.basename(markdown_file).replace('.md', '.html')
            markdown_elements = parse_markdown_file(markdown_file)

            self.generate_story_page(markdown_elements=markdown_elements, html_filename=html_filename)

            date_posted = datetime.strptime(markdown_elements['posted'].lstrip('Posted '), '%b. %d, %Y').date()
            story_elements = (html_filename, markdown_elements['story_list_title'], date_posted)
            stories.append(story_elements)

        # Sort the list by date posted, in descending order
        stories.sort(key=lambda x: x[2], reverse=True)
        return stories

    def generate_story_page(self, markdown_elements, html_filename):
        """
        Generate a story page using elements from the markdown file to fill the template
        """
        context = {}

        context['story_title'] = markdown_elements['story_title']
        context['posted'] = markdown_elements['posted']
        context['story_content'] = render_story_content(markdown_elements['story_content'])
        context['references'] = render_references(markdown_elements['references'])

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

            date_posted = datetime.strptime(markdown_elements['posted'].lstrip('Posted '), '%b. %d, %Y').date()
            story_elements = (html_filename, markdown_elements['story_list_title'], date_posted)
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

        context['story_title'] = markdown_elements['story_title']
        context['posted'] = markdown_elements['posted']
        context['story_content'] = render_story_content(markdown_elements['story_content'])
        context['references'] = render_references(markdown_elements['references'])

        return context


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
                html = render_paragraph(element_content)
        elif element_type == 'blockquote':
            html = render_blockquote(element_content)
        elif element_type == 'image':
            html = render_image(element_content)

        story_content.append(html)

    return story_content


def render_blockquote(element_content):
    quote = element_content.split('> ')[0]
    html = render_to_string('blog/blog_to_generate/partials/blockquote.html',
                            context={'quote': quote})
    return html


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
    first_word = element_content.split(' ')[0]
    rest_of_paragraph = element_content.lstrip(first_word)
    html = render_to_string('blog/blog_to_generate/partials/lead_paragraph.html',
                            context={'first_letter': first_word[0],
                                     'rest_of_first_word': first_word[1:],
                                     'rest_of_paragraph': rest_of_paragraph})
    return html


def render_paragraph(element_content):
    html = render_to_string('blog/blog_to_generate/partials/paragraph.html',
                            context={'paragraph': element_content})
    return html


def render_references(element_content):
    rendered_references = []
    for element in element_content:
        if element.rstrip():
            rendered_reference = format_html(element)
            rendered_references.append(rendered_reference)
    return rendered_references
