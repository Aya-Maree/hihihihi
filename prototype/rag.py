"""
RAG Pipeline for Household Event Planner
Simple Retrieval-Augmented Generation demonstration
"""

import re
from datetime import datetime
from models import Event, Task, HouseholdMember


class DocumentStore:
    """Store events and tasks as documents for retrieval"""

    def __init__(self, household_id):
        self.household_id = household_id
        self.documents = []

    def load_documents(self):
        """Load all events and tasks as documents"""
        self.documents = []

        # Load events
        events = Event.find_by_household(self.household_id)
        for event in events:
            doc = {
                'id': f"event_{event.event_id}",
                'type': 'event',
                'title': event.title,
                'content': f"{event.title}. {event.description or ''} {event.location or ''}",
                'datetime': event.start_time,
                'source': event
            }
            self.documents.append(doc)

        # Load tasks
        tasks = Task.find_by_household(self.household_id)
        for task in tasks:
            doc = {
                'id': f"task_{task.task_id}",
                'type': 'task',
                'title': task.title,
                'content': f"{task.title}. {task.description or ''} Status: {task.status}. Priority: {task.priority}",
                'datetime': task.due_date,
                'source': task
            }
            self.documents.append(doc)

        return self.documents

    def retrieve(self, query, top_k=3):
        """Retrieve relevant documents based on query"""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored_docs = []
        for doc in self.documents:
            score = 0
            # Title match (higher weight)
            if any(word in doc['title'].lower() for word in query_words):
                score += 3
            # Content match
            if any(word in doc['content'].lower() for word in query_words):
                score += 1
            # Type keyword match
            if 'event' in query_lower and doc['type'] == 'event':
                score += 2
            if 'task' in query_lower and doc['type'] == 'task':
                score += 2

            if score > 0:
                scored_docs.append((score, doc))

        # Sort by score and return top_k
        scored_docs.sort(reverse=True, key=lambda x: x[0])
        return [doc for score, doc in scored_docs[:top_k]]


class RAGPipeline:
    """Simple RAG pipeline for querying household events and tasks"""

    def __init__(self, household_id):
        self.document_store = DocumentStore(household_id)
        self.household_id = household_id

    def query(self, user_question):
        """
        Main RAG pipeline:
        1. Load documents
        2. Retrieve relevant docs
        3. Generate response
        """
        # Step 1: Load documents
        docs = self.document_store.load_documents()

        # Step 2: Retrieve relevant documents
        retrieved = self.document_store.retrieve(user_question)

        # Step 3: Generate response
        response = self._generate_response(user_question, retrieved)

        return response

    def _generate_response(self, question, retrieved_docs):
        """Generate a natural language response"""

        if not retrieved_docs:
            return "I couldn't find any events or tasks matching your question."

        # Extract info from retrieved docs
        events = [d for d in retrieved_docs if d['type'] == 'event']
        tasks = [d for d in retrieved_docs if d['type'] == 'task']

        response_parts = []

        # Analyze the question
        question_lower = question.lower()

        # Response based on question type
        if any(word in question_lower for word in ['when', 'date', 'time', 'upcoming']):
            if events:
                response_parts.append("Here are the upcoming events I found:")
                for doc in events:
                    dt = doc['datetime']
                    if isinstance(dt, str):
                        response_parts.append(f"  - {doc['title']}: {dt}")
                    else:
                        response_parts.append(f"  - {doc['title']}: {dt.strftime('%Y-%m-%d %H:%M')}")
            else:
                response_parts.append("No events found.")

        elif any(word in question_lower for word in ['task', 'todo', 'due', 'pending']):
            if tasks:
                response_parts.append("Here are the tasks I found:")
                for doc in tasks:
                    dt = doc['datetime']
                    if dt:
                        if isinstance(dt, str):
                            response_parts.append(f"  - {doc['title']} (Due: {dt}, Status: {doc['source'].status})")
                        else:
                            response_parts.append(f"  - {doc['title']} (Due: {dt.strftime('%Y-%m-%d %H:%M')}, Status: {doc['source'].status})")
                    else:
                        response_parts.append(f"  - {doc['title']} (Status: {doc['source'].status})")
            else:
                response_parts.append("No tasks found.")

        elif any(word in question_lower for word in ['show', 'list', 'all', 'what']):
            if events:
                response_parts.append("Events:")
                for doc in events:
                    response_parts.append(f"  - {doc['title']}")
            if tasks:
                response_parts.append("Tasks:")
                for doc in tasks:
                    response_parts.append(f"  - {doc['title']} [{doc['source'].status}]")

        else:
            # Generic response
            response_parts.append("Here's what I found:")
            for doc in retrieved_docs:
                response_parts.append(f"  - {doc['title']} ({doc['type']})")

        # Add citation
        response_parts.append(f"\n[Cited {len(retrieved_docs)} documents from your household database]")

        return "\n".join(response_parts)


def demo_rag():
    """Demo the RAG pipeline"""
    print("=" * 60)
    print("RAG PIPELINE DEMO")
    print("=" * 60)

    # For demo, we'll need a household
    from database import Database
    db = Database("household_planner.db")

    # Check if we have data
    from models import Household, Event, User

    # Find a user
    user = User.find_by_username("demo")
    if not user:
        print("No demo user found. Please run main.py first to create data.")
        return

    household = Household.find_by_owner(user.user_id)
    if not household:
        print("No household found.")
        return

    print(f"\nUsing household: {household.name}")

    # Initialize RAG
    rag = RAGPipeline(household.household_id)

    # Test questions
    test_questions = [
        "What events do I have?",
        "What tasks are pending?",
        "When is my event?",
    ]

    print("\n" + "-" * 60)
    for question in test_questions:
        print(f"\nUser: {question}")
        print("-" * 40)
        response = rag.query(question)
        print(f"AI: {response}")
        print("-" * 40)


if __name__ == "__main__":
    demo_rag()