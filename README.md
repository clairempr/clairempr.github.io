# https://clairempr.github.io

## quick & dirty blog generator

with an emphasis on **dirty**

### Uses custom Markdown to generate html "story" pages

- `_story_title `: Story Title
- `_date_posted `: Posted `date`  
- `_references `: References header (will always be "References")
- `story_list_title `: Story title on main blog page
- `_large_blockquote` : Blockquote but a bit larger, with even bigger quotation marks  
- `# `: H1  
- `## `: H2  
- `### `: H3  
-`** **`: Bold
- `> `: Blockquote  
- '```': Code block,
- Images use modified markdown to allow for setting width  
`![Alt text](https://path/to/image.jpg width="500" 'Image caption')`  
- `- `: Reference list item
- Anything else will be treated as a paragraph and fed through the real Markdown formatter   

### To generate blog index page and story pages

#### Install requirements 

#### Change blog title if "quick & dirty blog" isn't good enough  
See setting `BLOG_TITLE` in `quick_and_dirty_blog.settings`

#### Create Markdown files for stories  
Create Markdown files with extension ".md" and put them in `INPUT_PAGES_DIR`  
Any images go in `INPUT_IMAGES_DIR`
Stylesheet is called `style.css` and goes in root `INPUT_DIR`   

#### Start up Django application  
```python manage.py runserver```  
  
#### Open blog generation page in browser 
```http://127.0.0.1:8000/blog/```  

#### Under **Generate blog**, click "hold my beer"  
![Blog generator page](blog/screenshots/blog_generation_screenshot.png "Blog generator page")  

### Output files will end up in the following places  
- `OUTPUT_DIR`: `index.html` and `style.css` 
- `OUTPUT_PAGES_DIR`: story pages   
- `OUTPUT_IMAGES_DIR`: images   
