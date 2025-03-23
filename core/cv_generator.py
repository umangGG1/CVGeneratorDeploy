"""
CV generator module for generating standard and visual CVs.
"""
import re
import os
from typing import Dict, List, Any, Optional, Tuple

import openai
from openai import OpenAI

from models.data_models import ExtractedData, AnalysisResults
from utils.logger import setup_logger
from utils.helpers import format_dates, format_list_as_bullet_string
from config.settings import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, OUTPUT_DIR

# Set up logger
logger = setup_logger(__name__)

# Configure OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


class CVGenerator:
    """Generates CV content using professional CV writing approaches"""
    
    def __init__(self, analysis_results: AnalysisResults, extracted_data: ExtractedData):
        self.analysis_results = analysis_results
        self.extracted_data = extracted_data
        self.standard_cv = ""
        self.visual_cv = ""
        logger.info("CVGenerator initialized")
    
    def generate_standard_cv(self) -> str:
        """
        Generate complete standard CV.
        
        Returns:
            String containing the standard CV content
        """
        logger.info("Generating standard CV")
        
        try:
            # Generate each component
            cv_components = []
            
            # 1. Generate headline
            headline = self._generate_headline()
            cv_components.append(headline)
            
            # 2. Generate summary section
            summary = self._generate_summary_section()
            cv_components.append(summary)
            
            # 3. Generate core skills and competencies
            skills = self._generate_skills_section()
            cv_components.append(skills)
            
            # 4. Generate work experience
            experience = self._generate_work_experience()
            cv_components.append(experience)
            
            # 5. Generate education
            education = self._generate_education_section()
            cv_components.append(education)
            
            # 6. Generate certifications and training
            certifications = self._generate_certifications_section()
            if certifications:
                cv_components.append(certifications)
            
            # 7. Generate optional section based on display_section flag
            display_section = self.analysis_results.display_section
            if display_section == "languages":
                languages = self._generate_languages_section()
                if languages:
                    cv_components.append(languages)
            elif display_section == "interests":
                interests = self._generate_interests_section()
                if interests:
                    cv_components.append(interests)
            elif display_section == "systems":
                systems = self._generate_systems_section()
                if systems:
                    cv_components.append(systems)
            
            # Combine all components, filtering out empty strings
            self.standard_cv = "\n\n".join([comp for comp in cv_components if comp])
            
            # Save to file
            output_path = os.path.join(OUTPUT_DIR, "standard_cv.md")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(self.standard_cv)
            logger.info(f"Standard CV saved to {output_path}")
            
            return self.standard_cv
        except Exception as e:
            logger.error(f"Error generating standard CV: {str(e)}", exc_info=True)
            raise
        
    def generate_visual_cv(self) -> str:
        """
        Generate complete visual CV based on standard CV.
        
        Returns:
            String containing the visual CV content
        """
        logger.info("Generating visual CV")
        
        try:
            # Ensure standard CV has been generated
            if not self.standard_cv:
                logger.info("Standard CV not found, generating it first")
                self.generate_standard_cv()
            
            visual_components = []
            
            # 1. Use same headline
            headline = self._extract_headline_from_standard_cv()
            visual_components.append(headline)
            
            # 2. Generate condensed profile
            profile = self._generate_condensed_profile()
            visual_components.append(profile)
            
            # 3. Generate career achievements section
            achievements = self._generate_career_achievements()
            visual_components.append(achievements)
            
            # 4. Generate condensed work experience
            work_exp = self._generate_condensed_work_experience()
            visual_components.append(work_exp)
            
            # 5. Generate core skills and competencies in visual format
            skills = self._generate_visual_skills_section()
            visual_components.append(skills)
            
            # 6. Add education, certifications, languages in condensed format
            additional = self._generate_additional_sections_condensed()
            visual_components.append(additional)
            
            # Combine all components
            self.visual_cv = "\n\n".join(visual_components)
            
            # Save to file
            output_path = os.path.join(OUTPUT_DIR, "visual_cv.md")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(self.visual_cv)
            logger.info(f"Visual CV saved to {output_path}")
            
            return self.visual_cv
        except Exception as e:
            logger.error(f"Error generating visual CV: {str(e)}", exc_info=True)
            raise
    
    def _generate_headline(self) -> str:
        """
        Generate headline section.
        
        Returns:
            Formatted headline section
        """
        logger.debug("Generating headline section")
        
        try:
            # Use name from extracted data
            name = self.extracted_data.personal_info.name or "Professional"
            
            # Get contact info
            contact_info = self.extracted_data.personal_info.contact_info or {}
            contact_parts = []
            
            # Add email if available
            if "email" in contact_info and contact_info["email"]:
                contact_parts.append(contact_info["email"])
            
            # Add phone if available
            if "phone" in contact_info and contact_info["phone"]:
                contact_parts.append(contact_info["phone"])
            
            # Add location if available
            if "location" in contact_info and contact_info["location"]:
                contact_parts.append(contact_info["location"])
            elif all(k in contact_info for k in ["city", "state", "zip"]):
                if contact_info["city"] and contact_info["state"] and contact_info["zip"]:
                    contact_parts.append(f"{contact_info['city']}, {contact_info['state']} {contact_info['zip']}")
            
            # Format contact info
            contact_text = " | ".join(contact_parts) if contact_parts else ""
            
            # Use top headline option if available
            if self.analysis_results.headline_options:
                headline = self.analysis_results.headline_options[0]  # Use top headline
                return f"# {name}\n{headline}\n{contact_text}"
            else:
                # Fallback to current role
                current_role = ""
                if self.extracted_data.experience:
                    current_role = self.extracted_data.experience[0].title
                return f"# {name}\n**{current_role}**\n{contact_text}"
        except Exception as e:
            logger.error(f"Error generating headline: {str(e)}", exc_info=True)
            return f"# Professional CV"
    
    def _generate_summary_section(self) -> str:
        """
        Generate summary section.
        
        Returns:
            Formatted summary section
        """
        logger.debug("Generating summary section")
        
        try:
            summary_points = self.analysis_results.summary_points
            
            summary = "## SUMMARY\n"
            summary += f"● **Profile:** {summary_points.get('profile', '')}\n\n"
            summary += f"● **Expertise:** {summary_points.get('expertise', '')}\n\n"
            summary += f"● **Education:** {summary_points.get('education', '')}\n\n"
            summary += f"● **Career Aspirations:** {summary_points.get('aspirations', '')}\n"
            
            return summary
        except Exception as e:
            logger.error(f"Error generating summary section: {str(e)}", exc_info=True)
            return "## SUMMARY\n● Professional with experience in industry.\n"
    
    def _generate_skills_section(self) -> str:
        """
        Generate skills section.
        
        Returns:
            Formatted skills section
        """
        logger.debug("Generating skills section")
        
        try:
            core_skills = self.analysis_results.core_skills
            competencies = self.analysis_results.competencies
            
            # Combine all skills with bullet separator
            all_skills = core_skills + competencies
            skills_text = format_list_as_bullet_string(all_skills)
            
            section = "## CORE SKILLS AND COMPETENCIES\n"
            section += skills_text
            
            return section
        except Exception as e:
            logger.error(f"Error generating skills section: {str(e)}", exc_info=True)
            return "## CORE SKILLS AND COMPETENCIES\nProfessional Skills • Technical Expertise • Leadership"
    
    def _generate_work_experience(self) -> str:
        """
        Generate work experience section.
        
        Returns:
            Formatted work experience section
        """
        logger.debug("Generating work experience section")
        
        try:
            experience_highlights = self.analysis_results.experience_highlights
            
            section = "## WORK EXPERIENCE\n\n"
            
            for exp in experience_highlights:
                title = exp.get("title", "")
                company = exp.get("company", "")
                dates = format_dates(exp.get("dates", ""))
                location = exp.get("location", "")
                achievements = exp.get("achievements", [])
                
                # Format according to professional template
                exp_text = f"**{dates} {title} at {company}**"
                if location:
                    exp_text += f" ({location})"
                exp_text += "\n"
                
                # Add achievements
                for achievement in achievements:
                    exp_text += f"● {achievement}\n"
                
                section += exp_text + "\n"
            
            return section
        except Exception as e:
            logger.error(f"Error generating work experience section: {str(e)}", exc_info=True)
            return "## WORK EXPERIENCE\n**Professional Experience**\n"
    
    def _generate_education_section(self) -> str:
        """
        Generate education section.
        
        Returns:
            Formatted education section
        """
        logger.debug("Generating education section")
        
        try:
            education_formatted = self.analysis_results.education_formatted
            
            section = "## EDUCATION\n"
            for edu in education_formatted:
                # Format each education entry
                parts = []
                if edu.get("degree"):
                    parts.append(edu["degree"])
                if edu.get("institution"):
                    parts.append(edu["institution"])
                if edu.get("dates"):
                    parts.append(edu["dates"])
                if edu.get("location"):
                    parts.append(edu["location"])
                
                if parts:
                    section += f"● {' | '.join(parts)}\n"
            
            return section
        except Exception as e:
            logger.error(f"Error generating education section: {str(e)}", exc_info=True)
            return "## EDUCATION\n"
    
    def _generate_certifications_section(self) -> str:
        """
        Generate certifications section.
        
        Returns:
            Formatted certifications section
        """
        logger.debug("Generating certifications section")
        
        try:
            certifications = self.analysis_results.certifications_formatted
            
            if not certifications:
                return ""  # Skip section if no certifications
                
            section = "## CERTIFICATIONS & TRAINING\n"
            for cert in certifications:
                section += f"● {cert}\n"
            
            return section
        except Exception as e:
            logger.error(f"Error generating certifications section: {str(e)}", exc_info=True)
            return ""  # Skip section on error
    
    def _generate_languages_section(self) -> str:
        """
        Generate languages section.
        
        Returns:
            Formatted languages section
        """
        logger.debug("Generating languages section")
        
        try:
            languages = self.analysis_results.languages_formatted
            
            if not languages:
                return ""  # Skip section if no languages
                
            section = "## LANGUAGES\n"
            if languages:
                section += format_list_as_bullet_string(languages)
            else:
                section += "English (Native)"  # Default
            
            return section
        except Exception as e:
            logger.error(f"Error generating languages section: {str(e)}", exc_info=True)
            return ""  # Skip section on error
        
    def _generate_interests_section(self) -> str:
        """
        Generate interests section.
        
        Returns:
            Formatted interests section
        """
        logger.debug("Generating interests section")
        
        try:
            interests = self.analysis_results.interests_formatted
            
            if not interests:
                return ""  # Skip section if no interests
                    
            section = "## INTERESTS\n"
            section += format_list_as_bullet_string(interests)
            
            return section
        except Exception as e:
            logger.error(f"Error generating interests section: {str(e)}", exc_info=True)
            return ""  # Skip section on error

    def _generate_systems_section(self) -> str:
        """
        Generate systems section.
        
        Returns:
            Formatted systems section
        """
        logger.debug("Generating systems section")
        
        try:
            systems = self.analysis_results.systems_formatted
            
            if not systems:
                return ""  # Skip section if no systems
                    
            section = "## SYSTEMS\n"
            section += format_list_as_bullet_string(systems)
            
            return section
        except Exception as e:
            logger.error(f"Error generating systems section: {str(e)}", exc_info=True)
            return ""  # Skip section on error
        
    def generate_pdf_cvs(self) -> tuple[str, str]:
        """
        Generate both standard and visual CVs in PDF format using LaTeX.
        
        Returns:
            Tuple of (standard_cv_pdf_path, visual_cv_pdf_path)
        """
        logger.info("Generating PDF CVs with LaTeX")
        
        try:
            # Import the LaTeX generator (import here to avoid circular imports)
            from core.latex_cv_generator import LaTeXCVGenerator
            
            # Create LaTeX generator
            latex_generator = LaTeXCVGenerator(self.analysis_results, self.extracted_data)
            
            # Generate both CVs
            standard_cv_path, visual_cv_path = latex_generator.generate_cvs()
            
            logger.info("PDF CV generation complete")
            return standard_cv_path, visual_cv_path
        except Exception as e:
            logger.error(f"Error generating PDF CVs: {str(e)}", exc_info=True)
            raise
    
    def _extract_headline_from_standard_cv(self) -> str:
        """
        Extract headline from standard CV.
        
        Returns:
            Extracted headline
        """
        logger.debug("Extracting headline from standard CV")
        
        try:
            lines = self.standard_cv.split('\n')
            if lines:
                # First line is the name heading
                if len(lines) > 1:
                    # Second line is the headline
                    return lines[0] + "\n" + lines[1]
                return lines[0]
            return "# Professional CV"
        except Exception as e:
            logger.error(f"Error extracting headline: {str(e)}", exc_info=True)
            return "# Professional CV"
    
    def _generate_condensed_profile(self) -> str:
        """
        Generate condensed profile for visual CV.
        
        Returns:
            Condensed profile
        """
        logger.debug("Generating condensed profile")
        
        try:
            summary_points = self.analysis_results.summary_points
            
            # Use OpenAI to condense the summary (75 words max)
            profile_text = summary_points.get('profile', '')
            expertise_text = summary_points.get('expertise', '')
            
            prompt = f"""
            Condense this professional summary into a single paragraph of no more than 75 words. Maintain the key points about experience, expertise, and value offered.
            
            Profile: {profile_text}
            
            Expertise: {expertise_text}
            
            The condensed profile should be impactful, professional, and highlight the most impressive aspects of the professional's background.
            """
            
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert CV writer specializing in concise professional profiles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            condensed_profile = response.choices[0].message.content.strip()
            return f"*{condensed_profile}*"
        except Exception as e:
            logger.error(f"Error generating condensed profile: {str(e)}", exc_info=True)
            return "*Experienced professional with a track record of success in the industry.*"
    
    def _generate_career_achievements(self) -> str:
        """
        Generate career achievements section for visual CV.
        
        Returns:
            Formatted career achievements section
        """
        logger.debug("Generating career achievements section")
        
        try:
            metrics = self.analysis_results.achievement_metrics
            
            if not metrics:
                return ""  # Skip section if no metrics
                
            section = "## Career Achievements\n"
            for metric in metrics:
                section += f"● {metric}\n"
            
            return section
        except Exception as e:
            logger.error(f"Error generating career achievements: {str(e)}", exc_info=True)
            return ""  # Skip section on error
    
    def _generate_condensed_work_experience(self) -> str:
        """Generate condensed work experience for visual CV.
        
        Returns:
            Formatted condensed work experience
        """
        logger.debug("Generating condensed work experience")
        
        try:
            experience_highlights = self.analysis_results.experience_highlights
            
            section = "## Work Experience\n\n"
            
            for exp in experience_highlights:
                title = exp.get("title", "")
                company = exp.get("company", "")
                dates = format_dates(exp.get("dates", ""))
                location = exp.get("location", "")
                achievements = exp.get("achievements", [])
                
                # Format company and title in visual format
                section += f"### {title}\n"
                section += f"**{company}**  \n"
                section += f"*{dates}*  \n"
                if location:
                    section += f"*{location}*\n\n"
                else:
                    section += "\n"
                
                # Convert achievements list to string first
                achievements_text = ''.join(['● ' + a + '\n' for a in achievements])
                
                # Use regular string concatenation instead of f-string with backslash
                prompt = (
                    "Condense these achievement bullets into a single paragraph of 50-60 words "
                    "that captures the most impressive aspects of this role:\n\n" +
                    achievements_text + "\n\n" +
                    "The paragraph should start with an impactful statement about the role "
                    "and then highlight 2-3 key achievements."
                )
                
                response = client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are an expert CV writer specializing in concise work descriptions."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1
                )
                
                condensed_description = response.choices[0].message.content.strip()
                section += f"{condensed_description}\n\n"
            
            return section
        except Exception as e:
            logger.error(f"Error generating condensed work experience: {str(e)}", exc_info=True)
            return "## Work Experience\n\nProfessional experience in the industry.\n"
    
    def _generate_visual_skills_section(self) -> str:
        """
        Generate visual skills section with two columns.
        
        Returns:
            Formatted skills section for visual CV
        """
        logger.debug("Generating visual skills section")
        
        try:
            core_skills = self.analysis_results.core_skills
            competencies = self.analysis_results.competencies
            
            # Limit to 9 skills in each category
            core_skills = core_skills[:9]
            competencies = competencies[:9]
            
            section = "## Core Skills\n"
            for skill in core_skills:
                section += f"● {skill}\n"
            
            section += "\n## Competencies\n"
            for comp in competencies:
                section += f"● {comp}\n"
            
            return section
        except Exception as e:
            logger.error(f"Error generating visual skills section: {str(e)}", exc_info=True)
            return "## Skills\n● Professional Skills\n● Technical Expertise\n● Leadership"
    
    def _generate_additional_sections_condensed(self) -> str:
        """
        Generate condensed additional sections for visual CV.
        
        Returns:
            Formatted additional sections for visual CV
        """
        logger.debug("Generating additional condensed sections")
        
        try:
            education = self.analysis_results.education_formatted
            certifications = self.analysis_results.certifications_formatted
            
            section = ""
            
            # Add education if available
            if education:
                section += "## Education\n"
                for edu in education:
                    section += f"**{edu}**  \n"
                section += "\n"
            
            # Add certifications if available
            if certifications:
                section += "## Certifications & Training\n"
                for cert in certifications:
                    section += f"● {cert}\n"
                section += "\n"
            
            # Add interests section if available
            interests = self.analysis_results.interests_formatted
            if interests:
                section += "## Interests\n"
                for interest in interests:
                    section += f"● {interest}\n"
                section += "\n"
            
            # Add one optional section based on display_section flag
            display_section = self.analysis_results.display_section
            if display_section == "languages":
                languages = self.analysis_results.languages_formatted
                if languages:
                    section += "## Languages\n"
                    for lang in languages:
                        section += f"● {lang}\n"
            elif display_section == "systems":
                systems = self.analysis_results.systems_formatted
                if systems:
                    section += "## Systems\n"
                    for system in systems:
                        section += f"● {system}\n"
            
            return section
        except Exception as e:
            logger.error(f"Error generating additional sections: {str(e)}", exc_info=True)
            return ""  # Skip sections on error