import streamlit as st
import pandas as pd 
import numpy as np
import sqlglot
from sqlglot import exp

st.title('Analizador de Query SQL')

query = st.text_area('Insert Query here...')

def extract_conditions(expression):
    conditions = []

    if isinstance(expression, (exp.And, exp.Or)):
        conditions += extract_conditions(expression.left)
        conditions += extract_conditions(expression.right)
    else:
        conditions.append(expression.sql())

    return conditions

def extract_selects(expression):
    selects = []

    if isinstance(expression, exp.Union):
        selects += extract_selects(expression.left)
        selects += extract_selects(expression.right)
    elif isinstance(expression, exp.Select):
        selects.append(expression)

    return selects


def analyze_query(query):
    try:
        parsed = sqlglot.parse_one(query)

        selects = extract_selects(parsed)

        results = []

        columns = []
        tables = []
        conditions = []

        for select in selects:
            columns = []
            tables = []
            conditions = []

            # Columns
            for col in select.find_all(exp.Column):
                columns.append(col.sql())

            # Tables
            for table in select.find_all(exp.Table):
                tables.append(table.sql())

            # WHERE
            where = select.find(exp.Where)
            if where:
                conditions = extract_conditions(where.this)

            results.append({
                "query": select.sql(pretty=True),
                "columns": columns,
                "tables": tables,
                "conditions": conditions
            })

        return parsed, results

    except Exception as e:
        return [{"error": str(e)}]


if query:
    full_query, results = analyze_query(query)

    st.subheader("Query")
    st.code(full_query.sql(pretty=True), language='sql')

    for i, res in enumerate(results):
        st.subheader(f"SELECT #{i+1}")

        if "error" in res:
            st.error(res["error"])
            continue

        st.code(res["query"], language='sql')

        st.subheader("Columns")
        st.dataframe(pd.DataFrame(res["columns"], columns=["Column"]))

        st.subheader("Tables")
        st.dataframe(pd.DataFrame(res["tables"], columns=["Table"]))

        st.subheader("Conditions")
        st.dataframe(pd.DataFrame(res["conditions"], columns=["Condition"]))