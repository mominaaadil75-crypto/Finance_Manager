import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from tkinter.font import Font
import sqlite3
from datetime import datetime, timedelta
import unittest
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import calendar
import re
import random
import pandas as pd
from fpdf import FPDF
import os
from PIL import Image, ImageTk

class DatabaseHandler:
    """Handles all database operations using SQLite"""
    def __init__(self, db_name='finance.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
        self.add_demo_data()
        
    def create_tables(self):
        """Create necessary tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Transactions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            description TEXT
        )
        ''')
        
        # Budgets table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            category TEXT PRIMARY KEY,
            amount REAL NOT NULL
        )
        ''')
        
        # Savings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS savings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL DEFAULT 0,
            target_date TEXT NOT NULL
        )
        ''')
        
        # Categories table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            name TEXT PRIMARY KEY,
            type TEXT NOT NULL
        )
        ''')
        
        self.conn.commit()
    
    def add_demo_data(self):
        """Add realistic demo data for showcasing the app"""
        cursor = self.conn.cursor()
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM transactions")
        if cursor.fetchone()[0] > 0:
            return
            
        # Add default categories
        income_categories = ["Salary", "Bonus", "Freelance", "Investment", "Dividends"]
        expense_categories = [
            "Rent", "Utilities", "Groceries", "Dining Out", "Transportation", 
            "Car Payment", "Insurance", "Healthcare", "Entertainment", 
            "Shopping", "Travel", "Education", "Gifts", "Savings"
        ]
        
        for cat in income_categories:
            cursor.execute("INSERT OR IGNORE INTO categories VALUES (?, ?)", (cat, "Income"))
        
        for cat in expense_categories:
            cursor.execute("INSERT OR IGNORE INTO categories VALUES (?, ?)", (cat, "Expense"))
        
        # Add sample transactions for past 6 months
        today = datetime.now()
        for month_offset in range(6, 0, -1):
            month_date = today - timedelta(days=30*month_offset)
            year = month_date.year
            month = month_date.month
            
            # Add income (salary on 1st of month)
            salary_amount = round(random.uniform(3500, 5000), 2)
            self.add_transaction("Income", "Salary", salary_amount, f"{year}-{month:02d}-01", "Monthly salary")
            
            # Add bonus (random chance)
            if random.random() < 0.3:
                bonus_amount = round(random.uniform(500, 2000), 2)
                self.add_transaction("Income", "Bonus", bonus_amount, f"{year}-{month:02d}-15", "Quarterly bonus")
            
            # Add expenses
            num_expenses = random.randint(15, 30)
            for _ in range(num_expenses):
                day = random.randint(1, 28)
                category = random.choice(expense_categories)
                amount = round(random.uniform(5, 300), 2)
                descriptions = {
                    "Rent": "Monthly rent payment",
                    "Utilities": "Electricity bill",
                    "Groceries": "Weekly groceries",
                    "Dining Out": "Dinner with friends",
                    "Transportation": "Gas refill",
                    "Car Payment": "Monthly car loan",
                    "Insurance": "Health insurance",
                    "Healthcare": "Doctor visit",
                    "Entertainment": "Movie tickets",
                    "Shopping": "New clothes",
                    "Travel": "Weekend getaway",
                    "Education": "Online course",
                    "Gifts": "Birthday present",
                    "Savings": "Monthly savings transfer"
                }
                description = descriptions.get(category, "Miscellaneous expense")
                
                self.add_transaction("Expense", category, amount, f"{year}-{month:02d}-{day:02d}", description)
        
        # Add budgets
        for cat in expense_categories:
            if random.random() < 0.7:  # 70% chance of having a budget
                budget = round(random.uniform(100, 1000), 2)
                self.set_budget(cat, budget)
        
        # Add savings goals
        goals = [
            ("Emergency Fund", 10000, "2024-12-31"),
            ("Vacation", 5000, "2024-06-30"),
            ("New Car", 25000, "2025-12-31")
        ]
        
        for goal, target, date in goals:
            current = round(random.uniform(0, target*0.7), 2)
            self.add_savings_goal(goal, target, date, current)
        
        self.conn.commit()
    
    # Transaction CRUD operations
    def add_transaction(self, trans_type, category, amount, date, description=""):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO transactions (type, category, amount, date, description)
            VALUES (?, ?, ?, ?, ?)
            ''', (trans_type, category, amount, date, description))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
    
    def get_transactions(self, month=None, year=None, category=None, search_term=None):
        cursor = self.conn.cursor()
        query = "SELECT * FROM transactions"
        params = []
        
        conditions = []
        if month and year:
            conditions.append("strftime('%m', date) = ? AND strftime('%Y', date) = ?")
            params.extend([f"{int(month):02d}", str(year)])
        if category:
            conditions.append("category = ?")
            params.append(category)
        if search_term:
            conditions.append("(description LIKE ? OR category LIKE ?)")
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def delete_transaction(self, transaction_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
    
    # Budget operations
    def set_budget(self, category, amount):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT OR REPLACE INTO budgets (category, amount)
            VALUES (?, ?)
            ''', (category, amount))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
    
    def get_budgets(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM budgets')
        return cursor.fetchall()
    
    def get_budget(self, category):
        cursor = self.conn.cursor()
        cursor.execute('SELECT amount FROM budgets WHERE category = ?', (category,))
        result = cursor.fetchone()
        return result[0] if result else 0
    
    # Savings operations
    def add_savings_goal(self, goal, target_amount, target_date, current_amount=0):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO savings (goal, target_amount, current_amount, target_date)
            VALUES (?, ?, ?, ?)
            ''', (goal, target_amount, current_amount, target_date))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
    
    def get_savings_goals(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM savings')
        return cursor.fetchall()
    
    def update_savings(self, goal_id, amount):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            UPDATE savings SET current_amount = current_amount + ?
            WHERE id = ?
            ''', (amount, goal_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
    
    def delete_savings_goal(self, goal_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM savings WHERE id = ?', (goal_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
    
    # Category operations
    def get_categories(self, type=None):
        cursor = self.conn.cursor()
        if type:
            cursor.execute('SELECT name FROM categories WHERE type = ?', (type,))
        else:
            cursor.execute('SELECT name FROM categories')
        return [row[0] for row in cursor.fetchall()]
    
    def add_category(self, name, type):
        try:
            cursor = self.conn.cursor()
            cursor.execute('INSERT INTO categories VALUES (?, ?)', (name, type))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
    
    def close(self):
        self.conn.close()


class FinanceManager:
    """Handles business logic and calculations"""
    def __init__(self, db_handler):
        self.db = db_handler
    
    def get_categories(self, type=None):
        """Get all categories or filtered by type"""
        return self.db.get_categories(type)
    
    def add_category(self, name, type):
        """Add a new custom category"""
        if not name.strip():
            return False, "Category name cannot be empty"
        if type not in ["Income", "Expense"]:
            return False, "Type must be Income or Expense"
        
        if self.db.add_category(name, type):
            return True, "Category added successfully"
        return False, "Error adding category"
    
    def add_transaction(self, trans_type, category, amount, date, description=""):
        # Validate category exists
        categories = self.get_categories(trans_type)
        if category not in categories:
            return False, "Invalid category"
        
        # Validate amount
        if amount <= 0:
            return False, "Amount must be positive"
        
        # Validate date format and validity
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return False, "Invalid date format (YYYY-MM-DD)"
        
        # Add to database
        if self.db.add_transaction(trans_type, category, amount, date, description):
            return True, "Transaction added successfully"
        return False, "Database error"
    
    def delete_transaction(self, transaction_id):
        if self.db.delete_transaction(transaction_id):
            return True, "Transaction deleted"
        return False, "Error deleting transaction"
    
    def set_budget(self, category, amount):
        # Validate category exists
        categories = self.get_categories("Expense")
        if category not in categories:
            return False, "Invalid category"
        
        # Validate amount
        if amount <= 0:
            return False, "Amount must be positive"
        
        # Set budget
        if self.db.set_budget(category, amount):
            return True, "Budget set successfully"
        return False, "Database error"
    
    def get_monthly_summary(self, month, year):
        transactions = self.db.get_transactions(month, year)
        income = 0
        expenses = 0
        
        for t in transactions:
            if t[1] == "Income":
                income += t[3]
            else:
                expenses += t[3]
        
        budget_data = self.db.get_budgets()
        budgets = {b[0]: b[1] for b in budget_data}
        actual_expenses = {category: 0 for category in self.get_categories("Expense")}
        
        for t in transactions:
            if t[1] == "Expense":
                if t[2] in actual_expenses:
                    actual_expenses[t[2]] += t[3]
        
        budget_status = {}
        for category, budget in budgets.items():
            actual = actual_expenses.get(category, 0)
            remaining = budget - actual
            status = "Within Budget" if remaining >= 0 else "Over Budget"
            budget_status[category] = {
                "budget": budget,
                "actual": actual,
                "remaining": abs(remaining),
                "status": status,
                "percentage": (actual / budget) * 100 if budget > 0 else 0
            }
        
        return {
            "income": income,
            "expenses": expenses,
            "net": income - expenses,
            "budget_status": budget_status
        }
    
    def get_yearly_summary(self, year):
        months = []
        income = []
        expenses = []
        
        for month in range(1, 13):
            summary = self.get_monthly_summary(month, year)
            months.append(calendar.month_abbr[month])
            income.append(summary["income"])
            expenses.append(summary["expenses"])
        
        return {
            "months": months,
            "income": income,
            "expenses": expenses,
            "net": [i - e for i, e in zip(income, expenses)]
        }
    
    def add_savings_goal(self, goal, target_amount, target_date, current_amount=0):
        # Validate goal name
        if not goal.strip():
            return False, "Goal name cannot be empty"
        
        # Validate target amount
        if target_amount <= 0:
            return False, "Target amount must be positive"
        
        # Validate date format and validity
        try:
            datetime.strptime(target_date, "%Y-%m-%d")
        except ValueError:
            return False, "Invalid date format (YYYY-MM-DD)"
        
        # Add to database
        if self.db.add_savings_goal(goal, target_amount, target_date, current_amount):
            return True, "Savings goal added"
        return False, "Database error"
    
    def update_savings(self, goal_id, amount):
        # Validate amount
        if amount <= 0:
            return False, "Amount must be positive"
        
        # Update savings
        if self.db.update_savings(goal_id, amount):
            return True, "Savings updated"
        return False, "Database error"
    
    def delete_savings_goal(self, goal_id):
        if self.db.delete_savings_goal(goal_id):
            return True, "Savings goal deleted"
        return False, "Error deleting goal"
    
    def export_transactions(self, file_path, file_type="csv"):
        """Export transactions to CSV or Excel"""
        transactions = self.db.get_transactions()
        df = pd.DataFrame(transactions, columns=["ID", "Type", "Category", "Amount", "Date", "Description"])
        
        try:
            if file_type == "csv":
                df.to_csv(file_path, index=False)
            elif file_type == "excel":
                df.to_excel(file_path, index=False)
            return True, "Export successful"
        except Exception as e:
            return False, f"Export failed: {str(e)}"


class FinanceApp(tk.Tk):
    """Main application class with modern UI"""
    def __init__(self):
        super().__init__()
        self.title("Personal Finance Manager")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        
        # Modern color palette
        self.colors = {
            "primary": "#3498db",
            "primary_dark": "#2980b9",
            "secondary": "#2ecc71",
            "secondary_dark": "#27ae60",
            "background": "#f5f7fa",
            "card": "#ffffff",
            "text": "#2c3e50",
            "text_light": "#7f8c8d",
            "positive": "#27ae60",
            "negative": "#e74c3c",
            "warning": "#f39c12"
        }
        
        # Initialize database and manager
        self.db = DatabaseHandler()
        self.manager = FinanceManager(self.db)
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.configure_styles()
        
        # Create main frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.dashboard_tab = ttk.Frame(self.notebook)
        self.transaction_tab = ttk.Frame(self.notebook)
        self.budget_tab = ttk.Frame(self.notebook)
        self.savings_tab = ttk.Frame(self.notebook)
        self.reports_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.dashboard_tab, text="Dashboard")
        self.notebook.add(self.transaction_tab, text="Transactions")
        self.notebook.add(self.budget_tab, text="Budgets")
        self.notebook.add(self.savings_tab, text="Savings")
        self.notebook.add(self.reports_tab, text="Reports")
        
        # Build each tab
        self.create_dashboard_tab()
        self.create_transaction_tab()
        self.create_budget_tab()
        self.create_savings_tab()
        self.create_reports_tab()
        
        # Load initial data
        self.update_dashboard()
        self.update_transactions_view()
        self.update_budgets_view()
        self.update_savings_view()
        
        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def configure_styles(self):
        """Configure custom styles for the application"""
        # Main styles
        self.style.configure(".", 
                           background=self.colors["background"],
                           foreground=self.colors["text"],
                           font=("Segoe UI", 10))
        
        # Frame styles
        self.style.configure("TFrame", background=self.colors["background"])
        self.style.configure("Card.TFrame", 
                           background=self.colors["card"],
                           borderwidth=1,
                           relief="solid",
                           bordercolor="#e0e0e0")
        
        # Button styles
        self.style.configure("TButton", 
                           font=("Segoe UI", 10, "bold"),
                           padding=8,
                           background=self.colors["primary"],
                           foreground="white",
                           borderwidth=0)
        self.style.map("TButton", 
                      background=[("active", self.colors["primary_dark"])])
        
        self.style.configure("Secondary.TButton",
                           background=self.colors["secondary"])
        self.style.map("Secondary.TButton",
                      background=[("active", self.colors["secondary_dark"])])
        
        # Label styles
        self.style.configure("Header.TLabel", 
                           font=("Segoe UI", 16, "bold"),
                           background=self.colors["background"],
                           foreground=self.colors["text"])
        
        self.style.configure("Subheader.TLabel", 
                           font=("Segoe UI", 12, "bold"),
                           background=self.colors["background"],
                           foreground=self.colors["text"])
        
        self.style.configure("Positive.TLabel", 
                           font=("Segoe UI", 12, "bold"),
                           foreground=self.colors["positive"])
        
        self.style.configure("Negative.TLabel", 
                           font=("Segoe UI", 12, "bold"),
                           foreground=self.colors["negative"])
        
        self.style.configure("Warning.TLabel",
                           font=("Segoe UI", 12, "bold"),
                           foreground=self.colors["warning"])
        
        # Notebook styles
        self.style.configure("TNotebook", background=self.colors["background"])
        self.style.configure("TNotebook.Tab", 
                           font=("Segoe UI", 10, "bold"),
                           padding=(12, 6),
                           background=self.colors["background"],
                           foreground=self.colors["text_light"])
        self.style.map("TNotebook.Tab", 
                      background=[("selected", self.colors["primary"])],
                      foreground=[("selected", "white")])
        
        # Entry and Combobox styles
        self.style.configure("TEntry",
                           fieldbackground="white",
                           bordercolor="#e0e0e0",
                           lightcolor="#e0e0e0",
                           darkcolor="#e0e0e0")
        
        self.style.configure("TCombobox",
                          fieldbackground="white",
                          bordercolor="#e0e0e0",
                          lightcolor="#e0e0e0",
                          darkcolor="#e0e0e0")
        
        # Treeview styles
        self.style.configure("Treeview",
                           background="white",
                           foreground=self.colors["text"],
                           rowheight=25,
                           fieldbackground="white",
                           bordercolor="#e0e0e0",
                           lightcolor="#e0e0e0",
                           darkcolor="#e0e0e0")
        
        self.style.configure("Treeview.Heading",
                           font=("Segoe UI", 10, "bold"),
                           background=self.colors["primary"],
                           foreground="white",
                           relief="flat")
        
        self.style.map("Treeview",
                      background=[("selected", self.colors["primary_dark"])])
    
    def create_dashboard_tab(self):
        """Create the dashboard tab with financial overview"""
        # Header
        header_frame = ttk.Frame(self.dashboard_tab)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, text="Financial Dashboard", style="Header.TLabel"
                 ).pack(side=tk.LEFT, padx=10)
        
        # Date selection
        date_frame = ttk.Frame(header_frame)
        date_frame.pack(side=tk.RIGHT, padx=10)
        
        ttk.Label(date_frame, text="Select Month:").grid(row=0, column=0, padx=5)
        
        self.month_var = tk.StringVar()
        self.month_combobox = ttk.Combobox(
            date_frame, textvariable=self.month_var, width=12,
            values=[calendar.month_name[i] for i in range(1, 13)],
            state="readonly"
        )
        self.month_combobox.current(datetime.now().month - 1)
        self.month_combobox.grid(row=0, column=1, padx=5)
        
        ttk.Label(date_frame, text="Year:").grid(row=0, column=2, padx=5)
        
        self.year_var = tk.StringVar(value=str(datetime.now().year))
        year_combobox = ttk.Combobox(
            date_frame, textvariable=self.year_var, width=8,
            values=[str(year) for year in range(2020, 2031)],
            state="readonly")
        year_combobox.grid(row=0, column=3, padx=5)
        
        ttk.Button(date_frame, text="Update", 
                  command=self.update_dashboard).grid(row=0, column=4, padx=10)
        
        # Summary cards
        summary_frame = ttk.Frame(self.dashboard_tab)
        summary_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Income card
        income_card = ttk.Frame(summary_frame, style="Card.TFrame", padding=15)
        income_card.pack(side=tk.LEFT, expand=True, padx=10)
        ttk.Label(income_card, text="INCOME", style="Subheader.TLabel"
                 ).pack(fill=tk.X, pady=(0, 10))
        self.income_label = ttk.Label(income_card, text="$0.00", 
                                     style="Positive.TLabel")
        self.income_label.pack()
        
        # Expense card
        expense_card = ttk.Frame(summary_frame, style="Card.TFrame", padding=15)
        expense_card.pack(side=tk.LEFT, expand=True, padx=10)
        ttk.Label(expense_card, text="EXPENSES", style="Subheader.TLabel"
                 ).pack(fill=tk.X, pady=(0, 10))
        self.expense_label = ttk.Label(expense_card, text="$0.00", 
                                      style="Negative.TLabel")
        self.expense_label.pack()
        
        # Net card
        net_card = ttk.Frame(summary_frame, style="Card.TFrame", padding=15)
        net_card.pack(side=tk.LEFT, expand=True, padx=10)
        ttk.Label(net_card, text="NET BALANCE", style="Subheader.TLabel"
                 ).pack(fill=tk.X, pady=(0, 10))
        self.net_label = ttk.Label(net_card, text="$0.00", font=("Segoe UI", 12, "bold"))
        self.net_label.pack()
        
        # Charts
        chart_frame = ttk.Frame(self.dashboard_tab)
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Expense breakdown chart
        expense_chart_frame = ttk.Frame(chart_frame, style="Card.TFrame", padding=10)
        expense_chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        ttk.Label(expense_chart_frame, text="Expense Breakdown", style="Subheader.TLabel"
                 ).pack(fill=tk.X, pady=(0, 10))
        
        self.expense_figure = Figure(figsize=(5, 4), dpi=100, facecolor=self.colors["card"])
        self.expense_canvas = FigureCanvasTkAgg(self.expense_figure, expense_chart_frame)
        self.expense_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Budget status chart
        budget_chart_frame = ttk.Frame(chart_frame, style="Card.TFrame", padding=10)
        budget_chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        ttk.Label(budget_chart_frame, text="Budget Status", style="Subheader.TLabel"
                 ).pack(fill=tk.X, pady=(0, 10))
        
        self.budget_figure = Figure(figsize=(5, 4), dpi=100, facecolor=self.colors["card"])
        self.budget_canvas = FigureCanvasTkAgg(self.budget_figure, budget_chart_frame)
        self.budget_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Yearly trend chart
        yearly_frame = ttk.Frame(self.dashboard_tab, style="Card.TFrame", padding=10)
        yearly_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        ttk.Label(yearly_frame, text="Yearly Trend", style="Subheader.TLabel"
                 ).pack(fill=tk.X, pady=(0, 10))
        
        self.yearly_figure = Figure(figsize=(10, 3), dpi=100, facecolor=self.colors["card"])
        self.yearly_canvas = FigureCanvasTkAgg(self.yearly_figure, yearly_frame)
        self.yearly_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def update_dashboard(self):
        """Update dashboard with current financial data"""
        try:
            month_num = datetime.strptime(self.month_var.get(), "%B").month
            year = int(self.year_var.get())
            
            summary = self.manager.get_monthly_summary(month_num, year)
            yearly_summary = self.manager.get_yearly_summary(year)
            
            # Update summary cards
            self.income_label.config(text=f"${summary['income']:,.2f}")
            self.expense_label.config(text=f"${summary['expenses']:,.2f}")
            
            net_text = f"${summary['net']:,.2f}"
            if summary['net'] >= 0:
                self.net_label.config(text=net_text, foreground=self.colors["positive"])
            else:
                self.net_label.config(text=net_text, foreground=self.colors["negative"])
            
            # Update expense breakdown chart
            self.expense_figure.clear()
            ax = self.expense_figure.add_subplot(111)
            
            # Prepare expense data
            expenses_by_category = {}
            transactions = self.db.get_transactions(month_num, year)
            for t in transactions:
                if t[1] == "Expense":
                    category = t[2]
                    expenses_by_category[category] = expenses_by_category.get(category, 0) + t[3]
            
            if expenses_by_category:
                labels = list(expenses_by_category.keys())
                values = list(expenses_by_category.values())
                
                # Sort by amount (descending)
                sorted_data = sorted(zip(values, labels), reverse=True)
                values, labels = zip(*sorted_data)
                
                # Use a modern color palette
                colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', 
                         '#1abc9c', '#d35400', '#34495e', '#7f8c8d', '#c0392b']
                
                # Add percentage labels inside the pie chart
                def autopct_format(values):
                    def my_format(pct):
                        total = sum(values)
                        val = int(round(pct*total/100.0))
                        return f'{pct:.1f}%\n(${val:,})'
                    return my_format
                
                wedges, texts, autotexts = ax.pie(
                    values, labels=labels, colors=colors[:len(values)],
                    autopct=autopct_format(values), startangle=90,
                    textprops={'fontsize': 8})
                
                # Make labels more readable
                for text in texts + autotexts:
                    text.set_fontsize(8)
                
                ax.set_title('Expense Distribution', fontsize=10, pad=20)
                ax.axis('equal')
            else:
                ax.text(0.5, 0.5, 'No expense data', 
                       horizontalalignment='center', verticalalignment='center')
            
            self.expense_canvas.draw()
            
            # Update budget status chart
            self.budget_figure.clear()
            ax = self.budget_figure.add_subplot(111)
            
            if summary['budget_status']:
                categories = []
                percentages = []
                status_colors = []
                
                for category, data in summary['budget_status'].items():
                    if data['budget'] > 0:  # Only show categories with budgets
                        categories.append(category)
                        percentage = data['percentage']
                        percentages.append(percentage)
                        status_colors.append(self.colors["positive"] if percentage <= 100 else self.colors["negative"])
                
                if categories:
                    # Sort by percentage (descending)
                    sorted_data = sorted(zip(percentages, categories, status_colors), reverse=True)
                    percentages, categories, status_colors = zip(*sorted_data)
                    
                    bars = ax.barh(categories, percentages, color=status_colors)
                    ax.set_xlabel('Percentage Used (%)', fontsize=9)
                    ax.set_title('Budget Utilization', fontsize=10, pad=15)
                    ax.set_xlim(0, max(percentages) * 1.2)
                    
                    # Customize appearance
                    ax.tick_params(axis='both', which='major', labelsize=8)
                    ax.grid(axis='x', linestyle='--', alpha=0.7)
                    
                    # Add value labels
                    for bar in bars:
                        width = bar.get_width()
                        ax.text(width + 1, bar.get_y() + bar.get_height()/2, 
                                f'{width:.1f}%', ha='left', va='center', fontsize=8)
            else:
                ax.text(0.5, 0.5, 'No budget data', 
                       horizontalalignment='center', verticalalignment='center')
            
            self.budget_canvas.draw()
            
            # Update yearly trend chart
            self.yearly_figure.clear()
            ax = self.yearly_figure.add_subplot(111)
            
            if yearly_summary["months"]:
                months = yearly_summary["months"]
                income = yearly_summary["income"]
                expenses = yearly_summary["expenses"]
                net = yearly_summary["net"]
                
                # Plot income and expenses
                ax.plot(months, income, label='Income', color=self.colors["positive"], marker='o', linewidth=2)
                ax.plot(months, expenses, label='Expenses', color=self.colors["negative"], marker='o', linewidth=2)
                
                # Add net values as bars
                net_colors = [self.colors["positive"] if val >= 0 else self.colors["negative"] for val in net]
                ax.bar(months, net, label='Net', color=net_colors, alpha=0.3)
                
                # Customize appearance
                ax.set_title('Monthly Trends', fontsize=10, pad=15)
                ax.set_ylabel('Amount ($)', fontsize=9)
                ax.legend(fontsize=8)
                ax.grid(True, linestyle='--', alpha=0.7)
                ax.tick_params(axis='both', which='major', labelsize=8)
                
                # Rotate x-axis labels for better fit
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
                
                # Add value labels for the last month
                last_month = len(months) - 1
                ax.text(months[last_month], income[last_month], f'${income[last_month]:,.0f}', 
                        ha='center', va='bottom', fontsize=8)
                ax.text(months[last_month], expenses[last_month], f'${expenses[last_month]:,.0f}', 
                        ha='center', va='top', fontsize=8)
            else:
                ax.text(0.5, 0.5, 'No yearly data available', 
                       horizontalalignment='center', verticalalignment='center')
            
            self.yearly_canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update dashboard: {str(e)}")

    # ================== VALIDATION HELPERS ================== #
    def validate_number(self, value):
        """Validate if input is a positive number"""
        if not value:
            return False
        try:
            num = float(value)
            return num > 0
        except ValueError:
            return False

    def validate_date(self, date_str):
        """Validate date format (YYYY-MM-DD)"""
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(pattern, date_str):
            return False
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def validate_non_empty(self, *fields):
        """Validate that fields are not empty"""
        return all(field.get().strip() for field in fields)

    def validate_savings_goal(self, goal):
        """Validate savings goal name"""
        return bool(goal.strip())
    
    # ================== TRANSACTION TAB ================== #
    def create_transaction_tab(self):
        """Create transaction management tab"""
    # Main container
        container = ttk.Frame(self.transaction_tab)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
        # Left panel - Form and filters
        left_panel = ttk.Frame(container)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
            
        # Form frame
        form_frame = ttk.LabelFrame(left_panel, text="Add New Transaction", padding=10)
        form_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Type selection
        ttk.Label(form_frame, text="Type:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.trans_type = tk.StringVar(value="Expense")
        ttk.Radiobutton(form_frame, text="Income", variable=self.trans_type, value="Income"
                    ).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Radiobutton(form_frame, text="Expense", variable=self.trans_type, value="Expense"
                    ).grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        
        # Category
        ttk.Label(form_frame, text="Category:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.trans_category = ttk.Combobox(form_frame, values=self.manager.get_categories())
        self.trans_category.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W, columnspan=2)
        self.trans_category.current(0)
        
        # Add category button
        ttk.Button(form_frame, text="+", width=3,
                command=self.add_category_dialog).grid(row=1, column=3, padx=5)
        
        # Amount
        ttk.Label(form_frame, text="Amount:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.trans_amount = ttk.Entry(form_frame, width=15)
        self.trans_amount.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Date
        ttk.Label(form_frame, text="Date (YYYY-MM-DD):").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.trans_date = ttk.Entry(form_frame, width=15)
        self.trans_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.trans_date.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        self.trans_desc = ttk.Entry(form_frame, width=30)
        self.trans_desc.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W, columnspan=2)
        
        # Add button
        ttk.Button(form_frame, text="Add Transaction", 
                command=self.add_transaction).grid(row=5, column=1, padx=5, pady=10, sticky=tk.W)
        
        # Filters frame
        filter_frame = ttk.LabelFrame(left_panel, text="Filter Transactions", padding=10)
        filter_frame.pack(fill=tk.X, pady=10)
        
        # Category filter
        ttk.Label(filter_frame, text="Category:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.filter_category = ttk.Combobox(filter_frame, values=["All"] + self.manager.get_categories())
        self.filter_category.set("All")
        self.filter_category.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Date range filter
        ttk.Label(filter_frame, text="Date Range:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.filter_date_from = ttk.Entry(filter_frame, width=12)
        self.filter_date_from.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(filter_frame, text="to").grid(row=1, column=2, padx=5, pady=5)
        self.filter_date_to = ttk.Entry(filter_frame, width=12)
        self.filter_date_to.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Search term
        ttk.Label(filter_frame, text="Search:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.search_term = ttk.Entry(filter_frame, width=30)
        self.search_term.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W, columnspan=3)
        
        # Filter buttons
        button_frame = ttk.Frame(filter_frame)
        button_frame.grid(row=3, column=0, columnspan=4, pady=5)
        
        ttk.Button(button_frame, text="Apply Filters", 
                command=self.apply_filters).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Filters", 
                command=self.clear_filters).pack(side=tk.LEFT, padx=5)
        
        # Export buttons
        export_frame = ttk.LabelFrame(left_panel, text="Export Transactions", padding=10)
        export_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(export_frame, text="Export to CSV", 
                command=lambda: self.export_transactions("csv")).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(export_frame, text="Export to Excel", 
                command=lambda: self.export_transactions("excel")).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(export_frame, text="Export to PDF", 
                command=lambda: self.export_transactions("pdf")).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Right panel - Transactions list
        right_panel = ttk.Frame(container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Transactions list
        list_frame = ttk.LabelFrame(right_panel, text="Recent Transactions", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for transactions
        columns = ("id", "type", "category", "amount", "date", "description")
        self.trans_tree = ttk.Treeview(
            list_frame, columns=columns, show="headings", selectmode="browse")
        
        # Configure columns
        self.trans_tree.heading("id", text="ID")
        self.trans_tree.heading("type", text="Type")
        self.trans_tree.heading("category", text="Category")
        self.trans_tree.heading("amount", text="Amount")
        self.trans_tree.heading("date", text="Date")
        self.trans_tree.heading("description", text="Description")
        
        self.trans_tree.column("id", width=50, anchor=tk.CENTER)
        self.trans_tree.column("type", width=80, anchor=tk.CENTER)
        self.trans_tree.column("category", width=100, anchor=tk.CENTER)
        self.trans_tree.column("amount", width=100, anchor=tk.CENTER)
        self.trans_tree.column("date", width=100, anchor=tk.CENTER)
        self.trans_tree.column("description", width=200, anchor=tk.W)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.trans_tree.yview)
        self.trans_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.trans_tree.pack(fill=tk.BOTH, expand=True)
        
        # Delete button
        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Delete Selected", 
                command=self.delete_transaction).pack(side=tk.RIGHT, padx=5)

    def add_category_dialog(self):
        """Open dialog to add a new category"""
        dialog = tk.Toplevel(self)
        dialog.title("Add New Category")
        dialog.geometry("400x200")
        dialog.transient(self)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Category Name:").pack(padx=10, pady=(20, 5))
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.pack(padx=10, pady=5)
        
        ttk.Label(dialog, text="Type:").pack(padx=10, pady=5)
        type_var = tk.StringVar(value="Expense")
        ttk.Radiobutton(dialog, text="Income", variable=type_var, value="Income"
                    ).pack(padx=10, pady=5, anchor=tk.W)
        ttk.Radiobutton(dialog, text="Expense", variable=type_var, value="Expense"
                    ).pack(padx=10, pady=5, anchor=tk.W)
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(padx=10, pady=10)
        
        ttk.Button(button_frame, text="Add Category", 
                command=lambda: self.add_category(name_entry.get(), type_var.get(), dialog)
                ).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def add_category(self, name, type, dialog):
        """Add a new category to the system"""
        if not name.strip():
            messagebox.showerror("Error", "Category name cannot be empty")
            return
            
        success, message = self.manager.add_category(name, type)
        if success:
            messagebox.showinfo("Success", message)
            # Refresh category dropdowns
            self.trans_category['values'] = self.manager.get_categories()
            self.filter_category['values'] = ["All"] + self.manager.get_categories()
            dialog.destroy()
        else:
            messagebox.showerror("Error", message)

    def apply_filters(self):
        """Apply filters to transactions view"""
        category = self.filter_category.get() if self.filter_category.get() != "All" else None
        date_from = self.filter_date_from.get() or None
        date_to = self.filter_date_to.get() or None
        search_term = self.search_term.get() or None
        
        # Validate dates if provided
        if date_from and not self.validate_date(date_from):
            messagebox.showerror("Error", "Invalid 'From' date format (YYYY-MM-DD)")
            return
        if date_to and not self.validate_date(date_to):
            messagebox.showerror("Error", "Invalid 'To' date format (YYYY-MM-DD)")
            return
            
        # Clear existing data
        for row in self.trans_tree.get_children():
            self.trans_tree.delete(row)
        
        # Get filtered transactions
        transactions = self.db.get_transactions(
            category=category, 
            search_term=search_term
        )
        
        # Apply date filters manually
        if date_from or date_to:
            filtered_transactions = []
            date_from_dt = datetime.strptime(date_from, "%Y-%m-%d") if date_from else datetime.min
            date_to_dt = datetime.strptime(date_to, "%Y-%m-%d") if date_to else datetime.max
            
            for t in transactions:
                trans_date = datetime.strptime(t[4], "%Y-%m-%d")
                if date_from_dt <= trans_date <= date_to_dt:
                    filtered_transactions.append(t)
            transactions = filtered_transactions
        
        # Add to treeview
        for trans in transactions:
            self.trans_tree.insert("", tk.END, values=trans)

    def clear_filters(self):
        """Clear all filters and reset view"""
        self.filter_category.set("All")
        self.filter_date_from.delete(0, tk.END)
        self.filter_date_to.delete(0, tk.END)
        self.search_term.delete(0, tk.END)
        self.update_transactions_view()

    def export_transactions(self, file_type):
        """Export transactions to the selected file type"""
        # Get all transactions
        transactions = self.db.get_transactions()
        
        if not transactions:
            messagebox.showwarning("Warning", "No transactions to export")
            return
            
        # Create a DataFrame
        df = pd.DataFrame(transactions, columns=["ID", "Type", "Category", "Amount", "Date", "Description"])
        
        # Get save file path
        file_ext = {
            "csv": ("CSV Files", "*.csv"),
            "excel": ("Excel Files", "*.xlsx"),
            "pdf": ("PDF Files", "*.pdf")
        }[file_type]
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=file_ext[1],
            filetypes=[file_ext, ("All Files", "*.*")],
            title=f"Export Transactions as {file_type.upper()}"
        )
        
        if not file_path:
            return  # User canceled
            
        try:
            if file_type == "csv":
                df.to_csv(file_path, index=False)
            elif file_type == "excel":
                df.to_excel(file_path, index=False)
            elif file_type == "pdf":
                # Create a PDF report
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "Transaction Report", 0, 1, "C")
                pdf.set_font("Arial", "", 10)
                
                # Add date
                pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1)
                pdf.ln(10)
                
                # Create table
                col_widths = [15, 20, 30, 20, 25, 80]
                headers = ["ID", "Type", "Category", "Amount", "Date", "Description"]
                
                # Header row
                pdf.set_fill_color(200, 220, 255)
                for i, header in enumerate(headers):
                    pdf.cell(col_widths[i], 10, header, 1, 0, "C", 1)
                pdf.ln()
                
                # Data rows
                pdf.set_fill_color(255, 255, 255)
                for _, row in df.iterrows():
                    for i, col in enumerate(headers):
                        value = str(row[col])
                        if col == "Amount":
                            # Highlight income vs expense
                            if row["Type"] == "Income":
                                pdf.set_text_color(0, 128, 0)  # Green for income
                            else:
                                pdf.set_text_color(220, 0, 0)  # Red for expenses
                        else:
                            pdf.set_text_color(0, 0, 0)
                            
                        pdf.cell(col_widths[i], 10, value, 1, 0, "C")
                    pdf.ln()
                
                # Summary
                pdf.ln(10)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, f"Total Income: ${df[df['Type'] == 'Income']['Amount'].sum():,.2f}", 0, 1)
                pdf.cell(0, 10, f"Total Expenses: ${df[df['Type'] == 'Expense']['Amount'].sum():,.2f}", 0, 1)
                net = df[df['Type'] == 'Income']['Amount'].sum() - df[df['Type'] == 'Expense']['Amount'].sum()
                pdf.cell(0, 10, f"Net Balance: ${net:,.2f}", 0, 1)
                
                pdf.output(file_path)
                
            messagebox.showinfo("Success", f"Transactions exported successfully to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export transactions: {str(e)}")

    def add_transaction(self):
        """Add a new transaction from form data"""
        # Get values
        trans_type = self.trans_type.get()
        category = self.trans_category.get()
        amount = self.trans_amount.get()
        date = self.trans_date.get()
        description = self.trans_desc.get()
        
        # Validate inputs
        if not self.validate_non_empty(self.trans_amount, self.trans_date):
            messagebox.showerror("Error", "Amount and Date are required fields")
            return
            
        if not self.validate_number(amount):
            messagebox.showerror("Error", "Amount must be a positive number")
            return
            
        if not self.validate_date(date):
            messagebox.showerror("Error", "Date must be in YYYY-MM-DD format")
            return
            
        # Convert amount to float
        try:
            amount = float(amount)
            success, message = self.manager.add_transaction(
                trans_type, category, amount, date, description)
            
            if success:
                messagebox.showinfo("Success", message)
                self.update_transactions_view()
                self.update_dashboard()
                # Clear form
                self.trans_amount.delete(0, tk.END)
                self.trans_desc.delete(0, tk.END)
            else:
                messagebox.showerror("Error", message)
        except ValueError:
            messagebox.showerror("Error", "Invalid amount. Please enter a number.")

    def delete_transaction(self):
        """Delete selected transaction"""
        selected = self.trans_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a transaction to delete")
            return
            
        item = self.trans_tree.item(selected[0])
        trans_id = item['values'][0]
        
        if messagebox.askyesno("Confirm", "Delete this transaction?"):
            success, message = self.manager.delete_transaction(trans_id)
            if success:
                messagebox.showinfo("Success", message)
                self.update_transactions_view()
                self.update_dashboard()
            else:
                messagebox.showerror("Error", message)

    def update_transactions_view(self):
        """Refresh transactions list"""
        # Clear existing data
        for row in self.trans_tree.get_children():
            self.trans_tree.delete(row)
        
        # Get transactions from database
        transactions = self.db.get_transactions()
        
        # Add to treeview
        for trans in transactions:
            self.trans_tree.insert("", tk.END, values=trans)

    # ================== BUDGET TAB ================== #
    def create_budget_tab(self):
        """Create budget management tab"""
        # Main container
        container = ttk.Frame(self.budget_tab)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Budget form
        left_panel = ttk.Frame(container)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Budget form
        form_frame = ttk.LabelFrame(left_panel, text="Set Budget", padding=10)
        form_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Category
        ttk.Label(form_frame, text="Category:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.budget_category = ttk.Combobox(form_frame, values=self.manager.get_categories("Expense"))
        self.budget_category.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.budget_category.current(0)
        
        # Amount
        ttk.Label(form_frame, text="Amount:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.budget_amount = ttk.Entry(form_frame, width=15)
        self.budget_amount.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Set button
        ttk.Button(form_frame, text="Set Budget", 
                command=self.set_budget).grid(row=2, column=1, padx=5, pady=10, sticky=tk.W)
        
        # Progress summary
        progress_frame = ttk.LabelFrame(left_panel, text="Budget Progress", padding=10)
        progress_frame.pack(fill=tk.X, pady=10)
        
        self.budget_progress_vars = {}
        row = 0
        for category in self.manager.get_categories("Expense"):
            ttk.Label(progress_frame, text=category).grid(row=row, column=0, padx=5, pady=2, sticky=tk.W)
            
            # Progress bar
            pb = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=150, mode="determinate")
            pb.grid(row=row, column=1, padx=5, pady=2, sticky=tk.W)
            
            # Value label
            lbl = ttk.Label(progress_frame, text="0% ($0/$0)")
            lbl.grid(row=row, column=2, padx=5, pady=2, sticky=tk.W)
            
            self.budget_progress_vars[category] = (pb, lbl)
            row += 1
        
        # Right panel - Budget list
        right_panel = ttk.Frame(container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Budget list
        list_frame = ttk.LabelFrame(right_panel, text="Current Budgets", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for budgets
        columns = ("category", "amount")
        self.budget_tree = ttk.Treeview(
            list_frame, columns=columns, show="headings", selectmode="browse")
        
        # Configure columns
        self.budget_tree.heading("category", text="Category")
        self.budget_tree.heading("amount", text="Amount")
        
        self.budget_tree.column("category", width=150, anchor=tk.W)
        self.budget_tree.column("amount", width=150, anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.budget_tree.yview)
        self.budget_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.budget_tree.pack(fill=tk.BOTH, expand=True)

    def set_budget(self):
        """Set budget from form data"""
        category = self.budget_category.get()
        amount = self.budget_amount.get()
        
        # Validate inputs
        if not self.validate_non_empty(self.budget_amount):
            messagebox.showerror("Error", "Amount is required")
            return
            
        if not self.validate_number(amount):
            messagebox.showerror("Error", "Amount must be a positive number")
            return
            
        # Convert amount to float
        try:
            amount = float(amount)
            success, message = self.manager.set_budget(category, amount)
            
            if success:
                messagebox.showinfo("Success", message)
                self.update_budgets_view()
                self.update_dashboard()
                self.update_budget_progress()
                # Clear form
                self.budget_amount.delete(0, tk.END)
            else:
                messagebox.showerror("Error", message)
        except ValueError:
            messagebox.showerror("Error", "Invalid amount. Please enter a number.")

    def update_budgets_view(self):
        """Refresh budgets list"""
        # Clear existing data
        for row in self.budget_tree.get_children():
            self.budget_tree.delete(row)
        
        # Get budgets from database
        budgets = self.db.get_budgets()
        
        # Add to treeview
        for budget in budgets:
            self.budget_tree.insert("", tk.END, values=budget)

    def update_budget_progress(self):
        """Update the budget progress bars"""
        # Get current month/year
        month = datetime.now().month
        year = datetime.now().year
        
        # Get budget status
        summary = self.manager.get_monthly_summary(month, year)
        budget_status = summary.get("budget_status", {})
        
        # Update each progress bar
        for category, (pb, lbl) in self.budget_progress_vars.items():
            if category in budget_status:
                status = budget_status[category]
                percentage = min(status["percentage"], 100)  # Cap at 100%
                pb["value"] = percentage
                
                # Set color based on status
                if percentage <= 75:
                    pb["style"] = "green.Horizontal.TProgressbar"
                elif percentage <= 90:
                    pb["style"] = "orange.Horizontal.TProgressbar"
                else:
                    pb["style"] = "red.Horizontal.TProgressbar"
                
                lbl.config(text=f"{percentage:.1f}% (${status['actual']:,.2f}/${status['budget']:,.2f})")
            else:
                pb["value"] = 0
                lbl.config(text="No budget set")

    # ================== SAVINGS TAB ================== #
    def create_savings_tab(self):
        """Create savings goals management tab"""
        # Main container
        container = ttk.Frame(self.savings_tab)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Form and contributions
        left_panel = ttk.Frame(container)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Form frame
        form_frame = ttk.LabelFrame(left_panel, text="Add Savings Goal", padding=10)
        form_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Goal
        ttk.Label(form_frame, text="Goal:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.savings_goal = ttk.Entry(form_frame, width=30)
        self.savings_goal.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W, columnspan=2)
        
        # Target amount
        ttk.Label(form_frame, text="Target Amount:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.savings_target = ttk.Entry(form_frame, width=15)
        self.savings_target.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Target date
        ttk.Label(form_frame, text="Target Date (YYYY-MM-DD):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.savings_date = ttk.Entry(form_frame, width=15)
        self.savings_date.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Add button
        ttk.Button(form_frame, text="Add Goal", 
                command=self.add_savings_goal).grid(row=3, column=1, padx=5, pady=10, sticky=tk.W)
        
        # Contributions frame
        contrib_frame = ttk.LabelFrame(left_panel, text="Add Contribution", padding=10)
        contrib_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(contrib_frame, text="Goal:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.contribution_goal = ttk.Combobox(contrib_frame, state="readonly")
        self.contribution_goal.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(contrib_frame, text="Amount:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.contribution_amount = ttk.Entry(contrib_frame, width=15)
        self.contribution_amount.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Button(contrib_frame, text="Add Contribution", 
                command=self.add_contribution).grid(row=2, column=1, padx=5, pady=10, sticky=tk.W)
        
        # Right panel - Savings list
        right_panel = ttk.Frame(container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Savings list
        list_frame = ttk.LabelFrame(right_panel, text="Savings Goals", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for savings
        columns = ("id", "goal", "current", "target", "date", "progress")
        self.savings_tree = ttk.Treeview(
            list_frame, columns=columns, show="headings", selectmode="browse")
        
        # Configure columns
        self.savings_tree.heading("id", text="ID")
        self.savings_tree.heading("goal", text="Goal")
        self.savings_tree.heading("current", text="Current")
        self.savings_tree.heading("target", text="Target")
        self.savings_tree.heading("date", text="Target Date")
        self.savings_tree.heading("progress", text="Progress")
        
        self.savings_tree.column("id", width=50, anchor=tk.CENTER)
        self.savings_tree.column("goal", width=150, anchor=tk.W)
        self.savings_tree.column("current", width=100, anchor=tk.CENTER)
        self.savings_tree.column("target", width=100, anchor=tk.CENTER)
        self.savings_tree.column("date", width=100, anchor=tk.CENTER)
        self.savings_tree.column("progress", width=150, anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.savings_tree.yview)
        self.savings_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.savings_tree.pack(fill=tk.BOTH, expand=True)
        
        # Button frame
        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Delete Goal", 
                command=self.delete_savings_goal).pack(side=tk.RIGHT, padx=5)

    def add_savings_goal(self):
        """Add a new savings goal"""
        goal = self.savings_goal.get()
        target = self.savings_target.get()
        date = self.savings_date.get()
        
        # Validate inputs
        if not self.validate_non_empty(self.savings_goal, self.savings_target, self.savings_date):
            messagebox.showerror("Error", "All fields are required")
            return
            
        if not self.validate_savings_goal(goal):
            messagebox.showerror("Error", "Goal name cannot be empty")
            return
            
        if not self.validate_number(target):
            messagebox.showerror("Error", "Target amount must be a positive number")
            return
            
        if not self.validate_date(date):
            messagebox.showerror("Error", "Date must be in YYYY-MM-DD format")
            return
            
        # Convert target to float
        try:
            target = float(target)
            success, message = self.manager.add_savings_goal(goal, target, date)
            
            if success:
                messagebox.showinfo("Success", message)
                self.update_savings_view()
                # Clear form
                self.savings_goal.delete(0, tk.END)
                self.savings_target.delete(0, tk.END)
                self.savings_date.delete(0, tk.END)
            else:
                messagebox.showerror("Error", message)
        except ValueError:
            messagebox.showerror("Error", "Invalid target amount. Please enter a number.")

    def add_contribution(self):
        """Add contribution to selected savings goal"""
        goal_id_str = self.contribution_goal.get()
        amount = self.contribution_amount.get()
        
        # Validate inputs
        if not goal_id_str:
            messagebox.showwarning("Warning", "Please select a savings goal")
            return
            
        if not self.validate_non_empty(self.contribution_amount):
            messagebox.showerror("Error", "Amount is required")
            return
            
        if not self.validate_number(amount):
            messagebox.showerror("Error", "Amount must be a positive number")
            return
            
        # Extract goal ID
        try:
            goal_id = goal_id_str.split(":")[0]
        except IndexError:
            messagebox.showerror("Error", "Invalid savings goal selection")
            return
            
        # Convert amount to float
        try:
            amount = float(amount)
            success, message = self.manager.update_savings(goal_id, amount)
            
            if success:
                messagebox.showinfo("Success", message)
                self.update_savings_view()
                self.contribution_amount.delete(0, tk.END)
            else:
                messagebox.showerror("Error", message)
        except ValueError:
            messagebox.showerror("Error", "Invalid amount. Please enter a number.")

    def delete_savings_goal(self):
        """Delete selected savings goal"""
        selected = self.savings_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a savings goal to delete")
            return
            
        item = self.savings_tree.item(selected[0])
        goal_id = item['values'][0]
        
        if messagebox.askyesno("Confirm", "Delete this savings goal?"):
            success, message = self.manager.delete_savings_goal(goal_id)
            if success:
                messagebox.showinfo("Success", message)
                self.update_savings_view()
            else:
                messagebox.showerror("Error", message)

    def update_savings_view(self):
        """Refresh savings goals list"""
        # Clear existing data
        for row in self.savings_tree.get_children():
            self.savings_tree.delete(row)
        
        # Clear and repopulate contributions combobox
        self.contribution_goal['values'] = []
        
        # Get savings goals from database
        goals = self.db.get_savings_goals()
        
        # Add to treeview and combobox
        for goal in goals:
            goal_id, name, target, current, date = goal
            progress = (current / target) * 100 if target > 0 else 0
            progress_text = f"{progress:.1f}% (${current:.2f}/${target:.2f})"
            
            self.savings_tree.insert("", tk.END, values=(
                goal_id, name, f"${current:.2f}", f"${target:.2f}", date, progress_text
            ))
            
            # Add to contributions combobox
            self.contribution_goal['values'] = list(self.contribution_goal['values']) + [
                f"{goal_id}: {name}"
            ]

    # ================== REPORTS TAB ================== #
    def create_reports_tab(self):
        """Create reports tab with financial summaries"""
        # Report type selection
        report_frame = ttk.Frame(self.reports_tab)
        report_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(report_frame, text="Report Type:").pack(side=tk.LEFT, padx=5)
        
        self.report_type = tk.StringVar(value="Monthly Summary")
        report_types = ["Monthly Summary", "Category Breakdown", "Budget vs Actual", "Yearly Overview"]
        ttk.Combobox(report_frame, textvariable=self.report_type, 
                    values=report_types, state="readonly").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(report_frame, text="Generate Report", 
                command=self.generate_report).pack(side=tk.LEFT, padx=10)
        
        # Date selection for reports
        date_frame = ttk.Frame(report_frame)
        date_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(date_frame, text="Month:").grid(row=0, column=0, padx=5)
        self.report_month = ttk.Combobox(date_frame, width=10,
            values=[calendar.month_name[i] for i in range(1, 13)],
            state="readonly")
        self.report_month.current(datetime.now().month - 1)
        self.report_month.grid(row=0, column=1, padx=5)
        
        ttk.Label(date_frame, text="Year:").grid(row=0, column=2, padx=5)
        self.report_year = ttk.Combobox(date_frame, width=8,
            values=[str(year) for year in range(2020, 2031)],
            state="readonly")
        self.report_year.set(str(datetime.now().year))
        self.report_year.grid(row=0, column=3, padx=5)
        
        # Report display area
        report_container = ttk.Frame(self.reports_tab)
        report_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Text report
        self.report_text = scrolledtext.ScrolledText(
            report_container, wrap=tk.WORD, font=("Arial", 10))
        self.report_text.pack(fill=tk.BOTH, expand=True)
        self.report_text.config(state=tk.DISABLED)
        
        # Report charts
        self.report_figure = Figure(figsize=(8, 4), dpi=100, facecolor=self.colors["card"])
        self.report_canvas = FigureCanvasTkAgg(self.report_figure, report_container)
        self.report_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def generate_report(self):
        """Generate the selected report"""
        report_type = self.report_type.get()
        month_num = datetime.strptime(self.report_month.get(), "%B").month if self.report_month.get() else None
        year = int(self.report_year.get())
        
        # Clear previous content
        self.report_text.config(state=tk.NORMAL)
        self.report_text.delete(1.0, tk.END)
        self.report_figure.clear()
        
        try:
            if report_type == "Monthly Summary":
                self.generate_monthly_summary(month_num, year)
            elif report_type == "Category Breakdown":
                self.generate_category_breakdown(month_num, year)
            elif report_type == "Budget vs Actual":
                self.generate_budget_vs_actual(month_num, year)
            elif report_type == "Yearly Overview":
                self.generate_yearly_overview(year)
                
            self.report_canvas.draw()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")

    def generate_monthly_summary(self, month, year):
        """Generate monthly summary report"""
        summary = self.manager.get_monthly_summary(month, year)
        
        # Prepare report content
        report = f"Monthly Financial Summary\n"
        report += f"Period: {calendar.month_name[month]} {year}\n\n"
        report += f"Income: ${summary['income']:,.2f}\n"
        report += f"Expenses: ${summary['expenses']:,.2f}\n"
        report += f"Net Balance: ${summary['net']:,.2f}\n\n"
        
        # Top expenses
        report += "Top Expense Categories:\n"
        expenses = {}
        transactions = self.db.get_transactions(month, year)
        for t in transactions:
            if t[1] == "Expense":
                category = t[2]
                expenses[category] = expenses.get(category, 0) + t[3]
        
        # Sort by amount descending
        sorted_expenses = sorted(expenses.items(), key=lambda x: x[1], reverse=True)[:5]
        for category, amount in sorted_expenses:
            report += f"  {category}: ${amount:,.2f}\n"
        
        # Display report
        self.report_text.insert(tk.END, report)
        self.report_text.config(state=tk.DISABLED)
        
        # Create chart
        ax = self.report_figure.add_subplot(111)
        
        # Pie chart of expense distribution
        if expenses:
            labels = list(expenses.keys())
            values = list(expenses.values())
            
            # Sort by amount (descending)
            sorted_data = sorted(zip(values, labels), reverse=True)
            values, labels = zip(*sorted_data)
            
            # Only show top 5, group others
            if len(values) > 5:
                other = sum(values[5:])
                values = values[:5] + (other,)
                labels = labels[:5] + ("Other",)
            
            colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c']
            wedges, texts, autotexts = ax.pie(
                values, labels=labels, autopct='%1.1f%%', 
                colors=colors[:len(values)], startangle=90)
            
            ax.set_title('Expense Distribution')
        else:
            ax.text(0.5, 0.5, 'No expense data', 
                horizontalalignment='center', verticalalignment='center')

    def generate_category_breakdown(self, month, year):
        """Generate category breakdown report"""
        transactions = self.db.get_transactions(month, year)
        
        # Prepare report content
        report = f"Category Breakdown\n"
        report += f"Period: {calendar.month_name[month]} {year}\n\n"
        
        # Expense by category
        expenses_by_category = {}
        for t in transactions:
            if t[1] == "Expense":
                category = t[2]
                expenses_by_category[category] = expenses_by_category.get(category, 0) + t[3]
        
        report += "Expenses by Category:\n"
        for category, amount in sorted(expenses_by_category.items(), key=lambda x: x[1], reverse=True):
            report += f"  {category}: ${amount:,.2f}\n"
            
        # Income by category
        income_by_category = {}
        for t in transactions:
            if t[1] == "Income":
                category = t[2]
                income_by_category[category] = income_by_category.get(category, 0) + t[3]
        
        report += "\nIncome by Category:\n"
        for category, amount in sorted(income_by_category.items(), key=lambda x: x[1], reverse=True):
            report += f"  {category}: ${amount:,.2f}\n"
            
        # Display report
        self.report_text.insert(tk.END, report)
        self.report_text.config(state=tk.DISABLED)
        
        # Create chart
        ax = self.report_figure.add_subplot(111)
        
        if expenses_by_category:
            # Bar chart of expenses by category
            categories = list(expenses_by_category.keys())
            amounts = list(expenses_by_category.values())
            
            # Sort by amount descending
            sorted_data = sorted(zip(amounts, categories), reverse=True)
            amounts, categories = zip(*sorted_data)
            
            ax.bar(categories, amounts, color=self.colors["primary"])
            ax.set_title('Expense by Category')
            ax.set_ylabel('Amount ($)')
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        else:
            ax.text(0.5, 0.5, 'No expense data', 
                horizontalalignment='center', verticalalignment='center')

    def generate_budget_vs_actual(self, month, year):
        """Generate budget vs actual report"""
        summary = self.manager.get_monthly_summary(month, year)
        budget_status = summary.get("budget_status", {})
        
        # Prepare report content
        report = f"Budget vs Actual\n"
        report += f"Period: {calendar.month_name[month]} {year}\n\n"
        
        report += "Budget Status:\n"
        for category, data in budget_status.items():
            report += f"  {category}:\n"
            report += f"    Budget: ${data['budget']:,.2f}\n"
            report += f"    Actual: ${data['actual']:,.2f}\n"
            report += f"    Remaining: ${data['remaining']:,.2f} ({data['status']})\n\n"
        
        # Display report
        self.report_text.insert(tk.END, report)
        self.report_text.config(state=tk.DISABLED)
        
        # Create chart
        ax = self.report_figure.add_subplot(111)
        
        if budget_status:
            categories = []
            budgets = []
            actuals = []
            
            for category, data in budget_status.items():
                categories.append(category)
                budgets.append(data['budget'])
                actuals.append(data['actual'])
            
            x = range(len(categories))
            width = 0.35
            
            ax.bar(x, budgets, width, label='Budget', color=self.colors["primary"])
            ax.bar([i + width for i in x], actuals, width, label='Actual', color=self.colors["secondary"])
            
            ax.set_ylabel('Amount ($)')
            ax.set_title('Budget vs Actual')
            ax.set_xticks([i + width/2 for i in x])
            ax.set_xticklabels(categories, rotation=45, ha='right')
            ax.legend()
        else:
            ax.text(0.5, 0.5, 'No budget data', 
                horizontalalignment='center', verticalalignment='center')

    def generate_yearly_overview(self, year):
        """Generate yearly overview report"""
        summary = self.manager.get_yearly_summary(year)
        
        # Prepare report content
        report = f"Yearly Financial Overview\n"
        report += f"Year: {year}\n\n"
        
        report += "Monthly Summary:\n"
        for i, month in enumerate(summary["months"]):
            report += f"  {month}: "
            report += f"Income ${summary['income'][i]:,.2f}, "
            report += f"Expenses ${summary['expenses'][i]:,.2f}, "
            report += f"Net ${summary['net'][i]:,.2f}\n"
        
        report += f"\nTotal Income: ${sum(summary['income']):,.2f}\n"
        report += f"Total Expenses: ${sum(summary['expenses']):,.2f}\n"
        report += f"Net Balance: ${sum(summary['net']):,.2f}\n"
        
        # Display report
        self.report_text.insert(tk.END, report)
        self.report_text.config(state=tk.DISABLED)
        
        # Create chart
        ax = self.report_figure.add_subplot(111)
        
        if summary["months"]:
            months = summary["months"]
            income = summary["income"]
            expenses = summary["expenses"]
            
            ax.plot(months, income, label='Income', color=self.colors["positive"], marker='o')
            ax.plot(months, expenses, label='Expenses', color=self.colors["negative"], marker='o')
            
            ax.set_xlabel('Month')
            ax.set_ylabel('Amount ($)')
            ax.set_title('Monthly Income vs Expenses')
            ax.legend()
            ax.grid(True, linestyle='--', alpha=0.7)
        else:
            ax.text(0.5, 0.5, 'No yearly data available', 
                horizontalalignment='center', verticalalignment='center')

    def on_close(self):
        """Handle application close event"""
        self.db.close()
        self.destroy()
        
        
if __name__ == "__main__":
    # Configure matplotlib to use the TkAgg backend
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    
        # Start the application
    app = FinanceApp()
    app.mainloop()