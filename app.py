from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import json
import os
import uuid
import re
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "chave-super-secreta"

def carregar_usuarios():
    if os.path.exists("usuarios.json"):
        with open("usuarios.json", "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    return []


def salvar_todos(usuarios):
    with open("usuarios.json", "w", encoding="utf-8") as arquivo:
        json.dump(usuarios, arquivo, indent=4)


def validar_cpf(cpf):
    padrao = r'^\d{3}\.\d{3}\.\d{3}\-\d{2}$'
    return re.match(padrao, cpf)

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/cadastro-usuario")
def tela_cadastro():
    return render_template("cadastro-usuario.html")

@app.route("/cadastro-usuario", methods=["POST"])
def cadastrar_usuario():

    nome = request.form.get("nome")
    cpf = request.form.get("cpf")
    email = request.form.get("email")
    idade = request.form.get("idade")
    senha = request.form.get("senha")

    if not all([nome, cpf, email, idade, senha]):
        flash("Todos os campos são obrigatórios.", "erro")
        return redirect(url_for("tela_cadastro"))

    if not validar_cpf(cpf):
        flash("CPF deve estar no formato 000.000.000-00", "erro")
        return redirect(url_for("tela_cadastro"))

    cpf_limpo = cpf.replace(".", "").replace("-", "")

    usuarios = carregar_usuarios()

    if any(u["cpf"] == cpf_limpo for u in usuarios):
        flash("CPF já cadastrado.", "erro")
        return redirect(url_for("tela_cadastro"))

    if int(idade) < 18:
        flash("Idade mínima é 18 anos.", "erro")
        return redirect(url_for("tela_cadastro"))

    senha_hash = generate_password_hash(senha)

    usuario = {
        "id": str(uuid.uuid4()),
        "nome": nome,
        "cpf": cpf_limpo,
        "email": email,
        "idade": idade,
        "senha": senha_hash,
        "nivel": "comum"  
    }

    usuarios.append(usuario)
    salvar_todos(usuarios)

    flash("Usuário cadastrado com sucesso.", "sucesso")
    return redirect(url_for("buscar_usuarios"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        cpf = request.form.get("cpf")
        senha_digitada = request.form.get("senha")

        cpf_limpo = cpf.replace(".", "").replace("-", "")

        usuarios = carregar_usuarios()

        for usuario in usuarios:
            if usuario["cpf"] == cpf_limpo and check_password_hash(usuario["senha"], senha_digitada):

                session["usuario_logado"] = usuario["cpf"]
                session["nivel"] = usuario.get("nivel", "comum")

                flash("Login realizado com sucesso", "sucesso")
                return redirect(url_for("buscar_usuarios"))

        flash("CPF ou senha incorretos", "erro")

    return render_template("login.html")

@app.route("/usuarios")
def buscar_usuarios():

    usuarios = carregar_usuarios()

    busca = request.args.get("busca")
    ordem = request.args.get("ordem")

    if busca:
        usuarios = [
            u for u in usuarios
            if busca.lower() in u["nome"].lower()
            or busca in u["cpf"]
        ]

    if ordem == "asc":
        usuarios = sorted(usuarios, key=lambda x: int(x["idade"]))
    elif ordem == "desc":
        usuarios = sorted(usuarios, key=lambda x: int(x["idade"]), reverse=True)

    return render_template("usuarios.html", usuarios=usuarios)

@app.route("/usuarios/json")
def buscar_usuarios_json():
    return jsonify(carregar_usuarios())

@app.route("/usuarios/deletar", methods=["POST"])
def deletar_usuario():

    if session.get("nivel") != "admin":
        flash("Apenas administradores podem excluir.", "erro")
        return redirect(url_for("buscar_usuarios"))

    cpf = request.form.get("cpf")

    usuarios = carregar_usuarios()
    novos = [u for u in usuarios if u["cpf"] != cpf]

    salvar_todos(novos)

    flash("Usuário removido.", "sucesso")
    return redirect(url_for("buscar_usuarios"))

@app.route("/logout")
def logout():
    session.clear()
    flash("Logout realizado.", "sucesso")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True, port=5001)