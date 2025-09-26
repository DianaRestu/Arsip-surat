from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import mysql.connector
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'rahasia'    
app.config['UPLOAD_FOLDER'] = 'uploads'  

# ---------- KONEKSI KE MYSQL ----------
db = mysql.connector.connect(
    host="localhost",
    user="root",        
    password="", 
    database="arsip surat"
)
cursor = db.cursor(dictionary=True)

# ---------- ROUTE HALAMAN UTAMA ----------
@app.route('/')
def index():
    q = request.args.get('q', '')
    if q:
        cursor.execute("SELECT a.*, k.nama_kategori FROM arsip a LEFT JOIN kategori k ON a.kategori_id=k.id WHERE a.judul LIKE %s ORDER BY a.tanggal_upload DESC", 
                       ('%' + q + '%',))
    else:
        cursor.execute("SELECT a.*, k.nama_kategori FROM arsip a LEFT JOIN kategori k ON a.kategori_id=k.id ORDER BY a.tanggal_upload DESC")
    arsip = cursor.fetchall()
    return render_template('index.html', arsip=arsip, q=q)

# ---------- UNGGAH SURAT ----------
@app.route('/arsip/tambah', methods=['GET','POST'])
def tambah_arsip():
    if request.method == 'POST':
        judul = request.form['judul']
        kategori_id = request.form['kategori_id']
        file = request.files['file_pdf']

        if file and file.filename.lower().endswith('.pdf'):
            nama_file = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], nama_file))
            cursor.execute("INSERT INTO arsip (judul, kategori_id, nama_file) VALUES (%s, %s, %s)",
                           (judul, kategori_id, nama_file))
            db.commit()
            flash("Data berhasil disimpan","success")
            return redirect(url_for('index'))
        else:
            flash("File harus berformat PDF","danger")

    cursor.execute("SELECT * FROM kategori ORDER BY nama_kategori")
    kategori = cursor.fetchall()
    return render_template('tambah_arsip.html', kategori=kategori)

# ---------- UNDUH FILE ----------
@app.route('/unduh/<nama_file>')
def unduh(nama_file):
    return send_from_directory(app.config['UPLOAD_FOLDER'], nama_file, as_attachment=True)

# ---------- HAPUS ARSIP ----------
@app.route('/hapus/<int:id>')
def hapus(id):
    cursor.execute("SELECT nama_file FROM arsip WHERE id=%s", (id,))
    data = cursor.fetchone()
    if data:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], data['nama_file']))
        except:
            pass
    cursor.execute("DELETE FROM arsip WHERE id=%s", (id,))
    db.commit()
    flash("Data berhasil dihapus","success")
    return redirect(url_for('index'))

# ---------- DETAIL / LIHAT ARSIP ----------
@app.route('/lihat/<int:id>')
def lihat(id):
    # ambil data arsip + kategori
    cursor.execute("""
        SELECT a.*, k.nama_kategori 
        FROM arsip a 
        LEFT JOIN kategori k ON a.kategori_id=k.id
        WHERE a.id=%s
    """, (id,))
    arsip = cursor.fetchone()
    if not arsip:
        flash("Arsip tidak ditemukan","danger")
        return redirect(url_for('index'))
    return render_template('lihat.html', arsip=arsip)


# ---------- CRUD KATEGORI ----------
@app.route('/kategori')
def list_kategori():
    cursor.execute("SELECT * FROM kategori ORDER BY id DESC")
    kategori = cursor.fetchall()
    return render_template('kategori.html', kategori=kategori)

@app.route('/kategori/tambah', methods=['GET','POST'])
def tambah_kategori():
    if request.method == 'POST':
        nama = request.form['nama']
        cursor.execute("INSERT INTO kategori (nama_kategori) VALUES (%s)", (nama,))
        db.commit()
        flash("Kategori berhasil ditambah","success")
        return redirect(url_for('list_kategori'))
    return render_template('tambah_kategori.html')

@app.route('/kategori/edit/<int:id>', methods=['GET','POST'])
def edit_kategori(id):
    if request.method == 'POST':
        nama = request.form['nama']
        cursor.execute("UPDATE kategori SET nama_kategori=%s WHERE id=%s", (nama, id))
        db.commit()
        flash("Kategori berhasil diupdate","success")
        return redirect(url_for('list_kategori'))
    cursor.execute("SELECT * FROM kategori WHERE id=%s", (id,))
    kat = cursor.fetchone()
    return render_template('edit_kategori.html', kat=kat)

@app.route('/kategori/hapus/<int:id>')
def hapus_kategori(id):
    cursor.execute("DELETE FROM kategori WHERE id=%s", (id,))
    db.commit()
    flash("Kategori berhasil dihapus","success")
    return redirect(url_for('list_kategori'))

# ---------- HALAMAN ABOUT ----------
@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
