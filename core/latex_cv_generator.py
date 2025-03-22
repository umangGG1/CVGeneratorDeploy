"""
LaTeX CV generator module for generating standard and visual CVs.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from models.data_models import ExtractedData, AnalysisResults
from utils.logger import setup_logger
from utils.helpers import (
    format_dates,
    format_list_as_bullet_string,
    escape_latex,
)
from config.settings import OUTPUT_DIR

# Set up logger
logger = setup_logger(__name__)


class LaTeXCVGenerator:
    """Generates LaTeX CVs using professional templates"""

    def __init__(self, analysis_results: AnalysisResults, extracted_data: ExtractedData):
        self.analysis_results = analysis_results
        self.extracted_data = extracted_data
        self.templates_dir = Path("templates")
        self.output_dir = Path(OUTPUT_DIR)
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("LaTeXCVGenerator initialized")

    def _get_pdflatex_path(self) -> str:
        """Get the path to pdflatex executable with validation."""
        if sys.platform == "win32":
            possible_paths = [
                r"C:\Users\umang\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe"
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    return str(path)

            raise FileNotFoundError(
                "pdflatex not found. Please install MiKTeX from https://miktex.org/download "
                "or TeX Live from https://tug.org/texlive/windows.html"
            )
        else:
            # Unix-like systems
            pdflatex_path = shutil.which("pdflatex")
            if not pdflatex_path:
                raise FileNotFoundError(
                    "pdflatex not found in PATH. Install with: "
                    "sudo apt-get install texlive-latex-base"
                )
            return pdflatex_path

    def _prepare_contact_info(self) -> str:
        """Prepare contact information string with LaTeX escaping."""
        try:
            contact_info = self.extracted_data.personal_info.contact_info or {}
            contact_parts = []
            
            if email := contact_info.get("email"):
                contact_parts.append(escape_latex(email))
            
            if phone := contact_info.get("phone"):
                contact_parts.append(escape_latex(phone))
            
            if location := contact_info.get("location"):
                contact_parts.append(escape_latex(location))
            elif all(k in contact_info for k in ("city", "state", "zip")):
                city = escape_latex(contact_info["city"])
                state = escape_latex(contact_info["state"])
                zip_code = escape_latex(contact_info["zip"])
                if city and state and zip_code:
                    contact_parts.append(f"{city}, {state} {zip_code}")
            
            if linkedin := contact_info.get("linkedin"):
                if not linkedin.startswith("https://"):
                    linkedin = "https://" + linkedin.lstrip("www.")
                # Use the actual URL as the display text
                display_url = linkedin.replace("https://", "").rstrip("/")
                contact_parts.append(f"\\href{{{escape_latex(linkedin)}}}{{{escape_latex(display_url)}}}")
            
            return " \\textbullet \\ ".join(contact_parts) if contact_parts else ""
        except Exception as e:
            logger.error(
                f"Error preparing contact info for {self.extracted_data.personal_info.name}: {str(e)}",
                exc_info=True,
            )
            return ""

    def _prepare_education(self) -> str:
        """Prepare education section content with LaTeX escaping."""
        try:
            education_text = []
            
            # Process each education entry from the formatted data
            for edu in self.analysis_results.education_formatted:
                # Extract components
                institution = escape_latex(edu.get("institution", ""))
                location = escape_latex(edu.get("location", ""))
                degree = escape_latex(edu.get("degree", ""))
                dates = escape_latex(edu.get("dates", ""))
                
                # Format institution and location on first line
                if institution:
                    first_line = f"\\textbf{{{institution}}}"
                    if location:
                        first_line += f" \\hfill {location}\n"
                    education_text.append(first_line)
                
                # Format degree and dates on second line
                if degree:
                    second_line = degree
                    if dates:
                        second_line += f" \\hfill {dates}"
                    education_text.append(second_line)
                
                # Add spacing between entries
                education_text.append("\\vspace{4pt}")
            
            return "\n".join(education_text)
        except Exception as e:
            logger.error(f"Error preparing education: {str(e)}", exc_info=True)
            return ""

    def _prepare_experience(self) -> str:
        """Prepare experience section content with LaTeX escaping."""
        try:
            experience_text = []
            for exp in self.analysis_results.experience_highlights:
                company = escape_latex(exp.get("company", ""))
                title = escape_latex(exp.get("title", ""))
                dates = format_dates(exp.get("dates", ""))
                location = escape_latex(exp.get("location", ""))
                achievements = [escape_latex(a) for a in exp.get("achievements", [])]

                # Format following the example provided in the images
                exp_text = f"\\textbf{{{company}}} \\hfill {location}\n"
                exp_text += f"\\textbf{{{title}}} \\hfill {dates}\n"

                if achievements:
                    exp_text += "\\begin{itemize}[noitemsep, topsep=0pt, partopsep=0pt, leftmargin=12pt]\n"
                    for achievement in achievements:
                        # Make sure each bullet begins with an action verb
                        if achievement.strip() and not achievement.strip().startswith("●"):
                            exp_text += f"    \\item {achievement}\n"
                        else:
                            # Remove the bullet point if it exists and replace with LaTeX itemize
                            cleaned_achievement = achievement.replace("●", "").strip()
                            exp_text += f"    \\item {cleaned_achievement}\n"
                    exp_text += "\\end{itemize}"

                experience_text.append(exp_text)
            return "\n\\vspace{6pt}\n".join(experience_text)
        except Exception as e:
            logger.error(f"Error preparing experience: {str(e)}", exc_info=True)
            return ""
        
    def _prepare_experience_harvard(self) -> str:
        """Prepare experience section content specifically for Harvard format."""
        try:
            experience_text = []
            for exp in self.analysis_results.experience_highlights:
                company = escape_latex(exp.get("company", ""))
                title = escape_latex(exp.get("title", ""))
                dates = format_dates(exp.get("dates", ""))
                location = escape_latex(exp.get("location", ""))
                achievements = [escape_latex(a) for a in exp.get("achievements", [])]

                # Organization and location formatted with right alignment
                exp_entry = f"\\textbf{{{company}}} \\hfill {location}\n\n"

                # Position title and dates formatted with right alignment
                exp_entry += f"\\textbf{{{title}}} \\hfill {dates}\n"

                # Add bullet points with Harvard formatting
                if achievements:
                    exp_entry += "\\begin{itemize}[noitemsep, topsep=0pt, partopsep=0pt, parsep=0pt]\n"
                    for ach in achievements:
                        cleaned_ach = ach.replace("●", "").strip()
                        if cleaned_ach:
                            exp_entry += f"    \\item {cleaned_ach}\n"
                    exp_entry += "\\end{itemize}"

                experience_text.append(exp_entry)

            # Separate entries with vertical space
            return "\n\\vspace{8pt}\n".join(experience_text)
        except Exception as e:
            logger.error(f"Error preparing Harvard experience: {str(e)}", exc_info=True)
            return ""



    def _prepare_skills(self) -> str:
        """Prepare skills section content with LaTeX escaping."""
        try:
            skills_text = []

            # Combine core skills and competencies
            all_skills = []
            if self.analysis_results.core_skills:
                all_skills.extend(self.analysis_results.core_skills)
            if self.analysis_results.competencies:
                all_skills.extend(self.analysis_results.competencies)
                
            if all_skills:
                # Format as a comma-separated list with formatting
                skills_text.append("\\textbf{Skills \\& Competencies:} " + ", ".join([escape_latex(skill) for skill in all_skills]))
            
            if self.analysis_results.languages_formatted:
                skills_text.append("\\textbf{Languages:} " + ", ".join([escape_latex(lang) for lang in self.analysis_results.languages_formatted]))
                
            if self.analysis_results.systems_formatted:
                skills_text.append("\\textbf{Technical Systems:} " + ", ".join([escape_latex(sys) for sys in self.analysis_results.systems_formatted]))
                
            return "\n\n".join(skills_text)
        except Exception as e:
            logger.error(f"Error preparing skills: {str(e)}", exc_info=True)
            return ""
            
    def _prepare_interests(self) -> str:
        """Prepare interests section content with LaTeX escaping."""
        try:
            if not self.analysis_results.interests_formatted:
                return ""
                
            interests_text = "\\textbf{Interests:} " + ", ".join([escape_latex(interest) for interest in self.analysis_results.interests_formatted])
            return interests_text
        except Exception as e:
            logger.error(f"Error preparing interests: {str(e)}", exc_info=True)
            return ""

    def _prepare_leadership(self) -> str:
        """Prepare leadership section content."""
        try:
            # For this section, we'll use achievement metrics as leadership examples
            if not self.analysis_results.achievement_metrics:
                return ""
                
            leadership_text = []
            leadership_text.append("\\textbf{Leadership Organization} \\hfill Professional Development")
            leadership_text.append("\\textbf{Leadership Role} \\hfill Ongoing")
            
            leadership_text.append("\\begin{itemize}[noitemsep, topsep=0pt, partopsep=0pt, parsep=0pt, leftmargin=12pt]")
            for achievement in self.analysis_results.achievement_metrics:
                leadership_text.append(f"    \\item {escape_latex(achievement)}")
            leadership_text.append("\\end{itemize}")
            
            return "\n".join(leadership_text)
        except Exception as e:
            logger.error(f"Error preparing leadership section: {str(e)}", exc_info=True)
            return ""

    def _prepare_optional_section(self) -> str:
        """Prepare optional section content with LaTeX escaping."""
        try:
            # Using leadership for optional section in standard template
            return self._prepare_leadership()
        except Exception as e:
            logger.error(f"Error preparing optional section: {str(e)}", exc_info=True)
            return ""

    def _prepare_achievements(self) -> str:
        """Prepare career achievements section content with LaTeX escaping."""
        try:
            if not self.analysis_results.achievement_metrics:
                return ""

            achievements = [escape_latex(a) for a in self.analysis_results.achievement_metrics]
            achievements_text = ["\\begin{itemize}[noitemsep, topsep=0pt, partopsep=0pt, parsep=0pt]"]
            achievements_text.extend(f"    \\item {a}" for a in achievements)
            achievements_text.append("\\end{itemize}")
            
            return "\n".join(achievements_text)
        except Exception as e:
            logger.error(f"Error preparing achievements: {str(e)}", exc_info=True)
            return ""

    def _compile_latex(self, tex_file: Path) -> bool:
        """Compile LaTeX file to PDF with artifact cleanup."""
        try:
            pdflatex_path = self._get_pdflatex_path()

            for _ in range(2):
                result = subprocess.run(
                    [pdflatex_path, "-interaction=nonstopmode", "-output-directory", str(self.output_dir), str(tex_file)],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    logger.error(f"LaTeX compilation error: {result.stderr}")
                    return False

            # Cleanup auxiliary files
            base_name = tex_file.stem
            for ext in [".aux", ".log", ".out", ".toc"]:
                file_path = self.output_dir / f"{base_name}{ext}"
                if file_path.exists():
                    file_path.unlink()

            return True
        except Exception as e:
            logger.error(f"Error compiling LaTeX: {str(e)}", exc_info=True)
            return False

    def generate_standard_cv(self) -> str:
        """Generate standard CV in PDF format."""
        logger.info("Generating standard CV")
        
        try:
            template_path = self.templates_dir / "standard_cv.tex"
            if not template_path.exists():
                raise FileNotFoundError(f"Standard CV template not found at {template_path}")

            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()

            name = escape_latex(self.extracted_data.personal_info.name or "Professional")
            
            content = (
                template.replace("$name", name)
                .replace("$contact_info", self._prepare_contact_info())
                .replace("$education", self._prepare_education())
                .replace("$experience", self._prepare_experience())
                .replace("$skills", self._prepare_skills())
                .replace("$optional_section", self._prepare_optional_section())
            )

            tex_file = self.output_dir / "standard_cv.tex"
            with open(tex_file, "w", encoding="utf-8") as f:
                f.write(content)

            if self._compile_latex(tex_file):
                pdf_path = self.output_dir / "standard_cv_pdf.pdf"
                logger.info(f"Standard CV saved to {pdf_path}")
                return str(pdf_path)
            raise Exception("Failed to compile LaTeX file")
        except Exception as e:
            logger.error(f"Error generating standard CV: {str(e)}", exc_info=True)
            raise

    def generate_harvard_cv(self) -> str:
        """Generate Harvard-style CV in PDF format."""
        logger.info("Generating Harvard-style CV")
        
        try:
            # Use the Harvard template content with improved formatting - omitting Leadership section
            harvard_template = """\\documentclass[11pt]{article}
    \\usepackage{graphicx} % Required for inserting images
    \\setlength{\\parindent}{0pt}
    \\usepackage{hyperref}
    \\usepackage{enumitem}
    \\usepackage{multicol}
    \\usepackage[utf8]{inputenc} 
    \\usepackage[T1]{fontenc}
    \\usepackage{helvet}
    \\renewcommand{\\familydefault}{\\sfdefault}
    \\usepackage{lipsum}
    \\usepackage[left=1.06cm,top=1.7cm,right=1.06cm,bottom=0.7cm]{geometry}

    % Improved formatting
    \\usepackage{titlesec}
    \\titleformat{\\section}{\\normalfont\\Large\\bfseries}{}{0em}{}[\\titlerule]
    \\titlespacing{\\section}{0pt}{12pt}{6pt}

    % Better font and spacing
    \\usepackage{setspace}
    \\setlength{\\parskip}{6pt}

    \\begin{document}
    \\begin{center}
        \\textbf{\\LARGE $name}\\\\ 
        \\hrulefill
    \\end{center}

    \\begin{center}
        $contact_info
    \\end{center}

    \\vspace{8pt}
    \\begin{center}
        \\textbf{\\large EDUCATION}
    \\end{center}
    $education

    \\vspace{16pt}
    \\begin{center}
        \\textbf{\\large EXPERIENCE}
    \\end{center}
    $experience

    \\vspace{12pt}
    \\begin{center}
        \\textbf{\\large SKILLS \\& COMPETENCIES}
    \\end{center}
    $skills

    \\vspace{12pt}
    \\begin{center}
        \\textbf{\\large INTERESTS}
    \\end{center}
    $interests
    \\end{document}"""

            name = escape_latex(self.extracted_data.personal_info.name or "Professional")
            
            content = (
                harvard_template.replace("$name", name)
                .replace("$contact_info", self._prepare_contact_info())
                .replace("$education", self._prepare_education())
                .replace("$experience", self._prepare_experience_harvard())
                .replace("$skills", self._prepare_skills())
                .replace("$interests", self._prepare_interests())
            )

            tex_file = self.output_dir / "harvard_cv.tex"
            with open(tex_file, "w", encoding="utf-8") as f:
                f.write(content)

            if self._compile_latex(tex_file):
                pdf_path = self.output_dir / "harvard_cv_pdf.pdf"
                logger.info(f"Harvard-style CV saved to {pdf_path}")
                return str(pdf_path)
            raise Exception("Failed to compile LaTeX file")
        except Exception as e:
            logger.error(f"Error generating Harvard-style CV: {str(e)}", exc_info=True)
            raise

    def generate_visual_cv(self) -> str:
        """Generate visual CV in PDF format."""
        logger.info("Generating visual CV")
        
        try:
            template_path = self.templates_dir / "visual_cv.tex"
            if not template_path.exists():
                raise FileNotFoundError(f"Visual CV template not found at {template_path}")

            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()

            name = escape_latex(self.extracted_data.personal_info.name or "Professional")
            profile = escape_latex(self.analysis_results.summary_points.get("profile", ""))
            
            content = (
                template.replace("$name", name)
                .replace("$contact_info", self._prepare_contact_info())
                .replace("$profile", profile)
                .replace("$achievements", self._prepare_achievements())
                .replace("$experience", self._prepare_experience())
                .replace("$skills", self._prepare_skills())
                .replace("$education", self._prepare_education())
                .replace("$optional_section", self._prepare_optional_section())
            )

            tex_file = self.output_dir / "visual_cv.tex"
            with open(tex_file, "w", encoding="utf-8") as f:
                f.write(content)

            if self._compile_latex(tex_file):
                pdf_path = self.output_dir / "visual_cv_pdf.pdf"
                logger.info(f"Visual CV saved to {pdf_path}")
                return str(pdf_path)
            raise Exception("Failed to compile LaTeX file")
        except Exception as e:
            logger.error(f"Error generating visual CV: {str(e)}", exc_info=True)
            raise

    def generate_cvs(self) -> Tuple[str, str, str]:
        """Generate standard, Harvard-style, and visual CVs in PDF format."""
        logger.info("Generating CVs")
        
        try:
            standard_cv_path = self.generate_standard_cv()
            harvard_cv_path = self.generate_harvard_cv()
            visual_cv_path = self.generate_visual_cv()
            logger.info("CV generation complete")
            return standard_cv_path, harvard_cv_path, visual_cv_path
        except Exception as e:
            logger.error(f"Error generating CVs: {str(e)}", exc_info=True)
            raise
            
    def generate_harvard_cv_only(self) -> str:
        """Generate only the Harvard-style CV in PDF format."""
        logger.info("Generating only Harvard-style CV")
        
        try:
            harvard_cv_path = self.generate_harvard_cv()
            logger.info("Harvard CV generation complete")
            return harvard_cv_path
        except Exception as e:
            logger.error(f"Error generating Harvard CV: {str(e)}", exc_info=True)
            raise