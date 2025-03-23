"""
Simplified PDF CV generator using FPDF for Harvard template format.
"""
import os
import re
from typing import Dict, Any, List, Optional
from fpdf import FPDF

from models.data_models import ExtractedData, AnalysisResults
from utils.logger import setup_logger
from config.settings import OUTPUT_DIR

# Set up logger
logger = setup_logger(__name__, "pdf_cv_generator.log")

class PDFCVGenerator:
    """Generates PDF CVs using the Harvard template format with FPDF"""
    
    def __init__(self, analysis_results: AnalysisResults, extracted_data: ExtractedData):
        self.analysis_results = analysis_results
        self.extracted_data = extracted_data
        self.bullet_char = "-"  # Use simple hyphen instead of bullet point
        logger.info("PDFCVGenerator initialized")
    
    def _prepare_contact_info(self) -> str:
        """
        Prepare contact information string for the header.
        
        Returns:
            Formatted contact info string
        """
        contact_parts = []
        
        try:
            # Use personal_info.contact_info
            contact_info = self.extracted_data.personal_info.contact_info or {}
            
            # Add address if available
            address_parts = []
            if "address" in contact_info and contact_info["address"]:
                address_parts.append(str(contact_info["address"]))
            
            if "city" in contact_info and "state" in contact_info and "zip" in contact_info:
                if contact_info["city"] and contact_info["state"] and contact_info["zip"]:
                    address_parts.append(f"{contact_info['city']}, {contact_info['state']} {contact_info['zip']}")
            elif "location" in contact_info and contact_info["location"]:
                address_parts.append(str(contact_info["location"]))
            
            # Only append joined address parts if there are valid parts
            if address_parts:
                valid_address_parts = [part for part in address_parts if part]
                if valid_address_parts:
                    contact_parts.append(" | ".join(valid_address_parts))  # Use pipe instead of bullet
            
            # Add email if available
            if "email" in contact_info and contact_info["email"]:
                contact_parts.append(str(contact_info["email"]))
            
            # Add phone if available
            if "phone" in contact_info and contact_info["phone"]:
                contact_parts.append(str(contact_info["phone"]))
            
            # Add LinkedIn if available
            if "linkedin" in contact_info and contact_info["linkedin"]:
                linkedin = contact_info["linkedin"]
                if not linkedin.startswith("https://"):
                    linkedin = "https://" + linkedin.lstrip("www.")
                contact_parts.append(linkedin)
            
            # If no specific contact info, try to extract from location
            if not contact_parts and "location" in contact_info and contact_info["location"]:
                contact_parts.append(str(contact_info["location"]))
            
            # If still no contact info, add a placeholder
            if not contact_parts:
                return self.extracted_data.personal_info.name or "Contact information available upon request"
            
            # Join all parts with pipes
            return " | ".join(contact_parts)  # Use pipe instead of bullet
        except Exception as e:
            logger.error(f"Error preparing contact info: {str(e)}", exc_info=True)
            # Return a safe fallback
            return self.extracted_data.personal_info.name or "Contact information available upon request"
    
    def _safe_achievement_render(self, pdf, achievement, indent=5):
        """Safely render an achievement with proper indentation and error handling"""
        try:
            if not achievement or len(achievement.strip()) == 0:
                return  # Skip empty achievements
                
            pdf.cell(indent, 7, self.bullet_char)
            remaining_width = pdf.w - pdf.l_margin - pdf.r_margin - indent
            # Make sure we have at least 10mm of width
            if remaining_width < 10:
                remaining_width = 150  # Default to a reasonable width
                
            # Break long achievements into multiple lines manually if needed
            if len(achievement) > 100:
                words = achievement.split()
                lines = []
                current_line = ""
                
                for word in words:
                    if len(current_line + " " + word) <= 80:  # Limit line length
                        current_line += (" " + word if current_line else word)
                    else:
                        lines.append(current_line)
                        current_line = word
                
                if current_line:
                    lines.append(current_line)
                
                for i, line in enumerate(lines):
                    if i == 0:
                        pdf.multi_cell(remaining_width, 7, line)
                    else:
                        pdf.cell(indent, 7, "")
                        pdf.multi_cell(remaining_width, 7, line)
            else:
                pdf.multi_cell(remaining_width, 7, achievement)
                
        except Exception as e:
            logger.error(f"Error rendering achievement: {str(e)}", exc_info=True)
            # Try a simpler approach
            try:
                pdf.ln()
                pdf.cell(indent, 7, "-")
                pdf.cell(0, 7, "Achievement details", ln=True)
            except:
                pdf.ln()  # Just move to next line if all else fails
    
    def generate_standard_cv_pdf(self) -> str:
        """
        Generate standard CV in PDF format.
        
        Returns:
            Path to the generated PDF file
        """
        logger.info("Generating standard CV PDF")
        
        try:
            # Create PDF object with wider margins for safety
            pdf = FPDF(orientation='P', unit='mm', format='A4')
            pdf.set_margins(15, 15, 15)  # left, top, right margins
            pdf.add_page()
            
            # Set font
            pdf.set_font("Times", size=12)
            
            # Add header
            name = self.extracted_data.personal_info.name
            contact_info = self._prepare_contact_info()
            
            pdf.set_font("Times", 'B', 14)
            pdf.cell(0, 10, name, ln=True, align='C')
            pdf.set_font("Times", '', 10)
            pdf.cell(0, 5, contact_info, ln=True, align='C')
            pdf.ln(5)
            
            # Education Section
            pdf.set_font("Times", 'B', 12)
            pdf.cell(0, 10, "EDUCATION", ln=True)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(2)
            pdf.set_font("Times", '', 11)
            
            try:
                for edu in self.analysis_results.education_formatted:
                    # Format institution and location on first line
                    if edu.get("institution"):
                        pdf.set_font("Times", 'B', 11)
                        first_line = edu["institution"]
                        if edu.get("location"):
                            first_line += f" | {edu['location']}"
                        pdf.cell(0, 7, first_line, ln=True)
                    
                    # Format degree and dates on second line
                    if edu.get("degree"):
                        pdf.set_font("Times", '', 11)
                        second_line = edu["degree"]
                        if edu.get("dates"):
                            second_line += f" | {edu['dates']}"
                        pdf.cell(0, 7, second_line, ln=True)
                    
                    pdf.ln(2)
            except Exception as e:
                logger.error(f"Error rendering education section: {str(e)}", exc_info=True)
                pdf.multi_cell(0, 7, "Education information not available")
                pdf.ln(2)
            
            # Experience Section
            pdf.set_font("Times", 'B', 12)
            pdf.cell(0, 10, "EXPERIENCE", ln=True)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(2)
            
            # Limited to top 6 experiences
            experiences = self.analysis_results.experience_highlights[:6] if self.analysis_results.experience_highlights else []
            
            for exp in experiences:
                try:
                    company = exp.get("company", "")
                    title = exp.get("title", "")
                    dates = exp.get("dates", "")
                    achievements = exp.get("achievements", [])
                    
                    # Company
                    pdf.set_font("Times", 'B', 11)
                    pdf.cell(0, 7, company, ln=True)
                    
                    # Title and date
                    pdf.set_font("Times", 'B', 11)
                    title_width = 130
                    pdf.cell(title_width, 7, title)
                    pdf.cell(0, 7, dates, ln=True, align='R')
                    
                    # Achievements
                    pdf.set_font("Times", '', 11)
                    for achievement in achievements:
                        if achievement and isinstance(achievement, str):
                            self._safe_achievement_render(pdf, achievement)
                    
                    pdf.ln(3)
                except Exception as e:
                    logger.error(f"Error rendering experience item: {str(e)}", exc_info=True)
                    pdf.ln()
                    continue
            
            # Skills Section
            pdf.set_font("Times", 'B', 12)
            pdf.cell(0, 10, "SKILLS & COMPETENCIES", ln=True)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(2)
            pdf.set_font("Times", '', 11)
            
            # Process skills
            skills = []
            
            # Handle core skills
            for skill in self.analysis_results.core_skills:
                if not skill:
                    continue
                    
                if isinstance(skill, str):
                    # Check if it's a multiline string with bullet points
                    if "\n" in skill and ("-" in skill or "•" in skill):
                        # Extract individual skills from the multiline string
                        for line in skill.split("\n"):
                            clean_skill = line.strip().lstrip("- •")
                            if clean_skill:
                                skills.append(clean_skill)
                    else:
                        skills.append(skill)
                elif isinstance(skill, list):
                    for s in skill:
                        if s:
                            skills.append(s)
            
            # Handle competencies
            for comp in self.analysis_results.competencies:
                if not comp:
                    continue
                    
                if isinstance(comp, str):
                    # Check if it's a multiline string with bullet points
                    if "\n" in comp and ("-" in comp or "•" in comp):
                        # Extract individual competencies from the multiline string
                        for line in comp.split("\n"):
                            clean_comp = line.strip().lstrip("- •")
                            if clean_comp:
                                skills.append(clean_comp)
                    else:
                        skills.append(comp)
                elif isinstance(comp, list):
                    for c in comp:
                        if c:
                            skills.append(c)
            
            # Ensure we have some skills to display
            if not skills:
                pdf.multi_cell(0, 7, "Skills information not available")
                pdf.ln()
            else:
                # Print skills in a simple list
                for skill in skills:
                    if skill and len(skill.strip()) > 0:
                        pdf.cell(5, 7, self.bullet_char)
                        pdf.cell(0, 7, skill, ln=True)
            
            # Optional Section (Languages, Interests, or Systems)
            display_section = self.analysis_results.display_section
            section_items = []
            
            if display_section == "languages":
                section_title = "LANGUAGES"
                section_items = self.analysis_results.languages_formatted
            elif display_section == "interests":
                section_title = "INTERESTS"
                section_items = self.analysis_results.interests_formatted
            elif display_section == "systems":
                section_title = "TECHNICAL SYSTEMS"
                section_items = self.analysis_results.systems_formatted
            
            if display_section and section_items:
                pdf.ln(3)
                pdf.set_font("Times", 'B', 12)
                pdf.cell(0, 10, section_title, ln=True)
                pdf.line(15, pdf.get_y(), 195, pdf.get_y())
                pdf.ln(2)
                pdf.set_font("Times", '', 11)
                
                # Print items as a simple list
                for item in section_items:
                    if item and len(item.strip()) > 0:
                        pdf.cell(5, 7, self.bullet_char)
                        pdf.cell(0, 7, item, ln=True)
            
            # Save PDF
            output_path = os.path.join(OUTPUT_DIR, "standard_cv.pdf")
            pdf.output(output_path)
            
            logger.info(f"Standard CV PDF saved to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error generating standard CV PDF: {str(e)}", exc_info=True)
            raise
    
    def generate_visual_cv_pdf(self) -> str:
        """
        Generate visual CV in PDF format.
        
        Returns:
            Path to the generated PDF file
        """
        logger.info("Generating visual CV PDF")
        
        try:
            # Create PDF object with wider margins for safety
            pdf = FPDF(orientation='P', unit='mm', format='A4')
            pdf.set_margins(15, 15, 15)  # left, top, right margins
            pdf.add_page()
            
            # Set font
            pdf.set_font("Times", size=12)
            
            # Add header
            name = self.extracted_data.personal_info.name
            contact_info = self._prepare_contact_info()
            
            pdf.set_font("Times", 'B', 14)
            pdf.cell(0, 10, name, ln=True, align='C')
            pdf.set_font("Times", '', 10)
            pdf.cell(0, 5, contact_info, ln=True, align='C')
            pdf.ln(5)
            
            # Profile section
            profile = self.analysis_results.summary_points.get("profile", "")
            if profile:
                pdf.set_font("Times", 'I', 11)
                pdf.multi_cell(0, 6, profile)
                pdf.ln(5)
            
            # Career Achievements
            pdf.set_font("Times", 'B', 12)
            pdf.cell(0, 10, "CAREER ACHIEVEMENTS", ln=True)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(2)
            pdf.set_font("Times", '', 11)
            
            if self.analysis_results.achievement_metrics:
                for achievement in self.analysis_results.achievement_metrics:
                    if achievement:
                        self._safe_achievement_render(pdf, achievement)
            else:
                pdf.multi_cell(0, 7, "Career achievement information not available")
            
            pdf.ln(3)
            
            # Experience Section (Condensed)
            pdf.set_font("Times", 'B', 12)
            pdf.cell(0, 10, "EXPERIENCE", ln=True)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(2)
            
            # Limited to top 4 experiences for the visual CV
            experiences = self.analysis_results.experience_highlights[:4] if self.analysis_results.experience_highlights else []
            
            for exp in experiences:
                try:
                    company = exp.get("company", "")
                    title = exp.get("title", "")
                    dates = exp.get("dates", "")
                    achievements = exp.get("achievements", [])
                    
                    # Company
                    pdf.set_font("Times", 'B', 11)
                    pdf.cell(0, 7, company, ln=True)
                    
                    # Title and date
                    pdf.set_font("Times", 'B', 11)
                    title_width = 130
                    pdf.cell(title_width, 7, title)
                    pdf.cell(0, 7, dates, ln=True, align='R')
                    
                    # Achievements (only first 2-3 for visual CV)
                    pdf.set_font("Times", '', 11)
                    for achievement in achievements[:3]:
                        if achievement and isinstance(achievement, str):
                            self._safe_achievement_render(pdf, achievement)
                    
                    pdf.ln(3)
                except Exception as e:
                    logger.error(f"Error rendering experience item in visual CV: {str(e)}", exc_info=True)
                    pdf.ln()
                    continue
            
            # Skills Section
            pdf.set_font("Times", 'B', 12)
            pdf.cell(0, 10, "SKILLS & COMPETENCIES", ln=True)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(2)
            pdf.set_font("Times", '', 11)
            
            # Process skills
            core_skills = []
            competencies = []
            
            # Handle core skills
            for skill in self.analysis_results.core_skills:
                if not skill:
                    continue
                    
                if isinstance(skill, str):
                    # Check if it's a multiline string with bullet points
                    if "\n" in skill and ("-" in skill or "•" in skill):
                        # Extract individual skills
                        for line in skill.split("\n"):
                            clean_skill = line.strip().lstrip("- •")
                            if clean_skill:
                                core_skills.append(clean_skill)
                    else:
                        core_skills.append(skill)
                elif isinstance(skill, list):
                    for s in skill:
                        if s:
                            core_skills.append(s)
            
            # Handle competencies
            for comp in self.analysis_results.competencies:
                if not comp:
                    continue
                    
                if isinstance(comp, str):
                    # Check if it's a multiline string with bullet points
                    if "\n" in comp and ("-" in comp or "•" in comp):
                        # Extract individual competencies
                        for line in comp.split("\n"):
                            clean_comp = line.strip().lstrip("- •")
                            if clean_comp:
                                competencies.append(clean_comp)
                    else:
                        competencies.append(comp)
                elif isinstance(comp, list):
                    for c in comp:
                        if c:
                            competencies.append(c)
            
            # Ensure we have some skills to display
            if not core_skills and not competencies:
                pdf.multi_cell(0, 7, "Skills information not available")
                pdf.ln()
            else:
                # Print skills as two sections
                pdf.set_font("Times", 'B', 11)
                pdf.cell(0, 7, "Core Skills:", ln=True)
                pdf.set_font("Times", '', 11)
                
                for skill in core_skills:
                    if skill and len(skill.strip()) > 0:
                        pdf.cell(5, 7, self.bullet_char)
                        pdf.cell(0, 7, skill, ln=True)
                
                pdf.ln(2)
                pdf.set_font("Times", 'B', 11)
                pdf.cell(0, 7, "Competencies:", ln=True)
                pdf.set_font("Times", '', 11)
                
                for comp in competencies:
                    if comp and len(comp.strip()) > 0:
                        pdf.cell(5, 7, self.bullet_char)
                        pdf.cell(0, 7, comp, ln=True)
            
            # Education Section (Condensed)
            pdf.ln(3)
            pdf.set_font("Times", 'B', 12)
            pdf.cell(0, 10, "EDUCATION", ln=True)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(2)
            pdf.set_font("Times", '', 11)
            
            try:
                for edu in self.analysis_results.education_formatted[:2]:  # Limit to top 2 educations
                    # Format institution and location on first line
                    if edu.get("institution"):
                        pdf.set_font("Times", 'B', 11)
                        first_line = edu["institution"]
                        if edu.get("location"):
                            first_line += f" | {edu['location']}"
                        pdf.cell(0, 7, first_line, ln=True)
                    
                    # Format degree and dates on second line
                    if edu.get("degree"):
                        pdf.set_font("Times", '', 11)
                        second_line = edu["degree"]
                        if edu.get("dates"):
                            second_line += f" | {edu['dates']}"
                        pdf.cell(0, 7, second_line, ln=True)
                    
                    pdf.ln(2)
            except Exception as e:
                logger.error(f"Error rendering education section in visual CV: {str(e)}", exc_info=True)
                pdf.multi_cell(0, 7, "Education information not available")
                pdf.ln(2)
            
            # Optional Section (Languages, Interests, or Systems)
            display_section = self.analysis_results.display_section
            section_items = []
            
            if display_section == "languages":
                section_title = "LANGUAGES"
                section_items = self.analysis_results.languages_formatted
            elif display_section == "interests":
                section_title = "INTERESTS"
                section_items = self.analysis_results.interests_formatted
            elif display_section == "systems":
                section_title = "TECHNICAL SYSTEMS"
                section_items = self.analysis_results.systems_formatted
            
            if display_section and section_items:
                pdf.ln(3)
                pdf.set_font("Times", 'B', 12)
                pdf.cell(0, 10, section_title, ln=True)
                pdf.line(15, pdf.get_y(), 195, pdf.get_y())
                pdf.ln(2)
                pdf.set_font("Times", '', 11)
                
                # Print items as a simple list
                for item in section_items:
                    if item and len(item.strip()) > 0:
                        pdf.cell(5, 7, self.bullet_char)
                        pdf.cell(0, 7, item, ln=True)
            
            # Save PDF
            output_path = os.path.join(OUTPUT_DIR, "visual_cv.pdf")
            pdf.output(output_path)
            
            logger.info(f"Visual CV PDF saved to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error generating visual CV PDF: {str(e)}", exc_info=True)
            raise