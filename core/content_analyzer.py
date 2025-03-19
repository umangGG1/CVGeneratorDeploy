"""
Content analyzer module for analyzing extracted data before CV generation, 
using strictly the candidate's data without assumptions.
"""
import re
import json
from typing import Dict, List, Any, Optional, Tuple

import openai
from openai import OpenAI

from models.data_models import ExtractedData, TranscriptInsights, GoalsData, AnalysisResults
from utils.logger import setup_logger
from utils.helpers import extract_text_between, safe_json_loads
from config.settings import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE

# Set up logger
logger = setup_logger(__name__)

# Configure OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


class ContentAnalyzer:
    """Analyzes extracted content to prepare for CV generation"""
    
    def __init__(self, extracted_data: ExtractedData, transcript_insights: TranscriptInsights, goals_data: GoalsData):
        self.extracted_data = extracted_data
        self.transcript_insights = transcript_insights
        self.goals_data = goals_data
        self.analysis_results = AnalysisResults()
        logger.info("ContentAnalyzer initialized")
    
    def analyze_all_content(self) -> AnalysisResults:
        """
        Run complete analysis on all content.
        
        Returns:
            Analysis results object
        """
        logger.info("Starting full content analysis")
        
        try:
            self._generate_headline_options()
            self._analyze_summary_components()
            self._categorize_skills_and_competencies()
            self._extract_experience_highlights()
            self._identify_achievement_metrics()
            self._format_education_certifications_languages()
            
            logger.info("Content analysis complete")
            return self.analysis_results
        except Exception as e:
            logger.error(f"Error during content analysis: {str(e)}", exc_info=True)
            raise
    
    def _generate_headline_options(self) -> None:
        """Generate professional headline options based on experience and goals"""
        logger.info("Generating headline options")
        
        # Extract current job titles
        current_titles = []
        for exp in self.extracted_data.experience:
            if exp.title:
                current_titles.append(exp.title)
        
        # If no experience data available, return early
        if not current_titles:
            logger.warning("No experience titles found for headline generation")
            return
        
        # Use OpenAI to generate headline options
        content = f"""
        Current job titles: {', '.join(current_titles[:3])}
        
        Career goals: {self.transcript_insights.career_goals}
        
        Target industries: {', '.join(self.transcript_insights.target_industries)}
        
        Unique value proposition: {self.transcript_insights.unique_value}
        """
        
        prompt = f"""
        Based on this professional's background, generate 5 professional headline options in the format:
        "Primary Title | Secondary Focus | Tertiary Specialty"
        
        For example: "Strategic Business Consultant | Market Expansion Leader | Cross-Cultural Operations Expert"
        
        Professional information:
        {content}
        
        Each headline should be concise, impactful, and highlight their key professional identity and value.
        Use ONLY information from the professional's actual experience and goals provided.
        Do not make up or assume additional information.
        """
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert CV writer specializing in crafting professional headlines. Use only the candidate's actual data without making assumptions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        headlines_text = response.choices[0].message.content
        # Extract headlines (one per line)
        headlines = [line.strip() for line in headlines_text.split('\n') if '|' in line]
        
        if headlines:
            self.analysis_results.headline_options = headlines[:5]  # Take up to 5 options
            logger.debug(f"Generated {len(self.analysis_results.headline_options)} headline options")
        else:
            # Use the most recent job title if available
            if current_titles:
                self.analysis_results.headline_options = [current_titles[0]]
                logger.debug(f"Using current job title as headline: {current_titles[0]}")
    
    def _analyze_summary_components(self) -> None:
        """Analyze content to prepare summary section components"""
        logger.info("Analyzing summary components")
        
        # Extract total experience only if there's experience data
        experience_years = self._calculate_total_experience() if self.extracted_data.experience else None
        
        # Get current role if available
        current_role = ""
        if self.extracted_data.experience:
            current_role = self.extracted_data.experience[0].title
        
        # Get highest education if available
        highest_education = ""
        if self.extracted_data.education:
            highest_education = self.extracted_data.education[0].degree
        
        # Compile information for summary components using only available data
        summary_info = {
            "experience_years": experience_years if experience_years is not None else "",
            "current_role": current_role,
            "key_industries": self.transcript_insights.target_industries,
            "unique_value": self.transcript_insights.unique_value,
            "career_goals": self.transcript_insights.career_goals,
            "highest_education": highest_education
        }
        
        # Generate summary components only if we have sufficient data
        if summary_info["current_role"] or summary_info["unique_value"]:
            prompt = f"""
            Based on this professional's information, create four components for a CV summary section:
            
            1. Profile: A brief overview of their professional background (1-2 sentences)
            2. Expertise: Key skills and areas of technical expertise (1-2 sentences)
            3. Education: Brief mention of educational background (single line)
            4. Career Aspirations: Forward-looking statement about desired roles (1 sentence)
            
            Professional information:
            {', '.join([f"{k}: {v}" for k, v in summary_info.items() if v])}
            
            Format each component separately and write in an active, concise style.
            Use ONLY information provided about the candidate, without making up additional details or assumptions.
            If you don't have enough information for a particular section, just mention the verifiable facts available.
            """
            
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert CV writer specializing in executive summaries. Use only the candidate's actual data without making assumptions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            summary_text = response.choices[0].message.content
            
            # Extract components
            profile_match = re.search(r'Profile:(.*?)(?=Expertise:|$)', summary_text, re.DOTALL)
            expertise_match = re.search(r'Expertise:(.*?)(?=Education:|$)', summary_text, re.DOTALL)
            education_match = re.search(r'Education:(.*?)(?=Career Aspirations:|$)', summary_text, re.DOTALL)
            aspirations_match = re.search(r'Career Aspirations:(.*?)(?=$)', summary_text, re.DOTALL)
            
            self.analysis_results.summary_points = {
                "profile": profile_match.group(1).strip() if profile_match else "",
                "expertise": expertise_match.group(1).strip() if expertise_match else "",
                "education": education_match.group(1).strip() if education_match else "",
                "aspirations": aspirations_match.group(1).strip() if aspirations_match else ""
            }
            
            logger.debug("Summary components generated successfully")
        else:
            logger.warning("Insufficient data to generate meaningful summary components")
            # Set empty summary points without assumptions
            self.analysis_results.summary_points = {
                "profile": "",
                "expertise": "",
                "education": "",
                "aspirations": ""
            }

    def _categorize_skills_and_competencies(self) -> None:
        """Categorize skills into core skills and competencies"""
        logger.info("Categorizing skills and competencies")
        
        # Skip if no skills available
        if not self.extracted_data.skills and not self.transcript_insights.skills:
            logger.warning("No skills found to categorize")
            return
        
        # Compile all skills from different sources
        all_skills = set()
        if self.extracted_data.skills:
            all_skills.update(self.extracted_data.skills)
        
        if self.transcript_insights.skills:
            all_skills.update(self.transcript_insights.skills)
        
        # Use OpenAI to categorize available skills
        if all_skills:
            skills_list = list(all_skills)
            
            current_title = ""
            if self.extracted_data.experience:
                current_title = self.extracted_data.experience[0].title
            
            prompt = f"""
            Please categorize these professional skills into two groups:
            1. Core Skills (technical/hard skills)
            2. Competencies (soft skills/attributes)
            
            Skills to categorize:
            {', '.join(skills_list)}
            
            Only categorize skills from the list provided. Do not add any skills that are not in the list.
            Your response should only contain skills that are explicitly mentioned in the list above.
            
            Format your response as JSON with two arrays: "core_skills" and "competencies".
            """
            
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert in professional skill categorization. Use only the candidate's actual skills without adding anything."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            try:
                content = response.choices[0].message.content
                skills_categorized = safe_json_loads(content)
                
                # Only use skills that were in the original list
                if "core_skills" in skills_categorized:
                    self.analysis_results.core_skills = [
                        skill for skill in skills_categorized["core_skills"] 
                        if any(skill.lower() in s.lower() for s in skills_list)
                    ]
                
                if "competencies" in skills_categorized:
                    self.analysis_results.competencies = [
                        comp for comp in skills_categorized["competencies"] 
                        if any(comp.lower() in s.lower() for s in skills_list)
                    ]
                
                logger.debug(f"Categorized {len(self.analysis_results.core_skills)} core skills and {len(self.analysis_results.competencies)} competencies")
            except Exception as json_error:
                logger.warning(f"Failed to parse skills JSON: {str(json_error)}")
                # Fallback to simple partition - strictly using candidate's skills
                self.analysis_results.core_skills = skills_list[:len(skills_list)//2]
                self.analysis_results.competencies = skills_list[len(skills_list)//2:]
    
    def _extract_experience_highlights(self) -> None:
        """Extract and enhance key highlights from experience"""
        logger.info("Extracting experience highlights")
        
        # Skip if no experience data available
        if not self.extracted_data.experience:
            logger.warning("No experience data found to extract highlights")
            return
        
        # Process each role
        for experience in self.extracted_data.experience:
            role_highlights = {
                "title": experience.title,
                "company": experience.company,
                "dates": experience.dates,
                "location": experience.location,
                "achievements": []
            }
            
            # If no description or achievements, copy existing data without enhancement
            if not experience.description and not experience.achievements:
                self.analysis_results.experience_highlights.append(role_highlights)
                continue
            
            # Get existing achievements and description
            achievements = experience.achievements
            raw_description = experience.description
            
            # Use OpenAI to enhance and format achievements from existing information only
            content = f"""
            Role: {role_highlights['title']}
            Company: {role_highlights['company']}
            Dates: {role_highlights['dates']}
            
            Description:
            {raw_description}
            
            Existing achievements:
            {'. '.join(achievements)}
            """
            
            prompt = f"""
            For this professional role, create 4-5 achievement-focused bullet points that:
            1. Start with strong action verbs
            2. Include specific metrics and quantifiable results from the description if available
            3. Demonstrate impact and value created
            4. Are concise and impactful
            
            Role information:
            {content}
            
            Format each achievement as a separate bullet point starting with a strong action verb.
            Use ONLY information provided in the description and existing achievements.
            Do not make up metrics, numbers, or achievements that aren't mentioned in the original content.
            If there isn't enough information to create 4-5 achievement statements, it's okay to create fewer.
            """
            
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert CV writer specializing in achievement-focused experience descriptions. Use only information from the candidate's actual data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            achievements_text = response.choices[0].message.content
            
            # Extract achievements (one per line)
            enhanced_achievements = []
            for line in achievements_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('•') or line.startswith('-') or re.match(r'^\d+\.', line)):
                    achievement = re.sub(r'^[•\-\d\.]+\s*', '', line)
                    enhanced_achievements.append(achievement)
                elif line and len(line) > 10:  # Check for minimum content
                    enhanced_achievements.append(line)
            
            # If no achievements were generated, keep original achievements
            if enhanced_achievements:
                role_highlights["achievements"] = enhanced_achievements
            else:
                role_highlights["achievements"] = achievements
            
            self.analysis_results.experience_highlights.append(role_highlights)
            
        logger.debug(f"Extracted highlights for {len(self.analysis_results.experience_highlights)} roles")
    
    def _identify_achievement_metrics(self) -> None:
        """Identify and extract key achievement metrics for career highlights"""
        logger.info("Identifying achievement metrics")
        
        # Compile all achievements from experiences
        all_achievements = []
        for exp in self.analysis_results.experience_highlights:
            all_achievements.extend(exp.get("achievements", []))
        
        # Add achievements from transcript insights
        if self.transcript_insights.achievements:
            all_achievements.extend(self.transcript_insights.achievements)
        
        # Skip if no achievements available
        if not all_achievements:
            logger.warning("No achievements found to identify metrics")
            return
        
        # Use OpenAI to identify top metrics-based achievements
        prompt = f"""
        From these professional achievements, identify the most impressive ones that:
        1. Contain specific metrics or quantifiable results
        2. Demonstrate significant impact
        3. Would be most impressive to potential employers
        
        Achievements:
        {'. '.join(all_achievements)}
        
        For each selected achievement, condense it into a brief, impactful statement that leads with the metric or result.
        For example, "Increased sales by 35% through implementation of new CRM system" becomes "Increased sales by 35% with new CRM implementation"
        
        Format your response as a list of condensed achievement statements, with a maximum of 8 statements.
        Only include achievements with actual metrics or clear results mentioned in the original text.
        Do not make up or assume any metrics or results that aren't explicitly stated.
        """
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert at identifying and highlighting key professional achievements. Use only the candidate's actual achievements without making assumptions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        metrics_text = response.choices[0].message.content
        
        # Extract metrics-based achievements (one per line)
        metrics = []
        for line in metrics_text.split('\n'):
            line = line.strip()
            if line and (line.startswith('•') or line.startswith('-') or re.match(r'^\d+\.', line)):
                metric = re.sub(r'^[•\-\d\.]+\s*', '', line)
                metrics.append(metric)
            elif line and len(line) > 10:  # Check for minimum content
                metrics.append(line)
        
        if metrics:
            self.analysis_results.achievement_metrics = metrics[:8]  # Take up to 8
            logger.debug(f"Identified {len(self.analysis_results.achievement_metrics)} achievement metrics")
    
    def _format_education_certifications_languages(self) -> None:
        """Format education, certifications, and languages sections"""
        logger.info("Formatting education, certifications, and languages")
        
        # Format education if available
        if self.extracted_data.education:
            for edu in self.extracted_data.education:
                # Only include available fields
                parts = []
                if edu.degree:
                    parts.append(edu.degree)
                if edu.institution:
                    parts.append(edu.institution)
                if edu.dates:
                    parts.append(f"({edu.dates})")
                
                if parts:
                    formatted_edu = " - ".join(parts)
                    self.analysis_results.education_formatted.append(formatted_edu)
            logger.debug(f"Formatted {len(self.analysis_results.education_formatted)} education entries")
        
        # Format certifications if available
        if self.extracted_data.certifications:
            for cert in self.extracted_data.certifications:
                self.analysis_results.certifications_formatted.append(cert)
            logger.debug(f"Formatted {len(self.analysis_results.certifications_formatted)} certifications")
        
        # Format languages if available
        if self.extracted_data.languages:
            for lang in self.extracted_data.languages:
                formatted_lang = f"{lang.language} ({lang.proficiency})"
                self.analysis_results.languages_formatted.append(formatted_lang)
            logger.debug(f"Formatted {len(self.analysis_results.languages_formatted)} languages")
    
    def _calculate_total_experience(self) -> Optional[int]:
        """
        Calculate total years of professional experience.
        
        Returns:
            Total years of experience or None if cannot be calculated
        """
        logger.debug("Calculating total years of experience")
        
        total_years = 0
        current_year = 2025  # Current year
        
        for exp in self.extracted_data.experience:
            dates = exp.dates
            if not dates:
                continue
                
            # Extract start and end years
            years_match = re.findall(r'\b(19|20)\d{2}\b', dates)
            if len(years_match) == 2:
                try:
                    start_year = int(years_match[0])
                    end_year = int(years_match[1])
                    total_years += (end_year - start_year)
                except ValueError:
                    # Skip this entry if years can't be converted to integers
                    continue
            elif len(years_match) == 1 and ("present" in dates.lower() or "current" in dates.lower()):
                try:
                    start_year = int(years_match[0])
                    total_years += (current_year - start_year)
                except ValueError:
                    # Skip this entry if year can't be converted to integer
                    continue
        
        if total_years > 0:
            logger.debug(f"Calculated {total_years} years of total experience")
            return total_years
        else:
            logger.warning("Could not calculate total experience from available data")
            return None  # Return None if we couldn't calculate experience