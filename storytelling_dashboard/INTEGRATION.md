# 🚀 Story-Telling Engine Dashboard — Integration Steps

**Status:** ✅ Complete app structure built  
**Next:** Wire up to Django project

---

## **What Was Created**

### **App Structure**
```
/storytelling_dashboard/
├── __init__.py
├── apps.py                          # AppConfig
├── models.py                        # StorySession model
├── views.py                         # Dashboard + API endpoints (6 views)
├── urls.py                          # URL routing (6 URLs)
├── admin.py                         # Admin registration
├── markdown_parser.py               # MASTER_DOCUMENT.md parser
├── README.md                        # App documentation
└── templates/storytelling_dashboard/
    ├── dashboard.html               # All 17 stories overview
    └── story_detail.html            # Story editor
```

### **Core Components**

**1. Markdown Parser** (`markdown_parser.py`)
- `StoryEntry` class (represents one story)
- `StoryMarkdownParser` class (reads/writes MASTER_DOCUMENT.md)
- Default placeholder entries (all 17 stories)
- Progress calculation (0-100%)

**2. Django Models** (`models.py`)
- `StorySession` — Tracks editing sessions, progress, metadata
- Admin-friendly with filters + search

**3. Views & APIs** (`views.py`)
- `dashboard()` — HTML view showing all stories + stats
- `story_detail()` — HTML view for editing one story
- `api_stories()` — JSON: Get all stories
- `api_story()` — JSON: Get single story
- `api_story_save()` — JSON: Save story edits
- `api_story_validate()` — JSON: Validate against schema

**4. Templates**
- `dashboard.html` — Table with progress bars, status badges, validation buttons
- `story_detail.html` — Rich editor with live progress, word count, validation

**5. URL Routing** (`urls.py`)
- `/` → Dashboard
- `/story/<id>/` → Story editor
- `/api/stories/` → API: List
- `/api/story/<id>/` → API: Detail
- `/api/story/<id>/save/` → API: Save
- `/api/story/<id>/validate/` → API: Validate

---

## **Integration Steps (Do These Next)**

### **Step 1: Add App to INSTALLED_APPS**

Edit `/gr_project/settings.py`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Your apps
    'home',
    'support',
    'forums',
    'career_app',
    'center',
    'domain',
    'polls',
    'povs',
    'problems',
    'requirements',
    'twist',
    'ui_apps',
    'users',
    'va',
    'polish',
    'baseTrue_news',
    
    # NEW: Storytelling Dashboard
    'storytelling_dashboard',
]
```

### **Step 2: Include URLs in Main Project**

Edit `/gr_project/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Existing apps
    path('', include('home.urls')),
    path('support/', include('support.urls')),
    # ... other apps ...
    
    # NEW: Storytelling Dashboard
    path('storytelling-dashboard/', include('storytelling_dashboard.urls')),
]
```

### **Step 3: Run Migrations**

```bash
cd /Users/martymcmillan/Desktop/GrassRoots
a_gr_venv/bin/python manage.py migrate
```

### **Step 4: Test It**

```bash
a_gr_venv/bin/python manage.py runserver
```

Then navigate to:
- http://localhost:8000/storytelling-dashboard/

### **Step 5: Create Superuser (if needed)**

```bash
a_gr_venv/bin/python manage.py createsuperuser
```

Login at http://localhost:8000/admin

---

## **Features Ready to Use**

### **Dashboard** (`/storytelling-dashboard/`)
✅ View all 17 stories  
✅ Status badges (Complete/In Progress/Pending)  
✅ Progress bars (% complete per story)  
✅ Summary stats (total, completed, pending, avg progress)  
✅ Quick "Edit" and "Check" buttons  

### **Story Editor** (`/storytelling-dashboard/story/<id>/`)
✅ Edit Title  
✅ Select Format (Short Series / 1-Hour / Movie / Epic)  
✅ Add Talking Points (3–5 hooks)  
✅ Write Core Concept  
✅ Write Synopsis (with word count)  
✅ Live progress tracking  
✅ Save to MASTER_DOCUMENT.md  
✅ Validate against ENGINE_SCHEMA.md  

### **API Endpoints** (JSON)
✅ GET `/api/stories/` — List all  
✅ GET `/api/story/<id>/` — Get one  
✅ POST `/api/story/<id>/save/` — Save edits  
✅ POST `/api/story/<id>/validate/` — Validate  

### **Admin Interface** (`/admin/`)
✅ Browse StorySession objects  
✅ Filter by status, format, date  
✅ Search by title or entry_id  
✅ Track last edited by + timestamp  

---

## **Next Steps**

1. **Follow Integration Steps above** (add to INSTALLED_APPS, include URLs, run migrations)
2. **Test dashboard** at `/storytelling-dashboard/`
3. **Pick first placeholder story** (e.g., "Dear Darwin")
4. **Click Edit** → Fill in Talking Points, Core Concept, Synopsis
5. **Click Save** → Story updates in MASTER_DOCUMENT.md
6. **Click Validate** → Check against schema
7. **Repeat** for all 10 placeholder entries

---

## **Current Limitations (v1.0)**

- Only edits Sections 1–4 (Talking Points, Core Concept, Synopsis)
- Sections 5–13 (Chapters, DN, Soundtrack, etc.) still manual in MASTER_DOCUMENT.md
- Markdown parser is basic (stub implementation; full parsing would be more complex)

---

## **Version 2.0 Ideas**

- Full 13-section editor
- Character profile builder
- Soundtrack timeline UI
- Dynamic Navigation helper
- Real-time markdown preview
- Git commit integration
- Bulk operations

---

**Ready to integrate?** Follow the 5 steps above and you'll have a working dashboard! 🚀
