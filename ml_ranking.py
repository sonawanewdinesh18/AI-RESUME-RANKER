# === FINAL & IMPROVED Resume Ranking Code ===
import re
from collections import Counter
from sentence_transformers import SentenceTransformer, util
from database import fetch_applications_by_job

# Load enhanced BERT model
bert_model = SentenceTransformer("all-mpnet-base-v2")

# Education Levels
EDUCATION_LEVELS = {
    "phd": 5, "mtech": 4, "msc": 4, "ma": 4, "mca": 4,
    "btech": 3, "be": 3, "bsc": 3, "ba": 3, "bca": 3,
    "bachelor of technology": 3, "bachelor": 3,
    "diploma": 2, "high school": 1
}

# Skills Aliases
SKILL_ALIASES = {
    "python": ["py", "python3", "python programming", "python language"],
    "java": ["core java", "java programming"],
    "c++": ["cpp", "c plus plus"],
    "c": ["c programming", "basic c"],
    "javascript": ["js", "ecmascript", "vanilla js"],
    "html": ["html5", "web markup"],
    "css": ["css3", "style sheet"],
    "sql": ["mysql", "postgresql", "structured query language"],
    "php": ["php scripting"],
    "react": ["react.js", "reactjs"],
    "node": ["node.js", "nodejs"],
    "machine learning": ["ml", "ml algorithms"],
    "deep learning": ["dl", "cnn", "rnn"],
    "nlp": ["natural language processing"],
    "pandas": ["dataframes"],
    "numpy": ["numerical python"],
    "git": ["github", "gitlab"],
    "linux": ["ubuntu"],
    "communication": ["verbal skills"]
}

# Certification Aliases
CERTIFICATION_ALIASES = {
    "nptel python": ["joy of computing using python"],
    "problem solving in c": ["nptel c programming"],
    "google data analytics": ["google analytics"],
    "aws cloud practitioner": ["aws certified"]
}

def normalize_tokens(text):
    return re.findall(r'\w+', text.lower())

def expand_aliases(keywords, alias_map):
    expanded = set()
    for word in keywords:
        word = word.lower()
        expanded.add(word)
        expanded.update(alias_map.get(word, []))
    return expanded

def rule_based_score(app, filters):
    parsed = app.get("parsed_data", {})
    if not isinstance(parsed, dict):
        return 0, "Invalid parsed data"

    score = 0
    max_score = 0
    explanation = []

    tokens = normalize_tokens(parsed.get("text", ""))
    token_counts = Counter(tokens)

    # Skills
    req_skills = filters.get("required_skills", [])
    skills_expanded_map = {
        skill: expand_aliases([skill], SKILL_ALIASES)
        for skill in req_skills
    }
    for skill, variants in skills_expanded_map.items():
        freq = sum(token_counts.get(w, 0) for w in variants)
        if freq >= 3:
            score += 10
            explanation.append(f"\u2705 Skill '{skill}' used frequently ({freq}x) [+10]")
        elif freq == 2:
            score += 6
            explanation.append(f"\u2705 Skill '{skill}' moderately mentioned ({freq}x) [+6]")
        elif freq == 1:
            score += 3
            explanation.append(f"\u2705 Skill '{skill}' mentioned once [+3]")
        else:
            explanation.append(f"\u274C Skill '{skill}' not found [+0]")
        max_score += 10

    # Certifications
    req_certs = filters.get("certifications", [])
    certs_expanded = expand_aliases(req_certs, CERTIFICATION_ALIASES)
    found_certs = set([c.lower() for c in parsed.get("certifications", [])])
    matches = certs_expanded.intersection(found_certs)
    score += len(matches) * 5
    max_score += len(req_certs) * 5
    explanation.append(f"🎓 Certification matches: {len(matches)} [+{len(matches)*5}]")

    # Project Domains
    req_projects = set([p.lower() for p in filters.get("project_domains", [])])
    found_projects = set([p.lower() for p in parsed.get("project_domains", [])])
    matches = len(req_projects.intersection(found_projects))
    score += matches * 4
    max_score += len(req_projects) * 4
    explanation.append(f"🧪 Project domain matches: {matches} [+{matches * 4}]")

    # Education
    edu_level = filters.get("education", "").lower()
    edu_score = max([EDUCATION_LEVELS.get(e.lower(), 0) for e in parsed.get("education", [])], default=0)
    if edu_score >= EDUCATION_LEVELS.get(edu_level, 0):
        score += edu_score
    explanation.append(f"📘 Education match score: {edu_score}/5")
    max_score += 5

    # Experience
    try:
        exp = int(re.sub(r"[^0-9]", "", str(parsed.get("experience", "0"))))
    except:
        exp = 0

    explanation.append(f"📌 Candidate has {exp} year(s) experience")
    if exp >= filters.get("min_experience", 0):
        score += 5
        explanation.append(f"💼 Experience meets/exceeds required [+5]")
    else:
        explanation.append(f"⚠️ Experience below required [+0]")
    max_score += 5

    match_score = (score / max_score) * 100 if max_score else 0
    return match_score, "\n".join(explanation)

def rank_resumes(job_id, filters):
    applications = fetch_applications_by_job(job_id)
    if not applications:
        return []

    job_text = filters.get("job_description") or " ".join(
        filters.get("required_skills", []) +
        filters.get("certifications", []) +
        filters.get("project_domains", [])
    )
    job_embedding = bert_model.encode(job_text, convert_to_tensor=True)

    ranked = []
    for app in applications:
        parsed = app.get("parsed_data", {})
        resume_text = parsed.get("text", "")
        if not resume_text.strip():
            continue

        resume_embedding = bert_model.encode(resume_text, convert_to_tensor=True)
        semantic_sim = float(util.cos_sim(job_embedding, resume_embedding).item()) * 100

        rule_score, explanation = rule_based_score(app, filters)
        final_score = round(0.5 * rule_score + 0.5 * semantic_sim, 2)

        app["match_score"] = int(final_score)
        app["explanation"] = explanation + f"\n🧠 BERT Semantic Similarity to Job Description: {semantic_sim:.2f}%"
        ranked.append(app)

    ranked = sorted(ranked, key=lambda x: x["match_score"], reverse=True)
    return ranked[:int(filters.get("num_shortlist", 5))]
