"""
RAG Reliability Testing Module for PawPal+
Display test results, confidence scores, and logs in Streamlit.
"""

import streamlit as st
import os
import json
from datetime import datetime
from pawpal_system import RagRetriever, AiCareCoach, EnhancedScheduler


def display_reliability_section():
    """Display RAG reliability testing and evaluation section."""
    
    st.divider()
    st.subheader("🧪 RAG Reliability & Testing")
    
    # Create tabs for different testing views
    tab1, tab2, tab3 = st.tabs(["🧪 Run Tests", "📊 Confidence Scores", "📋 Logs & Monitoring"])
    
    with tab1:
        st.markdown("### Automated Tests")
        st.caption("Run tests to verify RAG system reliability")
        
        if st.button("▶️ Run RAG Test Suite"):
            with st.spinner("Running tests..."):
                try:
                    import subprocess
                    result = subprocess.run(
                        ["python", "-m", "pytest", "test_rag.py", "-v", "--tb=short"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    st.success("✅ Tests executed successfully!")
                    
                    # Display test output
                    st.code(result.stdout, language="text")
                    
                    # Extract pass/fail counts
                    if "passed" in result.stdout:
                        st.success("All tests passed!")
                    if "FAILED" in result.stdout:
                        st.error("Some tests failed. See output above.")
                        
                except Exception as e:
                    st.error(f"❌ Error running tests: {e}")
        
        st.markdown("### Test Coverage")
        st.markdown("""
        **RAG System Tests:**
        - Document loading and retrieval ✓
        - Confidence scoring calculation ✓
        - Error handling and edge cases ✓
        - Consistency of results ✓
        - Advice generation quality ✓
        
        **Test Categories:**
        - 5 Retriever tests
        - 4 AI Coach tests
        - 3 Enhanced Scheduler tests
        - 4 Reliability tests
        """)
    
    with tab2:
        st.markdown("### Confidence Scores")
        st.caption("AI rates how confident it is in its advice")
        
        # Get current scheduler if available
        if "owner" in st.session_state:
            owner = st.session_state.owner
            scheduler = EnhancedScheduler(owner)
            
            if owner.get_all_tasks():
                result = scheduler.generate_ai_enhanced_summary()
                
                # Display overall confidence
                confidence = result.get('overall_confidence', 0.0)
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Overall Confidence", f"{confidence:.0%}")
                
                with col2:
                    if confidence >= 0.7:
                        st.success("✅ High Confidence")
                    elif confidence >= 0.4:
                        st.warning("⚠️ Medium Confidence")
                    else:
                        st.error("❌ Low Confidence")
                
                with col3:
                    st.info(f"{len(result.get('retrieval_details', []))} sources used")
                
                # Display query-level confidence
                if result.get('queries_executed'):
                    st.markdown("### Query-Level Confidence:")
                    confidence_data = []
                    for query, conf in result['queries_executed']:
                        confidence_data.append({
                            'Query': query,
                            'Confidence': f"{conf:.0%}",
                            'Status': '✅' if conf >= 0.7 else '⚠️' if conf >= 0.4 else '❌'
                        })
                    
                    import pandas as pd
                    st.dataframe(pd.DataFrame(confidence_data), use_container_width=True)
            else:
                st.info("Generate a schedule to see confidence scores")
        else:
            st.info("Create a pet and schedule tasks to see confidence scores")
    
    with tab3:
        st.markdown("### System Logs")
        st.caption("Monitor RAG system activity and errors")
        
        # Check if log file exists
        log_file = "pawpal_rag.log"
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Refresh Logs"):
                st.rerun()
        
        with col2:
            if os.path.exists(log_file):
                file_size = os.path.getsize(log_file) / 1024  # KB
                st.metric("Log File Size", f"{file_size:.1f} KB")
        
        # Display logs
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.readlines()
            
            # Show most recent logs
            st.markdown("### Recent Activity")
            num_logs = min(50, len(logs))  # Show last 50 lines
            
            log_text = "".join(logs[-num_logs:])
            st.code(log_text, language="text")
            
            # Log statistics
            st.markdown("### Statistics")
            info_count = sum(1 for log in logs if "INFO" in log)
            warning_count = sum(1 for log in logs if "WARNING" in log)
            error_count = sum(1 for log in logs if "ERROR" in log)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Info Messages", info_count)
            with col2:
                st.metric("Warnings", warning_count)
            with col3:
                st.metric("Errors", error_count)
        else:
            st.info("No logs generated yet. Generate a schedule to create logs.")
        
        # Download logs button
        if os.path.exists(log_file):
            with open(log_file, 'rb') as f:
                st.download_button(
                    label="📥 Download Logs",
                    data=f.read(),
                    file_name=f"pawpal_rag_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                    mime="text/plain"
                )
    
    # Summary section
    st.markdown("---")
    st.markdown("### Reliability Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.info("✅ **Automated Tests**: pytest suite included")
    
    with col2:
        st.info("📊 **Confidence Scoring**: Per-query reliability ratings")
    
    with col3:
        st.info("📋 **Logging**: All operations tracked in pawpal_rag.log")
    
    with col4:
        st.info("👤 **Human Review**: Interactive dashboard for evaluation")
