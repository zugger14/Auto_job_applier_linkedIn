from __future__ import annotations
'''
Author:     Sai Vignesh Golla
LinkedIn:   https://www.linkedin.com/in/saivigneshgolla/

Copyright (C) 2024 Sai Vignesh Golla

License:    GNU Affero General Public License
            https://www.gnu.org/licenses/agpl-3.0.en.html
            
GitHub:     https://github.com/GodsScion/Auto_job_applier_linkedIn

Support me: https://github.com/sponsors/GodsScion

version:    26.01.20.5.08
'''

import sys
import os
from modules.helpers import get_default_temp_profile, make_directories
from config.settings import run_in_background, stealth_mode, disable_extensions, safe_mode, file_name, failed_file_name, logs_folder_path, generated_resume_path
from config.questions import default_resume_path
if stealth_mode:
    import undetected_chromedriver as uc
else: 
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    # from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from modules.helpers import find_default_profile_directory, critical_error_log, print_lg
from selenium.common.exceptions import SessionNotCreatedException

def createChromeSession(isRetry: bool = False):
    make_directories([file_name,failed_file_name,logs_folder_path+"/screenshots",default_resume_path,generated_resume_path+"/temp"])
    # Set up WebDriver with Chrome Profile
    options = uc.ChromeOptions() if stealth_mode else Options()
    if run_in_background:   options.add_argument("--headless")
    if disable_extensions:  options.add_argument("--disable-extensions")
    if sys.platform.startswith('linux'):
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    print_lg("IF YOU HAVE MORE THAN 10 TABS OPENED, PLEASE CLOSE OR BOOKMARK THEM! Or it's highly likely that application will just open browser and not do anything!")
    profile_dir = find_default_profile_directory()
    if isRetry:
        print_lg("Will login with a guest profile, browsing history will not be saved in the browser!")
    elif profile_dir and not safe_mode:
        options.add_argument(f"--user-data-dir={profile_dir}")
    else:
        print_lg("Logging in with a guest profile, Web history will not be saved!")
        options.add_argument(f"--user-data-dir={get_default_temp_profile()}")
    if stealth_mode:
        print_lg("Downloading Chrome Driver... This may take some time. Undetected mode requires download every run!")
        import subprocess, re
        major_version = None
        try:
            if sys.platform == 'darwin':
                cmd = "/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --version"
            else:
                cmd = "google-chrome --version"
            out = subprocess.check_output(cmd, shell=True).decode()
            match = re.search(r'Google Chrome (\d+)', out)
            if match:
                major_version = int(match.group(1))
        except Exception:
            pass

        try:
            if major_version:
                driver = uc.Chrome(options=options, version_main=major_version)
            else:
                driver = uc.Chrome(options=options)
        except Exception as uc_err:
            print_lg(f"Failed with version_main={major_version}: {uc_err}. Retrying with fresh options...")
            retry_options = uc.ChromeOptions()
            if run_in_background: retry_options.add_argument("--headless")
            if disable_extensions: retry_options.add_argument("--disable-extensions")
            if sys.platform.startswith('linux'):
                retry_options.add_argument("--no-sandbox")
                retry_options.add_argument("--disable-dev-shm-usage")
            retry_options.add_argument(f"--user-data-dir={get_default_temp_profile()}")
            if major_version:
                driver = uc.Chrome(options=retry_options, version_main=major_version)
            else:
                driver = uc.Chrome(options=retry_options)
    else: 
        driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    wait = WebDriverWait(driver, 5)
    actions = ActionChains(driver)
    return options, driver, actions, wait

try:
    options, driver, actions, wait = None, None, None, None
    options, driver, actions, wait = createChromeSession()
except SessionNotCreatedException as e:
    critical_error_log("Failed to create Chrome Session, retrying with guest profile", e)
    options, driver, actions, wait = createChromeSession(True)
except Exception as e:
    msg = f'Error initializing Chrome session: {e}\n\nIf issue persists, try Safe Mode. Set safe_mode = True in config.py'
    if isinstance(e, TimeoutError): msg = "Couldn't download Chrome-driver. Set stealth_mode = False in config!"
    print_lg(msg)
    critical_error_log("In Opening Chrome", e)
    try:
        from pyautogui import alert
        alert(msg, "Error in opening chrome")
    except Exception:
        pass
    try:
        if driver: driver.quit()
    except Exception:
        pass
    exit(1)
    
