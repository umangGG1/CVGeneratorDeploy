"""
Document processor module for extracting information from input documents using LLMs.
"""
import os
import json
from typing import Dict, List, Any, Optional, Tuple

import openai
from openai import OpenAI
import PyPDF2

from models.data_models import ExtractedData, TranscriptInsights, GoalsData, Language, Experience, Education, PersonalInfo
from utils.logger import setup_logger
from utils.helpers import safe_json_loads
from config.settings import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE

# Set up logger
logger = setup_logger(__name__)

# Configure OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

class DocumentProcessor:
    """Processes and extracts information from PDF documents using LLMs"""
    
    def __init__(self):
        self.extracted_data = ExtractedData()
        logger.info("DocumentProcessor initialized")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as string
        """
        logger.info(f"Extracting text from PDF: {pdf_path}")
        
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            
            logger.debug(f"Extracted {len(text)} characters from PDF")
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}", exc_info=True)
            raise
    
    def process_linkedin_profile(self, pdf_path: str = "linkedin_profile.pdf") -> None:
        """
        Extract information from LinkedIn profile PDF.
        
        Args:
            pdf_path: Path to the LinkedIn profile PDF
        """
        logger.info(f"Processing LinkedIn profile from {pdf_path}")
        
        try:
            # Extract text from PDF
            text = self.extract_text_from_pdf(pdf_path)
            
            # Process using LLM
            prompt = f"""
            This is the LinkedIn profile text from the PDF, convert this into structured format, friendly for passing to LLMs.
            I want the sections to be:
            - name
            - headline
            - top skills
            - certifications
            - contact (including email, website, phone etc. mentioned)
            - current location
            - summary
            - experience (with all past experiences with fields: company title, job title, location, timeline, description)
            - education (with institution name, degree name, timeline of degree/class)
            
            Fetch any other thing if I am missing something.
            Note: Do extract multiple job roles in the same company, or multiple degrees achieved from the same institute.
            
            LinkedIn profile text:
            {text}
            
            Return the data in JSON format.
            """
            
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured information from LinkedIn profiles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            
            content = response.choices[0].message.content.strip()
            profile_data = safe_json_loads(content)
            
            if not profile_data:
                logger.warning("Failed to extract structured data from LinkedIn profile")
                return
            
            # Map extracted data to our data model
            self._map_linkedin_data_to_model(profile_data)
            
            logger.info("LinkedIn profile processing complete")
        except Exception as e:
            logger.error(f"Error processing LinkedIn profile: {str(e)}", exc_info=True)
            raise
    
    def process_current_cv(self, pdf_path: str = "current_cv.pdf") -> None:
        """
        Extract information from current CV PDF.
        
        Args:
            pdf_path: Path to the CV PDF
        """
        logger.info(f"Processing current CV from {pdf_path}")
        
        try:
            # Extract text from PDF
            text = self.extract_text_from_pdf(pdf_path)
            
            # Process using LLM
            prompt = f"""
            This is a CV/Resume text from the PDF. Convert this into a structured format suitable for parsing by LLMs.
            
            I want the sections to be:
            - personal_info (name, contact details, location, professional title)
            - summary/profile
            - skills (list of technical and soft skills)
            - experience (all work experiences with company name, job title, dates, location, responsibilities, achievements)
            - education (all education with institution, degree, dates, additional details)
            - certifications/training
            - languages (with proficiency levels if mentioned)
            - achievements/awards
            - additional_sections (any other sections present in the CV)
            
            Note: Please extract all details including multiple roles at the same company or multiple degrees from the same institution.
            Extract any quantifiable achievements with metrics when available.
            
            CV text:
            {text}
            
            Return the data in JSON format.
            """
            
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured information from CVs and resumes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            
            content = response.choices[0].message.content.strip()
            cv_data = safe_json_loads(content)
            
            if not cv_data:
                logger.warning("Failed to extract structured data from CV")
                return
            
            # Map extracted data to our data model
            self._map_cv_data_to_model(cv_data)
            
            logger.info("CV processing complete")
        except Exception as e:
            logger.error(f"Error processing CV: {str(e)}", exc_info=True)
            raise
    
    def process_meeting_transcript(self, pdf_path: str = "meeting_transcript.pdf") -> TranscriptInsights:
        """
        Extract key insights from meeting transcript PDF.
        
        Args:
            pdf_path: Path to the meeting transcript PDF
            
        Returns:
            TranscriptInsights object
        """
        logger.info(f"Processing meeting transcript from {pdf_path}")
        
        try:
            # Extract text from PDF
            text = self.extract_text_from_pdf(pdf_path)
            
            # Process using LLM
            prompt = f"""
            Please analyze this meeting transcript between a career coach and client, and extract the following information:
            
            1. Career goals and aspirations
            2. Target industries or roles
            3. Unique value proposition or professional strengths
            4. Key achievements mentioned (with any metrics)
            5. Skills and competencies highlighted
            6. Any pain points or areas for improvement
            
            Meeting transcript:
            {text}
            
            Please format the response as JSON with these categories.
            """
            
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert career coach assistant that extracts key information from meeting transcripts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            
            content = response.choices[0].message.content.strip()
            transcript_insights = safe_json_loads(content, default={
                "career_goals": "",
                "target_industries": [],
                "unique_value": "",
                "achievements": [],
                "skills": [],
                "improvement_areas": []
            })
            
            logger.info("Meeting transcript processing complete")
            return TranscriptInsights(**transcript_insights)
        except Exception as e:
            logger.error(f"Error processing meeting transcript: {str(e)}", exc_info=True)
            return TranscriptInsights()
    
    def process_professional_goals(self, pdf_path: str = "professional_goals.pdf") -> GoalsData:
        """
        Process professional goals document from PDF.
        
        Args:
            pdf_path: Path to the professional goals PDF
            
        Returns:
            GoalsData object
        """
        logger.info(f"Processing professional goals from {pdf_path}")
        
        try:
            # Extract text from PDF
            text = self.extract_text_from_pdf(pdf_path)
            
            # Process using LLM
            prompt = f"""
            This document contains a person's professional goals and aspirations. 
            Extract and structure the following information:
            
            1. Professional goals (overall career direction)
            2. Career goals (specific targets for the next 1-3 years)
            3. Target industries or roles the person is interested in
            4. Unique value proposition (what makes them stand out)
            5. Skills they want to highlight or develop
            6. Achievements they're proud of or want to emphasize
            
            Professional goals text:
            {text}
            
            Return the data in JSON format with these categories.
            """
            
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured information about professional goals and aspirations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            
            content = response.choices[0].message.content.strip()
            goals_data = safe_json_loads(content, default={
                "professional_goals": "",
                "career_goals": "",
                "target_industries": "",
                "unique_value": "",
                "skills": "",
                "achievements": ""
            })
            
            logger.info("Professional goals processing complete")
            return GoalsData(**goals_data)
        except Exception as e:
            logger.error(f"Error processing professional goals: {str(e)}", exc_info=True)
            return GoalsData()
    
    def _map_linkedin_data_to_model(self, profile_data: Dict[str, Any]) -> None:
        """
        Map extracted LinkedIn data to our data model.
        
        Args:
            profile_data: Dictionary of extracted LinkedIn data
        """
        logger.debug("Mapping LinkedIn data to model")
        
        try:
            # Map personal info
            self.extracted_data.personal_info.name = profile_data.get("name", "")
            self.extracted_data.personal_info.current_headline = profile_data.get("headline", "")
            self.extracted_data.personal_info.summary = profile_data.get("summary", "")
            
            # Add contact info if available
            if "contact" in profile_data:
                self.extracted_data.personal_info.contact_info = profile_data["contact"]
            
            # Map skills
            if "top_skills" in profile_data and isinstance(profile_data["top_skills"], list):
                self.extracted_data.skills.extend(profile_data["top_skills"])
            
            # Map experience
            if "experience" in profile_data and isinstance(profile_data["experience"], list):
                for exp_data in profile_data["experience"]:
                    experience = Experience(
                        title=exp_data.get("job_title", ""),
                        company=exp_data.get("company_title", ""),
                        location=exp_data.get("location", ""),
                        dates=exp_data.get("timeline", ""),
                        description=exp_data.get("description", "")
                    )
                    
                    # Extract achievements from description if not explicitly provided
                    if "achievements" in exp_data and isinstance(exp_data["achievements"], list):
                        experience.achievements = exp_data["achievements"]
                    
                    self.extracted_data.experience.append(experience)
            
            # Map education
            if "education" in profile_data and isinstance(profile_data["education"], list):
                for edu_data in profile_data["education"]:
                    education = Education(
                        degree=edu_data.get("degree_name", ""),
                        institution=edu_data.get("institution_name", ""),
                        dates=edu_data.get("timeline", ""),
                        details=edu_data.get("description", "")
                    )
                    
                    self.extracted_data.education.append(education)
            
            # Map certifications
            if "certifications" in profile_data and isinstance(profile_data["certifications"], list):
                self.extracted_data.certifications.extend(profile_data["certifications"])
            
            # Map languages if available
            if "languages" in profile_data and isinstance(profile_data["languages"], list):
                for lang_data in profile_data["languages"]:
                    if isinstance(lang_data, dict):
                        language = Language(
                            language=lang_data.get("language", ""),
                            proficiency=lang_data.get("proficiency", "Fluent")
                        )
                    else:
                        language = Language(language=lang_data)
                    
                    self.extracted_data.languages.append(language)
            
            logger.debug("LinkedIn data mapped successfully")
        except Exception as e:
            logger.error(f"Error mapping LinkedIn data to model: {str(e)}", exc_info=True)
    
    def _map_cv_data_to_model(self, cv_data: Dict[str, Any]) -> None:
        """
        Map extracted CV data to our data model.
        
        Args:
            cv_data: Dictionary of extracted CV data
        """
        logger.debug("Mapping CV data to model")
        
        try:
            # Map personal info
            if "personal_info" in cv_data:
                personal_info = cv_data["personal_info"]
                if isinstance(personal_info, dict):
                    self.extracted_data.personal_info.name = personal_info.get("name", "")
                    new_headline = personal_info.get("professional_title", "")
                    if new_headline:
                        if self.extracted_data.personal_info.current_headline:
                            self.extracted_data.personal_info.current_headline += " | " + new_headline
                        else:
                            self.extracted_data.personal_info.current_headline = new_headline

                    self.extracted_data.personal_info.contact_info = {
                        k: v for k, v in personal_info.items() 
                        if k not in ["name", "professional_title"]
                    }
            
            # Map summary
            if "summary" in cv_data:
                self.extracted_data.personal_info.summary = cv_data["summary"]
            elif "profile" in cv_data:
                self.extracted_data.personal_info.summary = cv_data["profile"]
            
            # Map skills
            if "skills" in cv_data:
                skills = cv_data["skills"]
                if isinstance(skills, list):
                    self.extracted_data.skills.extend(skills)
                elif isinstance(skills, dict):
                    for skill_category, skill_list in skills.items():
                        if isinstance(skill_list, list):
                            self.extracted_data.skills.extend(skill_list)
            
            # Map experience
            if "experience" in cv_data and isinstance(cv_data["experience"], list):
                for exp_data in cv_data["experience"]:
                    if not isinstance(exp_data, dict):
                        continue
                        
                    experience = Experience(
                        title=exp_data.get("job_title", ""),
                        company=exp_data.get("company_name", ""),
                        location=exp_data.get("location", ""),
                        dates=exp_data.get("dates", ""),
                        description=exp_data.get("description", "")
                    )
                    
                    # Add responsibilities if available
                    if "responsibilities" in exp_data and isinstance(exp_data["responsibilities"], list):
                        experience.description += "\n" + "\n".join(exp_data["responsibilities"])
                    
                    # Add achievements if available
                    if "achievements" in exp_data and isinstance(exp_data["achievements"], list):
                        experience.achievements = exp_data["achievements"]
                    
                    self.extracted_data.experience.append(experience)
            
            # Map education
            if "education" in cv_data and isinstance(cv_data["education"], list):
                for edu_data in cv_data["education"]:
                    if not isinstance(edu_data, dict):
                        continue
                        
                    education = Education(
                        degree=edu_data.get("degree", ""),
                        institution=edu_data.get("institution", ""),
                        dates=edu_data.get("dates", ""),
                        details=edu_data.get("details", "")
                    )
                    
                    self.extracted_data.education.append(education)
            
            # Map certifications
            if "certifications" in cv_data:
                certs = cv_data["certifications"]
                if isinstance(certs, list):
                    self.extracted_data.certifications.extend(certs)
            elif "certifications_training" in cv_data:
                certs = cv_data["certifications_training"]
                if isinstance(certs, list):
                    self.extracted_data.certifications.extend(certs)
            
            # Map languages
            if "languages" in cv_data:
                langs = cv_data["languages"]
                if isinstance(langs, list):
                    for lang_data in langs:
                        if isinstance(lang_data, dict):
                            language = Language(
                                language=lang_data.get("language", ""),
                                proficiency=lang_data.get("proficiency", "Fluent")
                            )
                        else:
                            language = Language(language=lang_data)
                        
                        self.extracted_data.languages.append(language)
            
            # Map achievements
            if "achievements" in cv_data or "awards" in cv_data:
                achievements = cv_data.get("achievements", []) or cv_data.get("awards", [])
                if isinstance(achievements, list):
                    self.extracted_data.achievements.extend(achievements)
            
            logger.debug("CV data mapped successfully")
        except Exception as e:
            logger.error(f"Error mapping CV data to model: {str(e)}", exc_info=True)