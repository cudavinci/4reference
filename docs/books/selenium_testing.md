# Python Testing with Selenium
**Sujay Raghavendra — Apress, 2021**

---

## Chapter 1: Getting Started

### Overview
- **Selenium** is an open-source tool for automating web browsers, primarily used for testing web applications
- Supports multiple languages (Python, Java, C#, Ruby, JavaScript, Kotlin) and browsers (Firefox, Chrome, Safari, Edge, Opera)
- Originated in 2004 by Jason Huggins at ThoughtWorks; name is a play on a competitor named "Mercury" (selenium is a cure for mercury poisoning)

### Selenium Components
- **Selenium IDE**: Browser extension for record-and-playback test creation (Firefox/Chrome); exports to multiple languages
- **Selenium RC (Remote Control)**: Deprecated predecessor to WebDriver; injected JavaScript into browsers via a server proxy
- **Selenium WebDriver**: Current standard — communicates directly with the browser via native APIs; no intermediary server needed
- **Selenium Grid**: Runs tests in parallel across multiple machines/browsers; uses a hub-node architecture

### Selenium WebDriver Architecture
- **Language Bindings** → **JSON Wire Protocol** → **Browser Drivers** → **Browsers**
- The JSON Wire Protocol uses a REST API (HTTP methods: GET, POST, DELETE) to pass commands between bindings and drivers
- Each browser has its own driver executable (geckodriver, chromedriver, etc.)

### Python Setup
```python
# Install selenium
pip install selenium

# Basic driver instantiation
from selenium import webdriver
driver = webdriver.Firefox()          # requires geckodriver on PATH
driver = webdriver.Chrome()           # requires chromedriver on PATH
driver = webdriver.Safari()           # built-in on macOS
driver = webdriver.Edge()             # requires msedgedriver
driver = webdriver.Opera()            # requires operadriver
```

### Key Driver Methods
```python
driver.get("https://example.com")     # navigate to URL
driver.current_url                     # get current URL
driver.title                           # get page title
driver.page_source                     # get full HTML source
driver.close()                         # close current tab/window
driver.quit()                          # close all windows and end session
```

### `get()` vs `navigate()`
- `driver.get(url)` — loads a new page, waits for `onload` to fire
- `driver.navigate().to(url)` — (Java-style) does not wait for full load; not commonly used in Python
- In Python, navigation is done via `driver.back()`, `driver.forward()`, `driver.refresh()`

---

## Chapter 2: Locating Elements

### Why Locators Matter
- Every interaction in Selenium requires first *locating* a web element on the page
- Selenium provides **8 locator strategies**, each with a single-element and multiple-element variant

### Locator Strategies

| Strategy | Single Element | Multiple Elements |
|---|---|---|
| ID | `find_element_by_id('val')` | `find_elements_by_id('val')` |
| Name | `find_element_by_name('val')` | `find_elements_by_name('val')` |
| XPath | `find_element_by_xpath('expr')` | `find_elements_by_xpath('expr')` |
| CSS Selector | `find_element_by_css_selector('sel')` | `find_elements_by_css_selector('sel')` |
| Link Text | `find_element_by_link_text('text')` | `find_elements_by_link_text('text')` |
| Partial Link Text | `find_element_by_partial_link_text('t')` | `find_elements_by_partial_link_text('t')` |
| Tag Name | `find_element_by_tag_name('tag')` | `find_elements_by_tag_name('tag')` |
| Class Name | `find_element_by_class_name('cls')` | `find_elements_by_class_name('cls')` |

> **Note:** The `find_element_by_*` methods are deprecated in Selenium 4+. Modern usage:
> ```python
> from selenium.webdriver.common.by import By
> driver.find_element(By.ID, 'value')
> driver.find_elements(By.XPATH, '//div')
> ```

### ID Locator
- Fastest and most reliable — IDs should be unique per page
- `find_element_by_id('username')` targets `<input id="username">`
- Returns `NoSuchElementException` if not found

### Name Locator
- Targets the `name` attribute; not guaranteed unique
- `find_element_by_name('email')` targets `<input name="email">`
- `find_elements_by_name()` returns a list when multiple elements share the same name

### XPath Locator
- Most flexible and powerful; can navigate entire DOM tree
- **Absolute XPath**: starts from root `/html/body/div[1]/form/input[2]` — brittle, breaks with DOM changes
- **Relative XPath**: starts with `//` — more robust

#### XPath Syntax
```
//tagname[@attribute='value']
```

#### XPath with Logical Operators
```python
# AND — both conditions must be true
driver.find_element_by_xpath("//input[@id='user' and @name='username']")

# OR — either condition can be true
driver.find_element_by_xpath("//input[@id='user' or @name='username']")
```

#### XPath Functions
```python
# contains() — partial attribute match
driver.find_element_by_xpath("//input[contains(@id, 'user')]")

# text() — match visible text content
driver.find_element_by_xpath("//label[text()='Username']")

# starts-with() — attribute prefix match
driver.find_element_by_xpath("//input[starts-with(@id, 'user')]")
```

#### XPath Axes (13 methods for DOM traversal)
- `ancestor` — all ancestors up to root
- `ancestor-or-self` — ancestors including current node
- `child` — direct children
- `descendant` — all children/grandchildren/etc.
- `descendant-or-self` — descendants including current node
- `following` — everything after the closing tag
- `following-sibling` — siblings after current node
- `parent` — direct parent
- `preceding` — everything before the opening tag
- `preceding-sibling` — siblings before current node
- `self` — the current node
- `attribute` — all attributes of the current node
- `namespace` — namespace nodes

```python
# Example: find parent of an element
driver.find_element_by_xpath("//input[@id='user']/parent::div")

# Example: find following sibling
driver.find_element_by_xpath("//label[@id='lbl']/following-sibling::input")
```

### CSS Selector Locator
- Generally faster than XPath in most browsers
- Cannot traverse upward in the DOM (no parent selection)

#### CSS Selector Syntax
```python
# By ID (#)
driver.find_element_by_css_selector("#username")

# By Class (.)
driver.find_element_by_css_selector(".form-control")

# By Attribute
driver.find_element_by_css_selector("input[name='email']")

# Substring matching
driver.find_element_by_css_selector("input[id^='user']")   # starts with
driver.find_element_by_css_selector("input[id$='name']")   # ends with
driver.find_element_by_css_selector("input[id*='ser']")    # contains

# Direct child (>)
driver.find_element_by_css_selector("form > input")

# nth-of-type
driver.find_element_by_css_selector("input:nth-of-type(2)")

# Inner text (non-standard, limited support)
driver.find_element_by_css_selector("a:contains('Login')")
```

### Link Text and Partial Link Text
- Only works on `<a>` (anchor) elements
```python
# Exact match of visible link text
driver.find_element_by_link_text("Click Here")

# Partial match
driver.find_element_by_partial_link_text("Click")
```

### Tag Name Locator
- Locates by HTML tag — useful when few elements of that tag exist
```python
driver.find_element_by_tag_name("h1")
driver.find_elements_by_tag_name("a")  # all links on page
```

### Class Name Locator
- Targets the `class` attribute
- Compound classes (e.g., `class="btn btn-primary"`) must be targeted one class at a time
```python
driver.find_element_by_class_name("btn-primary")
```

---

## Chapter 3: Mouse and Keyboard Actions

### ActionChains
- **ActionChains** queue up a series of input actions and execute them in order via `.perform()`
- Import: `from selenium.webdriver.common.action_chains import ActionChains`

```python
actions = ActionChains(driver)
actions.move_to_element(element).click().perform()
```

### Mouse Actions

#### click()
```python
ActionChains(driver).click(element).perform()
# or simply
element.click()
```

#### double_click()
```python
ActionChains(driver).double_click(element).perform()
```

#### context_click() (right-click)
```python
ActionChains(driver).context_click(element).perform()
```

#### click_and_hold()
```python
ActionChains(driver).click_and_hold(element).perform()
```

#### drag_and_drop()
```python
# Drag source element to target element
ActionChains(driver).drag_and_drop(source, target).perform()
```

#### drag_and_drop_by_offset()
```python
# Drag element by pixel offset (x, y)
ActionChains(driver).drag_and_drop_by_offset(element, 100, 50).perform()
```

#### move_to_element() (hover)
```python
ActionChains(driver).move_to_element(element).perform()
```

#### release()
```python
# Release a held click
ActionChains(driver).click_and_hold(element).release().perform()
```

### Keyboard Actions
- Import: `from selenium.webdriver.common.keys import Keys`

#### key_down() / key_up()
```python
# Hold Shift while typing
ActionChains(driver).key_down(Keys.SHIFT).send_keys("hello").key_up(Keys.SHIFT).perform()
# Result: "HELLO"
```

#### send_keys() / send_keys_to_element()
```python
# send_keys acts on the focused element
ActionChains(driver).send_keys("some text").perform()

# send_keys_to_element targets a specific element
ActionChains(driver).send_keys_to_element(element, "text").perform()
```

#### Common Keys Constants
```python
Keys.ENTER, Keys.RETURN, Keys.TAB, Keys.ESCAPE
Keys.BACKSPACE, Keys.DELETE
Keys.ARROW_UP, Keys.ARROW_DOWN, Keys.ARROW_LEFT, Keys.ARROW_RIGHT
Keys.SHIFT, Keys.CONTROL, Keys.ALT, Keys.COMMAND
Keys.HOME, Keys.END, Keys.PAGE_UP, Keys.PAGE_DOWN
Keys.F1 through Keys.F12
```

#### pause()
```python
# Pause between actions (seconds)
ActionChains(driver).click(el1).pause(2).click(el2).perform()
```

#### reset_actions()
```python
# Clear all queued actions
actions = ActionChains(driver)
actions.click(element)
actions.reset_actions()  # clears the queue
```

---

## Chapter 4: Web Elements

### What Is a Web Element?
- Any HTML component on a page: text fields, buttons, links, dropdowns, images, etc.
- In Selenium, interacting with an element requires first locating it, then calling methods on the returned `WebElement` object

### Key WebElement Properties and Methods
```python
element.text                    # visible text content
element.tag_name                # HTML tag name (e.g., 'input', 'div')
element.size                    # dict with 'height' and 'width'
element.location                # dict with 'x' and 'y' pixel coordinates
element.rect                    # combined: x, y, height, width
element.is_displayed()          # True if visible
element.is_enabled()            # True if interactable
element.is_selected()           # True if checked/selected (checkboxes, radios)
element.get_attribute('href')   # get any HTML attribute value
element.get_property('value')   # get DOM property (e.g., current input value)
element.value_of_css_property('color')  # get computed CSS property
element.screenshot('el.png')    # screenshot of just this element
```

### Web Tables
- HTML tables use `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>`
- Access cells via XPath indexing:
```python
# Get value of row 2, column 3
cell = driver.find_element_by_xpath("//table[@id='t1']/tbody/tr[2]/td[3]")
print(cell.text)

# Count rows
rows = driver.find_elements_by_xpath("//table[@id='t1']/tbody/tr")
print(len(rows))

# Iterate entire table
for row in rows:
    cells = row.find_elements_by_tag_name("td")
    for cell in cells:
        print(cell.text, end=" | ")
    print()
```

### Date Pickers
- Common patterns: text input with calendar popup, native `<input type="date">`, JavaScript widget
```python
# Direct value injection via JavaScript for stubborn date pickers
driver.execute_script(
    "document.getElementById('datepicker').value = '2021-03-15'"
)

# Or via send_keys
date_input = driver.find_element_by_id("datepicker")
date_input.clear()
date_input.send_keys("03/15/2021")
```

---

## Chapter 5: Navigation

### Navigating with Hyperlinks
```python
# By link text
driver.find_element_by_link_text("About Us").click()

# By partial link text
driver.find_element_by_partial_link_text("About").click()

# By XPath
driver.find_element_by_xpath("//a[@href='/about']").click()

# By CSS selector
driver.find_element_by_css_selector("a[href='/about']").click()

# Nth link on the page
links = driver.find_elements_by_tag_name("a")
links[3].click()  # click the 4th link (0-indexed)
```

### Testing Hyperlinks (Broken Link Checker)
```python
import requests

links = driver.find_elements_by_tag_name("a")
for link in links:
    url = link.get_attribute("href")
    if url:
        try:
            response = requests.head(url, allow_redirects=True, timeout=5)
            if response.status_code >= 400:
                print(f"BROKEN: {url} → {response.status_code}")
            else:
                print(f"OK: {url} → {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"ERROR: {url} → {e}")
```

### HTTP Status Code Categories
- **1xx**: Informational
- **2xx**: Success (200 OK, 201 Created)
- **3xx**: Redirection (301 Moved Permanently, 302 Found)
- **4xx**: Client Error (400 Bad Request, 403 Forbidden, 404 Not Found)
- **5xx**: Server Error (500 Internal Server Error, 503 Service Unavailable)

### Checking for Broken Images
```python
images = driver.find_elements_by_tag_name("img")
for img in images:
    # Check naturalWidth — broken images have width 0
    is_loaded = driver.execute_script(
        "return arguments[0].naturalWidth > 0", img
    )
    src = img.get_attribute("src")
    if not is_loaded:
        print(f"BROKEN IMAGE: {src}")
```

### Browser Navigation Methods
```python
driver.back()       # browser back button
driver.forward()    # browser forward button
driver.refresh()    # reload current page
```

---

## Chapter 6: Buttons, Checkboxes, and Radio Buttons

### Button Types
- **Default button**: `<button>Click Me</button>` or `<input type="button" value="Click">`
- **Submit button**: `<input type="submit" value="Submit">` — submits the parent form
- **Image button**: `<input type="image" src="btn.png">` — acts as a submit with an image
- **Reset button**: `<input type="reset">` — resets form fields to defaults

### Clicking Buttons
```python
# Standard click
driver.find_element_by_id("submitBtn").click()

# Submit a form directly (on any element inside the form)
driver.find_element_by_id("myForm").submit()

# Using JavaScript for elements obscured by overlays
driver.execute_script("arguments[0].click();", button_element)
```

### Checkboxes
```python
checkbox = driver.find_element_by_id("agree")

# Check if currently selected
if not checkbox.is_selected():
    checkbox.click()  # check it

# Uncheck
if checkbox.is_selected():
    checkbox.click()  # uncheck it

# Count selected checkboxes
checkboxes = driver.find_elements_by_css_selector("input[type='checkbox']")
selected = [cb for cb in checkboxes if cb.is_selected()]
print(f"{len(selected)} of {len(checkboxes)} checked")
```

### Radio Buttons
```python
# Select a radio button by value
radios = driver.find_elements_by_name("gender")
for radio in radios:
    if radio.get_attribute("value") == "male":
        radio.click()
        break

# Check which radio is selected
for radio in radios:
    if radio.is_selected():
        print(f"Selected: {radio.get_attribute('value')}")
```

### Button/Element Assertion Methods
```python
element.is_displayed()   # visible on page?
element.is_enabled()     # not disabled?
element.is_selected()    # checked/selected? (checkboxes, radios, options)
element.get_attribute("class")  # read any attribute
```

### Select (Dropdown) Lists
- Import: `from selenium.webdriver.support.select import Select`

#### Single Select
```python
dropdown = Select(driver.find_element_by_id("country"))

dropdown.select_by_visible_text("United States")
dropdown.select_by_value("us")
dropdown.select_by_index(2)  # 0-indexed

# Get currently selected option
print(dropdown.first_selected_option.text)

# Get all options
for option in dropdown.options:
    print(option.text)
```

#### Multiple Select
```python
multi = Select(driver.find_element_by_id("languages"))

multi.select_by_visible_text("Python")
multi.select_by_visible_text("JavaScript")

# Get all selected
for opt in multi.all_selected_options:
    print(opt.text)

# Deselect
multi.deselect_by_visible_text("Python")
multi.deselect_by_value("js")
multi.deselect_by_index(0)
multi.deselect_all()
```

> **Note:** `deselect_*` methods only work on `<select multiple>` elements. Calling them on a single-select raises `NotImplementedError`.

---

## Chapter 7: Frames and Textboxes

### Frames and iFrames
- **Frame**: `<frame>` (deprecated HTML4) — divides window into sections
- **iFrame**: `<iframe>` — embeds another HTML document within the current page
- Selenium can only interact with elements inside one frame at a time; you must explicitly switch

#### Switching to a Frame
```python
# By ID or Name attribute
driver.switch_to.frame("frame_id")
driver.switch_to.frame("frame_name")

# By index (0-based)
driver.switch_to.frame(0)  # first frame on the page

# By WebElement
frame_el = driver.find_element_by_xpath("//iframe[@class='content']")
driver.switch_to.frame(frame_el)
```

#### Switching Back
```python
# Back to the main (top-level) document
driver.switch_to.default_content()

# Back to the parent frame (one level up)
driver.switch_to.parent_frame()
```

#### Nested Frames
```python
# To interact with a nested frame: switch sequentially
driver.switch_to.frame("outer_frame")
driver.switch_to.frame("inner_frame")
# ... interact with inner frame elements ...
driver.switch_to.default_content()  # back to top
```

#### Frames with Explicit Waits
```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Wait until frame is available, then switch
WebDriverWait(driver, 10).until(
    EC.frame_to_be_available_and_switch_to_it("frame_id")
)
```

### Textboxes

#### Single-Line Input
```python
textbox = driver.find_element_by_id("username")
textbox.clear()                  # clear existing text
textbox.send_keys("my_user")    # type into the field

# Read current value
current_val = textbox.get_property("value")
# Note: .text returns empty string for input fields; use get_property('value')
```

#### Multi-Line Textarea
```python
textarea = driver.find_element_by_id("comments")
textarea.clear()
textarea.send_keys("Line 1\nLine 2\nLine 3")
```

#### Common Input Attributes
```python
textbox.get_attribute("placeholder")   # placeholder text
textbox.get_attribute("maxlength")     # max allowed characters
textbox.get_attribute("type")          # text, password, email, etc.
textbox.get_attribute("readonly")      # None if not readonly
textbox.get_attribute("disabled")      # "true" if disabled
```

---

## Chapter 8: Assertions

### What Are Assertions?
- **Assertion**: a check that verifies an expected condition is true; if false, the test fails
- In Python Selenium testing, assertions come from the `unittest` module
- Assertions are the mechanism by which a test becomes a *test* (as opposed to just a script)

### unittest Assertion Methods

#### Boolean Assertions
```python
import unittest

class TestExample(unittest.TestCase):
    def test_booleans(self):
        self.assertTrue(expr)        # passes if expr is truthy
        self.assertFalse(expr)       # passes if expr is falsy
```

#### Equality Assertions
```python
self.assertEqual(a, b)          # a == b
self.assertNotEqual(a, b)       # a != b
```

#### Identity Assertions
```python
self.assertIs(a, b)             # a is b (same object)
self.assertIsNot(a, b)          # a is not b
self.assertIsNone(a)            # a is None
self.assertIsNotNone(a)         # a is not None
```

#### Type Assertions
```python
self.assertIsInstance(a, list)       # isinstance(a, list)
self.assertNotIsInstance(a, str)     # not isinstance(a, str)
```

#### Comparison Assertions
```python
self.assertGreater(a, b)        # a > b
self.assertGreaterEqual(a, b)   # a >= b
self.assertLess(a, b)           # a < b
self.assertLessEqual(a, b)      # a <= b
```

#### Membership Assertions
```python
self.assertIn(a, b)             # a in b
self.assertNotIn(a, b)          # a not in b
```

#### Collection Assertions
```python
self.assertListEqual([1, 2], [1, 2])
self.assertTupleEqual((1, 2), (1, 2))
self.assertSetEqual({1, 2}, {1, 2})
self.assertDictEqual({"a": 1}, {"a": 1})
```

### Practical Selenium Assertion Examples
```python
class TestLogin(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.get("https://example.com/login")

    def test_page_title(self):
        self.assertEqual(self.driver.title, "Login Page")

    def test_element_present(self):
        elem = self.driver.find_element_by_id("username")
        self.assertTrue(elem.is_displayed())

    def test_button_enabled(self):
        btn = self.driver.find_element_by_id("submit")
        self.assertTrue(btn.is_enabled())

    def test_url_after_login(self):
        # ... perform login steps ...
        self.assertIn("/dashboard", self.driver.current_url)

    def tearDown(self):
        self.driver.quit()

if __name__ == "__main__":
    unittest.main()
```

### Test Outcomes
- **Pass (OK)**: all assertions passed
- **Fail**: an assertion evaluated to False — `AssertionError` raised
- **Error**: an unexpected exception occurred during the test (not an assertion failure)

---

## Chapter 9: Exceptions

### Common Selenium Exceptions
- All Selenium exceptions inherit from `selenium.common.exceptions.WebDriverException`

| Exception | Cause |
|---|---|
| `NoSuchElementException` | Element not found with given locator |
| `StaleElementReferenceException` | Element is no longer attached to the DOM (page refreshed/changed) |
| `ElementNotInteractableException` | Element exists but cannot be interacted with (hidden, overlapping) |
| `ElementClickInterceptedException` | Another element is covering the target element |
| `ElementNotVisibleException` | Element is present in DOM but not visible |
| `ElementNotSelectableException` | Trying to select a non-selectable element |
| `TimeoutException` | Explicit wait condition not met within timeout |
| `NoSuchFrameException` | Frame not found for switch_to |
| `NoSuchWindowException` | Window/tab not found for switch_to |
| `NoAlertPresentException` | No alert dialog open when expected |
| `InvalidSelectorException` | Malformed XPath/CSS selector |
| `InvalidElementStateException` | Element state doesn't allow the requested operation |
| `MoveTargetOutOfBoundsException` | ActionChains target is outside the viewport |
| `UnexpectedAlertPresentException` | An unexpected alert is blocking interaction |
| `ConnectionClosedException` | Browser connection lost (crash, manual close) |
| `InsecureCertificateException` | Site has an invalid SSL certificate |
| `NoSuchAttributeException` | Requested attribute doesn't exist on the element |
| `NoSuchCookieException` | Cookie not found by name |
| `SessionNotCreatedException` | WebDriver session could not be started |
| `ScreenshotException` | Screenshot capture failed |

### Exception Handling in Tests
```python
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException
)

class TestWithExceptions(unittest.TestCase):
    def test_element_exists(self):
        try:
            element = self.driver.find_element_by_id("maybe_missing")
            self.assertTrue(element.is_displayed())
        except NoSuchElementException:
            self.fail("Expected element #maybe_missing was not found in the DOM")

    def test_stale_element_retry(self):
        element = self.driver.find_element_by_id("dynamic")
        self.driver.refresh()  # element reference is now stale
        try:
            element.click()
        except StaleElementReferenceException:
            # Re-locate after refresh
            element = self.driver.find_element_by_id("dynamic")
            element.click()
```

### Best Practices
- Use explicit waits instead of catching `NoSuchElementException` in loops
- Catch specific exceptions, not bare `except:` or `except Exception:`
- Use `try/except` in tests when you want custom failure messages or recovery logic
- `StaleElementReferenceException` usually means you need to re-locate the element

---

## Chapter 10: Waits

### Why Waits Are Needed
- Web pages load asynchronously — elements may not be immediately available
- Without waits, tests will fail with `NoSuchElementException` on slow-loading elements
- Three strategies: **implicit waits**, **explicit waits**, and **fluent waits**

### Implicit Wait
- Sets a global timeout for all `find_element` calls
- If element isn't found immediately, Selenium polls the DOM until timeout expires
- Set once, applies to all subsequent find operations for that driver session
```python
driver = webdriver.Firefox()
driver.implicitly_wait(10)  # wait up to 10 seconds for any element lookup
driver.get("https://example.com")
# This will wait up to 10s if #dynamic doesn't exist yet
element = driver.find_element_by_id("dynamic")
```
- **Drawback**: applies uniformly — can slow down tests that legitimately need to verify element absence

### Explicit Wait
- Waits for a *specific condition* to be met, with a per-call timeout
- More granular and preferred over implicit waits
- Uses `WebDriverWait` + `expected_conditions`

```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Wait up to 10s for element to be clickable
element = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "submitBtn"))
)
element.click()
```

### Expected Conditions (EC)

| Condition | Description |
|---|---|
| `title_is("Title")` | Page title equals exactly |
| `title_contains("Part")` | Page title contains substring |
| `url_contains("/dashboard")` | Current URL contains substring |
| `url_to_be("https://...")` | Current URL equals exactly |
| `url_changes("https://old")` | URL has changed from given value |
| `presence_of_element_located(loc)` | Element exists in DOM (may not be visible) |
| `visibility_of_element_located(loc)` | Element is visible on page |
| `visibility_of(element)` | Given WebElement is visible |
| `invisibility_of_element_located(loc)` | Element is not visible or not present |
| `element_to_be_clickable(loc)` | Element is visible and enabled |
| `staleness_of(element)` | Element is no longer attached to DOM |
| `text_to_be_present_in_element(loc, txt)` | Element's `.text` contains given text |
| `text_to_be_present_in_element_value(loc, txt)` | Element's `value` attribute contains text |
| `frame_to_be_available_and_switch_to_it(loc)` | Frame is available and driver switches to it |
| `alert_is_present()` | An alert dialog is open |
| `element_to_be_selected(element)` | Element is selected |
| `element_located_to_be_selected(loc)` | Located element is selected |
| `number_of_windows_to_be(n)` | Exactly n windows are open |
| `new_window_is_opened(handles)` | A new window has opened since given handles |

### Fluent Wait
- Like explicit wait but allows customization of polling interval and which exceptions to ignore
```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, ElementNotVisibleException

wait = WebDriverWait(
    driver,
    timeout=30,
    poll_frequency=2,  # check every 2 seconds (default is 0.5)
    ignored_exceptions=[NoSuchElementException, ElementNotVisibleException]
)
element = wait.until(EC.visibility_of_element_located((By.ID, "slow_element")))
```

### Custom Wait Conditions
```python
# Using a lambda
element = WebDriverWait(driver, 10).until(
    lambda d: d.find_element_by_id("loaded") if d.find_element_by_id("loaded").text != "" else False
)

# Using a callable class
class element_has_text:
    def __init__(self, locator, text):
        self.locator = locator
        self.text = text

    def __call__(self, driver):
        element = driver.find_element(*self.locator)
        if self.text in element.text:
            return element
        return False

element = WebDriverWait(driver, 10).until(
    element_has_text((By.ID, "status"), "Complete")
)
```

### Implicit vs Explicit: Best Practices
- **Do not mix** implicit and explicit waits — can cause unpredictable timeout behavior
- Prefer explicit waits for most cases (more precise, self-documenting)
- If you must use implicit waits, keep them short (2-5 seconds)

---

## Chapter 11: Page Object Model (POM)

### What Is POM?
- **Page Object Model** is a design pattern that creates an object-oriented representation of each web page
- Each page gets its own class encapsulating locators and interactions
- Test scripts call page object methods instead of directly using Selenium APIs

### Why POM?
- **Reduces duplication**: locators defined once, reused across tests
- **Improves maintenance**: if the UI changes, only the page object needs updating
- **Shorter test cases**: test methods read like high-level user stories
- **Reusability**: page objects can be shared across test suites

### POM File Structure
```
project/
├── tests/
│   └── test_login.py       # Test cases
├── pages/
│   └── login_page.py       # Page object (locators + actions)
├── elements/
│   └── base_elements.py    # Reusable element wrappers (optional)
└── locators/
    └── login_locators.py   # Locator constants
```

### POM Implementation Example

**locators/login_locators.py**
```python
from selenium.webdriver.common.by import By

class LoginPageLocators:
    USERNAME = (By.ID, "username")
    PASSWORD = (By.ID, "password")
    LOGIN_BTN = (By.ID, "loginBtn")
    ERROR_MSG = (By.CSS_SELECTOR, ".error-message")
```

**pages/login_page.py**
```python
from locators.login_locators import LoginPageLocators

class LoginPage:
    def __init__(self, driver):
        self.driver = driver

    def enter_username(self, username):
        field = self.driver.find_element(*LoginPageLocators.USERNAME)
        field.clear()
        field.send_keys(username)

    def enter_password(self, password):
        field = self.driver.find_element(*LoginPageLocators.PASSWORD)
        field.clear()
        field.send_keys(password)

    def click_login(self):
        self.driver.find_element(*LoginPageLocators.LOGIN_BTN).click()

    def get_error_message(self):
        return self.driver.find_element(*LoginPageLocators.ERROR_MSG).text

    def login(self, username, password):
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()
```

**tests/test_login.py**
```python
import unittest
from selenium import webdriver
from pages.login_page import LoginPage

class TestLogin(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.get("https://example.com/login")
        self.login_page = LoginPage(self.driver)

    def test_valid_login(self):
        self.login_page.login("admin", "password123")
        self.assertIn("/dashboard", self.driver.current_url)

    def test_invalid_login_shows_error(self):
        self.login_page.login("bad_user", "wrong_pass")
        error = self.login_page.get_error_message()
        self.assertEqual(error, "Invalid credentials")

    def tearDown(self):
        self.driver.quit()

if __name__ == "__main__":
    unittest.main()
```

### POM Limitations
- **Initial setup time**: more files and structure upfront
- **Requires discipline**: team must consistently follow the pattern
- **Fixed model**: changes to page structure require updating the corresponding page object
- **Overhead for small projects**: may be excessive for simple one-off scripts

---

## Chapter 12: unittest Framework

### unittest Overview
- Python's built-in testing framework (inspired by JUnit)
- Part of the standard library — no installation required
- Key concepts: **TestCase**, **test fixtures**, **test suites**, **test runner**

### Test Case Structure
```python
import unittest
from selenium import webdriver

class TestSearchFeature(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Runs once before all tests in this class."""
        cls.driver = webdriver.Firefox()

    def setUp(self):
        """Runs before each individual test method."""
        self.driver.get("https://example.com")

    def test_search_valid_term(self):
        """Test methods must start with 'test_'."""
        # ... test logic ...
        self.assertEqual(self.driver.title, "Search Results")

    def test_search_empty_term(self):
        # ... test logic ...
        self.assertIn("error", self.driver.page_source)

    def tearDown(self):
        """Runs after each individual test method."""
        pass  # e.g., clear cookies, reset state

    @classmethod
    def tearDownClass(cls):
        """Runs once after all tests in this class."""
        cls.driver.quit()

if __name__ == "__main__":
    unittest.main()
```

### Fixture Hierarchy (Execution Order)
1. `setUpModule()` — once before all classes in the module
2. `setUpClass()` — once before all tests in a class (`@classmethod`)
3. `setUp()` — before each test method
4. `test_*()` — the actual test
5. `tearDown()` — after each test method
6. `tearDownClass()` — once after all tests in a class (`@classmethod`)
7. `tearDownModule()` — once after all classes in the module

```python
def setUpModule():
    print("Module setup — runs once at the very start")

def tearDownModule():
    print("Module teardown — runs once at the very end")

class TestExample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("Class setup — once per class")

    def setUp(self):
        print("Test setup — before each test")

    def test_alpha(self):
        print("Running test_alpha")

    def test_beta(self):
        print("Running test_beta")

    def tearDown(self):
        print("Test teardown — after each test")

    @classmethod
    def tearDownClass(cls):
        print("Class teardown — once per class")
```

### Test Execution Order
- Tests run in **alphabetical order** by method name within each class
- `test_alpha` runs before `test_beta`
- Tests should be **independent** — never rely on execution order

### Running Tests
```bash
# Run all tests in a file
python -m unittest test_login.py

# Run a specific test class
python -m unittest test_login.TestLogin

# Run a specific test method
python -m unittest test_login.TestLogin.test_valid_login

# Verbose output
python -m unittest -v test_login.py

# Auto-discover tests (finds test_*.py files)
python -m unittest discover -s tests/ -p "test_*.py"
```

### Screenshots in Tests
```python
class TestWithScreenshots(unittest.TestCase):
    def test_capture_page(self):
        self.driver.get("https://example.com")

        # Save screenshot to file
        self.driver.save_screenshot("screenshot.png")

        # Alternative method — returns True/False
        self.driver.get_screenshot_as_file("page.png")

        # Get as base64 string (useful for reports)
        b64_img = self.driver.get_screenshot_as_base64()

        # Get as PNG binary
        png_bytes = self.driver.get_screenshot_as_png()
```

### Capturing Screenshots on Failure
```python
class TestWithFailureScreenshots(unittest.TestCase):
    def tearDown(self):
        # Check if the test failed
        if hasattr(self, '_outcome'):
            result = self._outcome.result
            if result and result.failures or result.errors:
                test_name = self._testMethodName
                self.driver.save_screenshot(f"failure_{test_name}.png")
        self.driver.quit()
```

### Test Suites
```python
# Create a custom suite
def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(TestLogin("test_valid_login"))
    test_suite.addTest(TestLogin("test_invalid_login_shows_error"))
    test_suite.addTest(TestSearch("test_search_valid_term"))
    return test_suite

if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())
```

### Alternative Python Testing Tools (Comparison)

| Tool | Key Feature | Use Case |
|---|---|---|
| **unittest** | Built-in, class-based, JUnit-style | Standard test structure with fixtures |
| **pytest** | Minimal boilerplate, powerful fixtures, plugins | Most popular; preferred for new projects |
| **doctest** | Tests embedded in docstrings | Simple function-level examples |
| **nose2** | Extends unittest with auto-discovery | Legacy projects using unittest |
| **Robot Framework** | Keyword-driven, non-programmer friendly | Acceptance testing, BDD-style |
| **Testify** | Extends unittest with additional features | Advanced fixture management |

---

## Appendix: Quick Reference

### Minimal Selenium Test Template
```python
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestTemplate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = webdriver.Firefox()
        cls.driver.implicitly_wait(5)

    def test_example(self):
        self.driver.get("https://example.com")
        heading = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.TAG_NAME, "h1"))
        )
        self.assertEqual(heading.text, "Example Domain")

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

if __name__ == "__main__":
    unittest.main()
```

### Locator Strategy Decision Guide
1. **Has a unique `id`?** → Use `By.ID`
2. **Has a unique `name`?** → Use `By.NAME`
3. **Is a link with known text?** → Use `By.LINK_TEXT` or `By.PARTIAL_LINK_TEXT`
4. **Can be targeted by CSS?** → Use `By.CSS_SELECTOR` (faster than XPath)
5. **Needs DOM traversal or complex logic?** → Use `By.XPATH`
6. **Last resort** → `By.TAG_NAME` or `By.CLASS_NAME`