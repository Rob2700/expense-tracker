import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# --- Session State ---
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

st.title("💸 Expense Tracker")

# --- Database ---
conn = sqlite3.connect("expenses.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    category TEXT,
    amount REAL
)
""")
conn.commit()

# --- Add Expense ---
st.subheader("Add Expense")

date = st.date_input("Date")
category = st.selectbox("Category", ["Food", "Gas", "Bills", "Entertainment"])
amount = st.number_input("Amount", min_value=0.0)

if st.button("Add Expense"):
    c.execute(
        "INSERT INTO expenses (date, category, amount) VALUES (?, ?, ?)",
        (str(date), category, amount)
    )
    conn.commit()
    st.success("Expense added!")
    st.rerun()

# --- Load Data ---
df = pd.read_sql("SELECT * FROM expenses", conn)

# Always convert date
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])

# --- Filters ---
st.subheader("Filters")

if not df.empty:
    start_date = st.date_input("Start Date", df["date"].min())
    end_date = st.date_input("End Date", df["date"].max())

    df = df[
        (df["date"] >= pd.to_datetime(start_date)) &
        (df["date"] <= pd.to_datetime(end_date))
    ]

    category_filter = st.selectbox(
        "Filter by Category",
        ["All"] + list(df["category"].unique())
    )

    if category_filter != "All":
        df = df[df["category"] == category_filter]
else:
    st.warning("No expenses yet. Add some data!")

# --- Expense List ---
st.markdown("### 📋 Expense List")

for _, row in df.iterrows():
    col1, col2, col3, col4, col5 = st.columns([3, 3, 2, 2, 2])

    col1.write(row["date"].strftime("%Y-%m-%d"))
    col2.write(row["category"])
    col3.write(f"${row['amount']}")

    # Edit
    if col4.button("Edit", use_container_width=True, key=f"edit_{row['id']}"):
        st.session_state.edit_id = row["id"]

    # Delete
    if col5.button("Delete", use_container_width=True, key=f"delete_{row['id']}"):
        c.execute("DELETE FROM expenses WHERE id = ?", (row["id"],))
        conn.commit()
        st.rerun()

# --- Edit Expense ---
if st.session_state.edit_id is not None:
    st.markdown("---")
    st.subheader("✏️ Edit Expense")

    edit_rows = df[df["id"] == st.session_state.edit_id]

    
    if edit_rows.empty:
        st.session_state.edit_id = None
        st.warning("Item no longer exists.")
        st.rerun()

    edit_row = edit_rows.iloc[0]

    new_date = st.date_input("Edit Date", pd.to_datetime(edit_row["date"]))
    new_category = st.selectbox(
        "Edit Category",
        ["Food", "Gas", "Bills", "Entertainment"],
        index=["Food", "Gas", "Bills", "Entertainment"].index(edit_row["category"])
    )
    new_amount = st.number_input("Edit Amount", value=float(edit_row["amount"]))

    col1, col2 = st.columns(2)

    if col1.button("Save Changes"):
        c.execute("""
            UPDATE expenses
            SET date = ?, category = ?, amount = ?
            WHERE id = ?
        """, (str(new_date), new_category, new_amount, st.session_state.edit_id))
        conn.commit()
        st.session_state.edit_id = None
        st.success("Updated successfully!")
        st.rerun()

    if col2.button("Cancel"):
        st.session_state.edit_id = None
        st.rerun()

# --- Dashboard ---
st.markdown("---")
st.subheader("📊 Dashboard")

total = df["amount"].sum()

col1, col2 = st.columns(2)

with col1:
    st.metric("Total Spending", f"${total}")

with col2:
    st.metric("Transactions", len(df))

# --- Monthly Chart ---
st.subheader("📅 Monthly Spending")

if not df.empty:
    df["month"] = df["date"].dt.to_period("M").astype(str)
    monthly_totals = df.groupby("month")["amount"].sum()
    st.line_chart(monthly_totals)
else:
    st.info("No data for monthly chart yet.")

# --- Bar Chart ---
st.subheader("Spending by Category")

if not df.empty:
    category_totals = df.groupby("category")["amount"].sum()
    st.bar_chart(category_totals)
else:
    st.info("No data for bar chart yet.")

# --- Pie Chart ---
st.subheader("Spending Distribution")

if not df.empty:
    category_totals = df.groupby("category")["amount"].sum()

    fig, ax = plt.subplots(facecolor='none')

    ax.pie(
        category_totals,
        labels=category_totals.index,
        autopct="%1.1f%%",
        textprops={'color': 'white'}
    )

    ax.set_facecolor('none')
    ax.set_title("Spending Distribution", color="white")

    st.pyplot(fig)
else:
    st.info("No data for pie chart yet.")