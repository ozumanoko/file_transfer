from flask import Flask, redirect, request
from flask import render_template, send_file
import os, json, time
import fs_data #ファイルを管理するモジュール

app = Flask(__name__)
MASTER_PW = 'abcd' #管理者パスワード

@app.route('/')
def index():
    #ファイルのアップロードフォームを表示
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    #アップロードしたファイルのオブジェクト
    upfile = request.files.get('upfile', None)
    if upfile is None: return msg('アップロード失敗')
    if upfile.filename == '': return msg('アップロード失敗')
    # メタ情報を取得
    meta = {
        'name': request.form.get('name', '名無し'),
        'memo': request.form.get('memo', 'なし'),
        'pw': request.form.get('pw', ''),
        'limit': int(request.form.get('limit', '1')),
        'count': int(request.form.get('count', '0')),
        'filename': upfile.filename
    }
    if (meta['limit'] == 0) or (meta['pw'] == ''):
        return msg('パラメーターが不正です。')
    #ファイルを保存
    fs_data.save_file(upfile, meta)
    #ダウンロード先の表示
    return render_template('info.html',
                            meta=meta, mode='upload',
                            url=request.host_url + 'download/' + meta['id'])

@app.route('/download/<id>')
def download(id):
    #URLが正しいか判定
    meta = fs_data.get_data(id)
    if meta is None: return msd('パラメータが不正です')
    #ダウンロードページを表示
    return render_template('info.html',
                            meta=meta, mode='download',
                            url=request.host_url + 'download_go/' + id)

@app.route('/download_go/<id>', methods=['POST'])
def download_go(id):
    #URLが正しいか判定
    meta = fs_data.get_data(id)
    if meta is None: return msg('パラメータが不正です')
    #パスワードの確認
    pw = request.form.get('pw', '')
    print(pw, meta['pw']) #テスト
    if pw != meta['pw']: return msg('パスワードが違います')
    #ダウンロード回数の制限
    meta['count'] -= 1
    if meta['count'] < 0:
        return msg('ダウンロード回数を超えました')
    fs_data.set_data(id, meta)
    #ダウンロード期限の確認
    if meta['time_limit'] < time.time():
        return msg('ダウンロードの期限過ぎています')
    #ダウンロードができるようにファイルを送信
    return send_file(meta['path'],
                    as_attachment=True,
                    attachment_filename=meta['filename'])

@app.route('/admin/list')
def admin_list():
    if request.args.get('pw', '') != MASTER_PW:
        return msg('マスターパスワードが違います')
    #全データをデータベースから取り出して表示
    return render_template('admin_list.html',
                            files=fs_data.get_all(), pw=MASTER_PW)

@app.route('/adim/remove/<id>')
def admin_remove(id):
    if request.args.get('pw', ''):
        return msg('マスターパスワードが違います')
    fs_data.remove_data(id)
    return msg('消去しました')

def msg(s):
    return render_template('error.html', message=s)

def filter_datetime(tm):
    return time.strftime(
        '%Y/%m/%d %H:%M:%S',
        time.localtime(tm)
    )

#フィルターをテンプレートエンジンに登録
app.jinja_env.filters['datetime'] = filter_datetime

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
