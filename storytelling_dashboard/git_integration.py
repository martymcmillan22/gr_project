"""
Git integration for Story-Telling Dashboard.
Automatically commits story changes to GitHub with descriptive messages.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

import git
from django.conf import settings


class GitIntegration:
    """Handles git operations for story changes."""
    
    def __init__(self, repo_path: Optional[str] = None):
        """Initialize git integration with repository path."""
        self.repo_path = repo_path or settings.BASE_DIR
        try:
            self.repo = git.Repo(self.repo_path)
        except git.InvalidGitRepositoryError:
            self.repo = None
            
    def is_available(self) -> bool:
        """Check if git repository is available."""
        return self.repo is not None
    
    def get_changes_summary(self, story_data: Dict) -> str:
        """Generate a summary of what changed in the story."""
        changes = []
        
        if story_data.get('title'):
            changes.append(f"title: {story_data['title']}")
        
        talking_points = story_data.get('talking_points')
        if talking_points:
            count = len(talking_points) if isinstance(talking_points, (list, tuple)) else 1
            changes.append(f"talking points: {count} items")
        
        core_concept = story_data.get('core_concept')
        if core_concept:
            length = len(core_concept) if isinstance(core_concept, str) else len(str(core_concept))
            changes.append(f"core concept: {length} chars")
        
        synopsis = story_data.get('synopsis')
        if synopsis:
            length = len(synopsis) if isinstance(synopsis, str) else len(str(synopsis))
            changes.append(f"synopsis: {length} chars")
        
        chapters = story_data.get('chapters')
        if chapters is not None:
            count = len(chapters) if isinstance(chapters, (list, tuple)) else chapters
            changes.append(f"chapters: {count} total")
        
        characters = story_data.get('character_profiles')
        if characters:
            count = len(characters) if isinstance(characters, (list, tuple)) else 1
            changes.append(f"characters: {count} total")
        
        soundtracks = story_data.get('soundtrack_timeline')
        if soundtracks:
            count = len(soundtracks) if isinstance(soundtracks, (list, tuple)) else 1
            changes.append(f"soundtracks: {count} entries")
        
        if story_data.get('research_file'):
            changes.append(f"research: documented")
        if story_data.get('dynamic_navigation'):
            changes.append(f"navigation: defined")
        if story_data.get('bibliography'):
            changes.append(f"bibliography: added")
        if story_data.get('anti_plagiarism'):
            changes.append(f"originality: declared")
            
        return " | ".join(changes) if changes else "story updated"
    
    def generate_commit_message(self, entry_id: int, story_title: str, story_data: Dict) -> str:
        """Generate a meaningful commit message for story changes."""
        summary = self.get_changes_summary(story_data)
        
        message = (
            f"📖 Update story #{entry_id}: {story_title}\n\n"
            f"Changes:\n"
            f"  • {summary}\n\n"
            f"Updated via Story-Telling Dashboard\n"
            f"Timestamp: {datetime.now().isoformat()}"
        )
        
        return message
    
    def commit_story_changes(self, entry_id: int, story_title: str, story_data: Dict) -> bool:
        """Commit story changes to git repository."""
        if not self.is_available():
            return False
        
        try:
            # Generate commit message
            message = self.generate_commit_message(entry_id, story_title, story_data)
            
            # Get the MASTER_DOCUMENT.md file path (correct location with hyphen)
            master_doc_path = Path(self.repo_path) / "storytelling-engine" / "MASTER_DOCUMENT.md"
            
            if not master_doc_path.exists():
                return False
            
            # Stage the changes
            self.repo.index.add([str(master_doc_path)])
            
            # Check if there are actual changes to commit
            if not self.repo.index.diff("HEAD"):
                # No changes to commit
                return True
            
            # Commit the changes
            self.repo.index.commit(message)
            
            return True
        except Exception as e:
            print(f"Git commit error: {e}")
            return False
    
    def push_to_remote(self, remote_name: str = "origin", branch_name: Optional[str] = None) -> bool:
        """Push commits to remote repository."""
        if not self.is_available():
            return False
        
        try:
            # Use current branch if not specified
            if branch_name is None:
                branch_name = self.repo.active_branch.name
            
            remote = self.repo.remote(remote_name)
            remote.push(branch_name)
            return True
        except Exception as e:
            print(f"Git push error: {e}")
            return False
    
    def get_commit_history(self, file_path: Optional[str] = None, max_count: int = 5) -> List[Dict]:
        """Get recent commit history for file or repository."""
        if not self.is_available():
            return []
        
        try:
            if file_path:
                commits = list(self.repo.iter_commits(paths=file_path, max_count=max_count))
            else:
                commits = list(self.repo.iter_commits(max_count=max_count))
            
            history = []
            for commit in commits:
                history.append({
                    'hash': commit.hexsha[:7],
                    'author': commit.author.name,
                    'message': commit.message.split('\n')[0],  # First line only
                    'timestamp': datetime.fromtimestamp(commit.committed_date).isoformat(),
                })
            
            return history
        except Exception as e:
            print(f"Git history error: {e}")
            return []
    
    def get_status(self) -> Dict:
        """Get current git status."""
        if not self.is_available():
            return {'available': False}
        
        try:
            # Get modified files
            modified_files = []
            for item in self.repo.index.diff(None):
                modified_files.append(item.a_path)
            
            return {
                'available': True,
                'branch': self.repo.active_branch.name,
                'dirty': self.repo.is_dirty(),
                'untracked_files': len(self.repo.untracked_files),
                'modified_files': modified_files,
            }
        except Exception as e:
            return {'available': True, 'error': str(e)}


# Module-level singleton instance
_git_instance: Optional[GitIntegration] = None


def get_git_integration() -> GitIntegration:
    """Get or create git integration singleton."""
    global _git_instance
    if _git_instance is None:
        _git_instance = GitIntegration()
    return _git_instance
