"""
MCP (Model Context Protocol) Tools for Android/Compose UI Generation.

Provides integration with:
- GitHub for finding real Compose examples
- FileSystem for reading/writing Android projects
"""

import os
import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from github import Github
from github.GithubException import GithubException


@dataclass
class ComposeExample:
    """Represents a Jetpack Compose code example from GitHub."""
    code: str
    description: str
    file_path: str
    repo_url: str


class GitHubMCP:
    """
    GitHub MCP integration for finding Jetpack Compose examples.
    
    Searches android/compose-samples repository for real-world examples
    that can be used as context for UI generation.
    """
    
    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize GitHub MCP client.
        
        Args:
            access_token: Optional GitHub personal access token for higher rate limits
        """
        self.github = Github(access_token) if access_token else Github()
        self.compose_repo = "android/compose-samples"
    
    def search_compose_examples(
        self, 
        query: str, 
        max_results: int = 5
    ) -> List[ComposeExample]:
        """
        Search for Jetpack Compose examples matching the query.
        
        Args:
            query: Natural language or keyword query
            max_results: Maximum number of examples to return
            
        Returns:
            List of ComposeExample objects
        """
        try:
            # Extract keywords from query
            keywords = self._extract_keywords(query)
            
            # Search GitHub repository
            repo = self.github.get_repo(self.compose_repo)
            examples = []
            
            # Search in specific paths that likely contain UI components
            search_paths = [
                "app/src/main/java",
                "samples",
                "ui",
                "compose"
            ]
            
            for path in search_paths:
                if len(examples) >= max_results:
                    break
                    
                try:
                    contents = repo.get_contents(path)
                    examples.extend(
                        self._search_in_contents(contents, keywords, max_results - len(examples))
                    )
                except GithubException:
                    # Path might not exist, continue
                    continue
            
            return examples[:max_results]
            
        except Exception as e:
            # Handle network errors gracefully
            print(f"Warning: GitHub search failed: {e}")
            return []
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract relevant keywords from natural language query."""
        # Remove common words
        stop_words = {'a', 'an', 'the', 'with', 'and', 'or', 'for', 'to', 'of', 'in'}
        words = query.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return keywords
    
    def _search_in_contents(
        self, 
        contents: Any, 
        keywords: List[str], 
        max_results: int
    ) -> List[ComposeExample]:
        """Recursively search repository contents for matching files."""
        examples = []
        
        try:
            # Handle both single file and list of files
            if not isinstance(contents, list):
                contents = [contents]
            
            for content in contents:
                if len(examples) >= max_results:
                    break
                
                # Recursively search directories
                if content.type == "dir":
                    try:
                        sub_contents = self.github.get_repo(self.compose_repo).get_contents(content.path)
                        examples.extend(
                            self._search_in_contents(sub_contents, keywords, max_results - len(examples))
                        )
                    except Exception:
                        continue
                
                # Process Kotlin files
                elif content.type == "file" and content.path.endswith(".kt"):
                    try:
                        code = content.decoded_content.decode('utf-8')
                        
                        # Only include files with @Composable
                        if "@Composable" in code:
                            # Check if keywords match file path or code
                            if self._matches_keywords(content.path + " " + code, keywords):
                                examples.append(ComposeExample(
                                    code=code,
                                    description=self._generate_description(code, content.path),
                                    file_path=content.path,
                                    repo_url=f"https://github.com/{self.compose_repo}"
                                ))
                    except Exception:
                        continue
        
        except Exception:
            pass
        
        return examples
    
    def _matches_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains any of the keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)
    
    def _generate_description(self, code: str, file_path: str) -> str:
        """Generate a description from the code and file path."""
        # Extract composable function names
        composables = re.findall(r'@Composable\s+fun\s+(\w+)', code)
        if composables:
            return f"Compose UI: {', '.join(composables[:3])}"
        return f"Compose example from {os.path.basename(file_path)}"


class FileSystemMCP:
    """
    FileSystem MCP integration for Android project operations.
    
    Handles reading existing project structure and writing multi-file projects.
    """
    
    def read_project_structure(self, project_path: str) -> Dict[str, Any]:
        """
        Read Android project structure and extract relevant information.
        
        Args:
            project_path: Path to Android project root
            
        Returns:
            Dict with project info including existing composables
        """
        structure = {
            "app": {},
            "manifest": {},
            "resources": {},
            "existing_composables": []
        }
        
        if not os.path.exists(project_path):
            return structure
        
        # Find existing Composable functions
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if file.endswith('.kt'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if '@Composable' in content:
                                # Extract function names
                                composables = re.findall(r'@Composable\s+fun\s+(\w+)', content)
                                for comp in composables:
                                    structure["existing_composables"].append({
                                        "name": comp,
                                        "file": os.path.relpath(file_path, project_path)
                                    })
                    except Exception:
                        continue
        
        # Check for manifest
        manifest_path = os.path.join(project_path, "app/src/main/AndroidManifest.xml")
        if os.path.exists(manifest_path):
            structure["manifest"]["exists"] = True
            structure["manifest"]["path"] = manifest_path
        
        return structure
    
    def write_multi_file_project(
        self, 
        output_path: str, 
        files: Dict[str, str],
        validate: bool = False
    ) -> Dict[str, Any]:
        """
        Write multiple files to create a project structure.
        
        Args:
            output_path: Base path to write files
            files: Dict mapping relative file paths to file contents
            validate: Whether to validate Kotlin syntax
            
        Returns:
            Result dict with status and files written
        """
        result = {
            "status": "success",
            "files_written": 0,
            "validation_errors": []
        }
        
        try:
            for file_path, content in files.items():
                # Validate if requested
                if validate and not self._validate_kotlin(content):
                    result["status"] = "error"
                    result["validation_errors"].append(f"Invalid syntax in {file_path}")
                    continue
                
                # Create full path
                full_path = os.path.join(output_path, file_path)
                
                # Create directories
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Write file
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                result["files_written"] += 1
        
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def _validate_kotlin(self, code: str) -> bool:
        """Basic Kotlin syntax validation."""
        # Check for obvious syntax errors
        if "@@" in code or "##" in code or "$$$$" in code:
            return False
        
        # Check for balanced braces
        open_braces = code.count('{')
        close_braces = code.count('}')
        
        return open_braces == close_braces
    
    def get_file_tree_preview(self, files: Dict[str, str]) -> str:
        """
        Generate a file tree preview string.
        
        Args:
            files: Dict mapping file paths to contents
            
        Returns:
            Formatted tree string
        """
        lines = []
        sorted_paths = sorted(files.keys())
        
        # Track directories we've shown
        shown_dirs = set()
        
        # Build tree structure
        for path in sorted_paths:
            parts = path.split('/')
            
            # Show directories first
            for i in range(len(parts) - 1):
                dir_path = '/'.join(parts[:i+1])
                if dir_path not in shown_dirs:
                    indent = "  " * i
                    lines.append(f"{indent}├── {parts[i]}/")
                    shown_dirs.add(dir_path)
            
            # Show file
            indent = "  " * (len(parts) - 1)
            name = parts[-1]
            lines.append(f"{indent}├── {name}")
        
        return "\n".join(lines)
    
    def check_android_project(self, project_path: str) -> bool:
        """
        Check if a directory is an Android project.
        
        Args:
            project_path: Path to check
            
        Returns:
            True if it's an Android project
        """
        # Check for build.gradle or build.gradle.kts
        has_gradle = (
            os.path.exists(os.path.join(project_path, "build.gradle")) or
            os.path.exists(os.path.join(project_path, "build.gradle.kts"))
        )
        
        # Check for AndroidManifest.xml
        has_manifest = os.path.exists(
            os.path.join(project_path, "app/src/main/AndroidManifest.xml")
        )
        
        return has_gradle and has_manifest
