import sqlite3
from flask import Flask,request,url_for,render_template,redirect,g,session
from flask_session import Session
from helper import apology,admin_required,login_required
from werkzeug.security import generate_password_hash,check_password_hash
app=Flask(__name__)
app.config['SESSION_PERMANENT']=False
app.config['SESSION_TYPE']='filesystem'
app.config['DATABASE']='blog.db'
Session(app)
#链接数据库并将返回类型设置为row对象
def get_db():
    if 'db' not in g:
        g.db=sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory=sqlite3.Row
    return g.db
def close_db(e):
    db=g.pop('db',None)
    if db is not None:
        db.close()
app.teardown_appcontext(close_db)

#查找文章
def find_article(name=None,id=None):
    db=get_db()
    if name==None and id==None:
        articles=db.execute('SELECT * FROM articles ORDER BY created_at DESC').fetchall()
    elif id==None:
        articles=db.execute('SELECT * FROM articles WHERE name LIKE ? ORDER BY created_at',(f'%{name}%',)).fetchall()
    else:
        articles=db.execute('SELECT * FROM articles WHERE id=? ORDER BY created_at',(id,)).fetchall()
    return articles

def init_db():
    #初始化数据库
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user')''')
    db.execute('''CREATE TABLE IF NOT EXISTS articles(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        writer TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        type TEXT,
        article TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id))''')
    #生成管理账户
    
    db.execute('INSERT OR IGNORE INTO users(id,username,hash,role) VALUES(?,?,?,?)',(1,'admin',str(generate_password_hash('helloworld')),'admin'))
    
    db.commit()
    
    
#首页
@app.route('/',methods=['GET','POST'])
def index():
    articles=find_article()
    if session['user_id']:
        db=get_db()
        user=db.execute('SELECT * FROM users WHERE id=?',(session['user_id'],)).fetchone()
        return render_template('index.html',articles=articles,username=user['username'])
   
    return render_template('index.html',articles=articles)


@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        username=request.form.get('username')
        password=request.form.get('password')
        #防止空输入
        if not username or not password:
            return apology('请输入完整',403)
        #检查用户是否存在
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE username=?',(username,))
        userlist=cursor.fetchall()
        if bool(userlist):
            return apology('用户已存在')
        #加密密码
        hash_password=generate_password_hash(password)
        #存储用户数据
        cursor.execute('INSERT INTO users(username,hash) VALUES(?,?)',(username,hash_password))
        db.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


#登录
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        session.clear()
        username=request.form.get('username')
        password=request.form.get('password')
        #防止空输入
        if not username or not password:
            return apology('请输入完整')
        #检查用户是否存在
        db = get_db()
        userlist=db.execute('SELECT * FROM users WHERE username=?',(username,)).fetchall()
        
        if not userlist:
            return apology('用户不存在')
        #验证密码
        if check_password_hash(userlist[0]['hash'],password):
            session['user_id']=userlist[0]['id']
        else:
            return apology('密码错误')
        return redirect(url_for('index'))
    return render_template('login.html')


#发布文章
@app.route('/release',methods=['POST','GET'])
def release():
    if request.method=='POST':
        article=request.form.get('article')
        title=request.form.get('title')
        type=request.form.get('type')
        id=int(session.get('user_id'))
        print(article,title,type,id)
        if article and title:
            db=get_db()
            user=db.execute('SELECT * FROM users WHERE id=?',(id,)).fetchall()
            db.execute('INSERT INTO articles(article,title,type,user_id,writer) VALUES(?,?,?,?,?)',(article,title,type,id,user[0]['username']))
            db.commit()
        else:
            return apology('请输入完整')
        
    return render_template('release.html')


#查看某篇文章
@app.route('/article/<id>')
def article(id):
    article=find_article(id=id)
    
    return render_template('article.html',article=article[0])


#删除文章
@app.route('/delete',methods=['GET','POST'])
@admin_required
def delete():
    if request.method=='POST':
        id=request.form.get('id')
        db=get_db()
        db.execute('DELETE FROM articles WHERE id=?',(id,))
        db.commit()
    return redirect(url_for('index'))


#退出登录
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


#设置
@app.route('/setting',methods=['GET','POST'])
@login_required
def setting():
    if request.method=='POST':
        id=session['user_id']
        new_name=request.form.get('new_name')
        password=request.form.get('password')
        new_password=request.form.get('new_password')
        confirm_password=request.form.get('confirm_password')
        db=get_db()
        print(id)
        user=db.execute('SELECT * FROM users WHERE id=?',(id,)).fetchone()
        #判断密码是否正确
        print(user['hash'])
        if not password:
            return apology('请输入密码')
        if not check_password_hash(user['hash'],password):
            return apology('密码错误')
        #改变用户名
        if new_name:
            db.execute('UPDATE users SET username=? WHERE id=?',(new_name,id))
        #改变密码
        if new_password and confirm_password:
            if new_password == confirm_password:
                db.execute('UPDATE users SET hash=? WHERE id=?',(generate_password_hash(new_password),id))
            else:
                return apology('两次输入的密码不一致')
            
        db.commit()
        return redirect(url_for('index'))
    return render_template('setting.html')
with app.app_context():
    init_db()
        
