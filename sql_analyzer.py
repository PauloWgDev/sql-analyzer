import streamlit as st
import pandas as pd 
import numpy as np
import sqlglot
from sqlglot import exp

###   U T I L S 

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

def extract_joins(select):
    joins = []
    for join in select.find_all(exp.Join):
        join_type = join.args.get("kind", "INNER").upper()  # Default to INNER if not specified
        join_table = join.this.sql()
        on_conditions = []

        # Extract ON conditions if they exist
        if join.args.get("on"):
            on_conditions = extract_conditions(join.args["on"])

        joins.append({
            "table": join_table,
            "type": join_type,
            "on_conditions": on_conditions
        })
    return joins


def analyze_query(query):
    try:
        parsed = sqlglot.parse_one(query)

        selects = extract_selects(parsed)

        results = []

        columns = []
        tables = []
        conditions = []

        for select in selects:
            conditions = []

            # Columns
            columns = list(dict.fromkeys(col.sql() for col in select.find_all(exp.Column)))

            # Tables
            tables = list(dict.fromkeys(table.sql() for table in select.find_all(exp.Table)))

            # JOINS
            joins = extract_joins(select)

            # WHERE
            where = select.find(exp.Where)
            if where:
                conditions = extract_conditions(where.this)

            results.append({
                "query": select.sql(pretty=True),
                "columns": columns,
                "tables": tables,
                "conditions": conditions,
                "joins": joins
            })

        return parsed, results

    except Exception as e:
        return [{"error": str(e)}]


###  D I S P L A Y   P Á G I N A 

st.title('Analizador de Query SQL')

query = st.text_area('Insert Query here...')

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

        st.subheader("Joins")
        join_data = []
        for j in res["joins"]:
            join_data.append([j["type"], j["table"], ", ".join(j["on_conditions"])])
        st.dataframe(pd.DataFrame(join_data, columns=["Join Type", "Table", "ON Conditions"]))

        st.subheader("Conditions")
        st.dataframe(pd.DataFrame(res["conditions"], columns=["Condition"]))