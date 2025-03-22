"""
Main workflow orchestrator for CV generation process.
"""
import os
import json
from typing import Dict, List, Any, Optional, Tuple

from models.data_models import ExtractedData, TranscriptInsights, GoalsData, AnalysisResults
from core.document_processor import DocumentProcessor
from core.content_analyzer import ContentAnalyzer
from core.cv_generator import CVGenerator
from utils.logger import setup_logger
from config.settings import OUTPUT_DIR

# Set up logger
logger = setup_logger(__name__)


class CVGenerationWorkflow:
    """Main workflow orchestrator for CV generation"""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.content_analyzer = None
        self.cv_generator = None
        logger.info("CVGenerationWorkflow initialized")
    
    def process_input_documents(self, 
                                linkedin_pdf: str = "linkedin_profile.pdf", 
                                cv_pdf: str = "current_cv.pdf",
                                transcript_pdf: str = "meeting_transcript.pdf", 
                                goals_pdf: str = "professional_goals.pdf") -> None:
        """
        Process all input PDF documents to extract relevant information.
        
        Args:
            linkedin_pdf: Path to LinkedIn profile PDF
            cv_pdf: Path to current CV PDF
            transcript_pdf: Path to meeting transcript PDF
            goals_pdf: Path to professional goals PDF
        """
        logger.info("Processing input documents")
        
        try:
            # Process LinkedIn profile if provided
            if os.path.exists(linkedin_pdf):
                logger.info(f"Processing LinkedIn profile from {linkedin_pdf}")
                self.document_processor.process_linkedin_profile(linkedin_pdf)
            else:
                logger.warning(f"LinkedIn profile PDF not found: {linkedin_pdf}")
            
            # Process current CV if provided
            if os.path.exists(cv_pdf):
                logger.info(f"Processing current CV from {cv_pdf}")
                self.document_processor.process_current_cv(cv_pdf)
            else:
                logger.warning(f"Current CV PDF not found: {cv_pdf}")
            
            # Process transcript and goals
            transcript_insights = TranscriptInsights()
            if os.path.exists(transcript_pdf):
                logger.info(f"Processing meeting transcript from {transcript_pdf}")
                transcript_insights = self.document_processor.process_meeting_transcript(transcript_pdf)
            else:
                logger.warning(f"Meeting transcript PDF not found: {transcript_pdf}")
            
            goals_data = GoalsData()
            if os.path.exists(goals_pdf):
                logger.info(f"Processing professional goals from {goals_pdf}")
                goals_data = self.document_processor.process_professional_goals(goals_pdf)
            else:
                logger.warning(f"Professional goals PDF not found: {goals_pdf}")
            
            # Initialize content analyzer
            self.content_analyzer = ContentAnalyzer(
                self.document_processor.extracted_data,
                transcript_insights,
                goals_data
            )
            
            logger.info("Input document processing complete")
        except Exception as e:
            logger.error(f"Error processing input documents: {str(e)}", exc_info=True)
            raise
    
    def analyze_content(self) -> AnalysisResults:
        """
        Analyze extracted content to prepare for CV generation.
        
        Returns:
            AnalysisResults object
        """
        logger.info("Analyzing content")
        
        try:
            if not self.content_analyzer:
                raise ValueError("Input documents must be processed first")
                
            # Run analysis
            analysis_results = self.content_analyzer.analyze_all_content()
            
            # Initialize CV generator
            self.cv_generator = CVGenerator(
                analysis_results,
                self.document_processor.extracted_data
            )
            
            logger.info("Content analysis complete")
            return analysis_results
        except Exception as e:
            logger.error(f"Error analyzing content: {str(e)}", exc_info=True)
            raise
    
    def generate_cvs(self) -> Tuple[str, str]:
        """
        Generate both standard and visual CVs.
        
        Returns:
            Tuple of (standard_cv, visual_cv, harvard_cv) content
        """
        logger.info("Generating CVs")
        
        try:
            if not self.cv_generator:
                raise ValueError("Content must be analyzed first")
            
            # Generate both CVs
            standard_cv_pdf  = self.cv_generator.generate_standard_cv()
            visual_cv_pdf = self.cv_generator.generate_visual_cv()
            harvard_cv_pdf = self.cv_generator.generate_harvard_cv()
            logger.info("CV generation complete")
            return standard_cv_pdf, visual_cv_pdf, harvard_cv_pdf
        except Exception as e:
            logger.error(f"Error generating CVs: {str(e)}", exc_info=True)
            raise

    # def generate_pdf_cvs(self) -> tuple[str, str]:
    #     """
    #     Generate both standard and visual CVs in PDF format.
        
    #     Returns:
    #         Tuple of (standard_cv_pdf_path, visual_cv_pdf_path)
    #     """
    #     logger.info("Generating PDF CVs")
        
    #     try:
    #         if not self.cv_generator:
    #             raise ValueError("Content must be analyzed first")
            
    #         # Generate PDF CVs
    #         standard_cv_pdf, visual_cv_pdf = self.cv_generator.generate_pdf_cvs()
            
    #         logger.info("PDF CV generation complete")
    #         return standard_cv_pdf, visual_cv_pdf
    #     except Exception as e:
    #         logger.error(f"Error generating PDF CVs: {str(e)}", exc_info=True)
    #         raise
    
    def run_full_workflow(self) -> Tuple[str, str]:
        """
        Run the complete workflow from document processing to CV generation.
            
        Returns:
            Tuple of (standard_cv_path, visual_cv_path, harvard_cv_path)
        """
        logger.info("Running full CV generation workflow")
        
        try:
            # Create output directory if it doesn't exist
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            
            # Step 1: Process input documents
            self.process_input_documents()
            
            # Step 2: Analyze content
            analysis_results = self.analyze_content()
            
            # Step 3: Generate CVs using LaTeX generator
            from core.latex_cv_generator import LaTeXCVGenerator
            latex_generator = LaTeXCVGenerator(analysis_results, self.document_processor.extracted_data)
            standard_cv_pdf, visual_cv_pdf, harvard_cv_pdf = latex_generator.generate_cvs()
            
            # Step 4: Save processed data to JSON file
            processed_data = {
                "extracted_data": self.document_processor.extracted_data.dict(),
                "analysis_results": analysis_results.dict()
            }
            
            output_file = os.path.join(OUTPUT_DIR, "processed_data.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Processed data saved to {output_file}")
            logger.info("Full workflow completed successfully")
            return standard_cv_pdf, visual_cv_pdf, harvard_cv_pdf           
        except Exception as e:
            logger.error(f"Error in full workflow: {str(e)}", exc_info=True)
            raise