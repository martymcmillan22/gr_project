"""
Markdown Parser/Writer for Story-Telling Engine MASTER_DOCUMENT.md

Handles reading story entries from and writing story entries back to MASTER_DOCUMENT.md
while preserving the document structure and all non-story sections.
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Optional


MASTER_DOCUMENT_PATH = Path('/Users/martymcmillan/Desktop/GrassRoots/storytelling-engine/MASTER_DOCUMENT.md')

# Story format levels
FORMAT_CHOICES = {
    'short_series': 'Short Series (Sitcom)',
    'one_hour_series': '1-Hour Long Series Episode',
    'movie': 'Movie (90–120 minutes)',
    'epic_movie': 'Epic Movie (3+ hours)'
}


class StoryEntry:
    """Represents a single story entry with all 13 sections."""
    
    def __init__(self, entry_id: int, title: str = "", status: str = "pending"):
        self.entry_id = entry_id
        self.title = title
        self.status = status  # "complete", "pending", "in_progress"
        self.format = "movie"  # default
        
        # 13 Sections
        self.talking_points = []
        self.core_concept = ""
        self.synopsis = ""
        self.chapters = []  # List of chapter dicts: {number, title, description}
        self.dynamic_navigation = ""
        self.soundtrack_timeline = []
        self.character_profiles = []
        self.research_file = ""
        self.future_timeline = ""
        self.table_of_contents = ""
        self.bibliography = ""
        self.anti_plagiarism = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            'entry_id': self.entry_id,
            'title': self.title,
            'status': self.status,
            'format': self.format,
            'talking_points': self.talking_points,
            'core_concept': self.core_concept,
            'synopsis': self.synopsis,
            'chapters': self.chapters,
            'character_profiles': self.character_profiles,
            'chapter_count': len(self.chapters),
            'character_count': len(self.character_profiles),
            'chapters_preview': self.chapters[:3] if self.chapters else [],
            'progress': self.calculate_progress(),
        }
    
    def calculate_progress(self) -> float:
        """Calculate completion percentage (0-100)."""
        sections_filled = 0
        total_sections = 13
        
        if self.title: sections_filled += 1
        if self.talking_points: sections_filled += 1
        if self.core_concept: sections_filled += 1
        if self.synopsis: sections_filled += 1
        if self.chapters: sections_filled += 1
        if self.dynamic_navigation: sections_filled += 1
        if self.soundtrack_timeline: sections_filled += 1
        if self.character_profiles: sections_filled += 1
        if self.research_file: sections_filled += 1
        if self.future_timeline: sections_filled += 1
        if self.table_of_contents: sections_filled += 1
        if self.bibliography: sections_filled += 1
        if self.anti_plagiarism: sections_filled += 1
        
        return int((sections_filled / total_sections) * 100)


class StoryMarkdownParser:
    """Parse and write story entries from/to MASTER_DOCUMENT.md."""
    
    @staticmethod
    def load_all_stories() -> List[StoryEntry]:
        """Load all story entries from MASTER_DOCUMENT.md."""
        if not MASTER_DOCUMENT_PATH.exists():
            return StoryMarkdownParser._get_default_placeholder_entries()
        
        content = MASTER_DOCUMENT_PATH.read_text(encoding='utf-8')
        stories = []
        
        # Parse the document into story sections
        # Entry pattern: ## **ENTRY N — Title**
        entry_pattern = r'## \*\*ENTRY (\d+) — (.+?)\*\*'
        matches = list(re.finditer(entry_pattern, content))
        
        # Completed entries (Section 2)
        completed_start = content.find('# 📚 **SECTION 2 — COMPLETED STORY ENTRIES**')
        completed_end = content.find('# 📝 **SECTION 3 — PLACEHOLDER STORY ENTRIES')
        
        if completed_start != -1 and completed_end != -1:
            completed_section = content[completed_start:completed_end]
            for match in matches:
                if match.start() >= completed_start and match.start() < completed_end:
                    entry_id = int(match.group(1))
                    title = match.group(2)
                    story = StoryMarkdownParser._parse_entry(content, entry_id, title, 'complete')
                    stories.append(story)
        
        # Placeholder entries (Section 3)
        placeholder_section = content[completed_end:] if completed_end != -1 else ""
        for match in matches:
            if match.start() >= completed_end:
                entry_id = int(match.group(1))
                title = match.group(2)
                story = StoryMarkdownParser._parse_entry(content, entry_id, title, 'pending')
                stories.append(story)
        
        # If no entries found, return defaults
        if not stories:
            return StoryMarkdownParser._get_default_placeholder_entries()
        
        return sorted(stories, key=lambda s: s.entry_id)
    
    @staticmethod
    def _get_default_placeholder_entries() -> List[StoryEntry]:
        """Return default placeholder entries if parsing fails."""
        titles = [
            "Game",
            "Game 23",
            "4th State",
            "ExPost (ExPost Facto)",
            "Reclaiming Clarity",
            "Sergon General (Instinctive Behavior)",
            "Vicarious",
            "Dear Darwin",
            "Me and My Friends",
            "Live Fast Die Old",
            "435 — Gerrymander",
            "Big Game",
            "Honor Amongst",
            "Humanical Factor",
            "ICMPE (Instinctive Conscious of Momentum's Paternal Essence)",
            "Love's Composition",
            "Magic & Science",
        ]
        
        stories = []
        for i, title in enumerate(titles, 1):
            story = StoryEntry(i, title, 'complete' if i <= 7 else 'pending')
            stories.append(story)
        
        return stories
    
    @staticmethod
    def _parse_entry(content: str, entry_id: int, title: str, status: str) -> StoryEntry:
        """Parse a single entry from the document."""
        story = StoryEntry(entry_id, title, status)
        story.format = "movie"  # Default; would be parsed from entry if available
        
        # Find the entry section
        entry_header = f'## **ENTRY {entry_id} — '
        start_idx = content.find(entry_header)
        if start_idx == -1:
            return story
        
        # Find the end of this entry (next entry, section, or end of file)
        next_entry_pattern = r'^## \*\*ENTRY \d+ —'
        next_section_pattern = r'^# 📝|^# 📚|^# 🧭'
        
        lines = content[start_idx:].split('\n')
        end_offset = len(lines)
        
        for i, line in enumerate(lines[1:], 1):
            if (re.match(next_entry_pattern, line) or 
                re.match(next_section_pattern, line) or
                line.startswith('---')):
                end_offset = i
                break
        
        entry_content = '\n'.join(lines[:end_offset])
        
        # Extract sections
        story.talking_points = StoryMarkdownParser._extract_section(entry_content, 'Talking Points')
        story.core_concept = StoryMarkdownParser._extract_text_section(entry_content, 'Core Concept')
        story.synopsis = StoryMarkdownParser._extract_text_section(entry_content, 'Synopsis')
        story.chapters = StoryMarkdownParser._extract_chapters(entry_content)
        story.character_profiles = StoryMarkdownParser._extract_characters(entry_content)
        story.dynamic_navigation = StoryMarkdownParser._extract_text_section(entry_content, 'Dynamic Navigation')
        story.soundtrack_timeline = StoryMarkdownParser._extract_soundtracks(entry_content)
        story.research_file = StoryMarkdownParser._extract_text_section(entry_content, 'Research File')
        story.future_timeline = StoryMarkdownParser._extract_text_section(entry_content, 'Future Timeline')
        story.table_of_contents = StoryMarkdownParser._extract_text_section(entry_content, 'Table of Contents')
        story.bibliography = StoryMarkdownParser._extract_text_section(entry_content, 'Bibliography')
        story.anti_plagiarism = StoryMarkdownParser._extract_text_section(entry_content, 'Anti‑Plagiarism Section')
        
        return story
    
    @staticmethod
    def _extract_text_section(entry_content: str, section_name: str) -> str:
        """Extract a text section from entry content."""
        pattern = rf'### {section_name}\n(.+?)(?=###|$)'
        match = re.search(pattern, entry_content, re.DOTALL)
        if match:
            text = match.group(1).strip()
            # Remove placeholder text
            if text.startswith('*') and text.endswith('*'):
                return ""
            return text
        return ""
    
    @staticmethod
    def _extract_section(entry_content: str, section_name: str) -> List:
        """Extract a list section (bullet points) from entry content."""
        pattern = rf'### {section_name}\n(.+?)(?=###|$)'
        match = re.search(pattern, entry_content, re.DOTALL)
        items = []
        if match:
            section_text = match.group(1).strip()
            # Parse bullet points
            for line in section_text.split('\n'):
                line = line.strip()
                if line.startswith('- '):
                    items.append(line[2:].strip())
        return items
    
    @staticmethod
    def _extract_chapters(entry_content: str) -> List[Dict]:
        """Extract chapters from entry content."""
        chapters = []
        pattern = r'### Chapter Structure.*?\n(.+?)(?=###|$)'
        match = re.search(pattern, entry_content, re.DOTALL)
        if match:
            section_text = match.group(1)
            # Parse chapter entries: - Chapter N: Title - Description
            chapter_pattern = r'- Chapter (\d+):\s*(.+?)\s*-\s*(.+?)(?=\n-|\n###|$)'
            for ch_match in re.finditer(chapter_pattern, section_text, re.DOTALL):
                chapters.append({
                    'number': int(ch_match.group(1)),
                    'title': ch_match.group(2).strip(),
                    'description': ch_match.group(3).strip()
                })
        return chapters
    
    @staticmethod
    def _extract_characters(entry_content: str) -> List[Dict]:
        """Extract character profiles from entry content."""
        characters = []
        # Find Character Profiles section and extract until next ### section
        pattern = r'### Character Profiles\n(.*?)(?=\n### [A-Z]|\n---|\Z)'
        match = re.search(pattern, entry_content, re.DOTALL)
        if match:
            section_text = match.group(1)
            # Split by character entries (#### Name (type))
            char_pattern = r'#### (.+?)\s*\((.+?)\)(.*?)(?=\n#### |\Z)'
            for char_match in re.finditer(char_pattern, section_text, re.DOTALL):
                name = char_match.group(1).strip()
                char_type = char_match.group(2).strip()
                details_text = char_match.group(3).strip()
                
                character = {'name': name, 'type': char_type}
                # Parse **Field:** Value lines
                field_pattern = r'\*\*(.+?)\:\*\*\s*(.+?)(?=\n\*\*|\n####|\Z)'
                for field_match in re.finditer(field_pattern, details_text, re.DOTALL):
                    field_name = field_match.group(1).strip()
                    field_value = field_match.group(2).strip()
                    # Convert field name to key format
                    field_key = field_name.lower().replace(' ', '_')
                    character[field_key] = field_value
                
                characters.append(character)
        return characters
    
    @staticmethod
    def _extract_soundtracks(entry_content: str) -> List[Dict]:
        """Extract soundtrack timeline from entry content as structured objects."""
        soundtracks = []
        pattern = r'### Soundtrack Timeline\n(.*?)(?=\n### [A-Z]|\n---|\Z)'
        match = re.search(pattern, entry_content, re.DOTALL)
        if match:
            section_text = match.group(1).strip()
            # Skip placeholder
            if section_text.startswith('*') and section_text.endswith('*'):
                return []
            
            # Parse bullet-point format: - Ch N (HH:MM) - Song Name by Artist, Mood
            line_pattern = r'-\s*Ch\s*(\d+)\s*\((\d{1,2}:\d{2})\)\s*-\s*(.+?)\s+by\s+(.+?),\s*(.+?)$'
            for line in section_text.split('\n'):
                line = line.strip()
                if not line or line.startswith('*'):
                    continue
                    
                line_match = re.search(line_pattern, line)
                if line_match:
                    soundtracks.append({
                        'chapter': int(line_match.group(1)),
                        'timestamp': line_match.group(2),
                        'song': line_match.group(3).strip(),
                        'artist': line_match.group(4).strip(),
                        'mood': line_match.group(5).strip()
                    })
                else:
                    # Try alternate format without explicit "by" separator
                    # - Ch N (HH:MM) - Description, Mood
                    alt_pattern = r'-\s*Ch\s*(\d+)\s*\((\d{1,2}:\d{2})\)\s*-\s*(.+?),\s*(.+?)$'
                    alt_match = re.search(alt_pattern, line)
                    if alt_match:
                        soundtracks.append({
                            'chapter': int(alt_match.group(1)),
                            'timestamp': alt_match.group(2),
                            'song': alt_match.group(3).strip(),
                            'artist': 'Unknown',
                            'mood': alt_match.group(4).strip()
                        })
        
        return soundtracks
    
    @staticmethod
    def save_entry(story: StoryEntry) -> bool:
        """Save/update a story entry back to MASTER_DOCUMENT.md."""
        if not MASTER_DOCUMENT_PATH.exists():
            return False
        
        try:
            content = MASTER_DOCUMENT_PATH.read_text(encoding='utf-8')
            
            # Build the new entry content
            new_entry = StoryMarkdownParser._build_entry_markdown(story)
            
            # Find and replace the entry
            entry_header = f'## **ENTRY {story.entry_id} — '
            start_idx = content.find(entry_header)
            if start_idx == -1:
                return False
            
            # Find the end of this entry
            lines_before = content[:start_idx].split('\n')
            lines_after = content[start_idx:].split('\n')
            
            end_offset = 0
            for i, line in enumerate(lines_after[1:], 1):
                if (re.match(r'^## \*\*ENTRY \d+', line) or 
                    re.match(r'^# 📝|^# 📚|^# 🧭', line) or
                    line == '---'):
                    end_offset = i
                    break
            
            if end_offset == 0:
                end_offset = len(lines_after)
            
            # Reconstruct content
            before_entry = '\n'.join(lines_before)
            after_entry = '\n'.join(lines_after[end_offset:])
            
            new_content = before_entry + '\n' + new_entry + '\n' + after_entry
            
            # Write back to file
            MASTER_DOCUMENT_PATH.write_text(new_content, encoding='utf-8')
            return True
        except Exception as e:
            print(f"Error saving entry: {e}")
            return False
    
    @staticmethod
    def _build_entry_markdown(story: StoryEntry) -> str:
        """Build markdown content for a story entry."""
        lines = [
            f'## **ENTRY {story.entry_id} — {story.title}**',
            '',
            f'**Status:** {story.status}',
            f'**Format:** {story.format}',
            '',
        ]
        
        # Talking Points
        lines.append('### Talking Points')
        if story.talking_points:
            for point in story.talking_points:
                lines.append(f'- {point}')
        else:
            lines.append('*Pending*')
        lines.append('')
        
        # Core Concept
        lines.append('### Core Concept')
        if story.core_concept:
            lines.append(story.core_concept)
        else:
            lines.append('*Pending*')
        lines.append('')
        
        # Synopsis
        lines.append('### Synopsis')
        if story.synopsis:
            lines.append(story.synopsis)
        else:
            lines.append('*Pending*')
        lines.append('')
        
        # Chapter Structure
        lines.append(f'### Chapter Structure ({story.format})')
        if story.chapters:
            for chapter in story.chapters:
                lines.append(f"- Chapter {chapter.get('number', '')}: {chapter.get('title', '')} - {chapter.get('description', '')}")
        else:
            lines.append('*Pending*')
        lines.append('')
        
        # Dynamic Navigation
        lines.append('### Dynamic Navigation')
        if story.dynamic_navigation:
            lines.append(story.dynamic_navigation)
        else:
            lines.append('*Pending*')
        lines.append('')
        
        # Soundtrack Timeline
        lines.append('### Soundtrack Timeline')
        if story.soundtrack_timeline:
            for item in story.soundtrack_timeline:
                if isinstance(item, dict):
                    # Structured format
                    chapter = item.get('chapter', '')
                    timestamp = item.get('timestamp', '')
                    song = item.get('song', '')
                    artist = item.get('artist', '')
                    mood = item.get('mood', '')
                    lines.append(f'- Ch {chapter} ({timestamp}) - {song} by {artist}, {mood}')
                else:
                    # Legacy string format
                    lines.append(f'- {item}')
        else:
            lines.append('*Pending*')
        lines.append('')
        
        # Character Profiles
        lines.append('### Character Profiles')
        if story.character_profiles:
            for char in story.character_profiles:
                char_type = char.get('type', 'main')
                lines.append(f"#### {char.get('name', 'Unknown')} ({char_type})")
                lines.append(f"**Role:** {char.get('role', '')}")
                lines.append(f"**Appearance:** {char.get('appearance', '')}")
                lines.append(f"**Personality:** {char.get('personality', '')}")
                lines.append(f"**Motivation:** {char.get('motivation', '')}")
                lines.append(f"**Arc:** {char.get('arc', '')}")
                lines.append(f"**Relationships:** {char.get('relationships', '')}")
                lines.append('')
        else:
            lines.append('*Pending*')
        lines.append('')
        
        # Research File
        lines.append('### Research File')
        if story.research_file:
            lines.append(story.research_file)
        else:
            lines.append('*Pending*')
        lines.append('')
        
        # Future Timeline
        lines.append('### Future Timeline')
        if story.future_timeline:
            lines.append(story.future_timeline)
        else:
            lines.append('*Pending*')
        lines.append('')
        
        # Table of Contents
        lines.append('### Table of Contents')
        if story.table_of_contents:
            lines.append(story.table_of_contents)
        else:
            lines.append('*Pending*')
        lines.append('')
        
        # Bibliography
        lines.append('### Bibliography')
        if story.bibliography:
            lines.append(story.bibliography)
        else:
            lines.append('*Pending*')
        lines.append('')
        
        # Anti-Plagiarism Section
        lines.append('### Anti‑Plagiarism Section')
        if story.anti_plagiarism:
            lines.append(story.anti_plagiarism)
        else:
            lines.append('*Pending*')
        lines.append('')
        
        lines.append('---')
        
        return '\n'.join(lines)
    
    @staticmethod
    def get_story_by_id(entry_id: int) -> Optional[StoryEntry]:
        """Get a single story by ID."""
        stories = StoryMarkdownParser.load_all_stories()
        for story in stories:
            if story.entry_id == entry_id:
                return story
        return None
