import streamlit as st
from datetime import datetime, timedelta, time
import os

from pawpal_system import Owner, Pet, Task, EnhancedScheduler, Frequency, CompletionStatus
from rag_reliability import display_reliability_section

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")

# session-stored owner to survive reruns
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name)
else:
    if st.session_state.owner.name != owner_name:
        st.session_state.owner.name = owner_name

st.markdown("### Pets")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    owner = st.session_state.owner
    existing_pet = next((p for p in owner.get_pets() if p.name.lower() == pet_name.strip().lower()), None)
    if existing_pet:
        st.info(f"Pet '{pet_name}' already added")
        st.session_state.current_pet = existing_pet
    else:
        new_pet = Pet(name=pet_name.strip(), species=species)
        owner.add_pet(new_pet)
        st.success(f"Added pet '{pet_name}'")
        st.session_state.current_pet = new_pet

if "current_pet" in st.session_state:
    st.write("Current pet:", f"{st.session_state.current_pet.name} ({st.session_state.current_pet.species})")

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "task_date_input" not in st.session_state:
    st.session_state.task_date_input = datetime.now().date()

if "task_time_input" not in st.session_state:
    now = datetime.now()
    st.session_state.task_time_input = time(hour=now.hour, minute=now.minute)

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

task_date = st.date_input("Task date", key="task_date_input")
task_time_input = st.time_input("Task time", key="task_time_input")
task_time = datetime.combine(task_date, task_time_input)

if st.button("Schedule task"):
    if "current_pet" not in st.session_state:
        st.error("Select or add a pet before scheduling tasks.")
    else:
        pet = st.session_state.current_pet
        priority_map = {"low": 1, "medium": 2, "high": 3}
        task = Task(
            description=task_title,
            time=task_time,
            duration=int(duration),
            priority=priority_map.get(priority, 1),
        )
        scheduler = EnhancedScheduler(st.session_state.owner)
        scheduler.schedule_task(pet, task)

        st.session_state.tasks.append(
            {
                "pet": pet.name,
                "description": task_title,
                "time": task_time.strftime("%Y-%m-%d %H:%M"),
                "duration_minutes": int(duration),
                "priority": priority,
            }
        )

        st.success(f"Scheduled task '{task_title}' for {pet.name}")

if st.session_state.tasks:
    st.write("Current tasks:")
    st.dataframe(st.session_state.tasks, use_container_width=True)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button now calls your scheduler logic from pawpal_system.")

if st.button("Generate schedule"):
    owner = st.session_state.owner
    scheduler = EnhancedScheduler(owner)

    # Get prioritized upcoming tasks
    all_pending = scheduler.organize_tasks_by_priority()
    now = datetime.now()
    cutoff = now + timedelta(hours=24)
    upcoming = [task for task in all_pending if task.time >= now and task.time <= cutoff]

    if not upcoming:
        st.info("No upcoming tasks in the next 24 hours.")
    else:
        st.write("Upcoming tasks in next 24h (sorted by priority):")
        schedule_rows = [
            {
                "pet": next((pet.name for pet in owner.get_pets() if task in pet.tasks), "N/A"),
                "task": task.description,
                "time": task.time.strftime("%Y-%m-%d %H:%M"),
                "priority": task.priority,
                "status": task.completion_status.value,
            }
            for task in upcoming
        ]
        st.dataframe(schedule_rows, use_container_width=True)

    # Check for conflicts
    conflicts = []
    for pet in owner.get_pets():
        pet_conflicts = scheduler.check_conflicts(pet)
        if pet_conflicts:
            conflicts.extend([f"{pet.name}: {c}" for c in pet_conflicts])

    if conflicts:
        st.warning("Schedule conflicts detected:")
        for conflict in conflicts:
            st.write(f"- {conflict}")

    overdue = scheduler.get_overdue_tasks()
    if overdue:
        st.warning("Overdue tasks detected:")
        overdue_rows = [
            {
                "pet": next((pet.name for pet in owner.get_pets() if task in pet.tasks), "N/A"),
                "task": task.description,
                "time": task.time.strftime("%Y-%m-%d %H:%M"),
                "status": task.completion_status.value,
            }
            for task in overdue
        ]
        st.dataframe(overdue_rows, use_container_width=True)
    else:
        st.success("Schedule generated successfully! No overdue tasks.")

    # AI Care Coach Advice
    st.subheader("🤖 AI Care Coach")

    # RAG Demo Toggle
    show_rag_process = st.checkbox("🔍 Show RAG Process (Demo Mode)", help="Reveal how the AI retrieves and uses knowledge from local documents")

    ai_result = scheduler.generate_ai_enhanced_summary()
    st.text_area("AI-Enhanced Schedule Summary", ai_result['summary_text'], height=300)

    if show_rag_process:
        st.markdown("---")
        st.subheader("🔍 RAG Process Breakdown")

        # Show knowledge base
        st.markdown("**📚 Knowledge Base Documents:**")
        docs_path = "docs"
        if os.path.exists(docs_path):
            doc_files = [f for f in os.listdir(docs_path) if f.endswith('.md')]
            for doc_file in doc_files:
                with st.expander(f"📄 {doc_file}"):
                    with open(os.path.join(docs_path, doc_file), 'r') as f:
                        st.code(f.read(), language='markdown')
        else:
            st.warning("Knowledge base documents not found in 'docs/' directory")

        # Show retrieval process
        st.markdown("**🔎 Retrieval Analysis:**")

        if ai_result['retrieval_details']:
            st.markdown("**Search Queries & Retrieved Knowledge:**")
            for retrieval in ai_result['retrieval_details']:
                st.markdown(f"**Query:** `{retrieval['query']}`")
                if retrieval['matched_documents']:
                    st.markdown("**📖 Matched Documents:**")
                    for doc_name, matches in retrieval['matched_documents'].items():
                        with st.expander(f"From {doc_name}"):
                            for match in matches:
                                st.info(match)
                else:
                    st.warning("No documents matched this query")
                st.markdown("---")
        else:
            st.info("No specific queries triggered for current schedule")

        # Show schedule analysis
        st.markdown("**📊 Schedule Analysis:**")
        if ai_result['conflicts']:
            st.markdown("**⚠️ Conflicts Detected:**")
            for conflict in ai_result['conflicts']:
                st.error(conflict)
        else:
            st.success("✅ No conflicts detected")

        if ai_result['overdue']:
            st.markdown("**⏰ Overdue Tasks:**")
            for task in ai_result['overdue']:
                st.warning(f"• {task}")
        else:
            st.success("✅ No overdue tasks")

        # Show AI generation process
        st.markdown("**🧠 AI Generation Process:**")
        st.markdown("""
        1. **Schedule Analysis**: AI analyzes conflicts, overdue tasks, and priorities
        2. **Knowledge Retrieval**: Searches local documents for relevant pet care guidance
        3. **Advice Synthesis**: Combines schedule data with retrieved knowledge
        4. **Contextual Response**: Generates human-readable recommendations
        """)

        # Compare with basic scheduler
        st.markdown("**⚖️ Comparison: Basic vs AI-Enhanced**")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Basic Scheduler Output:**")
            basic_summary = scheduler.generate_daily_summary()
            st.text_area("Basic Summary", basic_summary, height=200, key="basic")

        with col2:
            st.markdown("**AI-Enhanced Output:**")
            st.text_area("AI Summary", ai_result['summary_text'], height=200, key="ai")

        st.markdown("*Notice how the AI coach provides specific pet care guidance and explanations!*")

# Add reliability testing section
display_reliability_section()
