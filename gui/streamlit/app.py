import streamlit as st
import streamlit.components.v1 as components
import sys
from pathlib import Path
import base64
import os
import git
import toml
from datetime import datetime

# Add parent directory to Python path to find utils module
sys.path.append(str(Path(__file__).parent.parent))

# Configure Streamlit page - must be first Streamlit command
st.set_page_config(
    page_title="SPARC GUI",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark mode CSS
dark_mode_css = """
<style>
    /* Dark mode styles */
    .stApp {
        background-color: #1E1E1E;
        color: #FFFFFF;
    }
    .stSidebar {
        background-color: #252526;
    }
    .stButton>button {
        background-color: #2D2D2D;
        color: #FFFFFF;
        border: 1px solid #3E3E3E;
    }
    .stTextInput>div>div>input {
        background-color: #2D2D2D;
        color: #FFFFFF;
    }
    .stSelectbox>div>div>select {
        background-color: #2D2D2D;
        color: #FFFFFF;
    }
</style>
"""

# Inject dark mode CSS
st.markdown(dark_mode_css, unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables."""
    if 'project_path' not in st.session_state:
        st.session_state.project_path = None
    if 'components' not in st.session_state:
        st.session_state.components = []
    if 'git_repo' not in st.session_state:
        st.session_state.git_repo = None

def load_project(path: str) -> bool:
    """Load an existing SPARC project."""
    try:
        project_dir = Path(path)
        if not project_dir.exists():
            st.error(f"Project directory does not exist: {path}")
            return False
            
        # Check for architecture files
        arch_dir = project_dir / "architecture"
        if not arch_dir.exists() or not any(arch_dir.iterdir()):
            st.error("No architecture files found. Please initialize project first.")
            return False
            
        # Load guidance if exists
        guidance_file = project_dir / "guidance.toml"
        if guidance_file.exists():
            with open(guidance_file) as f:
                st.session_state.guidance = toml.load(f)
                
        # Setup git repo
        try:
            st.session_state.git_repo = git.Repo(path)
        except git.InvalidGitRepositoryError:
            st.warning("Git repository not initialized")
            
        st.session_state.project_path = path
        return True
        
    except Exception as e:
        st.error(f"Failed to load project: {str(e)}")
        return False

def show_project_status():
    """Display project status information."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Project Info")
        st.text(f"Location: {st.session_state.project_path}")
        
        # Show architecture files
        arch_dir = Path(st.session_state.project_path) / "architecture"
        if arch_dir.exists():
            files = list(arch_dir.glob("*.md"))
            st.write("Architecture Files:")
            for f in files:
                st.text(f"- {f.name}")
                
    with col2:
        st.subheader("Git Status")
        if st.session_state.git_repo:
            repo = st.session_state.git_repo
            st.text(f"Branch: {repo.active_branch.name}")
            st.text(f"Last Commit: {repo.head.commit.message}")
            
            # Show changes
            if repo.is_dirty():
                st.warning("Uncommitted Changes:")
                for item in repo.index.diff(None):
                    st.text(f"- Modified: {item.a_path}")
        else:
            st.warning("Git not initialized")

def show_components():
    """Display project components."""
    st.subheader("Components")
    
    # Read components from Architecture.md
    arch_file = Path(st.session_state.project_path) / "architecture" / "Architecture.md"
    if arch_file.exists():
        content = arch_file.read_text()
        
        # Extract components using simple parsing
        import re
        components = re.findall(r'## Component: (\w+)', content)
        
        if components:
            for comp in components:
                with st.expander(comp):
                    st.text("Status: Implemented")
                    if st.button(f"View {comp} Details", key=f"view_{comp}"):
                        st.session_state.selected_component = comp
        else:
            st.info("No components defined in Architecture.md")
    else:
        st.error("Architecture.md not found")

def main():
    # Sidebar
    with st.sidebar:
        st.title("SPARC GUI")
        st.markdown("---")
        page = st.radio(
            "Navigation",
            ["Project", "Code", "Tests", "Settings"]
        )

    # Main content
    if page == "Project":
        from utils.database import init_db, save_project, get_projects
        from utils.project import scan_architecture_folders, load_project_files, init_git_repo
        from utils.ui import (show_project_setup_instructions, show_project_card, 
                            show_architecture_folder_card)
        
        init_db()  # Ensure database exists
        
        st.title("Project Management")
        
        # Top-level tabs
        tab1, tab2, tab3 = st.tabs(["📚 Getting Started", "🆕 New Project", "📂 Existing Projects"])
        
        with tab1:
            show_project_setup_instructions()
            
        with tab2:
            st.header("Create New Project")
            
            # Project details form
            with st.form("new_project"):
                name = st.text_input("Project Name")
                description = st.text_area("Project Description")
                path = st.text_input("Project Path")
                
                col1, col2 = st.columns(2)
                with col1:
                    init_git = st.checkbox("Initialize Git Repository", value=True)
                with col2:
                    create_arch = st.checkbox("Generate Architecture", value=True)
                    
                if st.form_submit_button("Create Project"):
                    if name and path:
                        # Create project directory
                        try:
                            project_dir = Path(path)
                            project_dir.mkdir(parents=True, exist_ok=True)
                            
                            # Initialize git if requested
                            if init_git:
                                repo = init_git_repo(path)
                            
                            # Save to database
                            if save_project(name, str(project_dir), description, {}):
                                st.success("Project created successfully!")
                                if create_arch:
                                    st.info("Generating architecture files...")
                                    # Add architecture generation logic here
                        except Exception as e:
                            st.error(f"Failed to create project: {str(e)}")
                    else:
                        st.error("Please provide project name and path")
            
        with tab3:
            col1, col2 = st.columns([2,1])
            
            with col1:
                st.subheader("Recent Projects")
                projects = get_projects()
                for project in projects:
                    if show_project_card(project):
                        st.experimental_rerun()
                        
            with col2:
                st.subheader("Architecture Folders")
                base_path = "."  # Configure this path as needed
                arch_folders = scan_architecture_folders(base_path)
                for folder in arch_folders:
                    if show_architecture_folder_card(folder):
                        st.experimental_rerun()

    elif page == "Code":
        st.title("Code Editor")
        st.info("Code editing features coming soon...")

    elif page == "Tests":
        st.title("Test Runner")
        st.info("Test execution features coming soon...")

    elif page == "Settings":
        st.title("Settings")
        with st.form("settings_form"):
            st.checkbox("Dark Mode (Always On)", value=True, disabled=True)
            st.text_input("Git Path")
            st.text_input("API Key", type="password")
            st.form_submit_button("Save Settings")

if __name__ == "__main__":
    main()
# Configure Streamlit page - must be first Streamlit command
st.set_page_config(
    page_title="SPARC GUI",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

import sys
from pathlib import Path
# Add parent directory to Python path to find utils module
sys.path.append(str(Path(__file__).parent.parent))

import streamlit.components.v1 as components
import base64
import os
import git
import toml
from datetime import datetime

# Dark mode CSS
dark_mode_css = """
<style>
    /* Dark mode styles */
    .stApp {
        background-color: #1E1E1E;
        color: #FFFFFF;
    }
    .stSidebar {
        background-color: #252526;
    }
    .stButton>button {
        background-color: #2D2D2D;
        color: #FFFFFF;
        border: 1px solid #3E3E3E;
    }
    .stTextInput>div>div>input {
        background-color: #2D2D2D;
        color: #FFFFFF;
    }
    .stSelectbox>div>div>select {
        background-color: #2D2D2D;
        color: #FFFFFF;
    }
</style>
"""

# Inject dark mode CSS
st.markdown(dark_mode_css, unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables."""
    if 'project_path' not in st.session_state:
        st.session_state.project_path = None
    if 'components' not in st.session_state:
        st.session_state.components = []
    if 'git_repo' not in st.session_state:
        st.session_state.git_repo = None

def load_project(path: str) -> bool:
    """Load an existing SPARC project."""
    try:
        project_dir = Path(path)
        if not project_dir.exists():
            st.error(f"Project directory does not exist: {path}")
            return False
            
        # Check for architecture files
        arch_dir = project_dir / "architecture"
        if not arch_dir.exists() or not any(arch_dir.iterdir()):
            st.error("No architecture files found. Please initialize project first.")
            return False
            
        # Load guidance if exists
        guidance_file = project_dir / "guidance.toml"
        if guidance_file.exists():
            with open(guidance_file) as f:
                st.session_state.guidance = toml.load(f)
                
        # Setup git repo
        try:
            st.session_state.git_repo = git.Repo(path)
        except git.InvalidGitRepositoryError:
            st.warning("Git repository not initialized")
            
        st.session_state.project_path = path
        return True
        
    except Exception as e:
        st.error(f"Failed to load project: {str(e)}")
        return False

def show_project_status():
    """Display project status information."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Project Info")
        st.text(f"Location: {st.session_state.project_path}")
        
        # Show architecture files
        arch_dir = Path(st.session_state.project_path) / "architecture"
        if arch_dir.exists():
            files = list(arch_dir.glob("*.md"))
            st.write("Architecture Files:")
            for f in files:
                st.text(f"- {f.name}")
                
    with col2:
        st.subheader("Git Status")
        if st.session_state.git_repo:
            repo = st.session_state.git_repo
            st.text(f"Branch: {repo.active_branch.name}")
            st.text(f"Last Commit: {repo.head.commit.message}")
            
            # Show changes
            if repo.is_dirty():
                st.warning("Uncommitted Changes:")
                for item in repo.index.diff(None):
                    st.text(f"- Modified: {item.a_path}")
        else:
            st.warning("Git not initialized")

def show_components():
    """Display project components."""
    st.subheader("Components")
    
    # Read components from Architecture.md
    arch_file = Path(st.session_state.project_path) / "architecture" / "Architecture.md"
    if arch_file.exists():
        content = arch_file.read_text()
        
        # Extract components using simple parsing
        import re
        components = re.findall(r'## Component: (\w+)', content)
        
        if components:
            for comp in components:
                with st.expander(comp):
                    st.text("Status: Implemented")
                    if st.button(f"View {comp} Details", key=f"view_{comp}"):
                        st.session_state.selected_component = comp
        else:
            st.info("No components defined in Architecture.md")
    else:
        st.error("Architecture.md not found")

def main():
    # Sidebar
    with st.sidebar:
        st.title("SPARC GUI")
        st.markdown("---")
        page = st.radio(
            "Navigation",
            ["Project", "Code", "Tests", "Settings"]
        )

    # Main content
    if page == "Project":
        from utils.database import init_db, save_project, get_projects
        from utils.project import scan_architecture_folders, load_project_files, init_git_repo
        from utils.ui import (show_project_setup_instructions, show_project_card, 
                            show_architecture_folder_card)
        
        init_db()  # Ensure database exists
        
        st.title("Project Management")
        
        # Top-level tabs
        tab1, tab2, tab3 = st.tabs(["📚 Getting Started", "🆕 New Project", "📂 Existing Projects"])
        
        with tab1:
            show_project_setup_instructions()
            
        with tab2:
            st.header("Create New Project")
            
            # Project details form
            with st.form("new_project"):
                name = st.text_input("Project Name")
                description = st.text_area("Project Description")
                path = st.text_input("Project Path")
                
                col1, col2 = st.columns(2)
                with col1:
                    init_git = st.checkbox("Initialize Git Repository", value=True)
                with col2:
                    create_arch = st.checkbox("Generate Architecture", value=True)
                    
                if st.form_submit_button("Create Project"):
                    if name and path:
                        # Create project directory
                        try:
                            project_dir = Path(path)
                            project_dir.mkdir(parents=True, exist_ok=True)
                            
                            # Initialize git if requested
                            if init_git:
                                repo = init_git_repo(path)
                            
                            # Save to database
                            if save_project(name, str(project_dir), description, {}):
                                st.success("Project created successfully!")
                                if create_arch:
                                    st.info("Generating architecture files...")
                                    # Add architecture generation logic here
                        except Exception as e:
                            st.error(f"Failed to create project: {str(e)}")
                    else:
                        st.error("Please provide project name and path")
            
        with tab3:
            col1, col2 = st.columns([2,1])
            
            with col1:
                st.subheader("Recent Projects")
                projects = get_projects()
                for project in projects:
                    if show_project_card(project):
                        st.experimental_rerun()
                        
            with col2:
                st.subheader("Architecture Folders")
                base_path = "."  # Configure this path as needed
                arch_folders = scan_architecture_folders(base_path)
                for folder in arch_folders:
                    if show_architecture_folder_card(folder):
                        st.experimental_rerun()

    elif page == "Code":
        st.title("Code Editor")
        st.info("Code editing features coming soon...")

    elif page == "Tests":
        st.title("Test Runner")
        st.info("Test execution features coming soon...")

    elif page == "Settings":
        st.title("Settings")
        with st.form("settings_form"):
            st.checkbox("Dark Mode (Always On)", value=True, disabled=True)
            st.text_input("Git Path")
            st.text_input("API Key", type="password")
            st.form_submit_button("Save Settings")

if __name__ == "__main__":
    main()