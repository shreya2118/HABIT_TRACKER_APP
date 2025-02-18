import sqlite3
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import matplotlib.pyplot as plt
from tkinter import Toplevel


# Initialize Database
conn = sqlite3.connect("habits.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT NOT NULL,
        periodicity text not null,
        streak INTEGER DEFAULT 0
    )
""")
conn.commit()

#function to get habit analytics
def get_habit_stats():
    cursor.execute("SELECT COUNT(*) FROM habits")
    total_habits = cursor.fetchone()[0]

    cursor.execute("SELECT name, MAX(streak) FROM habits")
    longest_habit = cursor.fetchone()

    cursor.execute("SELECT periodicity, COUNT(*) FROM habits GROUP BY periodicity")
    periodicity_data = cursor.fetchall()

    return total_habits, longest_habit, periodicity_data



#function to open analytics page
def open_analytics():
    stats_window = Toplevel(root)
    stats_window.title("📊 Habit Analytics")
    stats_window.geometry("600x400")
    stats_window.configure(bg="#ADD8E6")  # Light blue background

    total_habits, longest_habit, periodicity_data = get_habit_stats()

    # Display statistics
    ttk.Label(stats_window, text="📈 Habit Analytics", font="Arial 20 bold", background="#ADD8E6").pack(pady=10)
    ttk.Label(stats_window, text=f"Total Habits: {total_habits}", font="Arial 14", background="#ADD8E6").pack()
    if longest_habit[0]:
        ttk.Label(stats_window, text=f"Longest Streak: {longest_habit[1]} (Habit: {longest_habit[0]})", font="Arial 14", background="#ADD8E6").pack()

    # Show periodicity data
    for periodicity, count in periodicity_data:
        ttk.Label(stats_window, text=f"{periodicity} Habits: {count}", font="Arial 14", background="#ADD8E6").pack()

    # Button to show graph
    ttk.Button(stats_window, text="📊 Show Streak Graph", command=show_streak_graph, bootstyle="primary outline").pack(pady=20)

#function to plot habit streak graph
def show_streak_graph():
    cursor.execute("SELECT name, streak FROM habits ORDER BY streak DESC")
    data = cursor.fetchall()

    if not data:
        return  # No data to show

    habits = [row[0] for row in data]
    streaks = [row[1] for row in data]

    plt.figure(figsize=(8, 4))
    plt.barh(habits, streaks, color="skyblue")
    plt.xlabel("Streak Count")
    plt.ylabel("Habit Name")
    plt.title("Habit Streak Trends")
    plt.gca().invert_yaxis()  # Highest streak at the top
    plt.show()
    
# Function to add a habit
def add_habit():
    name = name_entry.get()
    description = desc_entry.get()
    periodicity=periodicity_var.get()

    if name and description and periodicity:
        try:
            cursor.execute("INSERT INTO habits (name, description, periodicity) VALUES (?, ?,?)", (name, description,periodicity))
            conn.commit()
            name_entry.delete(0, ttk.END)
            desc_entry.delete(0, ttk.END)
            msg_label.config(text="✅ Habit added!", bootstyle="success")
            load_habits()
        except sqlite3.IntegrityError:
            msg_label.config(text="⚠️ Habit already exists!", bootstyle="danger")
    else:
        msg_label.config(text="⚠️ Please enter both name & description!", bootstyle="danger")

# Function to update habit streak
def update_streak(habit_id, increment):
    if increment:
        cursor.execute("UPDATE habits SET streak = streak + 1 WHERE id = ?", (habit_id,))
    else:
        cursor.execute("UPDATE habits SET streak = 0 WHERE id = ?", (habit_id,))
    conn.commit()
    load_habits()

# Function to delete a habit
def delete_habit(habit_id):
    cursor.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
    conn.commit()
    load_habits()

# Function to load habits dynamically into the table
def load_habits(filter_type="All"):
    habit_table.delete(*habit_table.get_children())  # Clear the table

    if filter_type == "Daily":
        cursor.execute("SELECT * FROM habits WHERE periodicity='Daily'")
    elif filter_type == "Weekly":
        cursor.execute("SELECT * FROM habits WHERE periodicity='Weekly'")
    else:
        cursor.execute("SELECT * FROM habits")

    habits = cursor.fetchall()

    for i, habit in enumerate(habits):
        habit_id, name, description, periodicity, streak = habit
        row_color = "light" if i % 2 == 0 else "dark"  # Alternate row colors
        habit_table.insert("", "end", values=(habit_id, name, description, periodicity, streak), tags=(row_color,))

def modify_selected_habit(action):
    selected_item = habit_table.selection()
    if selected_item:
        habit_id = habit_table.item(selected_item)["values"][0]

        if action == "increment":
            update_streak(habit_id, 1)
        elif action == "reset":
            update_streak(habit_id, 0)
        elif action == "delete":
            delete_habit(habit_id)


# Exit full-screen mode
def exit_fullscreen(event=None):
    root.attributes("-fullscreen", False)

# Main Window Setup (Full-screen)
root = ttk.Window(themename="superhero")  # Modern Theme
root.title("Habit Tracker")


# Bind keys to toggle full-screen mode

root.bind("<Escape>", exit_fullscreen)

# Title
ttk.Label(root, text="📌 Habit Tracker", font="Helvetica 28 bold", bootstyle="primary").pack(pady=15)

# Input Fields
input_frame = ttk.Frame(root)
input_frame.pack(pady=10)

ttk.Label(input_frame, text="Habit Name:", font="Arial 14").grid(row=0, column=0, padx=10)
name_entry = ttk.Entry(input_frame, width=30, font="Arial 14")
name_entry.grid(row=0, column=1, padx=10)

ttk.Label(input_frame, text="Description:", font="Arial 14").grid(row=1, column=0, padx=10)
desc_entry = ttk.Entry(input_frame, width=30, font="Arial 14")
desc_entry.grid(row=1, column=1, padx=10)

ttk.Label(input_frame, text="Frequency:", font="Arial 14").grid(row=2, column=0, padx=10)
periodicity_var = ttk.StringVar(value="Daily")
ttk.Combobox(input_frame, textvariable=periodicity_var, values=["Daily", "Weekly"], state="readonly", width=47).grid(row=2, column=1, padx=10)

# Add Button

ttk.Button(root, text="➕ Add Habit", command=add_habit, bootstyle="primary", padding=10).pack(pady=10)

# Message Label
msg_label = ttk.Label(root, text="", font="Arial 14 bold")
msg_label.pack()

# Habit Table (Treeview)
columns = ("ID", "Habit Name", "Description","periodicity", "Streak")
habit_table = ttk.Treeview(root, columns=columns, show="headings", height=10, bootstyle="dark")
habit_table.pack(pady=20, padx=40, fill="both", expand=True)

# Define Column Headings
habit_table.heading("ID", text="ID", anchor="center")
habit_table.heading("Habit Name", text="Habit Name", anchor="center")
habit_table.heading("Description", text="Description", anchor="center")
habit_table.heading("periodicity", text="Periodicity", anchor="center")
habit_table.heading("Streak", text="Streak", anchor="center")

habit_table.column("ID", width=50, anchor="center")
habit_table.column("Habit Name", width=200, anchor="center")
habit_table.column("Description", width=350, anchor="center")
habit_table.column("periodicity", width=150, anchor="center")
habit_table.column("Streak", width=100, anchor="center")

#alternate row colors
habit_table.tag_configure("light", background="DodgerBlue")
habit_table.tag_configure("dark", background="SlateBlue")


# Action Buttons (Increment, Reset, Delete)
action_frame = ttk.Frame(root)
action_frame.pack(pady=10)

ttk.Button(action_frame, text="✔ Increment", command=lambda: modify_selected_habit("increment"), bootstyle="success outline").pack(side="left", padx=10)
ttk.Button(action_frame, text="🔄 Reset", command=lambda: modify_selected_habit("reset"), bootstyle="warning outline").pack(side="left", padx=10)
ttk.Button(action_frame, text="🗑 Delete", command=lambda: modify_selected_habit("delete"), bootstyle="danger outline").pack(side="left", padx=10)

filter_frame=ttk.Frame(root)
filter_frame.pack(pady=10)

ttk.Button(filter_frame, text="Show All", command=lambda: load_habits("All"), bootstyle="primary outline").pack(side="left", padx=10)
ttk.Button(filter_frame, text="Daily Only", command=lambda: load_habits("Daily"), bootstyle="primary outline").pack(side="left", padx=10)
ttk.Button(filter_frame, text="Weekly Only", command=lambda: load_habits("Weekly"), bootstyle="primary outline").pack(side="left", padx=10)

ttk.Button(root, text="📊 View Habit Analytics", command=open_analytics, bootstyle="info outline").pack(pady=10)


load_habits()  # Load existing habits

root.mainloop()

# Close database connection
conn.close()
