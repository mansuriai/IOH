# streamlit_app.py
import streamlit as st
from vapi import Vapi
import os
from dotenv import load_dotenv
import time
from app import InterviewAnalyzer  # This will be your existing analyzer class

# Load environment variables
load_dotenv()

# Initialize Vapi client
vapi_client = Vapi(token=os.getenv('VAPI_TOKEN'))

# Initialize analyzer
analyzer = InterviewAnalyzer()

def start_call():
    """Start a new call using Vapi"""
    try:
        # Configure your call parameters as needed
        call_params = {
            "assistant": {
                "name": "Interview Assistant",
                "model": {
                    "provider": "openai",
                    "model": "gpt-4",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are conducting a business case interview. Ask challenging questions and evaluate the candidate's responses."
                        }
                    ]
                },
                "voice": {
                    "provider": "11labs",
                    "voiceId": "rachel"
                },
                "firstMessage": "Hello, let's begin the case interview. How would you approach this business problem?",
            }
        }
        
        call = vapi_client.call.start(call_params)
        st.session_state.current_call_id = call.id
        st.success(f"Call started with ID: {call.id}")
        return call
    except Exception as e:
        st.error(f"Failed to start call: {str(e)}")
        return None

def end_call(call_id):
    """End an ongoing call"""
    try:
        vapi_client.call.end(call_id)
        st.session_state.call_ended = True
        st.success(f"Call {call_id} ended successfully")
        return True
    except Exception as e:
        st.error(f"Failed to end call: {str(e)}")
        return False

def get_latest_completed_call():
    """Fetch the most recent completed call"""
    try:
        calls = vapi_client.calls.list()
        completed_calls = [call for call in calls if hasattr(call, 'status') and call.status == 'ended']
        
        if not completed_calls:
            st.warning("No completed calls found")
            return None
            
        latest_call = max(completed_calls, key=lambda x: x.created_at)
        return latest_call.id
        
    except Exception as e:
        st.error(f"Error fetching calls: {e}")
        return None

def main():
    st.title("Interview Analysis Dashboard")
    
    # Initialize session state variables
    if 'current_call_id' not in st.session_state:
        st.session_state.current_call_id = None
    if 'call_ended' not in st.session_state:
        st.session_state.call_ended = False
    
    # Call control section
    st.header("Call Management")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Start New Call"):
            start_call()
    
    with col2:
        if st.session_state.current_call_id and not st.session_state.call_ended:
            if st.button("End Current Call"):
                end_call(st.session_state.current_call_id)
    
    # Analysis section
    st.header("Transcript Analysis")
    
    # Option 1: Analyze latest completed call
    if st.button("Analyze Latest Completed Call"):
        call_id = get_latest_completed_call()
        if call_id:
            st.session_state.analyze_call_id = call_id
            with st.spinner("Analyzing call..."):
                try:
                    transcript = analyzer.get_transcript_from_vapi(call_id)
                    analysis = analyzer.analyze_transcript(transcript)
                    
                    st.session_state.transcript = transcript
                    st.session_state.analysis = analysis
                    
                    st.success("Analysis completed!")
                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")
    
    # Option 2: Analyze specific call ID
    with st.expander("Analyze Specific Call"):
        call_id_input = st.text_input("Enter Call ID:")
        if st.button("Analyze This Call"):
            if call_id_input:
                st.session_state.analyze_call_id = call_id_input
                with st.spinner("Analyzing call..."):
                    try:
                        transcript = analyzer.get_transcript_from_vapi(call_id_input)
                        analysis = analyzer.analyze_transcript(transcript)
                        
                        st.session_state.transcript = transcript
                        st.session_state.analysis = analysis
                        
                        st.success("Analysis completed!")
                    except Exception as e:
                        st.error(f"Analysis failed: {str(e)}")
            else:
                st.warning("Please enter a Call ID")
    
    # Display results if available
    if 'analysis' in st.session_state and st.session_state.analysis:
        st.subheader("Analysis Results")
        
        # Display overall score
        overall_score = st.session_state.analysis.get('overall_score', 'N/A')
        st.metric("Overall Score", overall_score)
        
        # Display detailed feedback
        st.subheader("Detailed Feedback")
        detailed_feedback = st.session_state.analysis.get('detailed_feedback', {})
        
        for criterion, feedback in detailed_feedback.items():
            with st.expander(f"{criterion.replace('_', ' ').title()} (Score: {feedback.get('score', 'N/A')})"):
                st.write(f"**Feedback:** {feedback.get('feedback', '')}")
                st.write(f"**Strengths:** {feedback.get('strengths', '')}")
                st.write(f"**Improvements:** {feedback.get('improvements', '')}")
        
        # Display summary
        st.subheader("Summary")
        st.write(st.session_state.analysis.get('summary', ''))
        
        # Display transcript (collapsed by default)
        with st.expander("View Full Transcript"):
            st.text_area("Transcript", st.session_state.transcript, height=300)
    
    # Current call status
    st.sidebar.header("Current Call Status")
    if st.session_state.current_call_id:
        st.sidebar.write(f"**Call ID:** {st.session_state.current_call_id}")
        if st.session_state.call_ended:
            st.sidebar.success("Call ended")
        else:
            st.sidebar.warning("Call in progress")
    else:
        st.sidebar.info("No active call")

if __name__ == "__main__":
    main()