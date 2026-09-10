"""Create a transparent 21-concept / 51-artifact DEMO dataset.

The supplied release ZIP does not contain the user's real 21 concepts or 51
artifact files, so this script creates only clearly-labelled placeholders.
Run: python seed_demo.py
"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib, sqlite3
BASE_DIR=Path(__file__).resolve().parent
DB_PATH=BASE_DIR/'project_dashboard.db'; UPLOAD_ROOT=BASE_DIR/'uploads'/'imported'
def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
from app import init_db
init_db(); conn=sqlite3.connect(DB_PATH); conn.execute('PRAGMA foreign_keys=ON')
for i in range(1,22):
    name=f'Demo Concept {i:02d}'
    if not conn.execute('SELECT 1 FROM projects WHERE lower(project_name)=lower(?)',(name,)).fetchone():
        conn.execute('''INSERT INTO projects(project_name,domain,provisional_patent_status,sensor,planned_organisation,status,eta,comments,total_spend,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',(name,'Demo / Placeholder','Not Filed','N','','Planned','—','Structural seed placeholder',0,now(),now()))
conn.commit(); projects=conn.execute('SELECT id FROM projects ORDER BY id LIMIT 21').fetchall()
for n in range(1,52):
    if conn.execute('SELECT 1 FROM artifacts WHERE name=? AND description=?', (f'demo/artifact_{n:02d}.txt','Structural demo placeholder artifact')).fetchone(): continue
    project_id=projects[(n-1)%21][0]; rel=f'demo/artifact_{n:02d}.txt'; payload=f'DEMO PLACEHOLDER ARTIFACT {n}\nStructural validation record only.\n'; digest=hashlib.sha256(payload.encode()).hexdigest(); dest=UPLOAD_ROOT/str(project_id)/rel; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_text(payload,encoding='utf-8')
    conn.execute('''INSERT INTO artifacts(project_id,name,description,file_path,original_path,file_size,sha256,created_at) VALUES (?,?,?,?,?,?,?,?)''',(project_id,rel,'Structural demo placeholder artifact',str(dest.relative_to(BASE_DIR)),rel,len(payload.encode()),digest,now()))
conn.commit(); print('DEMO DATA READY: 21 concepts / 51 artifacts'); conn.close()
