Title: Modern Django: Part 2: Redux and React Router setup
Date: 2018-03-02 13:30
Modified: 2018-03-03 21:40
Category: Web Development
Tags: javascript, js, react, redux, react-router

This is the second part of the tutorial series on how to create a "Modern" web application or SPA using Django and React.js

In this part, we'll setup redux and react router in our note taking application. And later connect this frontend to an API backend.

The code for this repository is hosted on my github, [v1k45/ponynote](https://github.com/v1k45/ponynote). You can checkout `part-2` branch to see all the changes done till the end of this part.

### What is react router?

[React-router-dom](https://reacttraining.com/react-router/web) is a library which is used for in-application routing in react applications. Using it you can mount components on urls of your choice.

We'll first create a router for our application with relevant routes. Since this is a basic note-taking application, just one component/route should suffice but we'll still create a few other components and routes for demonstration.

#### Setup react-router-dom

Start by installing react-router-dom:

```
$ cd ponynote/frontend
$ npm install --save react-router-dom
```

After this let us create a few components which we will be using in the application. To maintain a clean directory structure we'll create all components inside a components directory. We will create a `PonyNote` component for our main app and `NotFound` component for 404 pages.

```
$ cd src/
$ mkdir components/
$ touch components/index.js
$ touch components/PonyNote.jsx
$ touch components/NotFound.jsx
```

Now that we have all our files created, update the `App.js` file to use `react-router-dom`:

```jsx
import React, { Component } from 'react';
import {Route, Switch, BrowserRouter} from 'react-router-dom';
import PonyNote from "./components/PonyNote";
import NotFound from "./components/NotFound";

class App extends Component {
  render() {
  return (
    <BrowserRouter>
    <Switch>
      <Route exact path="/" component={PonyNote} />
      <Route component={NotFound} />
    </Switch>
    </BrowserRouter>
  );
  }
}

export default App;
```

The above code will make use of [`BrowserRouter`](https://reacttraining.com/react-router/web/api/BrowserRouter), which means it will use the HTML5 history API to maintain the application routing. The [`Switch`](https://reacttraining.com/react-router/web/api/Switch) component is optional, but it is used for efficient routing. The [`Route`](https://reacttraining.com/react-router/web/api/Route) components render the target component when the location of the application matches it's path. If no path is specified to the `Route`, all path matches return true, which is useful for 404 pages.

Now that our component is ready, we can update our components to show actual content.

In the `PonyNote.jsx`:

```jsx
import React, { Component } from 'react';
import {Link} from 'react-router-dom';


export default class PonyNote extends Component {
  render() {
  return (
    <div>
    <h2>Welcome to PonyNote!</h2>
    <p>
      <Link to="/contact">Click Here</Link> to contact us!
    </p>
    </div>
  )
  }
}
```

This will display a welcome message and a link to contact page (which does not exist), which will show the NotFound component.

In the `NotFound.jsx` file:

```jsx
import React from 'react';


const NotFound = () => {
  return (
  <div>
    <h2>Not Found</h2>
    <p>The page you're looking for does not exists.</p>
  </div>
  )
}

export default NotFound
```

After this, start the django development server and webpack hotloader:

```
(ponynote) $ ./manage.py runserver
$ cd frontend && npm run start
```

You should see the following page in your browser:

![React router example welcome page]({filename}/images/modern-django-2-rrd-welcome.png)

And when you click on the contact link, you should get the 404 page:

![React router example 404 page]({filename}/images/modern-django-2-rrd-404.png)

And you'll be able to browse back to the previous page using the "Back" button in your browser.

### What is Redux?

[Redux](https://redux.js.org/) is a global application state management library based on [Flux](http://facebook.github.io/flux/) architecture and unidirectional data flow.

There are three major components in redux: [actions](https://redux.js.org/basics/actions), [reducers](https://redux.js.org/basics/reducers) and [store](https://redux.js.org/basics/store).

![Redux flow chart]({filename}/images/modern-django-2-redux-flow.png)

- Actions are payloads which are sent from your application to the redux store. They are the *only* source of information for the store.

- Reducers specify how the application state changes in response to the dispatched actions it receives.

- Store holds the state tree of the whole application. It is an object with methods to get the state and dispatch actions to perform state changes.


#### Setup redux

First install `react-redux`:

```
$ npm install --save redux react-redux
```

After installation, create directories for actions and reducers:

```
$ mkdir actions reducers
```

Create empty action and reducer files:

```
$ touch actions/index.js reducers/index.js
$ touch actions/notes.js reducers/notes.js
```

After the files are created, lets create our first reducer! Open `reducers/notes.js` and write the following code:

```js
const initialState = [
  {text: "Write code!"}
];


export default function notes(state=initialState, action) {
  switch (action.type) {
    default:
      return state;
  }
}
```

The `initialState` is the initial application state for notes (duh!). The `notes` function is a reducer, it takes state and action as arguments. We have defined one note for now.

Note that the `initialState` can be any valid javascript type. For our use case we are directly using Array but most commonly the state is defined as a Javascript object.

A common way of creating reducers is to have a switch statement which handles all types of actions using case label. For now, lets return the current application state as default with no cases.

After this reducer is created we need to use it in our application using redux store. For this, first edit `reducers/index.js`:

```jsx
import { combineReducers } from 'redux';
import notes from "./notes";


const ponyApp = combineReducers({
  notes,
})

export default ponyApp;
```

Using the above code we can combine multiple reducers into one. We don't need this in our application but for real world applications with lots of reducers, this comes in handy.

Now we need to create a redux store using this reducer. In `App.js` create a store:

```jsx
import { createStore } from "redux";
import ponyApp from "./reducers";

let store = createStore(ponyApp);
```

After creating store, we need to wrap our react application's root component with `react-redux`'s `Provider` component and pass `store` to it in order to use the redux store. The final App.js will look like this:

```jsx
import React, { Component } from 'react';
import {Route, Switch, BrowserRouter} from 'react-router-dom';

import { Provider } from "react-redux";
import { createStore } from "redux";
import ponyApp from "./reducers";

import PonyNote from "./components/PonyNote";
import NotFound from "./components/NotFound";

let store = createStore(ponyApp);

class App extends Component {
  render() {
    return (
      <Provider store={store}>
        <BrowserRouter>
          <Switch>
            <Route exact path="/" component={PonyNote} />
            <Route component={NotFound} />
          </Switch>
        </BrowserRouter>
      </Provider>
    );
  }
}

export default App;
```

#### Redux in action

Now that all setup for redux is done, we can use our redux state in the `PonyNote` component. Connect the `PonyNote` component with redux store to display notes on the web app:

```jsx
import React, { Component } from 'react';
import {connect} from 'react-redux';


class PonyNote extends Component {
  render() {
    return (
      <div>
        <h2>Welcome to PonyNote!</h2>
        <hr />

        <h3>Notes</h3>
        <table>
          <tbody>
            {this.props.notes.map(note => (
              <tr>
                <td>{note.text}</td>
                <td><button>edit</button></td>
                <td><button>delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }
}


const mapStateToProps = state => {
  return {
    notes: state.notes,
  }
}

const mapDispatchToProps = dispatch => {
  return {
  }
}


export default connect(mapStateToProps, mapDispatchToProps)(PonyNote);
```

In the above code we "connect" our component using the `connect` high order function provided by `react-redux`. `mapStateToProps` is used to "map" the application state to the "props" of the component. Here, we are passing the notes array as a component prop with same name. `mapDispatchToProps` is "mapping" action dispatcher functions to component "props".

Inside the render function we have created a table and iterated all notes with placeholder edit and delete button. The above code should result in a webpage like this:

![Redux sample component]({filename}/images/modern-django-2-redux-in-action.png)

#### Working with redux states using actions

Now that we have a read-only implementation of our note-taking app which just displays notes. We will now create actions, reducer cases and UI element to modify the redux state.

##### Defining actions and reducers

In `reducers/notes.js`, write cases to add, update and delete notes inside the switch statement.

```js
export default function notes(state=initialState, action) {
  let noteList = state.slice();

  switch (action.type) {

    case 'ADD_NOTE':
      return [...state, {text: action.text}];

    case 'UPDATE_NOTE':
      let noteToUpdate = noteList[action.id]
      noteToUpdate.text = action.text;
      noteList.splice(action.id, 1, noteToUpdate);
      return noteList;

    case 'DELETE_NOTE':
      noteList.splice(action.id, 1);
      return noteList;

    default:
      return state;
  }
}
```

In the above code we are handling different cases of action payload, namely `ADD_NOTE`, `UPDATE_NOTE` and `UPDATE_NOTE`. The individual cases do what their name suggest and return a modified copy of the state after the said action is done. Here we do not update the state directly, but we return a new state which will replace the current state of the notes reducer.

The cases in the reducers will only be invoked when an action is dispatched of corresponding type. In `actions/notes.js` declare the actions:

```js
export const addNote = text => {
  return {
    type: 'ADD_NOTE',
    text
  }
}

export const updateNote = (id, text) => {
  return {
    type: 'UPDATE_NOTE',
    id,
    text
  }
}

export const deleteNote = id => {
  return {
    type: 'DELETE_NOTE',
    id
  }
}
```

Each of the above functions returns an object with a `type` property which the reducer uses to determine *how* the state is to be updated. Besides `type` these payloads can have any property as values which can later be used inside the reducer function while modifying the state.

Update the `actions/index.js` file so that we can access all actions in one place:

```js
import * as notes from "./notes";

export {notes}
```

##### Using Actions inside a component

After the actions are defined, we can use them inside the `PonyNote` component by declaring properties in `mapDispatchToProps`.

Update `mapDispatchToProps` function to use all actions:

```js
import {notes} from "../actions";

const mapDispatchToProps = dispatch => {
  return {
    addNote: (text) => {
      dispatch(notes.addNote(text));
    },
    updateNote: (id, text) => {
      dispatch(notes.addNote(id, text));
    },
    deleteNote: (id) => {
      dispatch(notes.deleteNote(id));
    },
  }
}
```

Now all these dispatch actions are accessible inside a component using `this.props`.

##### Building UI elements to dispatch actions

Lets start by creating a form to add new notes to the notes redux state. In the `PonyNote` component, declare `state` and `submitNote` method.

```js
state = {
  text: ""
}

submitNote = (e) => {
  e.preventDefault();
  this.props.addNote(this.state.text);
  this.setState({text: ""});
}

```

Inside the body of the component add the HTML form to enter text and save the note:

```
<h3>Add new note</h3>
<form onSubmit={this.submitNote}>
  <input
    value={this.state.text}
    placeholder="Enter note here..."
    onChange={(e) => this.setState({text: e.target.value})}
    required />
  <input type="submit" value="Save Note" />
</form>
```

The above code will store the note text in the component state and save it when the form is submitted. `onSubmit`, the application will dispatch an action `ADD_NOTE` which will then add the note to redux state.

Similarly we can add an option to delete notes when the "delete" button is pressed. Replace the contents of `tbody` with the following:

```jsx
{this.props.notes.map((note, id) => (
  <tr key={`note_${id}`}>
    <td>{note.text}</td>
    <td><button>edit</button></td>
    <td><button onClick={() => this.props.deleteNote(id)}>delete</button></td>
  </tr>
))}
```

For updating notes, we will need to do some additional changes to our component state and form element so that it can support creating and updating notes at the same time.

```js
state = {
  text: "",
  updateNoteId: null,
}

resetForm = () => {
  this.setState({text: "", updateNoteId: null});
}

selectForEdit = (id) => {
  let note = this.props.notes[id];
  this.setState({text: note.text, updateNoteId: id});
}

submitNote = (e) => {
  e.preventDefault();
  if (this.state.updateNoteId === null) {
    this.props.addNote(this.state.text);
  } else {
    this.props.updateNote(this.state.updateNoteId, this.state.text);
  }
  this.resetForm();
}
```

The component state now keeps track whether we are creating or updating a note. The `submitNote` method changes behavior based on component state. We have also added a helper method to load and reset the form for updating notes.

Inside the form element, place a button to reset form after selecting notes to edit by mistake.

```
<button onClick={this.resetForm}>Reset</button>
```

And update the edit button to load notes for editing:

```
<td><button onClick={() => this.selectForEdit(id)}>edit</button></td>
```

This will result in a simple note-taking web app with functionality to add, update and edit notes. It should look like this:

![Redux working webapp]({filename}/images/modern-django-2-redux-working-webapp.png)

### Add some css

Before moving any further, lets add some css so that our application doesn't hurt our eyes. For this we will use [sakura.css](https://github.com/oxalorg/sakura), the same classless css library which is used for this blog!

Start by downloading normalize.css and sakura.css inside a css directory in our frontend root.

```
$ mkdir css
$ cd css
$ wget https://raw.githubusercontent.com/oxalorg/sakura/master/css/normalize.css
$ wget wget https://raw.githubusercontent.com/oxalorg/sakura/master/css/sakura.css
```

After this, update the index.css file to import these downloaded css files:

```
@import url("css/normalize.css");
@import url("css/sakura.css");
```

Much better!

![webapp with css]({filename}/images/modern-django-2-sakura.png)

########

Our webapp is working smoothly client-side but cannot store data permanently. In the [next post]({filename}/modern-django-part-3.md) we will create models and APIs in django to store and manipulate notes from database. This way we don't lose any notes.


### Reference

- [Example: Todo List with redux](https://redux.js.org/basics/example-todo-list)
- [react-router-dom docs](https://reacttraining.com/react-router/web/guides/philosophy)
- [redux data flow chart](https://medium.com/@abhayg772/introduction-to-redux-using-react-native-a8f1e8778333)
