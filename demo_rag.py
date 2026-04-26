#!/usr/bin/env python3
"""
Demo script showing RAG functionality in PawPal+
Run this to see how the AI retrieves and uses knowledge from local documents.
"""

from pawpal_system import EnhancedScheduler, Owner, Pet, Task
from datetime import datetime, timedelta

def demo_rag_functionality():
    """Demonstrate the RAG (Retrieval-Augmented Generation) capabilities."""

    print("🐾 PawPal+ RAG Demo")
    print("=" * 50)

    # Create owner and pet
    owner = Owner('Demo Owner')
    pet = Pet('Buddy', 'dog')
    owner.add_pet(pet)

    # Create scheduler with RAG
    scheduler = EnhancedScheduler(owner)

    print("\n📚 Knowledge Base Loaded:")
    print(f"Documents found: {len(scheduler.retriever.documents)}")
    for doc_name in scheduler.retriever.documents.keys():
        print(f"  • {doc_name}")

    print("\n🧪 Test Scenario 1: Basic Schedule with Feeding")
    print("-" * 40)

    # Add feeding task
    feeding_task = Task(
        'Feed Buddy breakfast',
        datetime.now() + timedelta(hours=1),
        priority=3
    )
    pet.add_task(feeding_task)

    # Generate AI-enhanced summary
    result = scheduler.generate_ai_enhanced_summary()

    print("Schedule Summary:")
    print(result['summary_text'])

    print("\n🔍 RAG Retrieval Details:")
    for retrieval in result['retrieval_details']:
        print(f"Query: '{retrieval['query']}'")
        print(f"Matched documents: {list(retrieval['matched_documents'].keys())}")
        print(f"Retrieved info: {retrieval['consolidated_info'][:100]}...")
        print()

    print("\n🧪 Test Scenario 2: Adding Conflicts")
    print("-" * 40)

    # Add conflicting task
    grooming_task = Task(
        'Groom Buddy',
        datetime.now() + timedelta(hours=1, minutes=30),  # Overlaps with feeding
        priority=2
    )
    pet.add_task(grooming_task)

    result = scheduler.generate_ai_enhanced_summary()

    print("Schedule with Conflicts:")
    print(result['summary_text'])

    print("\n🔍 RAG Retrieval for Conflicts:")
    for retrieval in result['retrieval_details']:
        if 'conflict' in retrieval['query']:
            print(f"Query: '{retrieval['query']}'")
            print(f"Retrieved guidance: {retrieval['consolidated_info']}")
            break

    print("\n✅ Demo Complete!")
    print("The AI successfully retrieved relevant pet care knowledge")
    print("and provided contextual advice based on the schedule analysis.")

if __name__ == "__main__":
    demo_rag_functionality()