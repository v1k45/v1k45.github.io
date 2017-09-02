Title: Hello, world!
Date: 2017-09-02 18:45
Category: Misc
Tags: hello, world

Like everyone else, I am also posting a _Hello, world!_ post as the first post on my blog.

This post is intended to be a test post to see if I was able to set up a static site.


This site uses [Pelican](https://getpelican.com/) to generate HTML from [Markdown](https://daringfireball.net/projects/markdown/syntax).

It uses a custom made theme which I made (not really, I didn't write a single line of CSS) using [oxalorg](https://oxal.org/)'s [Sakura](https://github.com/oxalorg/sakura). It uses dark version of sakura as base stylesheet and Pygments with Monokai style for syntax highlighting.

Let's see if we can write **bold** and _italics_ text with it. It is also renders images responsively.

![REEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE]({filename}/images/reeeeeeeeeeeeeeeeeeeeeeeeeeeee.jpg)


Sample python code as syntax highlight test

	:::python

	from django.shortcuts import render

	# show hello world page
	def hello_world(request):
		return render(request, 'hello_world.html')

That's all I can think of now :)
