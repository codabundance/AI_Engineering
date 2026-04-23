import argparse
import json
import os
import sys
from urllib.parse import urlparse
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from urllib3 import response
from scraper import fetch_website_contents, fetch_website_links
from IPython.display import display, Markdown


class WebsiteScraperApp:
    def __init__(self) -> None:
        load_dotenv(override=True)
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-5-nano"
        self.openai = OpenAI(api_key=self.api_key) if self.api_key else None

    @staticmethod
    def is_valid_url(url: str) -> bool:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)

    @staticmethod
    def build_parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Fetch website links and optionally page content."
        )
        parser.add_argument(
            "--url",
            required=True,
            help="Company URL to create summary, e.g. https://example.com",
        )
        parser.add_argument(
            "--companyname",
            required=True,
            help="Company Name whose Summary you want to create",
        )
        parser.add_argument(
            "--max-links",
            type=int,
            default=25,
            help="Maximum number of links to return (default: 25)",
        )
        parser.add_argument(
            "--fetch-content",
            action="store_true",
            help="Also fetch textual content for discovered links.",
        )
        parser.add_argument(
            "--save-json",
            default="output.json",
            help="Output file path for JSON results (default: output.json).",
        )
        return parser

    @staticmethod
    def get_link_system_prompt() -> str:
        return f"""
You are a helpful assistant that is given a list of links found on a webpage.
You are able to decide which of the links would be most relevant to include in a brochure about the company,
such as links to an About page, or a Company page, or Careers/Jobs pages.
You should respond in JSON as in this example:

{{
    "links": [
        {{"type": "about page", "url": "https://full.url/goes/here/about"}},
        {{"type": "careers page", "url": "https://another.full.url/careers"}}
    ]
}}
"""

    def get_links_user_prompt(self, url: str) -> str:
        user_prompt = f"""
Here is the list of links on the website {url} -
Please decide which of these are relevant web links for a brochure about the company,
respond with the full https URL in JSON format.
Do not include Terms of Service, Privacy, email links.

Links (some might be relative links):
"""
        links = fetch_website_links(url)
        user_prompt += "\n".join(links)
        return user_prompt

    def select_relevant_links(self, url: str):
        if not self.openai:
            raise RuntimeError("OPENAI_API_KEY not set. Cannot call OpenAI API.")

        try:
            response = self.openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.get_link_system_prompt()},
                    {"role": "user", "content": self.get_links_user_prompt(url)},
                ],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            links = json.loads(content)
            return links
        except Exception as exc:
            raise RuntimeError(f"Failed to select relevant links: {exc}") from exc


    def fetch_page_and_all_relevant_links(self, url: str):
        contents = fetch_website_contents(url)
        relevant_links = self.select_relevant_links(url)
        result = f"## Landing Page:\n\n{contents}\n## Relevant Links:\n"
        for link in relevant_links['links']:
            result += f"\n\n### Link: {link['type']}\n"
            result += fetch_website_contents(link["url"])
        return result

    def get_brochure_user_prompt(self, company_name, url):
        user_prompt = f"""
    You are looking at a company called: {company_name}
    Here are the contents of its landing page and other relevant pages;
    use this information to build a short brochure of the company in markdown without code blocks.\n\n
    """
        user_prompt += self.fetch_page_and_all_relevant_links(url)
        user_prompt = user_prompt[:5_000] # Truncate if more than 5,000 characters
        return user_prompt

    def create_brochure(self, company_name: str, url: str):
        brochure_system_prompt = """
    You are an assistant that analyzes the contents of several relevant pages from a company website
    and creates a short brochure about the company for prospective customers, investors and recruits.
    Respond in markdown without code blocks.
    Include details of company culture, customers and careers/jobs if you have the information.
    """
        response = self.openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role":"system", "content": brochure_system_prompt},
                {"role":"user", "content": self.get_brochure_user_prompt(company_name, url)}
            ],
            stream=True # stream responses back
        )
        result=""
        #handle the stream response
        for chunk in response:
            result += chunk.choices[0].delta.content or ''
            print(result)
        #display(Markdown(result))


    def run(self) -> int:
        if self.api_key:
            print("OPENAI_API_KEY detected in environment.")
        else:
            print("OPENAI_API_KEY not found in .env. Continuing without OpenAI usage.")

        parser = self.build_parser()
        args = parser.parse_args()

        if not self.is_valid_url(args.url):
            print("Error: Please provide a valid URL, e.g. https://example.com")
            return 1

        #links = self.fetch_page_and_all_relevant_links(args.url)
        #print(links)
        self.create_brochure(args.companyname, args.url)
        return 0


def main() -> int:
    app = WebsiteScraperApp()
    return app.run()

if __name__ == "__main__":
    sys.exit(main())
