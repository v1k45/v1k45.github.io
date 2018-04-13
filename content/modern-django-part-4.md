Title: Modern Django: Part 4: Adding authentication to React SPA using DRF
Date: 2018-04-13 21:00
Category: Web Development
Tags: python, django, javascript, js, react, django-rest-framework, django-rest-knox

In [last post]({filename}/modern-django-part-3.md) we managed to create/read/update/delete notes directly into the database using API created by Django Rest Framework with React Frontend. In this one will we allow users to maintain separate notes and protect them using authentication.

The code for this repository is hosted on my github, [v1k45/ponynote](https://github.com/v1k45/ponynote). You can checkout `part-4` branch to see all the changes done till the end of this part.

### Associating notes with users

In order to allow users have separate notes, we'll need to associate notes with users. We'll start by adding an `owner` field to the `Note` model. Update `notes/models.py`:

```python
from django.db import models
from django.contrib.auth.models import User


class Note(models.Model):
    text = models.CharField(max_length=255)
    owner = models.ForeignKey(User, related_name="notes",
                              on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

Make migrations and migrate the changes to database.

```
(ponynote)  $ ./manage.py makemigrations
Migrations for 'notes':
  notes/migrations/0002_note_owner.py
    - Add field owner to note
(ponynote)  $ ./manage.py migrate
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, notes, sessions
Running migrations:
  Applying notes.0002_note_owner... OK
```

### Creating Auth APIs

We need to create APIs for basic authentication actions like registration, user endpoint, login and logout.

Django Rest Framework allows various kinds of authentication techniques including BasicAuth, SessionAuth, TokenAuth. For single page applications, Token Authentication and their variations like JSON Web Tokens (JWT) are quite common choices.


#### Installing and setting up `knox`

DRF ships with a built-in TokenAuthentication feature but it is not ideal for user facing SPAs because of it lacks basic features. Instead, we will use `django-rest-knox`, It is similar to DRF's TokenAuth but much better and robust.

Start by installing it:

```
(ponynote)  $ pip install django-rest-knox
```

Update `ponynote/settings.py` by adding `knox` and `rest_framework` to  INSTALLED_APPS and setting knox's TokenAuthentication class as default in DRF.

```python
INSTALLED_APPS = [
    'rest_framework',
    'knox',
]

# Rest framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('knox.auth.TokenAuthentication',),
}
```

Add `knox` routes to `ponynote/urls.py`:

```python
urlpatterns = [
    url(r'^api/', include(endpoints)),
    url(r'^api/auth/', include('knox.urls')),
    url(r'^', TemplateView.as_view(template_name="index.html")),
]
```

Finally, migrate the database:

```
(ponynote)  $ ./manage.py migrate
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, knox, notes, sessions
Running migrations:
  Applying knox.0001_initial... OK
  Applying knox.0002_auto_20150916_1425... OK
  Applying knox.0003_auto_20150916_1526... OK
  Applying knox.0004_authtoken_expires... OK
  Applying knox.0005_authtoken_token_key... OK
  Applying knox.0006_auto_20160818_0932... OK
```

#### Creating a Registration API

To allow users to create accounts, we will create an API for registration. Ideally you'd use feature-rich third party applications like `allauth`, `rest-auth`, `djoser` etc to handle all kinds of authentication related needs. But since our application is simple, we are better off our own views/endpoints.

Start by creating `CreateUserSerializer` and `UserSerializer` in `notes/serializers.py`:

```python
from rest_framework import serializers
from django.contrib.auth.models import User

class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['username'],
                                        None,
                                        validated_data['password'])
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')
```

We'll use `CreateUserSerializer` for validating input for registration. We aren't using `email`, users will login with username and password. `UserSerializer` will be used to return the output after user has successfully registered.

Next, create the registration API, In `notes/api.py`:

```python
from rest_framework import viewsets, permissions, generics
from rest_framework.response import Response

from knox.models import AuthToken

from .models import Note
from .serializers import NoteSerializer, CreateUserSerializer, UserSerializer


class RegistrationAPI(generics.GenericAPIView):
    serializer_class = CreateUserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": AuthToken.objects.create(user)
        })
```

The API is pretty staight-forward, we validate the user input and create an account if the validation passes. In the response, we return the user object in serialized format and an authentication token which will be used by the application to perform user-specific api calls.


Update the API endpoints to include registration API, In `notes/endpoints.py`:

```python
from .api import NoteViewSet, RegistrationAPI

urlpatterns = [
    url("^", include(router.urls)),
    url("^auth/register/$", RegistrationAPI.as_view()),
]
```

After the endpoint is added, you can test the endpoint using curl:

```
$ curl --request POST \
--url http://localhost:8000/api/auth/register/ \
--header 'content-type: application/json' \
--data '{
  "username": "user1",
  "password": "hunter2"
}'
```

This will create the user with username `user1` and password `hunter2`. You'll get the following response from API:

```
{"user":{"id":1,"username":"user1"},"token":"<TOKEN HERE>"}
```

It handles valiadtion cases for fields, including uniquness of username. If you try to send the same data twice, you'll see that the API throws an error that the username needs to be unique.


#### Creating login API

Now that users can create account, we need a way for our users to log into the application and retrieve the authentication token for user-related actions.

First create a `LoginUserSerializer` in `notes/serializers.py`:

```python
from django.contrib.auth import authenticate


class LoginUserSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Unable to log in with provided credentials.")
```

The `validate` method of this serializer checks if the username and password are correct combination using django's `authenticate` function. It also makes sure the user is active.

Then create a `LoginAPI` in `notes/api.py`:

```python
from .serializers import (NoteSerializer, CreateUserSerializer,
                          UserSerializer, LoginUserSerializer)


class LoginAPI(generics.GenericAPIView):
    serializer_class = LoginUserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": AuthToken.objects.create(user)
        })
```

After this, add the API to API endpoints in `notes/endpoints.py`:

```python
from .api import NoteViewSet, RegistrationAPI, LoginAPI

urlpatterns = [
    url("^", include(router.urls)),
    url("^auth/register/$", RegistrationAPI.as_view()),
    url("^auth/login/$", LoginAPI.as_view()),
]
```

That will register our login API to endpoints. We can test it using curl:

```
$ curl --request POST \
  --url http://localhost:8000/api/auth/login/ \
  --header 'content-type: application/json' \
  --data '{
	"username": "user1",
	"password": "hunter2"
}'
```

#### User data endpoint

Now that the login and registration API are working, we need an API to return user data of the logged in user. We will use this API to determine if the user is logged in and retrieve their token for performing user specific api calls.

Since we already have a `UserSerializer`, we can create `UserAPI` right-away and add it to endpoints.

Add the following in `notes/api.py`

```python
class UserAPI(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, ]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
```

The above API will return user data for the authenticated user or 4XX range errors if user is not authenticated or token is incorrect.

Add the API to `notes/endpoints.py`:

```python
from .api import NoteViewSet, RegistrationAPI, LoginAPI, UserAPI

urlpatterns = [
    url("^", include(router.urls)),
    url("^auth/register/$", RegistrationAPI.as_view()),
    url("^auth/login/$", LoginAPI.as_view()),
    url("^auth/user/$", UserAPI.as_view()),
]
```

You can test the API using the auth token you retrieved from the `LoginAPI`:

```
$ curl --request GET \
  --url http://localhost:8000/api/auth/user/ \
  --header 'authorization: Token YOUR_API_TOKEN_HERE' \
  --header 'content-type: application/json' \
```

The above request will return the user object of the authenticated user.


### Restricting NotesAPI to authenticated users

Now that all authentication related APIs are working, we can update `NoteViewSet` and `NoteSerializer` to restict access to authenticated users only.

Start by updating `NoteViewSet` in `notes/api.py`:

```python
class NoteViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, ]
    serializer_class = NoteSerializer

    def get_queryset(self):
        return self.request.user.notes.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
```

We did the following changes here:

- Changed the API access from `AllowAny` to `IsAuthenticated`. This will require users to login/send authentication token in order to use this API.

- Override `perform_create` method to save owner of the note while creating it.

- Replace `queryset` attribute with `get_queryset` method and return the notes which the authenticated user owns.

After this, update the notes router registration to add a `base_name`. It is required if the viewset does not have a `queryset` attribute:

```
router.register('notes', NoteViewSet, 'notes')
```

This will make sure the notes api is only accessible to authenticated users and the users get to see and modify their own notes only.

### Bringing Authentication to React app

Authentication flow in the react application will be pretty simple, we'll redirect user to the login page if they are not logged in and then redirect back to the notes page after login is successful.

![react app authentication flow]({filename}/images/modern-django-4-auth-flow.png)


#### Login page

Let's start by creating a non-functional login page to which we will redirect un-authenticated users:

Create `frontend/src/components/Login.jsx`:


```jsx
import React, {Component} from "react";
import {connect} from "react-redux";

import {Link} from "react-router-dom";


class Login extends Component {

  state = {
    username: "",
    password: "",
  }

  onSubmit = e => {
    e.preventDefault();
    console.error("Not implemented!!1");
  }

  render() {
    return (
      <form onSubmit={this.onSubmit}>
        <fieldset>
          <legend>Login</legend>
          <p>
            <label htmlFor="username">Username</label>
            <input
              type="text" id="username"
              onChange={e => this.setState({username: e.target.value})} />
          </p>
          <p>
            <label htmlFor="password">Password</label>
            <input
              type="password" id="password"
              onChange={e => this.setState({password: e.target.value})} />
          </p>
          <p>
            <button type="submit">Login</button>
          </p>

          <p>
            Don't have an account? <Link to="/register">Register</Link>
          </p>
        </fieldset>
      </form>
    )
  }
}

const mapStateToProps = state => {
  return {};
}

const mapDispatchToProps = dispatch => {
  return {};
}

export default connect(mapStateToProps, mapDispatchToProps)(Login);
```

Then add login route to `App.js`:

```
import Login from "./components/Login";

class App extends Component {
  render() {
    return (
      <Provider store={store}>
        <BrowserRouter>
          <Switch>
            <Route exact path="/" component={PonyNote} />
            <Route exact path="/login" component={Login} />
            <Route component={NotFound} />
          </Switch>
        </BrowserRouter>
      </Provider>
    );
  }
}

export default App;
```

Then go to [localhost:8000/login](http://localhost:8000/login), you'll see the login page:

![login page]({filename}/images/modern-django-4-login-page.png)


#### Auth actions and reducers

To make the non-functional login page functional and restrict access on the notes page to only authenticated users, we'll need to add some actions and an authentication reducer.

##### Authentication reducer

Start by creating an `auth.js` file in `frontend/src/reducers/` and add reducer code:

```js
const initialState = {
  token: localStorage.getItem("token"),
  isAuthenticated: null,
  isLoading: true,
  user: null,
  errors: {},
};


export default function auth(state=initialState, action) {

  switch (action.type) {

    case 'USER_LOADING':
      return {...state, isLoading: true};

    case 'USER_LOADED':
      return {...state, isAuthenticated: true, isLoading: false, user: action.user};

    case 'LOGIN_SUCCESSFUL':
	  localStorage.setItem("token", action.data.token);
      return {...state, ...action.data, isAuthenticated: true, isLoading: false, errors: null};

    case 'AUTHENTICATION_ERROR':
    case 'LOGIN_FAILED':
    case 'LOGOUT_SUCCESSFUL':
	  localStorage.removeItem("token");
      return {...state, errors: action.data, token: null, user: null,
        isAuthenticated: false, isLoading: false};

    default:
      return state;
  }
}
```

Noticed the token value is being retrieved from `localStorage`? We'll store the authentication token in localStorage and then load it into the `auth` reducer on initial load. This will help us retain the user authentication state even if the user closes the browser window.

We are handling user loading and login actions. If a login is successful, the reducer will update the localStorage and redux token. If login fails, user logs out or the application throws authentication related errors, the reducer will remove the auth token, store errors and set the login state accordingly.

Add this reducer to `reducers/index.js`:

```js
import auth from "./auth";

const ponyApp = combineReducers({
  notes, auth,
})
```

##### Authentication actions

Create `frontend/src/actions/auth.js` and add `loadUser` action to it:

```js
export const loadUser = () => {
  return (dispatch, getState) => {
    dispatch({type: "USER_LOADING"});

    const token = getState().auth.token;

    let headers = {
      "Content-Type": "application/json",
    };

    if (token) {
      headers["Authorization"] = `Token ${token}`;
    }
    return fetch("/api/auth/user/", {headers, })
      .then(res => {
        if (res.status < 500) {
          return res.json().then(data => {
            return {status: res.status, data};
          })
        } else {
          console.log("Server Error!");
          throw res;
        }
      })
      .then(res => {
        if (res.status === 200) {
          dispatch({type: 'USER_LOADED', user: res.data });
          return res.data;
        } else if (res.status >= 400 && res.status < 500) {
          dispatch({type: "AUTHENTICATION_ERROR", data: res.data});
          throw res.data;
        }
      })
  }
}

```

In the above action, we are sending an `Authorization` header with the token stored in redux store. If this token exists and is correct, the API will return the user object, otherwise, we'll dispatch `AUTHENTICATION_ERROR` action.

Update `frontend/src/actions/index.js` to include `auth.js`:

```js
import * as notes from "./notes";
import * as auth from "./auth";

export {notes, auth}
```

#### Restricting anauthorized access

In order to stop unauthenticated users from accessing "private" routes we must redirect them to the login page.

To achieve this, we will create a `PrivateRoute` method which only renders the target component if the user is authenticated.

Update `frontend/src/App.js` file:

```jsx
import React, { Component } from 'react';
import {Route, Switch, BrowserRouter, Redirect} from 'react-router-dom';

import { Provider, connect } from "react-redux";
import { createStore, applyMiddleware } from "redux";
import thunk from "redux-thunk";

import {auth} from "./actions";
import ponyApp from "./reducers";

import PonyNote from "./components/PonyNote";
import NotFound from "./components/NotFound";
import Login from "./components/Login";

let store = createStore(ponyApp, applyMiddleware(thunk));

class RootContainerComponent extends Component {

  componentDidMount() {
    this.props.loadUser();
  }

  PrivateRoute = ({component: ChildComponent, ...rest}) => {
    return <Route {...rest} render={props => {
      if (this.props.auth.isLoading) {
        return <em>Loading...</em>;
      } else if (!this.props.auth.isAuthenticated) {
        return <Redirect to="/login" />;
      } else {
        return <ChildComponent {...props} />
      }
    }} />
  }

  render() {
    let {PrivateRoute} = this;
    return (
      <BrowserRouter>
        <Switch>
          <PrivateRoute exact path="/" component={PonyNote} />
          <Route exact path="/login" component={Login} />
          <Route component={NotFound} />
        </Switch>
      </BrowserRouter>
    );
  }
}

const mapStateToProps = state => {
  return {
    auth: state.auth,
  }
}

const mapDispatchToProps = dispatch => {
  return {
    loadUser: () => {
      return dispatch(auth.loadUser());
    }
  }
}

let RootContainer = connect(mapStateToProps, mapDispatchToProps)(RootContainerComponent);

export default class App extends Component {
  render() {
    return (
      <Provider store={store}>
        <RootContainer />
      </Provider>
    )
  }
}
```

In the above code, we moved the contents under `Provider` to a separate component named `RootContainerComponent`.

The `RootContainerComponent`, as it's name suggests, is the root container of the application and is connected to redux store. It has a `PrivateRoute` method which changes the component to be rendered when a route matches depending on the authentication state of the application. If the user is not logged in, it redirects the page to `/login`.

The `RootContainer` is then used inside `App` component and is placed inside `Provider` component.

After this, if you go the notes page ([localhost:8000](http://localhost:8000/)), you'll be redirected to the login page.

#### Making login page work

While this protects unauthorized access of the notes page, we still don't have the login feature implemented to allow authenticated users to access the page.

To make it work, create a `login` function in `frontend/src/actions/auth.js`:

```js
export const login = (username, password) => {
  return (dispatch, getState) => {
    let headers = {"Content-Type": "application/json"};
    let body = JSON.stringify({username, password});

    return fetch("/api/auth/login/", {headers, body, method: "POST"})
      .then(res => {
        if (res.status < 500) {
          return res.json().then(data => {
            return {status: res.status, data};
          })
        } else {
          console.log("Server Error!");
          throw res;
        }
      })
      .then(res => {
        if (res.status === 200) {
          dispatch({type: 'LOGIN_SUCCESSFUL', data: res.data });
          return res.data;
        } else if (res.status === 403 || res.status === 401) {
          dispatch({type: "AUTHENTICATION_ERROR", data: res.data});
          throw res.data;
        } else {
          dispatch({type: "LOGIN_FAILED", data: res.data});
          throw res.data;
        }
      })
  }
}
```

After this edit `frontend/src/components/Login.jsx` to make use of the action we created:

```jsx
import {Link, Redirect} from "react-router-dom";

import {auth} from "../actions";

class Login extends Component {

  onSubmit = e => {
    e.preventDefault();
    this.props.login(this.state.username, this.state.password);
  }

  render() {
    if (this.props.isAuthenticated) {
      return <Redirect to="/" />
    }
    return (
      <form onSubmit={this.onSubmit}>
        <fieldset>
          <legend>Login</legend>
          {this.props.errors.length > 0 && (
            <ul>
              {this.props.errors.map(error => (
                <li key={error.field}>{error.message}</li>
              ))}
            </ul>
          )}
          {/*KEEP THE OTHER ELEMENTS*/}
        </fieldset>
      </form>
    )
  }
}

const mapStateToProps = state => {
  let errors = [];
  if (state.auth.errors) {
    errors = Object.keys(state.auth.errors).map(field => {
      return {field, message: state.auth.errors[field]};
    });
  }
  return {
    errors,
    isAuthenticated: state.auth.isAuthenticated
  };
}

const mapDispatchToProps = dispatch => {
  return {
    login: (username, password) => {
      return dispatch(auth.login(username, password));
    }
  };
}

export default connect(mapStateToProps, mapDispatchToProps)(Login);
```

After this you should be able to login from the login page and taken to the notes page if the credentials are correct.

### Registration page

Until now we used the registraton API directly to create users. Since we have all actions and reducers in place, we can create a registration page too.


Start by creating `frontend/src/components/Register.jsx` and add the following code:

```jsx
import React, {Component} from "react";
import {connect} from "react-redux";

import {Link, Redirect} from "react-router-dom";

import {auth} from "../actions";

class Login extends Component {

  state = {
    username: "",
    password: "",
  }

  onSubmit = e => {
    e.preventDefault();
    this.props.register(this.state.username, this.state.password);
  }

  render() {
    if (this.props.isAuthenticated) {
      return <Redirect to="/" />
    }
    return (
      <form onSubmit={this.onSubmit}>
        <fieldset>
          <legend>Register</legend>
          {this.props.errors.length > 0 && (
            <ul>
              {this.props.errors.map(error => (
                <li key={error.field}>{error.message}</li>
              ))}
            </ul>
          )}
          <p>
            <label htmlFor="username">Username</label>
            <input
              type="text" id="username"
              onChange={e => this.setState({username: e.target.value})} />
          </p>
          <p>
            <label htmlFor="password">Password</label>
            <input
              type="password" id="password"
              onChange={e => this.setState({password: e.target.value})} />
          </p>
          <p>
            <button type="submit">Register</button>
          </p>

          <p>
            Already have an account? <Link to="/login">Login</Link>
          </p>
        </fieldset>
      </form>
    )
  }
}

const mapStateToProps = state => {
  let errors = [];
  if (state.auth.errors) {
    errors = Object.keys(state.auth.errors).map(field => {
      return {field, message: state.auth.errors[field]};
    });
  }
  return {
    errors,
    isAuthenticated: state.auth.isAuthenticated
  };
}

const mapDispatchToProps = dispatch => {
  return {
    register: (username, password) => dispatch(auth.register(username, password)),
  };
}

export default connect(mapStateToProps, mapDispatchToProps)(Login);
```

As you can see, the component is pretty similar to `Login.jsx` only noteable difference being the `register` function/action instead of `login` and some other text.


Add a `register` action to `frontend/src/actions/auth.js`:

```js
export const register = (username, password) => {
  return (dispatch, getState) => {
    let headers = {"Content-Type": "application/json"};
    let body = JSON.stringify({username, password});

    return fetch("/api/auth/register/", {headers, body, method: "POST"})
      .then(res => {
        if (res.status < 500) {
          return res.json().then(data => {
            return {status: res.status, data};
          })
        } else {
          console.log("Server Error!");
          throw res;
        }
      })
      .then(res => {
        if (res.status === 200) {
          dispatch({type: 'REGISTRATION_SUCCESSFUL', data: res.data });
          return res.data;
        } else if (res.status === 403 || res.status === 401) {
          dispatch({type: "AUTHENTICATION_ERROR", data: res.data});
          throw res.data;
        } else {
          dispatch({type: "REGISTRATION_FAILED", data: res.data});
          throw res.data;
        }
      })
  }
}

```

Update auth reducers to handle registration related actions, Update `frontend/src/reducers/auth.js`:

```js
case 'LOGIN_SUCCESSFUL':
case 'REGISTRATION_SUCCESSFUL':
	localStorage.setItem("token", action.data.token);
	return {...state, ...action.data, isAuthenticated: true, isLoading: false, errors: null};

case 'AUTHENTICATION_ERROR':
case 'LOGIN_FAILED':
case 'REGISTRATION_FAILED':
case 'LOGOUT_SUCCESSFUL':
	localStorage.removeItem("token");
	return {...state, errors: action.data, token: null, user: null,
		isAuthenticated: false, isLoading: false};
```

Update the cases to include `REGISTRATION_SUCCESSFUL` and `REGISTRATION_FAILED` action types.

Add the `Register` component in react router route list in `App.js` inside `RootContainerComponent`:

```jsx
import Register from "./components/Register";

class RootContainerComponent extends Component {

  render() {
    let {PrivateRoute} = this;
    return (
      <BrowserRouter>
        <Switch>
          <PrivateRoute exact path="/" component={PonyNote} />
          <Route exact path="/register" component={Register} />
          <Route exact path="/login" component={Login} />
          <Route component={NotFound} />
        </Switch>
      </BrowserRouter>
    );
  }
}

```

Now you'd be able to register by going to [localhost:8000/register](http://localhost:8000/register). You'll also see erros on the page if you try to register using an existing username.

### Using auth in notes actions

While the login page works and the notes page is displayed after login, the core functionality of the notes page is still non-functional. This is because the notes API now requires the user to be logged in to be able to use it.

Let's update notes actions to fix this issue:

Update `frontend/src/actions/notes.js`:

```js
export const fetchNotes = () => {
  return (dispatch, getState) => {
    let headers = {"Content-Type": "application/json"};
    let {token} = getState().auth;

    if (token) {
      headers["Authorization"] = `Token ${token}`;
    }

    return fetch("/api/notes/", {headers, })
      .then(res => {
        if (res.status < 500) {
          return res.json().then(data => {
            return {status: res.status, data};
          })
        } else {
          console.log("Server Error!");
          throw res;
        }
      })
      .then(res => {
        if (res.status === 200) {
          return dispatch({type: 'FETCH_NOTES', notes: res.data});
        } else if (res.status === 401 || res.status === 403) {
          dispatch({type: "AUTHENTICATION_ERROR", data: res.data});
          throw res.data;
        }
      })
  }
}

export const addNote = text => {
  return (dispatch, getState) => {
    let headers = {"Content-Type": "application/json"};
    let {token} = getState().auth;

    if (token) {
      headers["Authorization"] = `Token ${token}`;
    }

    let body = JSON.stringify({text, });
    return fetch("/api/notes/", {headers, method: "POST", body})
      .then(res => {
        if (res.status < 500) {
          return res.json().then(data => {
            return {status: res.status, data};
          })
        } else {
          console.log("Server Error!");
          throw res;
        }
      })
      .then(res => {
        if (res.status === 201) {
          return dispatch({type: 'ADD_NOTE', note: res.data});
        } else if (res.status === 401 || res.status === 403) {
          dispatch({type: "AUTHENTICATION_ERROR", data: res.data});
          throw res.data;
        }
      })
  }
}

export const updateNote = (index, text) => {
  return (dispatch, getState) => {

    let headers = {"Content-Type": "application/json"};
    let {token} = getState().auth;

    if (token) {
      headers["Authorization"] = `Token ${token}`;
    }

    let body = JSON.stringify({text, });
    let noteId = getState().notes[index].id;

    return fetch(`/api/notes/${noteId}/`, {headers, method: "PUT", body})
      .then(res => {
        if (res.status < 500) {
          return res.json().then(data => {
            return {status: res.status, data};
          })
        } else {
          console.log("Server Error!");
          throw res;
        }
      })
      .then(res => {
        if (res.status === 200) {
          return dispatch({type: 'UPDATE_NOTE', note: res.data, index});
        } else if (res.status === 401 || res.status === 403) {
          dispatch({type: "AUTHENTICATION_ERROR", data: res.data});
          throw res.data;
        }
      })
  }
}

export const deleteNote = index => {
  return (dispatch, getState) => {

    let headers = {"Content-Type": "application/json"};
    let {token} = getState().auth;

    if (token) {
      headers["Authorization"] = `Token ${token}`;
    }

    let noteId = getState().notes[index].id;

    return fetch(`/api/notes/${noteId}/`, {headers, method: "DELETE"})
      .then(res => {
        if (res.status === 204) {
          return {status: res.status, data: {}};
        } else if (res.status < 500) {
          return res.json().then(data => {
            return {status: res.status, data};
          })
        } else {
          console.log("Server Error!");
          throw res;
        }
      })
      .then(res => {
        if (res.status === 204) {
          return dispatch({type: 'DELETE_NOTE', index});
        } else if (res.status === 401 || res.status === 403) {
          dispatch({type: "AUTHENTICATION_ERROR", data: res.data});
          throw res.data;
        }
      })
  }
}
```

The above code makes sure that authorization token is sent with all note related API calls, relevant actions are dispatched depending upon the type of response we receive.

After this you should be able to manage notes as a user.

### Logout feature

Now that the application is functional, it is about time we added a basic yet essential feature. To add logout functionality, start by adding a `logout` action function in `frontend/src/actions/auth.js`:


```js
export const logout = () => {
  return (dispatch, getState) => {
    let headers = {"Content-Type": "application/json"};

    return fetch("/api/auth/logout/", {headers, body: "", method: "POST"})
      .then(res => {
        if (res.status === 204) {
          return {status: res.status, data: {}};
        } else if (res.status < 500) {
          return res.json().then(data => {
            return {status: res.status, data};
          })
        } else {
          console.log("Server Error!");
          throw res;
        }
      })
      .then(res => {
        if (res.status === 204) {
          dispatch({type: 'LOGOUT_SUCCESSFUL'});
          return res.data;
        } else if (res.status === 403 || res.status === 401) {
          dispatch({type: "AUTHENTICATION_ERROR", data: res.data});
          throw res.data;
        }
      })
  }
}
```

Now, let's use this action in `PonyNote` component to show a logout link. Update `frontend/src/components/PonyNote.jsx`:

```jsx
import {notes, auth} from "../actions";

class PonyNote extends Component {

  render() {
    return (
      <div>
        <h2>Welcome to PonyNote!</h2>
        <hr />
        <div style={{textAlign: "right"}}>
          {this.props.user.username} (<a onClick={this.props.logout}>logout</a>)
        </div>

        {*/KEEP OTHER ELEMENTS*/}

      </div>
    )
  }
}


const mapStateToProps = state => {
  return {
    notes: state.notes,
    user: state.auth.user,
  }
}

const mapDispatchToProps = dispatch => {
  return {
    fetchNotes: () => {
      dispatch(notes.fetchNotes());
    },
    addNote: (text) => {
      return dispatch(notes.addNote(text));
    },
    updateNote: (id, text) => {
      return dispatch(notes.updateNote(id, text));
    },
    deleteNote: (id) => {
      dispatch(notes.deleteNote(id));
    },
    logout: () => dispatch(auth.logout()),
  }
}
```

This will display the username of logged in user along with a logout link. Our application will look something like this at this point:

![final page]({filename}/images/modern-django-4-final.png)

### Summary

Now you'll be able to create, read, update and delete notes privately using user accounts. The notes pages will ebe protected by a login page and anyone would be able to register and start managing their notes.

I'm not sure what should I post for the next part. I am thinking of either server-side rendering (SSR) of the react application or deployment procedure of the application as a final post.

### Reference

- [Django Rest Framework](http://www.django-rest-framework.org/)
- [Django Rest Knox](https://github.com/James1345/django-rest-knox/)
