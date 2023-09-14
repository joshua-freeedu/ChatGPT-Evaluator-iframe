
import os
import shutil

import docx2txt
import PyPDF2

import streamlit as st

import openai
import requests
import json

#######################################################################################################################
current_path = os.path.abspath(os.path.dirname(__file__))

def read_pdf(file):
    pdfReader = PyPDF2.PdfReader(file)
    count = len(pdfReader.pages)
    all_page_text = ""
    for i in range(count):
        page = pdfReader.pages[i]
        all_page_text += page.extract_text()

    return all_page_text

def build_criteria(criteria, min_score, max_score):
    text = ""
    num_criteria = len(criteria)
    for i, val in enumerate(criteria):
        text += "Criteria: \n"
        text += f"({i+1}/{num_criteria}) {val} Minimum Score: {min_score[i]} | Maximum Score: {max_score[i]} \n\n"

    return text
def run_chatgpt(essay, criteria_text):
    # Define the endpoint URL and payload data
    endpoint = "https://joshuafreeedu.pythonanywhere.com/evaluate-essay"
    payload = {"essay_text": essay, "criteria": criteria_text}

    response = requests.post(endpoint, json=payload)

    return response.json()["evaluation"]

def main():
    uploaded_file = st.file_uploader('Upload Files', accept_multiple_files=False, type=['docx','txt','pdf'])
    ta_val = "" # Value for the text area
    upload_flag = False

    #If a file/s is uploaded, disable input in the text area; then, display the essays list
    if uploaded_file:
        upload_flag = True

        # Parse the contents of the uploaded file according to their extension txt docx or pdf
        if uploaded_file.name.split(".")[-1] == "docx": # docx files
            contents = docx2txt.process(uploaded_file)
        elif uploaded_file.name.split(".")[-1] == "pdf": # pdf files
            contents = read_pdf(uploaded_file)
        else: # txt files
            contents = uploaded_file.read().decode("utf-8")

        #ta_val will be the preview of all the essays in the text area; display index numbering if there are more than one file
        ta_val += contents

    # text area input for the essay, button to run the model, other widgets
    response_ta = st.text_area("Essay:",placeholder="You can input your essay here instead of uploading a file.",height=500, value=ta_val, disabled=upload_flag)

    if "criteria" not in st.session_state:
        st.session_state["criteria"] = ["Cohesion", "Syntax", "Vocabulary", "Phraseology", "Grammar", "Conventions"]
        st.session_state["min_scores"] = [0, 0, 0, 0, 0, 0]
        st.session_state["max_scores"] = [10, 10, 10, 10, 10, 10]
        st.session_state["remove_criteria"] = False

    with st.form(key="criteria_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("Criteria")
            new_criteria = []
            for i, val in enumerate(st.session_state["criteria"]):
                new_criteria.append(st.text_input(f"Criteria {i + 1}", st.session_state["criteria"][i], label_visibility="collapsed"))
        with col2:
            st.subheader("Minimum Score")
            new_min_scores = []
            for i, val in enumerate(st.session_state["min_scores"]):
                new_min_scores.append(st.number_input(f"Minimum Score {i + 1}", 0, st.session_state["max_scores"][i],
                                                      st.session_state["min_scores"][i], label_visibility="collapsed"))
        with col3:
            st.subheader("Maximum Score")
            new_max_scores = []
            for i, val in enumerate(st.session_state["max_scores"]):
                new_max_scores.append(st.number_input(f"Maximum Score {i + 1}", st.session_state["min_scores"][i], 100,
                                                      st.session_state["max_scores"][i], label_visibility="collapsed"))

        submit_criteria = col1.form_submit_button("Update Criteria")
        add_criteria = col2.checkbox("Add criteria")
        remove_criteria = col3.checkbox("Remove criteria")

        if submit_criteria:
            # Add new criterion
            if add_criteria and remove_criteria:
                st.warning("Cannot add and remove criteria at the same time.")
            else:
                if add_criteria:
                    new_criteria.append("Enter new criteria name..")
                    new_min_scores.append(0)
                    new_max_scores.append(10)

                    st.session_state["criteria"] = new_criteria
                    st.session_state["min_scores"] = new_min_scores
                    st.session_state["max_scores"] = new_max_scores
                    st._rerun()

                # Remove criterion
                if remove_criteria:
                    remove_list = st.multiselect("Select criteria to remove:", st.session_state["criteria"])
                    if remove_list:
                        new_criteria = [c for c in new_criteria if c not in remove_list]
                        new_min_scores = [s for c, s in zip(new_criteria, new_min_scores) if c not in remove_list]
                        new_max_scores = [s for c, s in zip(new_criteria, new_max_scores) if c not in remove_list]

                        st.session_state["criteria"] = new_criteria
                        st.session_state["min_scores"] = new_min_scores
                        st.session_state["max_scores"] = new_max_scores
                        st._rerun()

                else:
                    st.session_state["criteria"] = new_criteria
                    st.session_state["min_scores"] = new_min_scores
                    st.session_state["max_scores"] = new_max_scores
                    st._rerun()


    # send essay to chatGPT when the button is clicked
    if st.button("Submit"):
        if not ta_val:  # if the text area is empty:
            st.error("Please input the essay in the corresponding text area.")
        else:
            # ChatGPT Evaluation Section
            criteria_text = build_criteria(st.session_state["criteria"], st.session_state["min_scores"],
                                           st.session_state["max_scores"])
            st.session_state.chatgpt_evaluation = run_chatgpt(ta_val, criteria_text)

    if "chatgpt_evaluation" in st.session_state:
        st.subheader("Evaluation: ")
        st.write(st.session_state["chatgpt_evaluation"])


if __name__ == '__main__':
    main()

# To run streamlit, go to terminal and type: 'streamlit run app-source.py'
