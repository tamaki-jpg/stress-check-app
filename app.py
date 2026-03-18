import sqlite3
import csv
import io
import os
import random
import smtplib
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, render_template, Response, g, session, redirect, url_for

app = Flask(__name__)

# ============================================================
# 設定
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'stress_check.db')

# セッション用シークレットキー（変更しても問題なし）
app.secret_key = 'tsubasa-stress-check-secret-2024'

# 管理者認証情報
ADMIN_EMAIL    = 'tamaki@sr-tsubasa.com'
ADMIN_PASSWORD = 'tamatsuba'

# ============================================================
# SMTP設定（メール送信用）
# ご利用のメールサービスに合わせて変更してください
# ============================================================
SMTP_HOST = 'smtp.gmail.com'      # GmailはSMTPホスト名
SMTP_PORT = 587                   # TLS用ポート
SMTP_USER = 'tamaki@sr-tsubasa.com'   # 送信元アドレス（変更してください）
SMTP_PASS = 'inlrwcvlkhzbchoe'    # アプリパスワード（設定済み）
SMTP_FROM_NAME = 'つばさ社会保険労務士事務所'

# OTP保存（メモリ内）: { email: {'otp': '123456', 'expires': timestamp} }
_otp_store: dict = {}
OTP_EXPIRE_SECONDS = 600  # 10分

# ============================================================
# DB ヘルパー
# ============================================================
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    q_columns = ', '.join([f'q{i} INTEGER' for i in range(1, 58)])
    with sqlite3.connect(DATABASE) as conn:
        conn.execute(f'''
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                furigana TEXT NOT NULL,
                birth_date TEXT NOT NULL,
                gender TEXT NOT NULL,
                employee_id TEXT NOT NULL,
                workplace_code TEXT NOT NULL,
                workplace_name TEXT NOT NULL,
                {q_columns},
                submitted_at TEXT NOT NULL
            )
        ''')
        conn.commit()

# ============================================================
# OTP ヘルパー
# ============================================================
def generate_otp() -> str:
    return f'{random.randint(0, 999999):06d}'

def save_otp(email: str, otp: str):
    _otp_store[email] = {
        'otp': otp,
        'expires': time.time() + OTP_EXPIRE_SECONDS
    }

def verify_otp(email: str, otp_input: str) -> bool:
    entry = _otp_store.get(email)
    if not entry:
        return False
    if time.time() > entry['expires']:
        del _otp_store[email]
        return False
    if entry['otp'] != otp_input.strip():
        return False
    del _otp_store[email]  # 使用済みは削除
    return True

def send_otp_email(to_email: str, otp: str) -> bool:
    """OTPメールを送信する。成功したらTrue、失敗したらFalse"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '【つばさSR】管理画面ワンタイムパスワード'
        msg['From']    = f'{SMTP_FROM_NAME} <{SMTP_USER}>'
        msg['To']      = to_email

        html_body = f"""
<html><body style="font-family:sans-serif; color:#1a202c; max-width:480px; margin:0 auto; padding:24px;">
  <div style="background:#2d5a27; padding:20px; border-radius:8px 8px 0 0; text-align:center;">
    <div style="color:#d6e9ca; font-size:12px; letter-spacing:2px; font-weight:700;">STRESS CHECK SYSTEM</div>
    <div style="color:#fff; font-size:18px; font-weight:700; margin-top:4px;">ワンタイムパスワード</div>
  </div>
  <div style="background:#fff; border:1px solid #e2e8f0; border-top:none; padding:32px; border-radius:0 0 8px 8px;">
    <p>管理画面へのログインリクエストを受け付けました。<br>以下のコードを入力してください。</p>
    <div style="background:#f0f6ec; border:2px solid #2d5a27; border-radius:8px; text-align:center; padding:20px; margin:24px 0;">
      <div style="font-size:36px; font-weight:700; letter-spacing:12px; color:#2d5a27; font-family:monospace;">{otp}</div>
      <div style="font-size:12px; color:#9aa5b4; margin-top:8px;">有効期限：10分</div>
    </div>
    <p style="font-size:12px; color:#9aa5b4;">このメールに心当たりがない場合は、無視してください。</p>
    <hr style="border:none; border-top:1px solid #e2e8f0; margin:20px 0;">
    <p style="font-size:11px; color:#b0bac5; text-align:center;">つばさ社会保険労務士事務所</p>
  </div>
</body></html>"""

        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        app.logger.error(f'メール送信失敗: {e}')
        return False

# ============================================================
# 従業員向けルーティング
# ============================================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/submit', methods=['POST'])
def submit():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data received'}), 400

    required_fields = ['name', 'furigana', 'birth_date', 'gender',
                       'employee_id', 'workplace_code', 'workplace_name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    answers = []
    for i in range(1, 58):
        val = data.get(f'q{i}')
        if val is None or str(val) not in ['1', '2', '3', '4']:
            return jsonify({'error': f'q{i} の回答が不正です（1〜4で指定してください）'}), 400
        answers.append(int(val))

    q_cols       = ', '.join([f'q{i}' for i in range(1, 58)])
    placeholders = ', '.join(['?'] * (7 + 57 + 1))

    row = [
        data['name'], data['furigana'], data['birth_date'], data['gender'],
        data['employee_id'], data['workplace_code'], data['workplace_name'],
    ] + answers + [datetime.now().strftime('%Y/%m/%d %H:%M:%S')]

    db = get_db()
    db.execute(
        f'INSERT INTO responses (name, furigana, birth_date, gender, employee_id, workplace_code, workplace_name, {q_cols}, submitted_at) VALUES ({placeholders})',
        row
    )
    db.commit()
    return jsonify({'success': True, 'message': '回答を保存しました。'}), 201

# ============================================================
# 管理者向けルーティング
# ============================================================
def admin_required(f):
    """管理者セッションがなければログインページへリダイレクト"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/admin')
@admin_required
def admin():
    return render_template('admin.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            otp = generate_otp()
            save_otp(email, otp)
            success = send_otp_email(email, otp)
            if success:
                session['otp_email'] = email
                return redirect(url_for('admin_verify'))
            else:
                # メール送信失敗時はOTPをログに出力（開発用）
                app.logger.warning(f'[DEV] OTP for {email}: {otp}')
                session['otp_email'] = email
                error = f'メール送信に失敗しました。開発中はサーバーログにOTPが表示されています。'
                return redirect(url_for('admin_verify'))
        else:
            error = 'メールアドレスまたはパスワードが正しくありません。'

    return render_template('login.html', error=error)

@app.route('/admin/verify', methods=['GET', 'POST'])
def admin_verify():
    email = session.get('otp_email')
    if not email:
        return redirect(url_for('admin_login'))

    error = None
    if request.method == 'POST':
        otp_input = request.form.get('otp', '').strip()
        if verify_otp(email, otp_input):
            session.pop('otp_email', None)
            session['admin_logged_in'] = True
            session.permanent = True
            return redirect(url_for('admin'))
        else:
            error = 'コードが正しくないか、有効期限が切れています。'

    return render_template('verify.html', email=email, error=error)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/api/responses', methods=['GET'])
@admin_required
def get_responses():
    db = get_db()
    rows = db.execute(
        'SELECT id, name, furigana, birth_date, gender, employee_id, workplace_code, workplace_name, submitted_at FROM responses ORDER BY id DESC'
    ).fetchall()
    return jsonify([dict(row) for row in rows])

@app.route('/api/csv', methods=['GET'])
@admin_required
def download_csv():
    db = get_db()
    q_cols = ', '.join([f'q{i}' for i in range(1, 58)])
    rows = db.execute(
        f'SELECT name, furigana, birth_date, gender, employee_id, workplace_code, workplace_name, {q_cols} FROM responses ORDER BY id ASC'
    ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output, lineterminator='\r\n')
    header = ['氏名', 'フリガナ', '生年月日', '性別', '社員ID', '職場コード', '職場名']
    header += [f'Q{i}' for i in range(1, 58)]
    writer.writerow(header)
    for row in rows:
        writer.writerow(list(row))

    csv_bytes = output.getvalue().encode('utf-8-sig')
    return Response(
        csv_bytes,
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename="stress_check_results.csv"',
            'Content-Type': 'text/csv; charset=utf-8-sig'
        }
    )

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
