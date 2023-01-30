_story_title Twisty Little Passages: Comments on a Quick and Dirty Blog

_story_list_title Twisty little passages: Comments on a quick & dirty blog  

_date_posted Updated Jan. 29, 2023

_large_blockquote You are in a maze of twisty little passages

When I wanted to add comments (since removed) to this blog, which consists of static pages, I considered and rejected commenting systems that cost money and those that require users to have a GitHub account, as the content of my posts is as much about American history as it is about technical topics. I settled on <a href="https://staticman.net/">Staticman</a>, which is free, and has been used successfuly on other GitHub pages. Staticman is free, and it supports <a href="https://www.google.com/recaptcha/about/">reCaptcha</a>, spam filtering with <a href="https://akismet.com/">Akismet</a>, moderation, and email notifications from providers that all have a free tier. It's also open source. Comments can be left anonymously if that's what you want, and the data is stored in your GitHub repo, so you have complete control over it.   

This control over the comment data is what ultimately allowed me to get it working on my site, albeit in an extremely convoluted and kind of ridiculous way. I'm going to explain the process that I came up with.  

First, a little background on how this blog was built. There are tools for generating GitHub pages from markdown using static site generators like Jekyll, but I wanted to have complete control over the blog's appearance, for better or worse. My initial and totally non-scalable method was simply to write the html and use stylesheets as much as possible to make it easier to change the blog's apperance if I needed to. I quickly gave up on this idea after writing my first couple of stories and created a not actually so quick, but definitely dirty Django application to make use of Django's templating engine to generate pages from a very limited subset of Markdown. A lot of elements were repurposed to serve my specific needs.  

The significance of this method is that the build takes place locally on my machine, and I just push the generated pages, stylesheets, and images to my GitHub repo, unlike Jekyll, which runs a build on GitHub. This site is truly static.   

I found this Average Linux User page <a href="https://averagelinuxuser.com/staticman-comments/">Staticman: Add Comments to your Static Website for FREE</a> extremely helpful. I followed the various steps described: creating a bot account on GitHub to submit pull requests with a comment to the blog repo, setting up my own Staticman deployment on Heroku, and adding the main Staticman configuration file `staticman.yml` to my blog repo.   

After that I strayed from the path, because I was using Django locally instead of Jekyll on GitHub. I added the Staticman url to Django `settings.py` instead of `_config.yml`. The `comments.html` partial was included in the blog post template. Staticman comments are pushed to `"data/comments/{options.slug}"` in my repo, where `{options.slug}` is the slugified title of the given blog post page. Comment files can be either yml or json and are named using a combination of datetime and poster name by default.  

Existing comments would need to be loaded with JavaScript to be displayed. You can read a file from a url with Javascript if you know the url, but you can't list the contents of remote directories from the client side. How was I going to read the individual comment files if I didn't know their names? There had to be a way.  

I realized that if I had a file with a known url containing a list of comment filenames, I would know the urls of the individual comments and could read them that way. GitHub pages use a <a href="https://docs.github.com/en/actions">GitHub Action</a> to actually publish pages to github.io, and I knew that Actions could supposedly be used for all sorts of things, so I decided to try creating one that made lists of all the comment files in each blog post directory.  

I'd never used GitHub Actions before, so making my own was tricky. I tried doing it with JavaScript but got hung up on getting all the moving parts to move. However, one of the parts was a workflow which could be used on its own. In the end I made a GitHub workflow that used bash to traverse the comment directories, save the lising output to files, and commit the new files to my blog repo. I set up the workflow to be triggered every time a json file was pushed to the repo and used Javascript on the blog page to read the list of comment files for that page, if any, and then read each json comment file to load the comment.  

The workflow gets triggered every time a json file is pushed to my blog repo: 
``` yaml
name: File list action

on:
  # Workflow triggered on push or pull request events involving .json files
  # but only for the main branch
  push:
    branches: [ main ]
    paths:
      - '**.json'
  pull_request:
    branches: [ main ]
    paths:
      - '**.json'
```
The workflow uses bash to list all the json files in subdirectories under data/comments and save the output to text files:
``` yaml
jobs:
  # list-files job creates lists of certain files in certain subdirectories
  list-files:
    runs-on: ubuntu-latest
    name: Create lists of json files
    steps:
      # Check out repository under $GITHUB_WORKSPACE, so job can access it
      - name: Checkout
        uses: actions/checkout@v2

      # Commands to run using the runner's shell
      - name: Create file lists
        run: |
          cd data/comments
            for OUTPUT in $(ls)
            do
              if [[ -d $OUTPUT ]]
              then
                cd $OUTPUT
                ls *.json > "json_files.txt"
                ls -d $PWD/*.txt
                cd ..
              fi
            done
```
After the file listings are created, they get pushed to the main branch of the repo:
``` yaml
      - name: Git status
        run: git status
      - name: Git add
        run: git add .
      - name: Git commit
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "github-actions"
          git commit -m "Added testing.txt"
      - name: Push changes
        uses: ad-m/github-push-action@master
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          branch: 'main'
```

It's not pretty, the process of getting a new comment to display on the page is relatively slow, and my Javascript won't hold up to close scrutiny, but it seems to work. I show a Bootstrap toast with the message that the comment has been submitted for moderation to explain the delay. It's not true, of course. I chose not to go the moderation route because it sounded like too much hassle. Comments just get pushed to main. Hold my beer.  

In summary, the path that comments take is as follows: User writes a comment. If it gets past the spam filter, it gets posted to my Staticman instance on Heroku. From there, my GitHub comment bot pushes its json file to the main branch on my blog repo. The GitHub workflow is triggered by the push and creates a new list of comment files for that page. When the page gets loaded again later, the comment file will be read and the contents inserted into the page using Javascript.  

The main thing I'm not happy with, aside from my ugly Javascript and the delay in displaying new comments, is the fact that I could not for the life of me figure out how to prevent the redirect to the Akismet "spam detected" message when you post something about a certain medication. I appreciate a good json error message in a web application as much as the next person, but it looks sloppy.  

![Spam error](https://clairempr.github.io/images/akismet_spam_error.png width="775" 'Akismet spam error message')

So there you have it, unless I've forgotten a step already. Getting comments onto this quick and dirty blog page involved a journey along some really twisty little passages.  

Comments have been removed from the blog since I wrote this, because I decided that it wasn't worth the price of Heroku's new pricing.

_references References
- <a href="https://staticman.net/">Staticman</a>
- <a href="https://averagelinuxuser.com/staticman-comments/">Average Linux User: Staticman: Add Comments to your Static Website for FREE</a>
- "maze of twisty little passages" quote from <a href="https://en.wikipedia.org/wiki/Colossal_Cave_Adventure">Colossal Cave Adventure (also known as Adventure or ADVENT)</a> 
