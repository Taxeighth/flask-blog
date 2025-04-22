from flask import Flask, render_template, request, redirect, abort, url_for, session
from datetime import datetime
import os
import re
import markdown
from markupsafe import Markup
ADMIN_ID = "admin"
ADMIN_PW = "qlqjs!3367"


app = Flask(__name__)

POST_DIR = "post_files"

def load_posts():
    posts = []
    for filename in sorted(os.listdir(POST_DIR)):
        if filename.endswith(".txt"):
            with open(os.path.join(POST_DIR, filename), encoding="utf-8") as f:
                lines = f.readlines()
                if len(lines) >= 3:
                    title = lines[0].strip()
                    content = "".join(lines[1:-1]).strip()
                    date = lines[-1].strip()
                    posts.append({"title": title, "content": content, "date": date})
    print("불러온 글:", posts)
    return posts

app.secret_key = '비밀키123!'  # 꼭 설정해야 세션 작동함

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == ADMIN_ID and password == ADMIN_PW:
            session["user"] = username
            return redirect("/posts")
        else:
            return render_template("login.html", error="❌ 아이디 또는 비밀번호가 잘못되었습니다.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    try:
        with open("about.txt", "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = "소개글이 아직 작성되지 않았습니다."
    html_content = markdown.markdown(content)
    return render_template("about.html", content=html_content)

@app.route("/about/edit", methods=["GET", "POST"])
def edit_about():
    if 'user' not in session:
        return redirect("/login")

    if request.method == "POST":
        new_content = request.form["content"]
        with open("about.txt", "w", encoding="utf-8") as f:
            f.write(new_content)
        return redirect("/about")

    try:
        with open("about.txt", "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = ""

    return render_template("edit_about.html", content=content)

@app.route("/posts")
def posts():
    query = request.args.get("q", "").lower()
    post_list = load_posts()

    if query:
        post_list = [
            post for post in post_list
            if query in post["title"].lower() or query in post["content"].lower()
        ]

    return render_template("posts.html", posts=post_list, highlight_keyword=highlight_keyword)

@app.route("/posts/<int:post_id>")
def post_detail(post_id):
    post_list = load_posts()
    if 0 <= post_id < len(post_list):
        post = post_list[post_id]
        html_content = markdown.markdown(post["content"])  # ← 여기서 변환
        return render_template(
            "post_detail.html",
            title=post["title"],
            content=html_content,
            date=post["date"]
        )
    else:
        return "해당 글이 존재하지 않습니다.", 404


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        date = datetime.now().strftime("%Y-%m-%d %H:%M")

        filenames = sorted([f for f in os.listdir(POST_DIR) if f.endswith(".txt")])
        new_index = len(filenames)
        filename = f"{new_index}.txt"

        with open(os.path.join(POST_DIR, filename), "w", encoding="utf-8") as f:
            f.write(title.strip() + "\n")
            f.write(content.strip() + "\n")
            f.write(date)

        return redirect("/posts")
    else:
        return render_template("create.html")

@app.route("/delete/<int:post_id>", methods=["POST"])
def delete(post_id):
    filename = f"{post_id}.txt"
    file_path = os.path.join(POST_DIR, filename)

    if os.path.exists(file_path):
        os.remove(file_path)
        return redirect("/posts")
    else:
        abort(404)

@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
def edit(post_id):
    filepath = os.path.join(POST_DIR, f"{post_id}.txt")

    if not os.path.exists(filepath):
        return "해당 글이 존재하지 않습니다.", 404

    if request.method == "POST":
        # 폼에서 새로 입력한 데이터 가져오기
        title = request.form["title"]
        content = request.form["content"]

        # 기존 작성일 불러오기
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) >= 3:
            date = lines[-1].strip()
        else:
            date = ""

        # 다시 저장 (작성일은 유지)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(title.strip() + "\n")
            f.write(content.strip() + "\n")
            f.write(date)

        return redirect("/posts")
    
    else:
        # 수정 폼 열기 - 기존 내용 불러오기
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        title = lines[0].strip() if len(lines) > 0 else ""
        content = "".join(lines[1:-1]).strip() if len(lines) > 2 else ""

        return render_template("edit.html", title=title, content=content)



def highlight_keyword(text, keyword):
    if not keyword:
        return text
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    highlighted = pattern.sub(lambda match: f"<mark>{match.group(0)}</mark>", text)
    return Markup(highlighted)

if __name__ == "__main__":
    app.run(debug=True)
