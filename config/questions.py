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


###################################################### APPLICATION INPUTS ######################################################


# >>>>>>>>>>> Easy Apply Questions & Inputs <<<<<<<<<<<

# Give an relative path of your default resume to be uploaded. If file in not found, will continue using your previously uploaded resume in LinkedIn.
default_resume_path = "Shirish_Maharjan_CV copy.pdf"      # (In Development)

# What do you want to answer for questions that ask about years of experience you have, this is different from current_experience? 
years_of_experience = "5"          # A number in quotes Eg: "0","1","2","3","4", etc.

# Do you need visa sponsorship now or in future?
require_visa = "No"               # "Yes" or "No"

# What is the link to your portfolio website, leave it empty as "", if you want to leave this question unanswered
website = ""                        # "www.example.bio" or "" and so on....

# Please provide the link to your LinkedIn profile.
linkedIn = ""       # "https://www.linkedin.com/in/example" or "" and so on...

# What is the status of your citizenship? # If left empty as "", tool will not answer the question. However, note that some companies make it compulsory to be answered
# Valid options are: "U.S. Citizen/Permanent Resident", "Non-citizen allowed to work for any employer", "Non-citizen allowed to work for current employer", "Non-citizen seeking work authorization", "Canadian Citizen/Permanent Resident" or "Other"
us_citizenship = ""



## SOME ANNOYING QUESTIONS BY COMPANIES 🫠 ##

# What to enter in your desired salary question (American and European), What is your expected CTC (South Asian and others)?, only enter in numbers as some companies only allow numbers,
desired_salary = 4500          # 80000, 90000, 100000 or 120000 and so on... Do NOT use quotes
'''
Note: If question has the word "lakhs" in it (Example: What is your expected CTC in lakhs), 
then it will add '.' before last 5 digits and answer. Examples: 
* 2400000 will be answered as "24.00"
* 850000 will be answered as "8.50"
And if asked in months, then it will divide by 12 and answer. Examples:
* 2400000 will be answered as "200000"
* 850000 will be answered as "70833"
'''

# What is your current CTC? Some companies make it compulsory to be answered in numbers...
current_ctc = 800000            # 800000, 900000, 1000000 or 1200000 and so on... Do NOT use quotes
'''
Note: If question has the word "lakhs" in it (Example: What is your current CTC in lakhs), 
then it will add '.' before last 5 digits and answer. Examples: 
* 2400000 will be answered as "24.00"
* 850000 will be answered as "8.50"
# And if asked in months, then it will divide by 12 and answer. Examples:
# * 2400000 will be answered as "200000"
# * 850000 will be answered as "70833"
'''

# (In Development) # Currency of salaries you mentioned. Companies that allow string inputs will add this tag to the end of numbers. Eg: 
# currency = "INR"                 # "USD", "INR", "EUR", etc.

# What is your notice period in days?
notice_period = 30                   # Any number >= 0 without quotes. Eg: 0, 7, 15, 30, 45, etc.
'''
Note: If question has 'month' or 'week' in it (Example: What is your notice period in months), 
then it will divide by 30 or 7 and answer respectively. Examples:
* For notice_period = 66:
  - "66" OR "2" if asked in months OR "9" if asked in weeks
* For notice_period = 15:"
  - "15" OR "0" if asked in months OR "2" if asked in weeks
* For notice_period = 0:
  - "0" OR "0" if asked in months OR "0" if asked in weeks
'''

# Your LinkedIn headline in quotes Eg: "Software Engineer @ Google, Masters in Computer Science", "Recent Grad Student @ MIT, Computer Science"
linkedin_headline = "Full Stack Developer with Masters in Computer Science and 4+ years of experience" # "Headline" or "" to leave this question unanswered

# Your summary in quotes, use \n to add line breaks if using single quotes "Summary".You can skip \n if using triple quotes """Summary"""
linkedin_summary = """
I'm a Senior Software Engineer at Amazon with Masters in CS and 4+ years of experience in developing and maintaining Full Stack Web applications and cloud solutions. 
Specialized in React, Node.js, and Python.
"""

'''
Note: If left empty as "", the tool will not answer the question. However, note that some companies make it compulsory to be answered. Use \n to add line breaks.
''' 

# Your cover letter in quotes, use \n to add line breaks if using single quotes "Cover Letter".You can skip \n if using triple quotes """Cover Letter""" (This question makes sense though)
cover_letter = """
Cover Letter
"""
##> ------ Dheeraj Deshwal : dheeraj9811 Email:dheeraj20194@iiitd.ac.in/dheerajdeshwal9811@gmail.com - Feature ------

# Your user_information_all letter in quotes, use \n to add line breaks if using single quotes "user_information_all".You can skip \n if using triple quotes """user_information_all""" (This question makes sense though)
# We use this to pass to AI to generate answer from information , Assuing Information contians eg: resume  all the information like name, experience, skills, Country, any illness etc. 
user_information_all ="""
Shirish Maharjan
Mobile: +977-9803341626 | Email: shirishmaharjan0@gmail.com | LinkedIn: linkedin.com/in/shirish14/ | Location:
Kathmandu, Nepal
PROFESSIONAL SUMMARY
Results-driven DevOps & Software Intelligence Engineer with over 6 years of experience designing, automating,
and scaling cloud-native architectures. Proven track record in reducing deployment times by up to 70% and
eliminating manual configuration errors through robust Infrastructure as Code (IaC) and optimized CI/CD
pipelines. Adept at integrating AI coding assistants and Model Context Protocol (MCP) servers to build high-
productivity development workflows. Combines systems engineering precision with a creative analytical mindset
derived from digital music production and strategic problem-solving.
TECHNICAL SKILLS
▪ Cloud & Infrastructure: AWS (EC2, ECS, S3, VPC, IAM, Route 53, CloudWatch, Lambda), Azure, Docker,
Kubernetes
▪ Infrastructure as Code (IaC): Terraform, CloudFormation, Ansible
▪ CI/CD Pipelines: GitHub Actions, AWS CodePipeline, GitLab CI/CD, Bitbucket Pipelines, Azure Pipelines
▪ Monitoring & Observability: Datadog, Prometheus, Grafana, New Relic, Nagios, ELK Stack
▪ Automation & Programming: Python, JavaScript, TypeScript, Java, PHP, C, Bash, PowerShell
▪ AI & Software Intelligence: Cursor AI, GitHub Copilot, MCP Server integrations, AIOps workflows
▪ Databases & Operating Systems: MySQL, PostgreSQL, MongoDB, Oracle, MS SQL Server; Linux, macOS,
Windows
PROFESSIONAL EXPERIENCE
DevOps & Software Intelligence Engineer Apr 2025 – Present
Social Knowledge (RVLIFE), USA (Contract)
• Architected full-stack observability workflows using Datadog across APM, infrastructure metrics, and logs for
fast resolution.
• Authored reusable Terraform modules for AWS/Datadog, slashing environment deployment times by 70% with
strict reproducibility.
• Pioneered integration of AI assistants (Cursor AI, GitHub Copilot) and MCP servers to maximize developer
velocity.
• Engineered automated, zero-downtime CI/CD pipelines using GitHub Actions and AWS CodePipeline.
DevOps Engineer Jan 2024 – Mar 2025
EBPearls, Nepal
• Containerized high-traffic React, Node.js, NestJS, and Python apps using Docker to optimize environment
consistency.
• Automated software delivery pipelines with Bitbucket Pipelines and AWS CodePipeline, cutting deploy times
to minutes.
• Utilized Ansible and Terraform for server provisioning, reducing manual configuration errors by 90%.
• Established robust real-time monitoring infrastructures leveraging Nagios, New Relic, Prometheus, and
Grafana.
Page 1 of 2
• Developed a custom Node.js Zoom chatbot to automate real-time product release notifications for cross-
functional teams.
DevOps Engineer Jan 2023 – Jul 2023
Hitachi Energy, Nepal
• Orchestrated enterprise migration of ~150 repositories from SVN to Git, enabling modern collaborative
workflows.
• Standardized branching strategies and version control across teams through targeted developer training
sessions.
• Configured Azure Pipelines to automate builds and deployments for critical PHP and MS SQL applications.
DevOps Engineer Aug 2021 – Dec 2022
Legalfit, USA (Contract)
• Managed a fleet of ~100 servers using Ansible to ensure seamless, centralized configuration management.
• Successfully executed a zero-downtime automated DNS migration to AWS Route 53.
• Deployed and orchestrated highly available, auto-scaling environments on Docker and Kubernetes.
• Implemented security baselines aligned with the AWS Well-Architected Framework and SOC2 compliance
controls.
DevOps Engineer May 2020 – Aug 2021
Cloudyfox, Nepal
• Containerized multi-stack applications and deployed them onto highly scalable AWS ECS clusters using
Docker.
• Built GitLab CI/CD pipelines optimized for serverless AWS SAM infrastructure deployments.
• Managed scalable cloud infrastructure leveraging infrastructure as code via Terraform and AWS
CloudFormation.
• Centralized system logs by deploying an ELK Stack to enhance visibility and deep debugging capabilities.
EDUCATION & CREDENTIALS
Bachelor in Computer Information Systems (BCIS) 2014 – 2018
Apex College | Pokhara University | CGPA: 3.11/4.0
Higher Secondary Certificate & School Leaving Certificate 2010 – 2014
Trinity International College (HSEB: 80.8%) | Bhanubhakta Memorial HSS (SLC: 85%)
PROJECTS, ACHIEVEMENTS & HOBBIES
• Leadership & Web Development: Successfully led a cross-functional student team to design, build, and
deploy the official Apex College web infrastructure utilizing WordPress.
• Home Lab Innovation: Built personal GPU server infrastructure to run local LLMs and multi-modal GenAI
pipelines.
• Digital Music Production & Artistry: Active music producer and live drummer; experienced in DAW sound
engineering, multi-track mixing, arrangements, and performing for university events.
• Academic Excellence: Awarded "Best Final Year Academic Project" for building a secure multimedia e-
commerce platform.
• Strategic Mindset: Analytical problem solver; winner of multiple institutional and corporate chess competitions.
Page 2 of 2
"""
##<
'''
Note: If left empty as "", the tool will not answer the question. However, note that some companies make it compulsory to be answered. Use \n to add line breaks.
''' 

# Name of your most recent employer
recent_employer = "Not Applicable" # "", "Lala Company", "Google", "Snowflake", "Databricks"

# Example question: "On a scale of 1-10 how much experience do you have building web or mobile applications? 1 being very little or only in school, 10 being that you have built and launched applications to real users"
confidence_level = "8"             # Any number between "1" to "10" including 1 and 10, put it in quotes ""
##



# >>>>>>>>>>> RELATED SETTINGS <<<<<<<<<<<

## Allow Manual Inputs
# Should the tool pause before every submit application during easy apply to let you check the information?
pause_before_submit = False         # True or False, Note: True or False are case-sensitive
'''
Note: Will be treated as False if `run_in_background = True`
'''

# Should the tool pause if it needs help in answering questions during easy apply?
# Note: If set as False will answer randomly...
pause_at_failed_question = False    # True or False, Note: True or False are case-sensitive
'''
Note: Will be treated as False if `run_in_background = True`
'''
##

# Do you want to overwrite previous answers?
overwrite_previous_answers = False # True or False, Note: True or False are case-sensitive







############################################################################################################
'''
THANK YOU for using my tool 😊! Wishing you the best in your job hunt 🙌🏻!

Sharing is caring! If you found this tool helpful, please share it with your peers 🥺. Your support keeps this project alive.

Support my work on <PATREON_LINK>. Together, we can help more job seekers.

As an independent developer, I pour my heart and soul into creating tools like this, driven by the genuine desire to make a positive impact.

Your support, whether through donations big or small or simply spreading the word, means the world to me and helps keep this project alive and thriving.

Gratefully yours 🙏🏻,
Sai Vignesh Golla
'''
############################################################################################################