Title: Modern Django: Part 3: Creating an API and integrating with React
Date: 2018-03-03 21:40
Category: Web Development
Tags: python, django, javascript, js, react, django-rest-framework, redux

In [last post]({filename}/modern-django-part-2.md) we developed a frontend of our note taking application which has ability to store notes on client-side using redux store. In this part we will create database models and APIs to create, read, update and delete notes in database using react frontend and redux store.

The code for this repository is hosted on my github, [v1k45/ponynote](https://github.com/v1k45/ponynote). You can checkout `part-3` branch to all the changes done till the end of this part.

### Creating DB Models

To store the notes in database, first we need to create models. We'll start by creating an app and then a Note model inside it.

In the project root, create an app using `startapp` command and add it to admin.

```
(ponynote)  $ ./manage.py startapp notes
```

Add `notes.apps.NotesConfig` to the `INSTALLED_APPS` list in `ponynote/settings.py`.

### Note Model

Open `notes/models.py` create the following model:

```python
from django.db import models


class Note(models.Model):
    text = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text
```

Since our application feature is limited, two fields in the model will do.

Migrate the database to add this table using the following command:

```
(ponynote)  $ ./manage.py makemigrations
Migrations for 'notes':
  notes/migrations/0001_initial.py
    - Create model Note

(ponynote)  $ ./manage.py migrate
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, notes, sessions
Running migrations:
  Applying notes.0001_initial... OK
```

### Building API using DRF

Now that the model is created, we can create an API to peform CRUD actions on the database. We'll do this using `django-rest-framework`.

Install `django-rest-framework` in the project virtual environment:

```
(ponynote)  $ pip install djangorestframework
```

Now create three python files, `api.py`, `serialiers.py` and `endpoints.py`.

```
$ touch notes/api.py notes/serializers.py notes/endpoints.py
```

Start by creating a serializer for our Notes model, create the following serializer inside `serializers.py`:


```python
from rest_framework import serializers

from .models import Note


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ('id', 'text', )
```

The above serializer is `ModelSerializer`, it has an API similar (somewhat) to the `ModelForm` class in django.

After creating serializer, create an API for `Note` model using `NoteSerialzer`:

```python
from rest_framework import viewsets, permissions

from .models import Note
from .serializers import NoteSerializer


class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all()
    permission_classes = [permissions.AllowAny, ]
    serializer_class = NoteSerializer
```

A viewset works like a generic model view in django views. Lets allow all types of requests to this endpoint for now.

Lets register this API ViewSet to the DRF router and add it to django urls. In the `notes/endpoints.py` write the following:

```python
from django.conf.urls import include, url
from rest_framework import routers

from .api import NoteViewSet

router = routers.DefaultRouter()
router.register('notes', NoteViewSet)

urlpatterns = [
    url("^", include(router.urls)),
]
```

In project urls.py `ponynote/urls.py`:

```python
from django.conf.urls import url, include
from django.views.generic import TemplateView

from notes import endpoints

urlpatterns = [
    url(r'^api/', include(endpoints)),
    url(r'^', TemplateView.as_view(template_name="index.html")),
]
```

After this, you'll be able to make requests on the notes API using `curl` or your favorite http client like Postman or Insomnia:

### API in action

- Create Note:

```
curl --request POST \
  --url http://localhost:8000/api/notes/ \
  --header 'content-type: application/json' \
  --data '{
	"text": "First Note!"
}'
```

- Get All Notes:

```
curl --request GET \
  --url http://localhost:8000/api/notes/ \
  --header 'content-type: application/json'
```

- Get a specific note using id:

```
curl --request GET \
  --url http://localhost:8000/api/notes/1/ \
  --header 'content-type: application/json'
```

- Delete a specific note using id:

```
curl --request DELETE \
  --url http://localhost:8000/api/notes/1/ \
  --header 'content-type: application/json'
```

### Integrating DRF API with Frontend

To be able to fetch and manipulate notes in the backend from frontend, we need to make use of few libraries. In order to fetch notes, we will use `whatwg-fetch` (already included with `create-react-app`) and `redux-thunk` for asynchronous action creation.

#### What is redux-thunk?

Redux Thunk middleware allows you to write action creators that return a function instead of an action. The thunk can be used to delay the dispatch of an action, or to dispatch only if a certain condition is met. The inner function receives the store methods dispatch and getState as parameters

#### Install and setup redux-thunk

```
$ npm install redux-thunk --save
```

Then in the `App.js` file, import `thunk` and `applyMiddleware` function, pass it to the `createStore` function and we are good to go.

```js
import { createStore, applyMiddleware } from "redux";
import thunk from "redux-thunk";

let store = createStore(ponyApp, applyMiddleware(thunk));
```

#### Async redux actions

Let us create our first async action using redux thunk. Write the follwoing function in `actions/notes.js`:

```js
export const fetchNotes = () => {
  return dispatch => {
    let headers = {"Content-Type": "application/json"};
    return fetch("/api/notes/", {headers, })
      .then(res => res.json())
      .then(notes => {
        return dispatch({
          type: 'FETCH_NOTES',
          notes
        })
      })
  }
}
```

The above code will perform an API call to the django application at `api/notes/` and dispatch the `FETCH_NOTES` action when response is received.

Now handle this action in the reducer `reducers/notes.js` by adding `FETCH_NOTES` case in the `switch` statement.:

```js
case 'FETCH_NOTES':
	return [...state, ...action.notes];
```

Since we going to use the server database for notes, lets set the `initialState` as an empty array by removing the dummy note.

```js
const initialState = [];
```

#### Using the async action in component

Using this action is no different than using a normal action. Just add it to `mapDispatchToProps`.

```js
const mapDispatchToProps = dispatch => {
  return {
    fetchNotes: () => {
      dispatch(notes.fetchNotes());
    },
  }
}
```

And call that action dispatcher when component mounts so that the notes are fetched from API and loaded to redux store. Add `componentDidMount` method to `PonyNote` class:

```js
componentDidMount() {
	this.props.fetchNotes();
}
```

On reloading, you should see the list of notes which you created using the API directly. If you haven't already, lets connect the `addNote` action to the `API` so that we start seeing notes directly from the database.

#### Add notes using API call

Lets update the `addNote` action in `actions/notes.js` file to send a `POST` request to notes api:

```js
export const addNote = text => {
  return dispatch => {
    let headers = {"Content-Type": "application/json"};
    let body = JSON.stringify({text, });
    return fetch("/api/notes/", {headers, method: "POST", body})
      .then(res => res.json())
      .then(note => {
        return dispatch({
          type: 'ADD_NOTE',
          note
        })
      })
  }
}
```

In the above action function, our applcation will send a POST request with a JSON data of the note text and then disptach the `ADD_NOTE` action which will isert the added note to redux store. In `reducers/notes.js`, update the `ADD_NOTE` case to add the whole note object instead of text.

```js
case 'ADD_NOTE':
	return [...state, action.note];
```

After this a slight modification in our `PonyNote.jsx` component so that we reset the form only after the note has been successfully created:

Add a `return` statement to the action dispatch call so that we can chain additional callbacks to the API call promise.

```js
addNote: (text) => {
	return dispatch(notes.addNote(text));
},
```

Update the `submitNote` method by moving `this.resetForm()` call from bottom to a callback for `addNote` function:

```js
this.props.addNote(this.state.text).then(this.resetForm)
```

Similarly you can `catch` any errors thrown by the promise and handle API error and show then on the UI. For sake of simplicity, we will not cover that.

#### Updating notes

Updating notes is very similar to `addNote` action which calls API. All we need to do is pass the `note.id` in endpoint url.

Update the `updateNote` action in `actions/notes.js`:

```js
export const updateNote = (index, text) => {
  return (dispatch, getState) => {

    let headers = {"Content-Type": "application/json"};
    let body = JSON.stringify({text, });
    let noteId = getState().notes[index].id;

    return fetch(`/api/notes/${noteId}/`, {headers, method: "PUT", body})
      .then(res => res.json())
      .then(note => {
        return dispatch({
          type: 'UPDATE_NOTE',
          note,
          index
        })
      })
  }
}
```

Note that the first argument of `updateNote` is `index` instead of `id`, this is done to easily get the note which is being updated. Also, we have a `getState` argument for ther return action function, it is used to get current state of the application. We used it to get the note.id using the index we had.

Another important thing is that the request method is `PUT`, which indicates that the resource on server should be updated. In the final action dispatch we have the index and newly saved note as the data, we will use it in the reducer.

Update `UPDATE_NOTE` case in `redcers/notes.js`:

```js
case 'UPDATE_NOTE':
	let noteToUpdate = noteList[action.index]
	noteToUpdate.text = action.note.text;
	noteList.splice(action.index, 1, noteToUpdate);
	return noteList;
```

In `PonyNote.jsx`, update `mapDispatchToProps` and `submitNote` method like we did for adding notes.

```js
updateNote: (id, text) => {
	return dispatch(notes.updateNote(id, text));
},
```

```js
this.props.updateNote(this.state.updateNoteId, this.state.text).then(this.resetForm);
```

Now you'll be able to update notes and save it in the database.

#### Deleting Notes

Update `actions/notes.js`'s `deleteNote` action to send `DELETE` request to the API server:

```js
export const deleteNote = index => {
  return (dispatch, getState) => {

    let headers = {"Content-Type": "application/json"};
    let noteId = getState().notes[index].id;

    return fetch(`/api/notes/${noteId}/`, {headers, method: "DELETE"})
      .then(res => {
        if (res.ok) {
          return dispatch({
            type: 'DELETE_NOTE',
            index
          })
        }
      })
  }
}
```

In the `DELETE_NOTE` reducer in `reducers/notes.js` make the following changes:

```js
case 'DELETE_NOTE':
	noteList.splice(action.index, 1);
	return noteList;
```

### Summary

Now you'll be able to create, read, update and delete notes using the API built using django-rest-framework. All the notes are stored in redux store in client side and changes will be reflected in the database and persist on reload.

In next part we'll add authentication to pony note so that multiple users can maintain their notes privately. We'll implement login/signup flow and assosiate notes with users.

### Reference

- [Django Rest Framework](http://www.django-rest-framework.org/)
- [redux-thunk](https://github.com/gaearon/redux-thunk)
- [How to dispatch a Redux action with a timeout?](https://stackoverflow.com/a/35415559/4726598)
- [Async Redux actions](https://redux.js.org/advanced/async-actions#async-action-creators)
