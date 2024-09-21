import streamlit as st

import json
import google.generativeai as genai

from vertexai.preview import tokenization

def table2text(data):

    prompt = f"""there are {len(data.columns)} columns: {", ".join(data.columns)}. 
    These are the values: 
    """

    table_text = ""
    for row in data.astype(str).values:
        row = ", ".join(row)
        table_text += f"{row}.\n"

    prompt += table_text
    return prompt

def estimate_n_token(text):

    model_name = "gemini-1.5-flash"
    tokenizer = tokenization.get_tokenizer_for_model(model_name)

    result = tokenizer.count_tokens(text)
    return result.total_tokens
    # encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    # encoding = encoding.encode(text)

    # return len(encoding)

def generate_code(data, prompt, api_key):
    if "chart_response" not in st.session_state:

        genai.configure(api_key = api_key)

        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            system_instruction = """
            You are a data analyst, expert in analyzing complex and big data.
            Given the number of columns, column names and the values for each column, perform the 5 exploratory data analysis and provide the dashboard title.
            Assume there are a variable already initialized called data. 
            You should use a python package called plotly to visualize the data.
            The output must contain the first key called title for the dashboard title and second key called charts for the following items in JSON format when the main key is title, code, insights, and importance.
            1. The chart title
            2. The python code to generate the chart
            3. The explainations on the insights of each chart in details
            4. The importance or bussiness values of each chart in details
            """
        )

        response = model.generate_content(prompt)

        st.session_state["chart_response"] = response
        st.session_state["chart_usage"] = response.usage_metadata

    response = st.session_state["chart_response"]

    res = response.text.replace("json", "").replace("```\n", "").replace("```", "")
    res = json.loads(res)

    dashboard_title = res["title"]

    coder = []
    explainer = []

    code_file = f"# {dashboard_title}"

    for assistant in res["charts"]:
        coder.append(assistant["code"].replace("\nfig.show()", ""))
        explainer.append(f"""<p><strong>{assistant["title"]}</strong></p>
                            <p>{assistant["insights"]} {assistant["importance"]}</p>""")

        code_file += f"\n## {assistant['title']}\n\n{assistant['code']}\n"
        
    return dashboard_title, coder, explainer, code_file
    
def react_prompt(data, prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    response = model.generate_content(f"""
            You are a data analyst, expert in analyzing complex and big data.
            There is a CSV file called {st.session_state["file_name"]}. 
            {data}

            {prompt}

            """)

    return response.text