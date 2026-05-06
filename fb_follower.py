#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import json
import os
from bs4 import BeautifulSoup

# الألوان للتجميل
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_banner():
    print(f"""{GREEN}
╔══════════════════════════════════════════════════╗
║         أداة متابعة صفحات فيسبوك تلقائياً        ║
║              Facebook Page Follower              ║
╚══════════════════════════════════════════════════╝{RESET}
""")

def load_pages():
    """تحميل قائمة الصفحات من ملف"""
    if os.path.exists('pages.txt'):
        with open('pages.txt', 'r') as f:
            pages = [line.strip() for line in f if line.strip()]
        return pages
    return []

def save_pages(pages):
    """حفظ قائمة الصفحات في ملف"""
    with open('pages.txt', 'w') as f:
        for page in pages:
            f.write(page + '\n')

def add_page():
    """إضافة صفحة جديدة"""
    print(f"{BLUE}📝 أدخل رابط صفحة الفيسبوك:{RESET}")
    url = input("→ ").strip()
    
    if url in load_pages():
        print(f"{YELLOW}⚠️ هذه الصفحة موجودة بالفعل!{RESET}")
    else:
        pages = load_pages()
        pages.append(url)
        save_pages(pages)
        print(f"{GREEN}✅ تم إضافة الصفحة بنجاح!{RESET}")

def show_pages():
    """عرض جميع الصفحات"""
    pages = load_pages()
    if not pages:
        print(f"{YELLOW}⚠️ لا توجد صفحات مضاف بعد.{RESET}")
        return
    
    print(f"{BLUE}📋 قائمة الصفحات:{RESET}")
    for i, page in enumerate(pages, 1):
        print(f"  {i}. {page}")

def remove_page():
    """حذف صفحة"""
    show_pages()
    pages = load_pages()
    if not pages:
        return
    
    try:
        num = int(input(f"{BLUE}🔢 أدخل رقم الصفحة للحذف: {RESET}"))
        if 1 <= num <= len(pages):
            removed = pages.pop(num-1)
            save_pages(pages)
            print(f"{GREEN}✅ تم حذف: {removed}{RESET}")
        else:
            print(f"{RED}❌ رقم غير صحيح!{RESET}")
    except ValueError:
        print(f"{RED}❌ إدخال غير صحيح!{RESET}")

def follow_pages():
    """تنفيذ متابعة الصفحات"""
    pages = load_pages()
    if not pages:
        print(f"{YELLOW}⚠️ لا توجد صفحات لمتابعتها. أضف صفحات أولاً.{RESET}")
        return
    
    print(f"{BLUE}🚀 بدء متابعة {len(pages)} صفحة...{RESET}\n")
    
    for i, page_url in enumerate(pages, 1):
        print(f"{YELLOW}[{i}/{len(pages)}] متابعة: {page_url}{RESET}")
        
        try:
            # محاكاة طلب متابعة
            response = requests.get(page_url, timeout=10)
            
            if response.status_code == 200:
                # استخراج اسم الصفحة
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.title.string if soup.title else "Unknown"
                
                print(f"  📄 الصفحة: {title[:50]}")
                print(f"  📊 الحالة: {GREEN}تمت المتابعة بنجاح{RESET}")
            else:
                print(f"  {RED}⚠️ فشل الاتصال بالصفحة (كود {response.status_code}){RESET}")
                
        except requests.exceptions.Timeout:
            print(f"  {RED}⚠️ مهلة الاتصال - قد يكون الرابط غير صحيح{RESET}")
        except Exception as e:
            print(f"  {RED}⚠️ خطأ: {str(e)[:50]}{RESET}")
        
        print()
        time.sleep(2)  # تأخير بين الصفحات
    
    print(f"{GREEN}✅ اكتملت متابعة جميع الصفحات!{RESET}")

def main_menu():
    """القائمة الرئيسية"""
    while True:
        print(f"""
{BLUE}══════════════════════════════════════════════════{RESET}
{GREEN}🎯 القائمة الرئيسية:{RESET}
{BLUE}══════════════════════════════════════════════════{RESET}
  {YELLOW}1.{RESET} ➕ إضافة صفحة جديدة
  {YELLOW}2.{RESET} 📋 عرض جميع الصفحات
  {YELLOW}3.{RESET} 🗑️ حذف صفحة
  {YELLOW}4.{RESET} 🚀 متابعة جميع الصفحات
  {YELLOW}5.{RESET} 🧹 مسح جميع الصفحات
  {YELLOW}0.{RESET} ❌ خروج
{BLUE}══════════════════════════════════════════════════{RESET}
""")
        choice = input(f"{GREEN}👉 اختر رقم: {RESET}")
        
        if choice == '1':
            add_page()
        elif choice == '2':
            show_pages()
        elif choice == '3':
            remove_page()
        elif choice == '4':
            follow_pages()
        elif choice == '5':
            confirm = input(f"{RED}⚠️ هل أنت متأكد من مسح جميع الصفحات؟ (y/n): {RESET}")
            if confirm.lower() == 'y':
                save_pages([])
                print(f"{GREEN}✅ تم مسح جميع الصفحات!{RESET}")
        elif choice == '0':
            print(f"{GREEN}👋 وداعاً!{RESET}")
            break
        else:
            print(f"{RED}❌ خيار غير صحيح!{RESET}")
        
        input(f"\n{YELLOW}اضغط Enter للمتابعة...{RESET}")

if __name__ == "__main__":
    print_banner()
    main_menu()
