"""Skill taxonomy: canonical skills mapped to their synonyms and alternative spellings.

Each canonical skill lists the ways it is commonly written in resumes and job
descriptions. The parser searches for every synonym as a whole word and maps it
back to the canonical name (Section 3.7.3 of the report).
"""

SKILL_TAXONOMY = {
    # Programming and backend
    "python": ["python", "python3"],
    "java": ["java", "core java", "j2ee"],
    "javascript": ["javascript", "js", "es6", "ecmascript"],
    "django": ["django", "django rest framework", "drf"],
    "flask": ["flask"],
    "fastapi": ["fastapi", "fast api"],
    "rest api": ["rest api", "rest apis", "restful", "restful api", "restful services"],
    "sql": ["sql", "mysql", "postgresql", "postgres", "t-sql", "tsql", "pl/sql", "sqlite", "ms sql"],
    "nosql": ["nosql", "mongodb", "mongo", "cassandra", "dynamodb"],
    "git": ["git", "github", "gitlab", "bitbucket", "version control"],
    "oop": ["oop", "object oriented programming", "object-oriented programming"],
    # Cloud and DevOps
    "aws": ["aws", "amazon web services", "ec2", "s3", "lambda"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "docker": ["docker", "containerization", "containers", "dockerfile"],
    "kubernetes": ["kubernetes", "k8s", "eks", "aks", "gke", "helm"],
    "linux": ["linux", "unix", "ubuntu", "centos", "rhel"],
    "ci/cd": ["ci/cd", "ci cd", "cicd", "continuous integration", "continuous delivery",
              "jenkins", "github actions", "gitlab ci"],
    "terraform": ["terraform", "infrastructure as code", "iac"],
    "ansible": ["ansible"],
    "shell scripting": ["shell scripting", "bash", "shell script", "bash scripting"],
    "monitoring": ["monitoring", "prometheus", "grafana", "nagios", "datadog"],
    # Data
    "excel": ["excel", "ms excel", "microsoft excel", "advanced excel", "vlookup", "pivot tables"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "power bi": ["power bi", "powerbi"],
    "tableau": ["tableau"],
    "statistics": ["statistics", "statistical analysis", "hypothesis testing", "regression analysis"],
    "data visualization": ["data visualization", "data visualisation", "dashboards", "dashboard"],
    "machine learning": ["machine learning", "ml", "scikit-learn", "sklearn"],
    # QA
    "selenium": ["selenium", "selenium webdriver", "webdriver"],
    "manual testing": ["manual testing", "functional testing", "regression testing", "test cases"],
    "automation testing": ["automation testing", "test automation", "automated testing"],
    "jira": ["jira", "bug tracking", "defect tracking"],
    "api testing": ["api testing", "postman", "rest assured"],
    "pytest": ["pytest", "unittest", "testng", "junit"],
    "agile": ["agile", "scrum", "sprint", "kanban"],
    # HR
    "recruitment": ["recruitment", "talent acquisition", "recruiting", "sourcing", "end-to-end recruitment"],
    "onboarding": ["onboarding", "induction", "joining formalities"],
    "payroll": ["payroll", "payroll processing", "salary processing"],
    "employee engagement": ["employee engagement", "employee relations", "engagement activities"],
    "hrms": ["hrms", "hris", "workday", "successfactors", "zoho people"],
    "labour law": ["labour law", "labor law", "statutory compliance", "pf", "esic"],
    "performance management": ["performance management", "appraisals", "performance appraisal", "kra", "kpi setting"],
    # Digital marketing
    "seo": ["seo", "search engine optimization", "search engine optimisation"],
    "sem": ["sem", "google ads", "adwords", "ppc", "pay per click"],
    "social media marketing": ["social media marketing", "smm", "social media", "instagram marketing",
                               "facebook ads", "meta ads", "linkedin marketing"],
    "content marketing": ["content marketing", "content writing", "copywriting", "blogging"],
    "google analytics": ["google analytics", "ga4", "web analytics"],
    "email marketing": ["email marketing", "mailchimp", "email campaigns"],
    # General
    "communication": ["communication", "communication skills", "verbal communication", "written communication"],
}

# Reverse index: synonym -> canonical skill. Longer synonyms first so that
# "django rest framework" is preferred over "rest" when reading the output.
SYNONYM_TO_SKILL = {
    syn.lower(): canon
    for canon, syns in SKILL_TAXONOMY.items()
    for syn in sorted(syns, key=len, reverse=True)
}
