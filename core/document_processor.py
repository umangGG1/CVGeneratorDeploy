import os
import json
import re
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
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info("DocumentProcessor initialized")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
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
        logger.info(f"Processing LinkedIn profile from {pdf_path}")
        try:
            text = self.extract_text_from_pdf(pdf_path)
            prompt = f"""
            Extract the following information from the LinkedIn profile text and return it in JSON format with the specified structure:

            {{
              "name": "string",
              "headline": "string",
              "top_skills": ["string"],
              "certifications": ["string"],
              "contact": {{
                "email": "string",
                "phone": "string",
                "website": "string",
                "linkedin": "string"
              }},
              "current_location": "string",
              "summary": "string",
              "experience": [
                {{
                  "company_title": "string",
                  "job_title": "string",
                  "location": "string",
                  "timeline": "string",
                  "description": "string"
                }}
              ],
              "education": [
                {{
                  "institution_name": "string",
                  "degree_name": "string",
                  "timeline": "string"
                }}
              ],
              "interests": ["string"]
            }}

            If a section is not found, include it with an empty array or object as appropriate.
            Ensure to extract contact information (email, phone, website, LinkedIn URL, etc.) from anywhere in the text, not just dedicated sections.
            For interests, look for mentions of hobbies, volunteer work, personal interests, or activities throughout the text.
            
            LinkedIn profile text:
            {text}
            """
            
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured information from LinkedIn profiles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            profile_data = safe_json_loads(content)
            
            if not profile_data:
                logger.warning("Failed to extract structured data from LinkedIn profile")
                return
            
            self._map_linkedin_data_to_model(profile_data)
            
            output_file = os.path.join(self.output_dir, "linkedin_profile_data.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
            logger.info(f"LinkedIn profile data saved to {output_file}")
            
            if not self.extracted_data.personal_info.contact_info.get("email"):
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, text)
                if emails:
                    self.extracted_data.personal_info.contact_info["email"] = emails[0]
                    logger.info("Extracted email via regex: %s", emails[0])
            
            logger.info("LinkedIn profile processing complete")
        except Exception as e:
            logger.error(f"Error processing LinkedIn profile: {str(e)}", exc_info=True)
            raise
    
    def process_current_cv(self, pdf_path: str = "current_cv.pdf") -> None:
        logger.info(f"Processing current CV from {pdf_path}")
        try:
            text = self.extract_text_from_pdf(pdf_path)
            prompt = f"""
            Extract the following information from the CV/Resume text and return it in JSON format with the specified structure:

            {{
              "personal_info": {{
                "name": "string",
                "contact": {{
                  "email": "string",
                  "phone": "string",
                  "address": "string",
                  "linkedin": "string"
                }},
                "location": "string",
                "professional_title": "string"
              }},
              "summary": "string",
              "skills": ["string"],
              "experience": [
                {{
                  "company_name": "string",
                  "job_title": "string",
                  "dates": "string",
                  "location": "string",
                  "responsibilities": ["string"],
                  "achievements": ["string"]
                }}
              ],
              "education": [
                {{
                  "institution": "string",
                  "degree": "string",
                  "dates": "string",
                  "details": "string"
                }}
              ],
              "certifications": ["string"],
              "languages": [
                {{
                  "language": "string",
                  "proficiency": "string"
                }}
              ],
              "achievements": ["string"],
              "interests": ["string"],
              "systems_tools": ["string"],
              "additional_sections": {{}}
            }}

            If a section is not found, include it with an empty array or object as appropriate.
            Extract contact details (email, phone, address, LinkedIn URL, etc.) from anywhere in the CV.
            For interests/hobbies, look for mentions of personal interests, hobbies, volunteer work, or extracurricular activities throughout the text.
            
            CV text:
            {text}
            """
            
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured information from CVs and resumes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            cv_data = safe_json_loads(content)
            
            if not cv_data:
                logger.warning("Failed to extract structured data from CV")
                return
            
            self._map_cv_data_to_model(cv_data)
            
            output_file = os.path.join(self.output_dir, "cv_data.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(cv_data, f, indent=2, ensure_ascii=False)
            logger.info(f"CV data saved to {output_file}")
            
            if not self.extracted_data.personal_info.contact_info.get("email"):
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, text)
                if emails:
                    self.extracted_data.personal_info.contact_info["email"] = emails[0]
                    logger.info("Extracted email via regex: %s", emails[0])
            
            logger.info("CV processing complete")
        except Exception as e:
            logger.error(f"Error processing CV: {str(e)}", exc_info=True)
            raise
    
    def process_meeting_transcript(self, pdf_path: str = "meeting_transcript.pdf") -> TranscriptInsights:
        logger.info(f"Processing meeting transcript from {pdf_path}")
        try:
            text = self.extract_text_from_pdf(pdf_path)
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
                temperature=0.1
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
        logger.info(f"Processing professional goals from {pdf_path}")
        try:
            text = self.extract_text_from_pdf(pdf_path)
            prompt = f"""
            This document contains a person's professional goals and aspirations. 
            Extract and structure the following information as plain strings (not dictionaries or lists unless specified):
            
            1. Professional goals (overall career direction) - return as a single string
            2. Career goals (specific targets for the next 1-3 years) - return as a single string
            3. Target industries or roles the person is interested in - return as a single string (comma-separated if multiple)
            4. Unique value proposition (what makes them stand out) - return as a single string
            5. Skills they want to highlight or develop - return as a single string (comma-separated if multiple)
            6. Achievements they're proud of or want to emphasize - return as a single string (comma-separated if multiple)
            
            Professional goals text:
            {text}
            
            Return the data in JSON format with these categories:
            {{
                "professional_goals": "string",
                "career_goals": "string",
                "target_industries": "string",
                "unique_value": "string",
                "skills": "string",
                "achievements": "string"
            }}
            """
            
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured information about professional goals and aspirations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
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
    
    def _normalize_education_text(self, text: str) -> str:
        if not text:
            return ""
        
        # Convert to lowercase and remove extra spaces
        text = " ".join(text.lower().split())
        
        # Remove punctuation
        text = re.sub(r'[^\w\s-]', '', text)
        
        # Standardize degree variations
        degree_replacements = {
            'bachelor degree': 'bachelor',
            'bachelors degree': 'bachelor',
            'bachelor of': 'bachelor',
            'masters degree': 'master',
            'master of': 'master',
            'with financial accounting and auditing': '',  # Remove specific field mentions
            'accounting': '',  # Normalize by removing field if it's the only difference
        }
        for old, new in degree_replacements.items():
            text = text.replace(old, new)
        
        # Standardize institution names
        institution_replacements = {
            ', india': '',  # Remove country suffix
            'india': '',
            'university of': 'university',
        }
        for old, new in institution_replacements.items():
            text = text.replace(old, new)
        
        return text.strip()

    def _is_duplicate_education(self, new_edu: Dict[str, str], existing_education: List[Education]) -> bool:
        # Normalize new education data
        new_degree = self._normalize_education_text(new_edu.get("degree", ""))
        new_institution = self._normalize_education_text(new_edu.get("institution", ""))
        new_dates = self._normalize_education_text(new_edu.get("dates", ""))
        
        # Extract years from new dates
        new_years = re.findall(r'(19|20)\d{2}', new_dates)
        new_start_year = min(new_years) if new_years else ""
        new_end_year = max(new_years) if new_years else new_years[0] if new_years else ""
        
        for edu in existing_education:
            # Normalize existing education data
            existing_degree = self._normalize_education_text(edu.degree)
            existing_institution = self._normalize_education_text(edu.institution)
            existing_dates = self._normalize_education_text(edu.dates)
            
            # Extract years from existing dates
            existing_years = re.findall(r'(19|20)\d{2}', existing_dates)
            existing_start_year = min(existing_years) if existing_years else ""
            existing_end_year = max(existing_years) if existing_years else existing_years[0] if existing_years else ""
            
            # Check for duplicates with improved logic
            institution_match = new_institution and existing_institution and new_institution == existing_institution
            
            # Date overlap check
            date_match = False
            if new_years and existing_years:
                # Check if any year overlaps or is within 1 year
                for ny in new_years:
                    for ey in existing_years:
                        if abs(int(ny) - int(ey)) <= 1:
                            date_match = True
                            break
                    if date_match:
                        break
            elif not new_years or not existing_years:  # If one has no year, rely on other fields
                date_match = True
            
            # Degree similarity check (basic word overlap)
            new_degree_words = set(new_degree.split())
            existing_degree_words = set(existing_degree.split())
            degree_overlap = len(new_degree_words.intersection(existing_degree_words)) > 0
            
            if institution_match and date_match and degree_overlap:
                return True
        
        return False
    def _map_linkedin_data_to_model(self, profile_data: Dict[str, Any]) -> None:
        logger.debug("Mapping LinkedIn data to model")
        try:
            self.extracted_data.personal_info.name = profile_data.get("name", "")
            self.extracted_data.personal_info.current_headline = profile_data.get("headline", "")
            self.extracted_data.personal_info.summary = profile_data.get("summary", "")
            
            # Initialize contact info if empty
            if not self.extracted_data.personal_info.contact_info:
                self.extracted_data.personal_info.contact_info = {}
            
            # Map contact info
            contact = profile_data.get("contact", {})
            if isinstance(contact, dict):
                # Update contact info
                for key, value in contact.items():
                    if value:  # Always update if value exists, don't check if already set
                        self.extracted_data.personal_info.contact_info[key] = value
                
                # Add current_location to contact_info if available
                if current_location := profile_data.get("current_location"):
                    self.extracted_data.personal_info.contact_info["location"] = current_location
            else:
                logger.warning("Contact info is not a dictionary: %s", contact)
            
            # Ensure LinkedIn URL is set
            if linkedin_url := contact.get("linkedin"):
                if not linkedin_url.startswith("https://"):
                    linkedin_url = "https://" + linkedin_url.lstrip("www.")
                self.extracted_data.personal_info.contact_info["linkedin"] = linkedin_url
            
            if "top_skills" in profile_data and isinstance(profile_data["top_skills"], list):
                self.extracted_data.skills.extend(profile_data["top_skills"])
            
            if "experience" in profile_data and isinstance(profile_data["experience"], list):
                for exp_data in profile_data["experience"]:
                    experience = Experience(
                        title=exp_data.get("job_title", ""),
                        company=exp_data.get("company_title", ""),
                        location=exp_data.get("location", ""),
                        dates=exp_data.get("timeline", ""),
                        description=exp_data.get("description", "")
                    )
                    if "achievements" in exp_data and isinstance(exp_data["achievements"], list):
                        experience.achievements = exp_data["achievements"]
                    self.extracted_data.experience.append(experience)
            
            if "education" in profile_data and isinstance(profile_data["education"], list):
                for edu_data in profile_data["education"]:
                    # Skip if this education entry already exists
                    if self._is_duplicate_education({
                        "degree": edu_data.get("degree_name", ""),
                        "institution": edu_data.get("institution_name", ""),
                        "dates": edu_data.get("timeline", "")
                    }, self.extracted_data.education):
                        continue
                    
                    education = Education(
                        degree=edu_data.get("degree_name", ""),
                        institution=edu_data.get("institution_name", ""),
                        dates=edu_data.get("timeline", ""),
                        details=edu_data.get("description", "")
                    )
                    self.extracted_data.education.append(education)
            
            if "certifications" in profile_data and isinstance(profile_data["certifications"], list):
                self.extracted_data.certifications.extend(profile_data["certifications"])
            
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
            
            interests = profile_data.get("interests", [])
            if isinstance(interests, list):
                capitalized_interests = [interest.capitalize() for interest in interests if interest.strip()]
                self.extracted_data.interests.extend(capitalized_interests)
            else:
                logger.warning("Interests is not a list: %s", interests)
            
            logger.debug("LinkedIn data mapped successfully")
        except Exception as e:
            logger.error(f"Error mapping LinkedIn data to model: {str(e)}", exc_info=True)

    def _merge_education_entries(self, existing_edu: Education, new_edu: Dict[str, str]) -> None:
        # Merge degree if new one has more detail
        if len(new_edu.get("degree", "")) > len(existing_edu.degree):
            existing_edu.degree = new_edu["degree"]
        
        # Merge dates (take the range if available)
        new_dates = new_edu.get("dates", "")
        if '-' in new_dates and '-' not in existing_edu.dates:
            existing_edu.dates = new_dates
        
        # Merge details if new one has content
        if new_edu.get("details") and not existing_edu.details:
            existing_edu.details = new_edu["details"]
    
    def _map_cv_data_to_model(self, cv_data: Dict[str, Any]) -> None:
        logger.debug("Mapping CV data to model")
        try:
            if "personal_info" in cv_data and isinstance(cv_data["personal_info"], dict):
                personal_info = cv_data["personal_info"]
                self.extracted_data.personal_info.name = personal_info.get("name", "")
                new_headline = personal_info.get("professional_title", "")
                if new_headline:
                    if self.extracted_data.personal_info.current_headline:
                        self.extracted_data.personal_info.current_headline += " | " + new_headline
                    else:
                        self.extracted_data.personal_info.current_headline = new_headline
                contact = personal_info.get("contact", {})
                if isinstance(contact, dict):
                    # Update contact info, overwriting LinkedIn data if CV provides it
                    for key, value in contact.items():
                        if value:
                            self.extracted_data.personal_info.contact_info[key] = value
                else:
                    logger.warning("Contact info is not a dictionary: %s", contact)
            
            if "summary" in cv_data:
                self.extracted_data.personal_info.summary = cv_data["summary"]
            
            if "skills" in cv_data and isinstance(cv_data["skills"], list):
                self.extracted_data.skills.extend(cv_data["skills"])
            
            if "experience" in cv_data and isinstance(cv_data["experience"], list):
                for exp_data in cv_data["experience"]:
                    experience = Experience(
                        title=exp_data.get("job_title", ""),
                        company=exp_data.get("company_name", ""),
                        location=exp_data.get("location", ""),
                        dates=exp_data.get("dates", ""),
                        description=exp_data.get("description", "")
                    )
                    if "responsibilities" in exp_data and isinstance(exp_data["responsibilities"], list):
                        experience.description += "\n" + "\n".join(exp_data["responsibilities"])
                    if "achievements" in exp_data and isinstance(exp_data["achievements"], list):
                        experience.achievements = exp_data["achievements"]
                    self.extracted_data.experience.append(experience)
            
                    if "education" in cv_data and isinstance(cv_data["education"], list):
                        for edu_data in cv_data["education"]:
                            if self._is_duplicate_education(edu_data, self.extracted_data.education):
                                # Find the matching entry and merge
                                for existing_edu in self.extracted_data.education:
                                    if self._is_duplicate_education(edu_data, [existing_edu]):
                                        self._merge_education_entries(existing_edu, edu_data)
                                        break
                            else:
                                education = Education(
                                    degree=edu_data.get("degree", ""),
                                    institution=edu_data.get("institution", ""),
                                    dates=edu_data.get("dates", ""),
                                    details=edu_data.get("details", "")
                                )
                                self.extracted_data.education.append(education)
            
            if "certifications" in cv_data and isinstance(cv_data["certifications"], list):
                self.extracted_data.certifications.extend(cv_data["certifications"])
            
            if "languages" in cv_data and isinstance(cv_data["languages"], list):
                for lang_data in cv_data["languages"]:
                    if isinstance(lang_data, dict):
                        language = Language(
                            language=lang_data.get("language", ""),
                            proficiency=lang_data.get("proficiency", "Fluent")
                        )
                    else:
                        language = Language(language=lang_data)
                    self.extracted_data.languages.append(language)
            
            if "achievements" in cv_data and isinstance(cv_data["achievements"], list):
                self.extracted_data.achievements.extend(cv_data["achievements"])
            
            # Process interests from CV and combine with LinkedIn interests
            cv_interests = set()
            for field in ["interests", "interests/hobbies", "hobbies"]:
                if field in cv_data:
                    interests = cv_data[field]
                    if isinstance(interests, list):
                        cv_interests.update(interest.strip().capitalize() for interest in interests if interest.strip())
                    elif isinstance(interests, str):
                        cv_interests.add(interests.strip().capitalize())
                    else:
                        logger.warning("Interests field %s is not a list or string: %s", field, interests)
            
            # Convert existing interests to set and capitalize (in case LinkedIn data wasn't processed yet)
            existing_interests = set(interest.capitalize() for interest in self.extracted_data.interests)
            existing_interests.update(cv_interests)
            self.extracted_data.interests = list(existing_interests)
            
            if "systems_tools" in cv_data and isinstance(cv_data["systems_tools"], list):
                self.extracted_data.systems.extend(cv_data["systems_tools"])
            
            logger.debug("CV data mapped successfully")
        except Exception as e:
            logger.error(f"Error mapping CV data to model: {str(e)}", exc_info=True)