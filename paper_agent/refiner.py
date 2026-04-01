import os
import logging
from benchmark_collection.utils.openai_utils import GPTClient
from paper_agent.review_utils import clean_markdown_response

class Refiner:
    def __init__(self, research_field, instance_id, gpt_model='gpt-4o-2024-05-13'):
        self.project_dir = f"{research_field}/target_sections/{instance_id}"
        self.gpt_client = GPTClient(model=gpt_model)
        self.section_mapping = {
            "introduction": "introduction.tex",
            "related work": "related_work.tex",
            "methodology": "methodology.tex",
            "method": "methodology.tex",
            "proposed method": "methodology.tex",
            "experiments": "experiments.tex",
            "experiment": "experiments.tex",
            "conclusion": "conclusion.tex",
            "abstract": "abstract.tex"
        }

    async def refine_paper(self, review_report):
        recommendations = review_report.get("specific_recommendations_for_revision", [])

        for rec in recommendations:
            section_name = rec.get("section", "").lower()
            comment = rec.get("comment", "")

            target_file = None
            # Try to match key in section name
            for key, filename in self.section_mapping.items():
                if key in section_name:
                    target_file = filename
                    break

            # Fallback: try to find a file that matches the section name directly
            if not target_file and os.path.exists(self.project_dir):
                for filename in os.listdir(self.project_dir):
                    if filename.endswith(".tex") and filename.replace(".tex", "").lower() in section_name:
                        target_file = filename
                        break

            if target_file:
                await self._revise_section(target_file, comment)
            else:
                logging.warning(f"Could not find target file for section: {section_name}")

    async def _revise_section(self, filename, comment):
        # Prevent writing outside of project directory
        if os.path.dirname(filename):
             logging.warning(f"Skipping refinement for file with directory component: {filename}")
             return

        filepath = os.path.join(self.project_dir, filename)

        # Verify filepath is strictly within project_dir (redundant but safe)
        if not os.path.abspath(filepath).startswith(os.path.abspath(self.project_dir)):
             logging.warning(f"Path traversal detected in refiner: {filepath}")
             return

        if not os.path.exists(filepath):
            logging.warning(f"File not found: {filepath}")
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        prompt = f"""You are an expert academic writer.
You are refining a section of a paper based on a reviewer's comment.

Current Content ({filename}) (Delimited by <CONTENT>):
<CONTENT>
{content}
</CONTENT>

Reviewer's Comment (Delimited by <COMMENT>):
<COMMENT>
{comment}
</COMMENT>

Task:
Rewrite the content to address the reviewer's comment.
Maintain the LaTeX format.
Do not remove valid technical content unless asked to.
Improve clarity and flow.
Ensure the output is valid LaTeX.

Output ONLY the revised LaTeX content.
"""
        response = await self.gpt_client.chat(prompt=prompt)

        if not response:
             logging.error("GPTClient returned None during refinement")
             return

        response = clean_markdown_response(response)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response.strip())

        logging.info(f"Revised {filename} based on feedback.")
