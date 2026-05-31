#!/usr/bin/env python3
"""
Unified Data Processing Script for Facebook and LinkedIn Exports
"""
import argparse
import csv
import json
import os
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


SCRIPT_DIR = Path(__file__).parent
PARENT_DIR = SCRIPT_DIR.parent
USER_NAME = "Dmitry Kisselev"  
# Data source configurations
FACEBOOK_CONFIG = {
    "base_dir": PARENT_DIR / "data_raw" / "facebook",
    "sources": {
        "profile": "personal_information/profile_information/profile_information.json",
        "posts": "your_facebook_activity/posts",
        "comments": "your_facebook_activity/comments_and_reactions/comments.json",
        "messages": "your_facebook_activity/messages/inbox",
        "pages_liked": "your_facebook_activity/pages/pages_you've_liked.json",
        "event_responses": "your_facebook_activity/events/your_event_responses.json",
        "group_membership": "your_facebook_activity/groups/your_group_membership_activity.json",
        "saved_items": "your_facebook_activity/saved_items_and_collections/your_saved_items.json",
        "apps_posts": "apps_and_websites_off_of_facebook/posts_from_apps_and_websites.json",
    },
    "default_output": "processed_facebook_data.json"
}

LINKEDIN_CONFIG = {
    "base_dir": PARENT_DIR / "data_raw" / "linkedin",
    "sources": {
        "profile": "Profile.csv",
        "positions": "Positions.csv",
        "education": "Education.csv",
        "skills": "Skills.csv",
        "certifications": "Certifications.csv",
        "recommendations_received": "Recommendations_Received.csv",
        "publications": "Publications.csv",
        "projects": "Projects.csv",
        "comments": "Comments.csv",
        "volunteering": "Volunteering.csv",
    },
    "default_output": "processed_linkedin_data.json"
}

def _timestamp_to_date(timestamp: Optional[float], default: str = "an unknown date") -> str:
    """Convert Unix timestamp to formatted date string."""
    if not timestamp:
        return default
    try:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
    except (ValueError, OSError):
        return default

def parse_linkedin_date(date_str: str) -> Optional[str]:
    """Parse LinkedIn date formats (MM YYYY or YYYY)."""
    if not date_str or date_str == "":
        return None
    try:
        # Try MM YYYY format
        date_obj = datetime.strptime(date_str, "%b %Y")
        return date_obj.strftime("%Y-%m")
    except ValueError:
        try:
            # Try YYYY format
            date_obj = datetime.strptime(date_str, "%Y")
            return date_obj.strftime("%Y")
        except ValueError:
            return date_str

def to_first_person(text: str, user_name: str = USER_NAME) -> str:
    """Convert third-person references to first-person."""
    return (text
            .replace(user_name, "I")
            .replace("You ", "I ")
            .replace("you ", "I ")
            .replace("his own", "my own")
            .replace("his ", "my "))

def safe_load_json(file_path: Path) -> Optional[Dict]:
    """Safely load JSON file with error handling."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Warning: Could not load {file_path}: {e}")
        return None

def safe_load_csv(file_path: Path) -> List[Dict]:
    """Safely load CSV file with error handling."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f))
    except (FileNotFoundError, csv.Error) as e:
        print(f"Warning: Could not load {file_path}: {e}")
        return []

class DataProcessor(ABC):
    """Abstract base class for data processors."""
    
    def __init__(self, base_dir: Path, verbose: bool = False):
        self.base_dir = base_dir
        self.verbose = verbose
        self.chunks = []
    
    def log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"  {message}")
    
    def add_chunk(self, source: str, text: str, timestamp: Optional[float] = None):
        """Add a processed chunk to the collection."""
        chunk = {"source": source, "text": text}
        if timestamp is not None:
            chunk["timestamp"] = timestamp
        self.chunks.append(chunk)
    
    @abstractmethod
    def process(self, sources: Dict[str, str]) -> List[Dict]:
        """Process all data sources and return chunks."""
        pass

class FacebookProcessor(DataProcessor):
    """Facebook data processor."""
    
    def process_profile(self, file_path: Path):
        """Process Facebook profile information."""
        data = safe_load_json(file_path)
        if not data:
            return
        
        profile = data.get("profile_v2", {})
        if not profile:
            return
        
        # Name
        if profile.get("name"):
            self.add_chunk("profile_information.json", 
                          f"My name is {profile['name'].get('full_name')}.")
        
        # Birthday
        if profile.get("birthday"):
            bday = profile['birthday']
            self.add_chunk("profile_information.json",
                          f"I was born on {bday.get('month')}/{bday.get('day')}/{bday.get('year')}.")
        
        # Gender
        if profile.get("gender"):
            self.add_chunk("profile_information.json",
                          f"I am {profile['gender'].get('gender_option', '').lower()}.")
        
        # Current City
        if profile.get("current_city"):
            self.add_chunk("profile_information.json",
                          f"I live in {profile['current_city'].get('name')}.")
        
        # Hometown
        if profile.get("hometown"):
            self.add_chunk("profile_information.json",
                          f"My hometown is {profile['hometown'].get('name')}.")
        
        # Relationship
        if profile.get("relationship"):
            rel = profile['relationship']
            text = f"I am {rel.get('status')}."
            if rel.get('partner'):
                text += f" to {rel.get('partner')}."
            self.add_chunk("profile_information.json", text)
        
        # Education
        for exp in profile.get("education_experiences", []):
            self.add_chunk("profile_information.json",
                          f"I studied at {exp.get('name')}.")
        
        # Work
        for exp in profile.get("work_experiences", []):
            self.add_chunk("profile_information.json",
                          f"I worked at {exp.get('employer')}.")
    
    def process_posts(self, directory_path: Path):
        """Process all JSON files in the posts directory."""
        if not directory_path.exists():
            return
        
        for file_path in directory_path.rglob("*.json"):
            data = safe_load_json(file_path)
            if not data or not isinstance(data, list):
                continue
            
            for post in data:
                timestamp = post.get("timestamp")
                post_data = post.get("data", [])
                post_text = next((item.get("post") for item in post_data if "post" in item), None)
                
                if post_text:
                    self.add_chunk(file_path.name,
                                  f"On {_timestamp_to_date(timestamp)}, I posted: {post_text}",
                                  timestamp)
    
    def process_comments(self, file_path: Path):
        """Process comments."""
        data = safe_load_json(file_path)
        if not data:
            return
        
        for comment_entry in data.get("comments_v2", []):
            timestamp = comment_entry.get("timestamp")
            title = comment_entry.get("title", "commented on something.")
            
            # Convert to first person
            context = to_first_person(title)
            if "commented on" not in context.lower():
                context = "I commented on something."
            
            comment_data = comment_entry.get("data", [])
            comment_text = next((item["comment"].get("comment") 
                               for item in comment_data 
                               if "comment" in item and "comment" in item["comment"]), None)
            
            if comment_text:
                self.add_chunk(file_path.name,
                              f"On {_timestamp_to_date(timestamp)}, {context}: \"{comment_text}\"",
                              timestamp)
    
    def process_messages(self, directory_path: Path):
        """Process all message files in the inbox."""
        if not directory_path.exists():
            return
        
        for file_path in directory_path.rglob("message_1.json"):
            data = safe_load_json(file_path)
            if not data:
                continue
            
            for message in data.get("messages", []):
                # Only process messages from the user
                if message.get("sender_name") != USER_NAME:
                    continue
                
                timestamp_ms = message.get("timestamp_ms")
                timestamp = timestamp_ms / 1000 if timestamp_ms else None
                content = message.get("content")
                
                if content:
                    self.add_chunk("messages",
                                  f"On {_timestamp_to_date(timestamp)}, I sent a message: \"{content}\"",
                                  timestamp)
    
    def process_list_items(self, file_path: Path, data_key: str, item_type: str, 
                          name_key: str = "name", add_prefix: str = ""):
        """Generic processor for list-based JSON files (pages, events, groups, etc.)."""
        data = safe_load_json(file_path)
        if not data:
            return
        
        items = data.get(data_key, [])
        if isinstance(items, dict):
            # Handle nested structure (e.g., event_responses)
            items = items.get("events_joined", []) + items.get("events_declined", [])
        
        for item in items:
            timestamp = item.get("timestamp") or item.get("start_timestamp")
            name = item.get(name_key, "")
            description = item.get("description", "")[:200] if item.get("description") else ""
            
            if name:
                text = f"{add_prefix}{name}"
                if description:
                    text += f". Description: {description}"
                
                full_text = f"On {_timestamp_to_date(timestamp)}, {text}" if timestamp else text
                self.add_chunk(file_path.name, full_text, timestamp)
    
    def process_group_membership(self, file_path: Path):
        """Process group membership activity."""
        data = safe_load_json(file_path)
        if not data:
            return
        
        for group_entry in data.get("groups_joined_v2", []):
            timestamp = group_entry.get("timestamp")
            title = group_entry.get("title", "")
            group_data = group_entry.get("data", [])
            
            # Extract group name
            group_name = group_data[0].get("name", "") if group_data else ""
            
            # Convert to first person
            text = to_first_person(title)
            if group_name:
                if "became a member" in title:
                    text = f"I joined the group '{group_name}'."
                elif "stopped being a member" in title:
                    text = f"I left the group '{group_name}'."
            
            self.add_chunk(file_path.name,
                          f"On {_timestamp_to_date(timestamp)}, {text}",
                          timestamp)
    
    def process_saved_items(self, file_path: Path):
        """Process saved items."""
        data = safe_load_json(file_path)
        if not data:
            return
        
        for save_entry in data.get("saves_v2", []):
            timestamp = save_entry.get("timestamp")
            title = to_first_person(save_entry.get("title", ""))
            
            # Extract description or link name
            attachments = save_entry.get("attachments", [])
            description = ""
            link_name = ""
            
            for attachment in attachments:
                for data_item in attachment.get("data", []):
                    if "media" in data_item and "description" in data_item["media"]:
                        description = data_item["media"]["description"][:200]
                    elif "external_context" in data_item:
                        link_name = data_item["external_context"].get("name", "")
            
            text = title
            if description:
                text += f" Description: {description}"
            elif link_name:
                text += f" Link: {link_name}"
            
            self.add_chunk(file_path.name,
                          f"On {_timestamp_to_date(timestamp)}, {text}",
                          timestamp)
    
    def process_apps_posts(self, file_path: Path):
        """Process posts from apps and websites."""
        data = safe_load_json(file_path)
        if not data:
            return
        
        for post in data.get("app_posts_v2", []):
            timestamp = post.get("timestamp")
            title = to_first_person(post.get("title", ""))
            
            self.add_chunk(file_path.name,
                          f"On {_timestamp_to_date(timestamp)}, {title}",
                          timestamp)
    
    def process(self, sources: Dict[str, str]) -> List[Dict]:
        """Process all Facebook data sources."""
        self.chunks = []
        
        processors = {
            "profile": self.process_profile,
            "posts": self.process_posts,
            "comments": self.process_comments,
            "messages": self.process_messages,
            "group_membership": self.process_group_membership,
            "saved_items": self.process_saved_items,
            "apps_posts": self.process_apps_posts,
        }
        
        # Special handling for list-based items
        list_processors = {
            "pages_liked": ("page_likes_v2", "I like the page '", "name"),
            "event_responses": ("event_responses_v2", "I joined the event '", "name"),
        }
        
        for source_name, source_path in sources.items():
            file_path = self.base_dir / source_path
            
            self.log(f"Processing {source_name}...")
            
            if source_name in processors:
                processors[source_name](file_path)
            elif source_name in list_processors:
                data_key, prefix, name_key = list_processors[source_name]
                self.process_list_items(file_path, data_key, source_name, name_key, prefix)
            else:
                self.log(f"No processor for {source_name}, skipping")
        
        return self.chunks


class LinkedInProcessor(DataProcessor):
    """LinkedIn data processor."""
    
    def process_profile(self, file_path: Path):
        """Process LinkedIn profile."""
        rows = safe_load_csv(file_path)
        for row in rows:
            # Name
            first_name = row.get('First Name', '')
            last_name = row.get('Last Name', '')
            if first_name and last_name:
                self.add_chunk("profile", f"My name is {first_name} {last_name}.")
            
            # Headline
            if headline := row.get('Headline', ''):
                self.add_chunk("profile", f"My professional headline is: {headline}")
            
            # Summary
            if summary := row.get('Summary', ''):
                self.add_chunk("profile", f"My professional summary: {summary}")
            
            # Industry
            if industry := row.get('Industry', ''):
                self.add_chunk("profile", f"I work in the {industry} industry.")
            
            # Location
            if location := row.get('Geo Location', ''):
                self.add_chunk("profile", f"I am based in {location}.")
    
    def process_positions(self, file_path: Path):
        """Process work positions."""
        rows = safe_load_csv(file_path)
        for row in rows:
            company = row.get('Company Name', '')
            title = row.get('Title', '')
            description = row.get('Description', '')
            location = row.get('Location', '')
            started = parse_linkedin_date(row.get('Started On', ''))
            finished = parse_linkedin_date(row.get('Finished On', ''))
            
            if company and title:
                text = f"I worked as {title} at {company}"
                if location:
                    text += f" in {location}"
                if started:
                    text += f" from {started}"
                    text += f" to {finished}" if finished else " to present"
                text += "."
                if description:
                    text += f" {description}"
                
                self.add_chunk("positions", text)
    
    def process_education(self, file_path: Path):
        """Process education history."""
        rows = safe_load_csv(file_path)
        for row in rows:
            school = row.get('School Name', '')
            degree = row.get('Degree Name', '')
            started = parse_linkedin_date(row.get('Start Date', ''))
            finished = parse_linkedin_date(row.get('End Date', ''))
            
            if school:
                text = f"I studied at {school}"
                if degree:
                    text += f", earning a {degree}"
                if started and finished:
                    text += f" from {started} to {finished}"
                elif started:
                    text += f" starting in {started}"
                text += "."
                
                self.add_chunk("education", text)
    
    def process_skills(self, file_path: Path):
        """Process skills."""
        rows = safe_load_csv(file_path)
        skills_list = [row.get('Name', '') for row in rows if row.get('Name', '')]
        
        # Group skills into chunks of 10
        for i in range(0, len(skills_list), 10):
            skill_group = skills_list[i:i+10]
            self.add_chunk("skills", f"My skills include: {', '.join(skill_group)}.")
    
    def process_certifications(self, file_path: Path):
        """Process certifications."""
        rows = safe_load_csv(file_path)
        for row in rows:
            name = row.get('Name', '')
            authority = row.get('Authority', '')
            started = parse_linkedin_date(row.get('Started On', ''))
            finished = parse_linkedin_date(row.get('Finished On', ''))
            
            if name:
                text = f"I obtained the certification: {name}"
                if authority:
                    text += f" from {authority}"
                if started:
                    text += f" in {started}"
                if finished:
                    text += f" (expires {finished})"
                text += "."
                
                self.add_chunk("certifications", text)
    
    def process_recommendations_received(self, file_path: Path):
        """Process recommendations."""
        rows = safe_load_csv(file_path)
        for row in rows:
            first_name = row.get('First Name', '')
            last_name = row.get('Last Name', '')
            job_title = row.get('Job Title', '')
            company = row.get('Company', '')
            text = row.get('Text', '')
            
            if text:
                recommender = f"{first_name} {last_name}"
                if job_title or company:
                    recommender += " ("
                    if job_title:
                        recommender += job_title
                    if company:
                        recommender += f" at {company}" if job_title else company
                    recommender += ")"
                
                self.add_chunk("recommendations_received",
                              f"{recommender} wrote about me: \"{text}\"")
    
    def process_publications(self, file_path: Path):
        """Process publications."""
        rows = safe_load_csv(file_path)
        for row in rows:
            name = row.get('Name', '')
            published_on = parse_linkedin_date(row.get('Published On', ''))
            description = row.get('Description', '')
            publisher = row.get('Publisher', '')
            
            if name:
                text = f"I published: {name}"
                if publisher:
                    text += f" in {publisher}"
                if published_on:
                    text += f" on {published_on}"
                text += "."
                if description:
                    text += f" {description}"
                
                self.add_chunk("publications", text)
    
    def process_projects(self, file_path: Path):
        """Process projects."""
        rows = safe_load_csv(file_path)
        for row in rows:
            title = row.get('Title', '')
            description = row.get('Description', '')
            started = parse_linkedin_date(row.get('Started On', ''))
            finished = parse_linkedin_date(row.get('Finished On', ''))
            
            if title:
                text = f"I worked on a project: {title}"
                if started:
                    text += f" from {started}"
                    text += f" to {finished}" if finished else " to present"
                text += "."
                if description:
                    text += f" {description}"
                
                self.add_chunk("projects", text)
    
    def process_comments(self, file_path: Path):
        """Process comments."""
        rows = safe_load_csv(file_path)
        for row in rows:
            date = row.get('Date', '')
            message = row.get('Message', '')
            
            if message:
                text = f"I commented on LinkedIn: \"{message}\""
                if date:
                    try:
                        date_obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                        text = f"On {date_obj.strftime('%Y-%m-%d')}, {text}"
                    except ValueError:
                        pass
                
                self.add_chunk("comments", text)
    
    def process_volunteering(self, file_path: Path):
        """Process volunteering."""
        rows = safe_load_csv(file_path)
        for row in rows:
            role = row.get('Role', '')
            organization = row.get('Organization', '')
            cause = row.get('Cause', '')
            description = row.get('Description', '')
            
            if role and organization:
                text = f"I volunteered as {role} for {organization}"
                if cause:
                    text += f" supporting {cause}"
                text += "."
                if description:
                    text += f" {description}"
                
                self.add_chunk("volunteering", text)
    
    def process(self, sources: Dict[str, str]) -> List[Dict]:
        """Process all LinkedIn data sources."""
        self.chunks = []
        
        processors = {
            "profile": self.process_profile,
            "positions": self.process_positions,
            "education": self.process_education,
            "skills": self.process_skills,
            "certifications": self.process_certifications,
            "recommendations_received": self.process_recommendations_received,
            "publications": self.process_publications,
            "projects": self.process_projects,
            "comments": self.process_comments,
            "volunteering": self.process_volunteering,
        }
        
        for source_name, source_path in sources.items():
            file_path = self.base_dir / source_path
            
            if not file_path.exists():
                self.log(f"File not found: {file_path}, skipping")
                continue
            
            self.log(f"Processing {source_name}...")
            
            if source_name in processors:
                processors[source_name](file_path)
            else:
                self.log(f"No processor for {source_name}, skipping")
        
        return self.chunks


def main():
    parser = argparse.ArgumentParser(
        description='Process Facebook and/or LinkedIn data exports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process Facebook data
  python process_data.py facebook
  
  # Process LinkedIn data
  python process_data.py linkedin
  
  # Process both
  python process_data.py both
  
  # Custom output file
  python process_data.py facebook --output my_data.json
  
  # Verbose output
  python process_data.py both --verbose
        """
    )
    
    parser.add_argument('source', choices=['facebook', 'linkedin', 'both'],
                       help='Data source to process')
    parser.add_argument('--output', '-o', type=str,
                       help='Output file name (default: processed_<source>_data.json)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Process data based on source
    results = {}
    
    if args.source in ['facebook', 'both']:
        print("=" * 80)
        print("PROCESSING FACEBOOK DATA")
        print("=" * 80)
        
        processor = FacebookProcessor(FACEBOOK_CONFIG['base_dir'], args.verbose)
        chunks = processor.process(FACEBOOK_CONFIG['sources'])
        
        output_file = args.output if args.source == 'facebook' else FACEBOOK_CONFIG['default_output']
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2)
        
        print(f"\n✓ Facebook processing complete!")
        print(f"  Total chunks: {len(chunks)}")
        print(f"  Output: {output_file}")
        
        results['facebook'] = {'chunks': len(chunks), 'output': output_file}
    
    if args.source in ['linkedin', 'both']:
        if args.source == 'both':
            print("\n")
        
        print("=" * 80)
        print("PROCESSING LINKEDIN DATA")
        print("=" * 80)
        
        processor = LinkedInProcessor(LINKEDIN_CONFIG['base_dir'], args.verbose)
        chunks = processor.process(LINKEDIN_CONFIG['sources'])
        
        output_file = args.output if args.source == 'linkedin' else LINKEDIN_CONFIG['default_output']
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2)
        
        print(f"\n✓ LinkedIn processing complete!")
        print(f"  Total chunks: {len(chunks)}")
        print(f"  Output: {output_file}")
        
        results['linkedin'] = {'chunks': len(chunks), 'output': output_file}
    
    # Summary
    if args.source == 'both':
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        for source, data in results.items():
            print(f"{source.capitalize()}: {data['chunks']} chunks → {data['output']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

