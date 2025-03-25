import streamlit as st
import os
import tempfile
import subprocess
import time
from pathlib import Path
import base64
import sys
import shutil
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="CV Generator",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Create a temp directory to store uploaded files
def create_temp_directory():
    temp_dir = tempfile.mkdtemp()
    logger.info(f"Created temporary directory: {temp_dir}")
    return temp_dir

def save_uploaded_file(uploaded_file, temp_dir, filename):
    """Save an uploaded file and verify it was saved correctly"""
    if uploaded_file is None:
        return None
        
    file_path = os.path.join(temp_dir, filename)
    try:
        # Get the file content
        file_content = uploaded_file.getbuffer()
        file_size = len(file_content)
        
        # Save the file
        with open(file_path, "wb") as f:
            f.write(file_content)
            
        # Verify the file was saved
        if os.path.exists(file_path):
            saved_size = os.path.getsize(file_path)
            if saved_size == file_size:
                logger.info(f"Successfully saved {filename} ({saved_size} bytes)")
                return file_path
            else:
                logger.error(f"File size mismatch for {filename}. Expected: {file_size}, Got: {saved_size}")
                return None
        else:
            logger.error(f"Failed to save {filename}")
            return None
            
    except Exception as e:
        logger.error(f"Error saving {filename}: {str(e)}")
        return None

# Function to run the backend CV generator
def run_cv_generator(temp_dir, linkedin_path, cv_path, transcript_path, goals_path, photo_path):
    try:
        # Verify input files exist and have content
        for file_path in [linkedin_path, cv_path, transcript_path, goals_path, photo_path]:
            if file_path and os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                logger.info(f"Input file {os.path.basename(file_path)} exists with size: {file_size} bytes")
            else:
                logger.warning(f"Input file {file_path} does not exist or is empty")
        
        # Define output directories
        temp_output_dir = os.path.join(temp_dir, "output")
        os.makedirs(temp_output_dir, exist_ok=True)
        
        # Get the actual backend output directory path
        backend_output_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "output"
        )
        os.makedirs(backend_output_dir, exist_ok=True)
        
        # Get the backend working directory (where main.py is located)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Copy input files to the backend working directory
        backend_files = {}
        if linkedin_path:
            backend_files["linkedin"] = os.path.join(current_dir, "linkedin_profile.pdf")
            shutil.copy2(linkedin_path, backend_files["linkedin"])
            logger.info(f"Copied LinkedIn profile to: {backend_files['linkedin']}")
            
        if cv_path:
            backend_files["cv"] = os.path.join(current_dir, "current_cv.pdf")
            shutil.copy2(cv_path, backend_files["cv"])
            logger.info(f"Copied CV to: {backend_files['cv']}")
            
        if transcript_path:
            backend_files["transcript"] = os.path.join(current_dir, "meeting_transcript.pdf")
            shutil.copy2(transcript_path, backend_files["transcript"])
            logger.info(f"Copied transcript to: {backend_files['transcript']}")
            
        if goals_path:
            backend_files["goals"] = os.path.join(current_dir, "professional_goals.pdf")
            shutil.copy2(goals_path, backend_files["goals"])
            logger.info(f"Copied goals to: {backend_files['goals']}")
            
        if photo_path:
            backend_files["photo"] = os.path.join(current_dir, "profile_photo.jpg")
            shutil.copy2(photo_path, backend_files["photo"])
            logger.info(f"Copied profile photo to: {backend_files['photo']}")
        
        # Debug: Print the output directories
        logger.info(f"Temp output directory: {temp_output_dir}")
        logger.info(f"Backend output directory: {backend_output_dir}")
        
        # Build command to run CV generator
        python_executable = r"C:\Users\umang\OneDrive - iitr.ac.in\Desktop\Opguru\Kareem\cv_gen\Scripts\python.exe"
        
        # Get the full path to main.py
        main_py_path = os.path.join(current_dir, "main.py")
        
        if not os.path.exists(main_py_path):
            logger.error(f"main.py not found at: {main_py_path}")
            st.error("Error: main.py not found. Please check the installation.")
            return None, None
            
        cmd = [python_executable, main_py_path]
        
        # Add file paths as arguments if they exist
        if "linkedin" in backend_files:
            cmd.extend(["--linkedin", "linkedin_profile.pdf"])
        if "cv" in backend_files:
            cmd.extend(["--cv", "current_cv.pdf"])
        if "transcript" in backend_files:
            cmd.extend(["--transcript", "meeting_transcript.pdf"])
        if "goals" in backend_files:
            cmd.extend(["--goals", "professional_goals.pdf"])
        if "photo" in backend_files:
            cmd.extend(["--photo", "profile_photo.jpg"])
        
        # Use the output directory from the backend
        cmd.extend(["--output", "output"])
        
        # Set format to PDF only
        cmd.extend(["--format", "pdf"])
        
        # Debug: Show the command that will be executed
        logger.info(f"Executing command: {' '.join(cmd)}")
        st.code(" ".join(cmd), language="bash")
        
        # Create log placeholders
        log_placeholder = st.empty()
        
        # Run the CV generator
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=current_dir  # Set the working directory to where main.py is located
        )
        
        # Show a spinner while processing
        with st.spinner("Generating CV, please wait..."):
            stdout, stderr = process.communicate()
            
            # Show output
            if stdout:
                logger.info(f"Process stdout: {stdout}")
                log_placeholder.code(stdout, language="bash")
            if stderr:
                logger.error(f"Process stderr: {stderr}")
                st.error(f"Error output: {stderr}")
        
        if process.returncode != 0:
            logger.error(f"Process failed with return code: {process.returncode}")
            st.error(f"Error generating CV: {stderr}")
            return None, None
        
        # Look for PDFs in the backend output directory
        logger.info("Checking output directory for generated PDFs")
        pdf_files = []
        for file in os.listdir(backend_output_dir):
            logger.info(f"Found file in output: {file}")
            if file.endswith('.pdf'):
                pdf_files.append(file)
        
        # Check for Harvard CV and Visual CV PDFs in different naming patterns
        harvard_cv_path = None
        visual_cv_path = None
        possible_harvard_files = [
            "harvard_cv.pdf", 
            "harvard_cv_pdf.pdf", 
            "standard_cv.pdf", 
            "standard_cv_pdf.pdf"
        ]
        possible_visual_files = [
            "visual_cv.pdf",
            "visual_cv_pdf.pdf",
            "modern_cv.pdf",
            "modern_cv_pdf.pdf"
        ]
        
        for file_name in possible_harvard_files:
            if file_name in pdf_files:
                harvard_cv_path = os.path.join(backend_output_dir, file_name)
                logger.info(f"Found Harvard CV: {file_name}")
                st.success(f"Found Harvard CV: {file_name}")
                break
                
        for file_name in possible_visual_files:
            if file_name in pdf_files:
                visual_cv_path = os.path.join(backend_output_dir, file_name)
                logger.info(f"Found Visual CV: {file_name}")
                st.success(f"Found Visual CV: {file_name}")
                break
        
        # If no specific files found, use the first two PDFs
        if not harvard_cv_path and pdf_files:
            harvard_cv_path = os.path.join(backend_output_dir, pdf_files[0])
            logger.info(f"Using {pdf_files[0]} as the Harvard CV PDF")
            st.info(f"Using {pdf_files[0]} as the Harvard CV PDF")
            
        if not visual_cv_path and len(pdf_files) > 1:
            visual_cv_path = os.path.join(backend_output_dir, pdf_files[1])
            logger.info(f"Using {pdf_files[1]} as the Visual CV PDF")
            st.info(f"Using {pdf_files[1]} as the Visual CV PDF")
        
        # Display PDFs if they exist, regardless of backend completion status
        if harvard_cv_path and os.path.exists(harvard_cv_path):
            file_size = os.path.getsize(harvard_cv_path)
            logger.info(f"Final Harvard CV file size: {file_size} bytes")
            
            # Clean up the copied files
            for file_path in backend_files.values():
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"Cleaned up temporary file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file {file_path}: {str(e)}")
            
            return harvard_cv_path, visual_cv_path
        else:
            logger.error("Harvard CV PDF not found or doesn't exist")
            st.error("Harvard CV PDF not found or doesn't exist")
            return None, None
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        st.error(f"An error occurred: {str(e)}")
        st.code(traceback.format_exc(), language="python")
        return None, None

# Function to display PDF
def display_pdf(file_path):
    try:
        logger.info(f"Attempting to display PDF: {file_path}")
        
        # First try using st.pdf_viewer (new Streamlit method)
        try:
            with open(file_path, "rb") as f:
                pdf_bytes = f.read()
            st.pdf_viewer(pdf_bytes, width=700, height=1000)
            logger.info(f"Successfully displayed PDF using st.pdf_viewer: {file_path}")
            return
        except Exception as e:
            logger.warning(f"st.pdf_viewer failed, falling back to alternative method: {str(e)}")
        
        # Fallback method using base64 encoding
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        
        # Try using object tag first
        pdf_display = f"""
            <object data="data:application/pdf;base64,{base64_pdf}" type="application/pdf" width="700" height="1000">
                <embed src="data:application/pdf;base64,{base64_pdf}" type="application/pdf" width="700" height="1000" />
            </object>
        """
        
        st.markdown(pdf_display, unsafe_allow_html=True)
        logger.info(f"Successfully displayed PDF using fallback method: {file_path}")
    except Exception as e:
        logger.error(f"Error displaying PDF {file_path}: {str(e)}")
        st.error(f"Error displaying PDF: {str(e)}")
        # Add a direct download link as last resort
        st.markdown(get_download_link(file_path, os.path.basename(file_path)), unsafe_allow_html=True)
        st.info("If the PDF is not displaying properly, please use the download link above to view it.")

# Function to create download link for PDF
def get_download_link(file_path, filename):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Download {filename}</a>'
        return href
    except Exception as e:
        st.error(f"Error creating download link: {str(e)}")
        return ""

# Main application
def main():
    # App title and description
    st.title("Professional CV Generator")
    st.write("""
    Upload your documents to generate a professional Harvard-format CV.
    """)
    
    # File upload section
    st.header("Upload Documents")
    
    col1, col2 = st.columns(2)
    
    with col1:
        linkedin_file = st.file_uploader("LinkedIn Profile PDF", type=["pdf"], key="linkedin")
        transcript_file = st.file_uploader("Meeting Transcript PDF", type=["pdf"], key="transcript")
        photo_file = st.file_uploader("Profile Photo", type=["jpg", "jpeg", "png"], key="photo")
    
    with col2:
        cv_file = st.file_uploader("Current CV PDF", type=["pdf"], key="cv")
        goals_file = st.file_uploader("Professional Goals PDF", type=["pdf"], key="goals")
    
    # Show preview of uploaded photo if available
    if photo_file:
        st.image(photo_file, caption="Profile Photo Preview", width=200)
    
    # Generate button
    if st.button("Generate CV", type="primary"):
        # Check if at least one file was uploaded
        if not any([linkedin_file, cv_file, transcript_file, goals_file]):
            st.warning("Please upload at least one document to generate a CV.")
            return
        
        # Create temp directory
        temp_dir = create_temp_directory()
        st.write(f"Temporary directory created: {temp_dir}")
        
        # Save uploaded files to temp directory with verification
        file_paths = {}
        
        if linkedin_file:
            file_paths["linkedin"] = save_uploaded_file(linkedin_file, temp_dir, "linkedin_profile.pdf")
            if file_paths["linkedin"]:
                st.success("LinkedIn profile saved successfully")
            else:
                st.error("Failed to save LinkedIn profile")
        
        if cv_file:
            file_paths["cv"] = save_uploaded_file(cv_file, temp_dir, "current_cv.pdf")
            if file_paths["cv"]:
                st.success("Current CV saved successfully")
            else:
                st.error("Failed to save current CV")
        
        if transcript_file:
            file_paths["transcript"] = save_uploaded_file(transcript_file, temp_dir, "meeting_transcript.pdf")
            if file_paths["transcript"]:
                st.success("Meeting transcript saved successfully")
            else:
                st.error("Failed to save meeting transcript")
        
        if goals_file:
            file_paths["goals"] = save_uploaded_file(goals_file, temp_dir, "professional_goals.pdf")
            if file_paths["goals"]:
                st.success("Professional goals saved successfully")
            else:
                st.error("Failed to save professional goals")
                
        if photo_file:
            file_paths["photo"] = save_uploaded_file(photo_file, temp_dir, "profile_photo.jpg")
            if file_paths["photo"]:
                st.success("Profile photo saved successfully")
            else:
                st.error("Failed to save profile photo")
        
        # Check if any files were successfully saved
        if not any(file_paths.values()):
            st.error("No files were successfully saved. Please try uploading again.")
            return
        
        # Run CV generator
        harvard_cv_path, visual_cv_path = run_cv_generator(
            temp_dir,
            file_paths.get("linkedin"),
            file_paths.get("cv"),
            file_paths.get("transcript"),
            file_paths.get("goals"),
            file_paths.get("photo")
        )
        
        # Create tabs for different CVs if any PDFs were generated
        if harvard_cv_path or visual_cv_path:
            st.success("CVs generated successfully!")
            
            tab1, tab2 = st.tabs(["Harvard CV", "Visual CV"])
            
            with tab1:
                st.subheader("Harvard Format CV")
                if harvard_cv_path and os.path.exists(harvard_cv_path):
                    file_size = os.path.getsize(harvard_cv_path)
                    logger.info(f"Displaying Harvard CV - Size: {file_size} bytes")
                    st.markdown(get_download_link(harvard_cv_path, "Harvard_CV.pdf"), unsafe_allow_html=True)
                    display_pdf(harvard_cv_path)
                else:
                    st.info("Harvard CV was not generated or not found.")
                    logger.warning(f"Harvard CV path invalid: {harvard_cv_path}")
            
            with tab2:
                st.subheader("Visual Format CV")
                if visual_cv_path and os.path.exists(visual_cv_path):
                    file_size = os.path.getsize(visual_cv_path)
                    logger.info(f"Displaying Visual CV - Size: {file_size} bytes")
                    st.markdown(get_download_link(visual_cv_path, "Visual_CV.pdf"), unsafe_allow_html=True)
                    display_pdf(visual_cv_path)
                else:
                    st.info("Visual CV was not generated or not found.")
                    logger.warning(f"Visual CV path invalid: {visual_cv_path}")
        else:
            st.error("No CVs were generated. Please check the logs for details.")

# Run the app
if __name__ == "__main__":
    main()