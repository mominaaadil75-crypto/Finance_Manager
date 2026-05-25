import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
from datetime import datetime
import unittest
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import calendar
import re

class DatabaseHandler:
    """Handles all database operations using SQLite"""
    def __init__(self, db_name='finance.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
        
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
    
    def get_transactions(self, month=None, year=None):
        cursor = self.conn.cursor()
        if month and year:
            cursor.execute('''
            SELECT * FROM transactions 
            WHERE strftime('%m', date) = ? AND strftime('%Y', date) = ?
            ''', (f"{int(month):02d}", str(year)))
        else:
            cursor.execute('SELECT * FROM transactions')
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
    
    def close(self):
        self.conn.close()


class FinanceManager:
    """Handles business logic and calculations"""
    def __init__(self, db_handler):
        self.db = db_handler
        self.categories = [
            # Income categories
            "Salary", "Bonus", "Freelance", "Investment", 
            # Expense categories
            "Food", "Housing", "Transport", "Utilities", 
            "Healthcare", "Entertainment", "Education", 
            "Personal", "Savings", "Other"
        ]
    
    def add_transaction(self, trans_type, category, amount, date, description=""):
        # Validate category
        if category not in self.categories:
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
        # Validate category
        if category not in self.categories:
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
        actual_expenses = {category: 0 for category in self.categories}
        
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
                "status": status
            }
        
        return {
            "income": income,
            "expenses": expenses,
            "net": income - expenses,
            "budget_status": budget_status
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


class FinanceApp(tk.Tk):
    """Main application class with GUI"""
    def __init__(self):
        super().__init__()
        self.title("Personal Finance Manager")
        self.geometry("1200x700")
        self.configure(bg="#2C3E50")
        
        # Initialize database and manager
        self.db = DatabaseHandler()
        self.manager = FinanceManager(self.db)
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.configure_styles()
        
        # Create main frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
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
        self.style.configure("TFrame", background="#ECF0F1")
        self.style.configure("TButton", 
                            font=("Arial", 10, "bold"),
                            padding=6,
                            background="#3498DB",
                            foreground="white")
        self.style.map("TButton", 
                      background=[("active", "#2980B9")])
        self.style.configure("Header.TLabel", 
                           font=("Arial", 14, "bold"),
                           background="#2C3E50",
                           foreground="white")
        self.style.configure("Secondary.TLabel", 
                           font=("Arial", 12),
                           background="#34495E",
                           foreground="white")
        self.style.configure("Positive.TLabel", 
                           font=("Arial", 12, "bold"),
                           background="#ECF0F1",
                           foreground="#27AE60")
        self.style.configure("Negative.TLabel", 
                           font=("Arial", 12, "bold"),
                           background="#ECF0F1",
                           foreground="#E74C3C")
        self.style.configure("TNotebook", background="#2C3E50")
        self.style.configure("TNotebook.Tab", 
                           font=("Arial", 10, "bold"),
                           padding=(10, 5),
                           background="#3498DB",
                           foreground="white")
        self.style.map("TNotebook.Tab", 
                      background=[("selected", "#2980B9")])
    
    def create_dashboard_tab(self):
        """Create the dashboard tab with financial overview"""
        # Header
        header_frame = ttk.Frame(self.dashboard_tab)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Financial Dashboard", style="Header.TLabel"
                 ).pack(side=tk.LEFT, padx=10, pady=10)
        
        # Date selection
        date_frame = ttk.Frame(header_frame)
        date_frame.pack(side=tk.RIGHT, padx=10)
        
        ttk.Label(date_frame, text="Select Month:").grid(row=0, column=0, padx=5)
        
        self.month_var = tk.StringVar()
        self.month_combobox = ttk.Combobox(
            date_frame, textvariable=self.month_var, width=10,
            values=[calendar.month_name[i] for i in range(1, 13)]
        )
        self.month_combobox.current(datetime.now().month - 1)
        self.month_combobox.grid(row=0, column=1, padx=5)
        
        ttk.Label(date_frame, text="Year:").grid(row=0, column=2, padx=5)
        
        self.year_var = tk.StringVar(value=str(datetime.now().year))
        year_combobox = ttk.Combobox(
            date_frame, textvariable=self.year_var, width=8,
            values=[str(year) for year in range(2020, 2031)])
        year_combobox.grid(row=0, column=3, padx=5)
        
        ttk.Button(date_frame, text="Update", 
                  command=self.update_dashboard).grid(row=0, column=4, padx=10)
        
        # Summary cards
        summary_frame = ttk.Frame(self.dashboard_tab)
        summary_frame.pack(fill=tk.X, pady=10)
        
        # Income card
        income_card = ttk.Frame(summary_frame, style="Card.TFrame")
        income_card.pack(side=tk.LEFT, expand=True, padx=10)
        ttk.Label(income_card, text="INCOME", style="Secondary.TLabel"
                 ).pack(fill=tk.X, padx=10, pady=5)
        self.income_label = ttk.Label(income_card, text="$0.00", 
                                     style="Positive.TLabel")
        self.income_label.pack(pady=10)
        
        # Expense card
        expense_card = ttk.Frame(summary_frame, style="Card.TFrame")
        expense_card.pack(side=tk.LEFT, expand=True, padx=10)
        ttk.Label(expense_card, text="EXPENSES", style="Secondary.TLabel"
                 ).pack(fill=tk.X, padx=10, pady=5)
        self.expense_label = ttk.Label(expense_card, text="$0.00", 
                                      style="Negative.TLabel")
        self.expense_label.pack(pady=10)
        
        # Net card
        net_card = ttk.Frame(summary_frame, style="Card.TFrame")
        net_card.pack(side=tk.LEFT, expand=True, padx=10)
        ttk.Label(net_card, text="NET BALANCE", style="Secondary.TLabel"
                 ).pack(fill=tk.X, padx=10, pady=5)
        self.net_label = ttk.Label(net_card, text="$0.00")
        self.net_label.pack(pady=10)
        
        # Charts
        chart_frame = ttk.Frame(self.dashboard_tab)
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Expense breakdown chart
        expense_chart_frame = ttk.LabelFrame(chart_frame, text="Expense Breakdown")
        expense_chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        self.expense_figure = Figure(figsize=(5, 4), dpi=100)
        self.expense_canvas = FigureCanvasTkAgg(self.expense_figure, expense_chart_frame)
        self.expense_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Budget status chart
        budget_chart_frame = ttk.LabelFrame(chart_frame, text="Budget Status")
        budget_chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        self.budget_figure = Figure(figsize=(5, 4), dpi=100)
        self.budget_canvas = FigureCanvasTkAgg(self.budget_figure, budget_chart_frame)
        self.budget_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def update_dashboard(self):
        """Update dashboard with current financial data"""
        try:
            month_num = datetime.strptime(self.month_var.get(), "%B").month
            year = int(self.year_var.get())
            
            summary = self.manager.get_monthly_summary(month_num, year)
            
            # Update summary cards
            self.income_label.config(text=f"${summary['income']:,.2f}")
            self.expense_label.config(text=f"${summary['expenses']:,.2f}")
            
            net_text = f"${summary['net']:,.2f}"
            if summary['net'] >= 0:
                self.net_label.config(text=net_text, style="Positive.TLabel")
            else:
                self.net_label.config(text=net_text, style="Negative.TLabel")
            
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
                ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
                ax.set_title('Expense Distribution')
                ax.axis('equal')  # Equal aspect ratio ensures pie is circular
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
                        percentage = (data['actual'] / data['budget']) * 100
                        percentages.append(percentage)
                        status_colors.append('#27AE60' if percentage <= 100 else '#E74C3C')
                
                if categories:
                    bars = ax.barh(categories, percentages, color=status_colors)
                    ax.set_xlabel('Percentage Used (%)')
                    ax.set_title('Budget Utilization')
                    ax.set_xlim(0, max(percentages) * 1.2)
                    
                    # Add value labels
                    for bar in bars:
                        width = bar.get_width()
                        ax.text(width + 1, bar.get_y() + bar.get_height()/2, 
                                f'{width:.1f}%', ha='left', va='center')
            else:
                ax.text(0.5, 0.5, 'No budget data', 
                       horizontalalignment='center', verticalalignment='center')
            
            self.budget_canvas.draw()
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
        # Form frame
        form_frame = ttk.LabelFrame(self.transaction_tab, text="Add New Transaction")
        form_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Type selection
        ttk.Label(form_frame, text="Type:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.trans_type = tk.StringVar(value="Expense")
        ttk.Radiobutton(form_frame, text="Income", variable=self.trans_type, value="Income"
                       ).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Radiobutton(form_frame, text="Expense", variable=self.trans_type, value="Expense"
                       ).grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        
        # Category
        ttk.Label(form_frame, text="Category:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.trans_category = ttk.Combobox(form_frame, values=self.manager.categories)
        self.trans_category.current(0)
        self.trans_category.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
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
        
        # Transactions list
        list_frame = ttk.LabelFrame(self.transaction_tab, text="Recent Transactions")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
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
        # Budget form
        form_frame = ttk.LabelFrame(self.budget_tab, text="Set Budget")
        form_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Category
        ttk.Label(form_frame, text="Category:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.budget_category = ttk.Combobox(form_frame, values=self.manager.categories)
        self.budget_category.current(0)
        self.budget_category.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Amount
        ttk.Label(form_frame, text="Amount:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.budget_amount = ttk.Entry(form_frame, width=15)
        self.budget_amount.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Set button
        ttk.Button(form_frame, text="Set Budget", 
                  command=self.set_budget).grid(row=2, column=1, padx=5, pady=10, sticky=tk.W)
        
        # Budget list
        list_frame = ttk.LabelFrame(self.budget_tab, text="Current Budgets")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
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
    
    # ================== SAVINGS TAB ================== #
    def create_savings_tab(self):
        """Create savings goals management tab"""
        # Form frame
        form_frame = ttk.LabelFrame(self.savings_tab, text="Add Savings Goal")
        form_frame.pack(fill=tk.X, padx=10, pady=10)
        
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
        contrib_frame = ttk.LabelFrame(self.savings_tab, text="Add Contribution")
        contrib_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(contrib_frame, text="Goal:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.contribution_goal = ttk.Combobox(contrib_frame, state="readonly")
        self.contribution_goal.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(contrib_frame, text="Amount:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.contribution_amount = ttk.Entry(contrib_frame, width=15)
        self.contribution_amount.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Button(contrib_frame, text="Add Contribution", 
                  command=self.add_contribution).grid(row=2, column=1, padx=5, pady=10, sticky=tk.W)
        
        # Savings list
        list_frame = ttk.LabelFrame(self.savings_tab, text="Savings Goals")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
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
            progress_text = f"{progress:.1f}% ({current:.2f}/{target:.2f})"
            
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
        report_types = ["Monthly Summary", "Category Breakdown", "Budget vs Actual"]
        ttk.Combobox(report_frame, textvariable=self.report_type, 
                    values=report_types, state="readonly").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(report_frame, text="Generate Report", 
                  command=self.generate_report).pack(side=tk.LEFT, padx=10)
        
        # Report display area
        self.report_text = scrolledtext.ScrolledText(
            self.reports_tab, wrap=tk.WORD, font=("Arial", 10))
        self.report_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.report_text.config(state=tk.DISABLED)
    
    def generate_report(self):
        """Generate the selected report"""
        report_type = self.report_type.get()
        month_num = datetime.now().month
        year = datetime.now().year
        
        # Get data
        transactions = self.db.get_transactions(month_num, year)
        budgets = {b[0]: b[1] for b in self.db.get_budgets()}
        
        # Prepare report content
        report = f"Report: {report_type}\n"
        report += f"Period: {calendar.month_name[month_num]} {year}\n\n"
        
        if report_type == "Monthly Summary":
            income = sum(t[3] for t in transactions if t[1] == "Income")
            expenses = sum(t[3] for t in transactions if t[1] == "Expense")
            net = income - expenses
            
            report += f"Income: ${income:,.2f}\n"
            report += f"Expenses: ${expenses:,.2f}\n"
            report += f"Net Balance: ${net:,.2f}\n"
            
        elif report_type == "Category Breakdown":
            # Expense by category
            expenses_by_category = {}
            for t in transactions:
                if t[1] == "Expense":
                    category = t[2]
                    expenses_by_category[category] = expenses_by_category.get(category, 0) + t[3]
            
            report += "Expenses by Category:\n"
            for category, amount in expenses_by_category.items():
                report += f"  {category}: ${amount:,.2f}\n"
                
            # Income by category
            income_by_category = {}
            for t in transactions:
                if t[1] == "Income":
                    category = t[2]
                    income_by_category[category] = income_by_category.get(category, 0) + t[3]
            
            report += "\nIncome by Category:\n"
            for category, amount in income_by_category.items():
                report += f"  {category}: ${amount:,.2f}\n"
                
        elif report_type == "Budget vs Actual":
            actual_expenses = {category: 0 for category in self.manager.categories}
            for t in transactions:
                if t[1] == "Expense" and t[2] in actual_expenses:
                    actual_expenses[t[2]] += t[3]
            
            report += "Budget vs Actual Expenses:\n"
            for category, budget in budgets.items():
                actual = actual_expenses.get(category, 0)
                variance = budget - actual
                status = "Under" if variance >= 0 else "Over"
                report += f"  {category}:\n"
                report += f"    Budget: ${budget:,.2f}\n"
                report += f"    Actual: ${actual:,.2f}\n"
                report += f"    Variance: ${abs(variance):,.2f} {status} Budget\n\n"
        
        # Display report
        self.report_text.config(state=tk.NORMAL)
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, report)
        self.report_text.config(state=tk.DISABLED)
    
    def on_close(self):
        """Handle application close event"""
        self.db.close()
        self.destroy()

class TestFinanceSystem(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseHandler(':memory:')
        self.manager = FinanceManager(self.db)
        
    def test_add_transaction(self):
        # Valid transaction
        result, msg = self.manager.add_transaction(
            "Income", "Salary", 5000, "2023-10-15", "Monthly salary"
        )
        self.assertTrue(result)
        
        # Invalid category
        result, msg = self.manager.add_transaction(
            "Expense", "InvalidCategory", 100, "2023-10-15"
        )
        self.assertFalse(result)
        
        # Invalid amount
        result, msg = self.manager.add_transaction(
            "Expense", "Food", -50, "2023-10-15"
        )
        self.assertFalse(result)
        
        # Invalid date format
        result, msg = self.manager.add_transaction(
            "Income", "Bonus", 200, "2023/10/15"
        )
        self.assertFalse(result)
    
    def test_set_budget(self):
        # Valid budget
        result, msg = self.manager.set_budget("Food", 500)
        self.assertTrue(result)
        
        # Invalid category
        result, msg = self.manager.set_budget("InvalidCategory", 300)
        self.assertFalse(result)
        
        # Invalid amount
        result, msg = self.manager.set_budget("Transport", -100)
        self.assertFalse(result)
    
    def test_monthly_summary(self):
        # Add some transactions
        self.manager.add_transaction("Income", "Salary", 5000, "2023-10-01")
        self.manager.add_transaction("Expense", "Food", 200, "2023-10-05")
        self.manager.add_transaction("Expense", "Transport", 150, "2023-10-10")
        
        # Set a budget
        self.manager.set_budget("Food", 300)
        
        # Get summary
        summary = self.manager.get_monthly_summary(10, 2023)
        
        # Verify summary
        self.assertEqual(summary["income"], 5000)
        self.assertEqual(summary["expenses"], 350)
        self.assertEqual(summary["net"], 4650)
        
        # Verify budget status
        food_status = summary["budget_status"]["Food"]
        self.assertEqual(food_status["budget"], 300)
        self.assertEqual(food_status["actual"], 200)
        self.assertEqual(food_status["remaining"], 100)
        self.assertEqual(food_status["status"], "Within Budget")
    
    def test_savings_operations(self):
        # Add savings goal
        result, msg = self.manager.add_savings_goal(
            "Vacation", 5000, "2024-06-01"
        )
        self.assertTrue(result)
        
        # Update savings
        goals = self.db.get_savings_goals()
        goal_id = goals[0][0]
        
        result, msg = self.manager.update_savings(goal_id, 1000)
        self.assertTrue(result)
        
        # Verify update
        goals = self.db.get_savings_goals()
        self.assertEqual(goals[0][3], 1000)
        
        # Delete savings goal
        result, msg = self.manager.delete_savings_goal(goal_id)
        self.assertTrue(result)
        
        # Verify deletion
        goals = self.db.get_savings_goals()
        self.assertEqual(len(goals), 0)


if __name__ == "__main__":
    # Run unit tests
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestFinanceSystem)
    unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    # Start the application
    app = FinanceApp()
    app.mainloop()