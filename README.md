# Library Management System

Flask + SQLite + Bootstrap വെച്ച് ചെയ്ത Library Management System.

## Features
- **Admin Panel**: Login, Add Book, Edit Book, Delete Book
- **Student Panel**: Login, Search Book, Issue Book, Return Book
- **Logic**: Book Issue ചെയ്യുമ്പോൾ Available Copies Auto കുറയും. Return ചെയ്യുമ്പോൾ കൂടും.
- **Out of Stock**: Copies ഇല്ലെങ്കിൽ "Out of Stock" Badge കാണിക്കും

## Tech Stack
Python, Flask, SQLite, HTML, CSS, Bootstrap

## How to Run
1. `pip install flask`
2. `python app.py` 
3. Browser-ൽ `http://127.0.0.1:5000` Open ചെയ്യൂ

## Default Login
**Admin:** username = admin, password = admin123  
**Student:** username = student, password = student123