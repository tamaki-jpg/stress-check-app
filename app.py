import os
import json
import sqlite3
import datetime
import io
import csv
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, make_response

app = Flask(__name__)
# セッション（結果画面へのデータ受け渡し）を使うための暗号化キー
app.secret_key = 'stress_check_super_secret_key'

# ==========================================
# データベース(SQLite)の初期設定
# ==========================================
DB_NAME = 'database.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # 職場（組織図）テーブル
    c.execute('''
        CREATE TABLE IF NOT EXISTS workplaces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            level INTEGER NOT NULL
        )
    ''')
    # 設定テーブル（管理画面の実施者管理と連動）
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT ''
        )
    ''')
    # 回答結果テーブル（回答内容は扱いやすいようにJSONで丸ごと保存）
    c.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            name TEXT NOT NULL,
            workplace_name TEXT,
            is_high_stress BOOLEAN,
            answers_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# アプリ起動時にDBを作成
init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def get_setting(key, default=''):
    conn = get_db_connection()
    row = conn.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
    conn.close()
    return row['value'] if row else default

# ==========================================
# ストレスチェック 判定 ＆ 詳細スコア計算ロジック
# ==========================================
def analyze_stress(answers):
    # 1. 素点計算（高いほどストレス大）
    a_score = sum([int(answers.get(f'q{i}', 3)) if i in [8,9,10,16,17] else (5 - int(answers.get(f'q{i}', 3))) for i in range(1, 18)])
    b_score = sum([(5 - int(answers.get(f'q{i}', 3))) if i in [18,19,20] else int(answers.get(f'q{i}', 3)) for i in range(18, 47)])
    c_score = sum([int(answers.get(f'q{i}', 3)) for i in range(47, 56)])

    # 高ストレス判定（厚労省基準準拠）
    is_high_stress = False
    if b_score >= 77:
        is_high_stress = True
    elif b_score >= 63 and (a_score + c_score) >= 76:
        is_high_stress = True

    # 2. 5段階スケール変換（1:悪い ～ 5:良い）
    def to_5_scale(q_list, reverse_goodness=False):
        total = sum([(5 - int(answers.get(f'q{i}', 3))) if reverse_goodness else int(answers.get(f'q{i}', 3)) for i in q_list])
        avg = total / len(q_list)
        return round(1 + (avg - 1) * (4 / 3), 1)

    # レーダーチャート用（7軸）
    radar_scores = [
        to_5_scale([1,2,3,4,5,6,7], False),     # 負担
        to_5_scale([8,9,10], True),             # コントロール
        to_5_scale([18,19,20], False),          # 活気
        to_5_scale([21,22,23,24,25,26], True),  # イライラ
        to_5_scale([27,28,29,30,31,32,33,34,35], True), # 不安・抑うつ
        to_5_scale([47,50,53], True),           # 上司支援
        to_5_scale([48,51,54], True)            # 同僚支援
    ]

    # 3. 詳細棒グラフ用スコア ＆ 自動コメント生成
    domain_a_avg = to_5_scale(list(range(1, 18)), False)
    domain_b_avg = to_5_scale(list(range(18, 47)), True)
    domain_c_avg = to_5_scale(list(range(47, 56)), True)

    advice_text = "日々の業務お疲れ様です。"
    if domain_b_avg <= 2.5:
        advice_text += "心身のストレス反応が強く出ているようです。休息を最優先にしてください。"
    elif domain_a_avg <= 2.5:
        advice_text += "仕事の量や質による負担が大きいようです。業務の調整や周囲への相談を検討してみましょう。"
    elif domain_c_avg <= 2.5:
        advice_text += "周囲のサポートが不足していると感じているようです。一人で抱え込まず、発信することが大切です。"
    else:
        advice_text += "現在のところ、全体的なバランスは比較的良好に保たれています。引き続きセルフケアを継続してください。"

    return {
        'is_high_stress': is_high_stress,
        'radar_scores': radar_scores,
        'bars': {
            'domain_a': domain_a_avg,
            'domain_b': domain_b_avg,
            'domain_c': domain_c_avg
        },
        'advice_text': advice_text
    }

# ==========================================
# ルーティング（画面表示）
# ==========================================

@app.route('/')
def index():
    # 従業員ページ：DBから職場一覧と設定を取得して渡す
    conn = get_db_connection()
    workplaces_db = conn.execute('SELECT * FROM workplaces ORDER BY code').fetchall()
    conn.close()

    workplaces = [dict(wp) for wp in workplaces_db]
    company_name      = get_setting('company_name', 'デモ企業')
    practitioner_name = get_setting('practitioner_name', '（未設定）')
    return render_template('index.html',
                           company_name=company_name,
                           practitioner_name=practitioner_name,
                           workplaces=workplaces)

@app.route('/admin')
def admin():
    # 管理者ダッシュボード
    return render_template('admin.html')

@app.route('/result')
def show_result():
    # 従業員の個人結果レポート画面
    result_data = session.get('result_data')
    if not result_data:
        return redirect(url_for('index'))
    return render_template('result.html', **result_data)

# ==========================================
# APIエンドポイント（データ処理）
# ==========================================

@app.route('/api/submit', methods=['POST'])
def submit_data():
    """ 従業員からの回答データを受け取る """
    data = request.json

    # 1. 高ストレス判定とスコア計算を実行
    analysis = analyze_stress(data)

    # 2. データベース(SQLite)に保存（employee_idは自動採番）
    conn = get_db_connection()
    cursor = conn.execute('''
        INSERT INTO responses (employee_id, name, workplace_name, is_high_stress, answers_json)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        '',  # 仮で空にしてINSERT後に採番
        data.get('name', ''),
        data.get('workplace_name', ''),
        analysis['is_high_stress'],
        json.dumps(data, ensure_ascii=False)
    ))
    row_id = cursor.lastrowid
    # 挿入されたDBのIDをそのままemployee_idとして設定（1, 2, 3...の連番）
    conn.execute('UPDATE responses SET employee_id = ? WHERE id = ?', (str(row_id), row_id))
    conn.commit()
    conn.close()

    # 3. 結果画面に渡すデータをセッションに保存
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    session['result_data'] = {
        'employee_id': str(row_id),
        'name': data.get('name', ''),
        'workplace_name': data.get('workplace_name', ''),
        'exam_date': today_str,
        'ref_number': f"SC-{row_id:04d}",
        'is_high_stress': analysis['is_high_stress'],
        'radar_scores': analysis['radar_scores'],
        'bars': analysis['bars'],
        'advice_text': analysis['advice_text']
    }
    
    # 4. フロントエンドに「成功したから結果画面に飛んでね」と返す
    return jsonify({'success': True, 'redirect_url': url_for('show_result')})

# ----------------- 職場管理API -----------------
@app.route('/api/workplaces', methods=['GET', 'POST'])
def manage_workplaces():
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.json
        conn.execute('INSERT INTO workplaces (code, name, level) VALUES (?, ?, ?)',
                     (data['code'], data['name'], data['level']))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    else:
        workplaces = conn.execute('SELECT * FROM workplaces ORDER BY code').fetchall()
        conn.close()
        return jsonify([dict(wp) for wp in workplaces])

@app.route('/api/workplaces/<int:id>', methods=['DELETE'])
def delete_workplace(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM workplaces WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ----------------- 結果一覧取得API（管理者画面用） ----------------- 
@app.route('/api/responses') 
def get_responses(): 
    conn = get_db_connection() 
    rows = conn.execute('SELECT * FROM responses ORDER BY created_at DESC').fetchall() 
    conn.close() 
    
    results = []
    for r in rows:
        # DBに保存されている詳細データ（JSON）を読み解く
        try:
            ans = json.loads(r['answers_json'])
        except:
            ans = {}
            
        # admin.htmlが求めている名前（キー）にピッタリ合わせてデータを渡す
        results.append({
            'id': r['id'],
            'employee_id': r['employee_id'],
            'name': r['name'],
            'furigana': ans.get('furigana', ''),
            'birth_date': ans.get('birth_date', ''),
            'gender': ans.get('gender', ''),
            'workplace_code': ans.get('workplace_code', ''),
            'workplace_name': r['workplace_name'],
            'is_high_stress': r['is_high_stress'],
            'submitted_at': r['created_at']
        })
        
    return jsonify(results)

# ----------------- 設定管理API（管理画面の実施者管理と連動） -----------------
@app.route('/api/settings', methods=['GET', 'POST'])
def manage_settings():
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.json or {}
        for key, value in data.items():
            conn.execute(
                'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                (key, str(value))
            )
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    rows = conn.execute('SELECT key, value FROM settings').fetchall()
    conn.close()
    return jsonify({row['key']: row['value'] for row in rows})

# ----------------- Excel出力API（職場データ・取込用フォーマット） -----------------
@app.route('/api/csv/workplaces')
def export_workplaces_csv():
    conn = get_db_connection()
    workplaces = conn.execute('SELECT code, name, level FROM workplaces ORDER BY code').fetchall()
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'newSheet'

    # ヘッダー行の定義（添付Excelと同じ13列）
    headers = [
        '職場コード', '前回職場コード',
        '第1職場名', '第2職場名', '第3職場名', '第4職場名', '第5職場名',
        '第6職場名', '第7職場名', '第8職場名', '第9職場名', '第10職場名',
        '初回パスワード'
    ]

    # ヘッダースタイル
    header_fill   = PatternFill('solid', start_color='1F497D', end_color='1F497D')
    header_font   = Font(name='Arial', bold=True, color='FFFFFF', size=10)
    header_align  = Alignment(horizontal='center', vertical='center', wrap_text=True)
    thin_border   = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    for col_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.font   = header_font
        cell.fill   = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    # データ行：level に応じて第N職場名カラムに名前を入れる
    data_font  = Font(name='Arial', size=10)
    data_align = Alignment(vertical='center')

    for row_idx, wp in enumerate(workplaces, start=2):
        level = int(wp['level']) if wp['level'] else 1
        # 13列分の空行を作成し、職場コードと該当する第N職場名だけ埋める
        row_data = [''] * 13
        row_data[0] = str(wp['code'])          # A: 職場コード
        row_data[1] = ''                        # B: 前回職場コード（空）
        name_col = 1 + level                    # C=第1(level1), D=第2(level2)...
        if 2 <= name_col <= 11:
            row_data[name_col] = wp['name']     # 第N職場名
        row_data[12] = ''                       # M: 初回パスワード（空）

        for col_idx, val in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.font      = data_font
            cell.alignment = data_align
            cell.border    = thin_border

    # 列幅の調整
    col_widths = [14, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16]
    for i, width in enumerate(col_widths, start=1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

    ws.row_dimensions[1].height = 30  # ヘッダー行の高さ

    # バイト列として出力
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    output = make_response(buf.read())
    output.headers["Content-Disposition"] = "attachment; filename=workplaces.xlsx"
    output.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return output

# ----------------- CSV出力API（回答データ・指定フォーマット版） -----------------
@app.route('/api/csv')
def export_results_csv():
    conn = get_db_connection()
    responses = conn.execute('SELECT * FROM responses ORDER BY created_at DESC').fetchall()
    conn.close()

    si = io.StringIO()
    cw = csv.writer(si)
    
    # 1. いただいたCSVフォーマットに合わせたヘッダーを作成
    headers = [
        '氏名', 'フリガナ', '生年月日(西暦)', '性別', '社員ID', '職場コード', '職場名',
        '前回社員ID', 'メールアドレス', '電話番号', '内線番号', '備考', '管理者コメント', '変数値'
    ]
    headers += [f'A-{i}' for i in range(1, 18)]
    headers += [f'B-{i}' for i in range(1, 30)]
    headers += [f'C-{i}' for i in range(1, 10)]
    headers += [f'D-{i}' for i in range(1, 3)]
    
    cw.writerow(headers)

    # 2. データをフォーマットに当てはめる
    for r in responses:
        try:
            ans = json.loads(r['answers_json'])
        except:
            ans = {}
            
        row = [
            r['name'],                      # 氏名
            ans.get('furigana', ''),        # フリガナ
            ans.get('birth_date', ''),      # 生年月日(西暦)
            ans.get('gender', ''),          # 性別
            r['employee_id'],               # 社員ID
            ans.get('workplace_code', ''),  # 職場コード
            r['workplace_name'],            # 職場名
            '', '', '', '', '', '', ''      # 前回社員ID 〜 変数値までは空欄
        ]
        
        # A-1 〜 A-17 (q1 〜 q17)
        for i in range(1, 18):
            row.append(ans.get(f'q{i}', ''))
            
        # B-1 〜 B-29 (q18 〜 q46)
        for i in range(18, 47):
            row.append(ans.get(f'q{i}', ''))
            
        # C-1 〜 C-9 (q47 〜 q55)
        for i in range(47, 56):
            row.append(ans.get(f'q{i}', ''))
            
        # D-1 〜 D-2 (q56 〜 q57)
        for i in range(56, 58):
            row.append(ans.get(f'q{i}', ''))
            
        cw.writerow(row)

    # 取込システムで文字化けしないように「cp932 (Shift_JIS)」で出力します
    output = make_response(si.getvalue().encode('cp932', errors='replace'))
    output.headers["Content-Disposition"] = "attachment; filename=stress_results.csv"
    output.headers["Content-type"] = "text/csv"
    return output

# ==========================================
# サーバー起動設定（Gcloud Run対応）
# ==========================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)