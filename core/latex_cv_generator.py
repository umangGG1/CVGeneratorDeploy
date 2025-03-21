"""
LaTeX CV generator module for generating standard and visual CVs.
"""
import os
import subprocess
import sys
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from models.data_models import ExtractedData, AnalysisResults
from utils.logger import setup_logger
from utils.helpers import format_dates, format_list_as_bullet_string
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
        logger.info("LaTeXCVGenerator initialized")
    
    def _get_pdflatex_path(self) -> str:
        """Get the path to pdflatex executable."""
        if sys.platform == "win32":
            # Common MiKTeX installation paths on Windows
            possible_paths = [
                r"C:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe",
                r"C:\Program Files (x86)\MiKTeX\miktex\bin\x64\pdflatex.exe",
                r"C:\Program Files\MiKTeX\miktex\bin\pdflatex.exe",
                r"C:\Program Files (x86)\MiKTeX\miktex\bin\pdflatex.exe",
                r"C:\texlive\2023\bin\win32\pdflatex.exe",
                r"C:\texlive\2022\bin\win32\pdflatex.exe",
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    return path
            
            raise FileNotFoundError(
                "pdflatex not found. Please install MiKTeX from https://miktex.org/download "
                "or TeX Live from https://tug.org/texlive/windows.html"
            )
        else:
            return "pdflatex"  # On Unix-like systems, assume pdflatex is in PATH
    
    def _prepare_contact_info(self) -> str:
        """Prepare contact information string."""
        try:
            contact_info = self.extracted_data.personal_info.contact_info or {}
            contact_parts = []
            
            if "email" in contact_info and contact_info["email"]:
                contact_parts.append(contact_info["email"])
            
            if "phone" in contact_info and contact_info["phone"]:
                contact_parts.append(contact_info["phone"])
            
            if "location" in contact_info and contact_info["location"]:
                contact_parts.append(contact_info["location"])
            elif all(k in contact_info for k in ["city", "state", "zip"]):
                if contact_info["city"] and contact_info["state"] and contact_info["zip"]:
                    contact_parts.append(f"{contact_info['city']}, {contact_info['state']} {contact_info['zip']}")
            
            return " \\textbullet \\ ".join(contact_parts) if contact_parts else ""
        except Exception as e:
            logger.error(f"Error preparing contact info: {str(e)}", exc_info=True)
            return ""
    
    def _prepare_education(self) -> str:
        """Prepare education section content."""
        try:
            education_text = []
            for edu in self.analysis_results.education_formatted:
                lines = edu.strip().split('\n')
                if len(lines) > 1:
                    education_text.append(f"\\textbf{{{lines[1]}}} \\hfill {lines[0]}")
                else:
                    education_text.append(edu)
            return "\n\n".join(education_text)
        except Exception as e:
            logger.error(f"Error preparing education: {str(e)}", exc_info=True)
            return ""
    
    def _prepare_experience(self) -> str:
        """Prepare experience section content."""
        try:
            experience_text = []
            for exp in self.analysis_results.experience_highlights:
                company = exp.get("company", "")
                title = exp.get("title", "")
                dates = format_dates(exp.get("dates", ""))
                location = exp.get("location", "")
                achievements = exp.get("achievements", [])
                
                exp_text = f"\\textbf{{{company}}} \\hfill {location}\n"
                exp_text += f"\\textbf{{{title}}} \\hfill {dates}\n"
                
                if achievements:
                    exp_text += "\\begin{itemize}[noitemsep, topsep=0pt, partopsep=0pt, parsep=0pt]\n"
                    for achievement in achievements:
                        exp_text += f"    \\item {achievement}\n"
                    exp_text += "\\end{itemize}"
                
                experience_text.append(exp_text)
            return "\n\n".join(experience_text)
        except Exception as e:
            logger.error(f"Error preparing experience: {str(e)}", exc_info=True)
            return ""
    
    def _prepare_skills(self) -> str:
        """Prepare skills section content."""
        try:
            skills_text = []
            
            # Core skills
            if self.analysis_results.core_skills:
                skills_text.append("\\textbf{Core Skills:}")
                skills_text.append("\\begin{itemize}[noitemsep, topsep=0pt, partopsep=0pt, parsep=0pt]")
                for skill in self.analysis_results.core_skills:
                    skills_text.append(f"    \\item {skill}")
                skills_text.append("\\end{itemize}")
            
            # Competencies
            if self.analysis_results.competencies:
                skills_text.append("\\textbf{Competencies:}")
                skills_text.append("\\begin{itemize}[noitemsep, topsep=0pt, partopsep=0pt, parsep=0pt]")
                for comp in self.analysis_results.competencies:
                    skills_text.append(f"    \\item {comp}")
                skills_text.append("\\end{itemize}")
            
            return "\n\n".join(skills_text)
        except Exception as e:
            logger.error(f"Error preparing skills: {str(e)}", exc_info=True)
            return ""
    
    def _prepare_optional_section(self) -> str:
        """Prepare optional section content."""
        try:
            display_section = self.analysis_results.display_section
            if not display_section:
                return ""
            
            section_items = []
            if display_section == "languages":
                section_items = self.analysis_results.languages_formatted
                section_title = "Languages"
            elif display_section == "interests":
                section_items = self.analysis_results.interests_formatted
                section_title = "Interests"
            elif display_section == "systems":
                section_items = self.analysis_results.systems_formatted
                section_title = "Technical Systems"
            
            if not section_items:
                return ""
            
            section_text = [f"\\textbf{{{section_title}:}}"]
            section_text.append("\\begin{itemize}[noitemsep, topsep=0pt, partopsep=0pt, parsep=0pt]")
            for item in section_items:
                section_text.append(f"    \\item {item}")
            section_text.append("\\end{itemize}")
            
            return "\n".join(section_text)
        except Exception as e:
            logger.error(f"Error preparing optional section: {str(e)}", exc_info=True)
            return ""
    
    def _prepare_achievements(self) -> str:
        """Prepare career achievements section content."""
        try:
            if not self.analysis_results.achievement_metrics:
                return ""
            
            achievements_text = ["\\begin{itemize}[noitemsep, topsep=0pt, partopsep=0pt, parsep=0pt]"]
            for achievement in self.analysis_results.achievement_metrics:
                achievements_text.append(f"    \\item {achievement}")
            achievements_text.append("\\end{itemize}")
            
            return "\n".join(achievements_text)
        except Exception as e:
            logger.error(f"Error preparing achievements: {str(e)}", exc_info=True)
            return ""
    
    def _compile_latex(self, tex_file: Path) -> bool:
        """Compile LaTeX file to PDF."""
        try:
            pdflatex_path = self._get_pdflatex_path()
            
            # Run pdflatex twice to ensure proper compilation
            for _ in range(2):
                result = subprocess.run(
                    [pdflatex_path, "-interaction=nonstopmode", "-output-directory", str(self.output_dir), str(tex_file)],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    logger.error(f"LaTeX compilation error: {result.stderr}")
                    return False
            return True
        except FileNotFoundError as e:
            logger.error(f"LaTeX compiler not found: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error compiling LaTeX: {str(e)}", exc_info=True)
            return False
    
    def generate_standard_cv(self) -> str:
        """Generate standard CV in PDF format."""
        logger.info("Generating standard CV")
        
        try:
            # Read template
            template_path = self.templates_dir / "standard_cv.tex"
            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()
            
            # Prepare content
            content = template.replace("$name", self.extracted_data.personal_info.name or "Professional")
            content = content.replace("$contact_info", self._prepare_contact_info())
            content = content.replace("$education", self._prepare_education())
            content = content.replace("$experience", self._prepare_experience())
            content = content.replace("$skills", self._prepare_skills())
            content = content.replace("$optional_section", self._prepare_optional_section())
            
            # Save LaTeX file
            tex_file = self.output_dir / "standard_cv.tex"
            with open(tex_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Compile to PDF
            if self._compile_latex(tex_file):
                pdf_path = self.output_dir / "standard_cv.pdf"
                logger.info(f"Standard CV saved to {pdf_path}")
                return str(pdf_path)
            else:
                raise Exception("Failed to compile LaTeX file")
        except Exception as e:
            logger.error(f"Error generating standard CV: {str(e)}", exc_info=True)
            raise
    
    def generate_visual_cv(self) -> str:
        """Generate visual CV in PDF format."""
        logger.info("Generating visual CV")
        
        try:
            # Read template
            template_path = self.templates_dir / "visual_cv.tex"
            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()
            
            # Prepare content
            content = template.replace("$name", self.extracted_data.personal_info.name or "Professional")
            content = content.replace("$contact_info", self._prepare_contact_info())
            content = content.replace("$profile", self.analysis_results.summary_points.get("profile", ""))
            content = content.replace("$achievements", self._prepare_achievements())
            content = content.replace("$experience", self._prepare_experience())
            content = content.replace("$skills", self._prepare_skills())
            content = content.replace("$education", self._prepare_education())
            content = content.replace("$optional_section", self._prepare_optional_section())
            
            # Save LaTeX file
            tex_file = self.output_dir / "visual_cv.tex"
            with open(tex_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Compile to PDF
            if self._compile_latex(tex_file):
                pdf_path = self.output_dir / "visual_cv.pdf"
                logger.info(f"Visual CV saved to {pdf_path}")
                return str(pdf_path)
            else:
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