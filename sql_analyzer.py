import streamlit as st
import pandas as pd 
import numpy as np
import sqlglot
from sqlglot import exp

st.title('Analizador de Query SQL')

query = st.text_area('Insert Query here...')

def analyze_query(query):
    try:
        parsed = sqlglot.parse_one(query)

        columns = []
        tables = []
        conditions = []

        # Extract columns
        for col in parsed.find_all(exp.Column):
            columns.append(col.sql())

        # Extract tables
        for table in parsed.find_all(exp.Table):
            tables.append(table.sql())

        # Extract WHERE conditions
        where = parsed.find(exp.Where)
        if where:
            conditions.append(where.this.sql())

        return parsed, columns, tables, conditions

    except Exception as e:
        return [], [], [f"Error: {str(e)}"]


if query:
    parsed_query, cols, tabs, conds = analyze_query(query)

    st.subheader("Query")
    st.code(parsed_query.sql(pretty=True), language='sql')

    st.subheader("Columns")
    st.dataframe(pd.DataFrame(cols, columns=["Column"]))

    st.subheader("Tables")
    st.dataframe(pd.DataFrame(tabs, columns=["Table"]))

    st.subheader("Conditions")
    st.dataframe(pd.DataFrame(conds, columns=["Condition"]))