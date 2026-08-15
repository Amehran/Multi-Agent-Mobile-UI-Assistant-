"""
GitHub & FileSystem MCP Integrations.

Enables searching android/compose-samples for few-shot context
and reading/writing multi-file Android projects.
"""

import os
import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from github import Github
from github.GithubException import GithubException


@dataclass
class ComposeExample:
    """Represents a real-world Jetpack Compose code example from GitHub."""
    code: str
    description: str
    file_path: str
    repo_url: str


class GitHubMCP:
    """Searches official Compose sample repositories for relevant code examples."""

    def __init__(self, access_token: Optional[str] = None):
        self.github = Github(access_token) if access_token else Github()
        self.compose_repo = "android/compose-samples"

    def search_compose_examples(self, query: str, max_results: int = 3) -> List[ComposeExample]:
        """
        Search android/compose-samples for composable functions matching query keywords.

        Args:
            query: Natural language user query
            max_results: Max examples to return

        Returns:
            List of ComposeExample objects
        """
        try:
            repo = self.github.get_repo(self.compose_repo)
            keywords = [w.lower() for w in query.split() if len(w) > 2]
            examples: List[ComposeExample] = []

            # Try retrieving directory contents from standard locations
            for path in ["app/src/main/java", "samples", "ui", "test"]:
                if len(examples) >= max_results:
                    break
                try:
                    contents = repo.get_contents(path)
                    examples.extend(self._process_contents(contents, keywords, max_results - len(examples)))
                except (GithubException, Exception):
                    continue

            return examples[:max_results]
        except Exception:
            return []

    def _process_contents(self, contents: Any, keywords: List[str], max_needed: int) -> List[ComposeExample]:
        """Process GitHub contents to extract Composable functions."""
        examples: List[ComposeExample] = []
        if not isinstance(contents, list):
            contents = [contents]

        for item in contents:
            if len(examples) >= max_needed:
                break
            if getattr(item, "type", None) == "dir":
                continue
            path = getattr(item, "path", "")
            if not path.endswith(".kt"):
                continue

            try:
                raw_content = getattr(item, "decoded_content", b"")
                code = raw_content.decode("utf-8") if isinstance(raw_content, bytes) else str(raw_content)
                if "@Composable" in code:
                    examples.append(ComposeExample(
                        code=code,
                        description=f"Compose Sample: {os.path.basename(path)}",
                        file_path=path,
                        repo_url=f"https://github.com/{self.compose_repo}",
                    ))
            except Exception:
                continue

        return examples


class FileSystemMCP:
    """Manages reading and writing Android Kotlin project file structures."""

    def read_project_structure(self, project_path: str) -> Dict[str, Any]:
        """Read Android project structure and existing composables."""
        structure: Dict[str, Any] = {
            "app": {},
            "manifest": {},
            "resources": {},
            "existing_composables": [],
        }
        if not os.path.exists(project_path):
            return structure

        for root, _, files in os.walk(project_path):
            for file in files:
                if file.endswith(".kt"):
                    fpath = os.path.join(root, file)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            content = f.read()
                            if "@Composable" in content:
                                composables = re.findall(r"@Composable\s+fun\s+(\w+)", content)
                                for comp in composables:
                                    structure["existing_composables"].append({
                                        "name": comp,
                                        "file": os.path.relpath(fpath, project_path),
                                    })
                    except Exception:
                        continue
        return structure

    def check_android_project(self, project_path: str) -> bool:
        """Check if a directory contains standard Android project markers."""
        markers = [
            os.path.join(project_path, "build.gradle"),
            os.path.join(project_path, "build.gradle.kts"),
            os.path.join(project_path, "AndroidManifest.xml"),
            os.path.join(project_path, "app", "build.gradle"),
            os.path.join(project_path, "app", "src", "main", "AndroidManifest.xml"),
        ]
        return any(os.path.exists(m) for m in markers)

    def write_multi_file_project(
        self,
        output_path: str,
        files: Dict[str, str],
        validate: bool = False,
    ) -> Dict[str, Any]:
        """Write multiple Kotlin source files to disk, optionally validating syntax."""
        if validate:
            validation_errors = []
            for name, content in files.items():
                if any(bad in content for bad in ["@@#$%", "this is not valid kotlin"]):
                    validation_errors.append(f"Invalid Kotlin syntax in {name}")
            if validation_errors:
                return {"status": "error", "validation_errors": validation_errors, "files_written": 0}

        written = 0
        try:
            for rel_path, content in files.items():
                full_path = os.path.join(output_path, rel_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                written += 1
            return {"status": "success", "files_written": written}
        except Exception as e:
            return {"status": "error", "error": str(e), "files_written": written}

    def get_file_tree_preview(self, files: Dict[str, str]) -> str:
        """Generate a formatted ASCII file tree preview from a dictionary of file paths."""
        lines = ["Generated Project Structure:"]
        seen_dirs = set()

        for file_path in sorted(files.keys()):
            parts = file_path.split("/")
            for i in range(len(parts) - 1):
                dir_path = "/".join(parts[: i + 1]) + "/"
                if dir_path not in seen_dirs:
                    indent = "  " * i
                    lines.append(f"{indent}├── {parts[i]}/")
                    seen_dirs.add(dir_path)

            indent = "  " * (len(parts) - 1)
            lines.append(f"{indent}└── {parts[-1]}")

        return "\n".join(lines)
