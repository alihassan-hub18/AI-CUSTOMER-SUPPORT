import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="AI Business Automation & Support", 
    page_icon="🤖", 
    layout="wide"
)

# Sidebar Configuration for API Key & Mode
st.sidebar.header("⚙️ System Configuration")
api_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password")

# Initialize Session State for Database/Logs and Chat History
if "chat_logs" not in st.session_state:
    st.session_state.chat_logs = []

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! Welcome to our support center. How can I help you today?"}
    ]

# Navigation Mode Selection
app_mode = st.sidebar.radio("Select Portal Mode", ["💬 Customer Support Chat", "📊 Admin Escalation Dashboard"])

# ----------------- CUSTOMER SUPPORT CHAT -----------------
if app_mode == "💬 Customer Support Chat":
    st.title("💬 Automated AI Customer Support")
    st.markdown("Chat with our intelligent assistant. Complex issues or angry queries are automatically routed to human supervisors.")

    # Display Chat Messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User Input Handling
    if user_prompt := st.chat_input("Type your message here..."):
        if not api_key:
            st.error("Please configure your Gemini API Key in the sidebar first.")
        else:
            # Append user message
            st.session_state.messages.append({"role": "user", "content": user_prompt})
            with st.chat_message("user"):
                st.markdown(user_prompt)

            with st.spinner("AI is analyzing and generating response..."):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    
                    # Prompt engineering to handle sentiment, escalation, and auto-reply
                    system_prompt = f"""
                    You are an expert, empathetic customer support AI agent for a tech business. 
                    Analyze the customer's message: '{user_prompt}'
                    
                    Perform two tasks and format your output strictly as follows:
                    STATUS: [Normal OR Needs Human Escalation] (Choose 'Needs Human Escalation' if the user is extremely angry, wants a refund, threatens legal action, or asks a complex technical question you cannot resolve).
                    REPLY: [Your professional, helpful, polite response to the customer]
                    """
                    
                    response = model.generate_content(system_prompt)
                    response_text = response.text
                    
                    # Parse status and reply
                    if "STATUS: Needs Human Escalation" in response_text:
                        status = "Flagged for Human Review"
                        # Extract reply part
                        ai_reply = response_text.split("REPLY:")[-1].strip() if "REPLY:" in response_text else response_text
                        ai_reply += "\n\n*(Note: Your query has been flagged for our senior support team. A human agent will reach out soon.)*"
                    else:
                        status = "Resolved by AI"
                        ai_reply = response_text.split("REPLY:")[-1].strip() if "REPLY:" in response_text else response_text

                    # Save to session logs
                    st.session_state.chat_logs.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "customer_message": user_prompt,
                        "ai_response": ai_reply,
                        "status": status
                    })

                    # Display assistant response
                    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                    with st.chat_message("assistant"):
                        st.markdown(ai_reply)

                except Exception as e:
                    st.error(f"Error connecting to AI: {e}")

# ----------------- ADMIN DASHBOARD -----------------
elif app_mode == "📊 Admin Escalation Dashboard":
    st.title("📊 Business Automation Dashboard")
    st.markdown("Monitor customer interactions, AI resolution rates, and tickets flagged for human review.")

    if not st.session_state.chat_logs:
        st.info("No customer interactions recorded yet. Switch to the Chat mode and simulate a few conversations.")
    else:
        df_logs = pd.DataFrame(st.session_state.chat_logs)
        
        # Metrics Overview
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Interactions", len(df_logs))
        resolved_count = len(df_logs[df_logs["status"] == "Resolved by AI"])
        col2.metric("Resolved by AI", resolved_count)
        flagged_count = len(df_logs[df_logs["status"] == "Flagged for Human Review"])
        col3.metric("Flagged for Human Review", flagged_count, delta_color="inverse")

        st.markdown("---")
        st.subheader("📋 Detailed Conversation Logs & Tickets")
        st.dataframe(df_logs, use_container_width=True)

        # Export Option
        csv = df_logs.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Interaction Logs (CSV)",
            data=csv,
            file_name='support_automation_logs.csv',
            mime='text/csv',
        )