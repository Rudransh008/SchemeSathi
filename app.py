import os, json, sqlite3, re
from datetime import datetime
from flask import Flask, render_template, request, jsonify, g
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")
DB_PATH = "/tmp/schemesathi.db" if os.getenv("VERCEL") else os.path.join(app.root_path, "schemesathi.db")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()

SCHEMES = [
    {
        "name": "Post-Matric Scholarship (illustrative record)",
        "category": "Education", "state": "Madhya Pradesh",
        "summary": "A scholarship category that may support eligible students pursuing post-matric education.",
        "benefits": "Benefits and amounts depend on the applicable scheme, student category, course and current rules.",
        "min_age": None, "max_age": None, "max_income": 250000,
        "occupations": ["Student"], "education": ["Undergraduate", "BTech", "Postgraduate"],
        "documents": ["Current academic marksheet", "Admission or bonafide certificate", "Income certificate", "Category certificate if applicable", "Bank details as requested by the official portal"],
        "steps": ["Check the current state scholarship guidelines.", "Confirm category, income and course conditions.", "Apply through the official state portal if eligible."],
        "url": "https://scholarships.gov.in/",
        "source": "National Scholarship Portal (starting point; verify scheme-specific rules)",
        "verified": "Demo seed — not independently verified"
    },
    {
        "name": "PM-KISAN (illustrative information record)",
        "category": "Agriculture", "state": "All India",
        "summary": "A central-sector income-support scheme for eligible landholding farmer families, subject to exclusions and official rules.",
        "benefits": "The scheme provides income support as defined by current official guidelines.",
        "min_age": None, "max_age": None, "max_income": None,
        "occupations": ["Farmer"], "education": [],
        "documents": ["Landholding records", "Identity and bank details as required by the official process"],
        "steps": ["Review current eligibility and exclusion criteria.", "Check land records and required details.", "Use the official PM-KISAN portal for registration or status."],
        "url": "https://pmkisan.gov.in/",
        "source": "PM-KISAN official portal",
        "verified": "Demo seed — verify current rules"
    },
    {
        "name": "National Social Assistance Programme (NSAP) (illustrative record)",
        "category": "Senior Citizens", "state": "All India",
        "summary": "A programme that includes social assistance pensions for eligible people, with criteria and implementation varying by component and state.",
        "benefits": "Pension assistance as specified by the applicable programme component and state rules.",
        "min_age": 60, "max_age": None, "max_income": None,
        "occupations": ["Any"], "education": [],
        "documents": ["Age proof", "Residence proof", "Income or BPL-related documents as required", "Bank account details as requested"],
        "steps": ["Identify the applicable pension component.", "Check central and state eligibility conditions.", "Apply through the relevant state or local authority."],
        "url": "https://nsap.nic.in/",
        "source": "NSAP official portal",
        "verified": "Demo seed — verify current rules"
    },
    {
        "name": "Stand-Up India (illustrative information record)",
        "category": "Business", "state": "All India",
        "summary": "A scheme facilitating bank loans for eligible SC/ST and women entrepreneurs for greenfield enterprises, subject to current guidelines.",
        "benefits": "Bank credit support under applicable scheme conditions; this is not a guaranteed grant.",
        "min_age": 18, "max_age": None, "max_income": None,
        "occupations": ["Business Owner", "Entrepreneur"], "education": [],
        "documents": ["Identity and address proof", "Business plan", "Relevant category or ownership documents", "Bank-required documents"],
        "steps": ["Review current eligibility and loan conditions.", "Prepare a business plan.", "Contact a participating bank or official portal."],
        "url": "https://www.standupmitra.in/",
        "source": "Stand-Up India official portal",
        "verified": "Demo seed — verify current rules"
    },
    {
        "name": "Ayushman Bharat PM-JAY (illustrative information record)",
        "category": "Healthcare", "state": "All India",
        "summary": "A publicly funded health assurance programme for eligible beneficiary families, based on official beneficiary criteria.",
        "benefits": "Health coverage as defined under current PM-JAY guidelines and state implementation.",
        "min_age": None, "max_age": None, "max_income": None,
        "occupations": ["Any"], "education": [],
        "documents": ["Beneficiary identification details as required by the official system"],
        "steps": ["Check beneficiary status using the official portal or helpline.", "Confirm state-specific implementation.", "Follow the official process for eligible beneficiaries."],
        "url": "https://pmjay.gov.in/",
        "source": "Ayushman Bharat PM-JAY official portal",
        "verified": "Demo seed — verify current rules"
    }
]

def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("""CREATE TABLE IF NOT EXISTS schemes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE, category TEXT, state TEXT, summary TEXT, benefits TEXT,
        min_age INTEGER, max_age INTEGER, max_income REAL, occupations TEXT,
        education TEXT, documents TEXT, steps TEXT, url TEXT, source TEXT, verified TEXT
    )""")
    count = db.execute("SELECT COUNT(*) FROM schemes").fetchone()[0]
    if count == 0:
        for s in SCHEMES:
            db.execute("""INSERT INTO schemes
            (name,category,state,summary,benefits,min_age,max_age,max_income,occupations,education,documents,steps,url,source,verified)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (s["name"],s["category"],s["state"],s["summary"],s["benefits"],s["min_age"],s["max_age"],s["max_income"],
             json.dumps(s["occupations"]),json.dumps(s["education"]),json.dumps(s["documents"]),json.dumps(s["steps"]),
             s["url"],s["source"],s["verified"]))
    db.commit()
    db.close()

def serialize(row):
    d = dict(row)
    for key in ("occupations","education","documents","steps"):
        d[key] = json.loads(d[key] or "[]")
    return d

def eligibility(user, scheme):
    checks = []
    if scheme["min_age"] is not None:
        if user.get("age") is None: checks.append(("Age requirement", "unknown", f"Minimum age is {scheme['min_age']}."))
        elif user["age"] < scheme["min_age"]: checks.append(("Age requirement", "fail", f"Applicant is below the minimum age of {scheme['min_age']}."))
        else: checks.append(("Age requirement", "pass", f"Applicant meets the minimum age of {scheme['min_age']}."))
    if scheme["max_age"] is not None:
        if user.get("age") is None: checks.append(("Age limit", "unknown", f"Maximum age is {scheme['max_age']}."))
        elif user["age"] > scheme["max_age"]: checks.append(("Age limit", "fail", f"Applicant exceeds the maximum age of {scheme['max_age']}."))
        else: checks.append(("Age limit", "pass", "Applicant is within the age limit."))
    if scheme["max_income"] is not None:
        if user.get("income") is None: checks.append(("Income limit", "unknown", f"Annual income limit in this demo record is ₹{scheme['max_income']:,.0f}."))
        elif user["income"] > scheme["max_income"]: checks.append(("Income limit", "fail", f"Income exceeds the demo limit of ₹{scheme['max_income']:,.0f}."))
        else: checks.append(("Income limit", "pass", f"Income is within the demo limit of ₹{scheme['max_income']:,.0f}."))
    occs = scheme["occupations"]
    if occs and "Any" not in occs:
        if not user.get("occupation"): checks.append(("Occupation", "unknown", "Occupation information is required."))
        elif user["occupation"] not in occs: checks.append(("Occupation", "fail", f"This record is intended for: {', '.join(occs)}."))
        else: checks.append(("Occupation", "pass", "Occupation matches this record."))
    states = scheme["state"]
    if states and states != "All India":
        if not user.get("state"): checks.append(("State", "unknown", f"This record is listed for {states}."))
        elif user["state"].lower() != states.lower(): checks.append(("State", "fail", f"This record is listed for {states}."))
        else: checks.append(("State", "pass", "State matches this record."))
    fails = any(x[1] == "fail" for x in checks)
    unknown = any(x[1] == "unknown" for x in checks)
    status = "Does not match" if fails else ("More information required" if unknown else "Potential match")
    return {"status": status, "checks": [{"condition":a,"result":b,"explanation":c} for a,b,c in checks]}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/schemes")
def list_schemes():
    rows = get_db().execute("SELECT * FROM schemes ORDER BY category, name").fetchall()
    return jsonify([serialize(r) for r in rows])

@app.route("/api/recommend", methods=["POST"])
def recommend():
    data = request.get_json(force=True)
    try:
        user = {
            "age": int(data["age"]) if str(data.get("age","")).strip() else None,
            "income": float(data["income"]) if str(data.get("income","")).strip() else None,
            "state": data.get("state","").strip(),
            "occupation": data.get("occupation","").strip(),
            "education": data.get("education","").strip()
        }
    except (ValueError, TypeError):
        return jsonify({"error":"Please enter valid age and annual income values."}), 400
    rows = get_db().execute("SELECT * FROM schemes").fetchall()
    results = []
    for row in rows:
        s = serialize(row)
        result = eligibility(user, s)
        if result["status"] != "Does not match":
            results.append({"scheme":s, "eligibility":result})
    return jsonify({"results":results, "note":"Demo dataset only. Confirm every condition on the official scheme portal; this is not an official eligibility decision."})

def retrieve_context(question):
    rows = get_db().execute("SELECT * FROM schemes").fetchall()
    terms = set(re.findall(r"[a-zA-Z]{3,}", question.lower()))
    scored = []
    for row in rows:
        s = serialize(row)
        haystack = " ".join([s["name"],s["category"],s["summary"],s["benefits"],s["state"]," ".join(s["documents"])]).lower()
        score = sum(1 for t in terms if t in haystack)
        if score:
            scored.append((score,s))
    scored.sort(key=lambda x:x[0], reverse=True)
    return [s for _,s in scored[:4]] or [serialize(r) for r in rows[:3]]

def gemini_answer(question, language, context):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        context_text = json.dumps(context, ensure_ascii=False, indent=2)
        prompt = f"""You are SchemeSathi, an Indian government scheme information assistant.
Answer in {language}. Use ONLY the supplied scheme records. Do not invent eligibility criteria, benefits, deadlines, documents or links. If the records do not answer the question, say so and direct the user to the official source. Explain that this is guidance, not an official approval.
User question: {question}
Retrieved scheme records:
{context_text}
Give a concise helpful answer with scheme name, relevant facts, caveats and official URL."""
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except Exception as e:
        app.logger.exception("Gemini request failed")
        return None

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    question = (data.get("message") or "").strip()
    language = data.get("language") or "English"
    if not question:
        return jsonify({"error":"Please enter a question."}), 400
    context = retrieve_context(question)
    answer = gemini_answer(question, language, context)
    if not answer:
        # Honest fallback: deterministic answer from retrieved records, not a fake AI response.
        parts = ["I’m currently in demo mode because the Gemini API is not configured or could not be reached."]
        for s in context[:3]:
            parts.append(f"**{s['name']}** ({s['category']}) — {s['summary']} Official source: {s['url']}")
        parts.append("For an accurate decision, check the current official rules and application portal.")
        answer = "\n\n".join(parts)
    return jsonify({"answer":answer, "sources":[{"name":s["name"],"url":s["url"],"verified":s["verified"]} for s in context]})

@app.route("/api/admin/schemes", methods=["POST"])
def add_scheme():
    # Basic local-demo admin endpoint. Add authentication before public deployment.
    data = request.get_json(force=True)
    required = ["name","category","summary","url","source"]
    if any(not data.get(k) for k in required):
        return jsonify({"error":"Name, category, summary, official URL and source are required."}), 400
    try:
        get_db().execute("""INSERT INTO schemes
        (name,category,state,summary,benefits,min_age,max_age,max_income,occupations,education,documents,steps,url,source,verified)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (data["name"],data["category"],data.get("state","All India"),data["summary"],data.get("benefits",""),
         data.get("min_age"),data.get("max_age"),data.get("max_income"),json.dumps(data.get("occupations",[])),
         json.dumps(data.get("education",[])),json.dumps(data.get("documents",[])),json.dumps(data.get("steps",[])),
         data["url"],data["source"],data.get("verified","Needs verification")))
        get_db().commit()
        return jsonify({"message":"Scheme added. Verify its rules before publishing recommendations."}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error":"A scheme with this name already exists."}), 409

init_db()

if __name__ == "__main__":
    app.run(debug=True)
