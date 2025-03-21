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
            for edu in self.analysis_results.education_formatted:
                lines = [escape_latex(line) for line in edu.strip().split("\n")]
                if len(lines) > 1:
                    education_text.append(f"\\textbf{{{lines[1]}}} \\hfill {lines[0]}")
                else:
                    education_text.append(lines[0])
            return "\n\n".join(education_text)
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

                exp_text = f"\\textbf{{{company}}} \\hfill {location}\n"
                exp_text += f"\\textbf{{{title}}} \\hfill {dates}\n"

                if achievements:
                    exp_text += "\\begin{itemize}[noitemsep, topsep=0pt, partopsep=0pt, parsep=0pt]\n"
                    exp_text += "\n".join([f"    \\item {a}" for a in achievements])
                    exp_text += "\n\\end{itemize}"

                experience_text.append(exp_text)
            return "\n\n".join(experience_text)
        except Exception as e:
            logger.error(f"Error preparing experience: {str(e)}", exc_info=True)
            return ""

    def _prepare_skills(self) -> str:
        """Prepare skills section content with LaTeX escaping."""
        try:
            skills_text = []

            if self.analysis_results.core_skills:
                skills_text.append("\\textbf{Core Skills:}")
                skills_text.append("\\begin{itemize}[noitemsep, topsep=0pt, partopsep=0pt, parsep=0pt]")
                skills_text.extend(
                    f"    \\item {escape_latex(skill)}"
                    for skill in self.analysis_results.core_skills
                )
                skills_text.append("\\end{itemize}")

            if self.analysis_results.competencies:
                skills_text.append("\\textbf{Competencies:}")
                skills_text.append("\\begin{itemize}[noitemsep, topsep=0pt, partopsep=0pt, parsep=0pt]")
                skills_text.extend(
                    f"    \\item {escape_latex(comp)}"
                    for comp in self.analysis_results.competencies
                )
                skills_text.append("\\end{itemize}")

            return "\n\n".join(skills_text)
        except Exception as e:
            logger.error(f"Error preparing skills: {str(e)}", exc_info=True)
            return ""

    def _prepare_optional_section(self) -> str:
        """Prepare optional section content with LaTeX escaping."""
        try:
            display_section = self.analysis_results.display_section
            if not display_section:
                return ""

            section_items = []
            section_title = ""
            if display_section == "languages":
                section_items = [escape_latex(l) for l in self.analysis_results.languages_formatted]
                section_title = "Languages"
            elif display_section == "interests":
                section_items = [escape_latex(i) for i in self.analysis_results.interests_formatted]
                section_title = "Interests"
            elif display_section == "systems":
                section_items = [escape_latex(s) for s in self.analysis_results.systems_formatted]
                section_title = "Technical Systems"

            if not section_items:
                return ""

            section_text = [f"\\textbf{{{section_title}:}}"]
            section_text.append("\\begin{itemize}[noitemsep, topsep=0pt, partopsep=0pt, parsep=0pt]")
            section_text.extend(f"    \\item {item}" for item in section_items)
            section_text.append("\\end{itemize}")
            
            return "\n".join(section_text)
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
                pdf_path = self.output_dir / "standard_cv.pdf"
                logger.info(f"Standard CV saved to {pdf_path}")
                return str(pdf_path)
            raise Exception("Failed to compile LaTeX file")
        except Exception as e:
            logger.error(f"Error generating standard CV: {str(e)}", exc_info=True)
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
                pdf_path = self.output_dir / "visual_cv.pdf"
                logger.info(f"Visual CV saved to {pdf_path}")
                return str(pdf_path)
            raise Exception("Failed to compile LaTeX file")
        except Exception as e:
            logger.error(f"Error generating visual CV: {str(e)}", exc_info=True)
            raise

    def generate_cvs(self) -> Tuple[str, str]:
        """Generate both standard and visual CVs in PDF format."""
        logger.info("Generating CVs")
        
        try:
            standard_cv_path = self.generate_standard_cv()
            visual_cv_path = self.generate_visual_cv()
            logger.info("CV generation complete")
            return standard_cv_path, visual_cv_path
        except Exception as e:
            logger.error(f"Error generating CVs: {str(e)}", exc_info=True)
            raise