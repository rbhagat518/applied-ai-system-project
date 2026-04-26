from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional
from enum import Enum
import os
import glob
import re
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pawpal_rag.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Frequency(Enum):
    """Task frequency options."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ONCE = "once"


class CompletionStatus(Enum):
    """Task completion status."""
    PENDING = "pending"
    COMPLETED = "completed"
    OVERDUE = "overdue"


@dataclass
class Task:
    """Represents a single activity for a pet."""
    description: str
    time: datetime
    frequency: Frequency = Frequency.ONCE
    completion_status: CompletionStatus = CompletionStatus.PENDING
    duration: int = 30  # in minutes
    priority: int = 0

    def get_description(self) -> str:
        """Return the task description."""
        return self.description

    def get_time(self) -> datetime:
        """Return the task time."""
        return self.time

    def get_duration(self) -> int:
        """Return the task duration in minutes."""
        return self.duration

    def set_time(self, time: datetime) -> None:
        """Set a new time for the task."""
        self.time = time

    def mark_completed(self):
        """Mark the task as completed and return next recurrence if applicable."""
        self.completion_status = CompletionStatus.COMPLETED

        next_time = self.get_next_occurrence()
        if next_time is None:
            return None

        return Task(
            description=self.description,
            time=next_time,
            frequency=self.frequency,
            completion_status=CompletionStatus.PENDING,
            duration=self.duration,
            priority=self.priority,
        )

    def is_overdue(self) -> bool:
        """Check if the task is overdue."""
        return self.time < datetime.now() and self.completion_status == CompletionStatus.PENDING

    def get_next_occurrence(self) -> Optional[datetime]:
        """Get the next occurrence based on frequency."""
        if self.frequency == Frequency.ONCE:
            return None
        elif self.frequency == Frequency.DAILY:
            return self.time + timedelta(days=1)
        elif self.frequency == Frequency.WEEKLY:
            return self.time + timedelta(weeks=1)
        elif self.frequency == Frequency.MONTHLY:
            # Approximate monthly as 30 days
            return self.time + timedelta(days=30)
        return None


@dataclass
class Pet:
    """Stores pet details and a list of tasks."""
    name: str
    species: str = ""
    age: Optional[int] = None
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to the pet."""
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from the pet."""
        if task in self.tasks:
            self.tasks.remove(task)

    def get_tasks(self) -> List[Task]:
        """Return all tasks for this pet."""
        return self.tasks

    def get_pending_tasks(self) -> List[Task]:
        """Return only pending tasks."""
        return [task for task in self.tasks if task.completion_status == CompletionStatus.PENDING]

    def get_completed_tasks(self) -> List[Task]:
        """Return only completed tasks."""
        return [task for task in self.tasks if task.completion_status == CompletionStatus.COMPLETED]

    def get_overdue_tasks(self) -> List[Task]:
        """Return only overdue tasks."""
        return [task for task in self.tasks if task.is_overdue()]

    def get_name(self) -> str:
        """Return the pet's name."""
        return self.name


@dataclass
class Owner:
    """Manages multiple pets and provides access to all their tasks."""
    name: str
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's collection."""
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from the owner's collection."""
        if pet in self.pets:
            self.pets.remove(pet)

    def get_pets(self) -> List[Pet]:
        """Return all pets owned by this owner."""
        return self.pets

    def get_all_tasks(self) -> List[Task]:
        """Return all tasks across all pets."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks

    def get_all_pending_tasks(self) -> List[Task]:
        """Return all pending tasks across all pets."""
        all_pending = []
        for pet in self.pets:
            all_pending.extend(pet.get_pending_tasks())
        return all_pending

    def get_all_overdue_tasks(self) -> List[Task]:
        """Return all overdue tasks across all pets."""
        all_overdue = []
        for pet in self.pets:
            all_overdue.extend(pet.get_overdue_tasks())
        return all_overdue

    def get_tasks_by_pet(self, pet_name: str) -> List[Task]:
        """Get all tasks for a specific pet by name."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet.get_tasks()
        return []


class Scheduler:
    """The 'Brain' that retrieves, organizes, and manages tasks across pets."""

    def __init__(self, owner: Owner):
        self.owner = owner

    def get_upcoming_tasks(self, hours_ahead: int = 24) -> List[Task]:
        """Get all tasks scheduled within the next specified hours."""
        now = datetime.now()
        cutoff = now + timedelta(hours=hours_ahead)
        upcoming = []

        for task in self.owner.get_all_tasks():
            if task.time >= now and task.time <= cutoff and task.completion_status == CompletionStatus.PENDING:
                upcoming.append(task)

        return sorted(upcoming, key=lambda t: t.time)

    def get_overdue_tasks(self) -> List[Task]:
        """Get all overdue tasks across all pets."""
        return self.owner.get_all_overdue_tasks()

    def organize_tasks_by_priority(self) -> List[Task]:
        """Organize all pending tasks by priority (highest first)."""
        pending_tasks = self.owner.get_all_pending_tasks()
        return sorted(pending_tasks, key=lambda t: (-t.priority, t.time))

    def schedule_task(self, pet: Pet, task: Task) -> None:
        """Schedule a new task for a specific pet."""
        pet.add_task(task)

    def mark_task_completed(self, task: Task, pet: Optional[Pet] = None):
        """Mark a task as completed; if it recurs, add next occurrence back to pet."""
        next_task = task.mark_completed()
        if next_task is not None and pet is not None:
            pet.add_task(next_task)
        return next_task

    def reschedule_task(self, task: Task, new_time: datetime) -> None:
        """Reschedule a task to a new time."""
        task.set_time(new_time)

    def get_pet_schedule(self, pet: Pet, date: Optional[datetime] = None) -> List[Task]:
        """Get all tasks for a specific pet on a given date."""
        if date is None:
            date = datetime.now()

        # Get tasks for the specific date
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        pet_tasks = []
        for task in pet.get_tasks():
            if start_of_day <= task.time < end_of_day and task.completion_status == CompletionStatus.PENDING:
                pet_tasks.append(task)

        return sorted(pet_tasks, key=lambda t: t.time)

    def check_conflicts(self, pet: Pet, date: Optional[datetime] = None) -> List[str]:
        """Check for time conflicts in a pet's schedule for a given date."""
        tasks = self.get_pet_schedule(pet, date)
        conflicts = []

        for i, task1 in enumerate(tasks):
            task1_end = task1.time + timedelta(minutes=task1.duration)
            for task2 in tasks[i+1:]:
                if task2.time < task1_end:
                    conflicts.append(f"Conflict between '{task1.description}' and '{task2.description}'")

        return conflicts

    def generate_daily_summary(self, date: Optional[datetime] = None) -> str:
        """Generate a daily summary of all tasks."""
        if date is None:
            date = datetime.now()

        summary = f"Daily Summary for {date.strftime('%Y-%m-%d')}\n"
        summary += "=" * 40 + "\n\n"

        for pet in self.owner.get_pets():
            pet_tasks = self.get_pet_schedule(pet, date)
            if pet_tasks:
                summary += f"{pet.name} ({pet.species}):\n"
                for task in pet_tasks:
                    status_icon = "✓" if task.completion_status == CompletionStatus.COMPLETED else "○"
                    summary += f"  {status_icon} {task.time.strftime('%H:%M')} - {task.description}\n"
                summary += "\n"

        overdue = self.get_overdue_tasks()
        if overdue:
            summary += "Overdue Tasks:\n"
            for task in overdue:
                summary += f"  ⚠️  {task.description} (was due {task.time.strftime('%Y-%m-%d %H:%M')})\n"

        return summary


class RagRetriever:
    """Retrieves relevant pet care knowledge from local documents."""

    def __init__(self, docs_path: str = "docs"):
        self.docs_path = docs_path
        self.documents = self._load_documents()
        self.retrieval_log = []  # Track all retrievals for evaluation
        logger.info(f"RagRetriever initialized with {len(self.documents)} documents")

    def _load_documents(self) -> dict:
        """Load all markdown documents from the docs directory."""
        documents = {}
        if not os.path.exists(self.docs_path):
            logger.warning(f"Docs path '{self.docs_path}' does not exist")
            return documents

        try:
            for file_path in glob.glob(os.path.join(self.docs_path, "*.md")):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    filename = os.path.basename(file_path)
                    documents[filename] = content
                    logger.debug(f"Loaded document: {filename}")
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
        return documents

    def retrieve(self, query: str) -> dict:
        """Retrieve relevant information based on query keywords with confidence scoring."""
        relevant_info = []
        matched_docs = {}

        try:
            # Simple keyword-based retrieval
            keywords = query.lower().split()

            for doc_name, content in self.documents.items():
                content_lower = content.lower()
                matches = []

                for keyword in keywords:
                    if keyword in content_lower:
                        # Find sentences containing the keyword
                        sentences = re.split(r'[.!?]+', content)
                        for sentence in sentences:
                            if keyword in sentence.lower():
                                matches.append(sentence.strip())

                if matches:
                    matched_docs[doc_name] = matches[:3]  # Limit to 3 matches per doc
                    relevant_info.extend(matches[:3])

            consolidated_info = " ".join(relevant_info) if relevant_info else "No specific guidance found for this situation."
            confidence = self._calculate_confidence(matched_docs)
            
            # Log the retrieval
            retrieval_record = {
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'matched_doc_count': len(matched_docs),
                'total_matches': sum(len(v) for v in matched_docs.values()),
                'confidence': confidence
            }
            self.retrieval_log.append(retrieval_record)
            logger.info(f"Retrieved for query '{query}': {retrieval_record['matched_doc_count']} docs, confidence={confidence}")
            
            return {
                'query': query,
                'matched_documents': matched_docs,
                'consolidated_info': consolidated_info,
                'confidence': confidence
            }
        except Exception as e:
            logger.error(f"Error during retrieval for query '{query}': {e}")
            return {
                'query': query,
                'matched_documents': {},
                'consolidated_info': "No specific guidance found for this situation.",
                'confidence': 0.0
            }

    def _calculate_confidence(self, matched_docs: dict) -> float:
        """Calculate confidence score based on retrieval quality (0-1 scale)."""
        if not matched_docs:
            return 0.0
        
        # Score based on number of documents and matches
        doc_count = len(matched_docs)
        match_count = sum(len(v) for v in matched_docs.values())
        
        # Normalize to 0-1 scale
        confidence = min(1.0, (doc_count + match_count) / 10.0)
        return round(confidence, 2)


class AiCareCoach:
    """Generates AI-powered care advice using retrieved knowledge."""

    def __init__(self, retriever: RagRetriever):
        self.retriever = retriever
        self.advice_log = []  # Track generated advice for evaluation
        logger.info("AiCareCoach initialized")

    def generate_advice(self, schedule_summary: str, conflicts: List[str], overdue: List[str]) -> dict:
        """Generate comprehensive care advice with confidence scoring and logging."""
        advice_parts = []
        retrieval_details = []
        queries_executed = []

        try:
            # Basic schedule advice
            if "feeding" in schedule_summary.lower() or "feed" in schedule_summary.lower():
                retrieval = self.retriever.retrieve("feeding priority")
                advice_parts.append(f"Feeding guidance: {retrieval['consolidated_info']}")
                retrieval_details.append(retrieval)
                queries_executed.append(("feeding priority", retrieval['confidence']))

            if "medication" in schedule_summary.lower() or "med" in schedule_summary.lower():
                retrieval = self.retriever.retrieve("medication priority")
                advice_parts.append(f"Medication guidance: {retrieval['consolidated_info']}")
                retrieval_details.append(retrieval)
                queries_executed.append(("medication priority", retrieval['confidence']))

            # Conflict advice
            if conflicts:
                retrieval = self.retriever.retrieve("conflict resolution")
                advice_parts.append(f"Conflict resolution: {retrieval['consolidated_info']}")
                retrieval_details.append(retrieval)
                queries_executed.append(("conflict resolution", retrieval['confidence']))

            # Overdue advice
            if overdue:
                retrieval = self.retriever.retrieve("overdue tasks")
                advice_parts.append(f"Overdue task handling: {retrieval['consolidated_info']}")
                retrieval_details.append(retrieval)
                queries_executed.append(("overdue tasks", retrieval['confidence']))

            # General advice
            if not advice_parts:
                retrieval = self.retriever.retrieve("general pet care")
                advice_parts.append(f"General care tips: {retrieval['consolidated_info']}")
                retrieval_details.append(retrieval)
                queries_executed.append(("general pet care", retrieval['confidence']))

            # Calculate overall confidence
            overall_confidence = sum(conf for _, conf in queries_executed) / len(queries_executed) if queries_executed else 0.0
            
            advice_text = "\n\n".join(advice_parts) if advice_parts else "Follow standard pet care best practices."
            
            # Log the advice generation
            advice_record = {
                'timestamp': datetime.now().isoformat(),
                'queries_executed': len(queries_executed),
                'overall_confidence': round(overall_confidence, 2),
                'had_conflicts': len(conflicts) > 0,
                'had_overdue': len(overdue) > 0
            }
            self.advice_log.append(advice_record)
            logger.info(f"Generated advice: {len(queries_executed)} queries, confidence={overall_confidence:.2f}")
            
            return {
                'advice_text': advice_text,
                'retrieval_details': retrieval_details,
                'overall_confidence': round(overall_confidence, 2),
                'queries_executed': queries_executed
            }
        except Exception as e:
            logger.error(f"Error generating advice: {e}", exc_info=True)
            return {
                'advice_text': "Error generating advice. Please try again.",
                'retrieval_details': [],
                'overall_confidence': 0.0,
                'queries_executed': []
            }


class EnhancedScheduler(Scheduler):
    """Enhanced scheduler with RAG capabilities."""

    def __init__(self, owner: Owner):
        super().__init__(owner)
        self.retriever = RagRetriever()
        self.ai_coach = AiCareCoach(self.retriever)

    def generate_ai_enhanced_summary(self, date: Optional[datetime] = None) -> dict:
        """Generate a summary with AI-powered advice and detailed retrieval info."""
        basic_summary = self.generate_daily_summary(date)

        # Analyze for issues
        conflicts = []
        overdue = []
        for pet in self.owner.get_pets():
            conflicts.extend(self.check_conflicts(pet, date))
        overdue = [task.description for task in self.get_overdue_tasks()]

        # Get AI advice
        ai_result = self.ai_coach.generate_advice(basic_summary, conflicts, overdue)

        # Combine
        full_summary = basic_summary + "\n\n" + "="*40 + "\nAI Care Coach:\n" + ai_result['advice_text']

        return {
            'summary_text': full_summary,
            'retrieval_details': ai_result['retrieval_details'],
            'conflicts': conflicts,
            'overdue': overdue,
            'overall_confidence': ai_result['overall_confidence'],
            'queries_executed': ai_result['queries_executed'],
        }
