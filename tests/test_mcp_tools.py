"""
Tests for MCP (Model Context Protocol) tools integration.

Following TDD methodology:
1. RED: Write failing tests that define desired behavior
2. GREEN: Implement minimal code to make tests pass
3. REFACTOR: Improve code while keeping tests green
"""

import pytest
from unittest.mock import Mock, patch
from src.multi_agent_mobile_ui_assistant.mcp_tools import (
    GitHubMCP,
    FileSystemMCP,
    ComposeExample,
)


class TestGitHubMCP:
    """Test GitHub MCP integration for finding Compose examples."""
    
    def test_search_compose_examples_returns_list_of_examples(self):
        """
        GIVEN a search query for UI pattern
        WHEN searching GitHub compose-samples repository
        THEN should return list of ComposeExample objects
        """
        github_mcp = GitHubMCP()
        query = "login screen"
        
        examples = github_mcp.search_compose_examples(query, max_results=3)
        
        assert isinstance(examples, list)
        assert len(examples) <= 3
        assert all(isinstance(ex, ComposeExample) for ex in examples)
    
    def test_compose_example_has_required_fields(self):
        """
        GIVEN a ComposeExample object
        THEN it should have code, description, file_path, and repo_url
        """
        example = ComposeExample(
            code="@Composable fun LoginScreen() {}",
            description="Login screen with email and password",
            file_path="samples/authentication/LoginScreen.kt",
            repo_url="https://github.com/android/compose-samples"
        )
        
        assert example.code == "@Composable fun LoginScreen() {}"
        assert example.description == "Login screen with email and password"
        assert example.file_path == "samples/authentication/LoginScreen.kt"
        assert example.repo_url == "https://github.com/android/compose-samples"
    
    @patch('src.multi_agent_mobile_ui_assistant.mcp_tools.Github')
    def test_search_with_keywords_extraction(self, mock_github):
        """
        GIVEN a natural language query
        WHEN searching for compose examples
        THEN should extract keywords and search GitHub
        """
        # Setup mock
        mock_repo = Mock()
        mock_github.return_value.get_repo.return_value = mock_repo
        mock_content = Mock()
        mock_content.decoded_content = b"@Composable fun TestScreen() {}"
        mock_content.path = "test/Screen.kt"
        mock_repo.get_contents.return_value = [mock_content]
        
        github_mcp = GitHubMCP(access_token=None)
        _ = github_mcp.search_compose_examples("create a profile card", max_results=1)
        
        # Should search the repository
        mock_github.return_value.get_repo.assert_called_once()
    
    def test_search_handles_no_results_gracefully(self):
        """
        GIVEN a query that matches no examples
        WHEN searching GitHub
        THEN should return empty list without errors
        """
        github_mcp = GitHubMCP()
        examples = github_mcp.search_compose_examples("xyznonexistent123", max_results=5)
        
        assert examples == []
    
    @patch('src.multi_agent_mobile_ui_assistant.mcp_tools.Github')
    def test_search_filters_compose_files_only(self, mock_github):
        """
        GIVEN search results with mixed file types
        WHEN filtering results
        THEN should only return .kt files with @Composable
        """
        mock_repo = Mock()
        mock_github.return_value.get_repo.return_value = mock_repo
        
        # Mix of composable and non-composable files
        mock_kt_file = Mock()
        mock_kt_file.decoded_content = b"@Composable fun MyUI() {}"
        mock_kt_file.path = "ui/MyUI.kt"
        
        mock_non_compose = Mock()
        mock_non_compose.decoded_content = b"class DataModel {}"
        mock_non_compose.path = "data/Model.kt"
        
        mock_repo.get_contents.return_value = [mock_kt_file, mock_non_compose]
        
        github_mcp = GitHubMCP()
        results = github_mcp.search_compose_examples("UI component", max_results=10)
        
        # Should only return the composable file
        assert all("@Composable" in ex.code for ex in results)


class TestFileSystemMCP:
    """Test FileSystem MCP integration for Android project operations."""
    
    def test_read_project_structure_returns_dict(self):
        """
        GIVEN an Android project directory
        WHEN reading project structure
        THEN should return dict with app, manifest, and resources info
        """
        fs_mcp = FileSystemMCP()
        structure = fs_mcp.read_project_structure("/fake/android/project")
        
        assert isinstance(structure, dict)
        assert "app" in structure
        assert "manifest" in structure
        assert "resources" in structure
    
    def test_read_project_structure_finds_existing_composables(self):
        """
        GIVEN a project with existing Composable components
        WHEN reading project structure
        THEN should list all @Composable functions found
        """
        fs_mcp = FileSystemMCP()
        
        with patch('os.path.exists', return_value=True):
            with patch('os.walk') as mock_walk:
                mock_walk.return_value = [
                    ('/fake/app/ui', [], ['Button.kt', 'Card.kt']),
                ]
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = (
                        "@Composable fun CustomButton() {}"
                    )
                    
                    structure = fs_mcp.read_project_structure("/fake/android/project")
        
        assert "existing_composables" in structure
        assert isinstance(structure["existing_composables"], list)
    
    def test_write_multi_file_project_creates_directory_structure(self):
        """
        GIVEN multiple files to generate (Activity, Composables, ViewModel)
        WHEN writing multi-file project
        THEN should create proper Android directory structure
        """
        fs_mcp = FileSystemMCP()
        
        files = {
            "MainActivity.kt": "class MainActivity : ComponentActivity() {}",
            "ui/LoginScreen.kt": "@Composable fun LoginScreen() {}",
            "ui/components/Button.kt": "@Composable fun CustomButton() {}",
            "viewmodel/LoginViewModel.kt": "class LoginViewModel : ViewModel() {}"
        }
        
        with patch('os.makedirs') as mock_makedirs:
            with patch('builtins.open', create=True):
                result = fs_mcp.write_multi_file_project("/output/path", files)
        
        # Should create directories
        assert mock_makedirs.called
        # Should return success status
        assert result["status"] == "success"
        assert result["files_written"] == 4
    
    def test_write_multi_file_validates_kotlin_syntax(self):
        """
        GIVEN files with invalid Kotlin syntax
        WHEN writing multi-file project
        THEN should validate and return errors
        """
        fs_mcp = FileSystemMCP()
        
        files = {
            "Invalid.kt": "this is not valid kotlin @@#$%"
        }
        
        result = fs_mcp.write_multi_file_project("/output/path", files, validate=True)
        
        assert result["status"] == "error"
        assert "validation_errors" in result
    
    def test_get_file_tree_preview_returns_string(self):
        """
        GIVEN a dict of files to generate
        WHEN getting file tree preview
        THEN should return formatted tree string
        """
        fs_mcp = FileSystemMCP()
        
        files = {
            "MainActivity.kt": "...",
            "ui/LoginScreen.kt": "...",
            "ui/components/Button.kt": "..."
        }
        
        tree = fs_mcp.get_file_tree_preview(files)
        
        assert isinstance(tree, str)
        assert "MainActivity.kt" in tree
        assert "ui/" in tree
        assert "components/" in tree
    
    def test_check_android_project_detects_valid_project(self):
        """
        GIVEN a directory with build.gradle and AndroidManifest.xml
        WHEN checking if it's an Android project
        THEN should return True
        """
        fs_mcp = FileSystemMCP()
        
        with patch('os.path.exists') as mock_exists:
            # Simulate finding build.gradle and manifest
            mock_exists.side_effect = lambda path: (
                'build.gradle' in path or 'AndroidManifest.xml' in path
            )
            
            is_android = fs_mcp.check_android_project("/fake/project")
        
        assert is_android is True
    
    def test_check_android_project_returns_false_for_non_android(self):
        """
        GIVEN a directory without Android project files
        WHEN checking if it's an Android project
        THEN should return False
        """
        fs_mcp = FileSystemMCP()
        
        with patch('os.path.exists', return_value=False):
            is_android = fs_mcp.check_android_project("/fake/project")
        
        assert is_android is False


class TestMCPIntegration:
    """Integration tests for MCP tools working together."""
    
    @patch('src.multi_agent_mobile_ui_assistant.mcp_tools.Github')
    def test_github_and_filesystem_mcp_work_together(self, mock_github):
        """
        GIVEN GitHub examples and local project structure
        WHEN generating UI with both contexts
        THEN should combine information from both sources
        """
        # Setup GitHub mock
        mock_repo = Mock()
        mock_github.return_value.get_repo.return_value = mock_repo
        mock_content = Mock()
        mock_content.decoded_content = b"@Composable fun ExampleButton() {}"
        mock_content.path = "example.kt"
        mock_repo.get_contents.return_value = [mock_content]
        
        github_mcp = GitHubMCP()
        fs_mcp = FileSystemMCP()
        
        # Get examples from GitHub
        examples = github_mcp.search_compose_examples("button", max_results=1)
        
        # Check local project
        with patch('os.path.exists', return_value=True):
            with patch('os.walk', return_value=[]):
                project_info = fs_mcp.read_project_structure("/fake/project")
        
        # Both should provide useful context
        assert len(examples) > 0 or project_info is not None
    
    def test_mcp_tools_handle_network_errors_gracefully(self):
        """
        GIVEN network connectivity issues
        WHEN using MCP tools
        THEN should handle errors gracefully without crashing
        """
        github_mcp = GitHubMCP()
        
        with patch('src.multi_agent_mobile_ui_assistant.mcp_tools.Github') as mock_github:
            mock_github.side_effect = Exception("Network error")
            
            # Should not raise, should return empty list
            try:
                examples = github_mcp.search_compose_examples("test", max_results=1)
                assert examples == []
            except Exception:
                pytest.fail("Should handle network errors gracefully")
