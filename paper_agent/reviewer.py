import os
import json
import logging
from paper_agent.utils import read_latex_project
from benchmark_collection.utils.openai_utils import GPTClient
from paper_agent.review_utils import clean_markdown_response

class Reviewer:
    def __init__(self, research_field, instance_id, gpt_model='gpt-4o-2024-05-13'):
        self.research_field = research_field
        self.instance_id = instance_id
        self.gpt_client = GPTClient(model=gpt_model)
        self.project_dir = f"{research_field}/target_sections/{instance_id}"

    async def review_paper(self, main_file="iclr2025_conference.tex"):
        try:
            full_content = read_latex_project(self.project_dir, main_file)
        except FileNotFoundError:
            logging.error(f"Could not read project files in {self.project_dir}")
            return None

        # Add delimiters to separate instructions from content
        prompt = f"""You are a reviewer for a top-tier AI conference (e.g., ICLR, NeurIPS).
Please review the following research paper draft.

Paper Content (Delimited by <PAPER_CONTENT>):
<PAPER_CONTENT>
{full_content}
</PAPER_CONTENT>

Your task is to provide a constructive and critical review.
Focus on:
1. Clarity and Structure: Is the paper easy to follow? Are sections logically organized?
2. Technical Correctness: Are the claims supported by evidence? Is the methodology sound?
3. Novelty: Is the contribution clear and significant?
4. Completeness: Are there missing experiments or baselines? (Note: You cannot request new experiments, but point out if the existing ones are insufficient or ill-explained).
5. Writing Quality: check for typos, grammatical errors, and academic tone.

Output your review in the following JSON format:
{{
  "summary": "Brief summary of the paper",
  "strengths": ["List of strengths"],
  "weaknesses": ["List of weaknesses"],
  "detailed_comments": "Detailed comments section by section",
  "specific_recommendations_for_revision": [
     {{
        "section": "Name of section (e.g., Introduction, Methodology)",
        "comment": "Specific instruction on how to improve this part"
     }}
  ],
  "score": "1-10 (10 being best)"
}}

Ensure the output is valid JSON.
"""
        response = await self.gpt_client.chat(prompt=prompt)

        if not response:
            logging.error("GPTClient returned None")
            return None

        response = clean_markdown_response(response)

        try:
            review_data = json.loads(response)

            # Save the review
            output_path = os.path.join(self.project_dir, "review_report.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(review_data, f, indent=2)

            logging.info(f"Review generated and saved to {output_path}")
            return review_data
        except json.JSONDecodeError:
            logging.error("Failed to parse review response as JSON")
            logging.error(response)
            return None
