import logging
import re
from typing import List
from sqlalchemy.orm import Session
import asyncio

from .. import models
from ..database import SessionLocal

logger = logging.getLogger("janus-ml-processor")


class RequirementProcessor:
    """
    Processor for extracting and summarizing job requirements.
    """

    def __init__(self, db: Session):
        self.db = db

    async def process_jobs(self, limit: int = 50) -> int:
        """
        Process unprocessed jobs (those without requirements summary).

        Args:
            limit: Maximum number of jobs to process at once

        Returns:
            int: Number of jobs processed
        """
        # Get jobs without requirements summary
        jobs = (
            self.db.query(models.Job)
            .filter(
                models.Job.requirements_summary.is_(None),
                models.Job.description.isnot(None),
                models.Job.is_active == True,
            )
            .limit(limit)
            .all()
        )

        if not jobs:
            logger.info("No jobs to process")
            return 0

        logger.info(f"Processing {len(jobs)} jobs")

        count = 0
        for job in jobs:
            try:
                # Extract requirements from job description
                requirements = self._extract_requirements(job.description)

                if requirements:
                    # Format requirements as a bullet-point list
                    formatted_requirements = self._format_requirements(requirements)

                    # Update job with extracted requirements
                    job.requirements_summary = formatted_requirements
                    count += 1

                    logger.info(f"Processed job: {job.id} - {job.title}")
                else:
                    # If no requirements found, set a placeholder
                    job.requirements_summary = "No specific requirements extracted."
                    count += 1

                    logger.info(
                        f"No requirements found for job: {job.id} - {job.title}"
                    )

            except Exception as e:
                logger.error(f"Error processing job {job.id}: {str(e)}")

        # Commit changes
        self.db.commit()

        logger.info(f"Processed {count} jobs")
        return count

    def _extract_requirements(self, description: str) -> List[str]:
        """
        Extract requirements from job description.

        Args:
            description: Job description text

        Returns:
            List[str]: Extracted requirements
        """
        if not description:
            return []

        # Normalize line breaks
        text = description.replace("\r\n", "\n").replace("\r", "\n")

        # Find the requirements section
        requirements_section = self._find_requirements_section(text)
        if not requirements_section:
            return []

        # Extract bullet points or numbered list items
        requirements = self._extract_bullet_points(requirements_section)

        # If no bullet points found, try to extract sentences
        if not requirements:
            requirements = self._extract_sentences(requirements_section)

        # Filter irrelevant requirements
        requirements = self._filter_requirements(requirements)

        # Limit to a reasonable number of requirements
        if len(requirements) > 10:
            requirements = requirements[:10]

        return requirements

    def _find_requirements_section(self, text: str) -> str:
        """
        Find the requirements section in the job description.

        Args:
            text: Job description text

        Returns:
            str: Requirements section text or empty string
        """
        # Common section headers for requirements
        section_headers = [
            r"requirements",
            r"qualifications",
            r"skills required",
            r"what you'll need",
            r"what you need",
            r"required skills",
            r"minimum qualifications",
            r"basic qualifications",
            r"technical skills",
            r"education & experience",
            r"your qualifications",
            r"required experience",
            r"you have",
        ]

        # Look for sections with these headers
        for header in section_headers:
            # Create regex pattern for the header (case insensitive, followed by colon or newline)
            pattern = rf"(?:^|\n)(?:.*?{header}.*?)(?::|\n)"
            match = re.search(pattern, text, re.IGNORECASE)

            if match:
                # Found a match, extract the section
                start_pos = match.end()

                # Find the end of the section (next header or end of text)
                next_header_pattern = (
                    r"(?:^|\n)(?:[A-Z][a-z]+(?: [A-Z][a-z]+)*)(?::|\n)"
                )
                next_header_match = re.search(next_header_pattern, text[start_pos:])

                if next_header_match:
                    end_pos = start_pos + next_header_match.start()
                    section_text = text[start_pos:end_pos].strip()
                else:
                    section_text = text[start_pos:].strip()

                return section_text

        # If no specific section found, try to find requirement-like sentences throughout the text
        return text

    def _extract_bullet_points(self, text: str) -> List[str]:
        """
        Extract bullet points from text.

        Args:
            text: Text to extract bullet points from

        Returns:
            List[str]: Extracted bullet points
        """
        bullet_points = []

        # Common bullet point markers
        bullet_patterns = [
            r"^\s*[\*\-•♦★◊»]+\s+(.+)$",  # Bullets: *, -, •, ♦, ★, ◊, »
            r"^\s*(\d+\.)\s+(.+)$",  # Numbered: 1., 2., etc.
            r"^\s*([A-Za-z]\.)\s+(.+)$",  # Lettered: a., b., etc.
            r"^\s*(\d+\))\s+(.+)$",  # Numbered: 1), 2), etc.
            r"^\s*([A-Za-z]\))\s+(.+)$",  # Lettered: a), b), etc.
        ]

        # Split text into lines
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for bullet patterns
            for pattern in bullet_patterns:
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    if len(match.groups()) == 1:
                        bullet_points.append(match.group(1))
                    else:
                        bullet_points.append(match.group(2))
                    break

        return bullet_points

    def _extract_sentences(self, text: str) -> List[str]:
        """
        Extract sentences from text.

        Args:
            text: Text to extract sentences from

        Returns:
            List[str]: Extracted sentences
        """
        # Simple sentence extraction (split by period)
        sentences = re.split(r"(?<=[.!?])\s+", text)

        # Filter out short sentences and clean
        return [s.strip() for s in sentences if len(s.strip()) > 10]

    def _filter_requirements(self, requirements: List[str]) -> List[str]:
        """
        Filter irrelevant requirements.

        Args:
            requirements: List of potential requirements

        Returns:
            List[str]: Filtered requirements
        """
        filtered = []

        # Keywords that indicate relevant requirements
        relevant_keywords = [
            "degree",
            "experience",
            "knowledge",
            "skill",
            "proficiency",
            "familiar",
            "background",
            "education",
            "graduate",
            "bachelor",
            "master",
            "phd",
            "major",
            "computer science",
            "engineering",
            "programming",
            "software",
            "hardware",
            "coding",
            "development",
            "java",
            "python",
            "c++",
            "javascript",
            "typescript",
            "html",
            "css",
            "sql",
            "nosql",
            "react",
            "angular",
            "vue",
            "node",
            "database",
            "algorithm",
            "data structure",
            "problem solving",
            "communication",
            "teamwork",
            "collaboration",
            "design",
            "testing",
            "git",
            "cloud",
            "aws",
            "azure",
            "gcp",
            "docker",
            "kubernetes",
            "linux",
            "unix",
            "rest",
            "api",
            "web",
            "mobile",
            "frontend",
            "backend",
            "full stack",
            "systems",
            "networking",
            "security",
            "agile",
            "scrum",
            "devops",
            "ci/cd",
            "machine learning",
            "artificial intelligence",
            "deep learning",
            "nlp",
            "computer vision",
            "data science",
            "analytics",
            "statistics",
            "math",
            "mathematics",
            "physics",
            "electrical engineering",
            "fpga",
            "verilog",
            "hdl",
            "asic",
            "embedded",
            "firmware",
            "microcontroller",
            "architecture",
        ]

        for req in requirements:
            req = req.strip()

            # Skip very short requirements
            if len(req) < 5:
                continue

            # Skip requirements that don't contain any relevant keywords
            lower_req = req.lower()
            if not any(keyword in lower_req for keyword in relevant_keywords):
                continue

            # Clean the requirement text
            req = self._clean_requirement(req)

            # Add to filtered list if not already present
            if req and req not in filtered:
                filtered.append(req)

        return filtered

    def _clean_requirement(self, text: str) -> str:
        """
        Clean a requirement text.

        Args:
            text: Requirement text to clean

        Returns:
            str: Cleaned requirement text
        """
        # Remove any leading bullet points or numbers
        text = re.sub(r"^\s*[\*\-•♦★◊»]+\s+", "", text)
        text = re.sub(r"^\s*\d+\.\s+", "", text)
        text = re.sub(r"^\s*[A-Za-z]\.\s+", "", text)
        text = re.sub(r"^\s*\d+\)\s+", "", text)
        text = re.sub(r"^\s*[A-Za-z]\)\s+", "", text)

        # Capitalize first letter
        if text and text[0].islower():
            text = text[0].upper() + text[1:]

        return text.strip()

    def _format_requirements(self, requirements: List[str]) -> str:
        """
        Format requirements as a bullet-point list.

        Args:
            requirements: List of requirements

        Returns:
            str: Formatted requirements as bullet-point list
        """
        # Format as bullet points
        formatted = ""
        for req in requirements:
            formatted += f"• {req}\n"

        return formatted.strip()


async def process_single_batch(limit: int = 50) -> int:
    """
    Process a single batch of jobs.

    Args:
        limit: Maximum number of jobs to process

    Returns:
        int: Number of jobs processed
    """
    db = SessionLocal()
    try:
        processor = RequirementProcessor(db)
        return await processor.process_jobs(limit)
    finally:
        db.close()


async def process_all_jobs() -> int:
    """
    Process all unprocessed jobs.

    Returns:
        int: Total number of jobs processed
    """
    total_processed = 0
    batch_size = 50

    while True:
        processed = await process_single_batch(batch_size)
        total_processed += processed

        if processed < batch_size:
            # No more jobs to process
            break

    return total_processed


if __name__ == "__main__":
    asyncio.run(process_all_jobs())
