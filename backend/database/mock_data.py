import random
import hashlib
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
from database.connection import get_db, to_oid

try:
    from faker import Faker
    fake = Faker('en_IN')
except ImportError:
    fake = None

db = get_db()

# ===== FIXED TEST USERS =====
FIXED_STUDENTS = [
    {
        "_id": "STU001", "email": "student1@nm.tn.gov.in", "password": "student123", "name": "Ashwin Kumar T", "role": "student", 
        "college": "Anna University, Chennai", "college_tier": 1, "branch": "CSE", "nm_id": "NM2024001", "skills": ["Python", "Machine Learning", "SQL", "Pandas"], 
        "wallet_balance": 0, "total_earned": 0, "completed_tasks": 8, "gender": "Male", "district": "Chennai",
        "graduation_year": 2025, "college_email": "ashwin@annauniv.edu", "degree": "B.E", "alumni_mode": False
    },
    {
        "_id": "STU002", "email": "student2@nm.tn.gov.in", "password": "student123", "name": "Priya Dharshini R", "role": "student", 
        "college": "PSG College of Technology", "college_tier": 2, "branch": "AI&DS", "nm_id": "NM2024002", "skills": ["React", "JavaScript", "CSS", "Node.js"], 
        "wallet_balance": 0, "total_earned": 0, "completed_tasks": 5, "gender": "Female", "district": "Coimbatore",
        "graduation_year": 2024, "college_email": "priya@psgtech.edu", "degree": "B.Tech", "alumni_mode": False
    },
    {
        "_id": "STU003", "email": "student3@nm.tn.gov.in", "password": "student123", "name": "Karthik Selvan M", "role": "student", 
        "college": "Thiagarajar College of Engineering", "college_tier": 2, "branch": "IT", "nm_id": "NM2024003", "skills": ["Java", "Spring Boot", "MySQL", "Docker"], 
        "wallet_balance": 0, "total_earned": 0, "completed_tasks": 3, "gender": "Male", "district": "Madurai",
        "graduation_year": 2022, "college_email": "karthik@tce.edu", "degree": "B.E", "alumni_mode": False # Just on the edge
    },
]

FIXED_COMPANIES = [
    {"_id": "COMP001", "email": "techcorp@company.com", "password": "company123", "name": "TechCorp Solutions", "role": "company", "type": "Corporate", "csr_balance": 245000, "reserved_amount": 68500, "trust_score": 4.7, "tasks_posted": 24, "hired_count": 18, "industry_domain": "Technology", "logo_url": "../assets/tn-logo.png"},
    {"_id": "COMP002", "email": "startup@company.com", "password": "company123", "name": "StartupX Labs", "role": "company", "type": "Startup", "csr_balance": 78000, "reserved_amount": 12000, "trust_score": 4.9, "tasks_posted": 8, "hired_count": 12, "industry_domain": "Software", "logo_url": "../assets/tn-logo.png"},
    {"_id": "COMP003", "email": "bigcorp@company.com", "password": "company123", "name": "InnovateBig Corp", "role": "company", "type": "Corporate", "csr_balance": 520000, "reserved_amount": 156000, "trust_score": 4.5, "tasks_posted": 18, "hired_count": 22, "industry_domain": "Manufacturing", "logo_url": "../assets/tn-logo.png"},
]

FIXED_GOVERNMENT = [
    {"_id": "GOV001", "email": "admin@tn.gov.in", "password": "admin123", "name": "TN Admin - Rajesh Babu", "role": "government", "department": "Labour & Employment"},
]

FIXED_MENTORS = [
    {"_id": "MENT001", "email": "mentor1@techcorp.com", "password": "mentor123", "name": "Dr. Ramesh S", "role": "mentor", "domain": "Full Stack Dev", "experience_years": 12, "verified_company_email": True, "wallet_balance": 5500, "hours_mentored": 48},
    {"_id": "MENT002", "email": "mentor2@startupx.com", "password": "mentor123", "name": "Ananya Krishnan", "role": "mentor", "domain": "AI/Machine Learning", "experience_years": 8, "verified_company_email": True, "wallet_balance": 3200, "hours_mentored": 22},
]

TN_DISTRICTS = ["Chennai","Coimbatore","Madurai","Trichy","Salem","Tirunelveli","Vellore","Erode","Thanjavur","Tiruppur","Kanchipuram","Cuddalore","Nagapattinam","Dindigul","Ramanathapuram","Thoothukudi","Sivaganga","Pudukkottai","Perambalur","Ariyalur","Krishnagiri","Dharmapuri","Namakkal","Nilgiris","Karur","Virudhunagar","Theni","Villupuram","Kallakurichi","Ranipet","Chengalpattu","Tenkasi","Tirupattur"]

COLLEGES_BY_TIER = {
    1: ["Anna University Chennai", "VIT Vellore", "NIT Trichy", "SASTRA University", "SRM Institute"],
    2: ["PSG College of Technology", "Thiagarajar College", "Coimbatore Institute of Technology", "Kumaraguru College", "SSN College"],
    3: ["Dhanalakshmi College", "Karpaga Vinayaga College", "Prist University", "Vel Tech University", "Krishnamurthy College"],
}

SKILLS_POOL = ["Python", "JavaScript", "React", "Node.js", "Java", "C++", "Machine Learning", "Data Science", "SQL", "MongoDB", "AWS", "Docker", "Kubernetes", "Flutter", "Android", "iOS", "Figma", "UI/UX", "TensorFlow", "PyTorch", "NLP", "Computer Vision", "FastAPI", "Django", "Spring Boot"]

TASK_TEMPLATES = [
    {"title": "Python Data Pipeline Developer", "domain": "Data Science", "skills": ["Python", "SQL", "Pandas"], "difficulty": "Medium"},
    {"title": "React Frontend Component Library", "domain": "Web Dev", "skills": ["React", "JavaScript", "CSS"], "difficulty": "Easy"},
    {"title": "ML Model for Sentiment Analysis", "domain": "AI/ML", "skills": ["Python", "NLP", "TensorFlow"], "difficulty": "Hard"},
    {"title": "REST API with FastAPI", "domain": "Web Dev", "skills": ["Python", "FastAPI", "MongoDB"], "difficulty": "Medium"},
    {"title": "Computer Vision Object Detection", "domain": "AI/ML", "skills": ["Python", "OpenCV", "PyTorch"], "difficulty": "Hard"},
    {"title": "Flutter Mobile App Development", "domain": "Mobile", "skills": ["Flutter", "Dart", "Firebase"], "difficulty": "Medium"},
    {"title": "Interactive Dashboard Design", "domain": "Design", "skills": ["Figma", "CSS", "JavaScript"], "difficulty": "Easy"},
    {"title": "AWS Infrastructure with Terraform", "domain": "Data Science", "skills": ["AWS", "Docker", "CI/CD"], "difficulty": "Hard"},
    {"title": "Node.js Microservices Architecture", "domain": "Web Dev", "skills": ["Node.js", "MongoDB", "Docker"], "difficulty": "Hard"},
    {"title": "Data Visualization Dashboard", "domain": "Data Science", "skills": ["Python", "D3.js", "SQL"], "difficulty": "Medium"},
]


def generate_students(count: int = 50) -> List[Dict]:
    students = list(FIXED_STUDENTS)
    for i in range(4, count + 1):
        tier = random.choice([1, 1, 2, 2, 2, 3, 3])
        college = random.choice(COLLEGES_BY_TIER[tier])
        district = random.choice(TN_DISTRICTS)
        name_parts = ["Arun", "Priya", "Karthik", "Deepika", "Naveen", "Sowmiya", "Murugan", "Ananya", "Ravi", "Santhiya"]
        last_names = ["Kumar", "Selvan", "Dharshini", "Raj", "Krishnan", "Murugesan", "Pandian", "Subramaniam", "Venkatesh", "Balasubramanian"]
        name = f"{random.choice(name_parts)} {random.choice(last_names)}"
        grad_year = random.choice([2023, 2024, 2025, 2026])
        alumni_mode = datetime.now().year > grad_year + 2
        students.append({
            "_id": f"STU{str(i).zfill(3)}",
            "email": f"student{i}@nm.tn.gov.in",
            "password": "student123",
            "name": name,
            "role": "student",
            "college": college,
            "college_tier": tier,
            "college_email": f"stu{i}@college.edu",
            "graduation_year": grad_year,
            "alumni_mode": alumni_mode,
            "degree": random.choice(["B.E", "B.Tech", "M.E", "MCA"]),
            "branch": random.choice(["CSE", "IT", "ECE", "AI&DS", "Mech"]),
            "nm_id": f"NM2024{str(i).zfill(3)}",
            "skills": random.sample(SKILLS_POOL, random.randint(3, 7)),
            "wallet_balance": 0,
            "total_earned": 0,
            "completed_tasks": random.randint(0, 20),
            "gender": random.choice(["Male", "Female", "Male", "Female", "Other"]),
            "district": district,
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 180))).isoformat(),
        })
    return students


def generate_companies(count: int = 15) -> List[Dict]:
    companies = list(FIXED_COMPANIES)
    extra_names = ["CodeCraft Tech", "DataViz Inc", "AILabs TN", "MobileFirst Co", "CloudNative TN", "DevOps Masters", "FullStack Pro", "DataMind Analytics", "InnoTech Chennai", "StartupHub TN", "TechMinds India", "CodeBase Solutions"]
    for i, cname in enumerate(extra_names[:count-3], 4):
        ctype = random.choice(["Corporate", "Corporate", "Startup"])
        companies.append({
            "_id": f"COMP{str(i).zfill(3)}",
            "email": f"company{i}@company.com",
            "password": "company123",
            "name": cname,
            "role": "company",
            "type": ctype,
            "csr_balance": random.randint(50000, 500000),
            "reserved_amount": random.randint(10000, 100000),
            "trust_score": round(random.uniform(3.5, 5.0), 1),
            "hired_count": random.randint(0, 25),
            "industry_domain": random.choice(["Technology", "Software", "AI", "Cloud"]),
            "logo_url": "../assets/tn-logo.png",
            "created_at": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat(),
        })
    return companies

def generate_tasks(companies: List[Dict], count: int = 30) -> List[Dict]:
    tasks = []
    for i in range(count):
        company = random.choice(companies)
        template = TASK_TEMPLATES[i % len(TASK_TEMPLATES)]
        deadline = datetime.now() + timedelta(days=random.randint(1, 30))
        reward = random.choice([200, 300, 400, 500, 600, 700, 800, 900, 1000])
        max_participants = random.randint(10, 50)
        tasks.append({
            "_id": to_oid(f"507f1f77bcf86cd799439{str(i+1).zfill(3)}"),
            "company_id": str(company["_id"]),
            "company_name": company["name"],
            "company_type": company["type"],
            "title": template["title"],
            "description": f"Complete a {template['difficulty'].lower()}-level {template['domain']} task demonstrating proficiency in {', '.join(template['skills'])}. Deliverables include working code, documentation, and tests.",
            "skills_required": template["skills"],
            "difficulty": template["difficulty"],
            "domain": template["domain"],
            "reward_per_candidate": reward,
            "internship_stipend": random.choice([8000, 10000, 12000, 15000, 18000, 20000, 22000, 25000]),
            "max_participants": max_participants,
            "current_submissions": random.randint(0, max_participants),
            "deadline": deadline.isoformat(),
            "status": "active",
            "eligibility_criteria": {
                "required_experience": random.choice(["0-1 years", "1-2 years", "0-2 years"]),
                "min_skill_score": random.choice([60, 70, 75, 80]),
                "grad_year_range": [2022, 2026]
            },
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 14))).isoformat(),
        })
    return tasks

def generate_submissions(students: List[Dict], tasks: List[Dict], count: int = 200) -> List[Dict]:
    submissions = []
    for i in range(count):
        student = random.choice(students)
        task = random.choice(tasks)
        tech = random.randint(60, 98)
        orig = random.randint(85, 100)
        resume = random.randint(65, 95)
        combined = round(tech * 0.5 + orig * 0.3 + resume * 0.2)
        status = random.choice(["evaluated", "evaluated", "evaluated", "pending", "selected", "rejected"])
        submissions.append({
            "student_id": str(student["_id"]),
            "student_name": student["name"],
            "task_id": str(task["_id"]),
            "task_title": task["title"],
            "company_id": str(task["company_id"]),
            "code": "# Student submission\ndef solution():\n    pass",
            "language": random.choice(["Python", "JavaScript", "Java", "C++"]),
            "ai_evaluation": {
                "overall_score": tech,
                "plagiarism_risk": 100 - orig,
                "skills_match": resume,
                "combined_score": combined,
                "hiring_recommendation": "Strong Recommend" if combined >= 85 else "Consider" if combined >= 70 else "Do Not Hire",
                "extracted_skills": random.sample(task["skills_required"], min(len(task["skills_required"]), 3))
            },
            "reward_amount": task["reward_per_candidate"],
            "reward_status": "paid" if status in ["evaluated", "selected", "rejected"] else "pending",
            "status": status,
            "submitted_at": (datetime.now() - timedelta(days=random.randint(0, 14))).isoformat(),
            "evaluated_at": (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat() if status != "pending" else None,
        })
    return submissions

def generate_transactions(students: List[Dict], companies: List[Dict], count: int = 200) -> List[Dict]:
    transactions = []
    base_time = datetime.now() - timedelta(days=30)
    for i in range(count):
        student = random.choice(students)
        company = random.choice(companies)
        t_time = base_time + timedelta(minutes=i*180)
        
        tx_type = random.choice(["reward_payment", "deposit", "escrow_lock", "withdrawal"])
        
        txn = {
            "timestamp": t_time.isoformat(),
            "type": tx_type,
            "status": "completed",
            "verified": True,
            "task_id": f"TASK_{random.randint(100, 999)}"
        }

        if tx_type == "deposit":
            txn.update({
                "company_id": str(company["_id"]),
                "amount": random.randint(50000, 200000),
                "from_entity": {"type": "government", "id": "GOV001", "name": "TN Govt"},
                "to_entity": {"type": "company", "id": str(company["_id"]), "name": company["name"]}
            })
        elif tx_type == "escrow_lock":
            txn.update({
                "company_id": str(company["_id"]),
                "amount": -random.randint(5000, 20000),
                "from_entity": {"type": "company", "id": str(company["_id"]), "name": company["name"]},
                "to_entity": {"type": "escrow", "id": "ESCROW", "name": "Task Escrow"}
            })
        elif tx_type == "reward_payment":
            amt = random.randint(500, 5000)
            txn.update({
                "company_id": str(company["_id"]),
                "student_id": str(student["_id"]),
                "amount": amt,
                "from_entity": {"type": "company", "id": str(company["_id"]), "name": company["name"]},
                "to_entity": {"type": "student", "id": str(student["_id"]), "name": student["name"]}
            })
        elif tx_type == "withdrawal":
            txn.update({
                "student_id": str(student["_id"]),
                "amount": -random.randint(200, 1000),
                "from_entity": {"type": "student", "id": str(student["_id"]), "name": student["name"]},
                "to_entity": {"type": "bank", "id": "BANK", "name": "Personal Bank Account"}
            })
        
        transactions.append(txn)
    return transactions

def generate_questions() -> List[Dict]:
    domains = ["Machine Learning", "Web Development", "Python Programming", "Data Engineering"]
    questions = []
    for dom in domains:
        for i in range(30):
            questions.append({
                "domain": dom,
                "text": f"Verified {dom} Question: Which of the following is essential for {dom} scalability?",
                "options": ["Option A: Caching", "Option B: Redundancy", "Option C: Load Balancing", "Option D: All of above"],
                "correct": "Option D: All of above"
            })
    return questions

def generate_mentorship_data(students, mentors):
    requests = []
    mentorships = []
    messages = []
    for i in range(10):
        student = students[i]
        mentor = random.choice(mentors)
        status = random.choice(["pending", "accepted", "rejected"])
        req = {
            "student_id": student["_id"],
            "mentor_id": mentor["_id"],
            "status": status,
            "timestamp": (datetime.now() - timedelta(days=random.randint(1, 10))).isoformat()
        }
        requests.append(req)
        if status == "accepted":
            mentorships.append({
                "mentor_id": mentor["_id"],
                "student_id": student["_id"],
                "assigned_at": req["timestamp"]
            })
            for j in range(3):
                messages.append({
                    "sender_id": student["_id"] if j%2==0 else mentor["_id"],
                    "receiver_id": mentor["_id"] if j%2==0 else student["_id"],
                    "content": f"Hello! This is sample message {j+1}",
                    "timestamp": datetime.now().isoformat()
                })
    return requests, mentorships, messages

def generate_mentor_assignments(students, mentors, tasks):
    assignments = []
    for i in range(10):
        student = random.choice(students)
        mentor = random.choice(mentors)
        task = random.choice(tasks)
        assignments.append({
            "student_id": student["_id"],
            "mentor_id": mentor["_id"],
            "task_id": task["_id"],
            "created_at": datetime.now().isoformat()
        })
    return assignments

async def seed_db():
    print("Cleaning collections...")
    for coll in ["students", "companies", "government", "mentors", "tasks", "submissions", "transactions", "analytics", "question_bank", "mentorship_requests", "mentorships", "messages", "mentor_assignments", "mentor_feedback"]:
        await db[coll].delete_many({})

    print("Generating data...")
    students = generate_students(50)
    companies = generate_companies(15)
    government = list(FIXED_GOVERNMENT)
    mentors = list(FIXED_MENTORS)
    tasks = generate_tasks(companies, 30)
    submissions = generate_submissions(students, tasks, 100)
    transactions = generate_transactions(students, companies, 300)
    mentorship_requests, mentorships, messages = generate_mentorship_data(students, mentors)
    mentor_assignments = generate_mentor_assignments(students, mentors, tasks)
    
    # Force some data for student1
    s1 = students[0]
    c1 = companies[0]
    for _ in range(5):
        transactions.append({
            "timestamp": (datetime.now() - timedelta(days=random.randint(1, 15))).isoformat(),
            "type": "reward_payment",
            "company_id": str(c1["_id"]),
            "student_id": str(s1["_id"]),
            "amount": random.randint(1000, 5000),
            "from_entity": {"type": "company", "id": str(c1["_id"]), "name": c1["name"]},
            "to_entity": {"type": "student", "id": str(s1["_id"]), "name": s1["name"]},
            "status": "completed",
            "verified": True,
            "task_id": f"TASK_{random.randint(100, 999)}"
        })
    transactions.append({
        "timestamp": datetime.now().isoformat(),
        "type": "withdrawal",
        "student_id": str(s1["_id"]),
        "amount": -500,
        "from_entity": {"type": "student", "id": str(s1["_id"]), "name": s1["name"]},
        "to_entity": {"type": "bank", "id": "BANK", "name": "Personal Bank Account"},
        "status": "completed",
        "verified": True,
        "task_id": "WITHDRAW_001"
    })
    questions = generate_questions()

    print("Seeding database...")
    if students: 
        # Apply transactions to student balances for realism
        for t in transactions:
            if t["type"] == "reward_payment":
                for s in students:
                    if str(s["_id"]) == t.get("student_id"):
                        s["wallet_balance"] += t["amount"]
                        s["total_earned"] += t["amount"]
            elif t["type"] == "withdrawal":
                for s in students:
                    if str(s["_id"]) == t.get("student_id"):
                        amt = abs(t["amount"])
                        # Only withdraw if they have balance
                        if s["wallet_balance"] >= amt:
                            s["wallet_balance"] -= amt
                        else:
                            # Adjust transaction if balance too low
                            t["amount"] = -s["wallet_balance"]
                            s["wallet_balance"] = 0
        await db["students"].insert_many(students)
    
    if companies:
        # Also update company balances for logic
        for t in transactions:
            if t.get("company_id"):
                for c in companies:
                    if str(c["_id"]) == t["company_id"]:
                        if t["type"] == "deposit":
                            c["csr_balance"] = c.get("csr_balance", 0) + t["amount"]
                        elif t["type"] == "escrow_lock":
                            amt = abs(t["amount"])
                            c["csr_balance"] = c.get("csr_balance", 0) - amt
                            c["reserved_amount"] = c.get("reserved_amount", 0) + amt
                        elif t["type"] == "reward_payment":
                            # Reward payment usually comes out of reserved amount
                            amt = t["amount"]
                            c["reserved_amount"] = max(0, c.get("reserved_amount", 0) - amt)
        await db["companies"].insert_many(companies)
    if government: await db["government"].insert_many(government)
    if mentors: await db["mentors"].insert_many(mentors)
    if tasks: await db["tasks"].insert_many(tasks)
    if submissions: await db["submissions"].insert_many(submissions)
    if transactions: await db["transactions"].insert_many(transactions)
    if questions: await db["question_bank"].insert_many(questions)
    if mentorship_requests: await db["mentorship_requests"].insert_many(mentorship_requests)
    if mentorships: await db["mentorships"].insert_many(mentorships)
    if messages: await db["messages"].insert_many(messages)
    if mentor_assignments: await db["mentor_assignments"].insert_many(mentor_assignments)

    print("Database Seeding Complete!")

if __name__ == "__main__":
    asyncio.run(seed_db())
