import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
import os
import sys
import csv
import calendar
from collections import defaultdict
import requests
import json

# 添加matplotlib导入错误处理
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    messagebox.showwarning("警告", "未安装matplotlib库，图表功能将不可用。\n请使用pip安装：pip install matplotlib numpy")

# 添加AI API配置
AI_API_KEY = "towa-pW6u5OtZpxRQ7AHYNg1ANgIrkeqKa07D407K2dGJheapbS51nx99uM3A"
AI_API_URL = "https://towa.fofinvesting.com/api/v1/chat/completions"

class FamilyFinanceManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("家庭收支管理系统")
        
        # 设置最小窗口大小
        self.root.minsize(800, 600)
        
        # 设置初始窗口大小
        window_width = 1000
        window_height = 700
        
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 计算窗口居中位置
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # 设置窗口位置和大小
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 配置根窗口的网格权重，使其可以随窗口大小调整
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # 设置主题样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置温暖的主题颜色
        style.configure('TFrame', background='#FFF5E6')
        style.configure('TLabel', font=('微软雅黑', 10), background='#FFF5E6')
        style.configure('TButton', font=('微软雅黑', 10), background='#FFE4B5')
        style.configure('TEntry', font=('微软雅黑', 10), fieldbackground='#FFFFFF')
        style.configure('Treeview', font=('微软雅黑', 10), background='#FFFFFF', fieldbackground='#FFFFFF')
        style.configure('Treeview.Heading', font=('微软雅黑', 10, 'bold'), background='#FFE4B5')
        style.configure('TLabelframe', background='#FFF5E6')
        style.configure('TLabelframe.Label', background='#FFF5E6', font=('微软雅黑', 10))
        style.configure('TCombobox', fieldbackground='#FFFFFF', background='#FFFFFF')
        
        # 设置表格样式
        style.map('Treeview',
            background=[('selected', '#FFE4B5')],
            foreground=[('selected', '#000000')]
        )
        
        # 设置按钮样式
        style.map('TButton',
            background=[('active', '#FFD700')],
            foreground=[('active', '#000000')]
        )
        
        # 设置输入框样式
        style.map('TEntry',
            fieldbackground=[('readonly', '#F5F5F5')],
            selectbackground=[('readonly', '#FFE4B5')]
        )
        
        # 设置下拉框样式
        style.map('TCombobox',
            fieldbackground=[('readonly', '#FFFFFF')],
            selectbackground=[('readonly', '#FFE4B5')]
        )
        
        # 创建菜单栏
        self.create_menu()
        
        # 初始化数据库
        self.init_database()
        
        # 创建界面
        self.create_widgets()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 绑定窗口大小改变事件
        self.root.bind('<Configure>', self.on_window_configure)
        
    def on_window_configure(self, event):
        # 确保窗口始终居中
        if event.widget == self.root:
            # 获取窗口当前大小
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            
            # 获取屏幕尺寸
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # 计算居中位置
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            
            # 更新窗口位置，但不触发Configure事件
            self.root.after(100, lambda: self.root.geometry(f"+{x}+{y}"))
        
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出数据", command=self.export_data)
        file_menu.add_command(label="清空数据", command=self.clear_all_data)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing)
        
        # 统计菜单
        stats_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="统计", menu=stats_menu)
        stats_menu.add_command(label="本月统计", command=self.show_monthly_stats)
        stats_menu.add_command(label="类别统计", command=self.show_category_stats)
        stats_menu.add_command(label="年度统计", command=self.show_yearly_stats)
        if MATPLOTLIB_AVAILABLE:
            stats_menu.add_command(label="统计图表", command=self.show_statistics_charts)
        
        # AI助手菜单
        ai_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="AI助手", menu=ai_menu)
        ai_menu.add_command(label="收支分析", command=self.show_ai_analysis)
        ai_menu.add_command(label="理财建议", command=self.show_ai_advice)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
        
        # 绑定菜单栏事件
        menubar.bind('<Configure>', lambda e: self.root.after(100, self.update_menu_position))
        
    def update_menu_position(self):
        # 更新菜单栏位置，但不触发Configure事件
        if hasattr(self, 'root') and self.root.winfo_exists():
            self.root.update_idletasks()
            self.root.after(100, self.root.update)
        
    def init_database(self):
        try:
            # 连接到SQLite数据库（如果不存在则创建）
            self.conn = sqlite3.connect('family_finance.db', check_same_thread=False)
            self.cursor = self.conn.cursor()
            
            # 创建收支记录表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    description TEXT
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("数据库错误", f"初始化数据库失败：{str(e)}")
            self.root.destroy()
            raise
        
    def create_widgets(self):
        try:
            # 创建主框架
            main_frame = ttk.Frame(self.root, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # 配置网格权重
            main_frame.columnconfigure(0, weight=1)
            main_frame.rowconfigure(2, weight=1)  # 让记录显示区域可以随窗口调整大小
            
            # 创建输入区域
            input_frame = ttk.LabelFrame(main_frame, text="添加收支记录", padding="10")
            input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
            
            # 第一行输入
            row1_frame = ttk.Frame(input_frame)
            row1_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
            
            # 类型选择
            ttk.Label(row1_frame, text="类型:").grid(row=0, column=0, padx=5)
            self.type_var = tk.StringVar()
            type_combo = ttk.Combobox(row1_frame, textvariable=self.type_var, width=15, state='readonly')
            type_combo['values'] = ('收入', '支出')
            type_combo.grid(row=0, column=1, padx=5)
            type_combo.set('支出')
            
            # 类别输入
            ttk.Label(row1_frame, text="类别:").grid(row=0, column=2, padx=5)
            self.category_var = tk.StringVar()
            category_entry = ttk.Entry(row1_frame, textvariable=self.category_var, width=20)
            category_entry.grid(row=0, column=3, padx=5)
            
            # 金额输入
            ttk.Label(row1_frame, text="金额:").grid(row=0, column=4, padx=5)
            self.amount_var = tk.StringVar()
            amount_entry = ttk.Entry(row1_frame, textvariable=self.amount_var, width=15)
            amount_entry.grid(row=0, column=5, padx=5)
            
            # 第二行输入
            row2_frame = ttk.Frame(input_frame)
            row2_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
            
            # 描述输入
            ttk.Label(row2_frame, text="描述:").grid(row=0, column=0, padx=5)
            self.description_var = tk.StringVar()
            description_entry = ttk.Entry(row2_frame, textvariable=self.description_var, width=50)
            description_entry.grid(row=0, column=1, columnspan=4, padx=5)
            
            # 按钮区域
            button_frame = ttk.Frame(input_frame)
            button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
            
            # 添加按钮
            add_button = ttk.Button(button_frame, text="添加记录", command=self.add_transaction)
            add_button.grid(row=0, column=0, padx=5)
            
            # 编辑按钮
            edit_button = ttk.Button(button_frame, text="编辑记录", command=self.edit_transaction)
            edit_button.grid(row=0, column=1, padx=5)
            
            # 删除按钮
            delete_button = ttk.Button(button_frame, text="删除记录", command=self.delete_transaction)
            delete_button.grid(row=0, column=2, padx=5)
            
            # 创建统计信息区域
            stats_frame = ttk.LabelFrame(main_frame, text="统计信息", padding="5")
            stats_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
            
            # 统计标签
            self.total_income_label = ttk.Label(stats_frame, text="总收入: ¥0.00")
            self.total_income_label.grid(row=0, column=0, padx=10)
            
            self.total_expense_label = ttk.Label(stats_frame, text="总支出: ¥0.00")
            self.total_expense_label.grid(row=0, column=1, padx=10)
            
            self.balance_label = ttk.Label(stats_frame, text="结余: ¥0.00")
            self.balance_label.grid(row=0, column=2, padx=10)
            
            # 创建记录显示区域
            tree_frame = ttk.LabelFrame(main_frame, text="收支记录", padding="5")
            tree_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
            
            # 配置tree_frame的网格权重
            tree_frame.columnconfigure(0, weight=1)
            tree_frame.rowconfigure(0, weight=1)
            
            # 创建表格
            self.tree = ttk.Treeview(tree_frame, columns=('ID', '日期', '类型', '类别', '金额', '描述'), show='headings')
            self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # 设置列标题和宽度
            self.tree.heading('ID', text='ID')
            self.tree.heading('日期', text='日期')
            self.tree.heading('类型', text='类型')
            self.tree.heading('类别', text='类别')
            self.tree.heading('金额', text='金额')
            self.tree.heading('描述', text='描述')
            
            self.tree.column('ID', width=50)
            self.tree.column('日期', width=150)
            self.tree.column('类型', width=80)
            self.tree.column('类别', width=100)
            self.tree.column('金额', width=100)
            self.tree.column('描述', width=300)
            
            # 添加滚动条
            scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
            scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
            self.tree.configure(yscrollcommand=scrollbar.set)
            
            # 绑定选择事件
            self.tree.bind('<<TreeviewSelect>>', self.on_select)
            
            # 更新显示
            self.update_transaction_list()
            self.update_statistics()
            
        except Exception as e:
            messagebox.showerror("错误", f"创建界面失败：{str(e)}")
            self.root.destroy()
            raise
        
    def on_select(self, event):
        try:
            # 获取选中的记录
            selected_items = self.tree.selection()
            if selected_items:
                item = self.tree.item(selected_items[0])
                values = item['values']
                
                # 填充输入框
                self.type_var.set(values[2])
                self.category_var.set(values[3])
                self.amount_var.set(values[4])
                self.description_var.set(values[5])
        except Exception as e:
            messagebox.showerror("错误", f"选择记录失败：{str(e)}")
            
    def add_transaction(self):
        try:
            if not self.category_var.get().strip():
                messagebox.showerror("错误", "请输入类别")
                return
                
            amount = float(self.amount_var.get())
            if amount <= 0:
                messagebox.showerror("错误", "金额必须大于0")
                return
                
            transaction_type = self.type_var.get()
            category = self.category_var.get().strip()
            description = self.description_var.get().strip()
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 保存到数据库
            self.cursor.execute('''
                INSERT INTO transactions (date, type, category, amount, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (date, transaction_type, category, amount, description))
            self.conn.commit()
            
            # 清空输入框
            self.clear_inputs()
            
            # 更新显示
            self.update_transaction_list()
            self.update_statistics()
            
            messagebox.showinfo("成功", "记录添加成功！")
            
        except ValueError:
            messagebox.showerror("错误", "请输入有效的金额")
        except Exception as e:
            messagebox.showerror("错误", f"添加记录失败：{str(e)}")
            
    def edit_transaction(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要编辑的记录")
            return
            
        try:
            if not self.category_var.get().strip():
                messagebox.showerror("错误", "请输入类别")
                return
                
            amount = float(self.amount_var.get())
            if amount <= 0:
                messagebox.showerror("错误", "金额必须大于0")
                return
                
            item = self.tree.item(selected_items[0])
            record_id = item['values'][0]
            
            # 更新数据库
            self.cursor.execute('''
                UPDATE transactions 
                SET type=?, category=?, amount=?, description=?
                WHERE id=?
            ''', (self.type_var.get(), self.category_var.get().strip(), amount, 
                  self.description_var.get().strip(), record_id))
            self.conn.commit()
            
            # 清空输入框
            self.clear_inputs()
            
            # 更新显示
            self.update_transaction_list()
            self.update_statistics()
            
            messagebox.showinfo("成功", "记录更新成功！")
            
        except ValueError:
            messagebox.showerror("错误", "请输入有效的金额")
        except Exception as e:
            messagebox.showerror("错误", f"更新记录失败：{str(e)}")
            
    def delete_transaction(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要删除的记录")
            return
            
        if messagebox.askyesno("确认", "确定要删除选中的记录吗？"):
            try:
                item = self.tree.item(selected_items[0])
                record_id = item['values'][0]
                
                # 从数据库删除
                self.cursor.execute('DELETE FROM transactions WHERE id=?', (record_id,))
                self.conn.commit()
                
                # 清空输入框
                self.clear_inputs()
                
                # 更新显示
                self.update_transaction_list()
                self.update_statistics()
                
                messagebox.showinfo("成功", "记录删除成功！")
                
            except Exception as e:
                messagebox.showerror("错误", f"删除记录失败：{str(e)}")
                
    def clear_inputs(self):
        self.type_var.set('支出')
        self.category_var.set('')
        self.amount_var.set('')
        self.description_var.set('')
            
    def update_transaction_list(self):
        try:
            # 清空现有显示
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # 从数据库获取记录
            self.cursor.execute('SELECT id, date, type, category, amount, description FROM transactions ORDER BY date DESC')
            for record in self.cursor.fetchall():
                self.tree.insert('', 'end', values=record)
        except Exception as e:
            messagebox.showerror("错误", f"更新记录列表失败：{str(e)}")
            
    def update_statistics(self):
        try:
            # 计算总收入
            self.cursor.execute('SELECT SUM(amount) FROM transactions WHERE type="收入"')
            total_income = self.cursor.fetchone()[0] or 0
            
            # 计算总支出
            self.cursor.execute('SELECT SUM(amount) FROM transactions WHERE type="支出"')
            total_expense = self.cursor.fetchone()[0] or 0
            
            # 计算结余
            balance = total_income - total_expense
            
            # 更新标签
            self.total_income_label.config(text=f"总收入: ¥{total_income:.2f}")
            self.total_expense_label.config(text=f"总支出: ¥{total_expense:.2f}")
            self.balance_label.config(text=f"结余: ¥{balance:.2f}")
        except Exception as e:
            messagebox.showerror("错误", f"更新统计信息失败：{str(e)}")
            
    def on_closing(self):
        try:
            if messagebox.askokcancel("退出", "确定要退出程序吗？"):
                if hasattr(self, 'conn'):
                    self.conn.close()
                self.root.destroy()
                sys.exit(0)
        except Exception as e:
            print(f"关闭程序时出错：{str(e)}")
            self.root.destroy()
            sys.exit(1)
            
    def run(self):
        try:
            self.root.mainloop()
        except Exception as e:
            messagebox.showerror("错误", f"程序运行出错：{str(e)}")
            self.root.destroy()
            sys.exit(1)

    def export_data(self):
        try:
            # 选择保存路径
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV 文件", "*.csv")],
                title="导出数据"
            )
            
            if file_path:
                # 获取所有记录
                self.cursor.execute('SELECT date, type, category, amount, description FROM transactions ORDER BY date DESC')
                records = self.cursor.fetchall()
                
                # 写入CSV文件
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as file:
                    writer = csv.writer(file)
                    # 写入表头
                    writer.writerow(['日期', '类型', '类别', '金额', '描述'])
                    # 写入数据
                    writer.writerows(records)
                
                messagebox.showinfo("成功", "数据导出成功！")
                
        except Exception as e:
            messagebox.showerror("错误", f"导出数据失败：{str(e)}")
            
    def clear_all_data(self):
        if messagebox.askyesno("警告", "确定要清空所有数据吗？此操作不可恢复！"):
            try:
                # 清空数据库
                self.cursor.execute('DELETE FROM transactions')
                self.conn.commit()
                
                # 更新显示
                self.update_transaction_list()
                self.update_statistics()
                
                messagebox.showinfo("成功", "数据已清空！")
                
            except Exception as e:
                messagebox.showerror("错误", f"清空数据失败：{str(e)}")
                
    def show_help(self):
        help_text = """
使用说明：

1. 添加记录：
   - 选择类型（收入/支出）
   - 输入类别（如：工资、餐饮等）
   - 输入金额
   - 添加描述（可选）
   - 点击"添加记录"按钮

2. 编辑记录：
   - 在列表中选择要编辑的记录
   - 修改相关信息
   - 点击"编辑记录"按钮

3. 删除记录：
   - 在列表中选择要删除的记录
   - 点击"删除记录"按钮
   - 确认删除

4. 导出数据：
   - 点击"文件"菜单
   - 选择"导出数据"
   - 选择保存位置

5. 清空数据：
   - 点击"文件"菜单
   - 选择"清空数据"
   - 确认操作
"""
        messagebox.showinfo("使用说明", help_text)
        
    def show_about(self):
        about_text = """
家庭收支管理系统 v1.0

功能特点：
- 收支记录管理
- 数据统计
- 数据导出
- 界面美观

作者：AI助手
"""
        messagebox.showinfo("关于", about_text)

    def show_monthly_stats(self):
        try:
            # 获取当前年月
            current_date = datetime.now()
            year = current_date.year
            month = current_date.month
            
            # 获取本月第一天和最后一天
            _, last_day = calendar.monthrange(year, month)
            start_date = f"{year}-{month:02d}-01"
            end_date = f"{year}-{month:02d}-{last_day}"
            
            # 查询本月收入
            self.cursor.execute('''
                SELECT SUM(amount) FROM transactions 
                WHERE type="收入" AND date BETWEEN ? AND ?
            ''', (start_date, end_date))
            monthly_income = self.cursor.fetchone()[0] or 0
            
            # 查询本月支出
            self.cursor.execute('''
                SELECT SUM(amount) FROM transactions 
                WHERE type="支出" AND date BETWEEN ? AND ?
            ''', (start_date, end_date))
            monthly_expense = self.cursor.fetchone()[0] or 0
            
            # 计算结余
            monthly_balance = monthly_income - monthly_expense
            
            # 显示统计结果
            stats_text = f"""
本月统计 ({year}年{month}月)

收入总额：¥{monthly_income:.2f}
支出总额：¥{monthly_expense:.2f}
本月结余：¥{monthly_balance:.2f}

统计期间：{start_date} 至 {end_date}
"""
            messagebox.showinfo("本月统计", stats_text)
            
        except Exception as e:
            messagebox.showerror("错误", f"统计失败：{str(e)}")
            
    def show_category_stats(self):
        try:
            # 创建统计窗口
            stats_window = tk.Toplevel(self.root)
            stats_window.title("类别统计")
            stats_window.geometry("600x400")
            
            # 创建notebook用于切换收入/支出统计
            notebook = ttk.Notebook(stats_window)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # 收入统计页
            income_frame = ttk.Frame(notebook)
            notebook.add(income_frame, text="收入类别")
            
            # 支出统计页
            expense_frame = ttk.Frame(notebook)
            notebook.add(expense_frame, text="支出类别")
            
            # 创建收入统计表格
            income_tree = ttk.Treeview(income_frame, columns=('类别', '金额', '占比'), show='headings')
            income_tree.heading('类别', text='类别')
            income_tree.heading('金额', text='金额')
            income_tree.heading('占比', text='占比')
            income_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # 创建支出统计表格
            expense_tree = ttk.Treeview(expense_frame, columns=('类别', '金额', '占比'), show='headings')
            expense_tree.heading('类别', text='类别')
            expense_tree.heading('金额', text='金额')
            expense_tree.heading('占比', text='占比')
            expense_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # 获取收入统计
            self.cursor.execute('''
                SELECT category, SUM(amount) as total
                FROM transactions
                WHERE type="收入"
                GROUP BY category
                ORDER BY total DESC
            ''')
            income_data = self.cursor.fetchall()
            
            # 获取支出统计
            self.cursor.execute('''
                SELECT category, SUM(amount) as total
                FROM transactions
                WHERE type="支出"
                GROUP BY category
                ORDER BY total DESC
            ''')
            expense_data = self.cursor.fetchall()
            
            # 计算总收入
            total_income = sum(amount for _, amount in income_data)
            total_expense = sum(amount for _, amount in expense_data)
            
            # 显示收入统计
            for category, amount in income_data:
                percentage = (amount / total_income * 100) if total_income > 0 else 0
                income_tree.insert('', 'end', values=(category, f"¥{amount:.2f}", f"{percentage:.1f}%"))
            
            # 显示支出统计
            for category, amount in expense_data:
                percentage = (amount / total_expense * 100) if total_expense > 0 else 0
                expense_tree.insert('', 'end', values=(category, f"¥{amount:.2f}", f"{percentage:.1f}%"))
            
        except Exception as e:
            messagebox.showerror("错误", f"统计失败：{str(e)}")
            
    def show_yearly_stats(self):
        try:
            # 获取当前年份
            current_year = datetime.now().year
            
            # 创建统计窗口
            stats_window = tk.Toplevel(self.root)
            stats_window.title(f"{current_year}年度统计")
            stats_window.geometry("800x600")
            
            # 创建表格
            tree = ttk.Treeview(stats_window, columns=('月份', '收入', '支出', '结余'), show='headings')
            tree.heading('月份', text='月份')
            tree.heading('收入', text='收入')
            tree.heading('支出', text='支出')
            tree.heading('结余', text='结余')
            tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # 添加滚动条
            scrollbar = ttk.Scrollbar(stats_window, orient=tk.VERTICAL, command=tree.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            tree.configure(yscrollcommand=scrollbar.set)
            
            # 计算每月统计数据
            for month in range(1, 13):
                # 获取当月第一天和最后一天
                _, last_day = calendar.monthrange(current_year, month)
                start_date = f"{current_year}-{month:02d}-01"
                end_date = f"{current_year}-{month:02d}-{last_day}"
                
                # 查询当月收入
                self.cursor.execute('''
                    SELECT SUM(amount) FROM transactions 
                    WHERE type="收入" AND date BETWEEN ? AND ?
                ''', (start_date, end_date))
                monthly_income = self.cursor.fetchone()[0] or 0
                
                # 查询当月支出
                self.cursor.execute('''
                    SELECT SUM(amount) FROM transactions 
                    WHERE type="支出" AND date BETWEEN ? AND ?
                ''', (start_date, end_date))
                monthly_expense = self.cursor.fetchone()[0] or 0
                
                # 计算当月结余
                monthly_balance = monthly_income - monthly_expense
                
                # 添加到表格
                tree.insert('', 'end', values=(
                    f"{month}月",
                    f"¥{monthly_income:.2f}",
                    f"¥{monthly_expense:.2f}",
                    f"¥{monthly_balance:.2f}"
                ))
            
            # 计算年度总计
            self.cursor.execute('''
                SELECT 
                    SUM(CASE WHEN type="收入" THEN amount ELSE 0 END) as total_income,
                    SUM(CASE WHEN type="支出" THEN amount ELSE 0 END) as total_expense
                FROM transactions 
                WHERE strftime('%Y', date) = ?
            ''', (str(current_year),))
            
            total_income, total_expense = self.cursor.fetchone()
            total_income = total_income or 0
            total_expense = total_expense or 0
            total_balance = total_income - total_expense
            
            # 添加年度总计行
            tree.insert('', 'end', values=(
                "年度总计",
                f"¥{total_income:.2f}",
                f"¥{total_expense:.2f}",
                f"¥{total_balance:.2f}"
            ))
            
        except Exception as e:
            messagebox.showerror("错误", f"统计失败：{str(e)}")

    def show_statistics_charts(self):
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showerror("错误", "未安装matplotlib库，无法显示图表。\n请使用pip安装：pip install matplotlib numpy")
            return
            
        try:
            # 创建统计窗口
            stats_window = tk.Toplevel(self.root)
            stats_window.title("统计图表")
            stats_window.geometry("1000x800")
            
            # 创建notebook用于切换不同类型的图表
            notebook = ttk.Notebook(stats_window)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # 创建各个图表页面
            monthly_frame = ttk.Frame(notebook)
            notebook.add(monthly_frame, text="月度收支趋势")
            
            category_frame = ttk.Frame(notebook)
            notebook.add(category_frame, text="类别占比")
            
            # 设置图表样式
            plt.style.use('default')  # 使用默认样式
            
            # 创建月度收支趋势图
            self.create_monthly_trend_chart(monthly_frame)
            
            # 创建类别占比图
            self.create_category_pie_chart(category_frame)
            
        except Exception as e:
            messagebox.showerror("错误", f"创建统计图表失败：{str(e)}")
            
    def create_monthly_trend_chart(self, parent):
        try:
            # 获取当前年份
            current_year = datetime.now().year
            
            # 准备数据
            months = []
            incomes = []
            expenses = []
            
            for month in range(1, 13):
                # 获取当月第一天和最后一天
                _, last_day = calendar.monthrange(current_year, month)
                start_date = f"{current_year}-{month:02d}-01"
                end_date = f"{current_year}-{month:02d}-{last_day}"
                
                # 查询当月收入
                self.cursor.execute('''
                    SELECT SUM(amount) FROM transactions 
                    WHERE type="收入" AND date BETWEEN ? AND ?
                ''', (start_date, end_date))
                monthly_income = self.cursor.fetchone()[0] or 0
                
                # 查询当月支出
                self.cursor.execute('''
                    SELECT SUM(amount) FROM transactions 
                    WHERE type="支出" AND date BETWEEN ? AND ?
                ''', (start_date, end_date))
                monthly_expense = self.cursor.fetchone()[0] or 0
                
                months.append(f"{month}月")
                incomes.append(monthly_income)
                expenses.append(monthly_expense)
            
            # 创建图表
            fig, ax = plt.subplots(figsize=(10, 6))
            x = np.arange(len(months))
            width = 0.35
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
            plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
            
            ax.bar(x - width/2, incomes, width, label='收入', color='#4CAF50')
            ax.bar(x + width/2, expenses, width, label='支出', color='#F44336')
            
            ax.set_title(f'{current_year}年月度收支趋势', fontsize=12, pad=20)
            ax.set_xlabel('月份')
            ax.set_ylabel('金额 (元)')
            ax.set_xticks(x)
            ax.set_xticklabels(months)
            ax.legend()
            
            # 添加数值标签
            for i, v in enumerate(incomes):
                ax.text(i - width/2, v, f'¥{v:.0f}', ha='center', va='bottom')
            for i, v in enumerate(expenses):
                ax.text(i + width/2, v, f'¥{v:.0f}', ha='center', va='bottom')
            
            # 将图表添加到窗口
            canvas = FigureCanvasTkAgg(fig, master=parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            messagebox.showerror("错误", f"创建月度趋势图失败：{str(e)}")
            
    def create_category_pie_chart(self, parent):
        try:
            # 创建左右分栏
            left_frame = ttk.Frame(parent)
            left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            right_frame = ttk.Frame(parent)
            right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
            plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
            
            # 获取收入类别数据
            self.cursor.execute('''
                SELECT category, SUM(amount) as total
                FROM transactions
                WHERE type="收入"
                GROUP BY category
                ORDER BY total DESC
            ''')
            income_data = self.cursor.fetchall()
            
            # 获取支出类别数据
            self.cursor.execute('''
                SELECT category, SUM(amount) as total
                FROM transactions
                WHERE type="支出"
                GROUP BY category
                ORDER BY total DESC
            ''')
            expense_data = self.cursor.fetchall()
            
            # 创建收入饼图
            if income_data:
                fig_income, ax_income = plt.subplots(figsize=(6, 6))
                categories = [item[0] for item in income_data]
                amounts = [item[1] for item in income_data]
                
                ax_income.pie(amounts, labels=categories, autopct='%1.1f%%', 
                            colors=plt.cm.Pastel1(np.linspace(0, 1, len(categories))))
                ax_income.set_title('收入类别占比')
                
                canvas_income = FigureCanvasTkAgg(fig_income, master=left_frame)
                canvas_income.draw()
                canvas_income.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # 创建支出饼图
            if expense_data:
                fig_expense, ax_expense = plt.subplots(figsize=(6, 6))
                categories = [item[0] for item in expense_data]
                amounts = [item[1] for item in expense_data]
                
                ax_expense.pie(amounts, labels=categories, autopct='%1.1f%%',
                             colors=plt.cm.Pastel1(np.linspace(0, 1, len(categories))))
                ax_expense.set_title('支出类别占比')
                
                canvas_expense = FigureCanvasTkAgg(fig_expense, master=right_frame)
                canvas_expense.draw()
                canvas_expense.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            messagebox.showerror("错误", f"创建类别占比图失败：{str(e)}")

    def show_ai_analysis(self):
        try:
            # 获取最近一个月的收支数据
            current_date = datetime.now()
            _, last_day = calendar.monthrange(current_date.year, current_date.month)
            start_date = f"{current_date.year}-{current_date.month:02d}-01"
            end_date = f"{current_date.year}-{current_date.month:02d}-{last_day}"
            
            self.cursor.execute('''
                SELECT type, category, SUM(amount) as total
                FROM transactions
                WHERE date BETWEEN ? AND ?
                GROUP BY type, category
            ''', (start_date, end_date))
            
            results = self.cursor.fetchall()
            
            # 准备数据
            data = {
                "income": {},
                "expense": {}
            }
            
            for row in results:
                type_, category, amount = row
                if type_ == "收入":
                    data["income"][category] = amount
                else:
                    data["expense"][category] = amount
            
            # 调用AI API进行分析
            response = self.call_ai_api("analyze", data)
            
            # 显示分析结果
            self.show_ai_result("收支分析", response)
            
        except Exception as e:
            messagebox.showerror("错误", f"AI分析失败：{str(e)}")
            
    def show_ai_advice(self):
        try:
            # 获取最近三个月的收支数据
            current_date = datetime.now()
            start_date = f"{current_date.year}-{(current_date.month-2):02d}-01"
            end_date = f"{current_date.year}-{current_date.month:02d}-{calendar.monthrange(current_date.year, current_date.month)[1]}"
            
            self.cursor.execute('''
                SELECT type, category, SUM(amount) as total
                FROM transactions
                WHERE date BETWEEN ? AND ?
                GROUP BY type, category
            ''', (start_date, end_date))
            
            results = self.cursor.fetchall()
            
            # 准备数据
            data = {
                "income": {},
                "expense": {}
            }
            
            for row in results:
                type_, category, amount = row
                if type_ == "收入":
                    data["income"][category] = amount
                else:
                    data["expense"][category] = amount
            
            # 调用AI API获取建议
            response = self.call_ai_api("advice", data)
            
            # 显示建议结果
            self.show_ai_result("理财建议", response)
            
        except Exception as e:
            messagebox.showerror("错误", f"获取AI建议失败：{str(e)}")
            
    def call_ai_api(self, action, data):
        try:
            # 准备请求数据
            payload = {
                "chatId": "family_finance",
                "stream": False,
                "detail": False,
                "messages": [
                    {
                        "role": "user",
                        "content": f"请分析以下{action}数据：\n{json.dumps(data, ensure_ascii=False, indent=2)}"
                    }
                ],
                "variables": {}
            }
            
            headers = {
                "Authorization": f"Bearer {AI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # 发送POST请求
            response = requests.post(AI_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            # 返回分析结果
            if "choices" in result and len(result["choices"]) > 0:
                return {
                    "analysis": result["choices"][0]["message"]["content"]
                }
            else:
                return {
                    "analysis": "无法获取分析结果"
                }
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API请求失败：{str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"解析响应失败：{str(e)}")
        except Exception as e:
            raise Exception(f"API调用失败：{str(e)}")
            
    def show_ai_result(self, title, response):
        # 创建结果窗口
        result_window = tk.Toplevel(self.root)
        result_window.title(title)
        result_window.geometry("600x400")
        
        # 创建文本显示区域
        text_frame = ttk.Frame(result_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("微软雅黑", 10))
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # 显示结果
        text_widget.insert(tk.END, response.get("analysis", ""))
        text_widget.config(state=tk.DISABLED)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # 使窗口居中
        result_window.update_idletasks()
        width = result_window.winfo_width()
        height = result_window.winfo_height()
        x = (result_window.winfo_screenwidth() // 2) - (width // 2)
        y = (result_window.winfo_screenheight() // 2) - (height // 2)
        result_window.geometry(f"+{x}+{y}")

if __name__ == '__main__':
    try:
        app = FamilyFinanceManager()
        app.run()
    except Exception as e:
        print(f"程序启动失败：{str(e)}")
        sys.exit(1) 