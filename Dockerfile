# 公式のPython 3.10 スリムイメージをベースにする
FROM python:3.10-slim

# ローカルへ出力をバッファリングせず、即座にログに出力する設定
ENV PYTHONUNBUFFERED True

# コンテナ内の作業ディレクトリを指定
WORKDIR /app

# 依存関係ファイルのみ先にコピー（キャッシュ活用のため）
COPY requirements.txt ./

# 必要なライブラリをインストール
RUN pip install --no-cache-dir -r requirements.txt

# ローカルの全ファイルをコンテナにコピー
COPY . ./

# 本番環境ではFirestoreを使わせるフラグを設定
ENV USE_FIRESTORE=1

# Cloud Run が Listen する PORT を指定
ENV PORT=8080

# WebサーバーGunicornを利用してアプリを起動
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app