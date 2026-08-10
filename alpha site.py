"""
ЧОО АЛЬФА — Терминал v5.1 (Debug Mode)
+ Логотип фракции на всех страницах
+ Админ может закрывать смены
"""
from flask import Flask, render_template_string, request, redirect, session, send_from_directory
from datetime import datetime
import threading, json, os, requests, time
import pytz

TIMEZONE = pytz.timezone("Europe/Moscow")

app = Flask(__name__)
app.secret_key = "ALPHA_SECRET_KEY_123"

os.makedirs("static", exist_ok=True)

# ===== WEBHOOK =====
WEBHOOK = "https://discord.com/api/webhooks/1497300322706657383/FQD4rxra-mo31fnHaAKHYV-eOGl23f4PSC2X6c4ePfS3_flw384Ak1uoGMh98xaWHSuS"

def discord(title, desc="", color=0x00B4D8, ping=False, fields=None):
    embed = {
        "title": title, "description": desc, "color": color,
        "footer": {"text": "ЧОО «АЛЬФА» • v0.5"}
    }
    if fields: embed["fields"] = fields
    data = {"embeds": [embed]}
    if ping:
        data["content"] = "<@&1378126995447091274> 🚨АКТИВИРОВАНА КНОПКА ПАНИКИ🚨"
        embed["color"] = 0xFF0000
    try:
        r = requests.post(WEBHOOK, json=data, timeout=5)
        print(f"[Discord] {title} — {r.status_code}")
    except Exception as e:
        print(f"[Discord] Ошибка: {e}")

# ===== ЗАГРУЗКА ПОЛЬЗОВАТЕЛЕЙ =====
def load_users():
    print("\n" + "=" * 60)
    print("🔍 ДИАГНОСТИКА users.json")
    print("=" * 60)
    
    if not os.path.exists("users.json"):
        print("❌ Файл не найден!")
        return {"admin": {"password": "admin123", "full_name": "Администратор", "role": "admin"}}
    
    with open("users.json", "r", encoding="utf-8") as f:
        content = f.read()
    
    print("📄 Содержимое файла:")
    print(content[:200] + "..." if len(content) > 200 else content)
    
    try:
        users = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка JSON: {e}")
        return {"admin": {"password": "admin123", "full_name": "Администратор", "role": "admin"}}
    
    print(f"\n✅ Загружено пользователей: {len(users)}")
    for login, data in users.items():
        print(f"   • '{login}' — {data['full_name']} (пароль: {data['password'][:3]}***)")
    
    return users

USERS = load_users()
USERS_LOWER = {k.lower(): k for k in USERS}

# ===== ДАННЫЕ =====
DATA_FILE = "alpha_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"shift_counter": 100, "reports": [], "alarms": [], "shift_history": [], "active_shifts": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return {"shift_counter": 100, "reports": [], "alarms": [], "shift_history": [], "active_shifts": {}}
        d = json.loads(content)
    for u, s in d.get("active_shifts", {}).items():
        if isinstance(s.get("start_time"), str):
            try:
                s["start_time"] = datetime.strptime(s["start_time"], "%Y-%m-%d %H:%M:%S")
            except:
                s["start_time"] = datetime.now(TIMEZONE)
    return d

def save_data():
    asc = {}
    for u, s in st["active_shifts"].items():
        asc[u] = {
            "shift_id": s["shift_id"],
            "start_time": s["start_time"].strftime("%Y-%m-%d %H:%M:%S") if s["start_time"] else "",
            "elapsed_seconds": s["elapsed_seconds"]
        }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "shift_counter": st["shift_counter"],
            "reports": st["reports"],
            "alarms": st["alarms"],
            "shift_history": st["shift_history"],
            "active_shifts": asc
        }, f, ensure_ascii=False, indent=2)

sv = load_data()
st = {
    "shift_counter": sv["shift_counter"],
    "reports": sv["reports"],
    "alarms": sv["alarms"],
    "shift_history": sv["shift_history"],
    "alarm_active": False,
    "active_shifts": sv["active_shifts"]
}

# ===== ТАЙМЕР =====
def timer():
    last_tick = time.time()
    while True:
        now = time.time()
        elapsed = now - last_tick
        last_tick = now
        
        for s in st["active_shifts"].values():
            s["elapsed_seconds"] += elapsed
        
        time.sleep(0.1)

threading.Thread(target=timer, daemon=True).start()

def me():
    if "username" in session:
        orig_key = session["username"]
        if orig_key in USERS:
            return {"username": orig_key, **USERS[orig_key]}
    return None

# ===== CSS =====
CSS = """<style>
:root{--bg:#0A0C0F;--pn:#12161C;--bd:#1E2A36;--ac:#7F0000;--rd:#E63946;--gn:#2ECC71;--or:#F39C12;--tx:#C8CDD2;--mt:#7A8490}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--tx);font-family:Courier New,monospace;min-height:100vh;padding:20px;animation:fadeIn 0.3s ease}@keyframes fadeIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
body.alarm{animation:pulse 0.8s infinite}@keyframes pulse{0%,100%{background:#0A0000}50%{background:#1A0000}}
.card{background:var(--pn);border:1px solid var(--bd);border-radius:12px;padding:24px;margin-bottom:16px}
.logo{text-align:center;color:var(--ac);font-size:28px;font-weight:bold;letter-spacing:2px}
.logo-img{display:block;margin:0 auto 15px;max-width:120px;max-height:80px;object-fit:contain}
.sub{text-align:center;color:var(--mt);font-size:11px;letter-spacing:3px;text-transform:uppercase}
.btn{display:block;width:100%;padding:16px;font:inherit;font-size:16px;font-weight:bold;border:none;border-radius:10px;cursor:pointer;margin:10px 0;text-align:center;text-decoration:none;letter-spacing:1px;transition:.2s}
.btn:hover{transform:translateY(-1px)}
.btn-start{background:var(--gn);color:#fff}.btn-end{background:var(--rd);color:#fff}
.btn-alarm{background:#8B0000;color:#fff;font-size:20px;padding:20px;border:2px solid #F44}
.btn-alarm.active{animation:ap 0.5s infinite;background:red}@keyframes ap{0%,100%{box-shadow:0 0 15px rgba(255,0,0,.5)}50%{box-shadow:0 0 50px rgba(255,0,0,.9)}}
.btn-act{background:#1E2A36;color:var(--tx);font-size:14px;padding:12px}.btn-sm{padding:8px 18px;font-size:12px;width:auto;display:inline-block}
.btn-xs{padding:5px 12px;font-size:10px;width:auto;display:inline-block}
.info-t{font-size:11px;color:var(--mt);margin-bottom:10px;text-transform:uppercase;letter-spacing:2px}
table{width:100%;border-collapse:collapse;font-size:13px;margin-top:10px}
th{text-align:left;color:var(--mt);padding:10px 8px;border-bottom:2px solid var(--bd);font-size:11px;text-transform:uppercase}
td{padding:10px 8px;border-bottom:1px solid rgba(30,42,54,.5)}tr:hover td{background:rgba(255,255,255,.02)}
.badge{display:inline-block;padding:4px 12px;border-radius:20px;font-size:11px;font-weight:bold}
.badge-on{background:#1a3a2a;color:var(--gn)}.badge-off{background:#3a1a1a;color:var(--rd)}
.badge-adm{background:#1a2a3a;color:var(--ac);border:1px solid var(--ac)}
input,textarea{width:100%;padding:12px;margin:6px 0;background:#0D1117;color:var(--tx);border:1px solid var(--bd);border-radius:8px;font:inherit;font-size:14px}
input:focus,textarea:focus{outline:none;border-color:var(--ac)}
textarea{resize:none;height:80px}
.scroll{max-height:400px;overflow-y:auto}
.flex{display:flex;gap:20px;flex-wrap:wrap}.flex-c{flex:1;min-width:350px}
.bar{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:10px}
.out{color:var(--rd);text-decoration:none;font-size:12px;padding:8px 16px;border:1px solid var(--rd);border-radius:8px}
.out:hover{background:var(--rd);color:#fff}
a{color:var(--ac);text-decoration:none}
.modal{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.85);display:flex;justify-content:center;align-items:center;z-index:1000}
.modal-in{background:var(--pn);border:1px solid var(--ac);border-radius:16px;padding:30px;max-width:600px;width:90%;animation:mi .3s}@keyframes mi{from{transform:scale(.9);opacity:0}to{transform:scale(1);opacity:1}}
.det-l{color:var(--mt);font-size:10px;text-transform:uppercase;letter-spacing:2px;margin-bottom:4px}
.det-v{font-size:16px;margin-bottom:16px;color:#E8EDF2}
.det-t{background:#0D1117;border:1px solid var(--bd);border-radius:8px;padding:16px;font-size:14px;white-space:pre-wrap;line-height:1.6}
</style>"""

# ===== ШАБЛОНЫ =====
LOGIN = CSS + """<div style="display:flex;justify-content:center;align-items:center;min-height:90vh"><div class="card" style="width:400px;text-align:center;padding:40px"><img src="/static/logo.png" class="logo-img" onerror="this.style.display='none'"><div class="logo">ЧОО «АЛЬФА»</div><div class="sub">ТЕРМИНАЛ v5.1</div><div style="font-size:48px;margin:20px 0">🛡️</div>{% if e %}<div style="background:#3a1a1a;color:var(--rd);padding:12px;border-radius:8px;margin-bottom:20px;border:1px solid var(--rd)">{{e}}</div>{% endif %}<form method="post"><input name="u" placeholder="Логин" required autofocus><input name="p" type="password" placeholder="Пароль" required><button class="btn btn-start">🔐 ВОЙТИ</button></form></div></div>"""

MAIN = CSS + """<body class="{{'alarm' if alarm else ''}}"><div style="max-width:650px;margin:0 auto"><div class="bar"><div><span style="color:var(--ac);font-weight:bold;font-size:16px">{{u.full_name}}</span> <span style="color:var(--mt);font-size:11px">({{u.username}})</span>{% if u.role=='admin' %}<span class="badge badge-adm">АДМИН</span>{% endif %}</div><div><a href="/reports" class="btn btn-sm btn-act">📋 ОТЧЁТЫ</a>{% if u.role=='admin' %}<a href="/admin" class="btn btn-sm btn-act">📊 ПАНЕЛЬ</a>{% endif %}<a href="/logout" class="out">ВЫХОД</a></div></div><div class="card" style="text-align:center"><img src="/static/logo.png" class="logo-img" onerror="this.style.display='none'"><div class="logo">ЧОО «АЛЬФА»</div><div class="sub">ТЕРМИНАЛ v5.1</div></div><div class="card" style="text-align:center"><div class="info-t">СТАТУС СМЕНЫ</div><div style="font-size:38px;font-weight:bold;color:{{'#2ECC71' if duty else '#E63946'}}">{{'НА СМЕНЕ' if duty else 'ВНЕ СМЕНЫ'}}</div><div style="font-size:22px;margin-top:8px">{{timer}}</div></div><form method="post" action="/toggle">{% if duty %}<button class="btn btn-end">📤 СДАТЬ</button>{% else %}<button class="btn btn-start">🛡️ ЗАСТУПИТЬ</button>{% endif %}</form><form method="post" action="/alarm"><button class="btn btn-alarm {{'active' if alarm else ''}}">{{'🔴 ТРЕВОГА АКТИВНА!' if alarm else '🚨 ТРЕВОГА'}}</button></form>{% if alarm %}<form method="post" action="/alarm_reset"><button class="btn btn-end">🔇 СБРОСИТЬ</button></form>{% endif %}<div class="card"><div class="info-t">ИНФОРМАЦИЯ</div><p>ID: {{sid or '--'}} | Начало: {{st or '--'}} | Время: {{now}}</p><p>Охранник: {{u.full_name}}  </p></div><div class="card"><div class="info-t">📝 МОИ ОТЧЁТЫ</div><div class="scroll"><table><tr><th>ID</th><th>Тип</th><th>Описание</th><th>Время</th><th></th></tr>{% for r in reps %}<tr><td><b>#{{r.id}}</b></td><td style="color:{{r.clr}}">{{r.type}}</td><td>{{r.text[:35]}}{% if r.text|length>35%}...{% endif %}</td><td style="font-size:11px">{{r.time}}</td><td><a href="/r/{{r.id}}" class="btn btn-xs btn-act">👁️</a></td></tr>{% endfor %}</table></div></div><a href="/reports" class="btn btn-act" style="text-align:center;font-size:16px;padding:14px">📋 НОВЫЙ ОТЧЁТ</a></div>{% if duty or alarm %}<script>setTimeout(function(){location.reload()},3000)</script>{% endif %}</body>"""

REPORT_VIEW = CSS + """<body><div class="modal" onclick="if(event.target==this)location='/terminal'"><div class="modal-in"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px"><div class="logo" style="font-size:20px">ОТЧЁТ #{{r.id}}</div><a href="/terminal" style="color:var(--mt);font-size:20px">✕</a></div><div class="det-l">ТИП</div><div class="det-v" style="color:{{c}}">{{r.type}}</div><div class="det-l">ID СМЕНЫ</div><div class="det-v">{{r.shift_id}}</div><div class="det-l">АВТОР</div><div class="det-v">{{author}}</div><div class="det-l">ВРЕМЯ</div><div class="det-v">{{r.time}}</div><div class="det-l">СОДЕРЖАНИЕ</div><div class="det-t">{{r.text}}</div><div style="margin-top:20px;text-align:center"><a href="/terminal" class="btn btn-act" style="display:inline-block">🔙 ЗАКРЫТЬ</a></div></div></div></body>"""

REPORTS = CSS + """<body><div style="max-width:650px;margin:0 auto"><div class="bar"><div><span style="color:var(--ac);font-weight:bold">{{u.full_name}}</span></div><div><a href="/terminal" class="btn btn-sm btn-act">🏠</a><a href="/logout" class="out">ВЫХОД</a></div></div><div class="card" style="text-align:center"><img src="/static/logo.png" class="logo-img" onerror="this.style.display='none'"><div class="logo">ЧОО «АЛЬФА»</div><div class="sub">ШАБЛОНЫ ОТЧЁТОВ</div></div>
{% for t,c,n in [('Задержание','#E74C3C','🚔'),('Докладная','#F39C12','📄'),('Применение оружия','#E67E22','🔫'),('ГБР Выезд','#3498DB','🚁')] %}
<div class="card" style="border-left:4px solid {{c}};cursor:pointer" onclick="var f=document.getElementById('form{{loop.index}}');if(f.classList.contains('open')){f.style.maxHeight='0';f.classList.remove('open')}else{f.style.maxHeight=f.scrollHeight+'px';f.classList.add('open')}">
<div style="font-size:20px;color:{{c}};font-weight:bold">{{n}} {{t|upper}} <span style="float:right;font-size:14px" id="arrow{{loop.index}}">▼</span></div>
<div id="form{{loop.index}}" style="max-height:0;overflow:hidden;transition:max-height 0.4s ease;margin-top:0">
<div style="margin-top:15px">
<form method="post" action="/report"><input type="hidden" name="type" value="{{t}}"><input name="name" placeholder="Объект / имя"><textarea name="text" placeholder="Описание..."></textarea><button class="btn" style="background:{{c}};color:#fff;font-weight:bold">📝 СОЗДАТЬ</button></form>
</div></div></div>
{% endfor %}
</div></body>"""

ADMIN = CSS + """<body><div style="max-width:1200px;margin:0 auto"><div class="bar"><div><span style="color:var(--ac);font-weight:bold;font-size:18px">{{u.full_name}}</span> <span class="badge badge-adm">АДМИН</span></div><div><a href="/terminal" class="btn btn-sm btn-act">🏠</a><a href="/logout" class="out">ВЫХОД</a></div></div><img src="/static/logo.png" class="logo-img" style="width:100px;height:100px" onerror="this.style.display='none'"><div class="logo" style="font-size:32px">ЧОО «АЛЬФА»</div><div class="sub" style="margin-bottom:25px">АДМИН-ПАНЕЛЬ</div><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:20px"><div class="card" style="text-align:center;border-left:4px solid var(--gn)"><div style="font-size:36px;color:var(--gn)">{{ac}}</div><div style="color:var(--mt);font-size:12px">НА ПОСТУ</div></div><div class="card" style="text-align:center;border-left:4px solid var(--ac)"><div style="font-size:36px;color:var(--ac)">{{rc}}</div><div style="color:var(--mt);font-size:12px">ОТЧЁТОВ</div></div><div class="card" style="text-align:center;border-left:4px solid var(--or)"><div style="font-size:36px;color:var(--or)">{{alc}}</div><div style="color:var(--mt);font-size:12px">ТРЕВОГ</div></div><div class="card" style="text-align:center;border-left:4px solid var(--rd)"><div style="font-size:36px;color:var(--rd)">{{'🔴' if alarm else '🟢'}}</div><div style="color:var(--mt);font-size:12px">ТРЕВОГА</div></div></div><div class="flex"><div class="flex-c"><div class="card"><div class="info-t">👥 СОТРУДНИКИ</div><div class="scroll" style="max-height:350px"><table><tr><th>Логин</th><th>ФИО</th><th>Роль</th><th>Статус</th><th>На смене</th></tr>{% for u in users %}<tr><td><b>{{u.un}}</b></td><td>{{u.fn}}</td><td>{% if u.rl=='admin' %}<span class="badge badge-adm">АДМИН</span>{% else %}Охранник{% endif %}</td><td>{% if u.on %}<span class="badge badge-on">● НА ПОСТУ</span>{% else %}<span class="badge badge-off">○ НЕТ</span>{% endif %}</td><td>{{u.tm or '--'}}</td></tr>{% endfor %}</table></div></div></div><div class="flex-c"><div class="card"><div class="info-t">🟢 АКТИВНЫЕ СМЕНЫ</div><div class="scroll" style="max-height:350px">{% if shifts %}<table><tr><th>Охранник</th><th>ID</th><th>Начало</th><th>Прошло</th><th></th></tr>{% for s in shifts %}<tr><td><b>{{s.fn}}</b></td><td style="font-size:11px">{{s.id}}</td><td>{{s.st}}</td><td style="color:var(--gn);font-weight:bold">{{s.tm}}</td><td><form method="post" action="/force_end/{{s.un}}" style="display:inline"><button class="btn btn-xs btn-end" style="padding:4px 8px;font-size:10px">⛔</button></form></td></tr>{% endfor %}</table>{% else %}<p style="color:var(--mt);text-align:center;padding:30px">Никого на посту</p>{% endif %}</div></div></div></div><div class="card"><div class="info-t">📝 ВСЕ ОТЧЁТЫ</div><div class="scroll" style="max-height:300px"><table><tr><th>ID</th><th>Автор</th><th>Тип</th><th>Описание</th><th>Время</th></tr>{% for r in reps %}<tr><td><b>#{{r.id}}</b></td><td>{{r.username}}</td><td>{{r.type}}</td><td>{{r.text[:45]}}</td><td style="font-size:11px">{{r.time}}</td></tr>{% endfor %}</table></div></div></div><script>setTimeout(function(){location.reload()},10000)</script></body>"""

# ===== МАРШРУТЫ =====
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory('static', filename)

@app.route("/")
def index():
    return redirect("/terminal") if me() else redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        raw_login = request.form["u"].strip()
        password = request.form["p"]
        
        original_key = None
        
        if raw_login in USERS:
            original_key = raw_login
        elif raw_login.lower() in USERS_LOWER:
            original_key = USERS_LOWER[raw_login.lower()]
        
        if original_key and USERS[original_key]["password"] == password:
            session["username"] = original_key
            print(f"[LOGIN] ✅ {original_key}")
            return redirect("/terminal")
        
        print(f"[LOGIN] ❌ Попытка: '{raw_login}'")
        error = "❌ Неверный логин или пароль"
    
    return render_template_string(LOGIN, e=error)

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/login")

@app.route("/terminal")
def terminal():
    u = me()
    if not u: return redirect("/login")
    un = u["username"]
    duty = un in st["active_shifts"]
    sd = st["active_shifts"].get(un, {})
    sec = int(sd.get("elapsed_seconds", 0))
    h, m, s = sec // 3600, (sec % 3600) // 60, sec % 60
    now = datetime.now(TIMEZONE)
    reps = sorted([r for r in st["reports"] if r["username"] == un], key=lambda x: x["id"], reverse=True)[:10]
    cm = {"Задержание": "#E74C3C", "Докладная": "#F39C12", "Обход территории": "#1ABC9C",
          "Применение оружия": "#E67E22", "ГБР Выезд": "#3498DB", "ТРЕВОГА": "#FF0000", "О смене": "#9c1010"}
    for r in reps: r["clr"] = cm.get(r["type"], "#C8CDD2")
    return render_template_string(MAIN, u=u, duty=duty, timer=f"{h:02d}:{m:02d}:{s:02d}",
        sid=sd.get("shift_id"), st=sd["start_time"].strftime("%H:%M:%S") if sd.get("start_time") else None,
        now=now.strftime("%H:%M:%S"), alarm=st["alarm_active"], reps=reps)

@app.route("/r/<int:rid>")
def view(rid):
    u = me()
    if not u: return redirect("/login")
    r = next((r for r in st["reports"] if r["id"] == rid), None)
    if not r: return "Не найден", 404
    cm = {"Задержание": "#E74C3C", "Докладная": "#F39C12", "Обход территории": "#1ABC9C",
          "Применение оружия": "#E67E22", "ГБР Выезд": "#3498DB", "ТРЕВОГА": "#FF0000", "О смене": "#00B4D8"}
    author = USERS.get(r["username"], {}).get("full_name", r["username"])
    return render_template_string(REPORT_VIEW, r=r, c=cm.get(r["type"], "#C8CDD2"), author=author)

@app.route("/reports")
def reports():
    u = me()
    if not u: return redirect("/login")
    return render_template_string(REPORTS, u=u)

@app.route("/report", methods=["POST"])
def create():
    u = me()
    if not u: return redirect("/login")
    tp = request.form["type"]
    nm = request.form.get("name", "").strip()
    tx = request.form.get("text", "").strip() or "(пусто)"
    full = f"{nm} — {tx}" if nm else tx
    now = datetime.now(TIMEZONE)
    sid = st["active_shifts"].get(u["username"], {}).get("shift_id", "N/A")
    rid = len(st["reports"]) + 1
    st["reports"].append({"id": rid, "type": tp, "text": full,
        "time": now.strftime("%Y-%m-%d %H:%M"), "shift_id": sid, "username": u["username"]})
    save_data()
    colors = {"Задержание": 0xE74C3C, "Докладная": 0xF39C12, "Обход территории": 0x1ABC9C,
              "Применение оружия": 0xE67E22, "ГБР Выезд": 0x3498DB}
    discord(f"📝 {tp} #{rid}", full[:200], colors.get(tp, 0x00B4D8),
            fields=[{"name": "Автор", "value": u["full_name"], "inline": True},
                    {"name": "Смена", "value": sid, "inline": True}])
    return redirect("/reports")

@app.route("/toggle", methods=["POST"])
def toggle():
    u = me()
    if not u: return redirect("/login")
    un = u["username"]
    now = datetime.now(TIMEZONE)
    if un not in st["active_shifts"]:
        st["shift_counter"] += 1
        sid = f"ALPHA-{now.strftime('%Y-%m-%d')}-{st['shift_counter']:03d}"
        st["active_shifts"][un] = {"shift_id": sid, "start_time": now, "elapsed_seconds": 0}
        st["reports"].append({"id": len(st["reports"]) + 1, "type": "О смене",
            "text": f"Заступил: {sid}", "time": now.strftime("%Y-%m-%d %H:%M"),
            "shift_id": sid, "username": un})
        save_data()
        discord("🛡️ ЗАСТУПИЛ", f"{u['full_name']} — {sid}", 0x2ECC71,
                fields=[{"name": "Время", "value": now.strftime('%H:%M:%S'), "inline": True}])
    else:
        sd = st["active_shifts"].pop(un)
        total_sec = sd["elapsed_seconds"]
        hours = int(total_sec // 3600)
        minutes = int((total_sec % 3600) // 60)
        sid = sd["shift_id"]
        st["reports"].append({"id": len(st["reports"]) + 1, "type": "О смене",
            "text": f"Сдал: {hours}ч {minutes}мин", "time": now.strftime("%Y-%m-%d %H:%M"),
            "shift_id": sid, "username": un})
        st["shift_history"].append({"shift_id": sid, "username": un,
            "start": sd["start_time"].strftime("%Y-%m-%d %H:%M"),
            "end": now.strftime("%Y-%m-%d %H:%M"), "hours": round(total_sec/3600, 1)})
        save_data()
        discord("📤 СДАЛ", f"{u['full_name']} — {sid}", 0xE63946,
                fields=[{"name": "Отработано", "value": f"{hours} ч {minutes} мин", "inline": True}])
    return redirect("/terminal")

@app.route("/alarm", methods=["POST"])
def alarm():
    u = me()
    if not st["alarm_active"]:
        st["alarm_active"] = True
        now = datetime.now(TIMEZONE)
        un = u["username"] if u else "system"
        full_name = u["full_name"] if u else "Система"
        sid = st["active_shifts"].get(un, {}).get("shift_id") if u else None
        
        st["alarms"].append({"time": now.strftime("%Y-%m-%d %H:%M:%S"), "active": True, "shift_id": sid, "username": un, "full_name": full_name})
        st["reports"].append({"id": len(st["reports"]) + 1, "type": "ТРЕВОГА",
            "text": f"🚨 ТРЕВОГА! Активировал: {full_name}", "time": now.strftime("%Y-%m-%d %H:%M"),
            "shift_id": sid, "username": un})
        save_data()
        discord(
            "🚨 ТРЕВОГА!",
            "Требуется реагирование!",
            0xFF0000,
            True,
            fields=[
                {"name": "👤 Сотрудник", "value": full_name, "inline": True},
                {"name": "Смена", "value": sid or "N/A", "inline": True}
            ]
        )
    return redirect("/terminal")

@app.route("/alarm_reset", methods=["POST"])
def alarm_reset():
    if st["alarm_active"]:
        st["alarm_active"] = False
        if st["alarms"]: st["alarms"][-1]["active"] = False
        st["reports"].append({"id": len(st["reports"]) + 1, "type": "ТРЕВОГА",
            "text": "🔇 Сброшена", "time": datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M"),
            "shift_id": None, "username": "system"})
        save_data()
        discord("🔇 СБРОШЕНА", "", 0x95A5A6)
    return redirect("/terminal")

@app.route("/force_end/<username>", methods=["POST"])
def force_end(username):
    u = me()
    if not u or u.get("role") != "admin":
        return redirect("/login")
    
    if username in st["active_shifts"]:
        sd = st["active_shifts"].pop(username)
        total_sec = sd["elapsed_seconds"]
        hours = int(total_sec // 3600)
        minutes = int((total_sec % 3600) // 60)
        now = datetime.now(TIMEZONE)
        sid = sd["shift_id"]
        
        st["reports"].append({
            "id": len(st["reports"]) + 1,
            "type": "О смене",
            "text": f"⛔ Админ закрыл смену: {hours}ч {minutes}мин",
            "time": now.strftime("%Y-%m-%d %H:%M"),
            "shift_id": sid,
            "username": username
        })
        st["shift_history"].append({
            "shift_id": sid,
            "username": username,
            "start": sd["start_time"].strftime("%Y-%m-%d %H:%M"),
            "end": now.strftime("%Y-%m-%d %H:%M"),
            "hours": round(total_sec/3600, 1)
        })
        save_data()
        discord("⛔ АДМИН ЗАКРЫЛ СМЕНУ", f"{USERS.get(username,{}).get('full_name',username)} — {sid}\nОтработано: {hours}ч {minutes}мин", 0xFF9800,
                fields=[{"name": "Закрыл", "value": u["full_name"], "inline": True},
                        {"name": "Отработано", "value": f"{hours}ч {minutes}мин", "inline": True}])
        print(f"[ADMIN] {u['username']} закрыл смену {username}: {sid}")
    
    return redirect("/admin")

@app.route("/admin")
def admin():
    u = me()
    if not u or u.get("role") != "admin": return redirect("/login")
    users = []
    for un, ud in USERS.items():
        on = un in st["active_shifts"]
        sec = st["active_shifts"].get(un, {}).get("elapsed_seconds", 0)
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        users.append({"un": un, "fn": ud["full_name"], "rl": ud.get("role", "guard"),
                       "on": on, "tm": f"{h:02d}:{m:02d}:{s:02d}" if on else None})
    shifts = []
    for un, sd in st["active_shifts"].items():
        sec = sd.get("elapsed_seconds", 0)
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        shifts.append({"fn": USERS.get(un, {}).get("full_name", un),
                        "un": un,
                        "id": sd.get("shift_id", ""),
                        "st": sd["start_time"].strftime("%H:%M:%S") if sd.get("start_time") else "",
                        "tm": f"{h:02d}:{m:02d}:{s:02d}"})
    reps = sorted(st["reports"], key=lambda x: x["id"], reverse=True)[:50]
    return render_template_string(ADMIN, u=u, users=users, shifts=shifts, reps=reps,
                                  ac=len(shifts), rc=len(st["reports"]), alc=len(st["alarms"]), alarm=st["alarm_active"])

# ===== ЗАПУСК =====
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🛡️  ЧОО АЛЬФА v5.1 — DEBUG MODE")
    print("=" * 60)
    print("📡 http://127.0.0.1:5000")
    print(f"👤 Пользователей: {len(USERS)}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)