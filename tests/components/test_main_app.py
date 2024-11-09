"""Unit tests for the MainApp component using London-style TDD."""

import pytest
from unittest.mock import MagicMock, patch

def test_main_app_creation(mock_streamlit, mock_session_state):
    """Test MainApp component creation."""
    from src.components.main_app import MainApp
    
    # Create MainApp instance
    app = MainApp()
    
    # Verify initialization
    assert app.session_state == mock_session_state
    assert hasattr(app, 'theme')
    assert hasattr(app, 'sidebar')

def test_session_state_initialization(mock_streamlit, mock_session_state):
    """Test session state is initialized correctly."""
    from src.components.main_app import MainApp
    
    # Create MainApp instance
    app = MainApp()
    
    # Verify session state initialization
    assert 'project' in mock_session_state
    assert mock_session_state['project'] is None
    assert 'dark_mode' in mock_session_state
    assert mock_session_state['dark_mode'] is True

def test_theme_setup(mock_streamlit):
    """Test theme configuration."""
    from src.components.main_app import MainApp
    
    # Create MainApp instance
    app = MainApp()
    
    # Verify theme setup
    mock_streamlit.set_page_config.assert_called_once_with(
        layout="wide",
        initial_sidebar_state="expanded"
    )

def test_sidebar_creation(mock_streamlit):
    """Test sidebar creation and configuration."""
    from src.components.main_app import MainApp
    
    # Create MainApp instance
    app = MainApp()
    
    # Verify sidebar setup
    mock_streamlit.sidebar.image.assert_called_once()
    mock_streamlit.sidebar.title.assert_called_once_with("SPARC GUI")
    mock_streamlit.sidebar.radio.assert_called_once()

def test_navigation_handling(mock_streamlit):
    """Test navigation selection handling."""
    from src.components.main_app import MainApp
    
    # Mock navigation selection
    mock_streamlit.sidebar.radio.return_value = "Project"
    
    # Create MainApp instance
    app = MainApp()
    
    # Verify navigation options
    mock_streamlit.sidebar.radio.assert_called_with(
        "Navigation",
        ["Project", "Code", "Tests", "Settings"]
    )

@pytest.mark.parametrize("page", ["Project", "Code", "Tests", "Settings"])
def test_page_display(mock_streamlit, page):
    """Test display of different pages."""
    from src.components.main_app import MainApp
    
    # Mock page selection
    mock_streamlit.sidebar.radio.return_value = page
    
    # Create MainApp instance
    app = MainApp()
    
    # Call display method
    app.display()
    
    # Verify page title is set
    mock_streamlit.title.assert_called_once()
