#!/usr/bin/env python3
"""
CV Generator - Main Application Entry Point

This script processes PDF files (LinkedIn profile, CV, transcript, etc.) 
and generates professional standard and visual CVs using LLMs for the extraction process.
Now with PDF output support following Harvard template format.
"""
import os
import sys
import argparse

from core.workflow import CVGenerationWorkflow
from utils.logger import setup_logger
from config.settings import OUTPUT_DIR

# Set up logger
logger = setup_logger("main", "cv_generator.log")


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Generate professional CVs from PDF documents")
    
    parser.add_argument("--linkedin", help="Path to LinkedIn profile PDF (default: linkedin_profile.pdf)", 
                       default="linkedin_profile.pdf")
    parser.add_argument("--cv", help="Path to current CV PDF (default: current_cv.pdf)", 
                       default="current_cv.pdf")
    parser.add_argument("--transcript", help="Path to meeting transcript PDF (default: meeting_transcript.pdf)", 
                       default="meeting_transcript.pdf")
    parser.add_argument("--goals", help="Path to professional goals PDF (default: professional_goals.pdf)",
                       default="professional_goals.pdf")
    parser.add_argument("--output", help=f"Output directory (default: {OUTPUT_DIR})")
    parser.add_argument("--format", choices=["md", "pdf", "both"], default="both",
                        help="Output format: markdown only, PDF only, or both (default: both)")
    
    return parser.parse_args()


def main():
    """Main application entry point"""
    try:
        # Parse command-line arguments
        args = parse_arguments()
        
        # Update output directory if specified
        if args.output:
            global OUTPUT_DIR
            OUTPUT_DIR = args.output
            os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Initialize workflow
        workflow = CVGenerationWorkflow()
        
        # Run full workflow
        standard_cv_pdf, visual_cv_pdf, harvard_cv_pdf = workflow.run_full_workflow()
        
        # Print output file paths based on format choice
        if args.format in ["md", "both"]:
            print(f"Standard CV saved to: {os.path.join(OUTPUT_DIR, 'standard_cv.md')}")
            print(f"Visual CV saved to: {os.path.join(OUTPUT_DIR, 'visual_cv.md')}")

        if args.format in ["pdf", "both"]:
            print(f"Standard CV PDF saved to: {standard_cv_pdf}")
            print(f"Visual CV PDF saved to: {visual_cv_pdf}")
            print(f"Harvard CV PDF saved to: {harvard_cv_pdf}")
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print("\nOperation cancelled by user")
        return 130  # Standard Unix exit code for SIGINT
    
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())