# Code Snippets

Welcome back.  

## GIT

### Commands

| Command | Description |
| :------ | :----------- |
| `git checkout dev`<br>`git pull`<br>`git checkout -b feature-1`<br>[make changes]<br>`git commit -am "feature changes"`<br>`git push origin feature-1`<br>`git checkout dev`<br>`git rebase feature-1`<br>`git push`<br>`git checkout main`<br>`git pull`<br>`git merge dev`<br>`git push` | Gitflow -- rebase feature branches into dev<br>Then merge dev into main |
| `git remote add origin git@github.com:USERNAME/REPO_NAME.git` | Add remote origin (when not set) |
| `git remote set-url origin git@github.com:USERNAME/REPO_NAME.git` | Set remote origin (overwrite existing) |
| `git rm --cached FILE_OR_DIR_NAME`<br>`git commit -m "Removed FILE_OR_DIR_NAME from repository"`<br>`git push origin master` | Remove local already-pushed file from remote.<br>**Be careful if you mess with .gitignore, change branches, then merge<br>Local files will get deleted** |
| `git config --get remote.origin.url` | Get git remote origin's URL. |
| `git diff --cached origin/main` | Compare committed (pre-push) local changes to remote (all contents).<br>This opens the `less` editor.<br>`n`: Next change<br>`N`: Previous change<br>`spacebar`: Pagedown<br>`b`: Pageup<br>`q`: Quit<br>`?`: Help |
| `git diff --cached origin/main --name-only` | Compare committed (pre-push) local changes to remote (filenames only). |
| `git reset --hard --force` | Force-update local repo state to match remote branch (**overwrites** -- stash). |
| `git diff` | Show unstaged changes (working tree vs index). |
| `git diff --staged` | Show staged changes (index vs last commit). Alias for `--cached`. |
| `git diff HEAD` | Show all changes — staged and unstaged — vs last commit. |
| `git diff <commit>` | Compare working tree against a specific commit or branch tip. |
| `git diff <branch-a>..<branch-b>` | Compare the tips of two branches. Useful before a merge or PR review. |
| `git diff --stat` | Summary view: files changed, insertions, deletions. No full patch. |
| `git diff --word-diff` | Highlight changes at the word level instead of line level. Great for prose or config files. |
| `git reset --soft HEAD~1` | Undo most recent _local_ commit (to staging). |
| `git reset --mixed HEAD~1` | Undo most recent _local_ commit (to unstaged). |
| `git rm file_to_delete`<br>`git commit -m "removed file_to_delete"`<br>`git push origin master` | Delete file from remote and local. |
| `git rm -r folder_to_delete`<br>`git commit -m "removed folder_to_delete"`<br>`git push origin master` | Delete folder from remote and local. |
| `git rm --cached file_to_delete`<br>`git commit -m "removed file_to_delete"`<br>`git push origin master` | Delete file from remote only. |
| `git fetch origin`<br>`git ls-tree -r master --name-only` | List all files on remote master. |
| `git commit -am "commit message"` | Add and commit all changes. |
| `git clean -f` | Force-remove untracked files. |
| `git clean -fd` | Force-remove untracked directories. |
| `cd subdirectory`<br>`sudo rm -rf .git` | Force-remove subdirectory's sub-git repo. |
| `git branch new-branch`<br>`git checkout new-branch`<br>[make changes]<br>`git add -A`<br>`git commit -m "commit message"`<br>`git push origin new-branch`<br>`git branch -d new-branch` | Create new branch, make changes, push, and delete branch locally. |
| `git log origin/<branch-name>..HEAD` | View local commits not yet pushed to remote. |
| `git checkout <hash> -- <file>` | Pull a specific file out of any commit into your working tree. Classic form of the above. |
| `git show <commit>` | Show the diff and metadata for a specific commit. |
| `git show <commit>:<file>` | Print a file exactly as it was at a given commit. No checkout needed. |
| `git restore <file>` | Discard unstaged changes to a file. Replaces `git checkout -- <file>`. |
| `git restore --staged <file>` | Unstage a file while keeping the changes in the working tree. |
| `git restore --source=<commit> <file>` | Restore a file to its state at a specific commit without switching branches. |
| `git stash`<br>`git stash pop` | Stash dirty working tree state so you can switch context, then restore it. |
| `git stash list` | Show all stashed states. Use `git stash apply stash@{n}` to apply a specific one. |
| `git log --oneline --graph --all --decorate` | Visual branch graph in the terminal. Useful for understanding diverged history. |
| `git blame <file>` | Annotate every line with the commit and author that last touched it. |
| `git cherry-pick <commit>` | Apply a single commit from another branch onto the current branch. |
| `git switch <branch>` | Switch branches — modern replacement for `git checkout <branch>`. |
| `git switch -c <new-branch>` | Create and switch to a new branch — modern replacement for `git checkout -b`. |

### github CLI

| Command | Description |
| :------ | :----------- |
| `gh repo create ___ --private` | Create new repo (private). |
| `gh repo clone ___` | Clone repo. |
| `gh repo view --web` | Open repo in browser. |
| `gh repo delete ___` | Delete repo. |
| `gh repo list` | List all repos. |
| `gh repo rename old-name new-name` | Rename repo. |
| `gh repo transfer ___ new-owner` | Transfer repo to new owner. |
| `gh repo fork ___` | Fork repo. |
| `gh repo fork --clone ___` | Fork repo and clone locally. |
| `gh repo fork --clone ___ --remote` | Fork repo and clone locally with remote origin. |
| `gh repo fork --clone ___ --remote --remote-name=upstream` | Fork repo and clone locally with remote origin and upstream. |

### less editor

| Shortcut | Action | Windows (WSL) |
| :------ | :----------- | :----------- |
| `Space`  or  `f` | Scroll forward one window (or screen) | |
| `b` | Scroll backward one window (or screen) | |
| `d` | Scroll forward half a window | |
| `u` | Scroll backward half a window | |
| `Enter`  or  `e` | Scroll forward one line | |
| `y`  or  `k` | Scroll backward one line | |
| `g` | Go to the start of the document | |
| `G` | Go to the end of the document | |
| `/` | Search forward for a pattern | |
| `?` | Search backward for a pattern | |
| `n` | Repeat the previous search (in the same direction) | |
| `N` | Repeat the previous search (in the opposite direction) | |
| `q` | Quit  less  and return to the command line | |

---

## SHELL

### Shortcuts (zsh)
| Key/Command | Description | Windows (WSL) |
| --- | --- | --- |
| `Ctrl + a` | Go to the beginning of the line you are currently typing on. | |
| `Ctrl + e` | Go to the end of the line you are currently typing on. | |
| `Ctrl + _` | Undo the last command. | |
| `Ctrl + l` | Clears the Screen | |
| `Cmd + K` | Clears the Screen (iTerm2 — clears scrollback buffer) | `Ctrl + L` (shell clear only; no scrollback-clear equivalent by default) |
| `Ctrl + U` | Cut everything backwards to beginning of line | |
| `Ctrl + K` | Cut everything forward to end of line | |
| `Ctrl + W` | Cut one word backwards using white space as delimiter | |
| `Ctrl + Y` | Paste whatever was cut by the last cut command | |
| `Ctrl + Z` | Puts whatever you are running into a suspended background process. fg restores it | |
| `Ctrl + H` | Same as backspace | |
| `Ctrl + C` | Kill whatever you are running. Also clears everything on current line | |
| `Ctrl + D` | Exit the current shell when no process is running, or send EOF to a the running process | |
| `Ctrl + T` | Swap the last two characters before the cursor | |
| `Ctrl + F` | Move cursor one character forward | |
| `Ctrl + B` | Move cursor one character backward | |
| `Option + →` | Move cursor one word forward | `Alt + →` |
| `Option + ←` | Move cursor one word backward | `Alt + ←` |
| `Esc + T` | Move cursor one word backward | |
| `Esc + Backspace` | Swap the last two words before the cursor | |
| `Tab` | Cut one word backwards using none alphabetic characters as delimiters | |

### Core Commands

| Command | Description |
| --- | --- |
| `cd /` | Root of drive |
| `cd -` | Previous directory |
| `ls -l` | Long listing |
| `ls -a` | Listing including hidden files |
| `ls -lh` | Long listing with human-readable file sizes |
| `ls -R` | Entire content of folder recursively |
| `find [folder] -name [search_pattern]` | Search for files/dirs, e.g., `find . -name "*.txt"` (searches recursively) |
| `find [folder] -name [search_pattern] -type d` | Search for directories only |
| `find [folder] -name [search_pattern] -type f` | Search for files only |
| `find . -maxdepth 1 -name [search_pattern]` | Search non-recursively |
| `grep [search_pattern] [dir]` | Search all files in the specified directory for all lines that contain the pattern |
| `grep [search_pattern] [file]` | Search file for all lines that contain the pattern, e.g., `grep "Tom" file.txt` |
| `grep -r [search_pattern] [dir]` | Recursively search in all files in the specified directory for all lines that contain the pattern |
| `sudo [command]` | Run command with the security privileges of the superuser (Super User DO) |
| `open [file]` | Opens a file (as if you double-clicked it) |
| `top` | Displays active processes. Press q to quit |
| `nano [file]` | Opens the file using the nano editor |
| `vim [file]` | Opens the file using the vim editor |
| `clear` | Clears the screen |
| `reset` | Resets the terminal display |
| `unzip path/to/your/file.zip` | General unzip |
| `unzip path/to/your/file.zip -d path/to/destination/folder` | Unzip to specific path |
| `zip -r compressed_filename.zip foldername` | General zip |
| `zip -r compressed_filename.zip foldername` | General zip |
| `lsof -i -P -n \| grep LISTEN` | Show all active ports being used by user processes | 
| `sudo lsof -i -P -n \| grep LISTEN` | Show all active ports, including system | 

### Chaining Commands
| Command | Description |
| --- | --- |
| [command-a]; [command-b] | Run command A and then B, regardless of the success of A |
| [command-a] && [command-b] | Run command B if A succeeded |
| [command-a] \|\| [command-b] | Run command B if A failed |
| [command-a] & | Run command A in the background |

### Explanation of `grep` 
* `grep` is a command-line utility for searching plain-text data sets for lines that match a regular expression.
* `grep` searches the named input FILEs (or standard input if no files are named, or the file name - is given) for lines containing a match to the given PATTERN.
* By default, `grep` prints the matching lines.
* `egrep` or `grep -E` is the same as `grep`, but uses extended regular expressions instead of basic regular expressions.
  * Example: `egrep 'foo|bar'` is the same as `grep -E 'foo|bar'`
* `fgrep` or `grep -F` is the same as `grep`, but interprets PATTERN as a list of fixed strings (instead of regular expressions), separated by newlines, any of which is to be matched.
  * This is different from normal `grep` which interprets PATTERN as a regular expression.
  * Example: `fgrep 'foo'` is the same as `grep -F 'foo'`
  * Example: `fgrep -f file1 file2` is the same as `grep -F -f file1 file2`
* To obtain the opposite effect of `grep`, use the `-v` or `--invert-match` option.
  * Example: `grep -v 'foo'` will match all lines that do not contain the string 'foo'
* Output grep results to a file using the `>` operator.
  * Example: `grep 'foo' file.txt > output.txt`

### Piping Commands
| Command | Description |
| --- | --- |
| find [dir] -name [search_pattern] | Search for files, e.g., `find /Users -name "file.txt"` (searches recursively) |
| grep [search_pattern] [file] | Search for all lines that contain the pattern, e.g., grep "Tom" file.txt |
| grep -r [search_pattern] [dir] | Recursively search in all files in the specified directory for all lines that contain the pattern |
| grep -v [search_pattern] [file] | Search for all lines that do NOT contain the pattern |
| grep -i [search_pattern] [file] | Search for all lines that contain the case-insensitive pattern |
| mdfind [search_pattern] | Spotlight search for files (names, content, other metadata), e.g., mdfind skateboard |
| mdfind -onlyin [dir] -name [pattern] | Spotlight search for files named like pattern in the given directory |

### Help
| Command | Description |
| --- | --- |
| [command] -h | Offers help |
| [command] -help | Offers help |
| info [command] | Offers help |
| man [command] | Show the help manual for [command] |
| whatis [command] | Gives a one-line description of [command] |
| apropos [search-pattern] | Searches for command with keywords in description |

---

## Docker

- Docker Image: a read-only template with instructions for creating a Docker container
- Docker Container: a runnable instance of a Docker image
- Dockerfile: a text file that contains all the commands a user could call on the command line to assemble an image.
  - `FROM`: the base image to build upon
  - `WORKDIR`: set the working directory
  - `RUN`: execute a command in the container
  - `COPY`: copy files from the host to the container
  - `ADD`: copy files from the host to the container (can also download files from the internet and copy them to the container)
  - `ARG`: set build-time variables
  - `ENV`: set environment variables
  - `EXPOSE`: expose a port
  - `CMD`: the command to run when the container starts
  - `ENTRYPOINT`: the command to run when the container starts (can be overridden by `CMD`)
  - `HEALTHCHECK`: check the health of the container
- Common Docker commands:
  - `docker build -t [image-name] .`: build the Docker image (`-t` is the tag name)
    - Use with `--file` to specify a Dockerfile other than the default `Dockerfile`
    - Use with `--build-arg [arg-name]=[arg-value]` to pass build-time variables
    - Use with `--platform` to specify the platform (e.g., `linux/amd64`, `linux/arm64`, `linux/arm/v7`)
  - `docker run -it [image-name]`: run the Docker container
  - `docker tag [image-name] [username]/[repo-name]:[tag]`: tag the Docker image
  - `docker push [username]/[repo-name]:[tag]`: push the Docker image to Docker Hub (or ECR, etc.)
  - `docker login --username [username] --password [password]`: log in to Docker Hub (or ECR, etc.)
- Docker Compose: a tool for defining and running multi-container Docker applications
  - `docker-compose up`: start the Docker containers
  - `docker-compose down`: stop the Docker containers
  - `docker-compose build`: build the Docker containers
  - `docker-compose push`: push the Docker containers to Docker Hub (or ECR, etc.)
  - `docker-compose pull`: pull the Docker containers from Docker Hub (or ECR, etc.)
  - `docker-compose config`: validate and view the Docker Compose file
  - `docker-compose logs`: view the logs of the Docker containers
  - `docker-compose ps`: view the status of the Docker containers
  - `docker-compose top`: view the processes running in the Docker containers
  - `docker-compose exec [service-name] [command]`: execute a command in a running container
  - `docker-compose run [service-name] [command]`: run a one-off command in a new container
  - `docker-compose restart [service-name]`: restart a container
  - `docker-compose stop [service-name]`: stop a container
  - `docker-compose rm [service-name]`: remove a container
  - `docker-compose kill [service-name]`: kill a container
  - `docker-compose down --rmi all`: remove all containers and images
  - `docker-compose down --volumes`: remove all volumes
  - `docker-compose down --remove-orphans`: remove all orphaned containers
- docker-compose.yaml: a YAML file that defines the Docker Compose configuration
  - `version`: the version of the Docker Compose file format
  - `services`: the services to run
  - `networks`: the networks to create
  - `volumes`: the volumes to create
  - `configs`: the configs to create
  - `secrets`: the secrets to create
  - `deploy`: the deployment configuration
  - `build`: the build configuration
  - `image`: the image configuration
  - `container_name`: the container name
  - `command`: the command to run
  - `entrypoint`: the entrypoint to run
  - `environment`: the environment variables to set
  - `env_file`: the environment variables to set from a file
  - `ports`: the ports to expose
  - `volumes`: the volumes to mount
  - `depends_on`: the services to depend on
  - `networks`: the networks to connect to
  - `network_mode`: the network mode to use
  - `restart`: the restart policy
  - `logging`: the logging configuration
  - `labels`: the labels to set
  - `configs`: the configs to mount
  - `secrets`: the secrets to mount
  - `deploy`: the deployment configuration
  - `build`: the build configuration
  - `image`: the image configuration
  - `container_name`: the container name
  - `command`: the command to run
  - `entrypoint`: the entrypoint to run
  - `environment`: the environment variables to set
  - `env_file`: the environment variables to set from a file
  - `ports`: the ports to expose
  - `volumes`: the volumes to mount
  - `depends_on`: the services to depend on
  - `networks`: the networks to connect to
  - `network_mode`: the network mode to use
  - `restart`: the restart policy
  - `logging`: the logging configuration
  - `labels`: the labels to set
  - `configs`: the configs to mount
  - `secrets`: the secrets to mount
  - `deploy`: the deployment configuration
  - `build`: the build configuration
  - `image`: the image configuration
  - `container_name`: the container name
- Makefile: a text file that contains a set of tasks to be executed by the `make` command
  - Used to automate the build process
  - Used in conjunction with Docker Compose to automate the deployment process
  - `deploy`: deploy the Docker containers using the following commands...
- End-to-End workflow using Dockerfile, docker-compose.yaml, and Makefile:
  1) In Dockerfile, specify the base image to build upon, the working directory, and the commands to run in order to build the image in the container
  2) In docker-compose.yaml, specify version, services (and their configs/ports/etc.)
  3) In Makefile, specify the commands to run to build and deploy the Docker containers
  4) Run `make deploy` to build and deploy the Docker containers
- Dockerfile example:
  ```dockerfile
  FROM python:3.8.5-slim-buster

  WORKDIR /app

  RUN apt-get update && apt-get install -y \
      build-essential \
      libpq-dev \
      libssl-dev \
      libffi-dev \
      python3-dev \
      python3-pip \
      python3-setuptools \
      python3-wheel \
      && rm -rf /var/lib/apt/lists/*

  COPY requirements.txt requirements.txt
  RUN pip3 install -r requirements.txt

  COPY . .

  CMD ["python3", "app.py"]
  ```

- Simple docker-compose.yaml example:
  ```yaml
  version: "3.8"

  services:
    app:
      build: .
      ports:

        - "5000:5000"
    db:
      image: postgres:13.3
      environment:
        POSTGRES_USER: postgres
        POSTGRES_PASSWORD: postgres
        POSTGRES_DB: postgres
      ports:

        - "5432:5432"
  ```

- Makefile example:
  ```makefile
  .PHONY: deploy
  deploy:
      docker-compose build
      docker-compose push
      docker-compose pull
      docker-compose up -d
  ```

---

## postgres psql (Mac)

| Action | Command |
| --- | --- |
| Start postgres and log into main local database | `psql -U [username] -d [database]` |
| List all tables in this db | `\dt` |
| List all tables in all dbs | `\dt *.*` |
| List all databases | `\l` |
| Navigate to a different database | `\c [database]` |
| List all schemas in this db | `\dn` |
| Create a new database | `CREATE DATABASE [database];` |
| Create a new schema | `CREATE SCHEMA [schema];` |
| Create a new table | `CREATE TABLE [table] ( [column] [datatype] [constraints] );` |
| Delete a database | `DROP DATABASE [database];` |
| Export a database | `pg_dump -U [username] [database] > [filename].sql` |
| Import a database | `psql -U [username] -d [database] -f [filename].sql` |
| Exit psql | `\q` |

---

## numpy

### Reshaping

* The reshape() function takes a single tuple argument that specifies the new shape of the array
  * Used frequently to _add_ a dimension of when for libs like sklearn and keras (to the END of the shape tuple -- i.e. **right-padding with 1s**)
* In the case of reshaping 1-D `(m,)` --> 2-D `(m,1)`:
  * Tuple would be the shape of the array as the first dimension (data.shape[0]) and 1 for the second dimension:
    * `data.shape == (m_old, )` (e.g. `(1000,)`)
    * `data = data.reshape( (m_old, n_new)  )`
      * `data.shape == (m_old, n_new)` (e.g. `(1000, 1)`)

### Broadcasting

In formal LinAlg, arithmetic can only be performed when:  

* the shape of each dimension in the arrays are equal (even for dotproduct - though not matmul)
  
However, in ML, we often want to add **A** `(m,n)` to **v** `(,n)`.  
NumPy enables this by _broadcasting_ the vector to the shape of the matrix.  
Specifically np (**which considers vectors as (n,) since it is row-oriented**) effectively:

1. **Left-pads with 1s** the dimensions of the smaller array
2. **Right-to-left compares** the dimensions of the two arrays and ensures either
  a. The dimensions are equal **OR**
  b. At least one of the dimensions is 1

3. If all dimensions pass, np **replicates** (_broadcast_) the smaller array along the dim(s) where it is 1 to match the shape of the larger array.

**NOTE**: Broadcasting is not a copy operation. It is a view of the original array with the same data. This means that if you modify a broadcasted array, it modifies the original array.  

So for example:  

* 1-D vs. 2-D
  * LOOKS like comparing:  
    * A.shape -- (2,3)  
    * b.shape -- (3,)  
  * ACTUALLY np is comparing:  
    * A.shape -- (2,3)  
    * b.shape -- (1,3)  
* 2-D vs. scalar  
  * LOOKS like comparing:  
    * A.shape -- (2,3)  
    * b.shape -- (1,)  
  * ACTUALLY np is comparing:  
    * A.shape -- (2,3)  
    * b.shape -- (1,1)

---

## iTerm2 (this section copied from some dude on the internet)

### Tabs and Windows


**Function** | **Shortcut**
-------- | --------
New Tab | `⌘` + `T`
Close Tab or Window | `⌘` + `W`  (same as many mac apps)
Go to Tab | `⌘` + `Number Key`  (ie: `⌘2` is 2nd tab)
Go to Split Pane by Direction | `⌘` + `Option` + `Arrow Key`
Cycle iTerm Windows | `⌘` + `backtick`  (true of all mac apps and works with desktops/mission control)
**Splitting** | 
Split Window Vertically (same profile) | `⌘` + `D`
Split Window Horizontally (same profile) | `⌘` + `Shift` + `D`  (mnemonic: shift is a wide horizontal key)
**Moving** |
Move a pane with the mouse | `⌘` + `Alt` + `Shift` and then drag the pane from anywhere
**Fullscreen** |
Fullscreen | `⌘`+ `Enter`
Maximize a pane | `⌘` + `Shift` + `Enter`  (use with fullscreen to temp fullscreen a pane!)
Resize Pane | `Ctrl` + `⌘` + `Arrow` (given you haven't mapped this to something else)
**Less Often Used By Me** |
Go to Split Pane by Order of Use | `⌘` + `]` , `⌘` + `[`
Split Window Horizontally (new profile) | `Option` + `⌘` + `H`
Split Window Vertically (new profile) | `Option` + `⌘` + `V`
Previous Tab | `⌘`+ `Left Arrow`  (I usually move by tab number like `⌘+1`)
Next Tab | `⌘`+ `Right Arrow`
Go to Window | `⌘` + `Option` + `Number`


### My Favorite Shell Key Combos

These might be helpful to getting you faster with the shell.
These are just common shell shortcuts unrelated to iTerm itelf.
These will usually work in Bash/Zsh/Fish on Mac and on Linux.
There are many shortcuts out there but I use these quite a bit.
There is also more than one way to do a thing so adopt what you like best.

Hopefully some of these improve your work life.  :)

**Function** | **Key Combination** | **Use**
-------- | -------- | --------
Delete to start of line | `Ctrl` + `U` | Use this to start over typing without hitting Ctrl-C
Delete to end of line | `Ctrl` + `K` | Use this with command history to repeat commands and changing one thing at the end!
Repeat last command | `Up Arrow` | Cycle and browse your history with up and down.  `Ctrl-R` is faster if you know the string you are looking for.
Move back and forth on a line | `Arrow Keys` | This takes you off the home row but it's easy to remember
Move back and forth on a line by words | `⌥` + `Arrow Keys` | Fast way to jump by words to correct a typo or "run again" with minor changes to last command.  Ctrl as modifier might also work on mac and non-mac keyboards/shells/apps.
Delete previous word (in shell) | `Ctrl` + `W` | It's faster to delete by words.  Especially when your last command was wrong by a single typo or something.
Clear screen | `Ctrl` + `L` | This is telling the shell to do it instead of an explicit command like `clear` or `cls` in DOS.  If you use `⌘` + `K`, this is telling iTerm to clear the screen which might have the same result or do something terrible (like when using a TUI like `top` or `htop`.  In general, use this instead of typing `clear` over and over.
Exit Shell | `Ctrl` + `D` | Instead of typing exit, just get this in muscle memory.  It works in many contexts.


### Moving Faster

A lot of shell shortcuts work in iterm and it's good to learn these because arrow keys, home/end
keys and Mac equivalents don't always work.  For example `⌘` + `Left Arrow` is usually the same as `Home`
(go to beginning of current line) but that doesn't work in the shell.  Home works in many apps but it
takes you away from the home row.

**Function** | **Shortcut**
-------- | --------
Move to the start of line | `Ctrl` + `A` or `Home` (Home is fn+Left arrow)
Move to the end of line | `Ctrl` + `E` or `End` (End is fn+Right arrow)
Moving by word on a line (this is a shell thing but passes through fine)| `Ctrl` + `Left/Right Arrow`
Cursor Jump with Mouse (shell and vim - might depend on config) | `Option` + `Left Click`

### About keyboard shortcuts
> So, some keyboard shortcuts are Mac's.  For example fn+Left Arrow is the Home key.  On a fullsize Mac keyboard, there is a Home key.  Home will usually pass through to iTerm and the shell.  By shell, I mean zsh, bash or fish.  The shell is the program running inside of iTerm when you open iTerm.  If you launch `vim` or something, zsh/bash/fish is "gone" because vim is running.  So, it's complicated to explain when keys work and when they don't.
>
> For example, Home will work in zsh.  It will take you to the beginning of the line.  If your cursor is at the end of "three" in this below example
> ```
> one two three|
> ```
> When you press Home (fn+Left Arrow) your cursor will be on one: `|one`
> So, in this way, Home works the same in "the shell" as it does in TextEdit.app or any basic text box on Mac.
> This is not the case if you start up `vim` or `emacs`.  This is not iTerm's fault.  This is just how Mac/Linux works.  Just a head's up on that little detail.

### Copy and Paste with iTerm without using the mouse

I don't use this feature too much.  I instead just mouse select (which copies to the clipboard) and paste.  There's no need to Copy to the clipboard if you have `General > Selection > Copy to pasteboard on selection` enabled.

**Function** | **Shortcut**
-------- | --------
Enter Copy Mode | `Shift` + `⌘` + `C`
Enter Character Selection Mode in Copy Mode | `Ctrl` + `V`
Move cursor in Copy Mode | `HJKL` vim motions or arrow keys
Copy text in Copy Mode | `Ctrl` + `K`

Copy actions goes into the normal system clipboard which you can paste like normal.


### Search the Command History

Some of these are not directly related to iTerm and are just "shell features".  Like, if you open Terminal.app on Mac some of these still work because it's the shell and not iTerm.  I'm including them anyway.

**Function** | **Shortcut**
-------- | --------
Search as you type | `Ctrl` + `R` and type the search term; Repeat `Ctrl` + `R` to loop through result
Search the last remembered search term | `Ctrl` + `R` twice
End the search at current history entry  | `Ctrl` + `Y`
Cancel the search and restore original line | `Ctrl` + `G`

### Misc

**Function** | **Shortcut**
-------- | --------
Clear the screen/pane (when `Ctrl + L` won't work) | `⌘` + `K`  (I use this all the time)
Broadcast command to all panes in window (nice when needed!) | `⌘` + `Alt` +  `I` (again to toggle)
Find Cursor | `⌘` + `/`  _or use a theme or cursor shape that is easy to see_

---

## vim

Vim operates in **modes**. The key mental shift: Normal mode is *home* — where you spend most of your time moving around and operating on text. You drop into Insert mode to type, then immediately `Esc` back out. Visual mode is for selecting. Command mode (`:`) is for file and editor operations.

The deeper insight is that vim has a **grammar**: `[count] operator motion`. For example, `3dw` deletes 3 words, `ci"` changes everything inside quotes, `d$` deletes to end of line. Once the grammar clicks, you stop memorizing individual shortcuts and start composing them. The `.` key (repeat last change) becomes your best friend.

| Action | macOS | Windows (WSL) |
| :------ | :----------- | :----------- |
| **Modes** | | |
| Enter Insert mode (before cursor) | `i` | |
| Enter Insert mode (after cursor) | `a` | |
| Insert at start of line | `I` | |
| Append at end of line | `A` | |
| Open new line below, enter Insert | `o` | |
| Open new line above, enter Insert | `O` | |
| Return to Normal mode | `Esc` or `Ctrl + [` | |
| Enter Visual mode (char) | `v` | |
| Enter Visual mode (line) | `V` | |
| Enter Visual block mode | `Ctrl + v` | |
| Enter Command mode | `:` | |
| **File operations** | | |
| Save | `:w` | |
| Quit | `:q` | |
| Save and quit | `:wq` or `ZZ` | |
| Quit without saving | `:q!` | |
| **Navigation** | | |
| Left / Down / Up / Right | `h` / `j` / `k` / `l` | |
| Next word (start) / prev word | `w` / `b` | |
| Next word (end) | `e` | |
| Start of line / end of line | `0` / `$` | |
| First non-blank char of line | `^` | |
| Top of file / bottom of file | `gg` / `G` | |
| Jump to line n | `:{n}` or `{n}G` | |
| Page down / page up | `Ctrl + f` / `Ctrl + b` | |
| Half-page down / up | `Ctrl + d` / `Ctrl + u` | |
| Jump to matching bracket | `%` | |
| **Search** | | |
| Search forward | `/{pattern}` | |
| Search backward | `?{pattern}` | |
| Next / previous result | `n` / `N` | |
| Search word under cursor | `*` (forward) / `#` (backward) | |
| Clear search highlight | `:noh` | |
| **Editing** | | |
| Undo / redo | `u` / `Ctrl + r` | |
| Repeat last change | `.` | |
| Delete char under cursor | `x` | |
| Delete line | `dd` | |
| Delete to end of line | `D` or `d$` | |
| Delete word | `dw` | |
| Change word (delete + Insert) | `cw` | |
| Change to end of line | `C` or `c$` | |
| Replace single char | `r{char}` | |
| Yank (copy) line | `yy` | |
| Paste after cursor / before cursor | `p` / `P` | |
| Indent / dedent line | `>>` / `<<` | |
| **Operators + motions (composable)** | | |
| Delete {motion} | `d{motion}` — e.g. `d3w`, `dG` | |
| Yank {motion} | `y{motion}` — e.g. `y$`, `ygg` | |
| Change {motion} | `c{motion}` — e.g. `ciw`, `ci"` | |
| `i` vs `a` text objects | `i` = inside, `a` = around — e.g. `ci(`, `da[` | |
| **Useful extras** | | |
| Show line numbers | `:set number` | |
| Find and replace (whole file) | `:%s/old/new/g` | |
| Find and replace (with confirm) | `:%s/old/new/gc` | |
| Yank to system clipboard | `"+y` | `"+y` (requires xclip/xsel in WSL) |
| Paste from system clipboard | `"+p` | `"+p` |

## tmux

### Pane Management

* Split Pane Horizontally: `Ctrl + b, then "`
* Split Pane Vertically: `Ctrl + b, then %`
* Switch to x Pane: `Ctrl + b, then x-arrow`
* Close Current Pane: `Ctrl + b, then x (then press y to confirm)`
* (Switch to Next Pane: `Ctrl + b, then o)`

### Window Management

* Create New Window: `Ctrl + b, then c`
* Switch to Next Window: `Ctrl + b, then n`
* Switch to Previous Window: `Ctrl + b, then p`
* List Windows: `Ctrl + b, then w`
* Rename Current Window: `Ctrl + b, then ,`

### Session Management

* Detach from Session: `Ctrl + b, then d`
* List Sessions: `tmux ls (outside of tmux)`
* Attach to a Session: `tmux attach-session -t [session-name]`

### Resizing Panes

* Resize Pane Up: `Ctrl + b:resize-pane -U 10`
* Resize Pane Down: `Ctrl + b:resize-pane -D 10`
* Resize Pane Left: `Ctrl + b:resize-pane -L 10`
* Resize Pane Right: `Ctrl + b:resize-pane -R 10`

### Miscellaneous

* Scroll Mode: `Ctrl + b, then [ (use arrow keys to scroll, q to exit scroll mode)`
* Copy Mode: `Ctrl + b, then [ (enter copy mode for text selection)`
* Paste from Buffer: `Ctrl + b, then ]`

---
