# Book1 - Test-Driven Development with Python (2nd Edition)
## Obey the Testing Goat: Using Django, Selenium & JavaScript
### by Harry J.W. Percival (O'Reilly, 2017)

---

# Part I. The Basics of TDD and Django

---

## Chapter 1: Getting Django Set Up Using a Functional Test

### Obey the Testing Goat! Do Nothing Until You Have a Test

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

### Getting Django Up and Running

```bash
django-admin.py startproject superlists
cd superlists
python manage.py runserver
```

- Creates project scaffold: `manage.py`, `superlists/settings.py`, `superlists/urls.py`
- Dev server at `http://127.0.0.1:8000/`
- Running the FT against the dev server confirms Django's default "it worked!" page

### Starting a Git Repository

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

## Chapter 2: Extending Our Functional Test Using the unittest Module

### Using a Functional Test to Scope Out a Minimum Viable App

- FTs should read like a **user story** — comments describe what the user sees and does
- The to-do list app: users enter items, the app remembers them, each user gets a unique URL

### The Python Standard Library's unittest Module

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

## Chapter 3: Testing a Simple Home Page with Unit Tests

### Unit Tests, and How They Differ from Functional Tests

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

### Unit Testing in Django

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

### Django's MVC, URLs, and View Functions

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

### At Last! We Actually Write Some Application Code!

```bash
python manage.py startapp lists
```

Creates: `lists/models.py`, `lists/views.py`, `lists/tests.py`, `lists/admin.py`, `lists/migrations/`

### The Unit-Test/Code Cycle

1. Run test → see it fail (read the traceback)
2. Make smallest possible code change
3. Run test → see it pass (or get a new error)
4. Repeat

---

## Chapter 4: What Are We Doing with All These Tests? (And, Refactoring)

### Programming Is Like Pulling a Bucket of Water Up from a Well

- TDD is a **ratchet mechanism** — tests save your progress and prevent regression
- Each passing test is a notch in the ratchet

### Using Selenium to Test User Interactions

```python
from selenium.webdriver.common.keys import Keys

inputbox = self.browser.find_element_by_id('id_new_item')
inputbox.send_keys('Buy peacock feathers')
inputbox.send_keys(Keys.ENTER)
```

### The "Don't Test Constants" Rule, and Templates to the Rescue

- Don't test that HTML strings are exactly equal — test **behavior**, not constants
- Solution: move HTML to **templates** and test that the right template is used

#### Refactoring to Use a Template

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

#### The Django Test Client

```python
class HomePageTest(TestCase):
    def test_uses_home_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'home.html')
```

- **`self.client`**: Django's test client, simulates GET/POST without a real server
- **`assertTemplateUsed(response, name)`**: Checks which template rendered the response — much better than string comparison

### On Refactoring

- **Refactoring**: Changing code structure without changing behavior
- **Rule**: Only refactor when all tests pass
- **Rule**: Never change code and tests at the same time

### Recap: The TDD Process

```
FT fails → write unit test → UT fails → write minimal code →
UT passes → refactor → repeat until FT passes → commit
```

---

## Chapter 5: Saving User Input: Testing the Database

### Wiring Up Our Form to Send a POST Request

```html
<form method="POST">
  <input name="item_text" id="id_new_item" placeholder="Enter a to-do item" />
  {% csrf_token %}
</form>
```

- **`{% csrf_token %}`**: Django template tag — injects hidden CSRF protection token
- **CSRF (Cross-Site Request Forgery)**: Attack where malicious site triggers actions on your site

### Processing a POST Request on the Server

```python
def test_can_save_a_POST_request(self):
    response = self.client.post('/', data={'item_text': 'A new list item'})
    self.assertIn('A new list item', response.content.decode())
```

### Passing Python Variables to Be Rendered in the Template

```python
# View passes context to template
return render(request, 'home.html', {'new_item_text': request.POST.get('item_text', '')})
```

```html
<!-- Template uses {{ variable }} syntax -->
<td>{{ new_item_text }}</td>
```

### Three Strikes and Refactor

- When you see duplication three times, it's time to extract a helper

### The Django ORM and Our First Model

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

#### Our First Database Migration

```bash
python manage.py makemigrations   # Generate migration from model changes
python manage.py migrate          # Apply migrations to database
```

### Saving the POST to the Database

```python
def home_page(request):
    if request.method == 'POST':
        Item.objects.create(text=request.POST['item_text'])
        return redirect('/')
    items = Item.objects.all()
    return render(request, 'home.html', {'items': items})
```

### Redirect After a POST

- **Web best practice**: Always redirect after a successful POST to prevent duplicate submissions on refresh
- `return redirect('/')` sends HTTP 302

#### Better Unit Testing Practice: Each Test Should Test One Thing

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

### Rendering Items in the Template

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

## Chapter 6: Improving Functional Tests: Ensuring Isolation and Removing Voodoo Sleeps

### Ensuring Test Isolation in Functional Tests

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

#### Running Just the Unit Tests

```bash
python manage.py test lists                    # Unit tests only
python manage.py test functional_tests         # FTs only
```

### On Implicit and Explicit Waits, and Voodoo time.sleeps

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

## Chapter 7: Working Incrementally

### Small Design When Necessary

- **YAGNI** (You Ain't Gonna Need It): Only build what's needed to pass current tests
- **REST-ish URL design**: `/lists/<id>/` for viewing, `/lists/new` for creating, `/lists/<id>/add_item` for adding

### Implementing the New Design Incrementally Using TDD

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

### Ensuring We Have a Regression Test

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

### Taking a First, Self-Contained Step: One New URL

**Key Django assertion**:

```python
self.assertContains(response, 'itemey 1')
```

- `assertContains(response, text)` — checks status 200 AND text present in decoded content
- Cleaner than manual `.content.decode()` + `assertIn()`

### URL patterns with capture groups

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

# Part II. Web Development Sine Qua Nons

---

## Chapter 8: Prettification: Layout and Styling, and What to Test About It

### What to Functionally Test About Layout and Style

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

### Django Template Inheritance

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

### Static Files in Django

```python
# settings.py
STATIC_URL = '/static/'
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..', 'static'))
```

```bash
python manage.py collectstatic --noinput
```

#### Switching to StaticLiveServerTestCase

**Key library: `django.contrib.staticfiles.testing.StaticLiveServerTestCase`**

```python
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

class NewVisitorTest(StaticLiveServerTestCase):
    # Automatically serves static files during tests
    pass
```

- Replaces `LiveServerTestCase` — serves static files so CSS/JS load in FTs

---

## Chapter 9: Testing Deployment Using a Staging Site

### TDD and the Danger Areas of Deployment

- Danger areas: static files, database, dependencies
- **Solution**: Run FTs against a staging server before deploying to production

### As Always, Start with a Test

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

### Manually Provisioning a Server to Host Our Site

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

## Chapter 10: Getting to a Production-Ready Deployment

### Switching to Gunicorn

**Key tool: `gunicorn`** — Production WSGI HTTP server for Python.

```bash
pip install gunicorn
gunicorn --bind unix:/tmp/SITENAME.socket superlists.wsgi:application
```

### Switching to Using Unix Sockets

- Unix sockets (`/tmp/SITENAME.socket`) instead of TCP ports — more secure, no port collisions

### Switching DEBUG to False and Setting ALLOWED_HOSTS

```python
DEBUG = False
ALLOWED_HOSTS = ['superlists-staging.example.com']
```

### Using Systemd to Make Sure Gunicorn Starts on Boot

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

## Chapter 11: Automating Deployment with Fabric

**Key library: `fabric`** — Python tool for automating SSH commands on remote servers.

```bash
pip install fabric3
```

### Breakdown of a Fabric Script for Our Deployment

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

## Chapter 12: Splitting Our Tests into Multiple Files, and a Generic Wait Helper

### Skipping a Test

```python
from unittest import skip

@skip
def test_cannot_add_empty_list_items(self):
    self.fail('write me!')
```

- `@skip` temporarily disables a test — remove before committing

### Splitting Functional Tests Out into Many Files

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

### A New Functional Test Tool: A Generic Explicit Wait Helper

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

### Refactoring Unit Tests into Several Files

```
lists/tests/
    __init__.py
    test_models.py
    test_views.py
    test_forms.py
```

---

## Chapter 13: Validation at the Database Layer

### Model-Layer Validation

- Push validation **as low as possible** — database layer is the last line of defense

#### The self.assertRaises Context Manager

```python
from django.core.exceptions import ValidationError

def test_cannot_save_empty_list_items(self):
    list_ = List.objects.create()
    item = Item(list=list_, text='')
    with self.assertRaises(ValidationError):
        item.save()
        item.full_clean()  # Must call explicitly!
```

#### A Django Quirk: Model Save Doesn't Run Validation

- **`model.save()`** does NOT call validators on `TextField`
- **`model.full_clean()`** manually triggers all model validation
- This is a Django design choice — form-level validation is separate from save

### Surfacing Model Validation Errors in the View

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

### Django Pattern: Processing POST Requests in the Same View as Renders the Form

- Single view handles both GET (display form) and POST (process form)
- On validation error, re-render same template with error message

### Refactor: Removing Hardcoded URLs

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

## Chapter 14: A Simple Form

### Moving Validation Logic into a Form

**Key library: `django.forms`** — Django's form framework handles validation, rendering, and saving.

#### Exploring the Forms API with a Unit Test

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

#### Testing and Customising Form Validation

```python
def test_form_validation_for_blank_items(self):
    form = ItemForm(data={'text': ''})
    self.assertFalse(form.is_valid())
    self.assertEqual(form.errors['text'], [EMPTY_ITEM_ERROR])
```

- **`form.is_valid()`**: Returns `True`/`False`, populates `form.errors`
- **`form.errors`**: Dict mapping field names to lists of error strings

### Using the Form in Our Views

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

### Using the Form's Own Save Method

```python
class ItemForm(forms.models.ModelForm):
    # ...
    def save(self, for_list):
        self.instance.list = for_list
        return super().save()
```

### An Unexpected Benefit: Free Client-Side Validation from HTML5

- Django ModelForm adds `required` attribute to HTML inputs from `blank=False`
- Browsers prevent empty form submission automatically
- Still need server-side validation as a safety net

---

## Chapter 15: More Advanced Forms

### Preventing Duplicates at the Model Layer

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

### A More Complex Form to Handle Uniqueness Validation

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

### A Little Digression on Queryset Ordering and String Representations

```python
class Item(models.Model):
    def __str__(self):
        return self.text
```

- `__str__` makes debugging/assertions much more readable

---

## Chapter 16: Dipping Our Toes, Very Tentatively, into JavaScript

### Setting Up a Basic JavaScript Test Runner

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

### Using jQuery and the Fixtures Div

- **`$('#id')`**: jQuery selector
- **`.on('event', fn)`**: Attach event listener
- **`.is(':visible')`**: Check if element is displayed
- **`.hide()` / `.show()`**: Toggle visibility

### Building a JavaScript Unit Test for Our Desired Functionality

```javascript
// lists/static/list.js
$('#id_text').on('input', function () {
    $('.has-error').hide();
});
```

### JavaScript Testing in the TDD Cycle

- Write QUnit test → fails → implement JS → passes → refactor
- Same Red/Green/Refactor cycle as Python TDD

---

## Chapter 17: Deploying Our New Code

### Staging Deploy

```bash
cd deploy_tools
fab deploy:host=elspeth@superlists-staging.example.com
```

### Live Deploy

```bash
fab deploy:host=elspeth@superlists.example.com
sudo systemctl restart gunicorn-superlists.example.com
```

### Wrap-Up: git tag the New Release

```bash
git tag -f LIVE
git push -f origin LIVE
```

---

# Part III. More Advanced Topics in Testing

---

## Chapter 18: User Authentication, Spiking, and De-Spiking

### Passwordless Auth

- Token-based login: generate unique token, email login URL, user clicks link to authenticate
- No passwords to store or manage

### Exploratory Coding, aka "Spiking"

- **Spike**: Prototype code to explore an API or solution without TDD discipline
- Done on a **separate branch**: `git checkout -b passwordless-spike`
- Goal: learn how something works, then throw away the code

### De-spiking

- Rewrite the spike code using proper TDD
- Revert spike branch: `git checkout master`
- Write tests first, implement properly

### Custom Authentication Models

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

### Custom Authentication Backend

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

### Sending Emails from Django

```python
from django.core.mail import send_mail

send_mail(
    'Your login link for Superlists',
    f'Use this link to log in:\n\n{url}',
    'noreply@superlists',
    [email],
)
```

### Using Environment Variables to Avoid Secrets in Source Code

```python
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')
```

### A Minimal Custom User Model

- Minimal user model uses email as primary key
- Tests serve as documentation for model behavior

---

## Chapter 19: Using Mocks to Test External Dependencies or Reduce Duplication

### Mocking Manually, aka Monkeypatching

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

### The Python Mock Library

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

#### Using unittest.patch

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

#### Patching at the Class Level

```python
@patch('accounts.views.auth')
class LoginViewTest(TestCase):
    def test_redirects(self, mock_auth):
        ...
    def test_calls_authenticate(self, mock_auth):
        mock_auth.authenticate.return_value = None
        ...
```

### Using mock.return_value

```python
mock_auth.authenticate.return_value = mock_user
# Now when view calls auth.authenticate(...), it gets mock_user back
```

### Checking That We Send the User a Link with a Token

```python
@patch('accounts.views.send_mail')
def test_sends_link_to_login_using_token_uid(self, mock_send_mail):
    self.client.post('/accounts/send_login_email', data={'email': 'a@b.com'})
    token = Token.objects.first()
    expected_url = f'http://testserver/accounts/login?token={token.uid}'
    (subject, body, from_email, to_list), kwargs = mock_send_mail.call_args
    self.assertIn(expected_url, body)
```

### Testing the Django Messages Framework

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

## Chapter 20: Test Fixtures and a Decorator for Explicit Waits

### Skipping the Login Process by Pre-creating a Session

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

### Our Final Explicit Wait Helper: A Wait Decorator

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

## Chapter 21: Server-Side Debugging

### The Proof Is in the Pudding: Using Staging to Catch Final Bugs

- Run FTs against staging server to catch deployment-specific bugs
- Logging is essential for debugging production issues

#### Setting Up Logging

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

### Setting Secret Environment Variables on the Server

```bash
echo "EMAIL_PASSWORD=mysecret" >> ~/.env
# Source in Gunicorn systemd service via EnvironmentFile=
```

### Managing the Test Database on Staging

- Create sessions on the staging server for FTs using Django management commands
- Use `fabric` to run management commands remotely

---

## Chapter 22: Finishing "My Lists": Outside-In TDD

### The Alternative: "Inside-Out"

- **Inside-Out**: Build models first, then views, then templates
- Risk: building inner components more general than needed

### Why Prefer "Outside-In"?

- **Outside-In**: Start from templates/UI, work inward to views, then models
- Also called **"programming by wishful thinking"** — design the API you wish you had
- Each layer's tests inform the next layer's design

### The Outside Layer: Presentation and Templates

- Start with FT describing user-visible behavior
- FT failure reveals what the template needs

### Moving Down One Layer to View Functions (the Controller)

- Template needs data → view must provide it
- Write unit test for view → implement view

### Moving Down to the Model Layer

```python
class List(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)

    @property
    def name(self):
        return self.item_set.first().text
```

### The Outside-In Workflow

```
FT → Template needs X → View test → View needs Y from model →
Model test → Model implementation → View passes → FT passes
```

---

## Chapter 23: Test Isolation, and "Listening to Your Tests"

### A First Attempt at Using Mocks for Isolation

```python
from unittest.mock import patch, Mock

@patch('lists.views.NewListForm')
def test_passes_POST_data_to_NewListForm(self, mockNewListForm):
    self.client.post('/lists/new', data={'text': 'new item'})
    mockNewListForm.assert_called_once_with(data=self.request.POST)
```

#### Using Mock side_effects to Check the Sequence of Events

```python
def check_owner_assigned():
    self.assertEqual(mock_list.owner, user)

mock_list.save.side_effect = check_owner_assigned
```

- `side_effect` runs a function when the mock is called — verifies ordering

### Listen to Your Tests: Ugly Tests Signal a Need to Refactor

- Hard-to-write tests → code design needs improvement
- Solution: extract collaborators, hide ORM behind helper methods

### Rewriting Our Tests for the View to Be Fully Isolated

```python
@patch('lists.views.NewListForm')
def test_saves_form_with_owner_if_form_valid(self, mockNewListForm):
    mock_form = mockNewListForm.return_value
    mock_form.is_valid.return_value = True
    new_list(self.request)
    mock_form.save.assert_called_once_with(owner=self.request.user)
```

### Moving Down to the Forms Layer

```python
class NewListForm(ItemForm):
    def save(self, owner):
        if owner.is_authenticated:
            return List.create_new(first_item_text=self.cleaned_data['text'], owner=owner)
        else:
            return List.create_new(first_item_text=self.cleaned_data['text'])
```

### Moving Down to the Models Layer

```python
@staticmethod
def create_new(first_item_text, owner=None):
    list_ = List.objects.create(owner=owner)
    Item.objects.create(text=first_item_text, list=list_)
    return list_
```

### Thinking of Interactions Between Layers as "Contracts"

- **Implicit contract**: When you mock `form.save(owner=user)`, you're claiming the real form accepts `owner`
- Verify contracts with integration tests

### Conclusions: When to Write Isolated Versus Integrated Tests

- **Let complexity be your guide**: Simple code → integrated tests; complex code → isolated tests
- Keep a few integrated **sanity check** tests alongside isolated tests
- Use all three layers: FTs, integrated tests, isolated unit tests

---

## Chapter 24: Continuous Integration (CI)

### Installing Jenkins

**Key tool: Jenkins** — open-source CI server (Java-based).

```bash
wget -q -O - https://pkg.jenkins.io/debian-stable/jenkins.io.key | apt-key add -
apt-get install jenkins
```

### Configuring Jenkins

- Runs on port 8080
- **Key plugins**: ShiningPanda (Python/virtualenv), Xvfb (virtual display), Git

### Setting Up Our Project

- **Source Code Management**: Git repo URL
- **Build Triggers**: Poll SCM (`H/5 * * * *`)
- **Build Environment**: Start Xvfb before build (1024x768x24)

### Taking Screenshots

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

### If in Doubt, Try Bumping the Timeout

```python
MAX_WAIT = 20  # or even 30 for CI environments
```

- CI servers are often under heavier load — increase timeouts generously

### Running Our QUnit JavaScript Tests in Jenkins with PhantomJS

**Key tool: PhantomJS** — headless browser for JavaScript testing (deprecated, prefer Xvfb+Firefox).

```bash
npm install -g phantomjs
phantomjs runner.js tests.html
```

---

## Chapter 25: The Token Social Bit, the Page Pattern, and an Exercise for the Reader

### The Page Pattern

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

### An FT with Multiple Users, and addCleanup

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

## Chapter 26: Fast Tests, Slow Tests, and Hot Lava

### Thesis: Unit Tests Are Superfast and Good Besides That

- **Fast feedback** keeps you in flow state
- Unit tests drive better design by forcing decoupled code
- Run in milliseconds vs. minutes for FTs

### The Problems with "Pure" Unit Tests

- **Isolated tests can be harder to read** — mock setup obscures intent
- **Isolated tests don't automatically test integration** — mocks can lie
- **Unit tests seldom catch unexpected bugs** — they test what you expect
- **Mocky tests become tightly coupled to implementation** — refactoring breaks tests

### Synthesis: What Do We Want from Our Tests, Anyway?

Three goals:
1. **Correctness**: Does the code work?
2. **Clean, Maintainable Code**: Is the design good?
3. **Productive Workflow**: Is the feedback loop fast enough?

### Architectural Solutions

#### Ports and Adapters / Hexagonal / Clean Architecture

- Identify **boundaries** (DB, UI, network, email)
- **Core logic**: Pure Python, no side effects, easy to unit test
- **Adapters**: Handle boundary interactions, tested with integration tests

#### Functional Core, Imperative Shell

- Core follows **functional programming** (no side effects, pure functions)
- Shell handles all I/O and state mutation
- Core is trivially testable without mocks

### Evaluate Your Tests Against the Benefits You Want from Them

| Test Type | Speed | Correctness | Design Feedback | Integration Safety |
|---|---|---|---|---|
| Isolated unit tests | Fastest | Moderate | Excellent | None |
| Integrated unit tests | Fast | Good | Moderate | Good |
| Functional tests | Slowest | Excellent | Minimal | Excellent |

**Recommendation**: Use a balanced portfolio of all three, weighted by your project's needs.

---

# Appendices

---

## Appendix A: PythonAnywhere

- Cloud hosting for Django; browser-based console
- Use `xvfb-run` for headless Selenium tests: `xvfb-run python manage.py test`
- **Xvfb**: X Virtual Framebuffer — creates virtual display for GUI-less servers

---

## Appendix B: Django Class-Based Views

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

## Appendix C: Provisioning with Ansible

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

## Appendix D: Testing Database Migrations

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

## Appendix E: Behaviour-Driven Development (BDD)

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

## Appendix F: Building a REST API: JSON, Ajax, and Mocking with JavaScript

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

## Appendix G: Django-Rest-Framework

**Key library: `djangorestframework` (DRF)** — toolkit for building Web APIs.

```bash
pip install djangorestframework
```

- Provides serializers, viewsets, routers, authentication
- Auto-generates browsable API
- Reduces boilerplate for CRUD API endpoints
- Integrates with Django's model/form validation

---

## Quick Reference: Key Libraries and Tools

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

## Quick Reference: Key Django Test Assertions

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

## Quick Reference: The TDD Cycle

```
1. Write a Functional Test (user story)        → RED
2. Write a Unit Test (specific behavior)        → RED
3. Write minimal code to pass Unit Test         → GREEN
4. Refactor (improve code, tests still pass)    → REFACTOR
5. Repeat 2-4 until Functional Test passes      → GREEN
6. Commit!
```

# Book2 - Python Testing with pytest, Second Edition — Summary

> **Author:** Brian Okken | **Publisher:** Pragmatic Bookshelf (Feb 2022)
> **Sample App:** "Cards" — a CLI task tracker built with **Typer** (CLI), **Rich** (formatting), and **TinyDB** (database)

---

## Part I — Primary Power

### 1. Getting Started with pytest

#### Installing pytest
```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate.bat
pip install pytest
```

#### Running pytest
- `pytest` — searches current dir + subdirs for tests
- `pytest test_file.py` — run one file
- `pytest test_file.py::test_func` — run one test
- `pytest dir/` — run a directory
- `-v` / `--verbose` — show individual test names and PASSED/FAILED
- `--tb=no` — suppress tracebacks

#### Test Discovery
- Files named `test_*.py` or `*_test.py`
- Functions/methods named `test_*`
- Classes named `Test*`

#### Test Outcomes
| Symbol | Meaning |
|--------|---------|
| `.` / PASSED | Test succeeded |
| `F` / FAILED | Assertion or uncaught exception in test |
| `s` / SKIPPED | Test skipped via `@pytest.mark.skip` or `skipif` |
| `x` / XFAIL | Expected failure, and it did fail |
| `X` / XPASS | Expected failure, but it passed |
| `E` / ERROR | Exception in a fixture or hook, not the test itself |

---

### 2. Writing Test Functions

#### Installing the Sample Application
- Cards is an installable Python package: `pip install ./cards_proj/`
- **Application code** = code under test (CUT/SUT/DUT)
- **Test code** = code that validates the application

#### Writing Knowledge-Building Tests
- Quick tests to verify understanding of data structures / APIs
- Cards uses a Python **dataclass** (`Card`) with `summary`, `owner`, `state`, `id`
  - `compare=False` on `id` means equality ignores `id`
  - Convenience methods: `Card.from_dict(d)`, `card.to_dict()`

#### Using assert Statements
- pytest uses plain `assert` — no `assertEqual`, `assertTrue`, etc.
- **Assert rewriting**: pytest intercepts `assert` to provide rich failure diffs
- `-vv` shows full diff details (matching vs differing attributes, caret markers)

#### Failing with pytest.fail() and Exceptions
- Any uncaught exception fails a test
- `pytest.fail("message")` explicitly fails with a message
- Use `assert` by default; reserve `pytest.fail()` for assertion helpers

#### Writing Assertion Helper Functions
```python
def assert_identical(c1: Card, c2: Card):
    __tracebackhide__ = True        # hide this frame from traceback
    assert c1 == c2
    if c1.id != c2.id:
        pytest.fail(f"id's don't match. {c1.id} != {c2.id}")
```

#### Testing for Expected Exceptions
```python
# Check exception type
with pytest.raises(TypeError):
    cards.CardsDB()

# Check exception message with regex
with pytest.raises(TypeError, match="missing 1 .* positional argument"):
    cards.CardsDB()

# Inspect the exception object
with pytest.raises(TypeError) as exc_info:
    cards.CardsDB()
assert "missing 1 required" in str(exc_info.value)
```
- `exc_info` is of type `ExceptionInfo`

#### Structuring Test Functions
- **Arrange-Act-Assert** (Bill Wake) / **Given-When-Then** (BDD, Dan North)
  - **Given/Arrange** — set up data/state
  - **When/Act** — perform the action under test
  - **Then/Assert** — verify the outcome
- Avoid interleaved assert patterns (`Arrange-Assert-Act-Assert-...`); keep assertions at the end

#### Grouping Tests with Classes
```python
class TestEquality:
    def test_equality(self):
        ...
    def test_inequality(self):
        ...
```
- Run a class: `pytest test_file.py::TestEquality`
- Run a method: `pytest test_file.py::TestEquality::test_equality`
- Use classes primarily for grouping; avoid complex inheritance

#### Running a Subset of Tests
| Subset | Syntax |
|--------|--------|
| Single function | `pytest path/test_mod.py::test_func` |
| Single class | `pytest path/test_mod.py::TestClass` |
| Single method | `pytest path/test_mod.py::TestClass::test_method` |
| Single module | `pytest path/test_mod.py` |
| Directory | `pytest path/` |
| Keyword pattern | `pytest -k "pattern"` |

- `-k` supports `and`, `or`, `not`, and parentheses:
  ```bash
  pytest -k "(dict or ids) and not TestEquality"
  ```

---

### 3. pytest Fixtures

#### Getting Started with Fixtures
```python
@pytest.fixture()
def some_data():
    return 42

def test_some_data(some_data):    # pytest injects by name
    assert some_data == 42
```
- **Fixture**: a `@pytest.fixture()` decorated function run by pytest before (and sometimes after) tests
- Exception in a fixture → test reports **Error**, not Fail

#### Using Fixtures for Setup and Teardown
```python
@pytest.fixture()
def cards_db():
    with TemporaryDirectory() as db_dir:
        db = cards.CardsDB(Path(db_dir))
        yield db          # test runs here
        db.close()        # teardown — guaranteed to run
```
- Code **before** `yield` = setup; code **after** `yield` = teardown
- Teardown runs regardless of test pass/fail

#### Tracing Fixture Execution with --setup-show
```bash
pytest --setup-show test_count.py
```
- Shows `SETUP` / `TEARDOWN` around each test, with scope letter (`F`=function, `M`=module, `S`=session)

#### Specifying Fixture Scope
| Scope | Runs once per... |
|-------|-----------------|
| `function` (default) | each test function |
| `class` | each test class |
| `module` | each test module (.py file) |
| `package` | each test directory |
| `session` | entire test session |

```python
@pytest.fixture(scope="session")
def db():
    ...
```
- Scope is defined at the fixture, not where it's used
- Fixtures can only depend on fixtures of **equal or wider** scope

#### Sharing Fixtures through conftest.py
- Place fixtures in `conftest.py` to share across multiple test files
- pytest reads `conftest.py` automatically — **never import it**
- Can have `conftest.py` at any directory level

#### Finding Where Fixtures Are Defined
- `pytest --fixtures` — list all available fixtures with source locations
- `pytest --fixtures-per-test test_file.py::test_name` — fixtures used by a specific test

#### Using Multiple Fixture Levels
- Use a session-scoped DB fixture + a function-scoped fixture that calls `delete_all()`
- Gives you one DB connection but clean state per test

#### Using Multiple Fixtures per Test or Fixture
- Tests and fixtures can depend on multiple fixtures in their parameter lists

#### Deciding Fixture Scope Dynamically
```python
def db_scope(fixture_name, config):
    if config.getoption("--func-db", None):
        return "function"
    return "session"

@pytest.fixture(scope=db_scope)
def db():
    ...
```
- Pass a callable to `scope=` for runtime decisions

#### Using autouse for Fixtures That Always Get Used
```python
@pytest.fixture(autouse=True, scope="session")
def footer_session_scope():
    yield
    print(f"finished: {time.strftime(...)}")
```
- Runs for every test in scope without being named in the test's parameter list
- Use sparingly

#### Renaming Fixtures
```python
@pytest.fixture(name="app")
def _app():
    yield app()
```

---

### 4. Builtin Fixtures

#### Using tmp_path and tmp_path_factory
- **`tmp_path`** (function scope) — returns a `pathlib.Path` to a temp directory
- **`tmp_path_factory`** (session scope) — call `.mktemp("name")` to get temp dirs
- `--basetemp=mydir` to override the base temp directory
- Legacy equivalents: `tmpdir` / `tmpdir_factory` (return `py.path.local`)

#### Using capsys
```python
def test_version(capsys):
    cards.cli.version()
    output = capsys.readouterr().out.rstrip()
    assert output == cards.__version__
```
- `.readouterr()` returns a namedtuple with `.out` and `.err`
- `capsys.disabled()` context manager temporarily turns off capture
- `-s` / `--capture=no` flag disables capture globally
- Variants: `capfd`, `capsysbinary`, `capfdbinary`, `caplog`

#### Using monkeypatch
- **Monkeypatch**: dynamic modification of code/environment during a test, automatically undone after
- Methods:
  - `setattr(target, name, value)` / `delattr(target, name)`
  - `setitem(dic, name, value)` / `delitem(dic, name)`
  - `setenv(name, value)` / `delenv(name)`
  - `syspath_prepend(path)`
  - `chdir(path)`

```python
def test_patch_env_var(monkeypatch, tmp_path):
    monkeypatch.setenv("CARDS_DB_DIR", str(tmp_path))
    assert run_cards("config") == str(tmp_path)
```

#### Remaining Builtin Fixtures
- `cache` — persist values across pytest runs (enables `--last-failed`, `--failed-first`)
- `pytestconfig` — access config values and plugin hooks
- `request` — info on executing test; used in fixture parametrization
- `recwarn` — test warning messages
- `pytester` / `testdir` — for testing pytest plugins
- `record_property` / `record_testsuite_property` — add metadata to XML reports

---

### 5. Parametrization

#### Testing Without Parametrize
- Writing separate functions for each test case is redundant
- Combining into a loop loses individual reporting and stops at first failure

#### Parametrizing Functions
```python
@pytest.mark.parametrize("start_state", ["done", "in prog", "todo"])
def test_finish(cards_db, start_state):
    c = Card("write a book", state=start_state)
    ...
```
- First arg: comma-separated string or list of param names
- Second arg: list of values (or tuples for multiple params)
- Each value becomes a separate test case

#### Parametrizing Fixtures
```python
@pytest.fixture(params=["done", "in prog", "todo"])
def start_state(request):
    return request.param

def test_finish(cards_db, start_state):
    ...
```
- Useful when setup/teardown must run per parameter value
- All tests using the fixture get parametrized

#### Parametrizing with pytest_generate_tests
```python
def pytest_generate_tests(metafunc):
    if "start_state" in metafunc.fixturenames:
        metafunc.parametrize("start_state", ["done", "in prog", "todo"])
```
- Hook function called during test collection
- Most powerful: can use command-line flags, combine parameters dynamically

#### Using Keywords to Select Test Cases
```bash
pytest -k "todo and not (play or create)"
```
- Works on parametrized test IDs (the bracket portion)
- Quote expressions with spaces/brackets for shell safety

---

### 6. Markers

#### Using Builtin Markers
- `@pytest.mark.skip(reason=None)` — unconditional skip
- `@pytest.mark.skipif(condition, *, reason)` — conditional skip
- `@pytest.mark.xfail(condition, *, reason, run=True, raises=None, strict=False)` — expected failure
- `@pytest.mark.parametrize(...)` — covered in Ch5
- `@pytest.mark.usefixtures(...)` — apply fixtures to tests
- `@pytest.mark.filterwarnings(warning)` — add warning filter

#### Skipping Tests with pytest.mark.skip
```python
@pytest.mark.skip(reason="Feature not implemented yet")
def test_less_than():
    ...
```
- `-ra` flag shows reasons for all non-passing tests

#### Skipping Tests Conditionally with pytest.mark.skipif
```python
@pytest.mark.skipif(
    parse(cards.__version__).major < 2,
    reason="Not supported in 1.x",
)
```
- Uses **`packaging`** library (`pip install packaging`) for version parsing

#### Expecting Tests to Fail with pytest.mark.xfail
- `strict=False` (default): passing xfail → XPASS (not a failure)
- `strict=True`: passing xfail → FAILED
- Recommendation: set `xfail_strict = true` in `pytest.ini`

#### Selecting Tests with Custom Markers
```python
@pytest.mark.smoke
def test_start(cards_db):
    ...
```
- Register markers in `pytest.ini` to avoid typo warnings:
  ```ini
  [pytest]
  markers =
      smoke: subset of tests
      exception: check for expected exceptions
  ```
- Select: `pytest -m smoke`

#### Marking Files, Classes, and Parameters
- **File-level**: `pytestmark = pytest.mark.finish` (or a list)
- **Class-level**: `@pytest.mark.smoke` on the class
- **Parameter-level**: `pytest.param("in prog", marks=pytest.mark.smoke)`

#### Using "and," "or," "not," and Parentheses with Markers
```bash
pytest -m "(exception or smoke) and (not finish)"
```
- Can combine `-m` and `-k` flags

#### Being Strict with Markers
- `--strict-markers` turns unknown marker warnings into errors
- Add to `addopts` in `pytest.ini` for always-on behavior

#### Combining Markers with Fixtures
```python
@pytest.mark.num_cards(3)
def test_three_cards(cards_db):
    assert cards_db.count() == 3
```
- In the fixture, use `request.node.get_closest_marker("num_cards")` to read the marker
- Access args via `marker.args` and `marker.kwargs`
- **Faker** library (`pip install Faker`): provides a `faker` fixture for generating fake data
  - `faker.sentence()`, `faker.first_name()`, `faker.seed_instance(101)`

#### Listing Markers
```bash
pytest --markers
```

---

## Part II — Working with Projects

### 7. Strategy

#### Determining Test Scope
- Consider: security, performance, load testing, input validation
- Start with user-visible functionality testing; defer other concerns until needed

#### Considering Software Architecture
- Cards has 3 layers: **CLI** (cli.py) → **API** (api.py) → **DB** (db.py)
- CLI and DB layers intentionally thin; most logic in API
- Strategy: test features through the API; test CLI just enough to verify it calls the API correctly

#### Evaluating the Features to Test
- Prioritize by: **Recent**, **Core**, **Risk**, **Problematic**, **Expertise**
- Core features get thorough testing; non-core get at least one test case

#### Creating Test Cases
- Start with a non-trivial **happy path** test case
- Then consider: interesting inputs, interesting starting states, interesting end states, error states
- Example for `count`: empty DB, one item, more than one item
- Example for `delete`: delete one of many, delete the last card, delete non-existent

#### Writing a Test Strategy
- Document the strategy so you and your team can refer to it later
- Cards strategy summary:
  1. Test user-visible features through the API
  2. Test CLI just enough to verify API integration
  3. Test core features thoroughly (`add`, `count`, `delete`, `finish`, `list`, `start`, `update`)
  4. Cursory tests for `config` and `version`

---

### 8. Configuration Files

#### Understanding pytest Configuration Files
| File | Purpose |
|------|---------|
| `pytest.ini` | Primary config; its location defines **rootdir** |
| `conftest.py` | Fixtures and hook functions; can exist at any level |
| `__init__.py` | Prevents test filename collisions across subdirectories |
| `tox.ini` | tox config; can include a `[pytest]` section |
| `pyproject.toml` | Modern Python packaging; uses `[tool.pytest.ini_options]` |
| `setup.cfg` | Legacy packaging; uses `[tool:pytest]` |

#### Saving Settings and Flags in pytest.ini
```ini
[pytest]
addopts =
    --strict-markers
    --strict-config
    -ra
testpaths = tests
markers =
    smoke: subset of tests
```
- `--strict-config` raises errors for config file parsing issues

#### Using tox.ini, pyproject.toml, or setup.cfg in place of pytest.ini
- **tox.ini**: identical `[pytest]` section syntax
- **pyproject.toml**: `[tool.pytest.ini_options]`; values are quoted strings or lists
- **setup.cfg**: `[tool:pytest]` section; beware parser differences

#### Determining a Root Directory and Config File
- pytest searches upward from test path for a config file → that directory becomes **rootdir**
- Tip: always place at least an empty `pytest.ini` at the project root

#### Sharing Local Fixtures and Hook Functions with conftest.py
- Anything in `conftest.py` applies to tests in that directory and below
- Try to stick to one `conftest.py` for easy fixture discovery

#### Avoiding Test File Name Collision
- `__init__.py` in test subdirs allows duplicate filenames like `tests/api/test_add.py` and `tests/cli/test_add.py`
- Without it: `import file mismatch` error

---

### 9. Coverage

> **Key libraries:** **coverage.py** (`pip install coverage`) and **pytest-cov** (`pip install pytest-cov`)

#### Using coverage.py with pytest-cov
```bash
pytest --cov=cards ch7                          # basic report
pytest --cov=cards --cov-report=term-missing ch7  # show missed lines
```
- Equivalent without pytest-cov:
  ```bash
  coverage run --source=cards -m pytest ch7
  coverage report --show-missing
  ```
- `.coveragerc` config maps installed package paths to local source:
  ```ini
  [paths]
  source =
      cards_proj/src/cards
      */site-packages/cards
  ```

#### Generating HTML Reports
```bash
pytest --cov=cards --cov-report=html ch7
# or
coverage html
```
- Output: `htmlcov/index.html` — color-coded line-by-line coverage

#### Excluding Code from Coverage
```python
if __name__ == '__main__':  # pragma: no cover
    main()
```
- `# pragma: no cover` excludes a line or block

#### Running Coverage on Tests
```bash
pytest --cov=cards --cov=ch7 ch7
```
- Catches duplicate test function names (only last one in a file runs)
- Catches unused fixtures / dead code in fixtures

#### Running Coverage on a Directory
```bash
pytest --cov=ch9/some_code ch9/some_code
```

#### Running Coverage on a Single File
```bash
pytest --cov=single_file single_file.py   # no .py in --cov
```

---

### 10. Mocking

> **Key library:** `unittest.mock` (stdlib since Python 3.3)

#### Isolating the Command-Line Interface
- Cards CLI accesses: `cards.__version__`, `cards.CardsDB`, `cards.InvalidCardId`, `cards.Card`
- **Typer** provides `CliRunner` for in-process CLI testing:
  ```python
  from typer.testing import CliRunner
  runner = CliRunner()
  result = runner.invoke(cards.app, ["version"])
  ```

#### Testing with Typer
```python
import shlex
def cards_cli(command_string):
    result = runner.invoke(cards.app, shlex.split(command_string))
    return result.stdout.rstrip()
```

#### Mocking an Attribute
```python
from unittest import mock

def test_mock_version():
    with mock.patch.object(cards, "__version__", "1.2.3"):
        result = runner.invoke(app, ["version"])
        assert result.stdout.rstrip() == "1.2.3"
```

#### Mocking a Class and Methods
```python
with mock.patch.object(cards, "CardsDB") as MockCardsDB:
    MockCardsDB.return_value.path.return_value = "/foo/"
```
- Calling a mock returns `mock.return_value` (another mock)
- Set `.return_value` on chained mocks for method calls

#### Keeping Mock and Implementation in Sync with Autospec
```python
with mock.patch.object(cards, "CardsDB", autospec=True) as CardsDB:
    ...
```
- **Always use `autospec=True`** — prevents mock drift (misspelled methods, wrong params)
- Without it, mocks silently accept any attribute or call

#### Making Sure Functions Are Called Correctly
```python
def test_add_with_owner(mock_cardsdb):
    cards_cli("add some task -o brian")
    expected = cards.Card("some task", owner="brian", state="todo")
    mock_cardsdb.add_card.assert_called_with(expected)
```
- Variants: `assert_called()`, `assert_called_once()`, `assert_called_once_with(...)`, `assert_not_called()`

#### Creating Error Conditions
```python
mock_cardsdb.delete_card.side_effect = cards.api.InvalidCardId
out = cards_cli("delete 25")
assert "Error: Invalid card id 25" in out
```

#### Testing at Multiple Layers to Avoid Mocking
- Alternative: call CLI, then use the real API to verify state
- Tests **behavior** instead of implementation → more resilient to refactoring
- **Change detector tests**: tests that break during valid refactoring (avoid these)

#### Using Plugins to Assist Mocking
- **pytest-mock**: provides a `mocker` fixture (thin wrapper around `unittest.mock`)
- Domain-specific: `pytest-postgresql`, `pytest-mongo`, `pytest-httpserver`, `responses`, `betamax`

---

### 11. tox and Continuous Integration

#### What Is Continuous Integration?
- Automated build + test triggered on code changes
- Allows frequent integration, reducing merge conflicts

#### Introducing tox
> **tox** (`pip install tox`): local CI automation tool

- For each environment: creates venv → installs deps → builds package → installs package → runs tests

#### Setting Up tox
```ini
[tox]
envlist = py310
isolated_build = True       # required for pyproject.toml-based packages

[testenv]
deps =
    pytest
    faker
commands = pytest
```

#### Running tox
```bash
tox                         # run all environments
tox -e py310                # run one environment
tox -p                      # run environments in parallel
```

#### Testing Multiple Python Versions
```ini
envlist = py37, py38, py39, py310
skip_missing_interpreters = True
```

#### Adding a Coverage Report to tox
- Add `pytest-cov` to `deps`, change commands to `pytest --cov=cards`
- Use `.coveragerc` with `[paths]` to unify source paths

#### Specifying a Minimum Coverage Level
```ini
commands = pytest --cov=cards --cov=tests --cov-fail-under=100
```

#### Passing pytest Parameters Through tox
```ini
commands = pytest --cov=cards {posargs}
```
```bash
tox -e py310 -- -k test_version --no-cov
```
- `--` separates tox args from pytest args

#### Running tox with GitHub Actions
```yaml
# .github/workflows/main.yml
name: CI
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python: ["3.7", "3.8", "3.9", "3.10"]
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: ${{ matrix.python }}
      - run: pip install tox
      - run: tox -e py
```
- CI alternatives: GitLab CI, Bitbucket Pipelines, CircleCI, Jenkins

---

### 12. Testing Scripts and Applications

#### Testing a Simple Python Script
```python
from subprocess import run
def test_hello():
    result = run(["python", "hello.py"], capture_output=True, text=True)
    assert result.stdout == "Hello, World!\n"
```
- For tox with non-packaged code: set `skipsdist = true`

#### Testing an Importable Python Script
- Wrap logic in `main()`, guard with `if __name__ == "__main__": main()`
- Now tests can `import hello` and call `hello.main()` with `capsys`

#### Separating Code into src and tests Directories
```ini
# pytest.ini
[pytest]
pythonpath = src
testpaths = tests
```
- `pythonpath` (pytest 7+) adds directories to `sys.path` during test collection
- For pytest 6.2: use the **pytest-srcpaths** plugin

#### Defining the Python Search Path
- `sys.path` = list of directories Python searches during import
- pytest adds test directories automatically; `pythonpath` adds source directories

#### Testing requirements.txt-Based Applications
- In `tox.ini`, add `-rrequirements.txt` to `deps` to install dependencies

---

### 13. Debugging Test Failures

#### Installing Cards in Editable Mode
```bash
pip install -e "./cards_proj/[test]"   # editable + optional test deps
```

#### Debugging with pytest Flags

**Test selection/ordering:**
- `--lf` / `--last-failed` — rerun only failures
- `--ff` / `--failed-first` — run all, failures first
- `-x` / `--exitfirst` — stop after first failure
- `--maxfail=num` — stop after N failures
- `--sw` / `--stepwise` — stop at first failure; resume from there next time
- `--nf` / `--new-first` — order by file modification time

**Output control:**
- `-v` / `--verbose`
- `--tb=[auto/long/short/line/native/no]`
- `-l` / `--showlocals` — display local variables in tracebacks

**Debugger:**
- `--pdb` — drop into pdb at point of failure
- `--trace` — drop into pdb at start of each test
- `--pdbcls=IPython.terminal.debugger:TerminalPdb` — use IPython debugger

#### Re-Running Failed Tests
```bash
pytest --lf --tb=no          # verify failures reproduce
pytest --lf -x               # stop at first, show traceback
pytest --lf -x -l --tb=short # also show local variables
```

#### Debugging with pdb
- `breakpoint()` in code → pytest stops there
- **pdb commands:**
  - `l(ist)` / `ll` — show source; `w(here)` — stack trace
  - `p expr` / `pp expr` — print/pretty-print
  - `n(ext)` — next line; `s(tep)` — step into; `r(eturn)` — continue to return
  - `c(ontinue)` — run to next breakpoint; `unt(il) lineno` — run to line
  - `q(uit)` — exit

#### Combining pdb and tox
```bash
tox -e py310 -- --pdb --no-cov
```

---

## Part III — Booster Rockets

### 14. Third-Party Plugins

#### Finding Plugins
- https://docs.pytest.org/en/latest/reference/plugin_list.html
- https://pypi.org — search for `pytest-`
- https://github.com/pytest-dev

#### Installing Plugins
```bash
pip install pytest-cov     # or any plugin
```

#### Exploring the Diversity of pytest Plugins

**Test flow:**
- **pytest-order** — specify run order via marker
- **pytest-randomly** — randomize order (also seeds Faker/Factory Boy)
- **pytest-repeat** — repeat tests N times (`--count=10`)
- **pytest-rerunfailures** — rerun flaky tests
- **pytest-xdist** — parallel execution (`-n=auto`)

**Output:**
- **pytest-instafail** — show failures immediately
- **pytest-sugar** — green checkmarks + progress bar
- **pytest-html** — HTML test reports

**Web:**
- **pytest-selenium**, **pytest-splinter** — browser testing
- **pytest-django**, **pytest-flask** — framework integration

**Fake data:**
- **Faker** — general fake data
- **model-bakery** — Django model objects
- **pytest-factoryboy** — Factory Boy fixtures
- **pytest-mimesis** — faster alternative to Faker

**Misc:**
- **pytest-cov** — coverage
- **pytest-benchmark** — timing benchmarks
- **pytest-timeout** — enforce time limits
- **pytest-asyncio** — async tests
- **pytest-bdd** — BDD-style tests
- **pytest-freezegun** — freeze time
- **pytest-mock** — thin `unittest.mock` wrapper

#### Running Tests in Parallel
```bash
pip install pytest-xdist
pytest -n=auto              # use all CPU cores
pytest --looponfail         # watch mode: rerun failures on file changes
```

#### Randomizing Test Order
```bash
pip install pytest-randomly
pytest -v                   # order is now randomized
pytest -p no:randomly       # disable temporarily
```

---

### 15. Building Plugins

#### Starting with a Cool Idea
- Example: skip `@pytest.mark.slow` tests by default; include with `--slow` flag
- Default behavior change: no flag = exclude slow; `--slow` = include all

#### Building a Local conftest Plugin
Three **hook functions** used:
```python
# 1. Declare the marker
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")

# 2. Add --slow CLI flag
def pytest_addoption(parser):
    parser.addoption("--slow", action="store_true", help="include tests marked slow")

# 3. Skip slow tests unless --slow is passed
def pytest_collection_modifyitems(config, items):
    if not config.getoption("--slow"):
        skip_slow = pytest.mark.skip(reason="need --slow option to run")
        for item in items:
            if item.get_closest_marker("slow"):
                item.add_marker(skip_slow)
```

#### Creating an Installable Plugin
- Move conftest code into `pytest_skip_slow.py`
- Use **Flit** (`pip install flit`) to scaffold `pyproject.toml` with `flit init`
- Key `pyproject.toml` additions:
  - `[project.entry-points.pytest11]` with `skip_slow = "pytest_skip_slow"`
  - Classifier: `"Framework :: Pytest"`
- Build: `flit build` → creates `.whl` in `dist/`
- Install: `pip install dist/pytest_skip_slow-0.0.1-py3-none-any.whl`

#### Testing Plugins with pytester
```python
# tests/conftest.py
pytest_plugins = ["pytester"]

# tests/test_plugin.py
@pytest.fixture()
def examples(pytester):
    pytester.copy_example("examples/test_slow.py")

def test_skip_slow(pytester, examples):
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(["*test_slow SKIPPED*"])
    result.assert_outcomes(passed=1, skipped=1)
```
- **pytester** fixture: creates temp dir, provides `runpytest()`, `copy_example()`, `makepyfile()`, etc.
- `fnmatch_lines()` — glob-style matching on stdout lines
- `assert_outcomes()` — check pass/fail/skip counts
- `parseoutcomes()` — returns dict for manual assertions

#### Testing Multiple Python and pytest Versions with tox
```ini
[tox]
envlist = py{37,38,39,310}-pytest{62,70}

[testenv]
deps =
    pytest62: pytest==6.2.5
    pytest70: pytest==7.0.0
commands = pytest {posargs:tests}
```
- Curly braces + dashes create a matrix of environments

#### Publishing Plugins
- Git repository: `pip install git+https://github.com/user/repo`
- Shared directory: `pip install pkg --no-index --find-links=path/`
- PyPI: see Python packaging docs and Flit upload docs

---

### 16. Advanced Parametrization

#### Using Complex Values
```python
@pytest.mark.parametrize("starting_card", [
    Card("foo", state="todo"),
    Card("foo", state="in prog"),
    Card("foo", state="done"),
])
def test_card(cards_db, starting_card):
    ...
```
- Object values get numbered IDs by default (`starting_card0`, `starting_card1`, ...)

#### Creating Custom Identifiers

**`ids` as a function:**
```python
@pytest.mark.parametrize("starting_card", card_list, ids=lambda c: c.state)
```

**`ids` as a list:**
```python
@pytest.mark.parametrize("starting_card", card_list, ids=["todo", "in prog", "done"])
```

**`pytest.param` with explicit `id`:**
```python
pytest.param(Card("foo", state="in prog"), id="special")
```

**Dictionary technique** (keeps IDs and values together):
```python
text_variants = {"Short": "x", "With Spaces": "x y z", ...}
@pytest.mark.parametrize(
    "variant", text_variants.values(), ids=text_variants.keys()
)
```

#### Parametrizing with Dynamic Values
```python
def text_variants():
    variants = {"Short": "x", "With Spaces": "x y z", ...}
    for key, value in variants.items():
        yield pytest.param(value, id=key)

@pytest.mark.parametrize("variant", text_variants())
def test_summary(cards_db, variant):
    ...
```
- Generator function can read from files, databases, APIs, etc.

#### Using Multiple Parameters
**Explicit tuples:**
```python
@pytest.mark.parametrize("summary, owner, state", [
    ("short", "First", "todo"),
    ("short", "First", "in prog"),
])
```

**Stacking decorators** (creates a matrix):
```python
@pytest.mark.parametrize("state", states)
@pytest.mark.parametrize("owner", owners)
@pytest.mark.parametrize("summary", summaries)
def test_stacking(cards_db, summary, owner, state):
    ...
```
- 2 summaries × 2 owners × 3 states = 12 test cases

#### Using Indirect Parametrization
```python
@pytest.fixture()
def user(request):
    role = request.param
    print(f"\nLog in as {role}")
    yield role
    print(f"\nLog out {role}")

@pytest.mark.parametrize("user", ["admin", "team_member", "visitor"], indirect=["user"])
def test_access_rights(user):
    ...
```
- `indirect=["user"]` routes the param through the `user` fixture instead of directly to the test
- Useful for: setup/teardown per param, selecting a subset of fixture params

**Optional indirect fixture** (works with and without parametrize):
```python
@pytest.fixture()
def user(request):
    role = getattr(request, "param", "visitor")   # default if not parametrized
    ...
```

---

## Appendices

### A1. Virtual Environments
- `python -m venv venv --prompt .` — creates venv; `--prompt .` uses parent dir name
- Activate: `source venv/bin/activate` (macOS/Linux) or `venv\Scripts\activate.bat` (Windows)
- `deactivate` to exit

### A2. pip
- `pip install package` — install from PyPI
- `pip install ./local_dir/` — install local package
- `pip install -e ./local_dir/` — install in editable/development mode
- `pip install -r requirements.txt` — install from requirements file
- `pip install git+https://github.com/user/repo` — install from git
- `pip list` — show installed packages
- `pip uninstall package` — remove a package

# Book3 - Architecture Patterns with Python
**By Harry Percival & Bob Gregory (O'Reilly, 2020)**
**Subtitle:** Enabling Test-Driven Development, Domain-Driven Design, and Event-Driven Microservices

> Core thesis: As software grows in complexity, the way we structure our code matters more than the way we write individual functions. This book applies DDD, TDD, and event-driven patterns in Python to build systems that are testable, maintainable, and scalable.

---

# Introduction

## Why Do Our Designs Go Wrong?

- **Big ball of mud**: the natural state of software when we don't actively manage complexity
- Symptoms: hard to change, hard to test, side-effect-laden code
- The cure: **encapsulation** (simplifying behavior & hiding data) and **abstractions** (simplified interfaces hiding complex details)
- Layering: each layer depends only on the layer below it

## Encapsulation and Abstractions

- **Encapsulation**: simplifying behavior and hiding data behind a well-defined interface
- **Abstraction**: a simplified description of a system that emphasizes some details while ignoring others
- In traditional layered architecture, the problem is tight coupling to the database ("everything depends on the DB")

## The Dependency Inversion Principle

- **DIP**: High-level modules should not depend on low-level modules. Both should depend on abstractions.
- Instead of `BusinessLogic -> Database`, use `BusinessLogic -> AbstractRepository <- ConcreteRepository`
- The domain model should be the most important layer and should have *no* dependencies on infrastructure

---

# Part I: Building an Architecture to Support Domain Modeling

---

# Chapter 1: Domain Modeling

## What Is a Domain Model?

- **Domain model**: the mental map that business owners carry of the business processes they manage
- The software should mirror this mental map as closely as possible
- The book's example domain: a furniture allocation service (assigning incoming orders to batches of stock)

## Exploring the Domain Language

- Key terms from the example domain:
  - **SKU** (Stock Keeping Unit): a unique product type (e.g., `RED-CHAIR`)
  - **Batch**: a quantity of a SKU arriving on a specific date
  - **Order Line**: a single line on a customer's order (SKU + quantity)
  - **Allocate**: link an order line to a batch, reducing available stock

## Unit Testing Domain Models

```python
# Domain model tests are pure Python - no DB, no frameworks
def test_allocating_to_a_batch_reduces_the_available_quantity():
    batch = Batch("batch-001", "SMALL-TABLE", qty=20, eta=date.today())
    line = OrderLine("order-ref", "SMALL-TABLE", 2)

    batch.allocate(line)

    assert batch.available_quantity == 18
```

- Tests use plain Python objects — no ORM, no framework
- Business rules are expressed as simple unit tests

## Dataclasses Are Great for Value Objects

- **Value Object**: defined by its attributes, has no persistent identity, is interchangeable with other instances with same values
- Use `@dataclass(frozen=True)` for immutability

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int
```

## Entities vs Value Objects

| | Entity | Value Object |
|---|---|---|
| Identity | Has a persistent identity | Defined entirely by values |
| Equality | By reference/ID | By value (structural equality) |
| Mutability | Typically mutable | Preferably immutable |
| Example | `Batch` (has a reference) | `OrderLine` (no unique identity) |

## Domain Services

- When a piece of logic doesn't naturally belong to any existing entity/value object, it becomes a **domain service function**
- Example: `allocate()` is a standalone function in `model.py`, not a method on either `Order` or `Batch`

```python
# Domain service function (src/allocation/domain/model.py)
def allocate(line: OrderLine, batches: List[Batch]) -> str:
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
    except StopIteration:
        raise OutOfStock(f"Out of stock for sku {line.sku}")
    batch.allocate(line)
    return batch.reference
```

## Exceptions as Domain Concepts

```python
class OutOfStock(Exception):
    pass
```

- Domain exceptions are part of the ubiquitous language

---

# Chapter 2: Repository Pattern

## The Normal ORM Way: Model Depends on ORM

- Typical approach: define your model classes inheriting from the ORM base class (e.g., `django.db.models.Model`)
- Problem: your domain model is now coupled to the ORM — the most important layer depends on infrastructure

## Inverting the Dependency: ORM Depends on Model

- **Key library**: `SQLAlchemy` (specifically its Classical Mapping / Imperative Mapping)
- Define your domain model as plain Python classes *first*, then tell SQLAlchemy how to map them

```python
# orm.py — SQLAlchemy imperative/classical mapping
from sqlalchemy.orm import mapper, relationship
from domain import model

def start_mappers():
    lines_mapper = mapper(model.OrderLine, order_lines)  # table object
    mapper(model.Batch, batches, properties={
        '_allocations': relationship(lines_mapper, secondary=allocations)
    })
```

- This keeps the domain model **ignorant of persistence** — it's just plain Python classes
- The ORM imports the model, not the other way around

## Introducing the Repository Pattern

- **Repository**: an abstraction over persistent storage; it pretends all data is in memory
- Simplest possible interface: `.add()` and `.get()`

```python
import abc
from domain import model

class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, batch: model.Batch):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session):
        self.session = session

    def add(self, batch):
        self.session.add(batch)

    def get(self, reference):
        return self.session.query(model.Batch).filter_by(
            reference=reference
        ).one()

    def list(self):
        return self.session.query(model.Batch).all()
```

## Building a Fake Repository for Tests

```python
class FakeRepository(AbstractRepository):
    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)
```

- Fake repos enable fast, isolated unit tests with no DB needed

## Trade-Offs

| Pros | Cons |
|---|---|
| Simple interface for storage | Extra layer of abstraction (an "ORM is already an abstraction") |
| Easy to swap infra via fakes for testing | ORM mapping requires extra setup |
| Writes are decoupled from reads | Another thing for devs to learn |

---

# Chapter 3: A Brief Interlude: On Coupling and Abstractions

## Abstracting State Aids Testability

- Problem: how do you test code that has side effects (file I/O, HTTP calls, DB writes)?
- Three approaches:
  1. **Mock everything** (fragile, couples tests to implementation)
  2. **Edge-to-edge testing** (integration/E2E — slow, complex)
  3. **Abstract away side effects** behind simple interfaces (the book's preferred approach)

## The "Ports and Adapters" / Hexagonal Architecture

- Business logic at the core, infrastructure at the edges
- **Port**: an abstract interface (e.g., `AbstractRepository`)
- **Adapter**: a concrete implementation (e.g., `SqlAlchemyRepository`, `FakeRepository`)

## Functional Core, Imperative Shell

- Alternative framing: keep the *core* logic pure (no side effects), push I/O to the *shell*
- Not always achievable in Python, but a useful ideal

## Choosing the Right Abstraction

- Good abstractions simplify testing, aid in reasoning about code
- Bad abstractions add complexity without reducing coupling
- Rule of thumb: introduce an abstraction when you have a *concrete reason* (e.g., testability, swappability)

---

# Chapter 4: Our First Use Case: Flask API and Service Layer

## Connecting Our Application to the Real World

- **Flask** is the web framework used throughout the book
- Entrypoint (Flask route) should be thin — it just translates HTTP requests into domain operations

## A Typical Service Function

```python
# service_layer/services.py
def allocate(orderid: str, sku: str, qty: int, repo: AbstractRepository, session) -> str:
    batches = repo.list()
    if not is_valid_sku(sku, batches):
        raise InvalidSku(f"Invalid sku {sku}")
    batchref = model.allocate(OrderLine(orderid, sku, qty), batches)
    session.commit()
    return batchref
```

- **Service layer** (aka use-case layer): orchestrates a workflow
  - Fetches data from repositories
  - Calls domain model methods
  - Commits changes
- It doesn't *contain* business logic — it *coordinates* it

## The Service Layer and the Flask Endpoint

```python
# entrypoints/flask_app.py
@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    try:
        batchref = services.allocate(
            request.json["orderid"],
            request.json["sku"],
            request.json["qty"],
            repo, session,
        )
    except (model.OutOfStock, services.InvalidSku) as e:
        return jsonify({"message": str(e)}), 400
    return jsonify({"batchref": batchref}), 201
```

## Why Is Everything Called a Service?

- **Domain service**: pure logic that doesn't belong on an entity (e.g., `model.allocate()`)
- **Service layer / application service**: orchestration — fetches objects, invokes domain, persists results
- **Infrastructure service**: talks to external systems (email, file systems)

## Testing the Service Layer with Fakes

```python
# Unit tests use FakeRepository — no database needed
def test_returns_allocation():
    repo = FakeRepository([
        Batch("b1", "COMPLICATED-LAMP", 100, eta=None),
    ])
    result = services.allocate("o1", "COMPLICATED-LAMP", 10, repo, FakeSession())
    assert result == "b1"
```

---

# Chapter 5: TDD in High Gear and Low Gear

## Test Pyramid / Test Spectrum

- **Unit tests** (domain model): fast, isolated, business-rule focused
- **Service-layer tests**: test use cases, use fakes for infra
- **E2E tests** (against Flask + real DB): slow but validate integration

## Rules of Thumb for Test Types

- Write a few E2E tests to prove the plumbing works
- Write the bulk of your tests against the service layer (using fakes)
- Write unit tests for complex domain logic
- Aim to test *behavior*, not implementation

## High Gear vs. Low Gear

- **Low gear**: testing the domain model directly when building/debugging complex logic
- **High gear**: testing via the service layer once the API is stable
- Moving tests up to the service layer makes them less coupled to implementation — easier to refactor

## Fully Decoupling the Service-Layer Tests from the Domain

- Ideal: service-layer tests only use domain primitives (strings, ints) — never import domain classes
- This makes it easier to change the domain model without rewriting all tests

---

# Chapter 6: Unit of Work Pattern

## The Unit of Work Collaborates with the Repository

- **Unit of Work (UoW)**: abstracts the concept of an atomic operation / database transaction
- Provides a single entrypoint to repositories and handles `commit()` / `rollback()`

```python
class AbstractUnitOfWork(abc.ABC):
    products: repository.AbstractRepository

    def __enter__(self) -> "AbstractUnitOfWork":
        return self

    def __exit__(self, *args):
        self.rollback()

    @abc.abstractmethod
    def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError
```

## Real and Fake UoW

```python
# Real UoW
class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.products = repository.SqlAlchemyRepository(self.session)
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()


# Fake UoW for tests
class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass
```

## Using UoW in Service Layer

```python
def allocate(orderid: str, sku: str, qty: int,
             uow: unit_of_work.AbstractUnitOfWork) -> str:
    line = OrderLine(orderid, sku, qty)
    with uow:  # context manager handles transaction
        product = uow.products.get(sku=sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {sku}")
        batchref = product.allocate(line)
        uow.commit()  # explicit commit
    return batchref
```

- The `with` block ensures rollback on failure (via `__exit__`)
- Explicit `commit()` makes it clear when a transaction succeeds

---

# Chapter 7: Aggregates and Consistency Boundaries

## Why Do We Need Aggregates?

- An **aggregate** is a cluster of domain objects treated as a single unit for data changes
- It acts as a **consistency boundary**: all invariants within the aggregate are guaranteed to be consistent after each operation
- Operations across aggregates accept **eventual consistency**

## Choosing an Aggregate

- In the allocation example, `Product` becomes the aggregate root
- A `Product` contains its `Batch`es — you always go through the `Product` to allocate

```python
class Product:
    def __init__(self, sku: str, batches: List[Batch], version_number: int = 0):
        self.sku = sku
        self.batches = batches
        self.version_number = version_number

    def allocate(self, line: OrderLine) -> str:
        try:
            batch = next(b for b in sorted(self.batches) if b.can_allocate(line))
        except StopIteration:
            raise OutOfStock(f"Out of stock for sku {line.sku}")
        batch.allocate(line)
        self.version_number += 1
        return batch.reference
```

## Optimistic Concurrency with Version Numbers

- `version_number` is incremented on each change to detect concurrent modifications
- Implemented with SQLAlchemy's `version_id_col` feature

```sql
-- Optimistic lock at DB level
UPDATE products SET version_number=:new
WHERE sku=:sku AND version_number=:old
```

- If two transactions try to modify the same `Product` concurrently, one will fail (0 rows updated) and retry

## One Aggregate = One Repository

- Each aggregate type gets its own repository
- The repository fetches the *entire* aggregate (root + children) and saves it as a unit
- Aggregates reference each other only by identity (e.g., `sku` string), not by direct object reference

---

# Chapter 8: Events and the Message Bus

## Events

- **Domain Event**: a data structure representing something that happened in the domain
- Events are simple dataclasses

```python
from dataclasses import dataclass

class Event:
    pass

@dataclass
class OutOfStock(Event):
    sku: str

@dataclass
class Allocated(Event):
    orderid: str
    sku: str
    qty: int
    batchref: str
```

## The Model Raises Events

- Domain objects collect events on an internal list; they don't dispatch them directly
- Events are harvested and dispatched *after* the transaction commits

```python
class Product:
    def __init__(self, sku, batches, version_number=0):
        self.sku = sku
        self.batches = batches
        self.version_number = version_number
        self.events = []  # list of domain events

    def allocate(self, line):
        try:
            batch = next(...)
        except StopIteration:
            self.events.append(events.OutOfStock(line.sku))
            return None
        ...
```

## The Message Bus Maps Events to Handlers

```python
# service_layer/messagebus.py
HANDLERS = {
    events.OutOfStock: [handlers.send_out_of_stock_notification],
}  # type: Dict[Type[events.Event], List[Callable]]

def handle(event: events.Event, uow: AbstractUnitOfWork):
    for handler in HANDLERS[type(event)]:
        handler(event, uow=uow)
```

## The UoW Publishes Events to the Message Bus

```python
class AbstractUnitOfWork(abc.ABC):
    def collect_new_events(self):
        for product in self.products.seen:
            while product.events:
                yield product.events.pop(0)
```

- `products.seen` tracks all aggregates loaded during this UoW
- After commit, the service layer calls `messagebus.handle()` for each collected event

---

# Chapter 9: Going to Town on the Message Bus

## A New Architecture: Everything Is an Event Handler

- Refactors the entire application so that *all use cases* are event handlers
- The Flask endpoint just creates an event and passes it to the message bus
- The message bus becomes the single entrypoint for the service layer

```python
# Flask entrypoint
@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    try:
        event = events.AllocationRequired(
            request.json["orderid"], request.json["sku"], request.json["qty"]
        )
        results = messagebus.handle(event, uow)
        batchref = results.pop(0)
    except InvalidSku as e:
        return jsonify({"message": str(e)}), 400
    return jsonify({"batchref": batchref}), 201
```

## Test-Driving a New Handler

- New use case: `BatchQuantityChanged` event triggers reallocation if needed
- Test is end-to-end through the message bus: send events, assert outcomes

## Optionally: Unit Testing Event Handlers in Isolation with a Fake Message Bus

```python
class FakeUnitOfWorkWithFakeMessageBus(FakeUnitOfWork):
    def __init__(self):
        super().__init__()
        self.events_published = []

    def publish_events(self):
        for product in self.products.seen:
            while product.events:
                self.events_published.append(product.events.pop(0))
```

- Allows testing individual handlers without triggering the full chain
- Use edge-to-edge tests first; resort to isolated handler tests only for complex chains

---

# Chapter 10: Commands and Command Handler

## Commands and Events

| | Event | Command |
|---|---|---|
| Named | Past tense (`BatchCreated`) | Imperative mood (`CreateBatch`) |
| Error handling | Fail independently | Fail noisily |
| Sent to | All listeners (broadcast) | One recipient (directed) |

- **Commands** capture *intent*; **Events** capture *facts*
- Commands are sent by one actor to another with expectation of result
- Events are broadcast — sender doesn't know/care who handles them

```python
class Command:
    pass

@dataclass
class Allocate(Command):
    orderid: str
    sku: str
    qty: int

@dataclass
class CreateBatch(Command):
    ref: str
    sku: str
    qty: int
    eta: Optional[date] = None
```

## Differences in Exception Handling

```python
# messagebus.py
Message = Union[commands.Command, events.Event]

def handle(message: Message, uow):
    results = []
    queue = [message]
    while queue:
        message = queue.pop(0)
        if isinstance(message, events.Event):
            handle_event(message, queue, uow)
        elif isinstance(message, commands.Command):
            cmd_result = handle_command(message, queue, uow)
            results.append(cmd_result)
    return results

def handle_event(event, queue, uow):
    for handler in EVENT_HANDLERS[type(event)]:
        try:
            handler(event, uow=uow)
            queue.extend(uow.collect_new_events())
        except Exception:
            logger.exception("Exception handling event %s", event)
            continue  # events: log and continue

def handle_command(command, queue, uow):
    handler = COMMAND_HANDLERS[type(command)]  # exactly one handler
    try:
        result = handler(command, uow=uow)
        queue.extend(uow.collect_new_events())
        return result
    except Exception:
        logger.exception("Exception handling command %s", command)
        raise  # commands: raise to caller
```

- **Events**: catch exceptions, log, continue (event failures are isolated)
- **Commands**: let exceptions bubble up (the caller needs to know it failed)

## Recovering from Errors Synchronously

- **Library: `tenacity`** — Python library for retry logic with exponential backoff

```python
from tenacity import Retrying, RetryError, stop_after_attempt, wait_exponential

def handle_event(event, queue, uow):
    for handler in EVENT_HANDLERS[type(event)]:
        try:
            for attempt in Retrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential()
            ):
                with attempt:
                    handler(event, uow=uow)
                    queue.extend(uow.collect_new_events())
        except RetryError as retry_failure:
            logger.error("Failed to handle event %s times, giving up!",
                         retry_failure.last_attempt.attempt_number)
            continue
```

---

# Chapter 11: Event-Driven Architecture: Using Events to Integrate Microservices

## Distributed Ball of Mud, and Thinking in Nouns

- Anti-pattern: splitting a system into microservices by *nouns* (Orders, Batches, Warehouse) and using synchronous HTTP calls between them
- This creates **temporal coupling**: every part must be online at the same time
- **Connascence**: a taxonomy for types of coupling. Events reduce Connascence of Execution/Timing to Connascence of Name (only need to agree on event names/fields)

## The Alternative: Temporal Decoupling Using Asynchronous Messaging

- Think in terms of *verbs* (ordering, allocating), not *nouns* (orders, batches)
- Microservices should be **consistency boundaries** (like aggregates)
- Use **asynchronous messaging** (events) to integrate services — accept eventual consistency

## Using a Redis Pub/Sub Channel for Integration

- **Message broker**: infrastructure that routes messages between services (e.g., Redis pub/sub, RabbitMQ, Kafka, Amazon EventBridge)
- The book uses Redis pub/sub as a lightweight example

```python
# Redis event consumer (entrypoint) — src/allocation/entrypoints/redis_eventconsumer.py
r = redis.Redis(**config.get_redis_host_and_port())

def main():
    orm.start_mappers()
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe("change_batch_quantity")  # listen on channel

    for m in pubsub.listen():
        handle_change_batch_quantity(m)

def handle_change_batch_quantity(m):
    data = json.loads(m["data"])
    cmd = commands.ChangeBatchQuantity(ref=data["batchref"], qty=data["qty"])
    messagebus.handle(cmd, uow=unit_of_work.SqlAlchemyUnitOfWork())
```

```python
# Redis event publisher — src/allocation/adapters/redis_eventpublisher.py
def publish(channel, event: events.Event):
    r.publish(channel, json.dumps(asdict(event)))
```

## Internal Versus External Events

- Keep a clear distinction: not all internal events should be published externally
- Outbound events are a place where **validation** is especially important

---

# Chapter 12: Command-Query Responsibility Segregation (CQRS)

## Domain Models Are for Writing

- All the patterns in the book (aggregates, UoW, domain events) exist to enforce rules during *writes*
- Reads have very different requirements: simpler logic, higher throughput, staleness is OK

## Most Users Aren't Going to Buy Your Furniture

- Reads vastly outnumber writes in most systems
- Reads can be **eventually consistent** — trade consistency for performance

## Post/Redirect/Get and CQS

- **CQS (Command-Query Separation)**: functions should either modify state OR answer questions, never both
- Separate your POST (write) and GET (read) endpoints

## Hold On to Your Lunch, Folks

- Simplest CQRS: use raw SQL for reads, bypassing the domain model entirely

```python
# views.py — raw SQL read model
def allocations(orderid: str, uow: unit_of_work.SqlAlchemyUnitOfWork):
    with uow:
        results = list(uow.session.execute(
            'SELECT ol.sku, b.reference'
            ' FROM allocations AS a'
            ' JOIN batches AS b ON a.batch_id = b.id'
            ' JOIN order_lines AS ol ON a.orderline_id = ol.id'
            ' WHERE ol.orderid = :orderid',
            dict(orderid=orderid)
        ))
    return [{"sku": sku, "batchref": batchref} for sku, batchref in results]
```

## Alternatives for Read Models

| Option | Pros | Cons |
|---|---|---|
| Use repositories | Simple, consistent approach | Performance issues with complex queries |
| Custom ORM queries | Reuse DB config and model definitions | Adds query language complexity |
| Hand-rolled SQL | Fine control over performance | Schema changes affect both ORM and SQL |
| Separate read store (events) | Read-only copies scale out; queries are simple | Complex technique; eventual consistency |

## Updating a Read Model Table Using an Event Handler

```python
# Build a denormalized read-model table, updated by event handlers
EVENT_HANDLERS = {
    events.Allocated: [
        handlers.publish_allocated_event,
        handlers.add_allocation_to_read_model,  # updates the read table
    ],
}

def add_allocation_to_read_model(event: events.Allocated, uow):
    with uow:
        uow.session.execute(
            'INSERT INTO allocations_view (orderid, sku, batchref)'
            ' VALUES (:orderid, :sku, :batchref)',
            dict(orderid=event.orderid, sku=event.sku, batchref=event.batchref)
        )
        uow.commit()
```

## Changing Our Read Model Implementation Is Easy

- Can swap from SQL table to Redis with minimal changes
- Integration tests still pass because they test through the message bus, not the storage backend

```python
# Redis-backed read model
def add_allocation_to_read_model(event: events.Allocated, _):
    redis_eventpublisher.update_readmodel(event.orderid, event.sku, event.batchref)

# In redis_eventpublisher.py
def update_readmodel(orderid, sku, batchref):
    r.hset(orderid, sku, batchref)

def get_readmodel(orderid):
    return r.hgetall(orderid)
```

---

# Chapter 13: Dependency Injection (and Bootstrapping)

## Implicit Versus Explicit Dependencies

- **Explicit**: handler declares `uow: AbstractUnitOfWork` as a parameter — easy to swap in tests
- **Implicit**: handler does `from allocation.adapters import email` — tied to implementation; requires `mock.patch` in tests

```python
# Explicit (preferred) — dependency is a parameter
def send_out_of_stock_notification(event: events.OutOfStock, send_mail: Callable):
    send_mail('stock@made.com', f'Out of stock for {event.sku}')

# Implicit (less preferred) — dependency is a hardcoded import
from allocation.adapters import email
def send_out_of_stock_notification(event: events.OutOfStock, uow):
    email.send('stock@made.com', f'Out of stock for {event.sku}')
```

- Mocks tightly couple tests to *implementation*; explicit DI couples them to *abstractions*

## Preparing Handlers: Manual DI with Closures and Partials

```python
# Using closures / functools.partial to inject dependencies
import functools

def bootstrap(...)
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    # closure approach
    allocate_composed = lambda cmd: allocate(cmd, uow)
    # or equivalently with a partial
    allocate_composed = functools.partial(allocate, uow=uow)
```

- Closures use late binding (can cause surprises with mutable deps)
- `functools.partial` uses early binding — generally safer

## An Alternative Using Classes

```python
class AllocateHandler:
    def __init__(self, uow: unit_of_work.AbstractUnitOfWork):
        self.uow = uow

    def __call__(self, cmd: commands.Allocate):
        line = OrderLine(cmd.orderid, cmd.sku, cmd.qty)
        with self.uow:
            # ... handler body
```

## A Bootstrap Script

```python
# src/allocation/bootstrap.py
def bootstrap(
    start_orm: bool = True,
    uow: unit_of_work.AbstractUnitOfWork = unit_of_work.SqlAlchemyUnitOfWork(),
    send_mail: Callable = email.send,
    publish: Callable = redis_eventpublisher.publish,
) -> messagebus.MessageBus:

    if start_orm:
        orm.start_mappers()

    dependencies = {"uow": uow, "send_mail": send_mail, "publish": publish}

    injected_event_handlers = {
        event_type: [
            inject_dependencies(handler, dependencies)
            for handler in event_handlers
        ]
        for event_type, event_handlers in handlers.EVENT_HANDLERS.items()
    }
    # ... same for command handlers

    return messagebus.MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )

def inject_dependencies(handler, dependencies):
    params = inspect.signature(handler).parameters
    deps = {
        name: dependency
        for name, dependency in dependencies.items()
        if name in params
    }
    return lambda message: handler(message, **deps)
```

- `inspect.signature` matches handler params to the dependencies dict
- Keeps all initialization in one place — the **composition root**

## Initializing DI in Our Tests

```python
# Integration test bootstrap
@pytest.fixture
def sqlite_bus(sqlite_session_factory):
    bus = bootstrap.bootstrap(
        start_orm=True,
        uow=unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory),
        send_mail=lambda *args: None,  # no-op
        publish=lambda *args: None,
    )
    yield bus
    clear_mappers()

# Unit test bootstrap
def bootstrap_test_app():
    return bootstrap.bootstrap(
        start_orm=False,
        uow=FakeUnitOfWork(),
        send_mail=lambda *args: None,
        publish=lambda *args: None,
    )
```

## Building an Adapter "Properly": A Worked Example

1. **Define the abstract interface** (ABC)
2. **Implement the real thing** (e.g., `EmailNotifications` using `smtplib`)
3. **Build a fake** for unit/service-layer tests (e.g., `FakeNotifications`)
4. **Find a "less fake" for integration** (e.g., MailHog in Docker)
5. **Integration test** against the less-fake version

```python
# Abstract
class AbstractNotifications(abc.ABC):
    @abc.abstractmethod
    def send(self, destination, message):
        raise NotImplementedError

# Real
class EmailNotifications(AbstractNotifications):
    def __init__(self, smtp_host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.server = smtplib.SMTP(smtp_host, port=port)
        self.server.noop()

    def send(self, destination, message):
        msg = f"Subject: allocation service notification\n{message}"
        self.server.sendmail(
            from_addr="allocations@example.com",
            to_addrs=[destination],
            msg=msg
        )

# Fake (for unit tests)
class FakeNotifications(AbstractNotifications):
    def __init__(self):
        self.sent = defaultdict(list)  # type: Dict[str, List[str]]

    def send(self, destination, message):
        self.sent[destination].append(message)
```

## DI Framework Mentions

- **`Inject`** — used at MADE.com, works fine but annoys Pylint
- **`Punq`** — written by Bob Gregory
- **`dependencies`** — by the DRY-Python crew
- For most cases, manual DI (lambdas/partials + bootstrap script) is sufficient

## Message Bus Is Given Handlers at Runtime

```python
class MessageBus:
    def __init__(self, uow, event_handlers, command_handlers):
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers

    def handle(self, message: Message):
        self.queue = [message]
        while self.queue:
            message = self.queue.pop(0)
            if isinstance(message, events.Event):
                self.handle_event(message)
            elif isinstance(message, commands.Command):
                self.handle_command(message)
            else:
                raise Exception(f"{message} was not an Event or Command")
```

---

# Epilogue

## How Do I Get There from Here?

- You don't need a greenfield project — these patterns can be incrementally adopted in existing codebases
- Link refactoring to feature work to justify the investment (**"architecture tax"**)

## Separating Entangled Responsibilities

1. Identify **use cases** — give each an imperative name (Apply Billing Charges, Create Workspace)
2. Create a single function/class per use case that orchestrates the work
3. Pull data access and I/O out of the domain model and into use-case functions

## Identifying Aggregates and Bounded Contexts

- Break apart your object graph by replacing direct object references with IDs
- **Bidirectional links** are a code smell — they suggest aggregate boundaries are wrong
- For *reads*, replace ORM loops with raw SQL (first step toward CQRS)
- For *writes*, use message bus + events to coordinate between aggregates

## An Event-Driven Approach to Go to Microservices via Strangler Pattern

- **Strangler Fig pattern**: wrap a new system around the edges of the old one, gradually replacing functionality
- **Event interception**:
  1. Raise events in the old system
  2. Build a new system that consumes those events
  3. Replace the old system

## Convincing Your Stakeholders to Try Something New

- Use **domain modeling** (event storming, CRC cards, event modeling) to align engineers and business
- Treat domain problems as TDD katas — start small, demonstrate value

## Footguns

- **Reliable messaging is hard**: Redis pub/sub is not a production message broker; consider RabbitMQ, Kafka, Amazon EventBridge
- **Small, focused transactions**: design operations to fail independently
- **Idempotency**: handlers should be safe to call repeatedly with the same message
- **Event schema evolution**: document and version your events (JSON schema + markdown)

---

# Appendix A: Summary Diagram and Table

## Component Reference

| Layer | Component | Description |
|---|---|---|
| **Domain** | Entity | Object with identity that may change over time |
| | Value Object | Immutable, defined entirely by its attributes |
| | Aggregate | Cluster of objects treated as a unit; consistency boundary |
| | Event | Dataclass representing something that happened |
| | Command | Dataclass representing a job the system should do |
| **Service Layer** | Handler | Receives a command/event and orchestrates response |
| | Unit of Work | Abstraction around atomic DB operations |
| | Message Bus | Routes commands/events to their handlers |
| **Adapters** | Repository | Abstraction around persistent storage |
| | Event Publisher | Pushes events to external message bus |
| **Entrypoints** | Web (Flask) | Translates HTTP requests → commands |
| | Event Consumer | Translates external messages → commands |
| **Infrastructure** | External Message Bus | Message broker (Redis, Kafka, etc.) for inter-service communication |

---

# Appendix B: A Template Project Structure

## Project Layout

```
.
├── Dockerfile
├── Makefile
├── docker-compose.yml
├── mypy.ini
├── requirements.txt
├── src
│   ├── allocation
│   │   ├── __init__.py
│   │   ├── adapters/        (orm.py, repository.py)
│   │   ├── config.py
│   │   ├── domain/          (model.py, events.py, commands.py)
│   │   ├── entrypoints/     (flask_app.py, redis_eventconsumer.py)
│   │   └── service_layer/   (handlers.py, messagebus.py, unit_of_work.py)
│   └── setup.py
└── tests
    ├── conftest.py
    ├── e2e/          (test_api.py)
    ├── integration/  (test_orm.py, test_repository.py)
    ├── pytest.ini
    └── unit/         (test_batches.py, test_handlers.py)
```

## Key Config Patterns

- **`config.py`**: functions (not constants) that read from `os.environ` with sensible dev defaults
- **`docker-compose.yml`**: define services, set env vars, mount volumes for dev hot-reload
- **`setup.py`**: minimal `pip install -e` for src package
- **`PYTHONDONTWRITEBYTECODE=1`**: prevents .pyc clutter when mounting volumes in Docker
- **Library: `environ-config`** — elegant environment-based config in Python

---

# Appendix C: Swapping Out the Infrastructure: Do Everything with CSVs

## Key Lesson

- Because the domain model and service layer are decoupled from infrastructure, you can swap Postgres for CSV files by implementing new `CsvRepository` and `CsvUnitOfWork` classes
- All domain logic and service-layer orchestration is reused unchanged

```python
class CsvRepository(repository.AbstractRepository):
    def __init__(self, folder):
        self._batches_path = Path(folder) / "batches.csv"
        self._allocations_path = Path(folder) / "allocations.csv"
        self._batches = {}
        self._load()

    def get(self, reference):
        return self._batches.get(reference)

    def add(self, batch):
        self._batches[batch.reference] = batch

class CsvUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self, folder):
        self.batches = CsvRepository(folder)

    def commit(self):
        # write allocations back to CSV
        ...

    def rollback(self):
        pass
```

---

# Appendix D: Repository and Unit of Work Patterns with Django

*(Brief overview — see the book for full Django-specific code)*

- Django's ORM uses the Active Record pattern (model = table row), unlike SQLAlchemy's Data Mapper
- You can still apply Repository and UoW patterns on top of Django, though it requires more effort
- The key trick: use Django's `model_to_dict` and manual mapping to keep your domain model separate from Django models
- Django's `transaction.atomic()` can serve as the UoW's `commit()` boundary

---

# Appendix E: Validation

## Three Types of Validation

1. **Syntax validation**: is the input well-formed? (correct types, required fields present)
2. **Semantics validation**: does the input make sense? (is this a real SKU? is quantity positive?)
3. **Pragmatic validation**: can we do what's being asked? (is there enough stock?)

## Where to Validate

- **Syntax**: at the edge — in the entrypoint or on the message/command itself
- **Semantics**: in the domain model or handlers (e.g., checking a SKU exists)
- **Pragmatic**: deep in the domain model (business rules like "can't allocate more than available")

## The Ensure Pattern

```python
# Validation at command creation
@dataclass
class Allocate(Command):
    orderid: str
    sku: str
    qty: int

    def __post_init__(self):
        if not self.orderid:
            raise ValueError("orderid is required")
        if self.qty <= 0:
            raise ValueError("qty must be positive")
```

- Validate as early as possible
- Commands/events should be valid by construction
- Don't let invalid data propagate through the system

---

# Book4 - Crafting Test-Driven Software with Python — Summary

**Author:** Alessandro Molina | **Publisher:** Packt (2021)

---

## Part 1: Past and Present of Test-Driven Development

---

# Chapter 1: Getting Started with Software Testing

## Why software testing?

- Software testing verifies that code behaves as expected before shipping
- Catches bugs early, reduces cost of fixes, enables safe refactoring
- Tests act as living documentation of expected behavior

## Types of software tests

- **Unit tests** — test a single function/class in isolation; fast, numerous
- **Integration/Functional tests** — test multiple components working together
- **Acceptance/End-to-End tests** — test the whole system from user's perspective
- **Black-box tests** — test without knowledge of internals (input → expected output)
- **White-box tests** — test with knowledge of internals (verify paths/branches)

## The testing pyramid

- Bottom (most tests): **Unit tests** — fast, cheap, isolated
- Middle: **Integration tests** — moderate speed, test component interaction
- Top (fewest tests): **E2E/Acceptance tests** — slow, expensive, test full workflows
- Inverted pyramid = anti-pattern (too many slow tests, too few fast ones)

## Testing in Python

- Python stdlib includes `unittest` module (xUnit-style)
- **`pytest`** is the de facto standard third-party framework (used throughout book)
- **`pip install pytest`**

```python
# unittest style
import unittest

class TestExample(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(1 + 1, 2)

# pytest style (simpler — just use assert)
def test_addition():
    assert 1 + 1 == 2
```

## Arrange, Act, Assert pattern

```python
def test_something():
    # Arrange — set up preconditions
    data = [3, 1, 2]

    # Act — perform the action under test
    data.sort()

    # Assert — verify expected outcome
    assert data == [1, 2, 3]
```

## Test discovery in pytest

- Files must be named `test_*.py` or `*_test.py`
- Test functions must start with `test_`
- Test classes must start with `Test` (no `__init__`)
- Run with: `$ pytest` (auto-discovers tests)
- Verbose: `$ pytest -v`

---

# Chapter 2: Test Doubles with a Chat Application

## What are test doubles?

- **Test double** = generic term for any object that replaces a real dependency in tests
- Needed when real dependencies are slow, unreliable, or have side effects (I/O, network, DB)

## Types of test doubles

### Fakes

- Simplified working implementations (e.g., in-memory DB instead of real DB)

```python
# Real dependency
class DatabaseStorage:
    def save(self, data):
        # writes to actual database
        ...

# Fake — functional but simplified
class FakeStorage:
    def __init__(self):
        self._data = []
    def save(self, data):
        self._data.append(data)
```

### Stubs

- Return pre-configured responses; don't have real logic
- Replace a component to control what the system-under-test sees

```python
class StubConnection:
    def recv(self):
        return "Hello"  # always returns this, no real network
```

### Spies

- Record how they were called (args, call count) for later verification

```python
class SpyConnection:
    def __init__(self):
        self.sent_messages = []
    def send(self, msg):
        self.sent_messages.append(msg)

# In test:
spy = SpyConnection()
chat.broadcast("hi", spy)
assert "hi" in spy.sent_messages
```

### Mocks

- Pre-programmed with expectations; verify interactions happened correctly
- **`unittest.mock`** — Python stdlib mocking library

```python
from unittest.mock import Mock

mock_conn = Mock()
mock_conn.recv.return_value = "Hello"

result = mock_conn.recv()
assert result == "Hello"
mock_conn.recv.assert_called_once()
```

## `unittest.mock` key features

```python
from unittest.mock import Mock, patch, MagicMock

# Mock — generic mock object
m = Mock()
m.some_method.return_value = 42
m.some_method()  # returns 42
m.some_method.assert_called_once()

# side_effect — raise exception or call function
m.method.side_effect = ValueError("boom")

# patch — temporarily replace an object
with patch("module.ClassName") as MockClass:
    instance = MockClass.return_value
    instance.method.return_value = "fake"

# patch as decorator
@patch("module.function_name")
def test_something(mock_func):
    mock_func.return_value = "mocked"
```

## Dependency injection for testability

- Pass dependencies as constructor args instead of hardcoding them
- Makes it trivial to swap real implementations for test doubles

```python
class ChatClient:
    def __init__(self, connection):  # inject dependency
        self._connection = connection

# In production:
client = ChatClient(RealConnection("server.com"))

# In tests:
client = ChatClient(FakeConnection())
```

---

# Chapter 3: Test-Driven Development while Creating a TODO List

## The TDD cycle: Red → Green → Refactor

1. **Red** — Write a failing test for the next piece of functionality
2. **Green** — Write the minimum code to make the test pass
3. **Refactor** — Clean up the code while keeping tests green
4. Repeat

## Starting with a failing test

```python
# Write the test FIRST — it should fail (Red)
def test_add_todo():
    app = TodoApp()
    app.add("Buy groceries")
    assert app.todos == [("Buy groceries", False)]
```

## Making it pass with minimum code

```python
# Write just enough to pass (Green)
class TodoApp:
    def __init__(self):
        self.todos = []

    def add(self, item):
        self.todos.append((item, False))
```

## Refactoring

- After green, improve code structure without changing behavior
- Tests give confidence that refactoring didn't break anything

## Key TDD principles

- Never write production code without a failing test
- Write only enough test to fail (one assertion at a time)
- Write only enough code to pass the current failing test
- Tests guide the design — they are a first-class citizen

---

# Chapter 4: Scaling the Test Suite

## Organizing tests into directories

```
project/
├── src/
│   └── mypackage/
│       └── __init__.py
├── tests/
│   ├── unit/
│   ├── functional/
│   └── acceptance/
└── setup.py
```

## Continuous Integration (CI)

- **CI** = automatically run tests on every commit/push
- Book uses **Travis CI** as example (`.travis.yml`)

```yaml
language: python
python:
  - "3.7"
  - "3.8"
install:
  - "pip install -e src"
script:
  - "python -m unittest discover tests -v"
```

## Running tests in the cloud

- Push to GitHub → Travis CI picks up → runs test suite → reports pass/fail
- Badge in README shows build status

## Performance tests & benchmarks

```python
import unittest
import time

class TestPerformance(unittest.TestCase):
    def test_operation_speed(self):
        start = time.time()
        # ... operation ...
        elapsed = time.time() - start
        assert elapsed < 1.0, f"Too slow: {elapsed}s"
```

## `pytest.ini` / `setup.cfg` configuration

```ini
# pytest.ini
[pytest]
testpaths = tests
addopts = -v
```

---

## Part 2: Crafting Quality Code with PyTest

---

# Chapter 5: Introduction to PyTest

## Why PyTest over unittest

- Simpler syntax — plain `assert` instead of `self.assertEqual()`
- Better output on failures (shows values, diffs)
- Powerful fixture system (vs setUp/tearDown)
- Rich plugin ecosystem
- **`pip install pytest`**

## Writing tests with PyTest

```python
# No class needed, no imports needed for basic tests
def test_addition():
    assert 1 + 1 == 2

def test_string():
    assert "hello".upper() == "HELLO"

# Can still use classes (no inheritance required)
class TestMath:
    def test_multiply(self):
        assert 3 * 4 == 12
```

## PyTest assertions

```python
# pytest rewrites assert statements for rich failure messages
def test_list():
    result = [1, 2, 3]
    assert result == [1, 2, 4]
    # E  assert [1, 2, 3] == [1, 2, 4]
    # E    At index 2 diff: 3 != 4

# Testing exceptions
import pytest

def test_raises():
    with pytest.raises(ValueError):
        int("not_a_number")

def test_raises_match():
    with pytest.raises(ValueError, match="invalid literal"):
        int("abc")
```

## PyTest fixtures

- **Fixture** = a function that provides test data or setup/teardown logic
- Declared with `@pytest.fixture` decorator
- Injected by name into test function arguments

```python
import pytest

@pytest.fixture
def sample_list():
    return [1, 2, 3]

def test_length(sample_list):
    assert len(sample_list) == 3

# Fixture with teardown (using yield)
@pytest.fixture
def db_connection():
    conn = create_connection()
    yield conn          # test runs here
    conn.close()        # teardown after test
```

## Fixture scopes

```python
@pytest.fixture(scope="function")   # default — per test function
@pytest.fixture(scope="class")      # once per test class
@pytest.fixture(scope="module")     # once per test module
@pytest.fixture(scope="session")    # once per entire test session
```

## conftest.py

- Special file for sharing fixtures across multiple test files
- Pytest auto-discovers `conftest.py` files
- Can exist at any level of the test directory hierarchy

```python
# tests/conftest.py — available to ALL tests
@pytest.fixture
def app():
    return Application()
```

## Parametrize — running a test with multiple inputs

```python
@pytest.mark.parametrize("input,expected", [
    (1, 1),
    (2, 4),
    (3, 9),
])
def test_square(input, expected):
    assert input ** 2 == expected
```

## Markers

```python
@pytest.mark.slow
def test_big_computation():
    ...

# Run only slow tests:    $ pytest -m slow
# Skip slow tests:        $ pytest -m "not slow"

@pytest.mark.skip(reason="not implemented yet")
def test_future_feature():
    ...

@pytest.mark.skipif(sys.platform == "win32", reason="Unix only")
def test_unix_feature():
    ...
```

## Useful CLI options

```bash
pytest -v                   # verbose output
pytest -s                   # show print statements (no capture)
pytest -x                   # stop on first failure
pytest --lf                 # re-run only last failed tests
pytest -k "test_add"        # run tests matching keyword expression
pytest --tb=short           # shorter tracebacks
```

---

# Chapter 6: Dynamic and Parametric Fixtures and Test Configuration

## Dynamic fixtures with `request`

```python
@pytest.fixture
def dynamic_fixture(request):
    # request.param gives the parametrized value
    return request.param * 2

@pytest.mark.parametrize("dynamic_fixture", [1, 2, 3], indirect=True)
def test_doubled(dynamic_fixture):
    assert dynamic_fixture in [2, 4, 6]
```

## `pytest_addoption` — custom CLI options

```python
# conftest.py
def pytest_addoption(parser):
    parser.addoption(
        "--env", action="store", default="test",
        help="Environment to run tests against"
    )

@pytest.fixture
def env(request):
    return request.config.getoption("--env")
```

```bash
$ pytest --env=staging
```

## Temporary directories & files

```python
# tmp_path — built-in fixture (pathlib.Path)
def test_write_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello")
    assert f.read_text() == "hello"

# tmp_path_factory — session-scoped
@pytest.fixture(scope="session")
def shared_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("data")
```

## capsys — capturing stdout/stderr

```python
def test_print(capsys):
    print("hello")
    captured = capsys.readouterr()
    assert captured.out == "hello\n"
```

## monkeypatch — temporarily modifying objects

```python
def test_env_var(monkeypatch):
    monkeypatch.setenv("API_KEY", "test123")
    assert os.environ["API_KEY"] == "test123"

def test_patch_function(monkeypatch):
    monkeypatch.setattr("module.expensive_call", lambda: "mocked")
```

---

# Chapter 7: Acceptance Testing with BDD

## What is BDD?

- **Behavior-Driven Development (BDD)** = extension of TDD that uses natural language to describe behavior
- Tests are written in **Gherkin** syntax (Given/When/Then)
- Bridges gap between developers and non-technical stakeholders

## `pytest-bdd` — BDD plugin for pytest

- **`pip install pytest-bdd`**

### Feature files (`.feature`)

```gherkin
# features/contacts.feature
Feature: Contact management
  As a user I want to manage my contacts

  Scenario: Add a contact
    Given I have an empty contact book
    When I add a contact "Alice" with number "1234567890"
    Then I should have 1 contact
    And the contact "Alice" should exist
```

### Step definitions

```python
from pytest_bdd import scenario, given, when, then, parsers

@scenario("contacts.feature", "Add a contact")
def test_add_contact():
    pass

@given("I have an empty contact book")
def empty_app():
    return Application()

@when(parsers.parse('I add a contact "{name}" with number "{number}"'))
def add_contact(empty_app, name, number):
    empty_app.run(f"contacts add {name} {number}")

@then(parsers.parse("I should have {count:d} contact"))
def check_count(empty_app, count):
    assert len(empty_app._contacts) == count
```

### Key Gherkin keywords

- **Given** — preconditions / initial context
- **When** — action performed
- **Then** — expected outcome / assertion
- **And** — additional step (inherits type of preceding keyword)
- **Scenario Outline** + **Examples** — parametrized scenarios

```gherkin
Scenario Outline: Add multiple contacts
  Given I have an empty contact book
  When I add a contact "<name>" with number "<number>"
  Then I should have 1 contact

  Examples:
    | name  | number     |
    | Alice | 1234567890 |
    | Bob   | 0987654321 |
```

---

# Chapter 8: PyTest Essential Plugins

## `pytest-cov` — code coverage

- **`pip install pytest-cov`**
- Uses `coverage.py` under the hood

```bash
# Basic coverage report
$ pytest --cov=mypackage

# Show which lines are not covered
$ pytest --cov=mypackage --cov-report=term-missing

# Output:
# Name                    Stmts  Miss  Cover  Missing
# mypackage/__init__.py      48     1    98%    68
```

```python
# Exclude lines from coverage
from . import main  # pragma: no cover
main()  # pragma: no cover
```

```ini
# pytest.ini — auto-run coverage every time
[pytest]
addopts = --cov=contacts --cov-report=term-missing
```

### Coveralls — coverage as a service

- Integrates with CI (Travis CI) to track coverage trends over time
- **`pip install coveralls`**

```yaml
# .travis.yml
after_success:
  - coveralls
```

## `pytest-benchmark` — performance benchmarking

- **`pip install pytest-benchmark`**
- Provides a `benchmark` fixture

```python
from contacts import Application

def test_loading(benchmark):
    app = Application()
    app._contacts = [(f"Name {n}", "number") for n in range(1000)]
    app.save()

    benchmark(app.load)  # benchmarks the app.load call
```

```bash
$ pytest -v benchmarks
# Reports: Min, Max, Mean, OPS (Kops/s), Rounds
```

### Comparing benchmark runs

```bash
# Save benchmarks and compare against previous
$ pytest --benchmark-autosave --benchmark-compare

# Profile bottlenecks
$ pytest --benchmark-cprofile=tottime
```

## `flaky` — retry unstable tests

- **`pip install flaky`**
- For tests that sometimes fail due to timing, concurrency, external services

```python
from flaky import flaky

@flaky
def test_appender():
    l = []
    flaky_appender(l, range(7000))
    assert l == list(range(7000))
```

```bash
# Detect flakiness
$ pytest test_flaky.py --force-flaky --min-passes=10 --max-runs=10

# Control retries
$ pytest --max-runs=3
```

## `pytest-testmon` — smart test selection

- **`pip install pytest-testmon`**
- Builds a dependency graph between code and tests
- On subsequent runs, only re-runs tests affected by code changes

```bash
# First run — builds relationship graph
$ pytest --testmon

# After changing code — only runs affected tests
$ pytest --testmon
# collected 16 items / 14 deselected / 2 selected
```

- Caveat: can't detect changes to config files, data files, or databases

## `pytest-xdist` — parallel test execution

- **`pip install pytest-xdist`**
- Distributes tests across multiple CPU workers

```bash
# Run with 2 workers
$ pytest -n 2

# Auto-detect CPU count
$ pytest -n auto
```

- Tests must be **isolated** (no shared state) for parallel execution
- Benchmarks are unreliable in parallel mode — use `--ignore benchmarks`

---

# Chapter 9: Managing Test Environments with Tox

## Introducing Tox

- **Tox** = virtual environment manager for testing
- Automates: create venvs, install deps, run test commands
- **`pip install tox`**

### `tox.ini` configuration

```ini
[tox]
setupdir = ./src

[testenv]
deps =
    pytest == 6.0.2
    pytest-bdd == 3.4.0
    flaky == 3.7.0
    pytest-benchmark == 3.2.3
    pytest-cov == 2.10.1
commands =
    pytest --cov=contacts {posargs}
```

```bash
# Run all environments
$ tox

# Pass extra args to pytest
$ tox -- ./tests -k load

# Run specific environment
$ tox -e benchmarks
```

## Testing multiple Python versions with Tox

```ini
[tox]
setupdir = ./src
envlist = py37, py38, py39

[testenv]
deps = ...
commands = pytest --cov=contacts --benchmark-skip {posargs}

# Per-version overrides
[testenv:py27]
deps =
    pytest == 4.6.11
    ...
```

## Using environments for more than Python versions

```ini
# Separate benchmarks environment (not in envlist)
[testenv:benchmarks]
commands =
    pytest --no-cov ./benchmarks {posargs}
```

```bash
$ tox -e benchmarks  # explicitly run benchmarks
```

## Using Tox with Travis CI

- **`pip install tox-travis`** — bridges Tox and Travis
- `tox-travis` reuses Travis's Python instead of installing it twice

```yaml
# .travis.yml
language: python
python:
  - 3.7
  - 3.8
  - 3.9
  - nightly
install:
  - "pip install tox-travis"
  - "pip install coveralls"
script:
  - "tox"
after_success:
  - coveralls
  - "tox -e benchmarks"
```

---

## Part 3: Testing for the Web

---

# Chapter 10: Testing Documentation and Property-Based Testing

## Testing documentation

- Documentation rots when code changes but docs don't
- **`doctest`** + **Sphinx** can verify code examples in docs actually run

### Sphinx setup

- **`pip install sphinx`**

```bash
$ sphinx-quickstart docs --ext-doctest --ext-autodoc
```

### `autoclass` directive — code-based reference

```rst
.. autoclass:: contacts.Application
   :members:
```

- Generates docs from docstrings → docs stay in sync with code

### `testcode` / `testoutput` — verified user guides

```rst
.. testsetup::

    from contacts import Application
    app = Application()

.. testcode::

    app.run("contacts add Name 0123456789")

.. testcode::

    app.run("contacts ls")

.. testoutput::

    Name 0123456789
```

```bash
$ make doctest  # runs all testcode blocks and verifies testoutput
```

- `code-block` = display only (not verified)
- `testcode` = displayed AND executed (verified)

## Property-based testing with Hypothesis

- **`pip install hypothesis`**
- Instead of testing specific examples, test **properties** that should hold for all inputs
- Hypothesis generates random inputs automatically

### Key concept: strategies

```python
from hypothesis import given
from hypothesis import strategies as st

# st.integers() — generates random ints
# st.text() — generates random strings
# st.lists() — generates random lists
# st.floats(), st.booleans(), st.none(), etc.

@given(st.integers(), st.integers())
def test_addition_commutative(a, b):
    assert a + b == b + a

@given(st.lists(st.integers()))
def test_sort_idempotent(lst):
    assert sorted(sorted(lst)) == sorted(lst)
```

### Composite strategies

```python
@st.composite
def phone_number(draw):
    prefix = draw(st.sampled_from(["+1", "+44", ""]))
    digits = draw(st.text(
        alphabet="0123456789",
        min_size=7, max_size=10
    ))
    return prefix + digits
```

### Hypothesis finds edge cases automatically

- Empty strings, boundary values, unicode, very large numbers
- When a test fails, Hypothesis **shrinks** the input to the minimal failing case
- Failed examples are saved in a database and replayed on future runs

```python
@given(st.text())
def test_add_contact_name(name):
    app = Application()
    # Hypothesis will try "", " ", unicode, very long strings, etc.
    if name.strip():
        app.run(f"contacts add {name} 1234567890")
        assert len(app._contacts) == 1
```

---

# Chapter 11: Testing for the Web: WSGI versus HTTP

## Testing HTTP clients

### Using real HTTP (slow, fragile)

```python
import requests

class HTTPClient:
    def __init__(self, url, requests=requests):
        self._url = url
        self._requests = requests

    def GET(self):
        return self._requests.get(self._url).text

    def POST(self, **kwargs):
        return self._requests.post(self._url, **kwargs).text

    def DELETE(self):
        return self._requests.delete(self._url).text
```

### `requests-mock` — mock HTTP responses without network

- **`pip install requests-mock`**

```python
import requests_mock as rm

class TestHTTPClient:
    def test_GET(self):
        with rm.Mocker() as m:
            m.get("http://httpbin.org/get", json={
                "headers": {"Host": "httpbin.org"},
                "args": {}
            })
            client = HTTPClient(url="http://httpbin.org/get")
            response = client.GET()
            assert '"Host": "httpbin.org"' in response
```

- Fast (no network), but doesn't verify client-server compatibility

## Testing WSGI with WebTest

- **WSGI** (Web Server Gateway Interface) = Python standard for web app ↔ server communication (PEP 333)
- **`pip install webtest`**

### WSGI basics

```python
# Minimal WSGI application
class Application:
    def __call__(self, environ, start_response):
        start_response(
            '200 OK',
            [('Content-type', 'text/plain; charset=utf-8')]
        )
        return ["Hello World".encode("utf-8")]
```

### WebTest — test WSGI apps without a server

```python
import webtest

class TestWSGIApp:
    def test_GET(self):
        client = webtest.TestApp(Application())
        response = client.get("http://httpbin.org/get").text
        assert '"Host": "httpbin.org"' in response

    def test_POST(self):
        client = webtest.TestApp(Application())
        response = client.post(
            url="http://httpbin.org/get?alpha=1",
            params={"beta": "2"}
        ).json
        assert response["form"] == {"beta": "2"}
```

- `TestApp` routes all requests to the WSGI app in-memory (no network!)
- Tests run in milliseconds vs seconds for real HTTP

### Dependency injection for dual testing

```python
class HTTPClient:
    def __init__(self, url, requests=requests):  # inject requests
        self._requests = requests
        ...

# Integration test — inject WebTest instead of requests
client = HTTPClient(
    url="http://httpbin.org/get",
    requests=webtest.TestApp(Application())
)
```

## Using WebTest with web frameworks

- Works with any WSGI framework: **Flask, Django, Pyramid, TurboGears2**

```python
# conftest.py — fixture to select framework via CLI
def pytest_addoption(parser):
    parser.addoption("--framework", action="store",
                     help="Choose: [tg2, django, flask, pyramid]")

@pytest.fixture
def wsgiapp(request):
    framework = request.config.getoption("--framework")
    if framework == "flask":
        from myapp.flask import make_application
    elif framework == "django":
        from myapp.django import make_application
    # ...
    return make_application()
```

```bash
$ pytest --framework=flask
$ pytest --framework=django
```

## Writing Django tests with Django's test client

```python
from django.test import TestCase

class HttpbinTests(TestCase):
    def test_home(self):
        response = self.client.get("/")
        self.assertContains(response, "Hello World")

    def test_GET(self):
        response = self.client.get("/get").content.decode("utf-8")
        assert '"Host": "httpbin.org"' in response
```

```bash
$ python manage.py test
```

- **`pytest-django`** — package that lets you run Django tests with pytest

---

# Chapter 12: End-to-End Testing with the Robot Framework

## Introducing the Robot Framework

- **Robot Framework** = automation framework for ATDD/BDD-style end-to-end testing
- Tests written in natural English-like keyword syntax in `.robot` files
- Originally developed by Nokia; widely used for web and mobile E2E tests
- **`pip install robotframework robotframework-seleniumlibrary webdrivermanager robotframework-screencaplibrary`**

### `.robot` file structure

```robot
*** Settings ***
Library    SeleniumLibrary

*** Variables ***
${BROWSER}    chrome

*** Test Cases ***
Hello World
    Run    echo "Hello World" > hello.txt
    ${filecontent} =    Get File    hello.txt
    Should Contain    ${filecontent}    Hello

*** Keywords ***
Echo Hello
    Log    Hello!
```

- `*** Settings ***` — configure libraries
- `*** Variables ***` — reusable variables
- `*** Test Cases ***` — the tests themselves
- `*** Keywords ***` — custom reusable commands
- Multiple spaces separate commands from arguments

## Testing with web browsers

- **`SeleniumLibrary`** — Robot library for browser automation (wraps Selenium)
- **`webdrivermanager`** — download browser drivers

```bash
$ webdrivermanager firefox chrome
```

```robot
*** Settings ***
Library    SeleniumLibrary

*** Test Cases ***
Search On Google
    Open Browser    http://www.google.com    Chrome
    Input Text    name=q    Stephen\ Hawking
    Press Keys    name=q    ENTER
    Page Should Contain    Wikipedia
    Close Window
```

## Recording the execution of tests

- **`ScreenCapLibrary`** — screenshots and video recording

```robot
*** Settings ***
Library    SeleniumLibrary
Library    ScreenCapLibrary

Test Setup      Start Video Recording
Test Teardown   Stop Video Recording
```

- Recordings and screenshots embedded in `log.html`

## Testing with headless browsers

```robot
*** Variables ***
${BROWSER}        headlesschrome
${NOTHEADLESS}=   "headlesschrome" not in "${BROWSER}"

*** Test Cases ***
Search On Google
    Open Browser    http://www.google.com    ${BROWSER}
    Run Keyword If    ${NOTHEADLESS}    Wait Until Page Contains Element    cnsw
    ...
```

## Testing multiple browsers

```bash
# Override variable from CLI
$ robot --variable browser:firefox searchgoogle.robot
$ robot --variable browser:headlessfirefox searchgoogle.robot
```

## Extending the Robot Framework

### Adding custom keywords (in `.robot` files)

```robot
*** Keywords ***
Echo Hello
    Log    Hello!

*** Test Cases ***
Use Custom Keywords
    Echo Hello
```

### Extending Robot from Python

```python
# HelloLibrary/__init__.py
class HelloLibrary:
    def say_hello(self):
        print("Hello from Python!")
```

```python
# setup.py
from setuptools import setup
setup(name='robotframework-hellolibrary', packages=['HelloLibrary'])
```

```robot
*** Settings ***
Library    HelloLibrary

*** Test Cases ***
Use Custom Keywords
    Say Hello
```

### Library scoping

```python
class HelloLibrary:
    ROBOT_LIBRARY_SCOPE = "SUITE"   # share instance across suite
    # or "GLOBAL" for entire test run (default is per-test)
```

---

## Quick Reference: Libraries Introduced

| Library / Tool | Purpose | Install |
|---|---|---|
| `pytest` | Test framework | `pip install pytest` |
| `unittest.mock` | Mocking (stdlib) | built-in |
| `pytest-bdd` | BDD / Gherkin tests | `pip install pytest-bdd` |
| `pytest-cov` | Code coverage | `pip install pytest-cov` |
| `pytest-benchmark` | Performance benchmarking | `pip install pytest-benchmark` |
| `flaky` | Retry unstable tests | `pip install flaky` |
| `pytest-testmon` | Smart test selection | `pip install pytest-testmon` |
| `pytest-xdist` | Parallel test execution | `pip install pytest-xdist` |
| `tox` | Test environment manager | `pip install tox` |
| `tox-travis` | Tox + Travis CI bridge | `pip install tox-travis` |
| `coveralls` | Coverage-as-a-service | `pip install coveralls` |
| `hypothesis` | Property-based testing | `pip install hypothesis` |
| `sphinx` | Documentation generator | `pip install sphinx` |
| `requests-mock` | Mock HTTP requests | `pip install requests-mock` |
| `webtest` | WSGI integration testing | `pip install webtest` |
| `pytest-django` | Django + pytest bridge | `pip install pytest-django` |
| `robotframework` | E2E test framework | `pip install robotframework` |
| `robotframework-seleniumlibrary` | Browser automation | `pip install robotframework-seleniumlibrary` |
| `robotframework-screencaplibrary` | Video/screenshot recording | `pip install robotframework-screencaplibrary` |
| `webdrivermanager` | Browser driver management | `pip install webdrivermanager` |

# Book5 - Refactoring: Improving the Design of Existing Code (2nd Edition)
**Martin Fowler, with Kent Beck**

---

## Chapter 1: Refactoring: A First Example

### The Starting Point

The chapter opens with a small theater company billing program. The initial `statement` function calculates charges for a customer's performance invoice. It's a single long function with a switch statement handling different play types (`tragedy`, `comedy`), computing charges and volume credits inline.

**Key problem:** The code works, but it's hard to change. Adding an HTML statement output or new play types requires duplicating or deeply modifying the tangled logic.

> A program that works but is poorly structured is hard to change. The compiler doesn't care whether the code is ugly — but people do.

### Decomposing the `statement` Function

Fowler's first move: **Extract Function** on logical chunks.

```python
def amount_for(a_performance: dict, play: dict) -> int:
    """Calculate the charge for a single performance."""
    result = 0
    if play["type"] == "tragedy":
        result = 40000
        if a_performance["audience"] > 30:
            result += 1000 * (a_performance["audience"] - 30)
    elif play["type"] == "comedy":
        result = 30000
        if a_performance["audience"] > 20:
            result += 10000 + 500 * (a_performance["audience"] - 20)
        result += 300 * a_performance["audience"]
    else:
        raise ValueError(f"unknown type: {play['type']}")
    return result
```

Each extraction follows the same rhythm:
1. Identify a coherent block of code
2. Extract it into its own function
3. **Run the tests** after every change
4. Commit frequently — small steps let you revert easily if something breaks

**Naming convention:** Use `result` as the return variable name inside extracted functions — it immediately signals the function's purpose.

### Removing the `play` Variable (Replace Temp with Query)

Instead of passing `play` as a parameter, Fowler replaces the temp variable with a function call:

```python
def play_for(a_performance: dict) -> dict:
    return plays[a_performance["play_id"]]
```

This **removes a local variable**, making future extractions easier (fewer params to pass). The trade-off: a repeated lookup vs. simpler function signatures. Fowler argues the performance cost is negligible and clarity wins.

### Extracting Volume Credits

```python
def volume_credits_for(perf: dict) -> int:
    result = max(perf["audience"] - 30, 0)
    if play_for(perf)["type"] == "comedy":
        result += perf["audience"] // 5
    return result
```

### Replacing the Accumulator (Split Loop + Replace Temp with Query)

Fowler splits the loop so each concern (total amount, total credits) has its own loop, then extracts each into a function:

```python
def total_volume_credits(invoice: dict) -> int:
    return sum(volume_credits_for(perf) for perf in invoice["performances"])

def total_amount(invoice: dict) -> int:
    return sum(amount_for(perf) for perf in invoice["performances"])
```

**"But doesn't looping twice hurt performance?"** — Fowler's answer: rarely. The refactored code is easier to optimize later (e.g., caching), and most performance concerns about refactoring are unfounded. **Refactor first, then profile and optimize.**

### Creating a Statement Data Structure (Split Phase)

To support both plain text and HTML output, Fowler introduces an intermediate data structure:

```python
def create_statement_data(invoice: dict, plays: dict) -> dict:
    """Build a data structure with all the info the rendering functions need."""
    result = {
        "customer": invoice["customer"],
        "performances": [enrich_performance(perf) for perf in invoice["performances"]],
    }
    result["total_amount"] = total_amount(result)
    result["total_volume_credits"] = total_volume_credits(result)
    return result

def enrich_performance(a_performance: dict) -> dict:
    result = dict(a_performance)  # shallow copy
    result["play"] = play_for(result)
    result["amount"] = amount_for(result)
    result["volume_credits"] = volume_credits_for(result)
    return result
```

Now rendering functions (`render_plain_text`, `render_html`) only depend on the data structure, not the raw invoice + plays.

### Polymorphism for Play Type Calculation

The final refactoring replaces the conditional logic with polymorphism:

```python
class PerformanceCalculator:
    def __init__(self, a_performance: dict, a_play: dict):
        self.performance = a_performance
        self.play = a_play

    @property
    def amount(self) -> int:
        raise NotImplementedError

    @property
    def volume_credits(self) -> int:
        return max(self.performance["audience"] - 30, 0)


class TragedyCalculator(PerformanceCalculator):
    @property
    def amount(self) -> int:
        result = 40000
        if self.performance["audience"] > 30:
            result += 1000 * (self.performance["audience"] - 30)
        return result


class ComedyCalculator(PerformanceCalculator):
    @property
    def amount(self) -> int:
        result = 30000
        if self.performance["audience"] > 20:
            result += 10000 + 500 * (self.performance["audience"] - 20)
        result += 300 * self.performance["audience"]
        return result

    @property
    def volume_credits(self) -> int:
        return super().volume_credits + self.performance["audience"] // 5


def create_calculator(a_performance: dict, a_play: dict) -> PerformanceCalculator:
    """Factory function replacing conditionals with polymorphism."""
    match a_play["type"]:
        case "tragedy":
            return TragedyCalculator(a_performance, a_play)
        case "comedy":
            return ComedyCalculator(a_performance, a_play)
        case _:
            raise ValueError(f"unknown type: {a_play['type']}")
```

**Key takeaway:** Adding a new play type now means adding a new subclass — no existing code needs modification (Open-Closed Principle).

### Chapter 1 Summary

The entire refactoring follows a pattern:
1. **Small steps** — each change is tiny, testable, and independently commitable
2. **Tests after every change** — if something breaks, you know exactly which change caused it
3. **Decompose → reorganize → replace conditionals with polymorphism**
4. The end result has the same behavior but is far easier to extend

---

## Chapter 2: Principles of Refactoring

### Defining Refactoring

- **Refactoring (noun):** A change made to the internal structure of software to make it easier to understand and cheaper to modify without changing its observable behavior.
- **Refactoring (verb):** To restructure software by applying a series of refactorings without changing its observable behavior.

The key distinction from general "restructuring": refactoring is a **specific, disciplined technique** — a sequence of small behavior-preserving transformations that cumulatively produce a large restructuring. Each individual step is small enough that errors are easy to find.

### The Two Hats

Fowler borrows Kent Beck's metaphor: at any moment, you're wearing either the **adding functionality** hat or the **refactoring** hat. Never both simultaneously.

- **Adding functionality:** Writing new tests, adding new capabilities, making tests pass
- **Refactoring:** Restructuring code without adding any new tests (existing tests should all still pass)

You swap hats frequently — sometimes every few minutes — but you should always be clear about which hat you're currently wearing.

### Why Should We Refactor?

- **Improves the design of software** — without refactoring, architecture decays as people make short-term changes without understanding the full design
- **Makes software easier to understand** — code is read far more often than it's written; investing in clarity pays off
- **Helps you find bugs** — when you understand the code deeply enough to refactor it, bugs become visible
- **Helps you program faster** — counterintuitive but critical: good internal design lets you add features faster over time (the "Design Stamina Hypothesis")

### When Should We Refactor?

**The Rule of Three:** The first time you do something, just do it. The second time, wince but do it anyway. The third time, refactor.

More practically:

- **Preparatory refactoring** — restructure before adding a feature so the feature is easier to add. *"It's like I want to go 100 miles east but instead of driving through the swamp, I'll drive 20 miles north to the highway."*
- **Comprehension refactoring** — refactor to understand code you're reading. As you understand it, embed that understanding back into the code.
- **Litter-pickup refactoring** — you see something slightly wrong while working nearby; fix it if easy, note it if hard.
- **Planned refactoring** — sometimes needed for neglected codebases, but ideally most refactoring is **opportunistic** (woven into feature work).
- **Long-term refactoring** — large-scale changes (replacing a library, untangling a dependency) done gradually over weeks by a team.

### When Should We NOT Refactor?

- When the code works and you don't need to understand or modify it — treat it as an API
- When it's easier to rewrite from scratch than to refactor

### Refactoring and Performance

Refactoring can make code slower (e.g., splitting a loop), but it almost never matters. The approach:
1. Write well-factored code without worrying about performance
2. Profile to find the actual bottlenecks (usually a small fraction of the code)
3. Optimize only those hotspots
4. Well-factored code is *easier* to optimize because you can isolate the hot path

### Refactoring and Architecture

- Refactoring changes the role of upfront architecture: you don't need to predict every future need, because you can restructure later
- **YAGNI (You Ain't Gonna Need It):** Build only for current requirements, then refactor when requirements change
- This doesn't mean no architecture — it means you make architecture decisions that are easy to refactor

### Refactoring and Software Development Process

- Self-testing code is a prerequisite for refactoring
- Refactoring enables Continuous Integration (CI): frequent integration reduces merge pain because each developer keeps their code well-factored
- The trio of **self-testing code + continuous integration + refactoring** (together called Extreme Programming) creates a virtuous cycle

---

## Chapter 3: Bad Smells in Code

**Definition:** A *code smell* is a surface-level indicator that something may be wrong in the code. Smells are heuristics, not rules — they suggest where to look, not necessarily what to do.

### Mysterious Name

Code that doesn't clearly communicate what it does. Names should reveal intent. Key refactorings: **Change Function Declaration**, **Rename Variable**, **Rename Field**.

### Duplicated Code

The same code structure in more than one place. Even slight variations count. Key refactorings: **Extract Function**, **Slide Statements**, **Pull Up Method**.

### Long Function

Longer functions are harder to understand. The key heuristic: whenever you feel the need to write a comment, extract that block into a function named after the *intent* of the code (not what it does mechanically). Key refactorings: **Extract Function**, **Replace Temp with Query**, **Replace Conditional with Polymorphism**.

### Long Parameter List

Too many parameters make functions hard to understand and call. Key refactorings: **Replace Parameter with Query**, **Preserve Whole Object**, **Introduce Parameter Object**, **Remove Flag Argument**, **Combine Functions into Class**.

### Global Data

Global data can be modified from anywhere, making bugs extremely hard to track. Key refactoring: **Encapsulate Variable** (at minimum, wrap in a function so you can monitor access and modification).

### Mutable Data

Mutations are a major source of bugs, especially when changes happen in unexpected places. Key refactorings: **Encapsulate Variable**, **Split Variable**, **Replace Derived Variable with Query**, **Combine Functions into Class**, **Change Reference to Value**, **Move Statements to Callers**.

### Divergent Change

A single module changes for multiple different reasons (e.g., adding a new database AND adding a new financial instrument both require changes to the same module). Violates Single Responsibility. Key refactorings: **Split Phase**, **Extract Function**, **Extract Class**, **Move Function**.

### Shotgun Surgery

The opposite of Divergent Change: a single logical change requires touching many different modules. Key refactorings: **Move Function**, **Move Field**, **Combine Functions into Class**, **Combine Functions into Transform**, **Inline Function**, **Inline Class**.

### Feature Envy

A function that interacts more with data from another module than its own. It *wants* to be in the other module. Key refactoring: **Move Function**. Exception: Strategy and Visitor patterns deliberately separate function from data.

### Data Clumps

Groups of data items that appear together repeatedly (e.g., `start_x, start_y, end_x, end_y`). If deleting one of the group would make the others meaningless, they belong in an object. Key refactorings: **Extract Class**, **Introduce Parameter Object**, **Preserve Whole Object**.

### Primitive Obsession

Using primitive types (strings, ints) where a small object would be better (e.g., money, phone numbers, date ranges). Key refactorings: **Replace Primitive with Object**, **Replace Type Code with Subclasses**, **Replace Conditional with Polymorphism**.

### Repeated Switches

The same `switch`/`match` statement (or `if-elif` chain) appearing in multiple places, switching on the same type code. Problem: adding a new case means finding and updating every switch. Key refactoring: **Replace Conditional with Polymorphism**.

### Loops

Loops can often be replaced with pipeline operations (`map`, `filter`, `reduce`, list comprehensions) that more clearly communicate intent. Key refactoring: **Replace Loop with Pipeline**.

### Lazy Element

A class or function that doesn't do enough to justify its existence (e.g., a class with one method that just delegates). Key refactorings: **Inline Function**, **Inline Class**, **Collapse Hierarchy**.

### Speculative Generality

"We might need this someday" — abstract classes, hooks, special cases, parameters that are never used. Key refactorings: **Collapse Hierarchy**, **Inline Function**, **Inline Class**, **Change Function Declaration** (to remove unused params), **Remove Dead Code**.

### Temporary Field

An object field that is only set in certain circumstances. Confusing because you expect all fields to be relevant. Key refactorings: **Extract Class**, **Move Function**, **Introduce Special Case**.

### Message Chains

`a.get_b().get_c().get_d()` — a long chain of navigations couples the code to the object structure. Key refactorings: **Hide Delegate**, or better, **Extract Function** on the code *using* the chain + **Move Function** to push it closer to the chain.

### Middle Man

A class where the majority of its methods just delegate to another class. Key refactorings: **Remove Middle Man**, **Inline Function**, **Replace Superclass with Delegate**, **Replace Subclass with Delegate**.

### Insider Trading

Modules trading too much data back and forth. Key refactorings: **Move Function**, **Move Field**, **Hide Delegate**, **Replace Subclass with Delegate**, **Replace Superclass with Delegate**.

### Large Class

A class doing too much — has too many fields, too much code, too many responsibilities. Key refactorings: **Extract Class**, **Extract Superclass**, **Replace Type Code with Subclasses**.

### Alternative Classes with Different Interfaces

Two classes that do similar things but have different interfaces. Key refactorings: **Change Function Declaration**, **Move Function**, **Extract Superclass**.

### Data Class

Classes that have fields, getters/setters, and nothing else. Not always a smell (data classes are fine for immutable data) but can indicate that behavior that should live with the data is elsewhere. Key refactorings: **Encapsulate Record**, **Remove Setting Method**, **Move Function**, **Extract Function**.

### Refused Bequest

A subclass that doesn't want most of the behavior it inherits. Mild form: mostly harmless. Strong form (subclass rejects interface): use **Replace Subclass with Delegate** or **Replace Superclass with Delegate**.

### Comments

Comments aren't inherently bad, but they often signal code that needs refactoring. If you feel the need to write a comment, try refactoring first so the code speaks for itself. Good comments explain *why*, not *what*. Key refactorings: **Extract Function**, **Change Function Declaration**, **Introduce Assertion**.

---

## Chapter 4: Building Tests

### The Value of Self-Testing Code

> Make sure all tests are fully automatic and that they check their own results.

**Self-testing code:** A comprehensive test suite that you can run with a single command. The key benefit isn't catching bugs after writing code — it's the **safety net for refactoring**. Without tests, refactoring is too risky.

Fowler's workflow: write a test, make it fail, make it pass, then refactor. This is essentially Test-Driven Development (TDD), though Fowler doesn't insist on strict TDD — the critical point is having tests, not the order you write them.

### Setting Up a Test Framework

The chapter uses a production planning example. In Python, this maps to `pytest`:

```python
# test_province.py
import pytest
from province import Province

@pytest.fixture
def asia():
    """Sample province data for testing."""
    return Province({
        "name": "Asia",
        "producers": [
            {"name": "Byzantium", "cost": 10, "production": 9},
            {"name": "Attalia", "cost": 12, "production": 10},
            {"name": "Sinope", "cost": 10, "production": 6},
        ],
        "demand": 30,
        "price": 20,
    })

def test_shortfall(asia):
    assert asia.shortfall == 5

def test_profit(asia):
    assert asia.profit == 230
```

**Key principles:**
- Each test should have its own fresh fixture — **never share mutable state between tests**. The `@pytest.fixture` mechanism provides a fresh copy for each test function.
- Tests should be **isolated** from each other; running order shouldn't matter.

### What to Test

- **Probe the boundaries:** Test edge cases, zero, negative, empty collections.
- **Test the things most likely to break:** Focus on complex conditionals, data transformations, boundary conditions.
- **Think about what can go wrong,** not just what should go right.

```python
def test_zero_demand(asia):
    asia.demand = 0
    assert asia.shortfall == -25
    assert asia.profit == 0

def test_negative_demand(asia):
    asia.demand = -1
    assert asia.shortfall == -26
    assert asia.profit == -10

def test_empty_producers():
    no_producers = Province({"name": "Empty", "producers": [], "demand": 30, "price": 20})
    assert no_producers.shortfall == 30
    assert no_producers.profit == 0
```

### Testing for Exceptions

```python
def test_string_for_producers():
    """Test with invalid data — string instead of list for producers."""
    data = {"name": "String producers", "producers": "", "demand": 30, "price": 20}
    prov = Province(data)
    assert prov.shortfall == 30  # or expect an error — test documents actual behavior
```

### How Much Testing?

- **Coverage tools** are useful for finding *untested* code but don't guarantee *quality*. 100% coverage doesn't mean the tests are good.
- Fowler's heuristic: "I get a feeling of confidence from testing, and I adjust my strategy to maintain that level of confidence."
- Focus testing effort on complex, tricky, and error-prone areas.
- **When you find a bug, write a test for it first** before fixing it.
- Tests don't need to be perfect — imperfect tests that run frequently are far better than perfect tests you never write.

> "The best measure of a good test suite is subjective: how confident are you that if someone introduces a bug into the code, your tests will catch it?"

---

## Chapter 5: Introducing the Catalog

Chapters 6–12 form a catalog of refactorings. Each refactoring follows a consistent format:

- **Name** — builds a vocabulary for communicating about refactoring
- **Sketch** — a visual summary of the transformation
- **Motivation** — when to apply it and when not to
- **Mechanics** — step-by-step instructions for applying it safely
- **Examples** — demonstrations with code

The refactorings are organized by theme: basic operations (Ch. 6), encapsulation (Ch. 7), moving features (Ch. 8), organizing data (Ch. 9), conditionals (Ch. 10), APIs (Ch. 11), and inheritance (Ch. 12).

---

## Chapter 6: A First Set of Refactorings

### Extract Function

**Motivation:** If you have to spend time figuring out *what* a chunk of code does, extract it into a function and name it after the *intent*. A function can be as short as a single line if the name adds clarity.

**Heuristic:** "If the code fragment requires a comment to explain what it does, extract it and name the function after that comment."

```python
# Before
def print_owing(invoice):
    print_banner()
    outstanding = calculate_outstanding(invoice)

    # print details
    print(f"name: {invoice.customer}")
    print(f"amount: {outstanding}")

# After
def print_owing(invoice):
    print_banner()
    outstanding = calculate_outstanding(invoice)
    print_details(invoice, outstanding)

def print_details(invoice, outstanding):
    print(f"name: {invoice.customer}")
    print(f"amount: {outstanding}")
```

**Mechanics:**
1. Create a new function named after the intent (what, not how)
2. Copy the extracted code into the new function
3. Check for local variables — pass them as parameters or return them
4. Replace the original code with a call to the new function
5. Test

### Inline Function

**Motivation:** The inverse of Extract Function. When a function body is as clear as the name, or when you have a group of badly factored functions, inline them first, then re-extract better.

```python
# Before
def get_rating(driver):
    return 2 if more_than_five_late_deliveries(driver) else 1

def more_than_five_late_deliveries(driver):
    return driver.number_of_late_deliveries > 5

# After
def get_rating(driver):
    return 2 if driver.number_of_late_deliveries > 5 else 1
```

### Extract Variable

**Motivation:** Break complex expressions into named local variables to add explanation.

```python
# Before
def price(order):
    return (
        order.quantity * order.item_price
        - max(0, order.quantity - 500) * order.item_price * 0.05
        + min(order.quantity * order.item_price * 0.1, 100)
    )

# After
def price(order):
    base_price = order.quantity * order.item_price
    quantity_discount = max(0, order.quantity - 500) * order.item_price * 0.05
    shipping = min(base_price * 0.1, 100)
    return base_price - quantity_discount + shipping
```

Within a class, prefer **Extract Function** (making properties/methods) over local variables, since methods are reusable across the class.

### Inline Variable

**Motivation:** When a variable name says no more than the expression itself, or when the variable gets in the way of an adjacent refactoring.

```python
# Before
base_price = order.base_price
return base_price > 1000

# After
return order.base_price > 1000
```

### Change Function Declaration

**Motivation:** Function names and parameter lists are the joints of the software system. Good names are critical. If you think of a better name, rename immediately.

**Simple Mechanics (rename):**

```python
# Before
def circum(radius):
    return 2 * math.pi * radius

# After
def circumference(radius):
    return 2 * math.pi * radius
```

**Migration Mechanics (for published APIs or complex changes):**
1. Extract the body into a new function with the desired signature
2. Have the old function delegate to the new one
3. Callers migrate one at a time
4. Remove the old function when all callers are updated

### Encapsulate Variable

**Motivation:** For widely accessed data, wrap it in functions. This provides a clear point for monitoring, validation, or mutation control.

```python
# Before — module-level mutable data
_default_owner = {"first_name": "Martin", "last_name": "Fowler"}

# After — encapsulated with getter/setter
_default_owner = {"first_name": "Martin", "last_name": "Fowler"}

def get_default_owner():
    return dict(_default_owner)  # return a copy to prevent mutation

def set_default_owner(new_owner):
    global _default_owner
    _default_owner = new_owner
```

**Key insight:** For mutable data, returning a copy prevents callers from reaching past the encapsulation. For immutable data (frozen dataclasses, named tuples), this isn't necessary.

### Rename Variable

**Motivation:** Good names are the heart of clear programming. For variables used beyond a single function, the name matters even more.

```python
# Before
a = height * width

# After
area = height * width
```

For persistent fields in dataclasses, encapsulate first (getter/setter), then rename the underlying field.

### Introduce Parameter Object

**Motivation:** When the same group of parameters travel together across multiple functions, bundle them into an object.

```python
# Before
def amount_invoiced(start_date, end_date): ...
def amount_received(start_date, end_date): ...
def amount_overdue(start_date, end_date): ...

# After
@dataclass(frozen=True)
class DateRange:
    start: date
    end: date

    def contains(self, d: date) -> bool:
        return self.start <= d <= self.end

def amount_invoiced(date_range: DateRange): ...
def amount_received(date_range: DateRange): ...
def amount_overdue(date_range: DateRange): ...
```

**Key insight:** The new object often becomes a natural home for behavior (like `contains` above), creating a new abstraction that simplifies the domain model.

### Combine Functions into Class

**Motivation:** When a group of functions operate on the same data, bundle them into a class. The class provides a common environment for the functions and simplifies argument passing.

```python
# Before — loose functions passing a reading dict around
def base_rate(month, year): ...
def base_charge(reading): return base_rate(reading["month"], reading["year"]) * reading["quantity"]
def taxable_charge(reading): return max(0, base_charge(reading) - tax_threshold(reading["year"]))

# After
class Reading:
    def __init__(self, data: dict):
        self.customer = data["customer"]
        self.quantity = data["quantity"]
        self.month = data["month"]
        self.year = data["year"]

    @property
    def base_charge(self) -> float:
        return base_rate(self.month, self.year) * self.quantity

    @property
    def taxable_charge(self) -> float:
        return max(0, self.base_charge - tax_threshold(self.year))
```

### Combine Functions into Transform

**Motivation:** An alternative to the class approach: a transform function that takes the source data and returns an enriched copy with all derived values attached.

```python
def enrich_reading(original: dict) -> dict:
    result = dict(original)  # shallow copy — don't modify the input
    result["base_charge"] = calculate_base_charge(result)
    result["taxable_charge"] = max(0, result["base_charge"] - tax_threshold(result["year"]))
    return result
```

**Class vs. Transform:** Use a class when you want to enforce encapsulation or when the data is mutable. Use a transform when the data is essentially immutable and you're building a pipeline. **If the source data is mutated elsewhere, prefer the class** — a transform with stale derived values is a bug farm.

### Split Phase

**Motivation:** When code does two different things in sequence (e.g., parse input, then compute on the parsed data), split it into two phases with an explicit intermediate data structure.

```python
# Before — parsing and computation interleaved
def price_order(product, quantity, shipping_method):
    base_price = product["base_price"] * quantity
    discount = max(quantity - product["discount_threshold"], 0) * product["base_price"] * product["discount_rate"]
    shipping_per_case = (
        shipping_method["discounted_fee"] if base_price > shipping_method["discount_threshold"]
        else shipping_method["fee_per_case"]
    )
    shipping_cost = quantity * shipping_per_case
    return base_price - discount + shipping_cost

# After — pricing and shipping in separate phases
@dataclass
class PriceData:
    base_price: float
    quantity: int
    discount: float

def price_order(product, quantity, shipping_method):
    price_data = calculate_pricing_data(product, quantity)
    return apply_shipping(price_data, shipping_method)

def calculate_pricing_data(product, quantity) -> PriceData:
    base_price = product["base_price"] * quantity
    discount = max(quantity - product["discount_threshold"], 0) * product["base_price"] * product["discount_rate"]
    return PriceData(base_price=base_price, quantity=quantity, discount=discount)

def apply_shipping(price_data: PriceData, shipping_method) -> float:
    shipping_per_case = (
        shipping_method["discounted_fee"] if price_data.base_price > shipping_method["discount_threshold"]
        else shipping_method["fee_per_case"]
    )
    shipping_cost = price_data.quantity * shipping_per_case
    return price_data.base_price - price_data.discount + shipping_cost
```

---

## Chapter 7: Encapsulation

### Encapsulate Record

**Motivation:** Replace raw dicts/records with objects that control access. This lets you hide what is stored vs. what is derived.

```python
# Before
organization = {"name": "Acme Gooseberries", "country": "GB"}

# After
class Organization:
    def __init__(self, data: dict):
        self._name = data["name"]
        self._country = data["country"]

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def country(self) -> str:
        return self._country

    @country.setter
    def country(self, value: str):
        self._country = value
```

For nested records (e.g., `customers[id]["usages"][year][month]`), encapsulation is even more valuable — it hides the internal navigation structure.

### Encapsulate Collection

**Motivation:** When a class exposes a mutable collection directly, callers can modify the collection without the owning class knowing. Return a copy or a read-only view instead.

```python
class Person:
    def __init__(self, name: str):
        self._name = name
        self._courses: list[Course] = []

    @property
    def courses(self) -> tuple[Course, ...]:
        return tuple(self._courses)  # return immutable view

    def add_course(self, course: Course):
        self._courses.append(course)

    def remove_course(self, course: Course):
        self._courses.remove(course)
```

**Key point:** Never provide a setter for a collection that replaces the entire list. Provide `add` and `remove` methods. If you must allow bulk replacement, copy the incoming collection.

### Replace Primitive with Object

**Motivation:** Simple data items often grow into something richer. A phone number that started as a string eventually needs formatting, validation, area-code extraction. Wrap it early.

```python
# Before
orders = [o for o in all_orders if o.priority == "high" or o.priority == "rush"]

# After
class Priority:
    LEGAL_VALUES = ("low", "normal", "high", "rush")

    def __init__(self, value: str):
        if value not in self.LEGAL_VALUES:
            raise ValueError(f"Invalid priority: {value}")
        self._value = value

    def higher_than(self, other: "Priority") -> bool:
        return self.LEGAL_VALUES.index(self._value) > self.LEGAL_VALUES.index(other._value)

    def __eq__(self, other):
        return isinstance(other, Priority) and self._value == other._value

    def __str__(self):
        return self._value

orders = [o for o in all_orders if o.priority.higher_than(Priority("normal"))]
```

### Replace Temp with Query

**Motivation:** Temps used once to store intermediate results can be replaced by method/function calls. This makes the logic reusable and reduces parameter passing in Extract Function.

```python
# Before
def calculate_total(order):
    base_price = order.quantity * order.item_price
    if base_price > 1000:
        return base_price * 0.95
    return base_price * 0.98

# After
class Order:
    @property
    def base_price(self):
        return self.quantity * self.item_price

    @property
    def total(self):
        if self.base_price > 1000:
            return self.base_price * 0.95
        return self.base_price * 0.98
```

**Caveat:** Only do this when the extracted query has no side effects (is referentially transparent). If the computation is expensive, profile before worrying.

### Extract Class

**Motivation:** A class doing two things should be split into two classes. Signs: a subset of the fields/methods form a natural cluster, or data that changes together is separate from data that doesn't.

```python
# Before — Person has phone number logic mixed in
class Person:
    def __init__(self, name, office_area_code, office_number):
        self._name = name
        self._office_area_code = office_area_code
        self._office_number = office_number

    @property
    def telephone_number(self):
        return f"({self._office_area_code}) {self._office_number}"

# After — phone number extracted
class TelephoneNumber:
    def __init__(self, area_code, number):
        self._area_code = area_code
        self._number = number

    def __str__(self):
        return f"({self._area_code}) {self._number}"

class Person:
    def __init__(self, name, office_area_code, office_number):
        self._name = name
        self._telephone_number = TelephoneNumber(office_area_code, office_number)

    @property
    def telephone_number(self):
        return str(self._telephone_number)
```

### Inline Class

**Motivation:** The inverse of Extract Class. When a class is too thin — not pulling its weight — fold it back into its host.

Also useful as an intermediate step: inline two classes into one, then re-extract into better-factored classes.

### Hide Delegate

**Motivation:** When a client calls `person.department.manager`, it depends on both `Person` and `Department`. Hide the delegation:

```python
class Person:
    @property
    def manager(self):
        return self._department.manager
```

Now clients call `person.manager` and don't need to know about `Department`.

**Danger:** If you do this too much, the host class becomes a swollen middle man. Balance is key.

### Remove Middle Man

**Motivation:** The inverse of Hide Delegate. When a class has too many delegating methods, let clients call the delegate directly.

```python
# Instead of person.manager (delegating):
manager = person.department.manager
```

There's no "right" amount of hiding — it evolves over time. Add delegates when coupling hurts; remove them when the middle man bloats.

### Substitute Algorithm

**Motivation:** When you find a clearer or simpler way to accomplish what a function does, replace the entire body.

```python
# Before
def found_person(people):
    for p in people:
        if p == "Don":
            return "Don"
        if p == "John":
            return "John"
        if p == "Kent":
            return "Kent"
    return ""

# After
def found_person(people):
    candidates = {"Don", "John", "Kent"}
    return next((p for p in people if p in candidates), "")
```

---

## Chapter 8: Moving Features

### Move Function

**Motivation:** Move a function to the module/class where it's most used or where its context lives. Good modularity means related things are together.

**Heuristics for where a function should live:**
- What data does it reference most?
- What other functions call it?
- What functions does it call?

```python
# Before — account_type is passed in but owns the logic
class Account:
    @property
    def bank_charge(self):
        result = 4.5
        if self._days_overdrawn > 0:
            result += self.overdraft_charge
        return result

    @property
    def overdraft_charge(self):
        if self.type.is_premium:
            base = 10
            if self._days_overdrawn <= 7:
                return base
            return base + (self._days_overdrawn - 7) * 0.85
        return self._days_overdrawn * 1.75

# After — move overdraft_charge to AccountType
class AccountType:
    def overdraft_charge(self, days_overdrawn):
        if self.is_premium:
            base = 10
            if days_overdrawn <= 7:
                return base
            return base + (days_overdrawn - 7) * 0.85
        return days_overdrawn * 1.75

class Account:
    @property
    def bank_charge(self):
        result = 4.5
        if self._days_overdrawn > 0:
            result += self.type.overdraft_charge(self._days_overdrawn)
        return result
```

### Move Field

**Motivation:** Move a field to the class/record that uses it most. A sign you need this: you always pass the field to functions in another class, or every time a record changes, you need to update a field in another record.

```python
# Before — discount_rate on Customer
class Customer:
    def __init__(self, name, discount_rate):
        self.name = name
        self.discount_rate = discount_rate

class CustomerContract:
    def __init__(self, start_date):
        self.start_date = start_date

# After — discount_rate moves to CustomerContract
class CustomerContract:
    def __init__(self, start_date, discount_rate):
        self.start_date = start_date
        self.discount_rate = discount_rate

class Customer:
    def __init__(self, name, discount_rate):
        self.name = name
        self._contract = CustomerContract(datetime.today(), discount_rate)

    @property
    def discount_rate(self):
        return self._contract.discount_rate

    @discount_rate.setter
    def discount_rate(self, value):
        self._contract.discount_rate = value
```

### Move Statements into Function

**Motivation:** When the same code always executes alongside a function call, move it inside the function.

```python
# Before
def emit_photo_data(photo, output):
    output.append(f"<p>title: {photo.title}</p>")
    output.append(f"<p>location: {photo.location}</p>")

# caller always adds the date too:
emit_photo_data(photo, result)
result.append(f"<p>date: {photo.date.strftime('%Y-%m-%d')}</p>")

# After
def emit_photo_data(photo, output):
    output.append(f"<p>title: {photo.title}</p>")
    output.append(f"<p>location: {photo.location}</p>")
    output.append(f"<p>date: {photo.date.strftime('%Y-%m-%d')}</p>")
```

### Move Statements to Callers

**Motivation:** The inverse — when a function does something that only *some* callers want, move that part back to those callers.

This commonly happens as code evolves: a function that was perfectly cohesive now has a line that should behave differently in different contexts.

### Slide Statements

**Motivation:** Move related code to be adjacent, making it easier to understand and a precursor to Extract Function.

```python
# Before
pricing_plan = retrieve_pricing_plan()
order = retrieve_order()
charge_per_unit = pricing_plan.unit
# ... unrelated code ...
units = order.units
total = charge_per_unit * units

# After — slide declarations next to their usage
pricing_plan = retrieve_pricing_plan()
charge_per_unit = pricing_plan.unit
order = retrieve_order()
units = order.units
total = charge_per_unit * units
```

**Safety check:** Ensure no data dependency or side effect prevents the reordering. A statement can't move past code that modifies data it reads (or vice versa).

### Replace Inline Code with Function Call

**Motivation:** When you have code that does the same thing as an existing library function, use the library function. It communicates intent better and reduces duplication.

```python
# Before
has_new_england = False
for s in states:
    if s == "MA" or s == "CT" or s == "ME" or s == "VT" or s == "NH" or s == "RI":
        has_new_england = True
        break

# After
has_new_england = any(s in NEW_ENGLAND_STATES for s in states)
```

### Split Loop

**Motivation:** A loop that does two different things should be split into two loops, each doing one thing. This makes it possible to extract each loop body into its own function.

```python
# Before — single loop calculates both totals
youngest_age = float("inf")
total_salary = 0
for p in people:
    if p.age < youngest_age:
        youngest_age = p.age
    total_salary += p.salary

# After — separate loops, then extract
youngest_age = min(p.age for p in people)
total_salary = sum(p.salary for p in people)
```

**"But doesn't this mean looping twice?"** — Yes, and it almost never matters. If profiling shows it does, recombine the loops later.

### Replace Loop with Pipeline

**Motivation:** Collection pipelines (map, filter, reduce, list comprehensions) communicate intent more clearly than loops.

```python
# Before
names = []
for c in companies:
    if c.country == "India":
        names.append(c.name)

# After
names = [c.name for c in companies if c.country == "India"]
```

More complex pipelines:

```python
# Before — nested loop logic
result = []
for line in input_lines:
    fields = line.strip().split(",")
    if fields[1].strip() == "office":
        city = fields[0].strip()
        result.append(f"office in {city}")

# After
result = [
    f"office in {fields[0].strip()}"
    for line in input_lines
    for fields in [line.strip().split(",")]
    if fields[1].strip() == "office"
]
```

### Remove Dead Code

**Motivation:** Unused code creates confusion. Delete it — version control remembers everything.

```python
# Before
def calculate_price(order):
    # old_price = order.quantity * 5  # commented out since 2019
    return order.quantity * order.item_price
```

Just delete the commented-out line. Don't keep code "just in case" — that's what `git log` is for.

---

## Chapter 9: Organizing Data

### Split Variable

**Motivation:** A variable that is assigned more than once (and isn't a loop counter or collecting variable) is doing two jobs. Give each job its own variable.

```python
# Before — 'temp' is reused for two different purposes
def distance_travelled(scenario, time):
    result = 0
    acc = scenario.primary_force / scenario.mass  # acceleration phase 1
    primary_time = min(time, scenario.delay)
    result = 0.5 * acc * primary_time ** 2
    secondary_time = time - scenario.delay
    if secondary_time > 0:
        primary_velocity = acc * scenario.delay
        acc = (scenario.primary_force + scenario.secondary_force) / scenario.mass  # reused!
        result += primary_velocity * secondary_time + 0.5 * acc * secondary_time ** 2
    return result

# After — each acceleration gets its own variable
def distance_travelled(scenario, time):
    result = 0
    primary_acceleration = scenario.primary_force / scenario.mass
    primary_time = min(time, scenario.delay)
    result = 0.5 * primary_acceleration * primary_time ** 2
    secondary_time = time - scenario.delay
    if secondary_time > 0:
        primary_velocity = primary_acceleration * scenario.delay
        secondary_acceleration = (scenario.primary_force + scenario.secondary_force) / scenario.mass
        result += primary_velocity * secondary_time + 0.5 * secondary_acceleration * secondary_time ** 2
    return result
```

### Rename Field

**Motivation:** Names matter — especially in records and classes used widely. Renaming a field is straightforward with encapsulation already in place (just rename the internal field; the property name is what callers see).

### Replace Derived Variable with Query

**Motivation:** Mutable derived data easily becomes stale. Replace it with a calculation.

```python
# Before — _discounted_total is updated whenever a discount changes
class ProductionPlan:
    def __init__(self):
        self._adjustments = []
        self._production = 0  # derived, maintained manually

    def apply_adjustment(self, adjustment):
        self._adjustments.append(adjustment)
        self._production += adjustment.amount

# After — calculate on demand
class ProductionPlan:
    def __init__(self):
        self._adjustments = []

    @property
    def production(self):
        return sum(a.amount for a in self._adjustments)
```

**Exception:** When the calculation is expensive and you've profiled to confirm it's a bottleneck, caching is appropriate — but encapsulate it.

### Change Reference to Value

**Motivation:** Value objects are simpler to reason about because they're immutable. If a field doesn't need to be shared and updated in place, make it a value.

```python
# Before — Person's telephone number is a shared reference
class TelephoneNumber:
    def __init__(self, area_code, number):
        self.area_code = area_code  # mutable
        self.number = number        # mutable

# After — immutable value object
@dataclass(frozen=True)
class TelephoneNumber:
    area_code: str
    number: str
```

With a frozen dataclass, `==` compares by value automatically. To change the number, you create a new `TelephoneNumber` instead of mutating.

### Change Value to Reference

**Motivation:** Sometimes you *need* shared identity — e.g., multiple orders reference the same customer, and updating the customer should be reflected everywhere.

```python
# Solution: use a repository / registry
_customer_repository: dict[str, Customer] = {}

def register_customer(id: str) -> Customer:
    if id not in _customer_repository:
        _customer_repository[id] = Customer(id)
    return _customer_repository[id]

class Order:
    def __init__(self, data: dict):
        self._customer = register_customer(data["customer_id"])
```

---

## Chapter 10: Simplifying Conditional Logic

### Decompose Conditional

**Motivation:** Complex conditional logic is one of the hardest things to read. Extract the condition and each branch into functions named for their intent.

```python
# Before
if plan.start_date <= a_date <= plan.end_date:
    charge = plan.base_rate * quantity + plan.tax
else:
    charge = plan.base_rate * quantity * plan.off_peak_factor + plan.tax

# After
if is_peak_season(a_date, plan):
    charge = peak_charge(quantity, plan)
else:
    charge = off_peak_charge(quantity, plan)
```

Or using a conditional expression for simple cases:

```python
charge = peak_charge(quantity, plan) if is_peak_season(a_date, plan) else off_peak_charge(quantity, plan)
```

### Consolidate Conditional Expression

**Motivation:** When multiple conditions yield the same result, combine them into a single check with a descriptive name.

```python
# Before
def disability_amount(employee):
    if employee.seniority < 2:
        return 0
    if employee.months_disabled > 12:
        return 0
    if employee.is_part_time:
        return 0
    return compute_disability(employee)

# After
def disability_amount(employee):
    if is_not_eligible_for_disability(employee):
        return 0
    return compute_disability(employee)

def is_not_eligible_for_disability(employee):
    return (
        employee.seniority < 2
        or employee.months_disabled > 12
        or employee.is_part_time
    )
```

### Replace Nested Conditional with Guard Clauses

**Motivation:** Use guard clauses (early returns) for special cases at the top of a function, leaving the "happy path" as the main logic.

```python
# Before — deeply nested
def pay_amount(employee):
    if employee.is_separated:
        result = separated_amount()
    else:
        if employee.is_retired:
            result = retired_amount()
        else:
            result = normal_pay_amount(employee)
    return result

# After — guard clauses
def pay_amount(employee):
    if employee.is_separated:
        return separated_amount()
    if employee.is_retired:
        return retired_amount()
    return normal_pay_amount(employee)
```

**Key insight:** Guard clauses say "this is an unusual condition — handle it and get out." The indented `if-else` form implies both branches are equally likely/normal. Use the form that matches the semantics.

### Replace Conditional with Polymorphism

**Motivation:** When you have a switch/match on a type code that appears in multiple places, replace it with a class hierarchy. Each case becomes a subclass with its own implementation.

```python
# Before — switch on bird type
def plumage(bird):
    match bird["type"]:
        case "EuropeanSwallow":
            return "average"
        case "AfricanSwallow":
            return "average" if bird["number_of_coconuts"] <= 2 else "tired"
        case "NorwegianBlueParrot":
            return "beautiful" if bird["voltage"] <= 100 else "scorched"

# After — polymorphism
class Bird:
    def __init__(self, data):
        self._name = data["name"]

class EuropeanSwallow(Bird):
    @property
    def plumage(self):
        return "average"

class AfricanSwallow(Bird):
    def __init__(self, data):
        super().__init__(data)
        self._number_of_coconuts = data["number_of_coconuts"]

    @property
    def plumage(self):
        return "average" if self._number_of_coconuts <= 2 else "tired"

class NorwegianBlueParrot(Bird):
    def __init__(self, data):
        super().__init__(data)
        self._voltage = data["voltage"]

    @property
    def plumage(self):
        return "beautiful" if self._voltage <= 100 else "scorched"

def create_bird(data):
    match data["type"]:
        case "EuropeanSwallow": return EuropeanSwallow(data)
        case "AfricanSwallow": return AfricanSwallow(data)
        case "NorwegianBlueParrot": return NorwegianBlueParrot(data)
        case _: return Bird(data)
```

**Variant — using polymorphism for a variation within a type:** When you don't want a full hierarchy for the main type, create a helper hierarchy for just the varying behavior (delegation instead of inheritance).

### Introduce Special Case

**Motivation:** When many callers check for a special value (often `None`) and do the same thing, create a Special Case object (also known as the **Null Object pattern**).

```python
# Before — scattered null checks
customer_name = site.customer.name if site.customer != "unknown" else "occupant"
plan = site.customer.plan if site.customer != "unknown" else BASIC_PLAN

# After — special case class
class UnknownCustomer:
    @property
    def name(self):
        return "occupant"

    @property
    def plan(self):
        return BASIC_PLAN

    @property
    def is_unknown(self):
        return True

class Site:
    @property
    def customer(self):
        return self._customer if self._customer != "unknown" else UnknownCustomer()

# Now callers just use site.customer.name — no special-casing needed
```

### Introduce Assertion

**Motivation:** Assertions document assumptions that should always be true. They make implicit assumptions explicit and serve as both documentation and a safety net.

```python
class Customer:
    def apply_discount(self, amount):
        assert self.discount_rate is not None, "discount_rate must be set before applying discount"
        return amount - (self.discount_rate * amount)
```

**Key point:** Assertions should never affect the logic — the program should behave identically whether they're present or stripped out. Don't use assertions for validation of external inputs; use them to document internal invariants.

---

## Chapter 11: Refactoring APIs

### Separate Query from Modifier

**Motivation (Command-Query Separation):** A function should either return a value (query) or have a side effect (command), never both. This makes code easier to reason about and test.

```python
# Before — find miscreant AND send alert (side effect + return value)
def alert_for_miscreant(people):
    for p in people:
        if p.name == "Don" or p.name == "John":
            send_alert(p)
            return p.name
    return ""

# After — separate the query from the command
def find_miscreant(people):
    for p in people:
        if p.name == "Don" or p.name == "John":
            return p.name
    return ""

def alert_for_miscreant(people):
    if miscreant := find_miscreant(people):
        send_alert(miscreant)
```

### Parameterize Function

**Motivation:** When multiple functions do very similar things with different literal values, unify them into a single function with a parameter.

```python
# Before
def ten_percent_raise(person):
    person.salary = person.salary * 1.10

def five_percent_raise(person):
    person.salary = person.salary * 1.05

# After
def raise_salary(person, factor):
    person.salary = person.salary * (1 + factor)
```

### Remove Flag Argument

**Motivation:** Boolean (or string) flags that change function behavior are confusing for callers. Replace with explicit functions.

```python
# Before
def set_dimension(name, value):
    if name == "height":
        self._height = value
    elif name == "width":
        self._width = value

# After
def set_height(value):
    self._height = value

def set_width(value):
    self._width = value
```

**Key insight:** The caller's code should read clearly. `book_concert(customer, True)` is opaque; `book_concert_premium(customer)` communicates intent.

### Preserve Whole Object

**Motivation:** When you extract several values from an object just to pass them to a function, pass the whole object instead. This reduces parameter lists and makes the function more resilient to changes in the object's structure.

```python
# Before
low = room.days_temp_range.low
high = room.days_temp_range.high
if heating_plan.within_range(low, high): ...

# After
if heating_plan.within_range(room.days_temp_range): ...
```

**Caveat:** If passing the whole object introduces a dependency you don't want (e.g., a utility function shouldn't depend on a domain object), keep the individual parameters.

### Replace Parameter with Query

**Motivation:** When a parameter can be derived from another parameter or from the receiver, remove it and have the function compute the value itself.

```python
# Before
class Order:
    @property
    def final_price(self):
        base = self.quantity * self.item_price
        level = 1 if self.quantity > 100 else 2
        return self.discounted_price(base, level)

    def discounted_price(self, base, level):
        return base * 0.95 if level == 1 else base * 0.98

# After
class Order:
    @property
    def final_price(self):
        base = self.quantity * self.item_price
        return self.discounted_price(base)

    @property
    def discount_level(self):
        return 1 if self.quantity > 100 else 2

    def discounted_price(self, base):
        return base * 0.95 if self.discount_level == 1 else base * 0.98
```

**Caveat:** Don't do this if computing the value introduces an unwanted dependency or side effect into the called function.

### Replace Query with Parameter

**Motivation:** The inverse — when a function reaches into a global or has an unwanted dependency to get a value, pass it as a parameter instead. This is common when removing a dependency on a mutable global.

```python
# Before — function depends on a global thermostat
def target_temperature(plan):
    current_temp = thermostat.current_temperature  # global dependency
    if plan.target > current_temp:
        return plan.target
    return plan.target - (plan.target - current_temp) * plan.adjustment

# After — caller provides the value
def target_temperature(plan, current_temp):
    if plan.target > current_temp:
        return plan.target
    return plan.target - (plan.target - current_temp) * plan.adjustment
```

This makes the function **referentially transparent** (same inputs → same output), which is easier to test and reason about. The trade-off: it pushes the responsibility to the caller.

### Remove Setting Method

**Motivation:** If a field should not change after construction, remove its setter. This communicates immutability.

```python
# Before
class Person:
    def __init__(self, id_):
        self.id = id_  # settable — but should it be?

# After
class Person:
    def __init__(self, id_):
        self._id = id_

    @property
    def id(self):
        return self._id
    # No setter — id is immutable after construction
```

### Replace Constructor with Factory Function

**Motivation:** Constructors have limitations: they must return an instance of that exact class (no subclasses), they can't have descriptive names. Factory functions are more flexible.

```python
# Before
class Employee:
    def __init__(self, name, type_code):
        self.name = name
        self.type_code = type_code

# After
class Employee:
    def __init__(self, name, type_code):
        self.name = name
        self.type_code = type_code

def create_employee(name, type_code):
    return Employee(name, type_code)

# Or for subclass selection:
def create_employee(name, type_code):
    match type_code:
        case "engineer": return Engineer(name)
        case "manager": return Manager(name)
        case "salesman": return Salesman(name)
        case _: raise ValueError(f"unknown type: {type_code}")
```

### Replace Function with Command

**Motivation:** When a function is complex enough that you need to break it apart, but the pieces share significant local state, wrap it in a command object. The command object turns local variables into fields that all methods can access.

**Definition:** A *command object* (or just "command") is an object that encapsulates a function invocation. It provides facilities like undo, lifecycle management, and customization that plain functions don't.

```python
# Before — complex scoring function with many local variables
def score(candidate, medical_exam, scoring_guide):
    result = 0
    health_level = 0
    high_medical_risk = False

    if medical_exam.is_smoker:
        health_level += 10
        high_medical_risk = True

    certification_grade = "regular"
    if scoring_guide.state_with_low_certification(candidate.origin_state):
        certification_grade = "low"
        result -= 5

    # ... more complex logic using all these temps ...
    result -= max(health_level - 5, 0)
    return result

# After — command object
class Scorer:
    def __init__(self, candidate, medical_exam, scoring_guide):
        self._candidate = candidate
        self._medical_exam = medical_exam
        self._scoring_guide = scoring_guide

    def execute(self):
        self._result = 0
        self._health_level = 0
        self._high_medical_risk = False
        self._score_smoking()
        self._certify()
        self._result -= max(self._health_level - 5, 0)
        return self._result

    def _score_smoking(self):
        if self._medical_exam.is_smoker:
            self._health_level += 10
            self._high_medical_risk = True

    def _certify(self):
        self._certification_grade = "regular"
        if self._scoring_guide.state_with_low_certification(self._candidate.origin_state):
            self._certification_grade = "low"
            self._result -= 5

# Usage
score = Scorer(candidate, medical_exam, scoring_guide).execute()
```

### Replace Command with Function

**Motivation:** The inverse — when a command object is simple enough that a plain function would do, simplify. Commands add complexity; don't keep that complexity if you don't need it.

---

## Chapter 12: Dealing with Inheritance

### Pull Up Method

**Motivation:** When subclasses have identical methods, move the method to the superclass to eliminate duplication.

```python
# Before
class Employee:
    pass

class Engineer(Employee):
    @property
    def annual_cost(self):
        return self.monthly_cost * 12

class Salesman(Employee):
    @property
    def annual_cost(self):
        return self.monthly_cost * 12

# After
class Employee:
    @property
    def annual_cost(self):
        return self.monthly_cost * 12
```

**Variation — Template Method:** If the methods are *similar* but not identical, parameterize the differences or extract the differing parts into abstract methods, then pull up the common structure.

### Pull Up Field

**Motivation:** When subclasses have the same field, move it to the superclass.

### Pull Up Constructor Body

**Motivation:** When subclass constructors have common initialization logic, pull the common parts to the superclass `__init__`.

```python
# Before
class Employee:
    def __init__(self):
        self._name = None

class Manager(Employee):
    def __init__(self, name, grade):
        super().__init__()
        self._name = name
        self._grade = grade

class Engineer(Employee):
    def __init__(self, name):
        super().__init__()
        self._name = name

# After
class Employee:
    def __init__(self, name):
        self._name = name

class Manager(Employee):
    def __init__(self, name, grade):
        super().__init__(name)
        self._grade = grade

class Engineer(Employee):
    def __init__(self, name):
        super().__init__(name)
```

### Push Down Method

**Motivation:** When a method is only relevant to one subclass, move it out of the superclass into that subclass.

### Push Down Field

**Motivation:** When a field is only used by one subclass, push it down.

### Replace Type Code with Subclasses

**Motivation:** When an object has a type code that affects behavior (e.g., `type_code == "engineer"` triggers different logic), replace the type code with subclasses.

**Direct subclassing:**

```python
# Before
class Employee:
    def __init__(self, name, type_code):
        self._name = name
        self._type_code = type_code

# After
class Employee:
    def __init__(self, name):
        self._name = name

class Engineer(Employee):
    @property
    def type(self):
        return "engineer"

class Manager(Employee):
    @property
    def type(self):
        return "manager"

def create_employee(name, type_code):
    match type_code:
        case "engineer": return Engineer(name)
        case "manager": return Manager(name)
        case _: raise ValueError(f"Unknown type: {type_code}")
```

**Indirect subclassing (when you can't subclass the main class):** Subclass the *type* instead:

```python
class EmployeeType:
    pass

class Engineer(EmployeeType):
    def __str__(self):
        return "engineer"

class Manager(EmployeeType):
    def __str__(self):
        return "manager"

class Employee:
    def __init__(self, name, type_code):
        self._name = name
        self._type = self._create_type(type_code)

    @staticmethod
    def _create_type(type_code):
        match type_code:
            case "engineer": return Engineer()
            case "manager": return Manager()
            case _: raise ValueError(f"Unknown type: {type_code}")
```

### Remove Subclass

**Motivation:** When subclasses no longer justify their complexity (e.g., they've been refactored down to just a type code), fold them back into the superclass. The inverse of Replace Type Code with Subclasses.

### Extract Superclass

**Motivation:** When two classes do similar things, create a superclass and pull up the common features.

```python
# Before — two unrelated classes with similar fields/methods
class Department:
    def __init__(self, name, staff):
        self._name = name
        self._staff = staff

    @property
    def total_annual_cost(self):
        return sum(e.annual_cost for e in self._staff)

    @property
    def head_count(self):
        return len(self._staff)

class Employee:
    def __init__(self, name, id_, annual_cost):
        self._name = name
        self._id = id_
        self._annual_cost = annual_cost

# After — common name and annual cost pulled into Party superclass
class Party:
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def annual_cost(self):
        raise NotImplementedError
```

**Alternative:** If you don't want or can't use inheritance, **Extract Class** and use delegation instead.

### Collapse Hierarchy

**Motivation:** When a superclass and subclass are no longer sufficiently different, merge them into one class.

### Replace Subclass with Delegate

**Motivation:** Inheritance has limitations: a class can only vary on one axis, and it creates tight coupling between parent and child. Delegation provides the same behavior variation with more flexibility.

**When to prefer delegation over inheritance:**
- The object needs to vary on multiple independent axes
- The "type" can change at runtime (you can swap a delegate, but you can't change an object's class)
- You want to avoid coupling to the superclass's implementation

**Example — booking with premium variant:**

```python
# Before — inheritance
class Booking:
    def __init__(self, show, date):
        self._show = show
        self._date = date

class PremiumBooking(Booking):
    def __init__(self, show, date, extras):
        super().__init__(show, date)
        self._extras = extras

    @property
    def has_talkback(self):
        return self._show.has_talkback

    @property
    def base_price(self):
        return round(super().base_price + self._extras.premium_fee)

# After — delegation
class Booking:
    def __init__(self, show, date):
        self._show = show
        self._date = date
        self._premium_delegate = None

    def be_premium(self, extras):
        self._premium_delegate = PremiumBookingDelegate(self, extras)

    @property
    def has_talkback(self):
        if self._premium_delegate:
            return self._premium_delegate.has_talkback
        return self._show.has_talkback and not self._is_peak_day

    @property
    def base_price(self):
        result = self._show.price[self._date]  # base calculation
        if self._premium_delegate:
            result = self._premium_delegate.extend_base_price(result)
        return result


class PremiumBookingDelegate:
    def __init__(self, host_booking, extras):
        self._host = host_booking
        self._extras = extras

    @property
    def has_talkback(self):
        return self._host._show.has_talkback

    def extend_base_price(self, base):
        return round(base + self._extras.premium_fee)
```

**Bird hierarchy example** demonstrates the same pattern: replacing a class hierarchy (EuropeanSwallow, AfricanSwallow, NorwegianBlueParrot) with a single Bird class that delegates species-specific behavior to SpeciesDelegate subclasses. The factory function creates the appropriate delegate.

### Replace Superclass with Delegate

**Motivation:** When inheritance creates problems — the subclass doesn't really want *all* the superclass behavior (Refused Bequest), or the semantic "is-a" relationship is misleading. Classic example: a `Stack` shouldn't inherit from `List` because stacks don't support arbitrary list operations.

```python
# Before — Scroll inherits from CatalogItem, but it's a stretch
class CatalogItem:
    def __init__(self, id_, title, tags):
        self._id = id_
        self._title = title
        self._tags = tags

class Scroll(CatalogItem):
    def __init__(self, id_, title, tags, date_last_cleaned):
        super().__init__(id_, title, tags)
        self._last_cleaned = date_last_cleaned

# After — Scroll delegates to CatalogItem
class Scroll:
    def __init__(self, id_, catalog_item, date_last_cleaned):
        self._id = id_
        self._catalog_item = catalog_item
        self._last_cleaned = date_last_cleaned

    @property
    def title(self):
        return self._catalog_item.title

    @property
    def tags(self):
        return self._catalog_item.tags

    def has_tag(self, tag):
        return tag in self._catalog_item.tags
```

**Fowler's advice on inheritance vs. delegation:**

> "Favor a judicious mixture of composition and inheritance over either alone, and always be ready to change your mind."

Use inheritance when the relationship genuinely is-a and the subclass wants all the superclass behavior. Use delegation when the relationship is more "uses-a" or "has-a", or when inheritance creates coupling problems. The refactorings in this chapter make it straightforward to switch between the two as your understanding evolves.

---

# Book6 - Fundamentals of Data Engineering — Summary
### Joe Reis & Matt Housley (O'Reilly, 2022)

> **Context**: This summary is tailored for a team migrating on-prem pipelines (Excel files on shared network drives, Autosys/.jil orchestration) to a cloud-native architecture (AWS S3 / Postgres, Airflow orchestration, EKS deployment). Sections less relevant to this context are trimmed or omitted.

---

# Part I: Foundation and Building Blocks

---

## Chapter 1: Data Engineering Described

### What Is Data Engineering?

#### Data Engineering Defined

- **Data engineering**: The development, implementation, and maintenance of systems and processes that take in raw data and produce high-quality, consistent information for downstream use cases (analytics, ML).
- **Data engineer**: Manages the data engineering lifecycle — from getting data from source systems to serving data for end use cases.
- DE sits at the intersection of: **security, data management, DataOps, data architecture, orchestration, and software engineering**.

#### The Data Engineering Lifecycle

Five stages, plus undercurrents that cut across all stages:

```
Stages:          Generation → Ingestion → Transformation → Serving
                                   ↕
                               Storage (underlies all)

Outputs:         Analytics | Machine Learning | Reverse ETL

Undercurrents:   Security | Data Management | DataOps |
                 Data Architecture | Orchestration | Software Engineering
```

**See Figure 1-1 for the canonical data engineering lifecycle diagram.**

#### Evolution of the Data Engineer

| Era | Key Developments |
|---|---|
| **1980–2000** | Data warehousing, SQL, Kimball/Inmon modeling, MPP databases, BI |
| **2000s** | Big data era begins — Hadoop, MapReduce, commodity hardware, AWS launches |
| **2010s** | Big data engineering — Spark, Kafka, streaming, code-first culture, open source explosion |
| **2020s** | Data lifecycle engineering — managed services, abstraction, modern data stack, DataOps, governance |

- The modern data engineer is a **data lifecycle engineer** — focused higher in the value chain on management, architecture, orchestration, and governance rather than low-level infrastructure.
- The term "big data" is passé; the tooling has been democratized and absorbed into standard DE practice.

#### Data Engineering and Data Science

- DE is **upstream** from data science/analytics. DE provides the inputs that data scientists convert into value.
- **See Figure 1-5 (Data Science Hierarchy of Needs)**: DS teams spend 70–80% of time on data collection, cleaning, and prep. Good DE frees them to focus on modeling and analysis.

### Data Engineering Skills and Activities

#### Data Maturity and the Data Engineer

**Data maturity** = the progression toward higher data utilization, capabilities, and integration across the org. Three stages:

| Stage | Characteristics | DE Focus |
|---|---|---|
| **1. Starting with data** | Fuzzy goals, small team, ad hoc requests | Get buy-in, define architecture, build foundations, avoid undifferentiated heavy lifting |
| **2. Scaling with data** | Formal practices, growing pipelines, specialist roles | Establish formal data practices, adopt DevOps/DataOps, build scalable architecture |
| **3. Leading with data** | Self-service analytics, seamless new data intro, automation | Automation, custom tooling for competitive advantage, data governance, DataOps |

> **Relevant to your migration**: You're moving from Stage 1→2 territory. Focus on formalizing practices, choosing scalable architecture, and avoiding custom builds where off-the-shelf solutions exist.

#### Type A vs Type B Data Engineers

- **Type A (Abstraction)**: Uses managed services and off-the-shelf tools. Avoids reinventing the wheel. Works at all maturity levels.
- **Type B (Build)**: Builds custom data tools and systems for competitive advantage. More common at stages 2–3.

> **For your team**: Default to Type A. Use managed services (Airflow on MWAA/Cloud Composer or self-hosted on EKS, S3 for object storage, RDS Postgres). Only build custom when it provides clear competitive advantage for portfolio optimization workflows.

### Data Engineers Inside an Organization

- **Internal-facing DE**: Maintains pipelines and warehouses for BI, reports, DS, ML (this is your team).
- **External-facing DE**: Builds systems for customer-facing applications.
- Key upstream stakeholders: software engineers, data architects, DevOps/SREs.
- Key downstream stakeholders: data analysts, data scientists, ML engineers.

---

## Chapter 2: The Data Engineering Lifecycle

### What Is the Data Engineering Lifecycle?

The lifecycle stages turn raw data into useful end products:

1. **Generation** — Source systems produce data
2. **Storage** — Data is persisted for use
3. **Ingestion** — Data is moved from source to storage
4. **Transformation** — Data is changed into useful form
5. **Serving** — Data is made available for analytics, ML, reverse ETL

Storage underpins all stages. The stages are not strictly linear — they overlap, repeat, and interweave.

### Generation: Source Systems

- **Source system**: The origin of data (application database, IoT device, message queue, spreadsheet, API, etc.).
- You typically don't own or control source systems — maintain open communication with source system owners.
- Key evaluation questions for source systems:
  - Data persistence model? Rate of generation? Schema type (fixed vs schemaless)?
  - Data quality/consistency? Duplicate handling? Late-arriving data?
  - Will reading from it impact its performance? How are schema changes communicated?

> **Your context**: Current source systems are Excel files on a shared network drive. This is a classic file-based source system with slow access and no schema enforcement.

### Storage

- Cloud architectures often leverage **multiple** storage solutions simultaneously.
- Key evaluation questions:
  - Read/write speed compatibility? Will it bottleneck downstream?
  - Can it scale? Does it support complex queries or just raw storage?
  - Are you capturing metadata, lineage, schema evolution?

#### Understanding Data Access Frequency

- **Hot data**: Frequently accessed (e.g., serving user requests) — fast storage.
- **Lukewarm data**: Accessed periodically (weekly/monthly reports).
- **Cold data**: Rarely queried, archived for compliance — cheap storage, expensive retrieval (e.g., S3 Glacier).

### Ingestion

- Source systems and ingestion are the most common bottlenecks in the lifecycle.
- Key questions: Use case? Frequency? Volume? Format? Quality?

#### Batch vs Streaming

- **Batch**: Process data in chunks at scheduled intervals. Default for most analytics/ML use cases. Simpler and cheaper.
- **Streaming**: Continuous, near-real-time. Adopt only when business use case justifies the added complexity.
- Many frameworks (Spark, Flink) handle both batch and micro-batch.

#### Push vs Pull

- **Push**: Source writes to a target (database, object store, filesystem).
- **Pull**: Ingestion system queries source on schedule (traditional ETL).
- **CDC (Change Data Capture)**: Can be push (trigger-based, log-based) or pull (timestamp-based queries). Log-based CDC adds minimal load to source DB.

### Transformation

- Converts raw data to useful forms for downstream consumption.
- Early transformations: type casting, format standardization, deduplication.
- Later transformations: schema normalization, aggregation, featurization for ML.
- **Business logic** is a major driver — data modeling translates business rules into reusable patterns.

### Serving Data

- **Analytics**: BI (historical), operational analytics (real-time), embedded analytics (customer-facing).
- **Machine Learning**: Feature engineering, model training data.
- **Reverse ETL**: Feeding processed data back into source systems (e.g., scored models → CRM).
- Data has **value** only when it's consumed. Avoid "data vanity projects."

### Major Undercurrents Across the Data Engineering Lifecycle

#### Security

- **Principle of least privilege**: Give users/systems only the access they need, nothing more.
- Antipattern: Giving admin access to all users. Catastrophe waiting to happen.
- Security is about people, process, and technology. Culture of security first.
- Protect data in flight and at rest (encryption, tokenization, masking).
- Know IAM, network security, password policies, and encryption.

#### Data Management

Key facets:

- **Data governance**: Discoverability, security, accountability. Core categories: data quality, metadata, privacy.
- **Metadata**: Four types:
  - *Business metadata*: Business definitions, rules, data owners.
  - *Technical metadata*: Schema, data lineage, pipeline workflows.
  - *Operational metadata*: Job IDs, runtime logs, process results.
  - *Reference metadata*: Lookup data (codes, standards, calendars).
- **Data quality**: Accuracy, completeness, timeliness. Test and monitor proactively.
- **Master data management (MDM)**: Golden records — consistent entity definitions across the org.
- **Data modeling**: Converting data into usable form. Kimball, Inmon, Data Vault are key patterns (covered in Ch 8).
- **Data lineage**: Audit trail of data through its lifecycle — critical for debugging and compliance.
- **Data lifecycle management**: Archival, retention, destruction policies. Cloud makes this easier with tiered storage classes but pay-as-you-go means CFOs watch storage costs closely.

#### DataOps

Combines Agile, DevOps, and statistical process control (SPC) for data products. Three pillars:

1. **Automation**: CI/CD for data pipelines, environment management, configuration as code.
2. **Observability and monitoring**: Detect data quality issues, stale data, pipeline failures before stakeholders do. Apply SPC. Related concept: **DODD (Data Observability Driven Development)** — like TDD for data.
3. **Incident response**: Rapid root cause identification, blameless communication, proactive issue detection.

> **Automation maturity progression** (highly relevant to your migration):
> 1. Cron jobs → fragile, no dependency awareness
> 2. Orchestration framework (Airflow) → dependency-aware DAGs, alerting, backfill
> 3. Automated DAG deployment with testing → CI/CD for DAGs, validated before deploy
> 4. Full DataOps → metadata-driven DAGs, automated quality checks, lineage tracking

#### Orchestration

- **Orchestration** ≠ scheduling. An orchestrator manages **job dependencies** via DAGs. A scheduler (cron) just triggers at fixed times.
- DAGs can be run once or on schedule (daily, hourly, etc.).
- Orchestration systems provide: dependency management, job history, visualization, alerting, backfill capability.
- **Airflow**: Open-sourced by Airbnb in 2014, written in Python. Highly extensible. Mindshare leader. Alternatives: Prefect, Dagster (better metadata/portability/testability), Argo (K8s-native).

```python
# Conceptual Airflow DAG structure
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

with DAG("etl_pipeline", start_date=datetime(2024, 1, 1), schedule="@daily") as dag:

    def extract():
        # Pull data from source (e.g., read from S3 or query source DB)
        ...

    def transform():
        # Apply business logic, clean data, reshape
        ...

    def load():
        # Write to destination (S3, Postgres, data warehouse)
        ...

    t1 = PythonOperator(task_id="extract", python_callable=extract)
    t2 = PythonOperator(task_id="transform", python_callable=transform)
    t3 = PythonOperator(task_id="load", python_callable=load)

    t1 >> t2 >> t3  # Dependency chain
```

#### Software Engineering

- Core data processing code (SQL, Spark, Python) remains essential.
- **Testing**: Unit, regression, integration, end-to-end, smoke tests — all apply to data pipelines.
- **Infrastructure as code (IaC)**: Terraform, Helm, CloudFormation. Manage cloud infra declaratively.
- **Pipelines as code**: DAGs defined in Python/code. Core concept in modern orchestration.
- **Streaming**: Windowing methods, joins in real-time, function platforms (Lambda, Flink).

---

## Chapter 3: Designing Good Data Architecture

### What Is Data Architecture?

- **Data architecture**: The design of systems to support the evolving data needs of an enterprise, achieved through **flexible and reversible decisions** reached through careful **evaluation of trade-offs**.
- Distinct from but related to **enterprise architecture** (TOGAF, Gartner, EABOK frameworks).
- Has two components:
  - **Operational architecture**: *What* needs to be done (functional requirements).
  - **Technical architecture**: *How* it will happen (systems, technologies, implementation).

#### "Good" Data Architecture

- Serves business requirements with reusable building blocks while maintaining flexibility.
- Key distinguishing trait: **agility** — ability to respond to changes in business and technology.
- Bad data architecture: tightly coupled, rigid, overly centralized, or "accidentally" architected.

### Principles of Good Data Architecture

#### Principle 1: Choose Common Components Wisely

- Common components = shared building blocks across the org (object storage, event-streaming platforms, version control, observability).
- Should be accessible and understandable. Keep them simple and avoid customization that creates technical debt.

#### Principle 2: Plan for Failure

- Availability = percentage of time a system is operational (e.g., 99.99% = ~52 min downtime/year).
- **Reliability**: System performs function correctly. **Durability**: Data survives intact.
- Design for failure: redundancy, graceful degradation, self-healing, automated recovery.

#### Principle 3: Architect for Scalability

- **Scaling up** (vertical): Bigger machine. **Scaling out** (horizontal): More machines.
- **Elasticity**: Dynamically scale with demand. Cloud-native advantage.

#### Principle 4: Architecture Is Leadership

- Architects mentor, collaborate, and guide. Not ivory tower — hands-on influence.

#### Principle 5: Always Be Architecting

- Architecture is never "done." Iterate continuously.

#### Principle 6: Build Loosely Coupled Systems

- Systems should be independent, able to change without cascading effects.
- Modular, well-defined interfaces between components.
- Opposite of tightly coupled monolith where changing one component breaks everything.

#### Principle 7: Make Reversible Decisions

- **Two-way doors** (easily reversible): Preferred. Try things, revert if needed.
- **One-way doors** (irreversible): Proceed with great caution.
- Cloud environments favor two-way doors — spin up, test, tear down.

> **Relevant to your S3 vs Postgres decision**: This is a two-way door. You can start with S3 (file-based, familiar to your team) and add Postgres later. Or use both — S3 for raw/landing zone, Postgres for curated/queried data. The hybrid approach is low-risk and reversible.

#### Principle 8: Prioritize Security

- Bake security into every layer. Hardened defaults, principle of least privilege, encryption at rest and in transit.

#### Principle 9: Embrace FinOps

- **FinOps**: Cloud financial operations. Monitor spend, optimize costs, allocate by team/project.
- Cloud costs are operational (OpEx), not capital (CapEx). Track and attribute them.

### Major Architecture Concepts

#### Domains and Services

- **Domain**: A real-world subject area with its own data, rules, and logic (e.g., "portfolio management," "trading").
- **Service**: A set of functionality in a domain, accessed via a well-defined interface.

#### Distributed Systems, Scalability, and Designing for Failure

- Horizontal scaling distributes load but introduces complexity (CAP theorem, network partitions).
- Design for failure at every level.

#### Tight vs Loose Coupling: Tiers, Monoliths, and Microservices

- **Monolith**: Single deployment unit. Simple but hard to scale independently.
- **Microservices**: Independent, loosely coupled services. Flexible but complex.
- **Practical middle ground**: Start monolithic, extract services when clear boundaries emerge.

#### Event-Driven Architecture

- Systems communicate via events rather than direct calls.
- Great for decoupling, real-time processing, and audit trails.

#### Brownfield vs Greenfield Projects

- **Brownfield**: Working within existing systems (your migration — existing Autosys, Excel-based pipelines).
- **Greenfield**: Starting from scratch.
- Brownfield requires understanding legacy constraints, incremental migration, running old and new in parallel.

> **Your migration strategy** (brownfield approach): Keep on-prem running, add S3/Postgres writes to production pipeline, build cloud pipeline on feature branch, validate, cutover.

### Examples and Types of Data Architecture

#### Data Warehouse

- Centralized, highly structured repository for analytical data.
- Uses schema-on-write — data conforms to schema upon loading.
- Optimized for complex queries and aggregations (OLAP).
- Cloud warehouses (Snowflake, BigQuery, Redshift) separate compute from storage.

#### Data Lake

- Stores raw data in its native format (schema-on-read).
- Object storage (S3) is the standard substrate.
- Risk: becomes a "data swamp" without governance, metadata, and quality enforcement.

#### Convergence: Data Lakehouse and Data Platform

- **Data Lakehouse**: Combines lake (raw storage, schema-on-read) with warehouse features (ACID transactions, schema enforcement, query optimization). Examples: Delta Lake, Apache Iceberg, Apache Hudi.
- **Data Platform**: Umbrella term for the full stack — lake + warehouse + processing + governance + serving.

#### Modern Data Stack

- Collection of cloud-native, modular, plug-and-play tools.
- Typical components: Fivetran (ingestion) → Snowflake (warehouse) → dbt (transformation) → Looker (BI) → Airflow (orchestration).

#### Lambda Architecture

- Parallel **batch layer** (full reprocessing) and **speed layer** (real-time) with a **serving layer** merging results.
- Complexity: Maintaining two separate codepaths. Falling out of favor.

#### Kappa Architecture

- Streaming-only. All data treated as streams. Simpler than Lambda but requires mature streaming infra.

#### Data Mesh

- Decentralized, domain-oriented architecture.
- Four principles:
  1. **Domain-oriented ownership**: Each domain team owns its data end-to-end.
  2. **Data as a product**: Each domain exposes curated "data products" with SLAs.
  3. **Self-serve data platform**: Central platform team provides infrastructure as a service.
  4. **Federated computational governance**: Standards enforced computationally across domains.

---

## Chapter 4: Choosing Technologies Across the Data Engineering Lifecycle

### Key Evaluation Criteria

| Factor | Question to Ask |
|---|---|
| **Team size & capabilities** | Can your team realistically learn and maintain this technology? |
| **Speed to market** | How quickly can you deliver value? |
| **Interoperability** | Does it play well with your other tools? |
| **Cost optimization** | TCO (total cost of ownership) + opportunity cost? |
| **FinOps** | Can you monitor and control cloud spend? |

### Today vs Future: Immutable vs Transitory Technologies

- **Immutable technologies**: SQL, object storage, Linux, networking fundamentals — learn these deeply.
- **Transitory technologies**: Specific vendors, frameworks, SaaS tools — change rapidly.
- Focus on understanding the immutables. Choose transitory tech based on current needs.

### Location

#### On Premises

- You own hardware, network, physical security. High upfront CapEx.
- Limitations: slow provisioning, finite capacity, hard to scale dynamically.
- **Your current state**: Autosys on-prem, shared network drives, Excel files.

#### Cloud

- Pay-as-you-go, elastic scaling, managed services.
- **IaaS**: VMs, raw compute (EC2). **PaaS**: Managed services (RDS, S3). **SaaS**: Fully managed applications (Snowflake).
- Cloud-native advantages: separation of compute and storage, auto-scaling, global availability.

#### Hybrid Cloud

- Mix of on-prem and cloud. **Your migration approach** — run on-prem and cloud in parallel during transition.

### Build vs Buy

- **Default to buy (managed services)** unless custom build provides clear competitive advantage.
- **Open source**: Free licensing but not free to operate. Consider operational burden (patching, scaling, debugging).
- **Managed open source**: Best of both worlds (e.g., Amazon MWAA for Airflow, Amazon RDS for Postgres).

> **For your team**: Use managed Airflow (MWAA) or self-host on EKS via Helm chart. Use RDS Postgres (managed) instead of running Postgres yourself on EC2. Use S3 natively (zero ops burden).

### Monolith vs Modular

- **Monolith**: Single system does everything. Simple at first, hard to evolve.
- **Modular**: Compose best-of-breed tools. More flexible, but integration complexity.
- **Distributed monolith**: Worst of both worlds — "microservices" that are actually tightly coupled.

> **Recommended**: Modular approach. S3 (storage) + Postgres (queryable store) + Airflow (orchestration) + Python (processing). Loosely coupled, replaceable components.

### Serverless vs Servers

- **Serverless** (Lambda, Fargate): No server management, scale-to-zero, pay per invocation. Good for event-driven and sporadic workloads.
- **Containers** (EKS/K8s): You manage the cluster. Good for long-running, complex workloads.
- Serverless for simple tasks (triggers, small transforms). Containers for heavy processing (your existing K8s expertise on EKS).

### Orchestration Example: Airflow

- Airflow as the de facto standard for batch orchestration.
- DAG-based dependency management replaces Autosys .jil files.
- Key benefits over Autosys: Python-native DAG definitions, built-in dependency resolution, web UI for monitoring, backfill capability, rich ecosystem of operators/hooks.

---

# Part II: The Data Engineering Lifecycle in Depth

---

## Chapter 5: Data Generation in Source Systems

### Sources of Data: How Is Data Created?

- Data originates as analog or digital signals, then flows into systems.
- Know your source systems deeply — patterns, quirks, volumes, frequencies.

### Source Systems: Main Ideas

#### Files and Unstructured Data

- Files (CSV, Excel, JSON, XML, etc.) are the universal exchange medium between organizations.
- **Your current state**: Excel files on shared network drive = file-based source system.

#### APIs

- Standard method for inter-system data exchange. REST, GraphQL, gRPC.
- Despite frameworks, maintaining API connections often requires ongoing engineering effort.

#### Application Databases (OLTP Systems)

- Store application state (e.g., account balances). Optimized for high-throughput reads/writes.
- **ACID properties**: Atomicity, Consistency, Isolation, Durability — guarantee transaction reliability.

#### Online Analytical Processing (OLAP) Systems

- Optimized for complex queries, aggregations, historical analysis. Column-oriented storage.
- May serve as source system if you're reading from another team's warehouse.

#### Change Data Capture (CDC)

- Tracks changes (inserts, updates, deletes) in a source database.
- Methods: timestamp-based (pull), trigger-based (push), log-based (push, minimal source load).
- **Log-based CDC** (e.g., Debezium reading Postgres WAL) is preferred — minimal impact on source DB.

#### Logs

- Application and system logs are a critical data source. Often semi-structured (JSON, key-value).
- **Database logs**: Transaction logs (WAL in Postgres) are the basis for log-based CDC.

#### CRUD and Insert-Only Patterns

- **CRUD**: Create, Read, Update, Delete. Standard mutable pattern.
- **Insert-only (append-only)**: Never update/delete — only insert new records. Creates natural audit trail. Used in event sourcing and streaming.

#### Messages and Streams

- **Message queue**: Asynchronous communication between systems. Messages consumed and deleted.
- **Event stream**: Append-only log of events. Can be replayed. Retained for a configurable period.
- Key platforms: Apache Kafka, AWS Kinesis, Google Pub/Sub, Apache Pulsar.

#### Types of Time

- **Event time**: When the event actually occurred.
- **Ingestion time**: When the data was ingested into the pipeline.
- **Processing time**: When the data was processed/transformed.
- Understanding the difference is critical for correct analytics and handling late-arriving data.

### Source System Practical Details

#### Databases

- **Relational (RDBMS)**: Tables with rows and columns. Schema-enforced. Strong for structured data. (Postgres, MySQL, Oracle).
- **NoSQL**: Key-value (DynamoDB), document (MongoDB), wide-column (Cassandra), graph (Neo4j).
- **Considerations**: Connection management, query load on source DB, change tracking strategy.

#### APIs

- REST (most common), GraphQL (flexible queries), Webhooks (push-based), gRPC (high-performance).

#### Message Queues and Event-Streaming Platforms

- **Kafka**: Distributed event-streaming platform. Topics, partitions, consumer groups. High throughput, durable, replayable.
- **Cloud equivalents**: Kinesis (AWS), Pub/Sub (GCP).

### Undercurrents and Their Impact on Source Systems

- **DataOps**: Track data quality at the source. Metadata collection.
- **Orchestration**: Coordinate ingestion jobs and dependency chains.
- **Software engineering**: Version control source definitions, test data contracts.

---

## Chapter 6: Storage

### Raw Ingredients of Data Storage

#### Magnetic Disk Drive (HDD)

- Sequential reads fast, random access slow. Cheap per GB.

#### Solid-State Drive (SSD)

- Much faster random access. More expensive. Wear leveling limits write cycles.

#### Random Access Memory (RAM)

- Orders of magnitude faster than disk. Volatile. Used for caching and in-memory processing.

#### Serialization

- **Definition**: Encoding data structures into byte sequences for storage or transmission.
- **Row-oriented**: CSV, JSON, Avro — good for transactional workloads (write-heavy).
- **Column-oriented**: Parquet, ORC — good for analytical workloads (read/scan-heavy, compressible).

> **For your team**: Migrate Excel files to **Parquet on S3** for analytical workloads (columnar, compressed, fast reads) or **insert into Postgres** for queryable structured data.

#### Compression

- Reduces storage cost and I/O. Common algorithms: gzip, Snappy (fast), Zstandard (good ratio), LZ4 (fastest).
- Parquet and ORC have built-in compression support.

#### Caching

- Frequently accessed data kept in faster storage layer (RAM, SSD). Critical for hot data serving.

### Data Storage Systems

#### Single Machine vs Distributed Storage

- Single machine: simpler but limited. Distributed: scales but introduces consistency challenges.
- **CAP Theorem**: Distributed systems can guarantee at most 2 of 3: Consistency, Availability, Partition tolerance.

#### Eventual vs Strong Consistency

- **Strong consistency**: Reads always return latest write. Higher latency.
- **Eventual consistency**: Reads may return stale data temporarily. Lower latency, higher availability. (S3 now offers strong read-after-write consistency.)

#### File Storage

- Traditional hierarchical filesystem (directories and files). Network file storage (NFS, SMB/CIFS).
- **Your current state**: Shared network drive = network file storage. Slow access, no metadata, no versioning.
- Cloud file storage exists (EFS, FSx) but object storage (S3) is usually the better choice for data engineering.

#### Block Storage

- Raw storage blocks (EBS, local SSD). Used as underlying storage for databases and VMs.
- Not directly used in data pipelines — but your Postgres database sits on block storage.

#### Object Storage

- **Key-value store**: Objects addressed by key (path). Flat namespace (though `/` simulates hierarchy).
- **S3**: The de facto standard for cloud data storage. Highly durable (99.999999999% — "11 nines"), massively scalable, cheap.
- **Ideal for**: Data lakes, landing zones, raw/archive data, Parquet/CSV/JSON files.
- **Not ideal for**: Low-latency random access, transactional workloads (use a database instead).
- **Antipattern**: Using S3 for high-rate random-access updates (it's optimized for large sequential reads/writes).

```python
# Example: Writing a Pandas DataFrame to S3 as Parquet
import boto3
import pandas as pd
import io

df = pd.DataFrame({"portfolio_id": [1, 2], "nav": [1000000.5, 2500000.3]})

# Write to Parquet in-memory, then upload to S3
buffer = io.BytesIO()
df.to_parquet(buffer, engine="pyarrow", index=False)
buffer.seek(0)

s3 = boto3.client("s3")
s3.put_object(Bucket="my-data-lake", Key="curated/portfolios/2024-01-15.parquet", Body=buffer)
```

```python
# Example: Writing to Postgres
import psycopg2
from io import StringIO

conn = psycopg2.connect("host=mydb.rds.amazonaws.com dbname=analytics user=etl_user")
cur = conn.cursor()

# Use COPY for bulk loading (much faster than INSERT for large batches)
buffer = StringIO()
df.to_csv(buffer, index=False, header=False)
buffer.seek(0)

cur.copy_expert("COPY portfolios FROM STDIN WITH CSV", buffer)
conn.commit()
```

#### Cache and Memory-Based Storage Systems

- Redis, Memcached — for sub-millisecond access to frequently queried data.

#### Indexes, Partitioning, and Clustering

- **Index**: Data structure that speeds up lookups on specific columns (B-tree, hash, bitmap).
- **Partitioning**: Splitting data into segments by a key (date, region). Reduces scan scope.
- **Clustering**: Physically ordering data on disk to match a common access pattern.

> **S3 "partitioning"**: Achieved via key prefix naming convention:
> ```
> s3://my-bucket/raw/portfolios/year=2024/month=01/day=15/data.parquet
> ```
> This enables efficient prefix-based listing and integrates with tools like Athena, Spark, Hive.

### Data Engineering Storage Abstractions

#### The Data Warehouse

- Central, highly curated, schema-enforced analytical store.
- Cloud warehouses (Snowflake, BigQuery, Redshift) separate compute from storage.

#### The Data Lake

- Raw storage in native format on object storage (S3). Schema-on-read.
- Risk of "data swamp" without governance. Need metadata management.

#### The Data Lakehouse

- Adds ACID transactions, schema enforcement, and time travel to data lake.
- Technologies: **Delta Lake**, **Apache Iceberg**, **Apache Hudi**.
- Enables warehouse-like queries directly on S3 data.

#### Stream-to-Batch Storage Architecture

- Streaming data lands in an event platform (Kafka), then is periodically materialized to object storage (S3) or a warehouse in batch windows.

### Big Ideas and Trends in Storage

#### Separation of Compute from Storage

- **Core cloud-native pattern**: Storage (S3) is decoupled from compute (Spark on EMR, Athena, etc.).
- Scale storage and compute independently. Pay for each separately.
- Enables multiple compute engines to query the same data (Spark, Presto, Athena, Redshift Spectrum).

> **Highly relevant to your architecture**: S3 as storage layer + multiple compute engines. EKS pods can read from S3 directly. Postgres handles structured queries. No need to pick one — use both.

#### Data Storage Lifecycle and Data Retention

- Define retention policies. Cloud storage tiers reduce cost for aging data:
  - S3 Standard → S3 Infrequent Access → S3 Glacier → Glacier Deep Archive.
- Automate lifecycle transitions with S3 Lifecycle Rules.

---

## Chapter 7: Ingestion

### What Is Data Ingestion?

- Moving data from source systems into the data engineering lifecycle.
- **Data pipeline**: The combination of architecture, systems, and processes that move data through lifecycle stages. Intentionally flexible definition.

### Key Engineering Considerations for the Ingestion Phase

#### Bounded vs Unbounded Data

- **Bounded**: Finite dataset (e.g., a daily CSV export, a database table snapshot).
- **Unbounded**: Continuous stream of data with no defined end (e.g., Kafka topic, IoT sensor feed).
- Batch processing inherently treats data as bounded. Streaming handles unbounded data.

#### Frequency

- How often should data be updated? Real-time? Hourly? Daily?
- **Your context**: Currently batch (Autosys schedules). Airflow will maintain batch cadence but with better dependency management. Consider whether any pipelines benefit from more frequent updates.

#### Synchronous vs Asynchronous Ingestion

- **Synchronous**: Source sends data and waits for acknowledgment. Tightly coupled.
- **Asynchronous**: Source fires and forgets (or relies on a queue/buffer). Decoupled, more resilient.
- Prefer async ingestion for pipeline decoupling and fault tolerance.

#### Serialization and Deserialization

- Data must be serialized for transmission and deserialized upon receipt.
- Format compatibility between source and destination matters (CSV → Parquet conversion, JSON parsing, etc.).

#### Throughput and Scalability

- Design ingestion to handle peak loads, not just average.
- Use buffering (queues, object storage) to absorb spikes.

#### Reliability and Durability

- Can you replay failed ingestion? Is data buffered safely?
- **At-least-once** delivery is common (handle deduplication downstream).
- **Exactly-once** delivery is the gold standard but harder to achieve.

#### Push vs Pull Patterns

- **Push**: Source writes data to target. Examples: Webhooks, database-triggered CDC, sensor → message queue.
- **Pull**: Ingestion system queries source on schedule. Examples: Scheduled API polls, `SELECT *` from source DB.

### Batch Ingestion Considerations

#### Snapshot vs Differential Extraction

- **Snapshot (full extract)**: Grab entire dataset each time. Simple but expensive for large datasets.
- **Differential (incremental)**: Only grab what changed since last extraction. More efficient, more complex.

> **Your migration**: Currently likely doing full Excel file reads. As you move to Postgres/S3, implement incremental extraction using timestamps or CDC.

#### File-Based Export and Ingestion

- Export data to files (CSV, Parquet), transfer to target storage.
- Simple, reliable, battle-tested. Works well with S3 as landing zone.

> **Your pattern**: Excel → Python → Parquet → S3 (or directly to Postgres via COPY).

#### ETL vs ELT

- **ETL (Extract, Transform, Load)**: Transform before loading. Traditional on-prem approach.
- **ELT (Extract, Load, Transform)**: Load raw, transform in place. Cloud-native approach — leverage cheap storage and powerful cloud compute.
- **ELT is the modern default** — land raw data in S3/warehouse, then transform using SQL/Spark/dbt.

```
# ETL (traditional — your current on-prem approach)
Source → [Python transform on local server] → Destination

# ELT (cloud-native — your target state)
Source → [Land raw in S3] → [Transform with Spark/SQL/dbt] → Curated in S3/Postgres
```

#### Data Migration

- Moving data from one system to another (your exact project).
- Key principles: run old and new in parallel, validate data parity, cutover when confident.

### Message and Stream Ingestion Considerations

- **Schema evolution**: Handle backward/forward compatible schema changes (Avro schema registry).
- **Late-arriving data**: Define SLAs for acceptable lateness. Decide how to handle late records.
- **Ordering and deduplication**: Distributed systems don't guarantee order. Handle at consumer side.
- **Dead-letter queues (DLQ)**: Failed messages routed to a separate queue for manual inspection.
- **Replay**: Ability to re-consume historical messages (Kafka supports this with retention).

### Ways to Ingest Data

#### Direct Database Connection

- Query source DB directly (JDBC/ODBC). Simple but puts load on source.
- Use read replicas or off-peak windows to minimize impact.

#### Change Data Capture (CDC)

- Log-based CDC (Debezium) reads database transaction logs. Minimal source impact, near-real-time.
- Recommended for database-to-database or database-to-stream ingestion.

#### APIs

- REST polling, webhook push, GraphQL subscriptions.
- Watch for rate limits, pagination, auth token management.

#### Message Queues and Event-Streaming Platforms

- Kafka, Kinesis, Pub/Sub for real-time data ingestion.

#### Managed Data Connectors

- Fivetran, Airbyte, Stitch — managed ELT tools that handle source→destination pipelines.
- Good for reducing engineering effort on commoditized integrations.

#### Moving Data with Object Storage

- Upload files to S3, then process. Simple, reliable, decoupled.
- Works well as the **landing zone** pattern.

```
# Landing zone pattern for your migration:
# 1. On-prem pipeline writes to S3 (new step added to existing pipeline)
# 2. Cloud pipeline reads from S3, transforms, loads to Postgres or curated S3
# 3. Both pipelines run in parallel during migration period

# On-prem addition:
import boto3
s3 = boto3.client("s3")
s3.upload_file("output.parquet", "my-landing-zone", "raw/portfolios/2024-01-15.parquet")
```

---

## Chapter 8: Queries, Modeling, and Transformation

### Queries

#### What Is a Query?

- A query retrieves or acts on data. SQL is the primary language.
- SQL categories: **DDL** (CREATE, DROP), **DML** (SELECT, INSERT, UPDATE, DELETE), **DCL** (GRANT, REVOKE), **TCL** (COMMIT, ROLLBACK).

#### The Life of a Query

```
SQL query → Parsing → Bytecode → Query Optimizer → Execution → Results
```

#### The Query Optimizer

- Analyzes query plan and determines most efficient execution strategy.
- Considers: join order, index usage, data scan size, join algorithms.
- Different databases optimize differently — understand your engine's optimizer.

#### Improving Query Performance

- **Optimize joins**: Prejoin frequently combined datasets. Avoid many-to-many explosions.
- **Use CTEs and subqueries wisely**: CTEs improve readability but some engines don't optimize them.
- **Manage data scan size**: Partition data, use columnar formats (Parquet), predicate pushdown.
- **Avoid full table scans**: Use indexes, partition pruning, column projection.
- **Caching**: Materialized views, query result caching.

```sql
-- Example: Partitioned query on S3 data via Athena
-- Only scans the relevant date partition
SELECT portfolio_id, SUM(market_value) as total_mv
FROM portfolio_holdings
WHERE year = '2024' AND month = '01'
GROUP BY portfolio_id;
```

#### Queries on Streaming Data

- Streaming SQL (e.g., Flink SQL, KSQL) operates on unbounded data.
- **Windowing**: Tumbling windows (fixed, non-overlapping), sliding/hopping windows (overlapping), session windows (activity-based).

### Data Modeling

#### What Is a Data Model?

- An abstract representation of data, its relationships, and constraints.
- Serves as a contract between data producers and consumers.

#### Conceptual, Logical, and Physical Data Models

- **Conceptual**: High-level business entities and relationships (no technical detail).
- **Logical**: Detailed structure with attributes and data types (database-agnostic).
- **Physical**: Actual implementation — tables, columns, indexes, partitions (database-specific).

#### Normalization

- **Normalization**: Organizing data to reduce redundancy. Normal forms (1NF through 3NF typically).
  - **1NF**: Atomic values, unique rows.
  - **2NF**: 1NF + no partial dependencies on composite keys.
  - **3NF**: 2NF + no transitive dependencies.
- Fully normalized = minimal redundancy, maximum integrity, but complex joins for analytics.
- **Denormalization**: Intentionally introducing redundancy for query performance. Common in analytics.

#### Techniques for Modeling Batch Analytical Data

**Kimball (Dimensional Modeling)**
- **Star schema**: Central fact table surrounded by dimension tables.
  - **Fact tables**: Quantitative measurements (transactions, events). Grain = level of detail per row.
  - **Dimension tables**: Descriptive attributes (who, what, when, where).
- Simple, intuitive, fast queries. Widely adopted.

```sql
-- Star schema example
-- Fact table: portfolio_holdings (grain: one row per holding per day)
-- Dimensions: dim_portfolio, dim_security, dim_date

SELECT d.date, p.portfolio_name, s.security_name, f.market_value
FROM fact_portfolio_holdings f
JOIN dim_date d ON f.date_key = d.date_key
JOIN dim_portfolio p ON f.portfolio_key = p.portfolio_key
JOIN dim_security s ON f.security_key = s.security_key
WHERE d.date = '2024-01-15';
```

**Inmon (Corporate Information Factory)**
- Top-down approach. Build a normalized enterprise data warehouse (3NF) first, then create dimensional data marts.
- More rigorous, better for complex enterprises, but slower to build.

**Data Vault**
- Hybrid approach designed for agility and auditability.
- Three entity types:
  - **Hubs**: Unique business keys.
  - **Links**: Relationships between hubs.
  - **Satellites**: Descriptive attributes with timestamps (full history).
- Insert-only (append-only), full auditability, parallelizable loading.

**Wide Denormalized Tables**
- Single flat table with many columns. Simple queries (no joins), but can be very wide.
- Popular in data lake environments and for ML feature tables.

> **Recommendation for your team**: Start with **wide denormalized tables** in S3/Parquet for simplicity. If you adopt Postgres for serving, consider a lightweight **star schema** for commonly queried datasets. Full Kimball/Inmon/Data Vault is overkill for your current scale.

### Transformations

#### Batch Transformations

- SQL-based transforms in a warehouse or on files (Spark, dbt, Pandas).
- **dbt (Data Build Tool)**: SQL-first transformation framework. Version-controlled, tested, documented. Widely adopted.

```sql
-- dbt-style transformation example
-- models/curated/portfolio_daily_nav.sql
WITH raw_holdings AS (
    SELECT * FROM {{ ref('stg_portfolio_holdings') }}
),
aggregated AS (
    SELECT
        portfolio_id,
        as_of_date,
        SUM(market_value) AS total_nav,
        COUNT(DISTINCT security_id) AS num_holdings
    FROM raw_holdings
    GROUP BY portfolio_id, as_of_date
)
SELECT * FROM aggregated
```

#### Materialized Views, Federation, and Query Virtualization

- **Materialized view**: Precomputed query result stored physically. Fast reads, must be refreshed.
- **Federation**: Query across multiple data sources as if they were one.
- **Query virtualization**: Virtual tables that execute queries on the fly against underlying sources.

#### Streaming Transformations and Processing

- Apply transforms to data in motion (Kafka Streams, Flink, Spark Structured Streaming).
- Useful for real-time enrichment, filtering, aggregation.

---

## Chapter 9: Serving Data for Analytics, Machine Learning, and Reverse ETL

### General Considerations for Serving Data

#### Trust

- Downstream consumers must trust the data. Trust is built through quality, consistency, and transparency.
- Data quality issues erode trust quickly and are hard to rebuild.

#### What's the Use Case, and Who's the User?

- Understand the consumer: analyst, data scientist, ML pipeline, external customer?
- Tailor serving layer to use case: ad hoc queries, dashboards, model training, API access.

#### Data Products

- A **data product** is a dataset (or data-derived artifact) treated as a product — with SLAs, documentation, ownership, and quality guarantees.

#### Self-Service or Not?

- Self-service analytics: Users access and analyze data without IT help.
- Requires good data quality, documentation, and accessible tools.

#### Data Definitions and Logic

- **Metrics layer / semantic layer**: Centralized definitions of business metrics. Prevents conflicting definitions across teams.

### Analytics

#### Business Analytics (BI)

- Dashboards, reports, ad hoc queries on historical data.
- Tools: Tableau, Power BI, Looker, Metabase.
- Logic-on-read approach: Store data clean but fairly raw, apply business logic at query time via BI tool.

#### Operational Analytics

- Real-time or near-real-time monitoring. Live dashboards, alerting.
- Data consumed directly from streaming sources or near-real-time refreshed tables.

#### Embedded Analytics

- Analytics delivered to external customers within a product.
- Access control is critical — each customer must see only their data (multi-tenancy).

### Machine Learning

- Data engineers provide the infrastructure for ML: feature pipelines, training data management, serving infrastructure.
- **Feature stores**: Centralized repositories for ML features with versioning, sharing, and serving (online + offline).
- Key considerations: Data quality sufficient for features? Data discoverable? Technical/org boundaries between DE and ML clear?

### Ways to Serve Data for Analytics and ML

| Method | Use Case |
|---|---|
| **File exchange (S3)** | Share Parquet/CSV files. Simple. Good for batch ML training. |
| **Database (Postgres, warehouse)** | Structured queries, BI tools, dashboards. |
| **Streaming (Kafka)** | Real-time consumers, event-driven serving. |
| **Query federation** | Query across multiple sources without moving data. |
| **Semantic/metrics layer** | Consistent business definitions across tools. |
| **Notebooks** | Interactive analysis, ad hoc exploration (Jupyter). |

### Reverse ETL

- Pushing processed/enriched data from the analytical layer back to operational systems (CRM, SaaS platforms, production applications).
- Growing practice as companies want to operationalize their analytics.

---

# Part III: Security, Privacy, and the Future of Data Engineering

---

## Chapter 10: Security and Privacy

### People

#### The Power of Negative Thinking

- The weakest link in security is human. Always think through attack and leak scenarios.
- Best way to protect sensitive data: **don't ingest it in the first place** unless there's a real downstream need.

#### Always Be Paranoid

- Verify credential requests. When in doubt, hold off and get second opinions.

### Processes

#### The Principle of Least Privilege

- Every user, service, and system gets the minimum access necessary.
- Applied to: IAM roles, database users, S3 bucket policies, Kubernetes RBAC.

```yaml
# Example: K8s RBAC for a pipeline service account (least privilege)
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: etl-pipeline-role
  namespace: data-pipelines
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["batch"]
  resources: ["jobs"]
  verbs: ["get", "list", "watch", "create"]
```

#### Shared Responsibility in the Cloud

- Cloud provider secures the infrastructure **of** the cloud. You secure everything **in** the cloud.
- You are responsible for: IAM policies, network config, encryption keys, application security, data classification.

#### Always Back Up Your Data

- S3 versioning, cross-region replication, database snapshots (RDS automated backups).
- Test restore procedures regularly.

### Technology

#### Encryption

- **At rest**: S3 SSE (server-side encryption), RDS encryption, EBS encryption.
- **In transit**: TLS/SSL for all network communication. Enforce HTTPS.
- Manage encryption keys via KMS (Key Management Service).

#### Logging, Monitoring, and Alerting

- CloudTrail for API audit logs. CloudWatch for metrics and alarms.
- Monitor: access patterns, unusual queries, failed auth attempts, data egress spikes.

#### Network Access

- VPCs, security groups, NACLs. Minimize public-facing endpoints.
- Use VPC endpoints for S3 and other AWS services (traffic stays within AWS network).

#### Security for Low-Level Data Engineering

- Principle of least privilege for IAM roles attached to EKS pods (IRSA — IAM Roles for Service Accounts).
- Use secrets management (AWS Secrets Manager, HashiCorp Vault) instead of hardcoded credentials.

```python
# Example: Retrieving a database password from AWS Secrets Manager
import boto3
import json

def get_db_credentials(secret_name: str) -> dict:
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])

creds = get_db_credentials("prod/postgres/etl-user")
# creds = {"username": "etl_user", "password": "...", "host": "...", "dbname": "analytics"}
```

---

## Chapter 11: The Future of Data Engineering

### The Data Engineering Lifecycle Isn't Going Away

- The lifecycle stages (generation, storage, ingestion, transformation, serving) are durable concepts.
- Specific tools will change but the lifecycle framework persists.

### The Decline of Complexity and Rise of Easy-to-Use Data Tools

- Abstraction continues. Tools become simpler, more accessible, less ops burden.
- Managed services replace self-hosted infrastructure.

### The Cloud-Scale Data OS and Improved Interoperability

- Cloud is converging toward a "data OS" — interoperable services that compose seamlessly.
- Open table formats (Iceberg, Delta Lake, Hudi) enable interoperability across engines.

### "Enterprisey" Data Engineering

- Governance, quality, lineage, cataloging — once "enterprise-only" practices — are now mainstream.
- Data mesh, data contracts, data products are formalizing these patterns.

### Moving Beyond the Modern Data Stack, Toward the Live Data Stack

- Real-time analytical databases (ClickHouse, Apache Druid, Materialize) enable low-latency analytics.
- Streaming pipelines become first-class alongside batch.
- Tight feedback loops between applications and ML models.

---

# Appendix A: Serialization and Compression Technical Details

### Serialization Formats

| Format | Type | Schema | Use Case |
|---|---|---|---|
| **CSV** | Row | None | Simple interchange, human-readable. Fragile (quoting, encoding issues). |
| **JSON** | Row (semi-structured) | Self-describing | API interchange, logs. Human-readable but verbose. |
| **Avro** | Row (binary) | Schema embedded | Streaming (Kafka), schema evolution, compact. |
| **Parquet** | Columnar (binary) | Schema embedded | Analytics, data lakes, ML training. Highly compressed, fast scans. |
| **ORC** | Columnar (binary) | Schema embedded | Hive/Spark ecosystems. Similar to Parquet. |
| **Arrow** | Columnar (in-memory) | Schema defined | Inter-process data exchange, zero-copy reads. Not for storage. |

> **Recommended for your migration**:
> - **Landing zone / raw**: Parquet (columnar, compressed, schema-embedded, Athena-queryable)
> - **Streaming**: Avro (compact, schema evolution via registry)
> - **Interchange with legacy systems**: CSV (if needed), but migrate to Parquet ASAP

### Compression Algorithms

| Algorithm | Speed | Ratio | Notes |
|---|---|---|---|
| **gzip** | Moderate | Good | Most compatible. Default for many tools. |
| **Snappy** | Very fast | Lower | Optimized for speed. Common in Spark/Hadoop. |
| **Zstandard (zstd)** | Fast | Excellent | Best balance of speed and ratio. Growing adoption. |
| **LZ4** | Fastest | Lower | Ultra-low latency. Good for streaming. |
| **bzip2** | Slow | Excellent | Maximum compression. Rarely used in pipelines. |

> **Recommendation**: Use **Snappy** or **Zstandard** with Parquet on S3. Both offer good speed/ratio tradeoffs for analytical workloads.

---

# Appendix B: Cloud Networking

### Key Concepts

- **VPC (Virtual Private Cloud)**: Isolated network within AWS. You define subnets, routing, and access.
- **Subnets**: Public (internet-accessible) and private (internal only). Data infrastructure belongs in private subnets.
- **Security Groups**: Stateful firewall rules at the instance level. Whitelist ingress/egress.
- **VPC Endpoints**: Private connectivity to AWS services (S3, Secrets Manager) without traversing the public internet.
- **VPC Peering / Transit Gateway**: Connect multiple VPCs. Useful for multi-account architectures.

> **For your EKS deployment**:
> - EKS worker nodes in private subnets.
> - S3 access via VPC Gateway Endpoint (free, private).
> - RDS Postgres in private subnet, accessible only from EKS security group.
> - Airflow web UI exposed via ALB in public subnet (with authentication).

```
┌──────────────────── VPC ────────────────────┐
│                                              │
│  ┌─ Private Subnet ─┐   ┌─ Private Subnet ─┐│
│  │  EKS Worker Nodes │   │  RDS Postgres    ││
│  │  Airflow Workers  │──▶│  (analytics DB)  ││
│  └───────┬───────────┘   └──────────────────┘│
│          │                                    │
│          │  VPC Endpoint                      │
│          ▼                                    │
│       ┌──────┐                                │
│       │  S3  │ (data lake)                    │
│       └──────┘                                │
│                                              │
│  ┌─ Public Subnet ──┐                        │
│  │  ALB → Airflow UI │                        │
│  └───────────────────┘                        │
└──────────────────────────────────────────────┘
```

---

# Quick Reference: Mapping Your Migration

| Current State (On-Prem) | Target State (Cloud) |
|---|---|
| Excel files on shared network drive | S3 (Parquet) + Postgres (RDS) |
| Autosys .jil orchestration | Apache Airflow (MWAA or on EKS) |
| Manual file-based data movement | Automated S3 put + Postgres insert |
| On-prem server execution | EKS (Kubernetes) on AWS |
| No formal data quality checks | DataOps: automated testing, monitoring, alerting |
| Ad hoc schema (Excel columns) | Enforced schema (Parquet schema, Postgres DDL) |
| No data lineage | Airflow DAG lineage + metadata tracking |

### Recommended Migration Sequence

1. **Add S3 writes to on-prem pipeline** — dual-write: existing output + S3 upload (Parquet).
2. **Optionally add Postgres inserts** — for data that needs structured querying.
3. **Build cloud pipeline on feature branch** — Airflow DAGs reading from S3/Postgres, running on EKS.
4. **Validate data parity** — compare on-prem outputs vs cloud outputs.
5. **Cutover** — switch downstream consumers to cloud pipeline.
6. **Decommission** — retire on-prem Autosys jobs.

---

# Book7 - Data Pipelines with Apache Airflow — 2nd Edition (Manning, 2026)

> **Context:** On-prem JIL/Autosys orchestration migrating to cloud. Current state uses Excel files on slow shared network drives. Future state: S3 or Postgres for data, Airflow (MWAA or EKS) for orchestration. 1.5-month refactoring window.

---

# Part 1 — Getting Started

---

## Chapter 1: Meet Apache Airflow

### 1.1 Introducing Data Pipelines

- **Data pipeline**: a sequence of tasks that must execute in a defined order to achieve a result (e.g., fetch → clean → load)
- **DAG (Directed Acyclic Graph)**: the core abstraction — tasks are nodes, dependencies are directed edges, and cycles are forbidden
  - Directed = edges have direction (A must finish before B)
  - Acyclic = no circular dependencies (prevents deadlocks)
- **Execution algorithm** (3-step loop):
  1. For each incomplete task, check if all upstream tasks are done
  2. If so, add to execution queue
  3. Execute queued tasks; repeat until all complete
- DAGs enable **parallel execution** naturally — independent branches run simultaneously without explicit threading logic
- **Workflow managers** (alternatives): Dagster, Prefect, Luigi, Argo, Temporal, ControlM. Airflow is the most widely adopted open-source option.

**See Figure 1.3 for DAG vs. cyclic graph visualization**

### 1.2 Introducing Airflow

- Pipelines defined in **Python code** (not XML/YAML like Oozie or JIL)
- Five core components:

| Component | Role |
|-----------|------|
| **DAG Processor** | Reads `.py` DAG files, serializes to metastore |
| **Scheduler** | Checks schedules, queues tasks when dependencies met |
| **Workers** | Execute queued tasks |
| **Triggerer** | Handles deferred/async tasks |
| **API Server** | Web UI + REST API; gateway to metastore |

- **Web UI** provides: DAG list, graph view (dependency visualization), grid view (historical run matrix), task logs, manual trigger/clear controls
- Supports **incremental loading** and **backfilling** natively

**See Figure 1.8 for architecture diagram, Figure 1.9 for full execution flow**

### 1.3 When to Use Airflow

- **Good fit**: batch-oriented ETL/ELT, scheduled data processing, ML pipelines, orchestrating external services
- **Not ideal for**: real-time streaming (use Kafka/Flink), simple single-step cron jobs, non-technical users who can't write Python

### Autosys → Airflow Mental Model

| Autosys/JIL | Airflow |
|-------------|---------|
| JIL job definition | Python DAG file |
| `condition: s(prev_job)` | `prev_task >> next_task` |
| Autosys scheduler | Airflow scheduler + executor |
| `autorep -j` / `sendevent` | Web UI + REST API |
| `.jil` files | `.py` files in `dags/` folder |

---

## Chapter 2: Anatomy of an Airflow DAG

### 2.1 Collecting Data from Numerous Sources

- Real-world example: fetching rocket launch images from an API, downloading them, and notifying users

### 2.2 Writing Your First Airflow DAG

**Two main DAG definition styles:**

```python
# Style 1: Context manager (recommended)
from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
import pendulum

with DAG(
    dag_id="my_pipeline",
    start_date=pendulum.datetime(2025, 1, 1),
    schedule="@daily",
):
    fetch = BashOperator(
        task_id="fetch_data",
        bash_command="curl -o /tmp/data.json https://api.example.com/data",
    )

    process = PythonOperator(
        task_id="process_data",
        python_callable=my_processing_function,
    )

    fetch >> process  # dependency: fetch before process
```

```python
# Style 2: Taskflow API (modern, decorator-based — see Ch 6)
from airflow.sdk import dag, task

@dag(schedule="@daily", start_date=pendulum.datetime(2025, 1, 1))
def my_pipeline():
    @task
    def fetch():
        ...
    @task
    def process(data):
        ...
    process(fetch())

my_pipeline()
```

#### 2.2.1 Tasks vs. Operators

- **Operator** = abstract class defining *what* work is done (e.g., `BashOperator`, `PythonOperator`, `S3CopyObjectOperator`)
- **Task** = wrapper around an operator managing *how* it's scheduled, retried, and tracked
- Common operators: `BashOperator`, `PythonOperator`, `EmailOperator`, `SQLExecuteQueryOperator`, plus hundreds of provider-specific operators

#### 2.2.2 Running Arbitrary Python Code

```python
def _get_pictures():
    # Any Python logic here — read files, call APIs, transform data
    pathlib.Path("/tmp/images").mkdir(parents=True, exist_ok=True)
    with open("/tmp/launches.json") as f:
        launches = json.load(f)
    for launch in launches["results"]:
        response = requests.get(launch["image"])
        with open(f"/tmp/images/{launch['id']}.jpg", "wb") as img:
            img.write(response.content)

get_pictures = PythonOperator(
    task_id="get_pictures",
    python_callable=_get_pictures,
)
```

### 2.3 Running a DAG in Airflow

```bash
# Quick local setup
pip install apache-airflow
airflow standalone  # starts all services, creates admin user
# UI at http://localhost:8080 (airflow/airflow)

# Docker setup (recommended for team consistency)
docker compose up
```

### 2.4 Running at Regular Intervals

- Set `schedule` parameter: `"@daily"`, `"@hourly"`, cron string, `timedelta`, or `None` (manual only)
- Set `start_date` and optionally `end_date` to bound the schedule window

### 2.5 Handling Failing Tasks

- Failed tasks appear red in the UI graph/grid views
- Click failed task → view logs (full stdout/stderr captured) → fix issue → **Clear Task Instance** to rerun
- Options when clearing: upstream, downstream, past, future, only-failed
- No need to restart the entire pipeline — Airflow reruns from the failure point

### 2.6 DAG Versioning

- Airflow 3 automatically tracks DAG code changes
- Historical DAG structures viewable via UI dropdown
- Foundation for safe backfills (run historical data against the code version that existed at that time)

---

## Chapter 3: Time-Based Scheduling

### 3.1 Processing User Events

- Use case: website event tracking API that stores only 30 days of data → need daily download + stats calculation
- Demonstrates why scheduling with date-awareness matters

### 3.2 The Basic Components of an Airflow Schedule

| Parameter | Required | Description |
|-----------|----------|-------------|
| `start_date` | Yes | Earliest possible execution |
| `end_date` | No | Stop scheduling after this date |
| `schedule` | Yes | When to run (cron, preset, timedelta, `None`) |
| `catchup` | No | Execute missed past runs (default `False` in Airflow 3) |

- **`catchup=True`**: If `start_date` is in the past, Airflow creates runs for every missed interval
- **`catchup=False`** (Airflow 3 default): Only future runs execute

### 3.3 Running Regularly Using Trigger-Based Schedules

#### 3.3.2 Cron Expressions

```
# ┌─── minute (0-59)
# │ ┌─── hour (0-23)
# │ │ ┌─── day of month (1-31)
# │ │ │ ┌─── month (1-12)
# │ │ │ │ ┌─── day of week (0-6, Sun=0)
# * * * * *

"0 0 * * *"       # Daily at midnight
"0 0 * * MON-FRI" # Weekdays at midnight
"0 9,17 * * *"    # 9am and 5pm daily
"*/15 * * * *"    # Every 15 minutes
```

#### 3.3.3 Shorthand Presets

| Preset | Equivalent Cron |
|--------|----------------|
| `@hourly` | `0 * * * *` |
| `@daily` | `0 0 * * *` |
| `@weekly` | `0 0 * * 0` |
| `@monthly` | `0 0 1 * *` |
| `@yearly` | `0 0 1 1 *` |

#### 3.3.4 Frequency-Based Timetables

```python
# For patterns cron can't express (e.g., every 2 days):
from datetime import timedelta
schedule = timedelta(days=2)
```

### 3.4 Incremental Processing with Data Intervals

- Each scheduled run has an implicit **data interval** (`data_interval_start` → `data_interval_end`)
- Tasks should process only data from their interval, not the entire dataset
- Use Jinja templating to parameterize by date:

```python
fetch_events = BashOperator(
    task_id="fetch_events",
    bash_command=(
        "curl -o /data/events/{{ logical_date | ds }}.json "
        "'http://events-api:8001/events?date={{ logical_date | ds }}'"
    ),
)
```

### 3.5 Handling Irregular Intervals

- Custom timetable classes for non-standard schedules (e.g., business days only, market hours)

### 3.6 Managing Backfilling of Historical Data

- `catchup=True` + historical `start_date` = automatic backfill
- CLI: `airflow dags backfill -s 2025-01-01 -e 2025-03-01 my_dag`
- ⚠️ Be cautious with large date ranges — can spawn hundreds of concurrent runs

### 3.7 Designing Well-Behaved Tasks

- **Atomicity**: Task either fully succeeds or fully fails (no partial writes). Use temp files + atomic rename, or database transactions.
- **Idempotency**: Running the same task twice with the same inputs produces the same result. Critical for reruns/backfills. Strategies:
  - Overwrite output files (not append)
  - Use `INSERT ... ON CONFLICT DO UPDATE` for database writes
  - Include execution date in output paths for partitioning

---

## Chapter 4: Asset-Aware Scheduling

### 4.1 Challenges of Scaling Time-Based Schedules

- Problem: multiple teams fetch the same data independently → duplicated work, inconsistent results, API overload
- Time-based coupling: downstream DAGs scheduled N minutes after upstream "should" finish → fragile

### 4.2 Introducing Asset-Aware Scheduling

- **Asset**: a virtual reference to a data dependency, identified by URI (e.g., `s3://bucket/data.csv`, `postgres://db/table`)
- **Producer DAG**: updates the asset (has `outlets=[asset]` on the writing task)
- **Consumer DAG**: triggered when the asset is updated (has `schedule=[asset]`)
- Decouples producers from consumers — no hardcoded timing or job names

**See Figure 4.2 for producer/consumer pattern diagram**

### 4.3 Producing Asset Events

```python
from airflow.sdk import Asset

events_dataset = Asset("s3://my-bucket/events/daily.json")

fetch_events = PythonOperator(
    task_id="fetch_events",
    python_callable=_fetch_events,
    outlets=[events_dataset],  # declares this task updates the asset
)
```

### 4.4 Consuming Asset Events

```python
with DAG(
    dag_id="stats_consumer",
    schedule=[events_dataset],  # triggers when asset is updated
    start_date=pendulum.datetime(2025, 1, 1),
):
    calculate_stats = PythonOperator(...)
```

### 4.5 Adding Extra Information to Events

```python
from airflow.sdk import Metadata

def _fetch_events(**context):
    # ... fetch data ...
    yield Metadata(events_dataset, extra={"row_count": len(data), "date": "2025-01-15"})
```

### 4.6 Skipping Updates

```python
from airflow.exceptions import AirflowSkipException

def _fetch_events(output_path, **context):
    if Path(output_path).exists():
        raise AirflowSkipException()  # no asset event emitted → consumer not triggered
    # ... fetch data ...
```

### 4.7 Consuming Multiple Assets

```python
# Wait for ALL assets to update (AND logic):
schedule = [asset_1, asset_2]

# Boolean logic:
schedule = (asset_1 | (asset_2 & asset_3))  # asset_1 OR (asset_2 AND asset_3)
```

### 4.8 Combining Time- and Asset-Based Schedules

- Assets can work alongside time-based triggers for hybrid scheduling

### Migration Relevance

> **Autosys parallel**: Autosys "conditions" (e.g., `condition: s(upstream_job)`) are conceptually similar but tightly coupled by job name. Assets decouple by data URI — the consumer doesn't know or care which DAG produced the data.
>
> **For your S3 migration**: Define assets as S3 URIs. On-prem producer DAGs write to S3 + emit asset events. Cloud consumer DAGs trigger automatically when S3 data lands.

---

## Chapter 5: Templating Tasks Using the Airflow Context

### 5.1 Inspecting Data for Processing with Airflow

- Use case: downloading Wikipedia pageview data where the URL contains the execution date/hour

### 5.2 Task Context and Jinja Templating

- **Jinja templating**: `{{ variable }}` syntax replaced at runtime with actual values
- Works in any operator argument that is a **templated field** (check operator docs)

#### 5.2.1 Templating Operator Arguments

```python
# BashOperator — bash_command is a templated field
download = BashOperator(
    task_id="download",
    bash_command=(
        "curl -o /tmp/pageviews-{{ logical_date.strftime('%Y%m%d-%H') }}.gz "
        "'https://dumps.wikimedia.org/other/pageviews/"
        "{{ logical_date.year }}/{{ logical_date.year }}-"
        "{{ '{:02d}'.format(logical_date.month) }}/...'"
    ),
)
```

#### 5.2.2 Templating the PythonOperator

```python
# PythonOperator receives context as **kwargs automatically
def _process_data(**context):
    logical_date = context["logical_date"]
    start = context["data_interval_start"]
    end = context["data_interval_end"]
    print(f"Processing data for {start} to {end}")

process = PythonOperator(
    task_id="process",
    python_callable=_process_data,
)
```

#### 5.2.3 Passing Additional Variables to the PythonOperator

```python
# op_kwargs supports Jinja templating too
process = PythonOperator(
    task_id="process",
    python_callable=_process_data,
    op_kwargs={
        "input_path": "/data/{{ logical_date | ds }}.json",
        "output_path": "/data/stats/{{ logical_date | ds }}.csv",
    },
)
```

#### 5.2.4 Inspecting Templated Arguments

```bash
# CLI tool to see rendered template values without running the task
airflow tasks render my_dag my_task 2025-04-24T00:00:00
```

Also viewable in the Web UI under the task's "Rendered Template" tab.

### 5.3 What Is Available for Templating

| Variable | Type | Description |
|----------|------|-------------|
| `logical_date` | `pendulum.DateTime` | The logical execution date |
| `data_interval_start` | `pendulum.DateTime` | Start of the data interval |
| `data_interval_end` | `pendulum.DateTime` | End of the data interval |
| `ds` | `str` | `logical_date` as `YYYY-MM-DD` |
| `ts` | `str` | `logical_date` as ISO 8601 |
| `dag` | `DAG` | Reference to the current DAG |
| `dag_run` | `DagRun` | Current DAG run metadata |
| `task_instance` | `TaskInstance` | Current task instance (for XCom) |
| `params` | `dict` | User-supplied parameters |
| `macros` | module | Utility functions (`macros.ds_add(ds, 7)`, etc.) |

### 5.4 Bringing It All Together

```python
# Full example: download Wikipedia data, extract top pages, write to Postgres
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

write_to_postgres = SQLExecuteQueryOperator(
    task_id="write_to_postgres",
    conn_id="my_postgres",                    # connection stored in Airflow
    sql="postgres_query.sql",                 # external SQL file (also templated)
    template_searchpath="/tmp",
)
```

```bash
# Store database credentials in Airflow (not in code)
airflow connections add \
    --conn-type postgres \
    --conn-host localhost \
    --conn-login postgres \
    --conn-password mysecretpassword \
    my_postgres
```

### Migration Relevance

> **Replaces JIL variable expansion**: Autosys uses `${AUTODATE}`, `${AUTORUNS}`. Airflow's `{{ logical_date }}`, `{{ ds }}`, `{{ data_interval_start }}` are far more powerful and Pythonic.

---

## Chapter 6: Defining Dependencies Between Tasks

### 6.1 Basic Dependencies

```python
# Linear: A → B → C
fetch >> clean >> load

# Fan-out: one task triggers multiple parallel tasks
fetch_weather >> clean_weather
fetch_sales >> clean_sales

# Fan-in: multiple tasks feed into one
[clean_weather, clean_sales] >> join_datasets >> train_model
```

### 6.2 Branching

#### 6.2.2 Branching Within the DAG

```python
from airflow.operators.python import BranchPythonOperator

def _pick_source(**context):
    if context["data_interval_start"] < ERP_MIGRATION_DATE:
        return "fetch_from_old_system"
    return "fetch_from_new_system"

pick_source = BranchPythonOperator(
    task_id="pick_source",
    python_callable=_pick_source,
)
pick_source >> [fetch_from_old_system, fetch_from_new_system]
```

- Non-selected branches are **skipped** (not failed)
- Downstream tasks need `trigger_rule="none_failed"` to run after branching

### 6.3 Conditional Tasks

```python
from airflow.operators.latest_only import LatestOnlyOperator

# Only deploy model on the most recent run (skip during backfills)
latest_only = LatestOnlyOperator(task_id="latest_only")
latest_only >> deploy_model
```

### 6.4 Exploring Trigger Rules

| Rule | Fires When | Use Case |
|------|-----------|----------|
| `all_success` (default) | All parents succeeded | Normal flow |
| `all_failed` | All parents failed | Error-only handlers |
| `all_done` | All parents finished (any state) | Cleanup/teardown |
| `one_failed` | ≥1 parent failed | Early alert |
| `one_success` | ≥1 parent succeeded | Race condition / first-wins |
| `none_failed` | No parent failed (skipped OK) | After branching |
| `none_skipped` | No parent skipped | All-branches-required |
| `always` | Regardless | Monitoring/logging |

### 6.5 Sharing Data Between Tasks

#### 6.5.1 XComs (Cross-Communication)

```python
# Push (explicit)
def _train(**context):
    model_id = str(uuid.uuid4())
    context["task_instance"].xcom_push(key="model_id", value=model_id)

# Pull
def _deploy(**context):
    model_id = context["task_instance"].xcom_pull(
        task_ids="train_model", key="model_id"
    )
```

#### 6.5.2 When (Not) to Use XComs

- ✅ Small values: IDs, file paths, row counts, status flags
- ❌ Large data: DataFrames, files, images → use S3/Postgres instead
- XComs are stored in the metastore database — keep them small

### 6.6 Chaining Python Tasks with the Taskflow API

```python
from airflow.sdk import task, dag

@dag(schedule="@daily", start_date=pendulum.datetime(2025, 1, 1))
def my_ml_pipeline():

    @task
    def train_model():
        model_id = str(uuid.uuid4())
        # ... training logic ...
        return model_id  # automatically pushed as XCom

    @task
    def deploy_model(model_id: str):
        print(f"Deploying {model_id}")

    # Dependencies + XCom passing inferred automatically
    deploy_model(train_model())

my_ml_pipeline()
```

- `@task` decorator replaces `PythonOperator` + manual XCom push/pull
- Return values are automatically XCom-pushed; function arguments are auto-pulled
- Use when DAG is mostly Python; mix with traditional operators as needed

---

# Part 2 — Beyond the Basics

---

## Chapter 7: Triggering Workflows with External Input

### 7.1 Polling Conditions with Sensors

- **Sensor**: a special operator that repeatedly checks ("pokes") a condition until it's true or times out
- **Poke interval**: seconds between checks (default 60)
- **Timeout**: max wait time (default 7 days)

```python
from airflow.providers.standard.sensors.filesystem import FileSensor

wait_for_file = FileSensor(
    task_id="wait_for_file",
    filepath="/data/incoming/daily_extract.csv",
    poke_interval=300,       # check every 5 minutes
    timeout=3600,            # give up after 1 hour
    mode="reschedule",       # release worker slot between pokes
)
```

#### 7.1.1 Custom Sensors

```python
from airflow.providers.standard.sensors.python import PythonSensor

def _check_data_ready(source_id):
    path = Path(f"/data/{source_id}")
    return (path / "_SUCCESS").exists() and list(path.glob("data-*.csv"))

wait = PythonSensor(
    task_id="wait_for_data",
    python_callable=_check_data_ready,
    op_kwargs={"source_id": "source_a"},
    timeout=timedelta(minutes=30),
)
```

#### 7.1.2 Sensor Modes and Deadlock Prevention

- **`mode="poke"` (default)**: sensor holds a worker slot the entire time → can cause **deadlock** if all slots occupied by waiting sensors
- **`mode="reschedule"`**: releases worker slot between pokes → prevents deadlock
- **Deferrable operators**: even better — yield control to the triggerer process, consuming zero worker slots while waiting
- Always set `max_active_tasks` on sensor-heavy DAGs as a safety net

**See Figure 7.8 for sensor deadlock visualization**

### 7.2 Starting Workflows with the REST API and CLI

```bash
# CLI trigger
airflow dags trigger my_dag

# REST API trigger with configuration payload
curl -u airflow:airflow -X POST \
    "http://localhost:8080/api/v1/dags/my_dag/dagRuns" \
    -H "Content-Type: application/json" \
    -d '{"conf": {"source": "manual", "run_type": "full"}}'
```

```python
# Access trigger config inside a task
def _process(**context):
    config = context["dag_run"].conf
    source = config.get("source", "default")
```

### 7.3 Triggering Workflows with Messages

```python
from airflow.providers.common.messaging.triggers.msg_queue import MessageQueueTrigger
from airflow.sdk import Asset, AssetWatcher

trigger = MessageQueueTrigger(
    queue="kafka://kafka:9092/events",
    apply_function="my_package.kafka_filter.should_trigger",
)

kafka_asset = Asset(
    "kafka_queue_asset",
    watchers=[AssetWatcher(name="kafka_watcher", trigger=trigger)],
)

with DAG(dag_id="event_driven_dag", schedule=[kafka_asset]):
    process = PythonOperator(...)
```

> **Migration relevance**: Replaces Autosys file-watcher jobs with sensors. REST API triggering replaces `sendevent -E FORCE_STARTJOB`. Kafka triggering enables true event-driven orchestration without polling.

---

## Chapter 8: Communicating with External Systems

### 8.1 Installing Additional Operators

```bash
# Provider packages for cloud services
pip install apache-airflow-providers-amazon      # S3, SageMaker, Redshift, etc.
pip install apache-airflow-providers-google       # GCS, BigQuery, Dataflow, etc.
pip install apache-airflow-providers-postgres     # PostgresOperator, PostgresHook
pip install apache-airflow-providers-cncf-kubernetes  # KubernetesPodOperator
```

### 8.2 Developing a Machine Learning Model

- Example: MNIST digit classifier using SageMaker
- Pattern: upload training data to S3 → train with `SageMakerTrainingOperator` → deploy with `SageMakerEndpointOperator`

```python
from airflow.providers.amazon.aws.operators.sagemaker import (
    SageMakerTrainingOperator,
    SageMakerEndpointOperator,
)

train = SageMakerTrainingOperator(
    task_id="train_model",
    config={
        "TrainingJobName": "my-model-{{ logical_date | ts_nodash }}",
        "AlgorithmSpecification": {...},
        "InputDataConfig": [{"ChannelName": "train", "DataSource": {"S3DataSource": {...}}}],
        "OutputDataConfig": {"S3OutputPath": f"s3://{BUCKET}/output"},
        "ResourceConfig": {"InstanceType": "ml.c4.xlarge", "InstanceCount": 1, ...},
        "wait_for_completion": True,
    },
)
```

> ⚠️ **EKS note**: SageMaker operators are Lambda/API-based — they submit jobs to SageMaker, which runs on its own infrastructure. These work fine from both MWAA and EKS-hosted Airflow. No Lambda dependency.

### 8.3 Moving Data Between Systems

#### 8.3.2 PostgresToS3Operator

```python
from airflow.providers.amazon.aws.transfers.postgres_to_s3 import PostgresToS3Operator

extract = PostgresToS3Operator(
    task_id="postgres_to_s3",
    postgres_conn_id="source_db",
    query="SELECT * FROM trades WHERE trade_date = '{{ ds }}'",
    s3_conn_id="aws_default",
    s3_bucket="my-data-lake",
    s3_key="raw/trades/{{ ds }}.csv",
)
```

#### 8.3.3 Outsourcing the Heavy Work

```python
from airflow.providers.docker.operators.docker import DockerOperator

crunch = DockerOperator(
    task_id="heavy_computation",
    image="my-registry/number-cruncher:latest",
    environment={"S3_BUCKET": "my-bucket", "DATE": "{{ ds }}"},
    network_mode="host",
    auto_remove="success",
)
```

- **Key principle**: Airflow orchestrates, it doesn't execute heavy computation. Offload to SageMaker, Spark, Docker containers, or Kubernetes pods.

---

## Chapter 9: Extending Airflow with Custom Operators and Sensors

### 9.1 Starting with a PythonOperator

- Always start with `PythonOperator` for prototyping; refactor to custom operator when the pattern stabilizes

### 9.2 Building a Custom Hook

- **Hook** = reusable class for connecting to an external service. Handles auth, sessions, connection caching.

```python
from airflow.hooks.base import BaseHook

class MyServiceHook(BaseHook):
    def __init__(self, conn_id: str):
        self._conn_id = conn_id
        self._session = None

    def get_conn(self):
        if self._session is None:
            config = self.get_connection(self._conn_id)  # reads from Airflow metastore
            self._session = requests.Session()
            self._session.auth = (config.login, config.password)
            self._base_url = f"{config.schema}://{config.host}:{config.port}"
        return self._session

    def get_data(self, start_date, end_date):
        session = self.get_conn()
        response = session.get(f"{self._base_url}/data?start={start_date}&end={end_date}")
        response.raise_for_status()
        return response.json()
```

### 9.3 Building a Custom Operator

```python
from airflow.models import BaseOperator

class FetchAndStoreOperator(BaseOperator):
    template_fields = ("_start_date", "_end_date", "_output_path")  # Jinja-enabled fields

    def __init__(self, conn_id, start_date, end_date, output_path, **kwargs):
        super().__init__(**kwargs)
        self._conn_id = conn_id
        self._start_date = start_date
        self._end_date = end_date
        self._output_path = output_path

    def execute(self, context):
        hook = MyServiceHook(self._conn_id)
        data = hook.get_data(self._start_date, self._end_date)
        Path(self._output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self._output_path, "w") as f:
            json.dump(data, f)
        self.log.info(f"Wrote {len(data)} records to {self._output_path}")
```

### 9.4 Building Custom Sensors

```python
from airflow.sensors.base import BaseSensorOperator

class DataAvailableSensor(BaseSensorOperator):
    template_fields = ("_start_date", "_end_date")

    def __init__(self, conn_id, start_date, end_date, **kwargs):
        super().__init__(**kwargs)
        self._conn_id = conn_id
        self._start_date = start_date
        self._end_date = end_date

    def poke(self, context):
        hook = MyServiceHook(self._conn_id)
        try:
            data = hook.get_data(self._start_date, self._end_date)
            return len(data) > 0  # True = condition met, sensor completes
        except Exception:
            return False  # False = keep waiting
```

### 9.5 Building a Custom Deferrable Operator

- For long-running tasks, yield to the **triggerer** to avoid holding worker slots
- Requires implementing a `Trigger` class and using `TaskDeferred` in the operator's `execute` method

### 9.6 Packaging the Components

```
my_airflow_package/
├── hooks.py          # MyServiceHook
├── operators.py      # FetchAndStoreOperator
├── sensors.py        # DataAvailableSensor
├── __init__.py
└── setup.py          # for pip install
```

```bash
pip install -e ./my_airflow_package
# or add to MWAA requirements.txt
```

---

## Chapter 10: Testing

### 10.1 Getting Started with Testing

#### 10.1.1 Integrity Testing All DAGs

```python
# tests/test_dag_integrity.py
import glob, os, pytest
from airflow.models import DagBag

DAG_PATH = os.path.join(os.path.dirname(__file__), "..", "dags/**/*.py")
DAG_FILES = glob.glob(DAG_PATH, recursive=True)

@pytest.mark.parametrize("dag_file", DAG_FILES)
def test_dag_integrity(dag_file):
    """Verify DAGs parse without errors (no cycles, valid task IDs, etc.)."""
    dag_bag = DagBag(dag_folder=dag_file, include_examples=False)
    assert len(dag_bag.import_errors) == 0, f"Import errors: {dag_bag.import_errors}"
```

- Run this in CI on every PR — catches syntax errors, circular dependencies, and import failures before deployment

#### 10.1.2 Setting Up a CI/CD Pipeline

- Use GitHub Actions (or equivalent) with steps:
  1. Lint: `flake8`, `ruff check`
  2. Format: `black --check`
  3. Type check: `mypy`
  4. DAG integrity test: `pytest tests/test_dag_integrity.py`
  5. Unit tests: `pytest tests/`

### 10.2 Working with External Systems

**Unit testing with mocks:**

```python
def test_my_operator(mocker):
    # Mock the hook so we don't need a real database
    mocker.patch.object(
        MyServiceHook, "get_connection",
        return_value=Connection(conn_id="test", login="user", password="pass"),
    )
    mocker.patch.object(
        MyServiceHook, "get_data",
        return_value=[{"id": 1, "value": 42}],
    )

    task = FetchAndStoreOperator(
        task_id="test", conn_id="test",
        start_date="2025-01-01", end_date="2025-01-02",
        output_path="/tmp/test_output.json",
    )
    task.execute(context={})
    assert Path("/tmp/test_output.json").exists()
```

**⚠️ Critical mocking rule**: Mock where the function is *called*, not where it's *defined*.

**Integration testing with real containers:**

```python
from pytest_docker_tools import fetch, container

postgres_image = fetch(repository="postgres:16-alpine")
postgres = container(
    image="{postgres_image.id}",
    environment={"POSTGRES_USER": "test", "POSTGRES_PASSWORD": "test"},
    ports={"5432/tcp": None},
)

def test_postgres_operator(postgres):
    port = postgres.ports["5432/tcp"][0]["HostPort"]
    # Run operator against real Postgres container
    # Assert results in the actual database
```

### 10.3 Using Tests for Development

- Use `pytest` with breakpoints (`breakpoint()`) and IDE debuggers for interactive development
- Test individual operators with `task.execute(context={})` — no need for a running Airflow instance

### 10.4 Testing Complete DAGs

```python
# dag.test() runs the entire DAG locally in a single process
from my_dags.pipeline import my_dag

my_dag.test(logical_date=datetime(2025, 1, 15, tzinfo=timezone.utc))
```

- **Whirl**: open-source tool for emulating production Airflow environments locally with Docker
- **DTAP pattern**: separate Development, Test, Acceptance, Production environments with corresponding Git branches

### Testing Strategy Summary

| Layer | What | How | When |
|-------|------|-----|------|
| DAG integrity | Parse errors, cycles | `DagBag` import test | Every PR (CI) |
| Unit tests | Individual operators | `task.execute()` + mocks | Every PR (CI) |
| Integration tests | Operators + real systems | `pytest-docker-tools` | Nightly / pre-deploy |
| DAG-level tests | End-to-end pipeline | `dag.test()` or Whirl | Pre-deploy |

---

## Chapter 11: Running Tasks in Containers

### 11.1 Challenges of Different Operators

- **Dependency conflicts**: DAG A needs `pandas==1.5`, DAG B needs `pandas==2.0` — can't have both in one Python environment
- **Solution**: run each task in its own container with isolated dependencies

### 11.2 Introducing Containers

- **Container** = lightweight isolated process with its own filesystem, libraries, and binaries. Shares host kernel (much lighter than VMs).
- **Docker image** = immutable blueprint for containers
- **Dockerfile** = recipe for building an image

```dockerfile
FROM python:3.12-slim
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
COPY scripts/my_task.py /usr/local/bin/my-task
RUN chmod +x /usr/local/bin/my-task
ENTRYPOINT ["/usr/local/bin/my-task"]
CMD ["--help"]
```

### 11.3 Containers and Airflow

- **Why containers?**
  - Dependency isolation per task
  - Uniform interface (all tasks are DockerOperator or KubernetesPodOperator)
  - Independent development and testing of task images
  - Reproducible builds via CI/CD

### 11.4 Running Tasks in Docker

```python
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

fetch = DockerOperator(
    task_id="fetch_data",
    image="my-registry/data-fetcher:1.0",
    command=[
        "fetch-data",
        "--start-date", "{{ data_interval_start | ds }}",
        "--end-date", "{{ data_interval_end | ds }}",
        "--output-path", "/data/raw/{{ ds }}.json",
    ],
    mounts=[Mount(source="shared_data_volume", target="/data", type="volume")],
    network_mode="bridge",
    auto_remove="success",
)
```

**Docker workflow:**
1. Developer writes Dockerfile + task script
2. CI/CD builds image, pushes to registry (ECR)
3. DAG references image by tag
4. Worker pulls image, runs container, captures logs

**See Figure 11.9 for Docker CI/CD workflow diagram**

### 11.5 Running Tasks in Kubernetes

#### 11.5.1-11.5.2 Kubernetes Basics

- **Pod**: smallest K8s unit (one or more containers)
- **Service**: stable network endpoint for pods
- **PersistentVolume (PV)** / **PersistentVolumeClaim (PVC)**: shared storage that survives pod restarts

```yaml
# PersistentVolumeClaim for shared task data
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pipeline-data
  namespace: airflow
spec:
  accessModes: [ReadWriteMany]
  resources:
    requests:
      storage: 10Gi
  storageClassName: gp2  # or your EKS storage class
```

#### 11.5.3 Using the KubernetesPodOperator

```python
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client import models as k8s

volume = k8s.V1Volume(
    name="pipeline-data",
    persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name="pipeline-data"),
)
volume_mount = k8s.V1VolumeMount(
    name="pipeline-data", mount_path="/data", read_only=False,
)

fetch = KubernetesPodOperator(
    task_id="fetch_data",
    image="123456789.dkr.ecr.us-east-1.amazonaws.com/data-fetcher:1.0",
    cmds=["fetch-data"],
    arguments=[
        "--start-date", "{{ data_interval_start | ds }}",
        "--end-date", "{{ data_interval_end | ds }}",
        "--output-path", "/data/raw/{{ ds }}.json",
    ],
    namespace="airflow",
    name="fetch-data-pod",
    volumes=[volume],
    volume_mounts=[volume_mount],
    image_pull_policy="Always",
    is_delete_operator_pod=True,  # cleanup after execution
    in_cluster=True,  # True when Airflow itself runs in K8s (EKS)
)
```

#### 11.5.4 Diagnosing Kubernetes-Related Issues

```bash
kubectl -n airflow get pods                    # list pods
kubectl -n airflow describe pod <pod-name>     # events, status, errors
kubectl -n airflow logs <pod-name>             # task stdout/stderr
```

#### DockerOperator vs KubernetesPodOperator

| Aspect | DockerOperator | KubernetesPodOperator |
|--------|---------------|----------------------|
| Runs on | Single Docker host | K8s cluster (multi-node) |
| Scaling | Limited to one machine | Automatic across cluster |
| Resource control | Basic | CPU/memory requests + limits |
| Data sharing | Docker volumes | PersistentVolumeClaims |
| Cleanup | Manual | `is_delete_operator_pod=True` |
| **Your use case** | Local dev | **Production on EKS** |

> ⚠️ **EKS note**: When Airflow itself runs on EKS (via MWAA or self-hosted), set `in_cluster=True`. KubernetesPodOperator creates pods in the same cluster. This is the native EKS pattern — no Lambdas involved.

---

# Part 3 — Airflow in Practice

---

## Chapter 12: Best Practices

### 12.1 Writing Clean DAGs

#### 12.1.1 Using Style Conventions

```bash
# Enforce consistent style across your team
pip install ruff     # fast linter + formatter (replaces flake8 + black)
ruff check dags/     # lint
ruff format dags/    # auto-format
```

#### 12.1.2 Managing Credentials Centrally

```python
# NEVER hardcode credentials in DAG files
# Use Airflow connections (stored encrypted in metastore)
from airflow.hooks.base import BaseHook

def _fetch_data(conn_id, **context):
    creds = BaseHook.get_connection(conn_id)
    # creds.host, creds.login, creds.password, creds.port, etc.
```

#### 12.1.3 Specifying Configuration Details Consistently

```python
# Option A: Airflow Variables (stored in metastore, editable via UI)
from airflow.sdk import Variable
input_path = Variable.get("pipeline_input_path")

# Option B: YAML config file
import yaml
with open("config.yaml") as f:
    config = yaml.safe_load(f)
```

#### 12.1.4 Avoiding Computation in Your DAG Definition

```python
# ❌ BAD: this runs every time the DAG file is parsed (every few seconds!)
result = expensive_api_call()
task = PythonOperator(op_kwargs={"data": result}, ...)

# ✅ GOOD: computation deferred to task execution time
def _my_task():
    result = expensive_api_call()
    # ... process result ...

task = PythonOperator(python_callable=_my_task, ...)
```

#### Using Factories to Generate Common Patterns

```python
def create_etl_tasks(source_name, dag):
    """Factory function generating fetch → transform → load for any source."""
    fetch = PythonOperator(
        task_id=f"fetch_{source_name}",
        python_callable=_fetch,
        op_kwargs={"source": source_name},
        dag=dag,
    )
    transform = PythonOperator(
        task_id=f"transform_{source_name}",
        python_callable=_transform,
        dag=dag,
    )
    load = PythonOperator(
        task_id=f"load_{source_name}",
        python_callable=_load,
        dag=dag,
    )
    fetch >> transform >> load
    return fetch, load

# Generate identical pipelines for multiple sources
for source in ["positions", "trades", "benchmarks"]:
    first, last = create_etl_tasks(source, dag)
    last >> final_report
```

#### Task Groups for Visual Organization

```python
from airflow.utils.task_group import TaskGroup

for source in ["positions", "trades", "benchmarks"]:
    with TaskGroup(source, tooltip=f"ETL for {source}"):
        create_etl_tasks(source, dag)
```

**See Figure 12.3 for task groups in the Airflow UI**

#### Dynamic Task Mapping

```python
# Generate tasks dynamically based on runtime data
@task
def get_source_list():
    return ["positions", "trades", "benchmarks"]

@task
def process_source(source_name):
    # ... process one source ...

with DAG(...):
    sources = get_source_list()
    process_source.expand(source_name=sources)  # creates N parallel task instances
```

**See Figure 12.5 for Dynamic Task Mapping schematic**

### 12.2 Designing Reproducible Tasks

- **Idempotent**: rerunning produces the same result (use UPSERT, overwrite files, include execution date in paths)
- **Deterministic**: same input → same output (avoid implicit dict ordering, unseeded randomness, race conditions)
- **Functional paradigm**: pure functions, no side effects, explicit inputs/outputs

### 12.3 Handling Data Efficiently

- **Filter early**: push WHERE clauses to the source database, not Python
- **Process incrementally**: use `data_interval_start`/`end` to bound queries
- **Cache intermediate data**: write to S3/Postgres between tasks (not local filesystem)
- **Avoid local filesystems**: Workers may be on different machines (especially on EKS) — use shared storage (S3, PVC)
- **Offload heavy work**: Use the database for aggregations (SQL), Spark for big data, SageMaker for ML

### 12.4 Managing Concurrency Using Pools

```python
# Create pool in UI: Admin → Pools → Add → name="postgres_pool", slots=4

# Assign task to pool
load_task = PythonOperator(
    task_id="load_to_postgres",
    python_callable=_load,
    pool="postgres_pool",  # max 4 concurrent tasks hitting Postgres
)
```

> **Migration relevance**: Pools replace Autosys "resources" and "max_run_alarm" — they prevent overwhelming shared databases or APIs during parallel execution.

---

## Chapter 13: Project — Finding the Fastest Way to Get Around NYC

*(Summarized for reusable architectural patterns)*

### Key Architecture Pattern: Raw → Processed → Export

```
S3 (or MinIO)
├── raw/              # Immutable copies of source data
│   ├── citibike/     #   timestamped: {ts_nodash}.json
│   └── taxi/         #   timestamped: {ts_nodash}.csv
├── processed/        # Transformed, normalized data
│   ├── citibike/     #   common schema: {ts_nodash}.parquet
│   └── taxi/         #   common schema: {ts_nodash}.parquet
└── export/           # Ready for consumption
    └── combined/     #   joined data: {ts_nodash}.parquet
```

### Idempotent File Operations

```python
# Include execution timestamp in S3 keys for safe reruns
s3_key = f"raw/trades/{data_interval_start.strftime('%Y%m%d%H%M%S')}.json"
```

### Idempotent Database Writes

```python
def _write_to_postgres(df, table, execution_date):
    with engine.begin() as conn:
        # Delete any existing records from this execution (idempotent)
        conn.execute(f"DELETE FROM {table} WHERE airflow_execution_date = '{execution_date}'")
        df["airflow_execution_date"] = execution_date
        df.to_sql(table, conn, if_exists="append", index=False)
```

---

## Chapter 14: Project — Keeping Family Traditions Alive with Airflow and Generative AI

*(Summarized for reusable patterns)*

### 14.2–14.3 RAG (Retrieval-Augmented Generation) Architecture

- **RAG** = retrieve relevant documents from a vector database, then pass them as context to an LLM
- Advantages over fine-tuning: no retraining needed, always current, source-transparent, cheaper

### Airflow + Vector DB Pipeline Pattern

```
Producer DAG (scheduled):
  1. Fetch new/updated documents from source
  2. Preprocess text (DockerOperator for isolation)
  3. Generate embeddings (embedding model in container)
  4. Upsert to vector database (Weaviate/Milvus/Pinecone)
  5. Delete outdated records

Consumer (on-demand or API-triggered):
  1. Embed user query
  2. Vector similarity search → top-K documents
  3. Pass query + documents to LLM
  4. Return generated response
```

> **Relevance**: If your team builds ML features (factor models, etc.) that need document context (research reports, filings), this RAG + Airflow pattern is directly applicable on EKS.

---

# Part 4 — Airflow in Production

---

## Chapter 15: Operating Airflow in Production

### 15.1 Revisiting the Airflow Architecture

**See Figure 15.1 for production architecture diagram**

All components (API server, scheduler, DAG processor, triggerer, workers) communicate through the **metastore** (Postgres/MySQL). In production, each can be scaled independently.

### 15.2 Choosing the Executor

| Executor | Distributed | Complexity | Best For |
|----------|------------|------------|----------|
| **LocalExecutor** | No | Low | Dev, small-scale, single-machine |
| **CeleryExecutor** | Yes | Medium | Multi-machine, MWAA uses this |
| **KubernetesExecutor** | Yes | High | EKS-native, each task = pod |
| **HybridExecutor** | Yes | High | Mix (e.g., Celery + K8s) |

**LocalExecutor**: Tasks run as subprocesses on the scheduler machine. Max parallelism configurable (default 32). Good for getting started.

**CeleryExecutor**: Tasks distributed via message broker (Redis/RabbitMQ/SQS) to worker machines.

```
AIRFLOW__CORE__EXECUTOR=CeleryExecutor
AIRFLOW__CELERY__BROKER_URL=redis://redis:6379/0
```

**KubernetesExecutor**: Each task launches as a K8s pod. No persistent workers — pods created on demand.

```
AIRFLOW__CORE__EXECUTOR=KubernetesExecutor
```

> ⚠️ **For your setup:**
> - **MWAA** uses CeleryExecutor under the hood with dynamic worker scaling — you don't configure it directly
> - **Self-hosted on EKS**: KubernetesExecutor is the natural fit — each task runs in its own pod, leveraging EKS autoscaling
> - **KubernetesPodOperator** works with ANY executor (including Celery) — it always creates K8s pods regardless of the executor choice

### 15.3 Configuring the Metastore

```bash
# Connection string for production Postgres
AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql://airflow:password@rds-endpoint:5432/airflow

# Useful CLI commands
airflow db migrate    # create/upgrade schema
airflow db check      # verify connectivity
airflow db clean      # delete old records (pass --clean-before-timestamp)
```

- **Production**: Always use external managed database (RDS for MWAA/EKS). Never SQLite.
- MWAA manages this automatically.

### 15.4 Configuring the Scheduler

**Key tuning parameters:**

| Setting | Default | Purpose |
|---------|---------|---------|
| `AIRFLOW__CORE__PARALLELISM` | 32 | Global max concurrent tasks |
| `AIRFLOW__CORE__MAX_ACTIVE_TASKS_PER_DAG` | 16 | Max tasks running per DAG |
| `AIRFLOW__CORE__MAX_ACTIVE_RUNS_PER_DAG` | 16 | Max concurrent DAG runs |
| `AIRFLOW__SCHEDULER__SCHEDULER_HEARTBEAT_SEC` | 5 | Seconds between scheduler loops |

- Multiple schedulers can run simultaneously (row-level DB locking ensures safety). Requires Postgres 9.6+ or MySQL 8+.
- MWAA handles scheduler scaling automatically.

### 15.5 Configuring the DAG Processor Manager

| Setting | Default | Purpose |
|---------|---------|---------|
| `AIRFLOW__DAG_PROCESSOR__MIN_FILE_PROCESS_INTERVAL` | 0 | Min seconds between re-parsing a DAG file |
| `AIRFLOW__DAG_PROCESSOR__PARSING_PROCESSES` | 2 | Max parallel parsing processes |

### 15.6 Capturing Logs

**Three log types:**
1. **API server logs** (web access/error)
2. **Scheduler logs** (task scheduling decisions)
3. **Task logs** (per task instance, per attempt)

**Remote log storage** (critical for distributed/EKS deployments):

```
AIRFLOW__LOGGING__REMOTE_LOGGING=True
AIRFLOW__LOGGING__REMOTE_LOG_CONN_ID=aws_default
AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER=s3://my-airflow-logs/logs
```

> **MWAA**: Logs automatically go to CloudWatch. For self-hosted EKS, configure S3 remote logging.

### 15.7 Visualizing and Monitoring Airflow Metrics

**Pipeline: Airflow → StatsD → Prometheus → Grafana**

```bash
# Enable StatsD metrics
AIRFLOW__METRICS__STATSD_ON=True
AIRFLOW__METRICS__STATSD_HOST=statsd-exporter
AIRFLOW__METRICS__STATSD_PORT=9125
```

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'airflow'
    static_configs:
      - targets: ['statsd-exporter:9102']
```

**See Figure 15.10 for the metrics pipeline diagram**

**Key metrics to monitor:**

| Signal | Metric | Meaning |
|--------|--------|---------|
| Latency | `dagrun.*.first_task_scheduling_delay` | Time from schedule to execution |
| Load | `executor.running_tasks` | Current task load |
| Errors | `ti_failures`, `dag_processing.import_errors` | Task/DAG failures |
| Saturation | `executor.open_slots` | Remaining capacity |

### 15.8 Setting Up Alerts

```python
def _alert_on_failure(context):
    # Send Slack/PagerDuty/email notification
    task_instance = context["task_instance"]
    dag_id = context["dag"].dag_id
    # ... send alert ...

dag = DAG(
    dag_id="critical_pipeline",
    default_args={"on_failure_callback": _alert_on_failure},
    on_failure_callback=_alert_on_failure,  # DAG-level too
)
```

### 15.9 Scaling Airflow Beyond a Single Instance

**Option A: Single instance, multiple teams** — shared infrastructure, simpler ops, but resource contention
**Option B: Instance per team** — full isolation, more operational overhead

> **For your team**: Start with shared MWAA instance. If your DAGs need specific EKS resources (GPU, high memory), use KubernetesPodOperator to run those tasks on dedicated node groups while keeping Airflow on MWAA.

---

## Chapter 16: Securing Airflow

### 16.1 Role-Based Access Control (RBAC)

| Role | Access Level |
|------|-------------|
| `Admin` | Full access (security management) |
| `Op` | View + edit connections, pools, variables |
| `User` | Trigger/pause/clear DAGs, no secrets access |
| `Viewer` | Read-only |
| `Public` | No access (default for unauthenticated) |

```bash
airflow users create --role User --username bobsmith \
    --email firstname@company.com --firstname Bob --lastname Smith \
    --password <secure_password>
```

### 16.2 Encrypting Data at Rest

```python
# Generate Fernet key for encrypting connections/variables in the metastore
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

```
AIRFLOW__CORE__FERNET_KEY=<your-generated-key>
# Or read from file: AIRFLOW__CORE__FERNET_KEY_CMD=cat /secrets/fernet.key
```

- Fernet = symmetric encryption for passwords stored in the metastore
- **Never** store the key in plain text alongside the database

### 16.3 Connecting with a Directory Service (LDAP)

- Integrate with corporate LDAP/Active Directory for SSO
- Configuration in `webserver_config.py`:

```python
from flask_appbuilder.const import AUTH_LDAP
AUTH_TYPE = AUTH_LDAP
AUTH_LDAP_SERVER = "ldap://your-ldap-server:389"
AUTH_LDAP_SEARCH = "dc=companyname,dc=com"
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Viewer"
```

### 16.4 Encrypting Traffic to the Web Server (HTTPS)

```bash
# Generate self-signed cert (dev/internal only)
openssl req -x509 -newkey rsa:4096 -sha256 -nodes -days 365 \
    -keyout privatekey.pem -out certificate.pem \
    -subj "/CN=airflow.internal"
```

```
AIRFLOW__API__SSL_CERT=/path/to/certificate.pem
AIRFLOW__API__SSL_KEY=/path/to/privatekey.pem
```

> **MWAA**: HTTPS is handled automatically. For self-hosted EKS, use an ALB with ACM certificate.

### 16.5 Fetching Credentials from Secrets-Management Systems

```
# Use AWS Secrets Manager as the secrets backend
AIRFLOW__SECRETS__BACKEND=airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend
AIRFLOW__SECRETS__BACKEND_KWARGS={"connections_prefix": "airflow/connections", "variables_prefix": "airflow/variables"}
```

- **Lookup order**: Secrets backend → Environment variables → Airflow metastore
- Supported: AWS Secrets Manager, HashiCorp Vault, Azure Key Vault, GCP Secret Manager

> **For your setup**: Use AWS Secrets Manager. Store database credentials, API keys, and service account tokens there. MWAA has native Secrets Manager integration.

---

## Chapter 17: Airflow Deployment Options

### 17.1 Managed Airflow

#### 17.1.1 Astronomer

- Fully managed Airflow by the company that employs many core Airflow committers
- Available on AWS, Azure, GCP
- Features: in-browser IDE, observability tooling, dbt integration (Cosmos)

#### 17.1.2 Google Cloud Composer

- Managed Airflow on GKE (Google Kubernetes Engine)
- Tight GCP service integration (BigQuery, GCS, Dataflow)

#### 17.1.3 Amazon Managed Workflows for Apache Airflow (MWAA)

- **Executor**: CeleryExecutor with dynamic worker scaling
- **DAG deployment**: Upload to designated S3 bucket
- **Dependencies**: `requirements.txt` in S3 bucket
- **Plugins**: Zip file in S3 bucket
- **Monitoring**: CloudWatch integration
- **Scaling**: Small/medium/large environment sizes; workers auto-scale with load
- **Cost**: Base environment fee + per-worker-hour + metastore storage

> ⚠️ **MWAA does NOT use Lambda for task execution** — it uses CeleryExecutor with Fargate-based workers. There is no Lambda dependency to worry about.
>
> **EKS integration**: From MWAA, use `KubernetesPodOperator` to run tasks on your EKS cluster. MWAA's Airflow scheduler connects to EKS via IAM role. This gives you MWAA's managed scheduler + EKS's compute flexibility.

### 17.2 Airflow on Kubernetes (Self-Hosted on EKS)

#### 17.2.3 Deploying with the Apache Airflow Helm Chart

```bash
# Add Helm repo and install
helm repo add apache-airflow https://airflow.apache.org
helm upgrade --install airflow apache-airflow/airflow \
    --create-namespace --namespace airflow \
    --set apiServer.service.type=LoadBalancer
```

**Pods created:**
- `airflow-api-server` — Web UI
- `airflow-scheduler` — Scheduling loop
- `airflow-dag-processor` — DAG parsing
- `airflow-triggerer` — Deferred task handling
- `airflow-worker` — Task execution (with CeleryExecutor)
- `airflow-redis` — Message broker (Celery)
- `airflow-postgresql` — Metastore (replace with RDS)
- `airflow-statsd` — Metrics

#### 17.2.5 Changing the apiserver Secret Key

```bash
# Create stable secret (prevents pod restarts on helm upgrade)
kubectl create secret generic my-apiserver-secret \
    --namespace airflow \
    --from-literal="api-secret-key=$(python3 -c 'import secrets; print(secrets.token_hex(16))')"
```

#### 17.2.6 Using an External Database

```yaml
# values.yaml — disable built-in Postgres, use RDS
postgresql:
  enabled: false
data:
  metadataSecretName: rds-connection-secret
```

#### 17.2.7 Deploying DAGs — Three Options

**Option 1: Bake into Docker image** (most reproducible)
```dockerfile
FROM apache/airflow:3.1.3
COPY dags/ ${AIRFLOW_HOME}/dags/
```

**Option 2: Persistent Volume** (shared NFS/EFS mount)
```yaml
dags:
  persistence:
    enabled: true
    existingClaim: efs-dags-claim
```

**Option 3: Git-sync sidecar** (auto-pulls from repo)
```yaml
dags:
  gitSync:
    enabled: true
    repo: https://github.com/your-org/airflow-dags.git
    branch: main
    subPath: "dags"
```

> **Recommendation for your team**: Start with **MWAA** for managed simplicity. Use **Git-sync** for DAG deployment (matches your Git workflow). Use **KubernetesPodOperator** to run heavy tasks on EKS. This avoids managing the Airflow infrastructure while still leveraging your existing EKS cluster for compute.

### 17.2.8 Deploying a Python Library

- Package custom hooks/operators as a pip-installable package
- For MWAA: add to `requirements.txt` in S3
- For self-hosted: bake into the Airflow Docker image

### 17.2.9 Configuring the Executor(s)

- Default Helm chart uses CeleryExecutor
- Switch to KubernetesExecutor:
```yaml
executor: "KubernetesExecutor"
```
- With KubernetesExecutor, workers are created as pods on demand — no persistent worker pods needed

### 17.3 Choosing a Deployment Strategy

| Criteria | MWAA | Self-hosted EKS |
|----------|------|-----------------|
| Operational overhead | Low | High |
| Customization | Limited | Full |
| Cost predictability | Environment-based pricing | Pay for what you run |
| Executor choice | CeleryExecutor (fixed) | Any executor |
| K8s integration | Via KubernetesPodOperator | Native |
| Scaling | Auto (workers) | Manual (configure autoscaler) |
| Security | AWS-managed | You manage |

---

# Quick Reference: Autosys → Airflow Migration Cheat Sheet

| Autosys Concept | Airflow Equivalent | Key Chapter |
|----------------|-------------------|-------------|
| `.jil` file | Python DAG file (`.py`) | 2 |
| `insert_job` / `job_type: CMD` | `BashOperator` or `PythonOperator` | 2 |
| `condition: s(prev_job)` | `prev_task >> next_task` | 6 |
| `date_conditions` / `start_times` | `schedule=` (cron, preset, timetable) | 3 |
| `box_name` (grouping) | `TaskGroup` | 12 |
| `std_out_file` / `std_err_file` | Automatic log capture (UI or S3) | 15 |
| `alarm_if_fail` / `notification` | `on_failure_callback` | 15 |
| `watch_file` | `FileSensor` | 7 |
| `sendevent -E FORCE_STARTJOB` | REST API trigger or `airflow dags trigger` | 7 |
| `autorep -j -d` | Web UI grid view | 2 |
| `max_run_alarm` / `resources` | Pools (`pool="my_pool"`) | 12 |
| Environment variables for dates | `{{ logical_date }}`, `{{ ds }}`, `{{ data_interval_start }}` | 5 |
| `profile` (run-as user) | K8s service account / IAM role | 16 |
| Autosys server | MWAA environment or EKS Helm deployment | 17 |