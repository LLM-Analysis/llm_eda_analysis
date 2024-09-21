import streamlit as st
import pandas as pd

from page_utils import *
from backend_utils import *

st.set_page_config(layout = "wide")

init_page_css()

file = st.sidebar.file_uploader("Choose a CSV", accept_multiple_files = False)

if file is not None:
    if "file_name" not in st.session_state:
        st.session_state["file_name"] = file.name
    
    if "chart_response" in st.session_state and file.name != st.session_state["file_name"]:
        del st.session_state["chart_response"]
        del st.session_state["messages"]

    st.session_state["file_name"] = file.name

    data = pd.read_csv(file)
    api_key = st.sidebar.text_input("API Key")
    
    markdown("<h3>Exploratory Data Analysis with Generative AI</h3>")

    if api_key == "":
        st.info("Enter your API Key to continue.")

    else:
        max_tokens = 1000000

        margin_tokens = max_tokens // 2

        text = table2text(data)
        n_tokens = estimate_n_token(text)
        analyze = True
        n_rows = len(data)

        if n_tokens + margin_tokens > max_tokens: 
            first_row_tokens = estimate_n_token(table2text(data.head(1))) 
            n_rows = (max_tokens - margin_tokens) // first_row_tokens
            
            if n_rows == 0:
                st.info(f"""The dataset is too large to be analyzed.  
                            It has reached the maximum estimation of {max_tokens:,} tokens.
                        """)
            
                analyze = False

        if analyze:  
            
            data = data.head(n_rows)
            prompt = table2text(data)
            
            if "progress_text" not in st.session_state:
                st.session_state["progress_text"] = {"val": 0, "text": "Analyzing the dataset"}
                st.session_state["re-attempt"] = 0

            my_bar = st.progress(st.session_state["progress_text"]["val"], 
                                 text = st.session_state["progress_text"]["text"])

            try:
                
                dashboard_title, coder, explainer, code_file = generate_code(data, prompt, api_key)
                generate_chart(data, coder)

                my_bar.progress(50, text = "Generating charts")

            except Exception as e:
                if "chart_response" in st.session_state:
                    del st.session_state["chart_response"]
                print(e)
                st.session_state['re-attempt'] += 1
                st.session_state["progress_text"] = {"val": 50, 
                                                     "text": f"{st.session_state['re-attempt']} attempt(s) to regenerate the charts"}

                st.rerun()

            my_bar.progress(100, "Done")
            my_bar.empty()

            generate_chart_header(dashboard_title, code_file)

            st.info(f"""The dataset is too large to be analyzed.  
                        It has reached the maximum estimation of {max_tokens:,} tokens.  
                        The system will analyze the first {n_rows} rows.""")
            
            explain_chart(prompt, explainer)
            
            st.session_state["progress_text"] = {"val": 0, "text": "Analyzing the dataset"}
            st.session_state['re-attempt'] = 0