import streamlit as st
from decision_tree import decision_trees, get_question, get_options, evaluate_answer
from utils import generate_recommendations, generate_checklist
from llm_assessment import (
    analyze_uploaded_evidence, 
    evaluate_open_text_compliance,
    generate_detailed_recommendations,
    ai_assistant_response
)

# Initialize session state for clause index, step, responses, and control flags
def init_session_state():
    if "clause_idx" not in st.session_state:
        st.session_state.clause_idx = 0
        st.session_state.step = "1"
        st.session_state.responses = {}
        st.session_state.last_verdict = False
        st.session_state.open_ended_responses = {}
        st.session_state.evidence_analysis = {}
        st.session_state.previous_answers = {}
    if "form_submitted" not in st.session_state:
        st.session_state.form_submitted = False
    if "show_ai_assistant" not in st.session_state:
        st.session_state.show_ai_assistant = False
    if "assessment_mode" not in st.session_state:
        st.session_state.assessment_mode = "structured"  # Options: "structured", "open_ended"

# Callback for form submission
def handle_form_submit():
    st.session_state.form_submitted = True

# Restart the entire assessment
def restart_assessment():
    for key in ["clause_idx", "step", "responses", "last_verdict", "form_submitted", 
                "open_ended_responses", "evidence_analysis", "previous_answers"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# Move to next clause
def next_clause():
    st.session_state.clause_idx += 1
    st.session_state.step = "1"
    st.session_state.last_verdict = False
    st.session_state.form_submitted = False

# Toggle AI assistant
def toggle_ai_assistant():
    st.session_state.show_ai_assistant = not st.session_state.show_ai_assistant
    
# Switch assessment mode
def switch_assessment_mode(mode):
    st.session_state.assessment_mode = mode

# Check if current step is a terminal step (leads to verdict)
def is_terminal_step(cid, step):
    current_options = decision_trees[cid]["steps"][step]["options"]
    return any(isinstance(target, dict) and "verdict" in target 
              for target in current_options.values())

# Begin
st.set_page_config(page_title="levnertech", layout="wide")
init_session_state()

clause_ids = list(decision_trees.keys())
total_clauses = len(clause_ids)


# Header and navigation
st.title("ISO 27001 Gap Assessment")

col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("🔄 Restart Assessment"):
        restart_assessment()
with col3:
    if st.button("💬 AI Assistant", type="secondary"):
        toggle_ai_assistant()


def display_analysis(analysis):
    st.write(f"**Compliance Level**: {analysis.get('compliance_level', 'Unknown')}")

    matched = analysis.get('matched_requirements', [])
    missing = analysis.get('missing_requirements', [])
    suggestions = analysis.get('suggestions', [])
    overall_assessment = analysis.get('overall_assessment', '')

    st.write("**Matched Requirements:**")
    if matched:
        for req in matched:
            st.write(f"- {req}")
    else:
        st.write("_No matched requirements found._")

    st.write("**Missing Requirements:**")
    if missing:
        for req in missing:
            st.write(f"- {req}")
    else:
        st.write("_No missing requirements detected._")

    st.write("**Suggestions for Improvement:**")
    if suggestions:
        for suggestion in suggestions:
            st.write(f"- {suggestion}")
    else:
        st.write("_No suggestions provided._")

    st.write("**Overall Assessment:**")
    if overall_assessment:
        st.write(overall_assessment)
    else:
        st.write("_No overall assessment available._")

# AI Assistant panel
if st.session_state.show_ai_assistant:
    with st.expander("ISO 27001 AI Assistant", expanded=True):
        cid = clause_ids[st.session_state.clause_idx] if st.session_state.clause_idx < total_clauses else None
        clause_context = None
        if cid:
            clause_context = f"{cid}: {decision_trees[cid]['title']}"
        
        user_query = st.text_input("Ask a question about ISO 27001 compliance:", key="assistant_query")
        if user_query:
            response = ai_assistant_response(user_query, clause_context)
            st.write(response)
            st.divider()
        
        st.info("Ask questions about ISO 27001 requirements, implementation advice, or clarification about specific clauses.")

# If all clauses done, show results
if st.session_state.clause_idx >= total_clauses:
    st.header("Assessment Results")
    
    # Display verdict summary
    st.subheader("Compliance Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    # Count verdicts
    verdict_counts = {"Complied": 0, "Minor NC": 0, "Opportunity for Improvement": 0, "Major NC": 0}
    for cid, verdict in st.session_state.responses.items():
        if isinstance(verdict, list):
            verdict = verdict[0]  # Handle list verdicts
        if verdict in verdict_counts:
            verdict_counts[verdict] += 1
    
    # Display counters
    with col1:
        st.metric("Complied", verdict_counts["Complied"])
    with col2:
        st.metric("Minor NCs", verdict_counts["Minor NC"])
    with col3:
        st.metric("Opportunities", verdict_counts["Opportunity for Improvement"])
    with col4:
        st.metric("Major NCs", verdict_counts["Major NC"])
    
    # Show detailed results by clause
    st.subheader("Results by Clause")
    for cid, verdict in st.session_state.responses.items():
        if verdict == "Complied":
            st.success(f"Clause {cid}: {verdict}")
        elif verdict in ("Minor NC", "Opportunity for Improvement"):
            st.warning(f"Clause {cid}: {verdict}")
        else:
            st.error(f"Clause {cid}: {verdict}")
        
        # Show evidence analysis if available
        if cid in st.session_state.evidence_analysis:
            with st.expander(f"Evidence Analysis for Clause {cid}"):
                analysis = st.session_state.evidence_analysis[cid]
                st.write(f"**Compliance Level**: {analysis.get('compliance_level', 'Not analyzed')}")
                st.write("**Matched Requirements:**")
                for req in analysis.get('matched_requirements', []):
                    st.write(f"- {req}")
                st.write("**Missing Requirements:**")
                for req in analysis.get('missing_requirements', []):
                    st.write(f"- {req}")
                st.write("**Suggestions:**")
                for sug in analysis.get('suggestions', []):
                    st.write(f"- {sug}")
    
    # Generate LLM-enhanced recommendations
    st.subheader("Detailed Recommendations")
    
    # Format assessment results for recommendation generation
    assessment_data = [
        {"clause": cid, "verdict": verdict, "evidence_analysis": st.session_state.evidence_analysis.get(cid, {})}
        for cid, verdict in st.session_state.responses.items()
    ]
    
    # Get organization context from user
    org_context = st.text_area("Provide additional context about your organization for customized recommendations:", 
                              placeholder="E.g., industry, size, risk profile, compliance priorities...")
    
    if st.button("Generate Detailed Recommendations"):
        with st.spinner("Generating customized recommendations..."):
            detailed_recs = generate_detailed_recommendations(assessment_data, org_context)
            
            # Display priority actions
            st.write("**Priority Actions:**")
            for action in detailed_recs.get("priority_actions", []):
                st.write(f"- {action}")
            
            # Display recommendations by clause
            st.write("**Recommendations by Clause:**")
            for clause_id, recs in detailed_recs.get("recommendations_by_clause", {}).items():
                with st.expander(f"Clause {clause_id}"):
                    st.write("**Actions:**")
                    for action in recs.get("actions", []):
                        st.write(f"- {action}")
                    st.write(f"**Suggested Timeline:** {recs.get('timeline', 'Not specified')}")
                    if recs.get("resources"):
                        st.write("**Resources:**")
                        for res in recs.get("resources", []):
                            st.write(f"- {res}")
            
            # Display implementation strategy
            st.write("**Implementation Strategy:**")
            st.write(detailed_recs.get("implementation_strategy", "Address major non-conformities first, followed by minor ones."))
            
            # Display strengths
            st.write("**Areas of Strength:**")
            for strength in detailed_recs.get("areas_of_strength", []):
                st.write(f"- {strength}")
    
    # Standard recommendations and checklist
    st.subheader("Quick Recommendations")
    all_recs = []
    for cid, verdict in st.session_state.responses.items():
        analysis = {"clause": cid, "verdict": verdict}
        all_recs.extend(generate_recommendations(analysis))
    for rec in dict.fromkeys(all_recs):
        st.write(f"- {rec}")

    st.subheader("Mitigation Checklist")
    checklist = generate_checklist([
        {"clause": cid, "verdict": verdict}
        for cid, verdict in st.session_state.responses.items()
    ])
    for item in checklist:
        st.write(f"- {item}")

    if st.button("🔄 Restart Assessment", key="restart_end"):
        restart_assessment()

# Otherwise, present current question
else:
    cid = clause_ids[st.session_state.clause_idx]
    step = st.session_state.step
    title = decision_trees[cid]["title"]

    st.header(f"Clause {cid}: {title}")
    
    # Assessment mode selector
    mode_col1, col2, mode_col3 = st.columns([1, 2, 1])
    
    with mode_col1:
        if st.button("Structured Assessment", 
                    type="primary" if st.session_state.assessment_mode == "structured" else "secondary"):
            switch_assessment_mode("structured")
    with mode_col3:
        if st.button("Open-Ended Assessment", 
                    type="primary" if st.session_state.assessment_mode == "open_ended" else "secondary"):
            switch_assessment_mode("open_ended")
    
    # Evidence upload for either mode
    with st.expander("Upload Evidence Documents"):
        uploaded_file = st.file_uploader(f"Upload evidence for Clause {cid}", type=["pdf", "docx", "txt"])
        if uploaded_file is not None:
            # Process the uploaded file
            file_contents = uploaded_file.read()
            # For text files, decode to string
            if uploaded_file.type == "text/plain":
                file_text = file_contents.decode('utf-8')
            else:
                # For simplicity, we'll just acknowledge receipt of non-text files
                file_text = f"[Received file: {uploaded_file.name}]"
            
            if st.button("Analyze Document"):
                with st.spinner("Analyzing document..."):
                    analysis = analyze_uploaded_evidence(cid, file_text)
                    st.session_state.evidence_analysis[cid] = analysis

                    display_analysis(analysis)
    
    # If structured assessment mode
    if st.session_state.assessment_mode == "structured":
        question = get_question(cid, step)
        options = get_options(cid, step)
        terminal = is_terminal_step(cid, step)

        if not st.session_state.last_verdict:
            # 1) Render form dan tangkap apakah sudah submit
            with st.form(key=f"form_{cid}_{step}"):
                choice = st.radio(question, options)
                submitted = st.form_submit_button("Submit")
            
            # 2) Setelah submit: simpan jawaban & munculkan konteks
            if submitted:
                # simpan jawaban
                st.session_state.previous_answers[question] = choice

                #Proses jawaban untuk verdict atau lanjut step
                result = evaluate_answer(cid, step, choice)
                if isinstance(result, dict) and "verdict" in result:
                    st.session_state.responses[cid] = result["verdict"]
                    st.session_state.last_verdict = True
                else:
                    st.session_state.step = result

                # reset flag form_submitted kalau masih pakai itu, lalu rerun
                st.session_state.form_submitted = False
                st.rerun()

        else:
            # Display the verdict when last_verdict is True
            verdict = st.session_state.responses[cid]
            if isinstance(verdict, list):
                verdict = verdict[0]  # Handle list verdicts
                
            if verdict == "Complied":
                st.success(f"Verdict for Clause {cid}: {verdict}")
            elif verdict in ("Minor NC", "Opportunity for Improvement"):
                st.warning(f"Verdict for Clause {cid}: {verdict}")
            else:
                st.error(f"Verdict for Clause {cid}: {verdict}")

    
    # If open-ended assessment mode
    else:  # open_ended mode
        # Display clause details and requirements
        clause_description = f"Clause {cid}: {title}\n"
        if cid in ["4.1", "4.2", "4.3", "4.4"]:
            clause_requirements = {
                "4.1": "The organization shall determine external and internal issues relevant to its purpose and strategic direction that affect its ability to achieve the intended outcome(s) of its ISMS.",
                "4.2": "The organization shall determine interested parties relevant to the ISMS, and their requirements.",
                "4.3": "The organization shall determine the boundaries and applicability of the ISMS to establish its scope.",
                "4.4": "The organization shall establish, implement, maintain and continually improve an ISMS."
            }
            st.write(f"**Requirement:** {clause_requirements[cid]}")
        
        # Only render the form if not already showing a verdict
        if not st.session_state.last_verdict:
            with st.form(key=f"form_open_{cid}"):
                st.write("**Describe your implementation:**")
                open_response = st.text_area(
                    "Provide details on how your organization meets this requirement:", 
                    height=200,
                    help="Be specific about processes, documents, and responsibilities"
                )
                
                submitted = st.form_submit_button("Evaluate Compliance", on_click=handle_form_submit)
            
            # Process the form submission
            if st.session_state.form_submitted:
                # Reset form submission flag
                st.session_state.form_submitted = False
                
                # Store the response
                st.session_state.open_ended_responses[cid] = open_response
                
                # Get document context if available
                doc_context = None
                if cid in st.session_state.evidence_analysis:
                    doc_context = str(st.session_state.evidence_analysis[cid])
                    
                # Evaluate the response
                with st.spinner("Evaluating response..."):
                    verdict, scores, feedback = evaluate_open_text_compliance(cid, open_response, doc_context)
                    st.session_state.responses[cid] = verdict
                    st.session_state.last_verdict = True
                    st.rerun()
        else:
            # Display the verdict when last_verdict is True
            verdict = st.session_state.responses[cid]
            open_response = st.session_state.open_ended_responses.get(cid, "")
            
            # Get document context if available
            doc_context = None
            if cid in st.session_state.evidence_analysis:
                doc_context = str(st.session_state.evidence_analysis[cid])
                
            # Re-evaluate to get feedback
            _, scores, feedback = evaluate_open_text_compliance(cid, open_response, doc_context)
            
            if verdict == "Complied":
                st.success(f"Verdict for Clause {cid}: {verdict}")
            elif verdict in ("Minor NC", "Opportunity for Improvement"):
                st.warning(f"Verdict for Clause {cid}: {verdict}")
            else:
                st.error(f"Verdict for Clause {cid}: {verdict}")
            
            # Display feedback
            st.subheader("Assessment Feedback")
            st.write(feedback)
            
            # Display scores if available
            if scores:
                st.subheader("Compliance Scores")
                score_labels = {
                    "completeness": "Completeness",
                    "specificity": "Specificity",
                    "evidence": "Evidence Provided",
                    "alignment": "Alignment with ISO 27001"
                }
                
                # Create columns for scores
                score_cols = st.columns(len(scores))
                for i, (key, label) in enumerate(score_labels.items()):
                    if key in scores:
                        with score_cols[i]:
                            # Display score as a gauge or metric
                            st.metric(label, f"{int(scores[key] * 100)}%")
    
    # Navigation buttons for either assessment mode
            # Show progress
    progress_text = f"Clause {st.session_state.clause_idx + 1} of {total_clauses}"
    st.progress((st.session_state.clause_idx + 1) / total_clauses, text=progress_text)
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.last_verdict:
            # Only show the next clause button if a verdict has been reached
            if st.session_state.clause_idx < total_clauses - 1:
                st.button("Next Clause", on_click=next_clause)
            else:
                st.button("View Results", on_click=next_clause)
                




# Add an insights section on the sidebar
with st.sidebar:
    st.title("ISO 27001 Insights")
    
    # Show current clause insights
    if st.session_state.clause_idx < total_clauses:
        cid = clause_ids[st.session_state.clause_idx]
        
        # Display clause tips
        st.subheader(f"Tips for Clause {cid}")
        
        # Define tips for specific clauses
        clause_tips = {
            "4.1": [
                "Consider both internal factors (organization structure, governance) and external factors (regulatory, technological, competitive landscape).",
                "Document how these issues might affect your information security objectives.",
                "Review these issues periodically, especially when significant changes occur."
            ],
            "4.2": [
                "Include stakeholders such as customers, employees, regulators, and suppliers.",
                "Document their specific security requirements and expectations.",
                "Establish a process for monitoring changes in stakeholder requirements."
            ],
            "4.3": [
                "Define physical locations, organizational functions, and technical boundaries.",
                "Justify any exclusions from the scope.",
                "Ensure interfaces and dependencies with out-of-scope activities are addressed."
            ],
            "4.4": [
                "Ensure top management support and sufficient resources.",
                "Define clear responsibilities for the ISMS.",
                "Implement processes for continual improvement based on risk assessment and effectiveness measurement."
            ]
        }
        
        # Display relevant tips
        if cid in clause_tips:
            for tip in clause_tips[cid]:
                st.info(tip)
        
        # Display common pitfalls
        st.subheader("Common Pitfalls")
        common_pitfalls = {
            "4.1": [
                "Failing to consider both internal and external issues",
                "Not documenting how issues affect information security",
                "Conducting the analysis only once without regular reviews"
            ],
            "4.2": [
                "Identifying too few stakeholders",
                "Omitting legal and regulatory requirements",
                "Not having a process to update requirements when they change"
            ],
            "4.3": [
                "Defining the scope too broadly or too narrowly",
                "Not documenting justifications for exclusions",
                "Failing to consider dependencies with third parties"
            ],
            "4.4": [
                "Insufficient management commitment",
                "Unclear responsibilities and authorities",
                "Lack of documented processes for ISMS improvement"
            ]
        }
        
        if cid in common_pitfalls:
            for pitfall in common_pitfalls[cid]:
                st.warning(pitfall)
    
    # Show overall progress
    st.subheader("Assessment Progress")
    completed = sum(1 for _ in st.session_state.responses.items())
    st.progress(completed / total_clauses, text=f"{completed}/{total_clauses} clauses assessed")
    
    # Show completed clauses
    if completed > 0:
        st.subheader("Completed Clauses")
        for cid, verdict in st.session_state.responses.items():
            if verdict == "Complied":
                st.success(f"✓ {cid}")
            elif verdict in ("Minor NC", "Opportunity for Improvement"):
                st.warning(f"⚠ {cid}")
            else:
                st.error(f"✗ {cid}")

    # Add quick reference
    with st.expander("ISO 27001 Quick Reference"):
        st.write("""
        **Clause 4: Context of the Organization**
        - 4.1: Understanding the organization and its context
        - 4.2: Understanding the needs and expectations of interested parties
        - 4.3: Determining the scope of the ISMS
        - 4.4: Information security management system
        
        **Key ISO 27001 Terms:**
        - ISMS: Information Security Management System
        - Risk: Effect of uncertainty on objectives
        - Asset: Anything that has value to the organization
        - Control: Measure that modifies risk
        """)
