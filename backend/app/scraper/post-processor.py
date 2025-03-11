import pandas as pd
import re
import json
import csv
import os
from typing import List, Dict, Any, Optional
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("job-processor")

def clean_job_data(input_csv: str, output_json: str) -> List[Dict[str, Any]]:
    """
    Process job data from JobSpy CSV export to structured JSON format for the internship tracker app
    
    Args:
        input_csv: Path to input CSV file from JobSpy
        output_json: Path to output JSON file
        
    Returns:
        List of processed job dictionaries
    """
    # Try multiple approaches to load the CSV file due to potential parsing issues
    df = None
    errors = []
    
    for attempt, params in enumerate([
        {'escapechar': '\\'},  # Try with escape character
        {'quoting': csv.QUOTE_NONE, 'escapechar': '\\'},  # Try with no quoting
        {'quoting': csv.QUOTE_MINIMAL},  # Try with minimal quoting
        {'engine': 'python'},  # Try with python engine
        {}  # Try default params as last resort
    ]):
        try:
            logger.info(f"Attempt {attempt+1} to read CSV with params: {params}")
            df = pd.read_csv(input_csv, **params)
            logger.info(f"Success! Loaded CSV with {len(df)} rows")
            break
        except Exception as e:
            errors.append(f"Attempt {attempt+1}: {str(e)}")
            continue
    
    if df is None:
        error_msg = f"Failed to load CSV file with multiple methods. Errors: {errors}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Log column names for debugging
    logger.info(f"CSV columns: {', '.join(df.columns)}")
    
    # Filter for USA jobs only
    usa_pattern = r'United States|USA|U\.S\.|US$|CA$|NY$|TX$|FL$|IL$|PA$|OH$|GA$|NC$|MI$|NJ$|VA$|WA$|AZ$|MA$|TN$|IN$|MO$|MD$|WI$|CO$|MN$|SC$|AL$|LA$|KY$|OR$|OK$|CT$|UT$|IA$|NV$|AR$|MS$|KS$|NM$|NE$|WV$|ID$|HI$|NH$|ME$|MT$|RI$|DE$|SD$|ND$|AK$|VT$|WY$'
    
    try:
        # Make sure location column exists
        if 'location' not in df.columns:
            logger.warning("No 'location' column found, processing all jobs")
            usa_df = df
        else:
            usa_df = df[df['location'].str.contains(usa_pattern, regex=True, na=False)]
            logger.info(f"Found {len(usa_df)} USA jobs out of {len(df)} total jobs")
            
            # If no USA jobs found, try a less strict filter
            if len(usa_df) == 0:
                logger.warning("No USA jobs found with strict filtering, using less strict filter")
                usa_df = df[df['location'].notna()]
                logger.info(f"Using {len(usa_df)} jobs with valid locations")
    except Exception as e:
        logger.error(f"Error filtering by location: {e}")
        # If we can't filter, use all jobs
        usa_df = df
        logger.info(f"Processing all {len(df)} jobs without filtering")
    
    # Initialize list to store processed jobs
    processed_jobs = []
    errors_count = 0
    
    # Process each job
    for idx, job in usa_df.iterrows():
        try:
            processed_job = process_job(job)
            if processed_job:
                processed_jobs.append(processed_job)
        except Exception as e:
            errors_count += 1
            logger.error(f"Error processing job at index {idx}: {e}")
            continue
    
    if errors_count > 0:
        logger.warning(f"Encountered {errors_count} errors while processing jobs")
    
    # Save to JSON file
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({"jobs": processed_jobs}, f, indent=4, ensure_ascii=False)
    
    logger.info(f"Successfully processed {len(processed_jobs)} jobs and saved to {output_json}")
    return processed_jobs

def process_job(job: pd.Series) -> Optional[Dict[str, Any]]:
    """Process a single job row into the required format"""
    
    # ONLY PROCESS JOB WITH job_url_direct FIELD NOT EMPTY. AKA CHECK THAT job_url_direct != ""
    if job['job_url_direct'] == "" or job['job_url_direct'] is None or pd.isna(job['job_url_direct']):
        logger.debug("Skipping job without direct URL")
        return None

    # Get the job URL
    job_url = ""
    if 'job_url_direct' in job and pd.notna(job['job_url_direct']) and job['job_url_direct']:
        job_url = job['job_url_direct']
    elif 'job_url' in job and pd.notna(job['job_url']):
        job_url = job['job_url']
        
    if not job_url:
        logger.debug("Skipping job without URL")
        return None
    
    # Get the description safely
    description = ""
    if 'description' in job and pd.notna(job['description']):
        description = str(job['description'])
    
    # Get the job title
    job_title = str(job['title']) if 'title' in job and pd.notna(job['title']) else ""
    
    # Skip non-internship jobs if they don't match criteria
    role_type = determine_role_type(job, description)
    if role_type != "Internship" and not is_entry_level(job_title, description):
        logger.debug(f"Skipping non-internship/non-entry level job: {job_title}")
        return None
    
    # Extract job details to match the specified output format
    job_details = {
        "job_title": job_title,
        "location": str(job['location']) if 'location' in job and pd.notna(job['location']) else "",
        "role_type": role_type,
        "category": determine_category(job, description),
        "summary": extract_summary(description),
        "responsibilities": extract_responsibilities(description),
        "minimum_qualifications": extract_minimum_qualifications(description),
        "preferred_qualifications": extract_preferred_qualifications(description),
        # Additional fields not in the example but useful for the app
        "company": str(job['company']) if 'company' in job and pd.notna(job['company']) else "",
        "job_url": job_url,
        "date_posted": str(job['date_posted']) if 'date_posted' in job and pd.notna(job['date_posted']) else ""
    }
    
    return job_details

def determine_role_type(job: pd.Series, description: str) -> str:
    """Determine the role type (Internship, Full-time, etc.)"""
    # Extract values safely
    job_title = str(job['title']).lower() if 'title' in job and pd.notna(job['title']) else ""
    job_type = str(job['job_type']).lower() if 'job_type' in job and pd.notna(job['job_type']) else ""
    description_lower = description.lower() if description else ""
    
    # Check for internship indicators
    internship_patterns = ['intern', 'internship', 'co-op']
    
    # Check title first
    for pattern in internship_patterns:
        if pattern in job_title:
            return "Internship"
    
    # Check if title has year with seasonal terms
    if ('2025' in job_title or '2026' in job_title) and ('summer' in job_title or 'spring' in job_title or 'fall' in job_title):
        return "Internship"
    
    # Check job_type if available
    if job_type:
        for pattern in internship_patterns:
            if pattern in job_type:
                return "Internship"
    
    # Check description as a fallback
    for pattern in internship_patterns:
        if pattern in description_lower:
            # Check if it's specifically mentioning internship program
            context_matches = re.findall(r'\b(?:summer|spring|fall)?\s*intern(?:ship)?\b', description_lower)
            if context_matches:
                return "Internship"
    
    # Default based on title patterns
    if 'part-time' in job_title or 'part time' in job_title:
        return "Part-time"
    elif 'contract' in job_title:
        return "Contract"
    
    # Default to Full-time if nothing else matches
    return "Full-time"

def is_entry_level(job_title: str, description: str) -> bool:
    """Determine if a job is entry level even if not an internship"""
    job_title_lower = job_title.lower()
    description_lower = description.lower()
    
    entry_level_patterns = [
        'entry level', 'entry-level', 'junior', 'jr.', 'associate', 'new grad', 
        'recent graduate', 'university graduate', 'campus hire', 'rotational program',
        'early career', 'graduate program'
    ]
    
    # Check title
    for pattern in entry_level_patterns:
        if pattern in job_title_lower:
            return True
    
    # Check description
    entry_level_score = 0
    for pattern in entry_level_patterns:
        if pattern in description_lower:
            entry_level_score += 1
    
    # Look for 0-2 years experience requirements
    exp_patterns = [
        r'0-1 years?', r'0-2 years?', r'1-2 years?', 
        r'no experience required', r'no prior experience',
        r'entry level', r'new graduates?', r'recent graduates?'
    ]
    
    for pattern in exp_patterns:
        if re.search(pattern, description_lower):
            entry_level_score += 2
    
    return entry_level_score >= 2

def determine_category(job: pd.Series, description: str) -> str:
    """Determine the job category"""
    # Extract values safely
    job_title = str(job['title']).lower() if 'title' in job and pd.notna(job['title']) else ""
    job_function = str(job['job_function']).lower() if 'job_function' in job and pd.notna(job['job_function']) else ""
    description_lower = description.lower() if description else ""
    
    # Define category patterns with weighted terms
    categories = {
        "Software": {
            'primary': ['software', 'developer', 'swe', 'web developer', 'mobile developer', 'full stack'],
            'secondary': ['programming', 'coding', 'frontend', 'backend', 'fullstack', 'web', 'app'],
            'languages': ['java', 'python', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin']
        },
        "Hardware": {
            'primary': ['hardware', 'electrical engineer', 'mechanical engineer'],
            'secondary': ['circuit', 'electronics', 'pcb', 'fpga', 'asic', 'embedded'],
            'specific': ['microcontroller', 'signal processing', 'power systems', 'vlsi']
        },
        "Data": {
            'primary': ['data scientist', 'data engineer', 'machine learning engineer'],
            'secondary': ['data analyst', 'analytics', 'machine learning', 'ml', 'ai', 'artificial intelligence', 'data science'],
            'specific': ['statistics', 'big data', 'tensorflow', 'pytorch', 'nlp']
        },
        "Legal": {
            'primary': ['legal intern', 'legal assistant', 'paralegal'],
            'secondary': ['law', 'attorney', 'counsel', 'compliance', 'contract'],
            'specific': ['intellectual property', 'patent', 'regulatory']
        },
        "Research": {
            'primary': ['research intern', 'research assistant', 'research associate'],
            'secondary': ['r&d', 'scientist', 'phd', 'laboratory', 'lab'],
            'specific': ['investigation', 'experimental']
        }
    }
    
    # Score system for category matching
    category_scores = {cat: 0 for cat in categories.keys()}
    
    # Check job function first (highest weight)
    if job_function:
        for category, patterns in categories.items():
            for pattern_type, pattern_list in patterns.items():
                for pattern in pattern_list:
                    if pattern in job_function:
                        weight = 5 if pattern_type == 'primary' else 3 if pattern_type == 'secondary' else 2
                        category_scores[category] += weight
    
    # Check title (high weight)
    for category, patterns in categories.items():
        for pattern_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if pattern in job_title:
                    weight = 4 if pattern_type == 'primary' else 2 if pattern_type == 'secondary' else 1
                    category_scores[category] += weight
    
    # Check description (lower weight)
    for category, patterns in categories.items():
        for pattern_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if pattern in description_lower:
                    weight = 2 if pattern_type == 'primary' else 1 if pattern_type == 'secondary' else 0.5
                    category_scores[category] += weight
    
    # Check for tie breakers or low confidence
    max_score = max(category_scores.values()) if category_scores else 0
    if max_score > 0:
        # Find category with highest score
        for category, score in category_scores.items():
            if score == max_score:
                return category
    
    # Special case for software engineering roles
    if ('engineer' in job_title and any(lang in description_lower for lang in categories['Software']['languages'])):
        return "Software"
    
    # Default to Engineering if no clear match or low confidence
    return "Engineering"

def extract_summary(description: str) -> str:
    """Extract a summary from the job description"""
    if not description:
        return ""
    
    # Try to find sections with these headers
    intro_patterns = [
        r'(?:^|\n)(?:##?\s*|[*•]\s*)?(?:Introduction|About|Overview|Summary|About the Role|Job Summary|Position Summary)[:\s]*\n+((?:.+\n)+?)(?:\n(?:##?\s*|[*•]\s*)?[A-Z]|\Z)',
        r'(?:^|\n)(?:##?\s*|[*•]\s*)?(?:Description)[:\s]*\n+((?:.+\n)+?)(?:\n(?:##?\s*|[*•]\s*)?[A-Z]|\Z)'
    ]
    
    for pattern in intro_patterns:
        match = re.search(pattern, description, re.IGNORECASE | re.MULTILINE)
        if match:
            # Found a section, clean it up
            summary = match.group(1).strip()
            # Remove excessive whitespace and newlines
            summary = re.sub(r'\s+', ' ', summary)
            # Remove markdown formatting
            summary = re.sub(r'[*_#\\]+', '', summary)
            # Return up to 500 characters
            return summary[:500] + ("..." if len(summary) > 500 else "")
    
    # If no matching section found, use first paragraph
    paragraphs = description.split('\n\n')
    if paragraphs:
        # Clean up the first paragraph
        first_para = paragraphs[0].strip()
        # Remove headers
        first_para = re.sub(r'^\s*(?:##?\s*|[*•]\s*)?(?:Description|About|Overview)[:\s]*', '', first_para, flags=re.IGNORECASE)
        # Remove excessive whitespace and newlines
        first_para = re.sub(r'\s+', ' ', first_para)
        # Remove markdown formatting
        first_para = re.sub(r'[*_#\\]+', '', first_para)
        if len(first_para) > 30:  # Only use if it's substantial
            return first_para[:300] + ("..." if len(first_para) > 300 else "")
    
    # Last resort: use first 300 characters of cleaned description
    cleaned_desc = re.sub(r'\s+', ' ', description)
    cleaned_desc = re.sub(r'[*_#\\]+', '', cleaned_desc)
    return cleaned_desc[:300] + ("..." if len(cleaned_desc) > 300 else "")

def extract_section_items(description: str, section_names: List[str]) -> List[str]:
    """Extract items from a section in the job description"""
    if not description:
        return []
    
    # Create pattern to match section headers
    section_pattern = r'(?:^|\n)(?:##?\s*|[*•]\s*)?(' + '|'.join(map(re.escape, section_names)) + r')[:\s]*\n+((?:.+\n)+?)(?:\n(?:##?\s*|[*•]\s*)?[A-Z]|\Z)'
    
    section_text = ""
    matches = list(re.finditer(section_pattern, description, re.IGNORECASE | re.MULTILINE))
    
    if matches:
        for match in matches:
            section_text += "\n" + match.group(2).strip()
    else:
        # Try looser pattern if no matches
        loose_pattern = r'(?:^|\n)(' + '|'.join(map(re.escape, section_names)) + r')[:\s]*\n+((?:.+\n)+?)(?:\n\n|\Z)'
        loose_matches = list(re.finditer(loose_pattern, description, re.IGNORECASE | re.MULTILINE))
        for match in loose_matches:
            section_text += "\n" + match.group(2).strip()
    
    if not section_text:
        return []
    
    # Extract bullet points
    bullet_pattern = r'(?:^|\n)[•*-]\s*(.+?)(?=\n[•*-]|\n\n|\Z)'
    bullet_matches = list(re.finditer(bullet_pattern, section_text, re.MULTILINE))
    
    bullet_points = []
    for match in bullet_matches:
        point = match.group(1).strip()
        # Remove any markdown formatting or excessive whitespace
        point = re.sub(r'\s+', ' ', point)
        point = re.sub(r'[*_#\\]+', '', point)
        if point and len(point) > 5:  # Avoid very short bullets
            bullet_points.append(point)
    
    # If no bullet points found, try to split by newlines
    if not bullet_points:
        lines = [line.strip() for line in section_text.split('\n')]
        for line in lines:
            # Remove any markdown formatting or excessive whitespace
            line = re.sub(r'\s+', ' ', line)
            line = re.sub(r'[*_#\\]+', '', line)
            if line and len(line) > 15:  # Avoid very short lines
                bullet_points.append(line)
    
    # Avoid duplicate bullets
    unique_bullets = []
    for bullet in bullet_points:
        if bullet not in unique_bullets:
            unique_bullets.append(bullet)
    
    return unique_bullets

def extract_responsibilities(description: str) -> List[str]:
    """Extract responsibilities from the job description"""
    section_names = [
        'Key Responsibilities', 'Responsibilities', 'Duties', 'Job Duties', 
        'What You\'ll Do', 'Role Responsibilities', 'Your Responsibilities',
        'What You Will Do', 'What You\'ll Be Doing', 'Essential Functions',
        'Day-to-Day Responsibilities', 'Primary Responsibilities', 'The Role', 
        'Job Description', 'Position Details', 'As an Intern'
    ]
    return extract_section_items(description, section_names)

def extract_minimum_qualifications(description: str) -> List[str]:
    """Extract minimum qualifications from the job description"""
    section_names = [
        'Required', 'Requirements', 'Qualifications', 'Minimum Qualifications', 
        'Required Skills', 'Basic Qualifications', 'Required Qualifications',
        'Must Have', 'Essential Qualifications', 'Education Requirements',
        'Required Experience', 'Basic Requirements', 'Minimum Requirements',
        'Skills Required', 'What You Need', 'What We Require'
    ]
    return extract_section_items(description, section_names)

def extract_preferred_qualifications(description: str) -> List[str]:
    """Extract preferred qualifications from the job description"""
    section_names = [
        'Preferred', 'Preferred Qualifications', 'Nice to Have', 'Desired Skills', 
        'Additional Qualifications', 'Preferred Skills', 'Bonus Points',
        'Desired Experience', 'Preferred Requirements', 'Pluses', 'Ideal Candidate',
        'What Sets You Apart', 'Good to Have', 'Preferred Experience',
        'Nice to Haves', 'Bonus Qualifications', 'Additionally'
    ]
    return extract_section_items(description, section_names)

def main():
    """Main entry point for the script"""
    input_csv = "jobs.csv"  # The CSV file produced by JobSpy
    output_json = "processed_jobs.json"  # The output JSON file
    
    logger.info(f"Starting job data processing from {input_csv}")
    
    if not os.path.exists(input_csv):
        logger.error(f"Input file not found: {input_csv}")
        print(f"Error: Input file not found: {input_csv}")
        return
    
    try:
        processed_jobs = clean_job_data(input_csv, output_json)
        logger.info(f"Successfully processed {len(processed_jobs)} jobs to {output_json}")
        print(f"Successfully processed {len(processed_jobs)} jobs to {output_json}")
    except Exception as e:
        logger.error(f"Error processing job data: {e}", exc_info=True)
        print(f"Error processing job data: {e}")

if __name__ == "__main__":
    main()