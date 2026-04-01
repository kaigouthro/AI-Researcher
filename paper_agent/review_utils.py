def clean_markdown_response(response):
    """
    Cleans markdown code blocks from the response.
    """
    if not response:
        return ""

    prefixes_to_check = ["```latex", "```tex", "```json", "```"]
    for prefix in prefixes_to_check:
        if response.startswith(prefix):
            response = response[len(prefix):]
            if response.endswith("```"):
                response = response.rsplit("```", 1)[0]
            break
    return response.strip()
