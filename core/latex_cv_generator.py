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
                r"C:\Users\umang\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe",
                "pdflatex.exe"  # Add a fallback for simpler path resolution
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
                # Split the education entry into lines if it's a string
                if isinstance(edu, str):
                    lines = [line.strip() for line in edu.strip().split("\n") if line.strip()]
                    # Format according to expected structure
                    if len(lines) > 1:
                        institution = escape_latex(lines[1])
                        degree = escape_latex(lines[0])
                        education_text.append(f"\\textbf{{{institution}}} \\hfill {degree}")
                    else:
                        education_text.append(escape_latex(edu))
                # If it's a dictionary, extract components directly
                elif isinstance(edu, dict):
                    institution = escape_latex(edu.get("institution", ""))
                    location = escape_latex(edu.get("location", ""))
                    degree = escape_latex(edu.get("degree", ""))
                    dates = escape_latex(edu.get("dates", ""))
                    
                    # Format institution and location on first line
                    if institution:
                        first_line = f"\\textbf{{{institution}}}"
                        if location:
                            first_line += f" \\hfill {location}"
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
                skills_text.append("\\textbf{Skills \\& COMPETENCIES:} " + ", ".join([escape_latex(skill) for skill in all_skills]))
            
            if self.analysis_results.languages_formatted:
                skills_text.append("\\textbf{Languages:} " + ", ".join([escape_latex(lang) for lang in self.analysis_results.languages_formatted]))
                
            if self.analysis_results.systems_formatted:
                skills_text.append("\\textbf{Technical Systems:} " + ", ".join([escape_latex(sys) for sys in self.analysis_results.systems_formatted]))
                
            return "\n\n".join(skills_text)
        except Exception as e:
            logger.error(f"Error preparing skills: {str(e)}", exc_info=True)
            return ""

    def _prepare_core_skills(self, max_items=9) -> str:
        """Prepare core skills for visual CV."""
        try:
            if not self.analysis_results.core_skills:
                return "\\cvitem{No core skills listed}"
                
            skills_text = []
            # Limit to max_items
            core_skills = self.analysis_results.core_skills[:max_items]
            for skill in core_skills:
                skills_text.append(f"\\cvitem{{{escape_latex(skill)}}}")
                
            return "\n  ".join(skills_text) if skills_text else "\\cvitem{No core skills listed}"
        except Exception as e:
            logger.error(f"Error preparing core skills: {str(e)}", exc_info=True)
            return "\\cvitem{No core skills listed}"
            
    def _prepare_competencies(self, max_items=9) -> str:
        """Prepare competencies for visual CV."""
        try:
            if not self.analysis_results.competencies:
                return "\\cvitem{No competencies listed}"
                
            competencies_text = []
            # Limit to max_items
            competencies = self.analysis_results.competencies[:max_items]
            for competency in competencies:
                competencies_text.append(f"\\cvitem{{{escape_latex(competency)}}}")
                
            return "\n  ".join(competencies_text) if competencies_text else "\\cvitem{No competencies listed}"
        except Exception as e:
            logger.error(f"Error preparing competencies: {str(e)}", exc_info=True)
            return "\\cvitem{No competencies listed}"
            
    def _prepare_career_achievements(self, max_items=8) -> str:
        """Prepare career achievements for visual CV."""
        try:
            if not self.analysis_results.achievement_metrics:
                return "\\cvitem{No career achievements listed}"
                
            achievements_text = []
            # Limit to max_items
            achievements = self.analysis_results.achievement_metrics[:max_items]
            for achievement in achievements:
                achievements_text.append(f"\\cvitem{{{escape_latex(achievement)}}}")
                
            return "\n  ".join(achievements_text) if achievements_text else "\\cvitem{No career achievements listed}"
        except Exception as e:
            logger.error(f"Error preparing career achievements: {str(e)}", exc_info=True)
            return "\\cvitem{No career achievements listed}"
            
    def _prepare_visual_experience(self) -> str:
        """Prepare experience entries for visual CV with condensed format."""
        try:
            experience_text = []
            for exp in self.analysis_results.experience_highlights:
                company = escape_latex(exp.get("company", ""))
                title = escape_latex(exp.get("title", ""))
                dates = format_dates(exp.get("dates", ""))
                achievements = [escape_latex(a) for a in exp.get("achievements", [])]
                
                if not achievements:
                    continue
                    
                # Create a summary paragraph from the first significant achievement
                summary = ""
                remaining_achievements = achievements
                
                # Find a suitable first achievement for the summary
                for achievement in achievements:
                    cleaned = achievement.replace("●", "").strip()
                    if len(cleaned.split()) >= 8:  # Check if it's substantial enough
                        summary = cleaned
                        remaining_achievements = [a for a in achievements if a != achievement]
                        break
                
                # If no suitable achievement found, create a generic summary
                if not summary:
                    summary = f"Led strategic initiatives and drove operational excellence as {title} at {company}, focusing on business growth and market expansion."
                
                # Format the experience entry
                entry = f"\\experienceentry{{{title}}}{{{company}}}{{{dates}}}{{"\
                       f"{summary}\n"
                
                # Add bullet points if there are remaining achievements
                if remaining_achievements:
                    entry += "\\begin{itemize}[noitemsep, topsep=2pt, partopsep=0pt, parsep=5pt, leftmargin=10pt]\n"
                    # Limit to 3 bullet points for visual balance
                    for achievement in remaining_achievements[:3]:
                        cleaned = achievement.replace("●", "").strip()
                        if cleaned:
                            entry += f"  \\item {cleaned}\n"
                    entry += "\\end{itemize}"
                
                entry += "}"
                experience_text.append(entry)
            
            # Limit to top 3-4 most recent experiences
            return "\n\n\\vspace{8pt}\n".join(experience_text[:3])
        except Exception as e:
            logger.error(f"Error preparing visual experience: {str(e)}", exc_info=True)
            return ""
            
    def _prepare_visual_education(self) -> str:
        """Prepare education entries for visual CV."""
        try:
            education_text = []
            
            for edu in self.analysis_results.education_formatted:
                # Handle string format (from the formatted data)
                if isinstance(edu, str):
                    lines = [line.strip() for line in edu.strip().split("\n") if line.strip()]
                    if len(lines) >= 2:
                        # Extract dates and degree from first line
                        dates_parts = lines[0].split()
                        dates = " ".join(dates_parts[:3]) if len(dates_parts) >= 3 else lines[0]
                        degree = " ".join(dates_parts[3:]) if len(dates_parts) >= 4 else ""
                        
                        # Get institution and location from second line
                        institution_parts = lines[1].split('(')
                        institution = institution_parts[0].strip()
                        location = institution_parts[1].rstrip(')') if len(institution_parts) > 1 else ""
                        
                        education_text.append(f"\\educationentry{{{escape_latex(dates)}}}{{{escape_latex(degree)}}}{{{escape_latex(institution)}}}{{{escape_latex(location)}}}")
                # Handle dictionary format
                elif isinstance(edu, dict):
                    dates = escape_latex(edu.get("dates", ""))
                    degree = escape_latex(edu.get("degree", ""))
                    institution = escape_latex(edu.get("institution", ""))
                    location = escape_latex(edu.get("location", ""))
                    
                    education_text.append(f"\\educationentry{{{dates}}}{{{degree}}}{{{institution}}}{{{location}}}")
            
            return "\n".join(education_text)
        except Exception as e:
            logger.error(f"Error preparing visual education: {str(e)}", exc_info=True)
            return ""
            
    def _prepare_visual_interests(self) -> str:
        """Prepare interests for visual CV."""
        try:
            if not self.analysis_results.interests_formatted:
                return "\\cvitem{No interests listed}"
                
            interests_text = []
            # Limit to 2-3 interests to save space
            interests = self.analysis_results.interests_formatted[:3]
            for interest in interests:
                interests_text.append(f"\\cvitem{{{escape_latex(interest)}}}")
                
            return "\n  ".join(interests_text) if interests_text else "\\cvitem{No interests listed}"
        except Exception as e:
            logger.error(f"Error preparing visual interests: {str(e)}", exc_info=True)
            return "\\cvitem{No interests listed}"
            
    def _prepare_visual_languages(self) -> str:
        """Prepare languages for visual CV."""
        try:
            if not self.analysis_results.languages_formatted:
                return "\\cvitem{No languages listed}"
                
            languages_text = []
            for lang in self.analysis_results.languages_formatted[:4]:  # Limit to 4 languages
                languages_text.append(f"\\cvitem{{{escape_latex(lang)}}}")
                    
            return "\n  ".join(languages_text) if languages_text else "\\cvitem{No languages listed}"
        except Exception as e:
            logger.error(f"Error preparing visual languages: {str(e)}", exc_info=True)
            return "\\cvitem{No languages listed}"

    def _prepare_visual_certifications(self) -> str:
        """Prepare certifications for visual CV."""
        try:
            if not self.analysis_results.certifications_formatted:
                return "\\cvitem{No certifications listed}"
                
            certifications_text = []
            for cert in self.analysis_results.certifications_formatted[:4]:  # Limit to 4 certifications
                certifications_text.append(f"\\cvitem{{{escape_latex(cert)}}}")
                    
            return "\n  ".join(certifications_text) if certifications_text else "\\cvitem{No certifications listed}"
        except Exception as e:
            logger.error(f"Error preparing certifications: {str(e)}", exc_info=True)
            return "\\cvitem{No certifications listed}"

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

    def _get_headline(self) -> str:
        """Get consistent headline for all CV formats."""
        try:
            # First try to get from headline options
            if self.analysis_results.headline_options and len(self.analysis_results.headline_options) > 0:
                return escape_latex(self.analysis_results.headline_options[0])
            
            # Fallback to constructing from experience
            headline_parts = []
            if self.analysis_results.experience_highlights:
                title = self.analysis_results.experience_highlights[0].get("title", "")
                if title:
                    headline_parts.append(escape_latex(title))
            
            # Add other components from core skills if available
            if self.analysis_results.core_skills and len(self.analysis_results.core_skills) >= 2:
                for skill in self.analysis_results.core_skills[:2]:
                    headline_parts.append(escape_latex(skill))
            
            # Final fallback
            if not headline_parts:
                return "Strategic Professional | Business Development | Operations Expert"
            
            return " | ".join(headline_parts[:3])
        except Exception as e:
            logger.error(f"Error generating headline: {str(e)}", exc_info=True)
            return "Strategic Professional | Business Development | Operations Expert"

    def _prepare_leadership(self) -> str:
        """Prepare leadership section content."""
        try:
            # For this section, we'll use achievement metrics as leadership examples
            if not self.analysis_results.achievement_metrics:
                return ""
                
            leadership_text = []
            leadership_text.append("\\textbf{Leadership \\& Achievements}")
            
            leadership_text.append("\\begin{itemize}[noitemsep, topsep=0pt, partopsep=0pt, parsep=0pt, leftmargin=12pt]")
            for achievement in self.analysis_results.achievement_metrics[:5]:  # Limit to top 5
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

    def _compile_latex(self, tex_file: Path) -> bool:
        """Compile LaTeX file to PDF with artifact cleanup."""
        try:
            pdflatex_path = self._get_pdflatex_path()

            # First run - this will handle most compilation
            result = subprocess.run(
                [pdflatex_path, "-interaction=nonstopmode", "-output-directory", str(self.output_dir), str(tex_file)],
                capture_output=True,
                text=True,
            )
            
            # Log the output for debugging
            if result.stderr:
                logger.error(f"LaTeX compilation error: {result.stderr}")
            
            # Second run - handles references and TOC if needed
            result = subprocess.run(
                [pdflatex_path, "-interaction=nonstopmode", "-output-directory", str(self.output_dir), str(tex_file)],
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                logger.error(f"LaTeX compilation failed on second run")
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
            headline = self._get_headline()
            
            content = (
                template.replace("$name", name)
                .replace("$headline", headline)
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

    def generate_harvard_cv(self) -> str:
        """Generate Harvard-style CV in PDF format."""
        logger.info("Generating Harvard-style CV")
        
        try:
            # Use the Harvard template content with improved formatting
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
        \\small $headline
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
            headline = self._get_headline()
            
            content = (
                harvard_template.replace("$name", name)
                .replace("$headline", headline)
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
                pdf_path = self.output_dir / "harvard_cv.pdf"
                logger.info(f"Harvard-style CV saved to {pdf_path}")
                return str(pdf_path)
            raise Exception("Failed to compile LaTeX file")
        except Exception as e:
            logger.error(f"Error generating Harvard-style CV: {str(e)}", exc_info=True)
            raise

    def generate_visual_cv(self) -> str:
        """Generate visual CV in PDF format using modern template."""
        logger.info("Generating visual CV")
        
        try:
            template_path = self.templates_dir / "visual_cv.tex"
            if not template_path.exists():
                raise FileNotFoundError(f"Visual CV template not found at {template_path}")

            with open(template_path, "r", encoding="utf-8") as f:
                visual_template = f.read()

            name = escape_latex(self.extracted_data.personal_info.name or "Professional")
            headline = self._get_headline()
            
            # Get profile from analysis results
            profile = self.analysis_results.summary_points.get("profile", "")
            
            # Prepare profile summary - limited to ~75 words
            profile_summary = escape_latex(profile)
            if len(profile_summary.split()) > 75:
                profile_summary = " ".join(profile_summary.split()[:75]) + "..."
            
            content = (
                visual_template.replace("$name", name)
                .replace("$headline", headline)
                .replace("$profile", profile_summary)
                .replace("$contact_info", self._prepare_contact_info())
                .replace("$career_achievements", self._prepare_career_achievements())
                .replace("$core_skills", self._prepare_core_skills())
                .replace("$competencies", self._prepare_competencies())
                .replace("$experience", self._prepare_visual_experience())
                .replace("$education", self._prepare_visual_education())
                .replace("$interests", self._prepare_visual_interests())
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
        """Generate standard and visual CVs in PDF format."""
        logger.info("Generating CVs")
        
        try:
            # Generate Harvard-style CV as the standard CV
            harvard_cv_path = self.generate_harvard_cv()
            standard_cv_path = self.generate_standard_cv()
            
            # Generate visual CV
            visual_cv_path = self.generate_visual_cv()
            
            logger.info("CV generation complete")
            return harvard_cv_path, standard_cv_path, visual_cv_path
        except Exception as e:
            logger.error(f"Error generating CVs: {str(e)}", exc_info=True)
            raise