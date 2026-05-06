#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# الألوان
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_banner():
    print(f"""{RED}
╔════════════════════════════════════════════════════════════╗
║     ⚠️  أداة متابعة صفحات فيسبوك التلقائية  ⚠️           ║
║         للاستخدام التعليمي فقط - استخدامك مسؤوليتك         ║
╚════════════════════════════════════════════════════════════╝{RESET}
""")

def load_pages(filename='pages.txt'):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    return []

def save_pages(pages, filename='pages.txt'):
    with open(filename, 'w') as f:
        for page in pages:
            f.write(page + '\n')

def add_page():
    pages = load_pages()
    print(f"{BLUE}📝 أدخل رابط صفحة فيسبوك (مثال: https://www.facebook.com/facebook){RESET}")
    url = input("→ ").strip()
    
    if url in pages:
        print(f"{YELLOW}⚠️ هذه الصفحة موجودة بالفعل!{RESET}")
    else:
        pages.append(url)
        save_pages(pages)
        print(f"{GREEN}✅ تم إضافة الصفحة: {url}{RESET}")

def show_pages():
    pages = load_pages()
    if not pages:
        print(f"{YELLOW}⚠️ لا توجد صفحات مضاف بعد.{RESET}")
        return
    
    print(f"{BLUE}📋 قائمة الصفحات المراد متابعتها ({len(pages)} صفحة):{RESET}")
    for i, page in enumerate(pages, 1):
        print(f"  {i}. {page}")

def remove_page():
    pages = load_pages()
    if not pages:
        return
    
    show_pages()
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

def setup_driver():
    """إعداد متصفح Chrome باستخدام webdriver-manager"""
    print(f"{BLUE}⚙️ جاري إعداد المتصفح...{RESET}")
    
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # تحديد مسار Chromium في Termux
    options.binary_location = "/data/data/com.termux/files/usr/bin/chromium"
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=options
    )
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def login_facebook(driver, email, password):
    print(f"{BLUE}🔐 جاري تسجيل الدخول إلى فيسبوك...{RESET}")
    
    driver.get("https://www.facebook.com/login")
    time.sleep(3)
    
    try:
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        email_field.send_keys(email)
        
        password_field = driver.find_element(By.ID, "pass")
        password_field.send_keys(password)
        
        login_button = driver.find_element(By.NAME, "login")
        login_button.click()
        
        time.sleep(5)
        print(f"{GREEN}✅ تم تسجيل الدخول بنجاح!{RESET}")
        return True
    except Exception as e:
        print(f"{RED}❌ فشل تسجيل الدخول: {e}{RESET}")
        return False

def follow_page(driver, page_url, delay=45):
    print(f"{YELLOW}📄 جاري متابعة: {page_url}{RESET}")
    
    try:
        driver.get(page_url)
        time.sleep(5)
        
        # محاولة إيجاد زر المتابعة
        follow_buttons = driver.find_elements(By.XPATH, "//div[@aria-label='متابعة' or @aria-label='Follow']")
        
        if follow_buttons:
            follow_buttons[0].click()
            print(f"  {GREEN}✅ تمت المتابعة بنجاح!{RESET}")
        else:
            like_buttons = driver.find_elements(By.XPATH, "//div[@aria-label='أعجبني' or @aria-label='Like']")
            if like_buttons:
                like_buttons[0].click()
                print(f"  {GREEN}✅ تم الإعجاب بالصفحة!{RESET}")
            else:
                print(f"  {YELLOW}⚠️ زر المتابعة غير موجود أو تمت المتابعة مسبقاً{RESET}")
        
        time.sleep(delay)
        return True
        
    except Exception as e:
        print(f"  {RED}❌ خطأ في متابعة الصفحة: {e}{RESET}")
        return False

def start_following(email, password):
    pages = load_pages()
    if not pages:
        print(f"{RED}❌ لا توجد صفحات للمتابعة. أضف صفحات أولاً.{RESET}")
        return
    
    print(f"{BLUE}🚀 بدء متابعة {len(pages)} صفحة...{RESET}")
    print(f"{YELLOW}⚠️ سيتم التأخير 45 ثانية بين كل صفحة لتجنب الحظر{RESET}\n")
    
    driver = None
    try:
        driver = setup_driver()
        
        if not login_facebook(driver, email, password):
            return
        
        success_count = 0
        for i, page_url in enumerate(pages, 1):
            print(f"\n{BLUE}[{i}/{len(pages)}]{RESET} متابعة...")
            if follow_page(driver, page_url):
                success_count += 1
        
        print(f"\n{GREEN}✅ اكتملت العملية! تمت متابعة {success_count}/{len(pages)} صفحة{RESET}")
        
    except Exception as e:
        print(f"{RED}❌ خطأ عام: {e}{RESET}")
    finally:
        if driver:
            driver.quit()

def main_menu():
    print(f"{BLUE}📱 بيانات حساب فيسبوك:{RESET}")
    email = input("البريد الإلكتروني أو رقم الهاتف: ").strip()
    password = input("كلمة المرور: ").strip()
    
    while True:
        print(f"""
{RED}════════════════════════════════════════════════════════════{RESET}
{GREEN}🎯 القائمة الرئيسية:{RESET}
{RED}════════════════════════════════════════════════════════════{RESET}
  {YELLOW}1.{RESET} ➕ إضافة صفحة جديدة للمتابعة
  {YELLOW}2.{RESET} 📋 عرض قائمة الصفحات
  {YELLOW}3.{RESET} 🗑️ حذف صفحة من القائمة
  {YELLOW}4.{RESET} 🚀 بدء متابعة جميع الصفحات
  {YELLOW}5.{RESET} 🧹 مسح جميع الصفحات
  {YELLOW}0.{RESET} ❌ خروج
{RED}════════════════════════════════════════════════════════════{RESET}
""")
        choice = input(f"{GREEN}👉 اختر رقم: {RESET}")
        
        if choice == '1':
            add_page()
        elif choice == '2':
            show_pages()
        elif choice == '3':
            remove_page()
        elif choice == '4':
            start_following(email, password)
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
    print(f"{RED}⚠️ تحذير: هذه الأداة للاستخدام التعليمي فقط{RESET}")
    print(f"{RED}   استخدامها قد يؤدي إلى حظر حساب فيسبوك الخاص بك{RESET}\n")
    
    confirm = input(f"{YELLOW}هل تفهم المخاطر وتوافق على الاستخدام التعليمي؟ (y/n): {RESET}")
    if confirm.lower() == 'y':
        main_menu()
    else:
        print(f"{GREEN}تم الإلغاء. وداعاً!{RESET}")
