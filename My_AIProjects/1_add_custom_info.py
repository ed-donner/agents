"""
STEP 1: Add Custom Information to RAG System
============================================

Use this to add custom information that your chatbot can use to answer questions.

Examples:
- Personal info (height, experience, background)
- Service info (pricing, areas served, hours)
- Equipment details
- Customer testimonials
- Special offers

Run this ANYTIME you want to add new information.
You DON'T need to run this if you're just starting the chatbot.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_system.rag_manager import RAGManager


def main():
    print("=" * 60)
    print("STEP 1: Add Custom Information to Your Chatbot")
    print("=" * 60)
    print("\nThis tool helps you add information that your chatbot can use")
    print("to answer customer questions more accurately.")
    print("\nYou can skip this step if you're just starting the chatbot.")
    print("\n" + "-" * 60)
    
    # Initialize RAG manager
    script_dir = os.path.dirname(os.path.abspath(__file__))
    manager = RAGManager(base_path=script_dir)
    
    while True:
        print("\n" + "=" * 60)
        print("What would you like to do?")
        print("=" * 60)
        print("1. Add personal information (height, experience, etc.)")
        print("2. Add service information (pricing, areas, hours, etc.)")
        print("3. Add equipment/tools information")
        print("4. Add customer testimonials")
        print("5. Add special offers/promotions")
        print("6. View current statistics")
        print("7. Exit (and move to next step)")
        print("=" * 60)
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == "1":
            add_personal_info(manager)
        elif choice == "2":
            add_service_info(manager)
        elif choice == "3":
            add_equipment_info(manager)
        elif choice == "4":
            add_testimonials(manager)
        elif choice == "5":
            add_promotions(manager)
        elif choice == "6":
            view_stats(manager)
        elif choice == "7":
            print("\n" + "=" * 60)
            print("Done! Your information has been saved.")
            print("\nNext step: Run the chatbot")
            print("Command: python 3_run_chatbot.py")
            print("=" * 60)
            break
        else:
            print("\nInvalid choice. Please enter a number from 1-7.")


def add_personal_info(manager):
    """Add personal information."""
    print("\n" + "-" * 60)
    print("Personal Information")
    print("-" * 60)
    
    info_type = input("\nWhat type? (height/experience/background/other): ").strip().lower()
    
    if info_type == "height":
        height = input("Enter your height (e.g., '6 feet 2 inches'): ").strip()
        if height:
            content = f"James Moelling is {height} tall. This height allows him to reach high windows and work efficiently on multi-story buildings without needing additional equipment for most residential properties."
            manager.add_custom_document(content, "james_height", {"type": "personal", "category": "height"})
            print("\nSUCCESS: Height information added!")
    elif info_type == "experience":
        experience = input("Describe your experience: ").strip()
        if experience:
            content = f"James Moelling's experience: {experience}"
            manager.add_custom_document(content, "james_experience", {"type": "personal", "category": "experience"})
            print("\nSUCCESS: Experience information added!")
    elif info_type == "background":
        background = input("Describe your background: ").strip()
        if background:
            content = f"James Moelling's background: {background}"
            manager.add_custom_document(content, "james_background", {"type": "personal", "category": "background"})
            print("\nSUCCESS: Background information added!")
    else:
        title = input("Enter a title for this information: ").strip()
        content = input("Enter the information: ").strip()
        if content:
            doc_id = f"personal_{info_type.replace(' ', '_')}"
            manager.add_custom_document(content, doc_id, {"type": "personal", "category": info_type})
            print(f"\nSUCCESS: {title} added!")


def add_service_info(manager):
    """Add service information."""
    print("\n" + "-" * 60)
    print("Service Information")
    print("-" * 60)
    
    service_type = input("\nWhat service info? (pricing/areas/hours/other): ").strip().lower()
    
    if service_type == "pricing":
        pricing = input("Enter pricing information: ").strip()
        if pricing:
            content = f"Window Wolf pricing: {pricing}"
            manager.add_custom_document(content, "service_pricing", {"type": "service", "category": "pricing"})
            print("\nSUCCESS: Pricing information added!")
    elif service_type == "areas":
        areas = input("Enter service areas: ").strip()
        if areas:
            content = f"Window Wolf serves these areas: {areas}"
            manager.add_custom_document(content, "service_areas", {"type": "service", "category": "areas"})
            print("\nSUCCESS: Service area information added!")
    elif service_type == "hours":
        hours = input("Enter business hours: ").strip()
        if hours:
            content = f"Window Wolf business hours: {hours}"
            manager.add_custom_document(content, "business_hours", {"type": "service", "category": "hours"})
            print("\nSUCCESS: Business hours added!")
    else:
        title = input("Enter a title: ").strip()
        content = input("Enter the information: ").strip()
        if content:
            doc_id = f"service_{service_type.replace(' ', '_')}"
            manager.add_custom_document(content, doc_id, {"type": "service", "category": service_type})
            print(f"\nSUCCESS: {title} added!")


def add_equipment_info(manager):
    """Add equipment information."""
    print("\n" + "-" * 60)
    print("Equipment & Tools")
    print("-" * 60)
    
    equipment = input("\nDescribe your equipment/tools: ").strip()
    if equipment:
        content = f"Window Wolf equipment and tools: {equipment}"
        manager.add_custom_document(content, "equipment_tools", {"type": "equipment"})
        print("\nSUCCESS: Equipment information added!")


def add_testimonials(manager):
    """Add customer testimonials."""
    print("\n" + "-" * 60)
    print("Customer Testimonials")
    print("-" * 60)
    
    testimonial = input("\nEnter customer testimonial: ").strip()
    if testimonial:
        import time
        doc_id = f"testimonial_{int(time.time())}"
        content = f'Customer testimonial: "{testimonial}"'
        manager.add_custom_document(content, doc_id, {"type": "testimonial"})
        print("\nSUCCESS: Testimonial added!")


def add_promotions(manager):
    """Add special offers."""
    print("\n" + "-" * 60)
    print("Special Offers & Promotions")
    print("-" * 60)
    
    offer = input("\nEnter special offer/promotion: ").strip()
    if offer:
        import time
        doc_id = f"promotion_{int(time.time())}"
        content = f"Window Wolf special offer: {offer}"
        manager.add_custom_document(content, doc_id, {"type": "promotion"})
        print("\nSUCCESS: Promotion added!")


def view_stats(manager):
    """View RAG system statistics."""
    print("\n" + "-" * 60)
    print("Current RAG System Statistics")
    print("-" * 60)
    
    stats = manager.get_system_stats()
    print(f"\nTotal chunks in system: {stats.get('total_chunks', 0)}")
    print(f"PDF chunks: {stats.get('pdf_chunks', 0)}")
    print(f"Summary chunks: {stats.get('summary_chunks', 0)}")
    print("\nYour chatbot can now answer questions using all this information!")


if __name__ == "__main__":
    main()

