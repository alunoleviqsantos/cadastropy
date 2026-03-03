from flask import Flask, render_template, request, jsonify, redirect, url_for, flash  # flash para mensagens de feedback
import json
import os
import uuid 
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "chave-super-secreta"

def carregar_usuarios():
    try:
        if os.path.exists("usuarios.json"):
            with open("usuarios.json", "r", encoding="utf-8") as arquivo:
                return json.load(arquivo)
        else:
            return []  
    except:
        return []  
def salvar_usuario(usuario):
    usuarios = carregar_usuarios()

    try:
        usuarios.append(usuario)

        with open("usuarios.json", "w", encoding="utf-8") as arquivo:
            json.dump(usuarios, arquivo, indent=4)

        return True 
    except:
        return False 

@app.route("/")
def home():
    return render_template("home.html") 
@app.route("/cadastro-usuario")
def tela_cadastro():
    return render_template("cadastro-usuario.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        cpf = request.form.get("cpf")
        senha_digitada = request.form.get("senha")

        usuarios = carregar_usuarios()

        for usuario in usuarios:
            if usuario.get("cpf") == cpf and check_password_hash(usuario.get("senha", ""), senha_digitada):
                flash("Login realizado com sucesso", "sucesso")
                return redirect(url_for("buscar_usuarios"))

        flash("CPF ou senha incorretos", "erro")
        return render_template("login.html")

    return render_template("login.html")

@app.route("/cadastro-usuario", methods=["POST"])
def cadastrar_usuario():
    nome = request.form.get("nome")
    cpf = request.form.get("cpf")            
    email = request.form.get("email")
    idade = request.form.get("idade")
    senha = request.form.get("senha")
    senha_hash = generate_password_hash(senha)

    if not all([nome, cpf, email, idade, senha]):
        flash("Todos os campos são obrigatórios.", "erro")
        return redirect(url_for("tela_cadastro"))
    usuarios = carregar_usuarios()

    if any(u.get("cpf") == cpf for u in usuarios):
        flash("CPF já cadastrado no sistema.", "erro")
        return redirect(url_for("tela_cadastro"))
    
    if int(idade) < 18:
        flash("Idade mínima para cadastro é de 18 anos.", "erro")
        return redirect(url_for("tela_cadastro"))
    usuario = {
        "id": str(uuid.uuid4()),  
        "nome": nome,
        "cpf": cpf,
        "email": email,
        "idade": idade,
        "senha": senha_hash,
    }

    status = salvar_usuario(usuario)

    if status:
        flash("Usuário cadastrado com sucesso.", "sucesso")
        return redirect(url_for('buscar_usuarios'))
    else:
        # caso de erro de escrita
        flash("Não foi possível cadastrar o usuário.", "erro")
        return redirect(url_for('home'))



@app.route("/usuarios/json", methods=["GET"])
def buscar_usuarios_json():
    usuarios = carregar_usuarios()
    return jsonify(usuarios)

@app.route("/usuarios", methods=["GET"])
def buscar_usuarios():
    usuarios = carregar_usuarios()
    total = len(usuarios)
    return render_template("usuarios.html", usuarios = usuarios, total=total)

@app.route("/usuarios/deletar", methods=["POST"])
def deletar_usuario():
    cpf = request.form.get("cpf")
    
    if not cpf:
        flash("CPF necessário para exclusão", "erro")
        return redirect(url_for('buscar_usuarios'))
    
    usuarios = carregar_usuarios()
    novos = [u for u in usuarios if u.get("cpf") != cpf]

    try: 
        with open("usuarios.json", "w", encoding="utf-8") as arquivo:
            json.dump(novos, arquivo, indent=4)
            flash ("usuario removido.",  "sucesso")
    except Exception as e:
        flash(f"Erro ao deleta: {e}", "erro")

    return redirect(url_for('buscar_usuarios'))
if __name__== '__main__':
    app.run(debug=True, port=5001)