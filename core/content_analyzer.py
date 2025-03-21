"""
Content analyzer module for analyzing extracted data before CV generation, 
using strictly the candidate's data without assumptions.
"""
import re
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

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
            self._format_interests_and_systems()
            
            # Save analysis results to file
            self._save_analysis_results()
            
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
        prompt = f"""
        Please suggest headline content that will go at the top of the CV in the following format:
        "Strategic Business Consultant | Market Expansion Leader | Cross-Cultural Operations Expert"

        The headline should convey the candidate's professional identity and expertise through three key specializations.

        Current job titles: {', '.join(current_titles[:3])}
        Career goals: {self.transcript_insights.career_goals}
        Target industries: {', '.join(self.transcript_insights.target_industries)}
        Unique value proposition: {self.transcript_insights.unique_value}

        Generate 5 headline options that:
        - Use the format of "Primary Title | Secondary Focus | Tertiary Specialty"
        - Reflect the candidate's level of seniority
        - Highlight their main professional focus areas
        - Align with their career aspirations
        - Contain approximately 10-12 words total
        
        IMPORTANT:
        - Use ONLY information provided about the candidate
        - Do not make up or assume additional information
        - Ensure titles are modern and impactful
        """
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert CV writer specializing in creating impactful professional headlines for senior professionals. Use only the candidate's actual data without making assumptions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0  # Slightly higher temperature for creative headline variations
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
        
        # Calculate total years of experience
        experience_years = self._calculate_total_experience()
        
        # Extract key industries from experience and insights
        industries = set()
        for exp in self.extracted_data.experience:
            if exp.company:
                industries.add(exp.company.split()[0])  # Add first word of company name as potential industry
        
        # Add industries from transcript insights
        if self.transcript_insights.target_industries:
            industries.update(self.transcript_insights.target_industries)
        
        # Get current role information
        current_role = ""
        current_company = ""
        if self.extracted_data.experience and len(self.extracted_data.experience) > 0:
            current_role = self.extracted_data.experience[0].title or ""
            current_company = self.extracted_data.experience[0].company or ""
        
        # Get highest education
        highest_education = ""
        degree_type = ""
        if self.extracted_data.education and len(self.extracted_data.education) > 0:
            highest_education = self.extracted_data.education[0].degree or ""
            if "MBA" in highest_education:
                degree_type = "MBA"
            elif "Master" in highest_education:
                degree_type = "Master's degree"
            elif "Bachelor" in highest_education:
                degree_type = "Bachelor's degree"
        
        # Compile information for summary components
        content = {
            "experience_years": experience_years if experience_years else "",
            "current_role": current_role,
            "current_company": current_company,
            "industries": list(industries)[:3],
            "unique_value": self.transcript_insights.unique_value,
            "key_achievements": self.transcript_insights.achievements[:3] if self.transcript_insights.achievements else [],
            "career_goals": self.transcript_insights.career_goals,
            "highest_education": highest_education,
            "degree_type": degree_type,
            "skills": self.transcript_insights.skills[:5] if self.transcript_insights.skills else []
        }
        
        # Skip if insufficient data
        if not content["current_role"] and not content["unique_value"]:
            logger.warning("Insufficient data for summary generation")
            return
        
        # Use OpenAI to generate summary components
        prompt = f"""
        Continue with updating the summary section for the CV. The summary should have 4 distinct components:

        1. Profile: Accomplished professional with overview of years of experience, expertise areas, and industries.
        2. Expertise: Key professional strengths, demonstrable skills, and technical capabilities.
        3. Education: Brief mention of highest educational qualifications and certifications.
        4. Career Aspirations: Forward-looking statement about career goals and target roles.

        Professional information:
        - Experience: {content['experience_years']} years
        - Current role: {content['current_role']} at {content['current_company']}
        - Industries: {', '.join(content['industries'])}
        - Unique value proposition: {content['unique_value']}
        - Key achievements: {'; '.join(content['key_achievements'])}
        - Career goals: {content['career_goals']}
        - Education: {content['highest_education']}
        - Skills: {', '.join(content['skills'])}

        For each component:
        - Write in bullet point format starting with '●'
        - Use active, concise language
        - Highlight measurable impact where possible
        - Keep each bullet to 2-3 lines maximum
        - Start with the strongest points
        - Format as shown in the example:
          ● Profile: Accomplished executive with over 20 years of leadership experience in Records and Information Management, Operations, and Business Development across emerging markets. Renowned for driving operational excellence, leading market expansions in seven African countries...

        Use ONLY information provided about the candidate. Do not make up additional details.
        """
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert CV writer specializing in professional executive summaries for senior professionals. Use only the candidate's actual data without making assumptions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        
        summary_text = response.choices[0].message.content
        
        # Extract components using regex pattern matching
        profile_match = re.search(r'(?:●|•)\s*Profile:(.*?)(?=(?:●|•)|$)', summary_text, re.DOTALL)
        expertise_match = re.search(r'(?:●|•)\s*Expertise:(.*?)(?=(?:●|•)|$)', summary_text, re.DOTALL)
        education_match = re.search(r'(?:●|•)\s*Education:(.*?)(?=(?:●|•)|$)', summary_text, re.DOTALL)
        aspirations_match = re.search(r'(?:●|•)\s*Career Aspirations:(.*?)(?=(?:●|•)|$)', summary_text, re.DOTALL)
        
        # Store results, ensuring we don't include empty strings
        self.analysis_results.summary_points = {
            "profile": profile_match.group(1).strip() if profile_match else "",
            "expertise": expertise_match.group(1).strip() if expertise_match else "",
            "education": education_match.group(1).strip() if education_match else "",
            "aspirations": aspirations_match.group(1).strip() if aspirations_match else ""
        }
        
        logger.debug("Summary components analysis complete")

    def _categorize_skills_and_competencies(self) -> None:
        """Categorize skills into core skills and competencies"""
        logger.info("Categorizing skills and competencies")
        
        # Compile comprehensive list of skills from all sources
        all_skills = set()
        
        # Add skills from extracted data
        if self.extracted_data.skills:
            all_skills.update(self.extracted_data.skills)
        
        # Add skills from transcript insights
        if self.transcript_insights.skills:
            all_skills.update(self.transcript_insights.skills)
        
        # Add skills extracted from experience descriptions
        for exp in self.extracted_data.experience:
            # Extract potential skills from descriptions using simple NLP
            if exp.description:
                # Look for noun phrases that might be skills
                words = exp.description.split()
                for i in range(len(words)-1):
                    if words[i].lower() in ['managed', 'developed', 'led', 'implemented', 'utilized', 'coordinated']:
                        potential_skill = ' '.join(words[i+1:i+4])
                        # Clean up and add if reasonable length
                        skill = re.sub(r'[^\w\s]', '', potential_skill).strip()
                        if 5 < len(skill) < 30:  # Reasonable length for a skill
                            all_skills.add(skill)
        
        # Skip if insufficient skills data
        if len(all_skills) < 3:
            logger.warning("Insufficient skills data for categorization")
            return
        
        skills_list = list(all_skills)
        
        # Use OpenAI to categorize skills
        prompt = f"""
        Thanks for that. Now let's move on to CORE SKILLS AND COMPETENCIES.
        Please compile in the following format:
        Project Management • Logistics Management • Lean Operations • Business Development • Sales Strategy • Legal Compliance • Cross-Cultural Leadership • Innovation and Problem-Solving • Decision-Making • Coaching and Training • Operational Excellence • Process Optimisation • KPI and ROI Analysis • Stakeholder Engagement

        Using the candidate's background, categorize these skills into:
        1. Core Skills (technical/hard skills related to their profession)
        2. Competencies (soft skills and professional attributes)

        Skills to categorize:
        {', '.join(skills_list)}

        IMPORTANT:
        - Organize skills in order of relevance to their most recent role
        - Format with bullet points (•) between skills
        - Select approximately 7-9 skills for each category
        - Include ONLY skills from the list provided
        - Skills should be 1-3 words each, concisely named
        - Use title case for each skill
        
        Provide your response as two separate lists labeled "Core Skills:" and "Competencies:"
        """
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert CV writer specializing in professional skill categorization for executive CVs. Use only the candidate's actual skills without adding anything."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        
        skills_text = response.choices[0].message.content
        
        # Extract core skills and competencies
        core_skills_match = re.search(r'Core Skills:(.+?)(?=Competencies:|$)', skills_text, re.DOTALL)
        competencies_match = re.search(r'Competencies:(.+)', skills_text, re.DOTALL)
        
        # Process core skills
        if core_skills_match:
            core_skills_text = core_skills_match.group(1).strip()
            # Split by bullet points or create a list if no bullet points are found
            if '•' in core_skills_text:
                core_skills = [s.strip() for s in core_skills_text.split('•') if s.strip()]
            else:
                core_skills = [s.strip() for s in core_skills_text.split(',') if s.strip()]
            
            # Validate against original skills
            self.analysis_results.core_skills = [
                skill for skill in core_skills 
                if any(skill.lower() in s.lower() or s.lower() in skill.lower() for s in skills_list)
            ]
        
        # Process competencies
        if competencies_match:
            competencies_text = competencies_match.group(1).strip()
            # Split by bullet points or create a list if no bullet points are found
            if '•' in competencies_text:
                competencies = [s.strip() for s in competencies_text.split('•') if s.strip()]
            else:
                competencies = [s.strip() for s in competencies_text.split(',') if s.strip()]
            
            # Validate against original skills
            self.analysis_results.competencies = [
                comp for comp in competencies 
                if any(comp.lower() in s.lower() or s.lower() in comp.lower() for s in skills_list)
            ]
        
        logger.debug(f"Categorized {len(self.analysis_results.core_skills)} core skills and {len(self.analysis_results.competencies)} competencies")

    def _extract_experience_highlights(self) -> None:
        """Extract and enhance key highlights from experience"""
        logger.info("Extracting experience highlights")
        
        # Skip if no experience data available
        if not self.extracted_data.experience:
            logger.warning("No experience data found to extract highlights")
            return
        
        # Process each role
        for exp in self.extracted_data.experience:
            # Basic role information
            role_info = {
                "title": exp.title,
                "company": exp.company,
                "dates": exp.dates,
                "location": exp.location,
                "achievements": []
            }
            
            # If no description or achievements, add role with empty achievements
            if not exp.description and not exp.achievements:
                self.analysis_results.experience_highlights.append(role_info)
                continue
            
            # Prepare experience data
            role_description = exp.description or ""
            role_achievements = exp.achievements or []
            
            # Convert achievements list to text
            achievements_text = "\n".join([f"- {a}" for a in role_achievements])
            
            # Generate concise prompt for experience highlights
            prompt = f"""
            Format the work experience for this role:

            Role details:
            Title: {exp.title}
            Company: {exp.company}
            Dates: {exp.dates}
            Location: {exp.location or 'N/A'}
            
            Description:
            {role_description}

            Existing achievements:
            {achievements_text}

            Create 4-5 achievement-focused bullet points that:
            1. Start with a strong action verb
            2. Include ONLY metrics and results explicitly mentioned in the description/achievements
            3. Focus on impact, not just responsibilities
            4. Are concise (1-2 lines each)

            For example:
            ● Integrated a 20-year local business into a multinational framework, standardising operations and aligning team performance
            ● Led digital transformation for a major bank, optimising information flow across 900+ branches

            IMPORTANT RULES:
            - Do NOT add any metrics, numbers, or achievements that aren't explicitly stated in the input
            - Do NOT invent percentages, dollar amounts, or team sizes
            - Use ONLY information directly provided in the description or achievements
            - If specific metrics aren't available, focus on the scope of responsibility and impact without inventing numbers
            - Format each bullet to start with ●
            """
            
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a CV formatter that strictly uses only the information provided. Never add metrics, numbers, or details that aren't explicitly mentioned in the input."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0  # Zero temperature to prevent invented metrics
            )
            
            highlights_text = response.choices[0].message.content
            
            # Extract achievement bullets
            bullets = []
            for line in highlights_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('●') or line.startswith('•') or line.startswith('-')):
                    achievement = re.sub(r'^[●•\-]+\s*', '', line).strip()
                    if achievement:
                        bullets.append(achievement)
            
            # If extraction failed, use original achievements if available
            if not bullets and role_achievements:
                bullets = role_achievements
            
            # Add achievements to role info
            role_info["achievements"] = bullets[:5]  # Limit to 5 achievements
            
            # Add to results
            self.analysis_results.experience_highlights.append(role_info)
        
        logger.debug(f"Extracted highlights for {len(self.analysis_results.experience_highlights)} roles")

    def _identify_achievement_metrics(self) -> None:
        """Identify and extract key achievement metrics for career highlights"""
        logger.info("Identifying achievement metrics")
        
        # Compile all achievements from experience highlights
        all_achievements = []
        for exp in self.analysis_results.experience_highlights:
            all_achievements.extend(exp.get("achievements", []))
        
        # Add achievements from transcript insights
        if self.transcript_insights.achievements:
            all_achievements.extend(self.transcript_insights.achievements)
        
        # Skip if insufficient achievements data
        if len(all_achievements) < 3:
            logger.warning("Insufficient achievements data for metric identification")
            return
        
        # First, identify achievements that already contain metrics
        metric_achievements = []
        for achievement in all_achievements:
            # Look for numbers, percentages, currency amounts
            if re.search(r'\d+', achievement) or '%' in achievement or any(currency in achievement for currency in ['$', '€', '£']):
                metric_achievements.append(achievement)
        
        # If we don't have enough achievements with metrics, include some without metrics
        if len(metric_achievements) < 8:
            non_metric_achievements = [a for a in all_achievements if a not in metric_achievements]
            combined_achievements = metric_achievements + non_metric_achievements
        else:
            combined_achievements = metric_achievements
        
        # Generate prompt for identifying achievement metrics
        prompt = f"""
        Extract the 8 most impressive career achievements from this list:

        {'. '.join(combined_achievements)}

        Format requirements:
        1. Start each achievement with a strong action verb in past tense
        2. Include ONLY metrics and numbers that are explicitly mentioned in the original text
        3. Keep each bullet to approximately 10-12 words
        4. Format as a simple list with one achievement per line, starting with a dash (-)
        
        Example of proper formatting:
        - Expanded business into 7 African markets through greenfield and M&A strategies
        - Built and scaled operations, driving $4M+ revenue, 53% EBITDA, and 20% growth
        - Merged five acquired companies, managing 300+ staff across seven markets

        EXTREMELY IMPORTANT:
        - DO NOT invent or add ANY numbers, percentages, or metrics that aren't present in the original text
        - If the original achievement doesn't contain metrics, do not add them
        - Use ONLY information that appears in the provided achievements list
        - Do not rephrase in a way that changes the meaning or implies metrics that aren't there
        """
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a strict CV formatter that extracts and formats existing achievements exactly as they are, without adding any new information, metrics, or numbers that aren't explicitly stated in the original text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0  # Zero temperature for strict adherence to instructions
        )
        
        metrics_text = response.choices[0].message.content
        
        # Extract metrics (one per line)
        metrics = []
        for line in metrics_text.split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•')):
                metric = re.sub(r'^[•\-]+\s*', '', line).strip()
                if metric and len(metric) > 10:  # Ensure it's a substantial achievement
                    metrics.append(metric)
        
        # If we extracted achievements successfully, store them
        if metrics:
            self.analysis_results.achievement_metrics = metrics[:8]  # Limit to 8 metrics
            logger.debug(f"Identified {len(self.analysis_results.achievement_metrics)} achievement metrics")
        else:
            # Fallback: use the original achievements with metrics
            self.analysis_results.achievement_metrics = metric_achievements[:8]
            logger.debug(f"Used fallback method to identify {len(self.analysis_results.achievement_metrics)} achievement metrics")

    def _format_education_certifications_languages(self) -> None:
        """Format education, certifications, and languages sections"""
        logger.info("Formatting education, certifications, and languages")
        
        # Generate prompt for education
        if self.extracted_data.education:
            education_data = []
            for edu in self.extracted_data.education:
                edu_item = {}
                if edu.degree:
                    edu_item["degree"] = edu.degree
                if edu.institution:
                    edu_item["institution"] = edu.institution
                if edu.dates:
                    edu_item["dates"] = edu.dates
                if edu.location:
                    edu_item["location"] = edu.location
                education_data.append(edu_item)
            
            if education_data:
                prompt = f"""
                Format the following education information for a CV, following exactly the example format:

                Education information:
                {json.dumps(education_data, indent=2)}

                Example format:
                2014 - 2017 Executive MBA
                Tiffin University (Ohio, USA)

                1989 - 1994 Bachelor of Engineering in Hydraulics and Pneumatics
                Polytechnic University of Bucharest (Bucharest, Romania)

                IMPORTANT:
                - Format each education entry as shown in the example
                - Only include information from the provided education data
                - Do not add any explanatory text, notes, or headings
                - Do not include bullet points
                - Provide only the formatted education entries, nothing else
                """
                
                response = client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a CV formatting assistant. Format the education section exactly as instructed without adding any additional text or explanations."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0  # Use zero temperature for strict formatting
                )
                
                education_text = response.choices[0].message.content
                
                # Filter out any lines that contain explanatory text or aren't in the expected format
                valid_education_entries = []
                possible_entries = [entry.strip() for entry in education_text.split('\n\n') if entry.strip()]
                
                for entry in possible_entries:
                    # Clean and normalize entry
                    lines = [line.strip() for line in entry.split('\n') if line.strip()]
                    
                    # Skip entries that look like explanatory text
                    if any(term in ' '.join(lines).lower() for term in ['note:', 'here is', 'format', 'example', 'bullet']):
                        continue
                    
                    # Skip entries with bullet points
                    if any(line.startswith('•') or line.startswith('●') or line.startswith('-') for line in lines):
                        continue
                    
                    # Check if it has a reasonable structure (at least two lines, first line should contain a year)
                    if len(lines) >= 2 and re.search(r'\b(19|20)\d{2}\b', lines[0]):
                        valid_education_entries.append('\n'.join(lines))
                
                # If valid entries were found, use them
                if valid_education_entries:
                    self.analysis_results.education_formatted = valid_education_entries
                    logger.debug(f"Formatted {len(valid_education_entries)} education entries")
            else:
                # Fallback: Format manually using the raw data
                fallback_entries = []
                for edu in education_data:
                    lines = []
                    if edu.get("dates") and edu.get("degree"):
                        lines.append(f"{edu['dates']} {edu['degree']}")
                    elif edu.get("degree"):
                        lines.append(edu["degree"])
                        
                    location_part = f" ({edu['location']})" if edu.get("location") else ""
                    if edu.get("institution"):
                        lines.append(f"{edu['institution']}{location_part}")
                    
                    if lines:
                        fallback_entries.append('\n'.join(lines))
                
                if fallback_entries:
                    self.analysis_results.education_formatted = fallback_entries
                    logger.debug(f"Used fallback formatting for {len(fallback_entries)} education entries")
        
        # Generate prompt for certifications
        certifications_data = []
        if self.extracted_data.certifications:
            certifications_data.extend(self.extracted_data.certifications)
        
        # Add certifications from transcript insights if available
        if hasattr(self.transcript_insights, 'certifications') and self.transcript_insights.certifications:
            certifications_data.extend(self.transcript_insights.certifications)
        
        if certifications_data:
            prompt = f"""
            Thanks. Now compile for CERTIFICATIONS & TRAINING section of the CV.

            Certification information:
            {', '.join(certifications_data)}

            Format each certification as follows:
            ● [Certification Name], [Issuing Organization], [Year/Date]

            For in-progress certifications, use:
            ● [Certification Name], [Issuing Organization], [Target Completion: Month Year]

            Example format:
            ● Certified Professional Coach Program, International Coach Academy, Sep 2025 (Target Completion)
            ● Communication Skills, Vinh Giang's Stage Academy, Mar 2025 (Target Completion)
            ● Generative AI for Project Managers, Project Management Institute, Jan 2025
            ● Project Management Professional (PMP), Project Management Institute, Mar 2007

            List the most recent certifications first.
            Include only the most relevant and impressive certifications.
            For each certification, ensure the format is consistent.
            """
            
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert CV writer specializing in formatting certification information for executive CVs."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            
            certifications_text = response.choices[0].message.content
            
            # Extract certification entries
            certifications = []
            for line in certifications_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('●') or line.startswith('•')):
                    cert = re.sub(r'^[●•]+\s*', '', line).strip()
                    if cert:
                        certifications.append(cert)
            
            # Store formatted certifications
            if certifications:
                self.analysis_results.certifications_formatted = certifications
                logger.debug(f"Formatted {len(certifications)} certifications")
        
        # Generate prompt for languages
        if self.extracted_data.languages:
            languages_data = []
            for lang in self.extracted_data.languages:
                lang_item = {}
                if lang.language:
                    lang_item["language"] = lang.language
                if lang.proficiency:
                    lang_item["proficiency"] = lang.proficiency
                languages_data.append(lang_item)
            
            if languages_data:
                prompt = f"""
                Thanks again. Final section for now is 'Languages'. Please compile.

                Language information:
                {json.dumps(languages_data, indent=2)}

                Format the languages section as follows:
                ● [Language] ([Proficiency level])

                Example format:
                ● English (fluent), French (fluent), Romanian (native)

                Group languages by proficiency level if appropriate.
                List the most widely spoken or professionally relevant languages first.
                """
                
                response = client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are an expert CV writer specializing in formatting language information for executive CVs."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0
                )
                
                languages_text = response.choices[0].message.content
                
                # Extract language entries
                languages = []
                for line in languages_text.split('\n'):
                    line = line.strip()
                    if line:
                        # Remove bullet points if present
                        lang = re.sub(r'^[●•]+\s*', '', line).strip()
                        if lang:
                            languages.append(lang)
                
                # Store formatted languages
                if languages:
                    self.analysis_results.languages_formatted = languages
                    logger.debug(f"Formatted {len(languages)} language entries")

    def _format_interests_and_systems(self) -> None:
        """
        Format interests and systems sections and determine which optional section to display
        based on preference order: Languages > Interests > Systems
        """
        logger.info("Formatting interests and systems sections")
        
        try:
            # Process interests if available
            if self.extracted_data.interests:
                interests = self.extracted_data.interests
                
                if interests:
                    # Clean and prepare the interest list
                    clean_interests = [interest.strip() for interest in interests if interest.strip()]
                    
                    # Just use the clean interests directly - no need for complex formatting
                    self.analysis_results.interests_formatted = clean_interests[:7]  # Limit to 7 interests max
                    logger.debug(f"Formatted {len(self.analysis_results.interests_formatted)} interests")
            
            # Process systems/tools if available
            if self.extracted_data.systems:
                systems = self.extracted_data.systems
                
                if systems:
                    # Clean and prepare the systems list
                    clean_systems = [system.strip() for system in systems if system.strip()]
                    
                    # Just use the clean systems directly - no need for complex formatting
                    self.analysis_results.systems_formatted = clean_systems[:7]  # Limit to 7 systems max
                    logger.debug(f"Formatted {len(self.analysis_results.systems_formatted)} systems")
            
            # Determine which section to display based on availability and preference order
            if self.analysis_results.languages_formatted:
                self.analysis_results.display_section = "languages"
                logger.debug("Languages will be displayed")
            elif self.analysis_results.interests_formatted:
                self.analysis_results.display_section = "interests"
                logger.debug("Interests will be displayed")
            elif self.analysis_results.systems_formatted:
                self.analysis_results.display_section = "systems"
                logger.debug("Systems will be displayed")
            else:
                self.analysis_results.display_section = ""
                logger.debug("No optional section available to display")
        
        except Exception as e:
            logger.error(f"Error formatting interests and systems: {str(e)}", exc_info=True)
    
    def _calculate_total_experience(self) -> Optional[int]:
        """
        Calculate total years of professional experience.
        
        Returns:
            Total years of experience or None if cannot be calculated
        """
        logger.debug("Calculating total years of experience")
        
        if not self.extracted_data.experience:
            logger.warning("No experience data available for calculation")
            return None
        
        total_years = 0
        current_year = datetime.now().year
        
        for exp in self.extracted_data.experience:
            dates = exp.dates
            if not dates:
                continue
                
            # Extract years using regex
            years_match = re.findall(r'\b(19|20)\d{2}\b', dates)
            if len(years_match) >= 2:
                try:
                    years = sorted([int(y) for y in years_match])
                    # Use the earliest and latest years
                    start_year = min(years)
                    end_year = max(years)
                    years_in_role = end_year - start_year
                    total_years += years_in_role
                except ValueError:
                    # Skip this entry if years can't be converted to integers
                    continue
            elif len(years_match) == 1 and ("present" in dates.lower() or "current" in dates.lower() or "to date" in dates.lower()):
                try:
                    start_year = int(years_match[0])
                    years_in_role = current_year - start_year
                    total_years += years_in_role
                except ValueError:
                    # Skip this entry if year can't be converted to integer
                    continue
        
        if total_years > 0:
            logger.debug(f"Calculated {total_years} years of total experience")
            return total_years
        else:
            logger.warning("Could not calculate total experience from available data")
            return None  # Return None if we couldn't calculate experience
    
    def _save_analysis_results(self) -> None:
        """
        Save the analysis results to a JSON file in the output directory.
        """
        logger.info("Saving analysis results to file")
        
        try:
            # Create output directory if it doesn't exist
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analyzed_content_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            
            # Convert analysis results to dictionary
            results_dict = {
                "headline_options": self.analysis_results.headline_options,
                "summary_points": self.analysis_results.summary_points,
                "core_skills": self.analysis_results.core_skills,
                "competencies": self.analysis_results.competencies,
                "experience_highlights": self.analysis_results.experience_highlights,
                "achievement_metrics": self.analysis_results.achievement_metrics,
                "education_formatted": self.analysis_results.education_formatted,
                "certifications_formatted": self.analysis_results.certifications_formatted,
                "languages_formatted": self.analysis_results.languages_formatted,
                "interests_formatted": self.analysis_results.interests_formatted,
                "systems_formatted": self.analysis_results.systems_formatted,
                "display_section": self.analysis_results.display_section
            }
            
            # Save to JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Analysis results saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving analysis results: {str(e)}", exc_info=True)
            raise