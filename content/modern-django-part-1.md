Title: Modern Django: Part 1: Setting up Django and React
Date: 2017-10-05 01:45
Modified: 2017-11-23 03:45
Category: Web Development
Tags: python, django, javascript, js, react


### Introduction

This will be a multi part tutorial series on how to create a "Modern" web application or SPA using Django and React.js.

We will create a Note taking Single Page Application which will be rendered by ReactJS with Django as an API backend. Let's call it "ponynote", because ponies are quite popular within django community.

We will be using multiple libraries in this project, mainly, `django-rest-framework` for creating APIs easily, `react-router-dom` for handling in-app routing, `redux` for maintaing global application state.

This part of the series is about setting up your project to serve django and react seamlessly.

The code for this repository is hosted on my github, [v1k45/ponynote](https://github.com/v1k45/ponynote). You can checkout `part-1` branch to all the changes done till the end of this part.

### Environment setup

I'll assume that you can setup your machine to run Python3 and Node >=6 on your own or using the tutorials available on the internet.

I highly recommened you to use python virualenv so that your project dependencies do not disturb system-wide python installation. I use [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/) to maintain multiple virtualenvs at single place using easy commands. I'll be using it throughout the tutorial.

### Setup Django

After you have created and activated your virtualenv. You can start by installing django.

```
(ponynote)  $ pip install django
```

After installing django, we will create a project called `ponynote` using `django-admin` tool.

```
(ponynote)  $ django-admin startproject ponynote
```

It will generate the following project:

```
(ponynote)  $ tree
.
└── ponynote
    ├── manage.py
    └── ponynote
        ├── __init__.py
        ├── settings.py
        ├── urls.py
        └── wsgi.py

2 directories, 5 files
```

After migrating and runing development server, you will be able to see the "It worked!" welcome page of Django on [http://127.0.0.1:8000](http://127.0.0.1:8000).

```
(ponynote)  $ cd ponynote
(ponynote)  $ ./manage.py migrate
(ponynote)  $ ./manage.py runserver
```

Now that we have got django working, it is time to set it up to work with React JS.

### Setup ReactJS with Webpack

If you haven't heard of Webpack before, it has now become the defacto tool to for _module bundling_, compiling all your dependencies to a small bundles (mostly one). You can learn more about webpack from their [official website](https://webpack.js.org/).

We won't be directly writing webpack configuration ourselves though, we will use `create-react-app` to generate the project boilerplate with all the configurations in it. Think of `create-react-app` as `django-admin startproject` command but much more powerful.

For this, first we will install `create-react-app` sytem-wide using npm. Because we are installing system-wide, we will need superuser permissions.


```
$ sudo npm install -g create-react-app
```

After installing we will create a react application using that command and then ejecting the config files so that we can edit them ourselves.

```
$ create-react-app frontend
$ cd frontend
$ npm run eject
```

It will create the following structure:

```
$ tree -I node_modules
.
├── config
│   ├── env.js
│   ├── jest
│   │   ├── cssTransform.js
│   │   └── fileTransform.js
│   ├── paths.js
│   ├── polyfills.js
│   ├── webpack.config.dev.js
│   ├── webpack.config.prod.js
│   └── webpackDevServer.config.js
├── package.json
├── public
│   ├── favicon.ico
│   ├── index.html
│   └── manifest.json
├── README.md
├── scripts
│   ├── build.js
│   ├── start.js
│   └── test.js
└── src
    ├── App.css
    ├── App.js
    ├── App.test.js
    ├── index.css
    ├── index.js
    ├── logo.svg
    └── registerServiceWorker.js

5 directories, 23 files

```

It is pretty obvious by the directory name that which file is store where.

You can test this application by running

```
$ npm run start
```

This will show a React welcome page.

![React welcome page]({filename}/images/modern-django-1-react-welcome.png)

The development server has hot loading enabled by default. This means any changes you do in you source files will be instantly reflected in the browser without you having to refresh the page manually again and again.


### Integrating React and Django

Now that we have a working django server and webpack dev server running react, we will now integrate both of them so that Django can show the SPA from it's own server. We will do that using `django-webpack-loader` a django application which injects link and script tag for the bundles which webpack generates dynamically.

We will start by installing `webpack_loader` in our django project first:


```
(ponynote)  $ pip install django-webpack-loader
```

Then in the project settings.py (`ponynote.settings`) add `webpack_loader` in `INSTALLED_APPS` list and add the following.

```python
WEBPACK_LOADER = {
    'DEFAULT': {
            'BUNDLE_DIR_NAME': 'bundles/',
            'STATS_FILE': os.path.join(BASE_DIR, 'webpack-stats.dev.json'),
        }
}
```

To serve the index page of the application we need to create a view and template in django. We'll start by creating an index template at `templates/index.html` in project root. We will also need to update project's template settings so it it can detect the tempalte directory.

In `ponynote.settings.py`'s TEMPLATES setting:

```python
TEMPLATES = [
    {
		# ... other settings
        'DIRS': [os.path.join(BASE_DIR, "templates"), ],
		# ... other settings
    },
]

```

Put the following content in your `templates/index.html`:

```html
{% load render_bundle from webpack_loader %}
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width" />
    <title>Ponynote</title>
  </head>
  <body>
    <div id="root">
    </div>
      {% render_bundle 'main' %}
  </body>
</html>
```

The HTML division with `root` id is the mounting point of our react application. The `render_bundle` tag with `main` as argument renders script tag for bundle named `main` which is produced by out webpack config.

Now that the template is ready, let's create a view to serve it. Since this will be a plain template, we can use django's `TemplateView` directly in our url config. In your project `ponynote.urls.py` file:


```python
from django.conf.urls import url
from django.contrib import admin
from django.views.generic import TemplateView

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', TemplateView.as_view(template_name="index.html")),
]
```

If you refresh your django homepage, you should see an error page with text `Are you sure webpack has generated the file and the path is correct?`. This means `webpack_loader` was searching for a file we specified in settings and was unable to find it.

![Django webpack error]({filename}/images/modern-django-1-webpack-error.png)

In order to generate this file, we need to install `webpack-bundle-tracker` plugin and configure webpack to generate required files. In `frontend` directory, run the following commands:

```
$ npm install webpack-bundle-tracker --save-dev
```

In your `frontend/config/paths.js` add the following key and value in the `module.exports` object.

```javascript
module.exports = {
  // ... other values
  statsRoot: resolveApp('../'),
}
```

In `frontend/config/webpack.config.dev.js` change `publicPath` and `publicUrl` to `http://localhost:3000/`.

```javascript
const publicPath = 'http://localhost:3000/';
const publicUrl = 'http://localhost:3000/';
```

In the same file, import `webpack-bundle-tracker` and include `BundleTracker` in webpack plugins and replace `webpackHotDevClient` line with the other two modules.

```javascript
const BundleTracker = require('webpack-bundle-tracker');

module.exports = {
  entry: [
	// ... KEEP OTHER VALUES
	// this will be found near line 30 of the file
    require.resolve('webpack-dev-server/client') + '?http://localhost:3000',
    require.resolve('webpack/hot/dev-server'),
    // require.resolve('react-dev-utils/webpackHotDevClient'),
  ],
  plugins: [
	// this will be found near line 215-220 of the file.
	// ... other plugins
    new BundleTracker({path: paths.statsRoot, filename: 'webpack-stats.dev.json'}),
  ],
}
```

The reason of replacing `webpackHotDevClient`, `publicPath` and `publicUrl` is that we are going to serve webpack dev server's bundle on a django page, and we don't want webpack hot loader to send requests to wrong url/host.


Now in `frontend/config/webpackDevServer.config.js` we need to allow the server to accept requests from external origins. [http://localhost:8000](http://localhost:8000) (Django server) will send XHR requests to [http://localhost:3000](http://localhost:3000) webpack server to check for source file changes.

Put `headers` object in the object returned by the exported function. This object is to be placed at the same level of `https` and `host` properties.

```
headers: {
  'Access-Control-Allow-Origin': '*'
},
```

That's it. Stop the webpack server and run it again and go to [http://localhost:8000/](http://localhost:8000/), you should see the same react welocme page as you did on webpack server page.


Now, any changes you do in `src/App.js` file will be instantly reflected on the opened page in browser using hot loading.

```jsx
import React, { Component } from 'react';
import logo from './logo.svg';
import './App.css';

class App extends Component {
  render() {
    return (
      <div className="App">
        <header className="App-header">
          <img src={logo} className="App-logo" alt="logo" />
          <h1 className="App-title">Welcome to Ponynote</h1>
        </header>
        <p className="App-intro">
            A react app with django as a backend.
        </p>
      </div>
    );
  }
}

export default App;
```

This will render the following page:

![Django and React welcome page]({filename}/images/modern-django-1-django-welcome.png)


### Production Setup

Since this is a multi-part tutorial series, it might take some time until we reach part 4/5 where I intend to talk about deployment. I'm writing the webpack deployment guide here for people who don't want to wait until part 4 or they know react and they just need a deployable django + webpack setup.

The production setup is pretty similar to changes we did for development setup. We will edit some config values in the `webpack.config` file.

Start with creating a `ponynote/production_settings.py` file at the same level of your project `settings.py`. For this project, the production server will use this settings file:

```
from .settings import *

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "assets"),
]

WEBPACK_LOADER = {
    'DEFAULT': {
            'BUNDLE_DIR_NAME': 'bundles/',
            'STATS_FILE': os.path.join(BASE_DIR, 'webpack-stats.prod.json'),
        }
}
```

The above config tells django to look for static files in `assets` directory of project root and use `webpack-stats.prod.json` as webpack stats file.

After this, create a directory `assets/bundles/` in your project root. This directory will store all our static assets. The bundles sub-directory will be used as build target. Webpack will save all the build file to `assets/bundles`.

```
$ mkdir -p assets/bundles
```

After this the change webpack's build output dir to `assets/bundles`. In `frontend/config/paths.js` change the `appBuild` value:

```js
// config after eject: we're in ./config/
module.exports = {
  // .. KEEP OTHER VALUES
  appBuild: resolveApp('../assets/bundles/'),
};
```

Now in `frontend/config/webpack.config.prod.js` do the following changes:

```js
const BundleTracker = require('webpack-bundle-tracker');

const publicPath = "/static/bundles/";

const cssFilename = 'css/[name].[contenthash:8].css';

module.exports = {
  // KEEP OTHER VALUES
  output: {
	// NEAR LINE 67

    // Generated JS file names (with nested folders).
    // There will be one main bundle, and one file per asynchronous chunk.
    // We don't currently advertise code splitting but Webpack supports it.
    filename: 'js/[name].[chunkhash:8].js',
    chunkFilename: 'js/[name].[chunkhash:8].chunk.js',
  },
  module: {
	// .. KEEP OTHER VALUES, ONLY UPDATE THE FOLLOWING VALUES
    rules: [
      {
        oneOf: [
		  // LINE 140
          {
            options: {
              limit: 10000,
              name: 'media/[name].[hash:8].[ext]',
            },
          },
          {
			// LINE 220
            options: {
              name: 'media/[name].[hash:8].[ext]',
            },
          },
        ],
      },
    ],
  },
  plugins: [
	// KEEP OTHER VALUES
	// LINE 320
    new BundleTracker({path: paths.statsRoot, filename: 'webpack-stats.prod.json'}),
  ],
}
```

Here we configured webpack to set `static/bundles/` as `publicPath` because the build files will be stored in `assets/bundles` and `/static/` url points to the `assets` directory. We also remove `static` prefixes from filenames and path to prevent unnecessary nesting of build files. This will make webpack to build all files directory into `assets/bundles` without creating an additional `static` directory inside it.

After saving the file, we can build the javascript files using the following command:

```
$ npm run build
```

This will create bunch of files in `assets/bundles` and a `webpack-stats.prod.json` file in the project root.

To check if everything was setup properly, we can run django server using production settings with webpack server stopped.

```
$ python manage.py runserver --settings=ponynote.production_settings
```

If you check [http://localhost:8000/](http://localhost:8000/), you'll see the same page which was rendered when webpack server was running. If you check the source code of the webpage, you'll see the js files are now being served directly through django and not webpack.

#### Important points

- It is better to build your js files on your CI server or your deployment server instead on including in version control or source code.

- Make sure you run `collectstatic` after you `build` the js files, otherwise your webserver won't be able to find the build files.

- Make sure your build generates a `webpack-stats.prod.json` file. If you are deploy by building the files manually, make sure you also include it when you're copying files from your machine to server.


All the directory and file names specified above are not enforced in any senese. Feel free to change the directory location or file names to your liking. But make sure all config files are properly updated.

#############

That's all on how to setup react and django to work together. In [next post]({filename}/modern-django-part-2.md) we'll setup in-application routing using `react-router-dom` and global state management using `redux`.


### References

- [Using Webpack transparently with Django](http://owaislone.org/blog/webpack-plus-reactjs-and-django/)
- [django-webpack-loader](https://github.com/ezhome/django-webpack-loader)
- [create-react-app](https://github.com/facebookincubator/create-react-app)
- [Create React App and Django](https://www.fusionbox.com/blog/detail/create-react-app-and-django/624/)
