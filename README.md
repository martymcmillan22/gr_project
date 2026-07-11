# Intro to Django

![CPINDCNO Constitutional Guardrail](https://img.shields.io/badge/CPINDCNO-Constitutional_Guardrail_PASS-2ea44f?style=for-the-badge)

This is the code for the *O'Reilly Video* - **Intro to Django** presented by Arianne Dee.

You can download a PDF of the slides [here](https://drive.google.com/file/d/1F-FDjBJnjrhnB7ulM3DJuro_T-5M07r-/view?usp=sharing).

## AI Workflow Directive

This repository uses a deterministic AI workflow for UI and semantic work.

See [GRASSROOTS_AI_WORKFLOW.md](GRASSROOTS_AI_WORKFLOW.md) for the Penpot to MDX to React to MLAS BTIF directive that all AI assistants should follow.

## Workflow Platform (Canonical)

The canonical workflow command center is under [workflow](workflow).

Core categories:
1. [workflow/database_design/mermaid_erds](workflow/database_design/mermaid_erds)
2. [workflow/logic_design/mermaid_sequences](workflow/logic_design/mermaid_sequences)
3. [workflow/ui_templates/penpot_templates](workflow/ui_templates/penpot_templates)
4. [workflow/ui_components/penpot_components](workflow/ui_components/penpot_components)

Workflow engine entrypoint:
- [workflow/cli.py](workflow/cli.py)

Workflow docs:
- [workflow/README.md](workflow/README.md)
- [workflow/ARCHITECTURE_OVERVIEW.md](workflow/ARCHITECTURE_OVERVIEW.md)
- [workflow/SEMANTIC_OVERVIEW.md](workflow/SEMANTIC_OVERVIEW.md)
- [workflow/SEMANTIC_DRIFT_OVERVIEW.md](workflow/SEMANTIC_DRIFT_OVERVIEW.md)
- [workflow/SEMANTIC_INFERENCE_OVERVIEW.md](workflow/SEMANTIC_INFERENCE_OVERVIEW.md)
- [workflow/ai_hints.json](workflow/ai_hints.json)
- [workflow/ai_navigation.json](workflow/ai_navigation.json)
- [workflow/semantic_context.json](workflow/semantic_context.json)
- [workflow/RELEASE_OVERVIEW.md](workflow/RELEASE_OVERVIEW.md)
- [workflow/VERSIONING_GUIDE.md](workflow/VERSIONING_GUIDE.md)
- [workflow/version.json](workflow/version.json)
- [workflow/governance_policy.json](workflow/governance_policy.json)

Common commands:
- python3 workflow/cli.py new-feature --name "Feature Name" --mlas-tier "Tier" --btif-classification "Class" --semantic-intent "Intent" --semantic-tags tag1 tag2
- python3 workflow/cli.py validate-suite
- python3 workflow/cli.py classify
- python3 workflow/cli.py semantic-check
- python3 workflow/cli.py sync --feature <slug>
- python3 workflow/cli.py sync-all
- python3 workflow/cli.py semantic-drift
- python3 workflow/cli.py semantic-infer
- python3 workflow/cli.py semantic-resolve
- python3 workflow/cli.py ai-context
- python3 workflow/cli.py ai-export
- python3 workflow/cli.py ai-new-feature --name "Feature Name"
- python3 workflow/cli.py version
- python3 workflow/cli.py bump-version --part patch
- python3 workflow/cli.py release --bump patch [--approve-semantic-changes]
- python3 workflow/cli.py release-notes

## AWS Deployment Docs

AWS planning and execution docs are organized under [docs/operations/aws](docs/operations/aws).

Primary entry point:
- [docs/operations/aws/README.md](docs/operations/aws/README.md)

Suggested reading order:
1. [AWS Deployment Recommendation](docs/operations/aws/aws_deployment_recommendation.md)
2. [AWS Implementation Plan](docs/operations/aws/aws_implementation_plan.md)
3. [AWS Staging Resource Checklist](docs/operations/aws/aws_staging_resource_checklist.md)
4. [AWS Staging Deployment Checklist](docs/operations/aws/aws_staging_deployment_checklist.md)

## Diagram Library

All Grassroots architecture and workflow diagrams are stored in [grassroots_diagrams](grassroots_diagrams).

These Mermaid files define the Penpot to MDX to React to MLAS BTIF pipeline and are used for onboarding, semantic reference, and VS Code AI tasks.

## Course setup

1. [Install Python 3.11](#1-install-python-311)
1. [Check that Python was installed properly](#2-make-sure-that-python-is-properly-installed)
1. [Choose an IDE](#3-choose-an-ide)
1. [Download the code](#4-download-the-course-files)
1. [Create a virtual environment](#5-create-a-virtual-environment)
1. [Install Django](#6-install-django)

## Set up instructions
Feel free to email me at
[arianne.dee.studios@gmail.com](mailto:arianne.dee.studios@gmail.com)
if you are having any problems getting set up for the course.

### 1. Install Python 3.11

This course uses Python 3.11, but Python 3.8 and higher should work.

The course uses Django 4.2,
so check which Python versions are compatible with 
Django 4.2 [here](https://docs.djangoproject.com/en/4.2/faq/install/#faq-python-version-support).

#### To install the latest version of Python:
1. Go to https://www.python.org/downloads/
1. Click the yellow button at the top to download the latest version of Python.

#### On Mac or Linux
Follow the prompts and install using the default settings.

#### On Windows
The default settings don't add Python to your PATH
so your computer doesn't know where to look for it when Python runs
(for some inexplicable reason).

##### If you're just installing Python now
Follow the instructions here: [Windows Python installer instructions](docs/install/WININSTALL.md)

##### If you've already installed Python with the default settings
Follow the instructions here: [Add Python to PATH variable in Windows](docs/install/WINSETPATH.md)

### 2. Make sure that Python is properly installed
1. Open the *PowerShell* application in Windows
   or *Terminal* on Mac or Linux

1. Type `python --version` and press enter
2. Type `python3 --version` and press enter
3. Type `py --version` and press enter

At least one of those commands should print
a Python version of 3.8 or higher
(whichever version you just installed).
If it doesn't, you have to follow instructions to
[add Python to your PATH variable](docs/install/WINSETPATH.md).

### 3. Choose an IDE
**PyCharm** or **VS Code** are recommended.

For Django development, I recommend using **PyCharm Professional Edition** (paid).
There is a 30-day free trial if you would like to try it out.

In the video I use the free **PyCharm Community Edition**, which is sufficient.

Download either version here: https://www.jetbrains.com/pycharm/download/

Install, open, and use the default settings.

### 4. Download the course files

#### If you know git:
Clone the repository.

#### If you don't know git:
1. Click the green "Code" button at the top-right of the page
2. Click "Download ZIP"
3. Unzip it and move the **intro-to-django-main** folder to a convenient location

### 5. Create a virtual environment
1. In your console, navigate to the project folder (if you open the project in PyCharm or VSCode, the Terminal pane should already be located there)
2. Using the python command from step 2, create a virtual environment
`python -m venv django_venv` or `python3 -m venv django_venv`
3. Activate your virtual environment
   - **Mac/Linux**: `source django_venv/bin/activate`
   - **PowerShell**: `django_venv\Scripts\Activate.ps1`

If you are new to virtual environments, please watch this 
[video lesson](https://learning.oreilly.com/videos/next-level-python/9780136904083/9780136904083-NLP1_01_03_03/)

### 6. Install Django
Once your virtual environment has been activated, install Django 3 using pip:
- `pip install django` to install the latest version of Django
  
**OR**
- `pip install "django>=4.2,<5"` to install the latest Django 4.2 version (once version 5+ is released)

## FAQs
### Can I use Python 2?

No. Django 3+, does not support Python 2 or Python < 3.6.

### PyCharm can't find Python 3

On a Mac:
- Go to **PyCharm** > **Preferences**

On a PC:
- Go to **File** > **Settings**

Once in Settings:
1. Go to **Project: intro-to-django** > **Project Interpreter**
1. Look for your Python version in the Project Interpreter dropdown
1. If it's not there, click **gear icon** > **Add...**
1. In the new window, select **System Interpreter** on the left, and then look for the Python version in the dropdown
1. If it's not there, click the **...** button and navigate to your Python location
    - To find where Python is located, [look in these directories](docs/install/PATH_LOCATIONS.md)
    - You may have to search the internet for where Python gets installed by default on your operating system

### How do I set up my IDE to use Django?
Here are some links to configure your Django project in the following IDEs
- [PyCharm Professional](docs/config/PyCharm_Pro.md)
  - My IDE of choice for working in Django
- [PyCharm Community](docs/config/PyCharm_Com.md)

- [VS Code](docs/config/VSCode.md)

---

## Django Trivia example project

### Local setup instructions

1. Navigate into the `trivia_site` folder
1. Create a virtual environment with Python 3.8+
1. Activate your virtual environment
1. `$ pip install --upgrade pip` to upgrade pip
1. `$ pip install -r requirements/local.txt` to install local requirements
1. `$ python manage.py migrate` to migrate your database
1. `$ python manage.py createsuperuser` and follow instructions
1. `$ python manage.py loaddata questions` to add seed data
1. `$ python manage.py runserver` to run the development server

### Production setup instructions

Live website at https://trivia-ariannedee.pythonanywhere.com/.

Hosted on Python Anywhere using Python 3.10 and MySQL 5.7.

To get a copy in production on your own server:

1. Set up a server environment with Python 3.8 or higher and a database (Postgres or MySQL preferred)
2. Fork this project or create a copy of the `trivia_site` folder in your own repository and clone into your sever
**Note**: The next few steps may differ depending on what kind of server/service you are using. Follow a Django setup tutorial if you can find one.
3. Create and activate a virtual environment if desired
4. Set the `DJANGO_SETTINGS_MODULE` environment variable to `trivia_project.settings.production`
   - `$ export DJANGO_SETTINGS_MODULE=trivia_project.settings.local` on Linux
   - On PythonAnywhere, edit the WSGI configuration file with `os.environ['DJANGO_SETTINGS_MODULE'] = 'trivia_project.settings.production'`
   - This makes sure running `manage.py` uses the right settings file
5. Configure the server to use WSGI (instead of `python manage.py runserver`)
   - Point to `trivia_project.wsgi.application` or configure a `wsgi.py` file on the server (follow tutorial instructions)
6. Set up your secrets in a `.env` file
   - Duplicate `.env.example` and save it as `.env`
   - Fill in the `DJANGO_SECRET_KEY` field with a random string of 50+ characters
   - Fill in the `DB_PASSWORD` field
   - Email fields are only used for the forgot password feature. If you want to get it working, the easiest is to create a new Gmail address and create an app password for it and use that for `EMAIL_PASSWORD`
7. Edit `trivia_site/trivia_project/settings/production.py`
   - Update `ALLOWED_HOSTS` to use your server address(es)
   - Edit your database settings (except password)
8. Edit `trivia_site/requirements/production.txt` to use the correct package for your database
   - Use a different `mysqlclient` if necessary, or `psycopg` or `psycopg2` if using Postgres (or other package if using a different DB)
   - This might be trial and error. You can pip install it, try to get it working, then update the requirements file with the pinned version
9. Install the requirements `$ pip install -r requirements/production.txt`
10. Run/reload the server and see if it works, troubleshoot if necessary
   - You may need to do more configuration to properly serve your static and media files. Look for a tutorial for your cloud provider or server type.
   - If you cannot serve media files from the same server, use Amazon S3
11. Migrate the database by running `python manage.py migrate`
12. If that works, commit any code changes you made.
13. `$ python manage.py createsuperuser` and follow instructions
14. `$ python manage.py loaddata questions` to add seed data
15. `$ python manage.py collectstatic` to collect the static files into `staticfiles/` (run this every time your static files change)

Please let me know if you have any suggestions/updates/questions about these instructions.

---

## Questions or comments?

Email me at  
[**arianne.dee.studios@gmail.com**](mailto:arianne.dee.studios@gmail.com) 
or submit an issue or pull request to this repository.

---

## BaseTrue Monthly Newsletter

The project now includes a monthly newsletter app at `/base-true-news/` with:

- Masthead (nameplate), headline, and byline layout.
- Two feature categories:
   - Perpetual Infrastructure Program (PIP)
   - Base True Information Format
- Story staging with `draft`, `scheduled`, and `published` statuses.
- Public email signup form for subscribers.
- One-click unsubscribe links in newsletter emails.

### Email setup (SMTP)

1. Copy `.env.example` values into your shell environment.
2. Set real SMTP credentials.
3. Restart your server process.

Example:

```bash
export EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_HOST_USER="your-email@example.com"
export EMAIL_HOST_PASSWORD="your-app-password"
export EMAIL_USE_TLS=True
export DEFAULT_FROM_EMAIL="BaseTrue Monthly <your-email@example.com>"
```

### Monthly send workflow

1. In Django admin, create an `Issue` for the target month/year.
2. Add `Story` entries to that issue and set `status=published` and `publish_at`.
3. Select the issue in admin and run action: `Email selected issues to active subscribers`.# gr_project
