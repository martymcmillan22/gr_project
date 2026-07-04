# Storytelling Dashboard — Story Management Interface

A Django web application for managing the Story-Telling Engine's 17 story entries directly from `MASTER_DOCUMENT.md`.

## Features

- **📊 Dashboard Overview** — View all 17 stories with status, format, and progress
- **✏️ Story Editor** — Edit individual entries with real-time validation
- **💾 Auto-Save** — Changes sync back to MASTER_DOCUMENT.md
- **✓ Schema Validation** — Check stories against ENGINE_SCHEMA.md rules (all 6 PARTS)
- **📈 Progress Tracking** — Visual progress bars for each story (0-100%)
- **🎯 Format Selection** — Choose from 4 format levels (Short Series, 1-Hour, Movie, Epic)

## Installation

1. **Add app to Django `INSTALLED_APPS`:**
   ```python
   # gr_project/settings.py
   INSTALLED_APPS = [
       ...
       'storytelling_dashboard',
       ...
   ]
   ```

2. **Include URLs in main project:**
   ```python
   # gr_project/urls.py
   urlpatterns = [
       ...
       path('storytelling-dashboard/', include('storytelling_dashboard.urls')),
       ...
   ]
   ```

3. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Access dashboard:**
   - URL: `/storytelling-dashboard/`
   - Auth: Login required (uses Django auth)

## File Structure

```
storytelling_dashboard/
├── __init__.py
├── apps.py                          # App config
├── models.py                        # StorySession model (for tracking)
├── views.py                         # Dashboard + API views
├── urls.py                          # URL routing
├── admin.py                         # Admin interface
├── markdown_parser.py               # MASTER_DOCUMENT.md parser/writer
├── templates/
│   └── storytelling_dashboard/
│       ├── dashboard.html           # Main dashboard (all 17 stories)
│       └── story_detail.html        # Story editor
└── README.md                        # This file
```

## API Endpoints

All endpoints require authentication.

### GET `/api/stories/`
Get all stories as JSON.

**Response:**
```json
{
  "success": true,
  "count": 17,
  "stories": [
    {
      "entry_id": 1,
      "title": "Game",
      "status": "complete",
      "format": "movie",
      "progress": 100,
      ...
    }
  ]
}
```

### GET `/api/story/{entry_id}/`
Get a single story by ID.

### POST `/api/story/{entry_id}/save/`
Save edits to a story.

**Payload:**
```json
{
  "title": "Story Title",
  "format": "movie",
  "talking_points": ["Hook 1", "Hook 2", "Hook 3"],
  "core_concept": "...",
  "synopsis": "...",
  "status": "in_progress"
}
```

### POST `/api/story/{entry_id}/validate/`
Validate story against ENGINE_SCHEMA.md rules.

**Response:**
```json
{
  "success": true,
  "valid": false,
  "issues": ["Title is required", "..."],
  "warnings": ["Expected 36+ chapters, found 12"],
  "progress": 45
}
```

## Markdown Parser

The `markdown_parser.py` module handles reading from and writing to `MASTER_DOCUMENT.md`.

### Key Classes

**`StoryEntry`**
- Represents a single story with all 13 sections
- Methods: `to_dict()`, `calculate_progress()`

**`StoryMarkdownParser`**
- Static methods for CRUD operations
- `load_all_stories()` — Load all 17 stories from markdown
- `get_story_by_id(id)` — Get single story
- `save_entry(story)` — Save story back to markdown

## Workflow

1. **Navigate to dashboard** → `/storytelling-dashboard/`
2. **Click "Edit" on a story** → Opens story_detail view
3. **Fill in sections:**
   - Title (locked once set)
   - Format (Short Series / 1-Hour / Movie / Epic)
   - Talking Points (3–5 hooks)
   - Core Concept (1 sentence + themes)
   - Synopsis (200–300 words)
4. **Click "Save Story"** → Updates MASTER_DOCUMENT.md
5. **Click "Validate"** → Checks against ENGINE_SCHEMA.md PART 2 + PART 6
6. **Repeat for remaining 10 placeholder entries**

## Admin Interface

Access at `/admin/storytelling_dashboard/storysession/`

- View/edit story metadata
- Filter by status, format, created date
- Search by title or entry_id
- Track last edited by + timestamp

## Notes

- **Source of Truth:** MASTER_DOCUMENT.md (markdown file)
- **Cache Layer:** StorySession model (for performance + metadata)
- **Auth:** Django built-in (login_required decorator)
- **Format:** Each story declares its format level (PART 6 of ENGINE_SCHEMA.md)

## Future Enhancements (v2.0)

- Full 13-section editor (currently only Sections 1–4)
- Character profile inline editor
- Soundtrack timeline builder
- Dynamic Navigation helper
- Real-time markdown preview
- Git commit integration
- Bulk import/export
