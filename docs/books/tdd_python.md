# Book1 - Test-Driven Development with Python (2nd Edition)
### Obey the Testing Goat: Using Django, Selenium & JavaScript
#### by Harry J.W. Percival (O'Reilly, 2017)

---

## Part I. The Basics of TDD and Django

---

### Chapter 1: Getting Django Set Up Using a Functional Test

#### Obey the Testing Goat! Do Nothing Until You Have a Test

- **TDD core rule**: Never write production code without a failing test first
- **Functional Test (FT)**: A test from the user's perspective (also called acceptance test / end-to-end test)
- **The Testing Goat**: Metaphor for the discipline of TDD — always write the test first

```python
# functional_tests.py — the very first test
from selenium import webdriver

browser = webdriver.Firefox()
browser.get('http://localhost:8000')
assert 'Django' in browser.title
```

**Key library: `selenium`** — browser automation framework that drives real browsers (Firefox via geckodriver) for functional testing.

#### Getting Django Up and Running

```bash
django-admin.py startproject superlists
cd superlists
python manage.py runserver
```

- Creates project scaffold: `manage.py`, `superlists/settings.py`, `superlists/urls.py`
- Dev server at `http://127.0.0.1:8000/`
- Running the FT against the dev server confirms Django's default "it worked!" page

#### Starting a Git Repository

```bash
git init
echo "db.sqlite3" >> .gitignore
echo "__pycache__" >> .gitignore
echo "*.pyc" >> .gitignore
git add .
git commit -m "First commit: basic Django project and FT"
```

- Commit early and often — git is integral to the TDD workflow
- `.gitignore` the database, bytecode, and geckodriver logs

---

### Chapter 2: Extending Our Functional Test Using the unittest Module

#### Using a Functional Test to Scope Out a Minimum Viable App

- FTs should read like a **user story** — comments describe what the user sees and does
- The to-do list app: users enter items, the app remembers them, each user gets a unique URL

#### The Python Standard Library's unittest Module

**Key library: `unittest`** — Python's built-in test framework.

```python
from selenium import webdriver
import unittest

class NewVisitorTest(unittest.TestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    def test_can_start_a_list_and_retrieve_it_later(self):
        self.browser.get('http://localhost:8000')
        self.assertIn('To-Do', self.browser.title)
        self.fail('Finish the test!')

if __name__ == '__main__':
    unittest.main(warnings='ignore')
```

- **`unittest.TestCase`**: Base class providing test infrastructure
- **`setUp()`**: Runs before each test method (e.g., launch browser)
- **`tearDown()`**: Runs after each test, even on failure (e.g., close browser)
- **Test methods must start with `test_`** to be discovered
- **`self.fail(msg)`**: Always fails — useful as a reminder placeholder
- **Assertions**: `assertIn`, `assertEqual`, `assertTrue`, `assertFalse`

---

### Chapter 3: Testing a Simple Home Page with Unit Tests

#### Unit Tests, and How They Differ from Functional Tests

| Functional Tests | Unit Tests |
|---|---|
| Test from user's perspective | Test from programmer's perspective |
| Ensure correct features are built | Ensure code is clean and bug-free |
| Use Selenium / real browser | Use Django test client / direct calls |
| Slow, end-to-end | Fast, isolated |

**Double-loop TDD workflow**:

1. Write FT (outer loop) → fails
2. Write unit test (inner loop) → fails
3. Write minimal code → unit test passes
4. Repeat inner loop until FT passes
5. Refactor

#### Unit Testing in Django

```python
# lists/tests.py
from django.test import TestCase
from django.urls import resolve
from lists.views import home_page

class HomePageTest(TestCase):

    def test_root_url_resolves_to_home_page_view(self):
        found = resolve('/')
        self.assertEqual(found.func, home_page)
```

- **`django.test.TestCase`**: Enhanced `unittest.TestCase` with Django-specific helpers (auto test DB, test client)
- **`resolve(url)`**: Maps URL path to view function — tests URL routing
- Run with: `python manage.py test`

#### Django's MVC, URLs, and View Functions

```python
# superlists/urls.py
from django.conf.urls import url
from lists import views

urlpatterns = [
    url(r'^$', views.home_page, name='home'),
]
```

```python
# lists/views.py
from django.http import HttpResponse

def home_page(request):
    return HttpResponse('<html><title>To-Do Lists</title></html>')
```

- **URL patterns** use regex: `^$` matches root path
- **View functions** take `HttpRequest`, return `HttpResponse`

#### At Last! We Actually Write Some Application Code!

```bash
python manage.py startapp lists
```

Creates: `lists/models.py`, `lists/views.py`, `lists/tests.py`, `lists/admin.py`, `lists/migrations/`

#### The Unit-Test/Code Cycle

1. Run test → see it fail (read the traceback)
2. Make smallest possible code change
3. Run test → see it pass (or get a new error)
4. Repeat

---

### Chapter 4: What Are We Doing with All These Tests? (And, Refactoring)

#### Programming Is Like Pulling a Bucket of Water Up from a Well

- TDD is a **ratchet mechanism** — tests save your progress and prevent regression
- Each passing test is a notch in the ratchet

#### Using Selenium to Test User Interactions

```python
from selenium.webdriver.common.keys import Keys

inputbox = self.browser.find_element_by_id('id_new_item')
inputbox.send_keys('Buy peacock feathers')
inputbox.send_keys(Keys.ENTER)
```

#### The "Don't Test Constants" Rule, and Templates to the Rescue

- Don't test that HTML strings are exactly equal — test **behavior**, not constants
- Solution: move HTML to **templates** and test that the right template is used

##### Refactoring to Use a Template

```html
<!-- lists/templates/home.html -->
<html>
  <title>To-Do Lists</title>
</html>
```

```python
# lists/views.py
from django.shortcuts import render

def home_page(request):
    return render(request, 'home.html')
```

- Register app in `settings.py` `INSTALLED_APPS` for template discovery
- `render(request, template_name, context_dict)` searches app `templates/` folders

##### The Django Test Client

```python
class HomePageTest(TestCase):
    def test_uses_home_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'home.html')
```

- **`self.client`**: Django's test client, simulates GET/POST without a real server
- **`assertTemplateUsed(response, name)`**: Checks which template rendered the response — much better than string comparison

#### On Refactoring

- **Refactoring**: Changing code structure without changing behavior
- **Rule**: Only refactor when all tests pass
- **Rule**: Never change code and tests at the same time

#### Recap: The TDD Process

```
FT fails → write unit test → UT fails → write minimal code →
UT passes → refactor → repeat until FT passes → commit
```

---

### Chapter 5: Saving User Input: Testing the Database

#### Wiring Up Our Form to Send a POST Request

```html
<form method="POST">
  <input name="item_text" id="id_new_item" placeholder="Enter a to-do item" />
  {% csrf_token %}
</form>
```

- **`{% csrf_token %}`**: Django template tag — injects hidden CSRF protection token
- **CSRF (Cross-Site Request Forgery)**: Attack where malicious site triggers actions on your site

#### Processing a POST Request on the Server

```python
def test_can_save_a_POST_request(self):
    response = self.client.post('/', data={'item_text': 'A new list item'})
    self.assertIn('A new list item', response.content.decode())
```

#### Passing Python Variables to Be Rendered in the Template

```python
# View passes context to template
return render(request, 'home.html', {'new_item_text': request.POST.get('item_text', '')})
```

```html
<!-- Template uses {{ variable }} syntax -->
<td>{{ new_item_text }}</td>
```

#### Three Strikes and Refactor

- When you see duplication three times, it's time to extract a helper

#### The Django ORM and Our First Model

**Django ORM** — maps Python classes to database tables:

```python
# lists/models.py
from django.db import models

class Item(models.Model):
    text = models.TextField(default='')
```

**ORM operations**:

```python
item = Item()
item.text = 'First item'
item.save()                        # INSERT into database

Item.objects.create(text='Second') # Create + save in one step
Item.objects.all()                 # SELECT * (returns QuerySet)
Item.objects.count()               # COUNT(*)
Item.objects.first()               # First record
```

##### Our First Database Migration

```bash
python manage.py makemigrations   # Generate migration from model changes
python manage.py migrate          # Apply migrations to database
```

#### Saving the POST to the Database

```python
def home_page(request):
    if request.method == 'POST':
        Item.objects.create(text=request.POST['item_text'])
        return redirect('/')
    items = Item.objects.all()
    return render(request, 'home.html', {'items': items})
```

#### Redirect After a POST

- **Web best practice**: Always redirect after a successful POST to prevent duplicate submissions on refresh
- `return redirect('/')` sends HTTP 302

##### Better Unit Testing Practice: Each Test Should Test One Thing

```python
# GOOD: Separate concerns into separate tests
def test_can_save_a_POST_request(self):
    self.client.post('/', data={'item_text': 'A new list item'})
    self.assertEqual(Item.objects.count(), 1)

def test_redirects_after_POST(self):
    response = self.client.post('/', data={'item_text': 'A new list item'})
    self.assertEqual(response.status_code, 302)
    self.assertEqual(response['location'], '/')
```

#### Rendering Items in the Template

```html
<table id="id_list_table">
  {% for item in items %}
    <tr><td>{{ forloop.counter }}: {{ item.text }}</td></tr>
  {% endfor %}
</table>
```

- **`{% for %}...{% endfor %}`**: Django template loop
- **`{{ forloop.counter }}`**: 1-based loop index

---

### Chapter 6: Improving Functional Tests: Ensuring Isolation and Removing Voodoo Sleeps

#### Ensuring Test Isolation in Functional Tests

**Problem**: Database state leaks between test runs.

**Solution**: **`LiveServerTestCase`** — Django test class that creates a test DB and dev server per test.

```python
from django.test import LiveServerTestCase

class NewVisitorTest(LiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    def test_can_start_a_list(self):
        self.browser.get(self.live_server_url)  # Use dynamic URL, not hardcoded
```

- Auto-creates and destroys a test database for each test
- `self.live_server_url` provides the actual server address

##### Running Just the Unit Tests

```bash
python manage.py test lists                    # Unit tests only
python manage.py test functional_tests         # FTs only
```

#### On Implicit and Explicit Waits, and Voodoo time.sleeps

**Problem with `time.sleep()`**: Too slow (wastes time) or too fast (flaky tests).

**Explicit wait pattern** (best practice):

```python
import time
from selenium.common.exceptions import WebDriverException

MAX_WAIT = 10

def wait_for_row_in_list_table(self, row_text):
    start_time = time.time()
    while True:
        try:
            table = self.browser.find_element_by_id('id_list_table')
            rows = table.find_elements_by_tag_name('tr')
            self.assertIn(row_text, [row.text for row in rows])
            return
        except (AssertionError, WebDriverException) as e:
            if time.time() - start_time > MAX_WAIT:
                raise e
            time.sleep(0.5)
```

- Polls every 0.5s up to `MAX_WAIT` seconds
- Catches `WebDriverException` (element not found yet) and `AssertionError` (wrong content)
- Returns immediately on success — no wasted time

---

### Chapter 7: Working Incrementally

#### Small Design When Necessary

- **YAGNI** (You Ain't Gonna Need It): Only build what's needed to pass current tests
- **REST-ish URL design**: `/lists/<id>/` for viewing, `/lists/new` for creating, `/lists/<id>/add_item` for adding

#### Implementing the New Design Incrementally Using TDD

**New models with ForeignKey**:

```python
class List(models.Model):
    pass

class Item(models.Model):
    text = models.TextField(default='')
    list = models.ForeignKey(List, default=None, on_delete=models.CASCADE)
```

**ORM reverse relationship**:

```python
list_ = List.objects.get(id=list_id)
items = list_.item_set.all()  # Django auto-creates reverse accessor
```

#### Ensuring We Have a Regression Test

```python
def test_multiple_users_can_start_lists_at_different_urls(self):
    # Edith creates a list
    self.browser.get(self.live_server_url)
    # ... add item, get URL ...
    edith_list_url = self.browser.current_url
    self.assertRegex(edith_list_url, '/lists/.+')

    # New browser session for Francis (new user)
    self.browser.quit()
    self.browser = webdriver.Firefox()

    # Francis should NOT see Edith's items
    page_text = self.browser.find_element_by_tag_name('body').text
    self.assertNotIn('Buy peacock feathers', page_text)
```

- `self.assertRegex(string, pattern)` — regex assertion
- New browser instance simulates a different user

#### Taking a First, Self-Contained Step: One New URL

**Key Django assertion**:

```python
self.assertContains(response, 'itemey 1')
```

- `assertContains(response, text)` — checks status 200 AND text present in decoded content
- Cleaner than manual `.content.decode()` + `assertIn()`

#### URL patterns with capture groups

```python
urlpatterns = [
    url(r'^$', views.home_page, name='home'),
    url(r'^lists/new$', views.new_list, name='new_list'),
    url(r'^lists/(\d+)/$', views.view_list, name='view_list'),
    url(r'^lists/(\d+)/add_item$', views.add_item, name='add_item'),
]
```

- `(\d+)` captures numeric ID, passed as argument to view function

---

## Part II. Web Development Sine Qua Nons

---

### Chapter 8: Prettification: Layout and Styling, and What to Test About It

#### What to Functionally Test About Layout and Style

- Don't write tests for aesthetics — test that **static files load correctly** (smoke test)
- Use `assertAlmostEqual` with `delta` for layout assertions (avoids pixel-brittle tests)

```python
def test_layout_and_styling(self):
    self.browser.get(self.live_server_url)
    self.browser.set_window_size(1024, 768)
    inputbox = self.browser.find_element_by_id('id_new_item')
    self.assertAlmostEqual(
        inputbox.location['x'] + inputbox.size['width'] / 2,
        512, delta=10
    )
```

#### Django Template Inheritance

```html
<!-- base.html -->
<html>
<head><title>To-Do Lists</title></head>
<body>
  <h1>{% block header_text %}{% endblock %}</h1>
  <form method="POST" action="{% block form_action %}{% endblock %}">
    {% csrf_token %}
    <input name="item_text" id="id_new_item" placeholder="Enter a to-do item" />
  </form>
  {% block table %}{% endblock %}
</body>
</html>

<!-- home.html -->
{% extends 'base.html' %}
{% block header_text %}Start a new To-Do list{% endblock %}
{% block form_action %}/lists/new{% endblock %}

<!-- list.html -->
{% extends 'base.html' %}
{% block header_text %}Your To-Do list{% endblock %}
{% block form_action %}/lists/{{ list.id }}/add_item{% endblock %}
{% block table %}
  <table id="id_list_table">
    {% for item in list.item_set.all %}
      <tr><td>{{ forloop.counter }}: {{ item.text }}</td></tr>
    {% endfor %}
  </table>
{% endblock %}
```

#### Static Files in Django

```python
# settings.py
STATIC_URL = '/static/'
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..', 'static'))
```

```bash
python manage.py collectstatic --noinput
```

##### Switching to StaticLiveServerTestCase

**Key library: `django.contrib.staticfiles.testing.StaticLiveServerTestCase`**

```python
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

class NewVisitorTest(StaticLiveServerTestCase):
    # Automatically serves static files during tests
    pass
```

- Replaces `LiveServerTestCase` — serves static files so CSS/JS load in FTs

---

### Chapter 9: Testing Deployment Using a Staging Site

#### TDD and the Danger Areas of Deployment

- Danger areas: static files, database, dependencies
- **Solution**: Run FTs against a staging server before deploying to production

#### As Always, Start with a Test

```python
import os

class NewVisitorTest(StaticLiveServerTestCase):
    def setUp(self):
        self.browser = webdriver.Firefox()
        staging_server = os.environ.get('STAGING_SERVER')
        if staging_server:
            self.live_server_url = 'http://' + staging_server
```

```bash
# Run FTs against staging
STAGING_SERVER=superlists-staging.example.com python manage.py test functional_tests
```

#### Manually Provisioning a Server to Host Our Site

**Directory structure on server**:

```
~/sites/SITENAME/
    database/       # db.sqlite3
    source/         # git repo
    static/         # collectstatic output
    virtualenv/     # Python virtualenv
```

**Key tools**: Nginx (reverse proxy), Gunicorn (WSGI server), Systemd (process manager)

---

### Chapter 10: Getting to a Production-Ready Deployment

#### Switching to Gunicorn

**Key tool: `gunicorn`** — Production WSGI HTTP server for Python.

```bash
pip install gunicorn
gunicorn --bind unix:/tmp/SITENAME.socket superlists.wsgi:application
```

#### Switching to Using Unix Sockets

- Unix sockets (`/tmp/SITENAME.socket`) instead of TCP ports — more secure, no port collisions

#### Switching DEBUG to False and Setting ALLOWED_HOSTS

```python
DEBUG = False
ALLOWED_HOSTS = ['superlists-staging.example.com']
```

#### Using Systemd to Make Sure Gunicorn Starts on Boot

```ini
# /etc/systemd/system/gunicorn-SITENAME.service
[Unit]
Description=Gunicorn server for SITENAME

[Service]
Restart=on-failure
User=elspeth
WorkingDirectory=/home/elspeth/sites/SITENAME/source
ExecStart=/home/elspeth/sites/SITENAME/virtualenv/bin/gunicorn \
    --bind unix:/tmp/SITENAME.socket superlists.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable gunicorn-SITENAME
sudo systemctl start gunicorn-SITENAME
```

---

### Chapter 11: Automating Deployment with Fabric

**Key library: `fabric`** — Python tool for automating SSH commands on remote servers.

```bash
pip install fabric3
```

#### Breakdown of a Fabric Script for Our Deployment

```python
# deploy_tools/fabfile.py
from fabric.api import run, env
import random

REPO_URL = 'https://github.com/hjwp/book-example.git'

def deploy():
    site_folder = f'/home/{env.user}/sites/{env.host}'
    source_folder = site_folder + '/source'
    _create_directory_structure_if_necessary(site_folder)
    _get_latest_source(source_folder)
    _update_virtualenv(source_folder)
    _update_static_files(source_folder)
    _update_database(source_folder)

def _create_directory_structure_if_necessary(site_folder):
    for subfolder in ('database', 'source', 'static', 'virtualenv'):
        run(f'mkdir -p {site_folder}/{subfolder}')

def _get_latest_source(source_folder):
    run(f'cd {source_folder} && git fetch')

def _update_virtualenv(source_folder):
    run(f'{source_folder}/../virtualenv/bin/pip install -r {source_folder}/requirements.txt')

def _update_static_files(source_folder):
    run(f'cd {source_folder} && ../virtualenv/bin/python manage.py collectstatic --noinput')

def _update_database(source_folder):
    run(f'cd {source_folder} && ../virtualenv/bin/python manage.py migrate --noinput')
```

```bash
fab deploy:host=elspeth@superlists-staging.example.com
```

- **Idempotent**: Safe to run multiple times — checks before creating
- Version-control the deployment script itself

---

### Chapter 12: Splitting Our Tests into Multiple Files, and a Generic Wait Helper

#### Skipping a Test

```python
from unittest import skip

@skip
def test_cannot_add_empty_list_items(self):
    self.fail('write me!')
```

- `@skip` temporarily disables a test — remove before committing

#### Splitting Functional Tests Out into Many Files

```
functional_tests/
    __init__.py
    base.py                          # Shared FunctionalTest base class
    test_simple_list_creation.py
    test_layout_and_styling.py
    test_list_item_validation.py
```

```python
# functional_tests/base.py
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

MAX_WAIT = 10

class FunctionalTest(StaticLiveServerTestCase):
    def setUp(self):
        self.browser = webdriver.Firefox()
    def tearDown(self):
        self.browser.quit()
    def wait_for(self, fn):
        # generic wait helper (see below)
```

```python
# functional_tests/test_simple_list_creation.py
from .base import FunctionalTest  # relative import

class NewVisitorTest(FunctionalTest):
    def test_can_start_a_list_for_one_user(self):
        ...
```

#### A New Functional Test Tool: A Generic Explicit Wait Helper

```python
def wait_for(self, fn):
    start_time = time.time()
    while True:
        try:
            return fn()
        except (AssertionError, WebDriverException) as e:
            if time.time() - start_time > MAX_WAIT:
                raise e
            time.sleep(0.5)
```

**Usage with lambdas** — defer execution until inside the retry loop:

```python
self.wait_for(lambda: self.assertEqual(
    self.browser.find_element_by_css_selector('.has-error').text,
    "You can't have an empty list item"
))
```

#### Refactoring Unit Tests into Several Files

```
lists/tests/
    __init__.py
    test_models.py
    test_views.py
    test_forms.py
```

---

### Chapter 13: Validation at the Database Layer

#### Model-Layer Validation

- Push validation **as low as possible** — database layer is the last line of defense

##### The self.assertRaises Context Manager

```python
from django.core.exceptions import ValidationError

def test_cannot_save_empty_list_items(self):
    list_ = List.objects.create()
    item = Item(list=list_, text='')
    with self.assertRaises(ValidationError):
        item.save()
        item.full_clean()  # Must call explicitly!
```

##### A Django Quirk: Model Save Doesn't Run Validation

- **`model.save()`** does NOT call validators on `TextField`
- **`model.full_clean()`** manually triggers all model validation
- This is a Django design choice — form-level validation is separate from save

#### Surfacing Model Validation Errors in the View

```python
from django.core.exceptions import ValidationError

def view_list(request, list_id):
    list_ = List.objects.get(id=list_id)
    error = None
    if request.method == 'POST':
        try:
            item = Item(text=request.POST['item_text'], list=list_)
            item.full_clean()
            item.save()
            return redirect(f'/lists/{list_.id}/')
        except ValidationError:
            error = "You can't have an empty list item"
    return render(request, 'list.html', {'list': list_, 'error': error})
```

#### Django Pattern: Processing POST Requests in the Same View as Renders the Form

- Single view handles both GET (display form) and POST (process form)
- On validation error, re-render same template with error message

#### Refactor: Removing Hardcoded URLs

```python
# In models
from django.urls import reverse

class List(models.Model):
    def get_absolute_url(self):
        return reverse('view_list', args=[self.id])

# In views — redirect using model method
return redirect(list_)  # Django calls get_absolute_url()
```

- **`{% url 'view_list' list.id %}`** — template tag for reverse URL resolution

---

### Chapter 14: A Simple Form

#### Moving Validation Logic into a Form

**Key library: `django.forms`** — Django's form framework handles validation, rendering, and saving.

##### Exploring the Forms API with a Unit Test

```python
# lists/forms.py
from django import forms
from lists.models import Item

EMPTY_ITEM_ERROR = "You can't have an empty list item"

class ItemForm(forms.models.ModelForm):
    class Meta:
        model = Item
        fields = ('text',)
        widgets = {
            'text': forms.fields.TextInput(attrs={
                'placeholder': 'Enter a to-do item',
                'class': 'form-control input-lg',
            }),
        }
        error_messages = {
            'text': {'required': EMPTY_ITEM_ERROR}
        }
```

- **`ModelForm`**: Auto-generates form from model — reuses model field definitions and validation
- **`widgets`**: Customize HTML rendering (placeholder, CSS classes)
- **`error_messages`**: Customize validation error text

##### Testing and Customising Form Validation

```python
def test_form_validation_for_blank_items(self):
    form = ItemForm(data={'text': ''})
    self.assertFalse(form.is_valid())
    self.assertEqual(form.errors['text'], [EMPTY_ITEM_ERROR])
```

- **`form.is_valid()`**: Returns `True`/`False`, populates `form.errors`
- **`form.errors`**: Dict mapping field names to lists of error strings

#### Using the Form in Our Views

```python
# GET — render empty form
def home_page(request):
    return render(request, 'home.html', {'form': ItemForm()})

# POST — validate and save
def new_list(request):
    form = ItemForm(data=request.POST)
    if form.is_valid():
        list_ = List.objects.create()
        form.save(for_list=list_)
        return redirect(list_)
    else:
        return render(request, 'home.html', {'form': form})
```

```html
<!-- Template renders form field + errors -->
{{ form.text }}
{% if form.errors %}
  <div class="form-group has-error">
    <span class="help-block">{{ form.text.errors }}</span>
  </div>
{% endif %}
```

#### Using the Form's Own Save Method

```python
class ItemForm(forms.models.ModelForm):
    # ...
    def save(self, for_list):
        self.instance.list = for_list
        return super().save()
```

#### An Unexpected Benefit: Free Client-Side Validation from HTML5

- Django ModelForm adds `required` attribute to HTML inputs from `blank=False`
- Browsers prevent empty form submission automatically
- Still need server-side validation as a safety net

---

### Chapter 15: More Advanced Forms

#### Preventing Duplicates at the Model Layer

```python
class Item(models.Model):
    text = models.TextField(default='')
    list = models.ForeignKey(List, default=None)

    class Meta:
        ordering = ('id',)
        unique_together = ('list', 'text')
```

- **`unique_together`**: Database-level constraint — same text + same list = error
- **`ordering`**: Default sort order for QuerySets

#### A More Complex Form to Handle Uniqueness Validation

```python
class ExistingListItemForm(ItemForm):
    def __init__(self, for_list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.list = for_list

    def validate_unique(self):
        try:
            self.instance.validate_unique()
        except ValidationError as e:
            e.error_dict = {'text': [DUPLICATE_ITEM_ERROR]}
            self._update_errors(e)

    def save(self):
        return forms.models.ModelForm.save(self)
```

- Form needs list context to validate uniqueness across items in the same list
- Override `validate_unique()` to customize the error message

#### A Little Digression on Queryset Ordering and String Representations

```python
class Item(models.Model):
    def __str__(self):
        return self.text
```

- `__str__` makes debugging/assertions much more readable

---

### Chapter 16: Dipping Our Toes, Very Tentatively, into JavaScript

#### Setting Up a Basic JavaScript Test Runner

**Key library: `QUnit`** — JavaScript unit testing framework.

```html
<!-- lists/static/tests/tests.html -->
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="qunit-2.0.1.css">
</head>
<body>
  <div id="qunit"></div>
  <div id="qunit-fixture">
    <!-- Test fixtures: HTML that gets reset for each test -->
    <form>
      <input id="id_text" />
      <div class="form-group has-error">
        <span class="help-block">An error</span>
      </div>
    </form>
  </div>
  <script src="qunit-2.0.1.js"></script>
  <script src="../jquery-3.1.1.min.js"></script>
  <script src="../list.js"></script>
  <script>
    QUnit.test("errors are hidden on input", function (assert) {
      $('#id_text').trigger('input');
      assert.equal($('.has-error').is(':visible'), false);
    });
  </script>
</body>
</html>
```

#### Using jQuery and the Fixtures Div

- **`$('#id')`**: jQuery selector
- **`.on('event', fn)`**: Attach event listener
- **`.is(':visible')`**: Check if element is displayed
- **`.hide()` / `.show()`**: Toggle visibility

#### Building a JavaScript Unit Test for Our Desired Functionality

```javascript
// lists/static/list.js
$('#id_text').on('input', function () {
    $('.has-error').hide();
});
```

#### JavaScript Testing in the TDD Cycle

- Write QUnit test → fails → implement JS → passes → refactor
- Same Red/Green/Refactor cycle as Python TDD

---

### Chapter 17: Deploying Our New Code

#### Staging Deploy

```bash
cd deploy_tools
fab deploy:host=elspeth@superlists-staging.example.com
```

#### Live Deploy

```bash
fab deploy:host=elspeth@superlists.example.com
sudo systemctl restart gunicorn-superlists.example.com
```

#### Wrap-Up: git tag the New Release

```bash
git tag -f LIVE
git push -f origin LIVE
```

---

## Part III. More Advanced Topics in Testing

---

### Chapter 18: User Authentication, Spiking, and De-Spiking

#### Passwordless Auth

- Token-based login: generate unique token, email login URL, user clicks link to authenticate
- No passwords to store or manage

#### Exploratory Coding, aka "Spiking"

- **Spike**: Prototype code to explore an API or solution without TDD discipline
- Done on a **separate branch**: `git checkout -b passwordless-spike`
- Goal: learn how something works, then throw away the code

#### De-spiking

- Rewrite the spike code using proper TDD
- Revert spike branch: `git checkout master`
- Write tests first, implement properly

#### Custom Authentication Models

```python
# accounts/models.py
class Token(models.Model):
    email = models.EmailField()
    uid = models.CharField(default=uuid.uuid4, max_length=40)

class ListUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(primary_key=True)
    USERNAME_FIELD = 'email'
    objects = ListUserManager()
```

#### Custom Authentication Backend

```python
# accounts/authentication.py
class PasswordlessAuthenticationBackend:
    def authenticate(self, uid):
        try:
            token = Token.objects.get(uid=uid)
        except Token.DoesNotExist:
            return None
        try:
            user = ListUser.objects.get(email=token.email)
        except ListUser.DoesNotExist:
            user = ListUser.objects.create(email=token.email)
        return user

    def get_user(self, email):
        try:
            return ListUser.objects.get(email=email)
        except ListUser.DoesNotExist:
            return None
```

```python
# settings.py
AUTH_USER_MODEL = 'accounts.ListUser'
AUTHENTICATION_BACKENDS = ['accounts.authentication.PasswordlessAuthenticationBackend']
```

#### Sending Emails from Django

```python
from django.core.mail import send_mail

send_mail(
    'Your login link for Superlists',
    f'Use this link to log in:\n\n{url}',
    'noreply@superlists',
    [email],
)
```

#### Using Environment Variables to Avoid Secrets in Source Code

```python
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')
```

#### A Minimal Custom User Model

- Minimal user model uses email as primary key
- Tests serve as documentation for model behavior

---

### Chapter 19: Using Mocks to Test External Dependencies or Reduce Duplication

#### Mocking Manually, aka Monkeypatching

```python
def test_sends_mail(self):
    self.send_mail_called = False

    def fake_send_mail(subject, body, from_email, to_list):
        self.send_mail_called = True
        self.subject = subject

    accounts.views.send_mail = fake_send_mail  # monkeypatch
    self.client.post('/accounts/send_login_email', data={'email': 'a@b.com'})
    self.assertTrue(self.send_mail_called)
```

#### The Python Mock Library

**Key library: `unittest.mock`** — Python's built-in mocking framework (stdlib since 3.3).

```python
from unittest.mock import Mock, patch, call

# Mock objects auto-create attributes and track calls
m = Mock()
m.any_attribute            # returns another Mock
m.any_method()             # returns a Mock, records the call
m.called                   # True — was it called?
m.call_args                # call() object with (args, kwargs)
m.return_value = 42        # configure what it returns
```

##### Using unittest.patch

```python
from unittest.mock import patch

@patch('accounts.views.send_mail')
def test_sends_mail_to_address_from_post(self, mock_send_mail):
    self.client.post('/accounts/send_login_email', data={'email': 'a@b.com'})

    self.assertTrue(mock_send_mail.called)
    (subject, body, from_email, to_list), kwargs = mock_send_mail.call_args
    self.assertEqual(subject, 'Your login link for Superlists')
    self.assertEqual(to_list, ['a@b.com'])
```

**How `@patch` works**:

1. Finds object at the dotted path (e.g., `accounts.views.send_mail`)
2. Replaces it with a `Mock` object for the duration of the test
3. Injects the mock as an extra argument to the test method
4. Restores the original after the test

**Critical rule**: Patch where the object is **used**, not where it's **defined**:

```python
# accounts/views.py imports send_mail
# So patch 'accounts.views.send_mail', NOT 'django.core.mail.send_mail'
```

##### Patching at the Class Level

```python
@patch('accounts.views.auth')
class LoginViewTest(TestCase):
    def test_redirects(self, mock_auth):
        ...
    def test_calls_authenticate(self, mock_auth):
        mock_auth.authenticate.return_value = None
        ...
```

#### Using mock.return_value

```python
mock_auth.authenticate.return_value = mock_user
# Now when view calls auth.authenticate(...), it gets mock_user back
```

#### Checking That We Send the User a Link with a Token

```python
@patch('accounts.views.send_mail')
def test_sends_link_to_login_using_token_uid(self, mock_send_mail):
    self.client.post('/accounts/send_login_email', data={'email': 'a@b.com'})
    token = Token.objects.first()
    expected_url = f'http://testserver/accounts/login?token={token.uid}'
    (subject, body, from_email, to_list), kwargs = mock_send_mail.call_args
    self.assertIn(expected_url, body)
```

#### Testing the Django Messages Framework

```python
# Better: test behavior, not implementation
def test_adds_success_message(self):
    response = self.client.post('/accounts/send_login_email',
        data={'email': 'a@b.com'}, follow=True)  # follow redirects
    message = list(response.context['messages'])[0]
    self.assertEqual(message.message, "Check your email...")
    self.assertEqual(message.tags, "success")
```

---

### Chapter 20: Test Fixtures and a Decorator for Explicit Waits

#### Skipping the Login Process by Pre-creating a Session

**Test Fixture**: Pre-created data that lets tests skip repetitive setup.

```python
def create_pre_authenticated_session(self, email):
    user = User.objects.create(email=email)
    session = SessionStore()
    session[SESSION_KEY] = user.pk
    session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
    session.save()

    # Must visit domain before setting cookie
    self.browser.get(self.live_server_url + '/404_no_such_url/')
    self.browser.add_cookie(dict(
        name=settings.SESSION_COOKIE_NAME,
        value=session.session_key,
        path='/',
    ))
```

- **`SessionStore`**: Django's session backend — creates a session record in DB
- **`browser.add_cookie()`**: Inject session cookie into Selenium browser
- Must navigate to the domain first (cookies are domain-scoped)

#### Our Final Explicit Wait Helper: A Wait Decorator

```python
import time
from functools import wraps

def wait(fn):
    @wraps(fn)
    def modified_fn(*args, **kwargs):
        start_time = time.time()
        while True:
            try:
                return fn(*args, **kwargs)
            except (AssertionError, WebDriverException) as e:
                if time.time() - start_time > MAX_WAIT:
                    raise e
                time.sleep(0.5)
    return modified_fn
```

**Usage** — decorate helper methods directly:

```python
@wait
def wait_for_row_in_list_table(self, row_text):
    table = self.browser.find_element_by_id('id_list_table')
    rows = table.find_elements_by_tag_name('tr')
    self.assertIn(row_text, [row.text for row in rows])

@wait
def wait_to_be_logged_in(self, email):
    self.browser.find_element_by_link_text('Log out')
    navbar = self.browser.find_element_by_css_selector('.navbar')
    self.assertIn(email, navbar.text)
```

---

### Chapter 21: Server-Side Debugging

#### The Proof Is in the Pudding: Using Staging to Catch Final Bugs

- Run FTs against staging server to catch deployment-specific bugs
- Logging is essential for debugging production issues

##### Setting Up Logging

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'level': 'DEBUG', 'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'django': {'handlers': ['console']},
    },
    'root': {'level': 'INFO'},
}
```

#### Setting Secret Environment Variables on the Server

```bash
echo "EMAIL_PASSWORD=mysecret" >> ~/.env
# Source in Gunicorn systemd service via EnvironmentFile=
```

#### Managing the Test Database on Staging

- Create sessions on the staging server for FTs using Django management commands
- Use `fabric` to run management commands remotely

---

### Chapter 22: Finishing "My Lists": Outside-In TDD

#### The Alternative: "Inside-Out"

- **Inside-Out**: Build models first, then views, then templates
- Risk: building inner components more general than needed

#### Why Prefer "Outside-In"?

- **Outside-In**: Start from templates/UI, work inward to views, then models
- Also called **"programming by wishful thinking"** — design the API you wish you had
- Each layer's tests inform the next layer's design

#### The Outside Layer: Presentation and Templates

- Start with FT describing user-visible behavior
- FT failure reveals what the template needs

#### Moving Down One Layer to View Functions (the Controller)

- Template needs data → view must provide it
- Write unit test for view → implement view

#### Moving Down to the Model Layer

```python
class List(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)

    @property
    def name(self):
        return self.item_set.first().text
```

#### The Outside-In Workflow

```
FT → Template needs X → View test → View needs Y from model →
Model test → Model implementation → View passes → FT passes
```

---

### Chapter 23: Test Isolation, and "Listening to Your Tests"

#### A First Attempt at Using Mocks for Isolation

```python
from unittest.mock import patch, Mock

@patch('lists.views.NewListForm')
def test_passes_POST_data_to_NewListForm(self, mockNewListForm):
    self.client.post('/lists/new', data={'text': 'new item'})
    mockNewListForm.assert_called_once_with(data=self.request.POST)
```

##### Using Mock side_effects to Check the Sequence of Events

```python
def check_owner_assigned():
    self.assertEqual(mock_list.owner, user)

mock_list.save.side_effect = check_owner_assigned
```

- `side_effect` runs a function when the mock is called — verifies ordering

#### Listen to Your Tests: Ugly Tests Signal a Need to Refactor

- Hard-to-write tests → code design needs improvement
- Solution: extract collaborators, hide ORM behind helper methods

#### Rewriting Our Tests for the View to Be Fully Isolated

```python
@patch('lists.views.NewListForm')
def test_saves_form_with_owner_if_form_valid(self, mockNewListForm):
    mock_form = mockNewListForm.return_value
    mock_form.is_valid.return_value = True
    new_list(self.request)
    mock_form.save.assert_called_once_with(owner=self.request.user)
```

#### Moving Down to the Forms Layer

```python
class NewListForm(ItemForm):
    def save(self, owner):
        if owner.is_authenticated:
            return List.create_new(first_item_text=self.cleaned_data['text'], owner=owner)
        else:
            return List.create_new(first_item_text=self.cleaned_data['text'])
```

#### Moving Down to the Models Layer

```python
@staticmethod
def create_new(first_item_text, owner=None):
    list_ = List.objects.create(owner=owner)
    Item.objects.create(text=first_item_text, list=list_)
    return list_
```

#### Thinking of Interactions Between Layers as "Contracts"

- **Implicit contract**: When you mock `form.save(owner=user)`, you're claiming the real form accepts `owner`
- Verify contracts with integration tests

#### Conclusions: When to Write Isolated Versus Integrated Tests

- **Let complexity be your guide**: Simple code → integrated tests; complex code → isolated tests
- Keep a few integrated **sanity check** tests alongside isolated tests
- Use all three layers: FTs, integrated tests, isolated unit tests

---

### Chapter 24: Continuous Integration (CI)

#### Installing Jenkins

**Key tool: Jenkins** — open-source CI server (Java-based).

```bash
wget -q -O - https://pkg.jenkins.io/debian-stable/jenkins.io.key | apt-key add -
apt-get install jenkins
```

#### Configuring Jenkins

- Runs on port 8080
- **Key plugins**: ShiningPanda (Python/virtualenv), Xvfb (virtual display), Git

#### Setting Up Our Project

- **Source Code Management**: Git repo URL
- **Build Triggers**: Poll SCM (`H/5 * * * *`)
- **Build Environment**: Start Xvfb before build (1024x768x24)

#### Taking Screenshots

```python
import os
from datetime import datetime

SCREEN_DUMP_LOCATION = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screendumps')

def _get_filename(self):
    timestamp = datetime.now().isoformat().replace(':', '.')[:19]
    return f'{SCREEN_DUMP_LOCATION}/{self.__class__.__name__}.{self._testMethodName}-window{self._windowId}-{timestamp}'

def take_screenshot(self):
    filename = self._get_filename() + '.png'
    self.browser.get_screenshot_as_file(filename)

def dump_html(self):
    filename = self._get_filename() + '.html'
    with open(filename, 'w') as f:
        f.write(self.browser.page_source)
```

- Screenshots + HTML dumps on test failure — invaluable for debugging CI

#### If in Doubt, Try Bumping the Timeout

```python
MAX_WAIT = 20  # or even 30 for CI environments
```

- CI servers are often under heavier load — increase timeouts generously

#### Running Our QUnit JavaScript Tests in Jenkins with PhantomJS

**Key tool: PhantomJS** — headless browser for JavaScript testing (deprecated, prefer Xvfb+Firefox).

```bash
npm install -g phantomjs
phantomjs runner.js tests.html
```

---

### Chapter 25: The Token Social Bit, the Page Pattern, and an Exercise for the Reader

#### The Page Pattern

**Page Object Pattern**: Encapsulates page structure in reusable classes.

```python
class ListPage:
    def __init__(self, test):
        self.test = test

    def get_table_rows(self):
        return self.test.browser.find_elements_by_css_selector('#id_list_table tr')

    @wait
    def wait_for_row_in_list_table(self, item_text, item_number):
        expected = f'{item_number}: {item_text}'
        rows = self.get_table_rows()
        self.test.assertIn(expected, [row.text for row in rows])

    def get_item_input_box(self):
        return self.test.browser.find_element_by_id('id_text')

    def add_list_item(self, item_text):
        new_item_no = len(self.get_table_rows()) + 1
        self.get_item_input_box().send_keys(item_text)
        self.get_item_input_box().send_keys(Keys.ENTER)
        self.wait_for_row_in_list_table(item_text, new_item_no)
        return self  # method chaining
```

**Benefits**:

- When HTML changes, update one place (the Page object), not every test
- Tests read like narratives: `ListPage(self).add_list_item('Buy milk')`
- Method chaining via `return self`

#### An FT with Multiple Users, and addCleanup

```python
def test_can_share_a_list_with_another_user(self):
    self.create_pre_authenticated_session('edith@example.com')
    edith_browser = self.browser
    self.addCleanup(lambda: quit_if_possible(edith_browser))

    oni_browser = webdriver.Firefox()
    self.addCleanup(lambda: quit_if_possible(oni_browser))
    self.browser = oni_browser
    self.create_pre_authenticated_session('oni@example.com')
```

- **`self.addCleanup(fn)`**: Register cleanup functions that run after tearDown, even on failure

---

### Chapter 26: Fast Tests, Slow Tests, and Hot Lava

#### Thesis: Unit Tests Are Superfast and Good Besides That

- **Fast feedback** keeps you in flow state
- Unit tests drive better design by forcing decoupled code
- Run in milliseconds vs. minutes for FTs

#### The Problems with "Pure" Unit Tests

- **Isolated tests can be harder to read** — mock setup obscures intent
- **Isolated tests don't automatically test integration** — mocks can lie
- **Unit tests seldom catch unexpected bugs** — they test what you expect
- **Mocky tests become tightly coupled to implementation** — refactoring breaks tests

#### Synthesis: What Do We Want from Our Tests, Anyway?

Three goals:

1. **Correctness**: Does the code work?
2. **Clean, Maintainable Code**: Is the design good?
3. **Productive Workflow**: Is the feedback loop fast enough?

#### Architectural Solutions

##### Ports and Adapters / Hexagonal / Clean Architecture

- Identify **boundaries** (DB, UI, network, email)
- **Core logic**: Pure Python, no side effects, easy to unit test
- **Adapters**: Handle boundary interactions, tested with integration tests

##### Functional Core, Imperative Shell

- Core follows **functional programming** (no side effects, pure functions)
- Shell handles all I/O and state mutation
- Core is trivially testable without mocks

#### Evaluate Your Tests Against the Benefits You Want from Them

| Test Type | Speed | Correctness | Design Feedback | Integration Safety |
|---|---|---|---|---|
| Isolated unit tests | Fastest | Moderate | Excellent | None |
| Integrated unit tests | Fast | Good | Moderate | Good |
| Functional tests | Slowest | Excellent | Minimal | Excellent |

**Recommendation**: Use a balanced portfolio of all three, weighted by your project's needs.

---

## Appendices

---

### Appendix A: PythonAnywhere

- Cloud hosting for Django; browser-based console
- Use `xvfb-run` for headless Selenium tests: `xvfb-run python manage.py test`
- **Xvfb**: X Virtual Framebuffer — creates virtual display for GUI-less servers

---

### Appendix B: Django Class-Based Views

**Class-Based Generic Views (CBGVs)** — reduce boilerplate for common patterns:

```python
from django.views.generic import FormView, CreateView, DetailView

class HomePageView(FormView):
    template_name = 'home.html'
    form_class = ItemForm

class ViewAndAddToList(DetailView, CreateView):
    model = List
    template_name = 'list.html'
    form_class = ExistingListItemForm
```

- **`FormView`**: Display form on GET, validate on POST
- **`CreateView`**: Create object from form submission
- **`DetailView`**: Display single object
- Customize via method overrides: `form_valid()`, `get_form()`
- Trade-off: Less boilerplate, but complex inheritance can be harder to debug

---

### Appendix C: Provisioning with Ansible

**Key tool: Ansible** — YAML-based configuration management via SSH.

```yaml
# provision.ansible.yaml
- hosts: all
  vars:
    host: "{{ inventory_hostname }}"
  tasks:
    - name: add deadsnakes PPA
      apt_repository: repo='ppa:fkrull/deadsnakes'

    - name: install packages
      apt: pkg=nginx,git,python3.6,python3.6-venv state=present

    - name: add nginx config
      template: src=./nginx.conf.j2 dest=/etc/nginx/sites-available/{{ host }}
      notify: restart nginx

    - name: add gunicorn service
      template: src=./gunicorn.service.j2 dest=/etc/systemd/system/gunicorn-{{ host }}.service
      notify: restart gunicorn

  handlers:
    - name: restart nginx
      service: name=nginx state=restarted
    - name: restart gunicorn
      systemd: name=gunicorn-{{ host }} daemon_reload=yes state=restarted
```

```bash
ansible-playbook -i inventory.ansible provision.ansible.yaml --ask-become-pass
```

- **Playbooks**: Declarative YAML defining desired server state
- **Handlers**: Run only when notified (e.g., restart after config change)
- **Templates**: Jinja2 templating for config files

---

### Appendix D: Testing Database Migrations

- **Data migrations**: Modify database content, not just schema
- Test with real (sanitized) data from production
- Example: Deduplicate data before adding a `unique_together` constraint

```python
# Migration: deduplicate items
def find_dupes(apps, schema_editor):
    List = apps.get_model("lists", "List")
    for list_ in List.objects.all():
        texts = set()
        for ix, item in enumerate(list_.item_set.all()):
            if item.text in texts:
                item.text = f'{item.text} ({ix})'
                item.save()
            texts.add(item.text)

class Migration(migrations.Migration):
    operations = [migrations.RunPython(find_dupes)]
```

- Always test migrations against a staging database before production

---

### Appendix E: Behaviour-Driven Development (BDD)

**Key library: `behave`** — Python BDD framework using Gherkin syntax.

```gherkin
# features/my_lists.feature
Feature: My Lists
  As a logged-in user
  I want to see all my lists on one page

  Scenario: Create two lists and see them on the My Lists page
    Given I am a logged-in user
    When I create a list with first item "Reticulate Splines"
    And I add an item "Immanentize Eschaton"
    Then I will see a link to "My lists"
```

```python
# features/steps/my_lists.py
from behave import given, when, then

@given('I am a logged-in user')
def step_impl(context):
    create_pre_authenticated_session(context)

@when('I create a list with first item "{item_text}"')
def step_impl(context, item_text):
    context.browser.get(context.get_url('/'))
    context.browser.find_element_by_id('id_text').send_keys(item_text)
    context.browser.find_element_by_id('id_text').send_keys(Keys.ENTER)
```

- **Given/When/Then** maps to **Arrange/Act/Assert**
- Step functions are reusable across scenarios
- **Trade-off**: More structured than inline FTs, but adds an abstraction layer

**Also mentioned**: `behave-django` for Django integration, `Lettuce` (limited Python 3 support)

---

### Appendix F: Building a REST API: JSON, Ajax, and Mocking with JavaScript

```python
# lists/api.py
from django.http import HttpResponse
import json

def list(request, list_id):
    list_ = List.objects.get(id=list_id)
    item_dicts = [{'id': i.id, 'text': i.text} for i in list_.item_set.all()]
    return HttpResponse(json.dumps(item_dicts), content_type='application/json')
```

```python
# API unit test
def test_get_returns_json_200(self):
    list_ = List.objects.create()
    response = self.client.get(f'/api/lists/{list_.id}/')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response['content-type'], 'application/json')
```

- REST API enables frontend/backend separation
- Test API independently from UI with Django test client

---

### Appendix G: Django-Rest-Framework

**Key library: `djangorestframework` (DRF)** — toolkit for building Web APIs.

```bash
pip install djangorestframework
```

- Provides serializers, viewsets, routers, authentication
- Auto-generates browsable API
- Reduces boilerplate for CRUD API endpoints
- Integrates with Django's model/form validation

---

### Quick Reference: Key Libraries and Tools

| Library/Tool | Purpose | Import / Install |
|---|---|---|
| `unittest` | Python test framework (stdlib) | `import unittest` |
| `unittest.mock` | Mocking framework (stdlib) | `from unittest.mock import Mock, patch` |
| `django.test.TestCase` | Django unit test base class | `from django.test import TestCase` |
| `LiveServerTestCase` | FT base with live server | `from django.test import LiveServerTestCase` |
| `StaticLiveServerTestCase` | FT base with static files | `from django.contrib.staticfiles.testing import StaticLiveServerTestCase` |
| `selenium` | Browser automation | `pip install selenium` |
| `fabric` | SSH deployment automation | `pip install fabric3` |
| `gunicorn` | Production WSGI server | `pip install gunicorn` |
| `behave` | BDD framework (Gherkin) | `pip install behave` |
| `QUnit` | JavaScript test framework | Download JS file |
| `Jenkins` | CI server | `apt-get install jenkins` |
| `Ansible` | Server provisioning | `pip install ansible` |
| `djangorestframework` | REST API toolkit | `pip install djangorestframework` |

### Quick Reference: Key Django Test Assertions

```python
self.assertEqual(a, b)                    # a == b
self.assertIn(needle, haystack)           # needle in haystack
self.assertTrue(x) / assertFalse(x)      # bool check
self.assertContains(response, text)       # status 200 + text in response
self.assertTemplateUsed(response, name)   # verify template
self.assertRedirects(response, url)       # status 302 + location
self.assertRaises(ExceptionType)          # context manager for exceptions
self.assertRegex(text, pattern)           # regex match
self.assertAlmostEqual(a, b, delta=N)     # approximate equality
```

### Quick Reference: The TDD Cycle

```
1. Write a Functional Test (user story)        → RED
2. Write a Unit Test (specific behavior)        → RED
3. Write minimal code to pass Unit Test         → GREEN
4. Refactor (improve code, tests still pass)    → REFACTOR
5. Repeat 2-4 until Functional Test passes      → GREEN
6. Commit!
```
