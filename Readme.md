# CV Generator with LLM-Powered Document Processing

A professional CV generation tool that processes LinkedIn profiles, existing CVs, meeting transcripts, and professional goals using LLMs (GPT-4o) to extract information and create well-structured, high-quality curriculum vitae documents.

## Features

- **LLM-Powered Extraction**: Uses GPT-4o to accurately extract information from documents instead of regex patterns
- **PDF Processing**: Directly processes PDF files using PyPDF2
- **Universal Document Handling**: Works with a wide variety of resume and profile formats
- **Dual CV Generation**: Creates both standard and visual CV formats
- **AI-Powered Content Enhancement**: Optimizes content for professional impact
- **Comprehensive Logging**: Detailed logging for debugging and tracking

## Project Structure

```
cv_generator/
│
├── main.py                     # Entry point of the application
├── requirements.txt            # Dependencies
├── .env                        # Environment variables (API keys, etc.)
├── README.md                   # Project documentation
│
├── config/
│   ├── __init__.py
│   └── settings.py             # Configuration settings
│
├── core/
│   ├── __init__.py
│   ├── document_processor.py   # LLM-based document extraction 
│   ├── content_analyzer.py     # Content analysis logic
│   ├── cv_generator.py         # CV generation logic
│   └── workflow.py             # Workflow orchestration
│
├── utils/
│   ├── __init__.py
│   ├── logger.py               # Logging configuration
│   └── helpers.py              # Helper functions
│
├── models/
│   ├── __init__.py
│   └── data_models.py          # Pydantic data models
│
└── output/                     # Generated CVs output directory
    └── .gitkeep
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/cv_generator.git
   cd cv_generator
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   OPENAI_MODEL=gpt-4o
   ```
5. **Install LaTeX**
   You need a LaTeX distribution installed:
   - **Windows:** Install [MiKTeX](https://miktex.org/download) or [TeX Live](https://tug.org/texlive/windows.html).
   - **Linux (Ubuntu/Debian):**
   ```bash
   sudo apt update && sudo apt install texlive-latex-base
   ```
   - **MacOS:** Install [MacTeX](https://tug.org/mactex/).

6. Ensure `pdflatex` is in **PATH**
   Run:
   ```bash
   pdflatex --version
   ```
   If it’s not found, manually add it to your system's PATH.

## Setup
   ### **1. Modify `possible_paths` in `_get_pdflatex_path`**
   If you're using Windows, update the `possible_paths` variable in `LaTeXCVGenerator._get_pdflatex_path()` with the correct path to `pdflatex.exe`:
   ```python
   possible_paths = [
      r"C:\\Path\\To\\Your\\MiKTeX\\miktex\\bin\\x64\\pdflatex.exe"
   ]
   ```
   Change the path accordingly based on your system configuration.

   ### **2. Create Required Directories**
   ```bash
   mkdir templates output
   ```
   Place your LaTeX templates (`standard_cv.tex`, `visual_cv.tex`) inside the `templates` folder.

## Usage

### Preparing Input Files

Place your PDF files in the project directory with the following default names:
- `linkedin_profile.pdf`: LinkedIn profile export
- `current_cv.pdf`: Current CV/resume
- `meeting_transcript.pdf`: Transcript from career coaching session
- `professional_goals.pdf`: Document outlining career goals

### Running the Application

```bash
python main.py
```

You can also specify custom file paths:
```bash
python main.py --linkedin path/to/linkedin.pdf --cv path/to/cv.pdf --transcript path/to/transcript.pdf --goals path/to/goals.pdf
```

### Output

The application generates two CV formats:

1. `standard_cv.md`: A comprehensive, detailed CV suitable for job applications
2. `visual_cv.md`: A concise, visually-focused CV ideal for networking and presentations

Both files are generated in Markdown format and can be found in the `output` directory.

## How It Works

1. **Document Processing**: PDF files are read and their content extracted
2. **LLM-Powered Information Extraction**: GPT-4o analyzes the document content and extracts structured information
3. **Content Analysis**: The extracted information is analyzed to identify key achievements, skills, etc.
4. **CV Generation**: Both standard and visual CVs are generated based on the analysis

## Advantages of Using LLMs for Document Processing

- **Format Flexibility**: Works with virtually any CV or profile format
- **Superior Information Extraction**: Intelligently identifies achievements, skills, and other key information
- **Context Understanding**: Comprehends the relevance and importance of different information
- **Adaptability**: No need to update regex patterns when document formats change

## Dependencies

- Python 3.8+
- OpenAI API
- PyPDF2
- python-dotenv
- pandas
- pydantic

See `requirements.txt` for all dependencies.

## License

[MIT License](LICENSE)