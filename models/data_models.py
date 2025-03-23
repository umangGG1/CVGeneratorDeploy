"""
Data models for the CV generator application.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class PersonalInfo(BaseModel):
    """Personal information model"""
    name: str = ""
    current_headline: str = ""
    summary: str = ""
    contact_info: Dict[str, str] = Field(default_factory=dict)


class Experience(BaseModel):
    """Work experience model"""
    title: str = ""
    company: str = ""
    location: str = ""
    dates: str = ""
    description: str = ""
    achievements: List[str] = Field(default_factory=list)


class Education(BaseModel):
    """Education model"""
    degree: str = ""
    institution: str = ""
    dates: str = ""
    details: str = ""
    location: str = ""


class Language(BaseModel):
    """Language model"""
    language: str
    proficiency: str = "Fluent"


class ExtractedData(BaseModel):
    """Model for all extracted data"""
    personal_info: PersonalInfo = Field(default_factory=PersonalInfo)
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)
    raw_skills: str = ""
    interests: List[str] = Field(default_factory=list)
    systems: List[str] = Field(default_factory=list)


class TranscriptInsights(BaseModel):
    """Model for insights extracted from meeting transcript"""
    career_goals: str = ""
    target_industries: List[str] = Field(default_factory=list)
    unique_value: str = ""
    achievements: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    improvement_areas: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    systems: List[str] = Field(default_factory=list)


class GoalsData(BaseModel):
    """Model for professional goals data"""
    professional_goals: str = ""
    career_goals: str = ""
    target_industries: str = ""
    unique_value: str = ""
    skills: str = ""
    achievements: str = ""
    interests: str = ""
    systems: str = ""


class AnalysisResults(BaseModel):
    """Model for analysis results"""
    headline_options: List[str] = Field(default_factory=list)
    summary_points: Dict[str, str] = Field(default_factory=dict)
    core_skills: List[str] = Field(default_factory=list)
    competencies: List[str] = Field(default_factory=list)
    experience_highlights: List[Dict[str, Any]] = Field(default_factory=list)
    achievement_metrics: List[str] = Field(default_factory=list)
    education_formatted: List[Dict[str, str]] = Field(default_factory=list)
    certifications_formatted: List[str] = Field(default_factory=list)
    languages_formatted: List[str] = Field(default_factory=list)
    interests_formatted: List[str] = Field(default_factory=list)
    systems_formatted: List[str] = Field(default_factory=list)
    display_section: str = ""  # Can be "languages", "interests", or "systems"