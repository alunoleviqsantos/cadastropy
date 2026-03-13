from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

from models.usuario import Usuario
from models.sessao_usuario import SessaoUsuario
from models.validacao_cadastro import ValidacaoCadastro

app = Flask(__name__)
app.secret_key = "chave-super-secreta"

sessao = SessaoUsuario(session)


def carregar_usuarios():
    if os.path.exists("usuarios.json"):
        with open("usuarios.json", "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    return []


def salvar_todos(usuarios):
    with open("usuarios.json", "w", encoding="utf-8") as arquivo:
        json.dump(usuarios, arquivo, indent=4)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/cadastro-usuario", methods=["GET", "POST"])
def cadastrar_usuario():

    if request.method == "GET":
        return render_template("cadastro-usuario.html")

    usuarios = carregar_usuarios()

    validador = ValidacaoCadastro(request.form, usuarios)

    if not validador.validar():

        for erro in validador.erros:
            flash(erro, "erro")

        return redirect(url_for("cadastrar_usuario"))

    nome = request.form.get("nome")
    cpf = request.form.get("cpf").replace(".", "").replace("-", "")
    email = request.form.get("email")
    idade = request.form.get("idade")
    senha = request.form.get("senha")

    senha_hash = generate_password_hash(senha)

    nivel = "admin" if len(usuarios) == 0 else "comum"

    usuario = Usuario(nome, cpf, email, idade, senha_hash, nivel)

    usuarios.append(usuario.to_dict())

    salvar_todos(usuarios)

    flash("Usuário cadastrado com sucesso.", "sucesso")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        cpf = request.form.get("cpf").replace(".", "").replace("-", "")
        senha = request.form.get("senha")

        usuarios = carregar_usuarios()

        for usuario in usuarios:

            if usuario["cpf"] == cpf and check_password_hash(usuario["senha"], senha):

                sessao.iniciar(usuario)

                flash("Login realizado com sucesso", "sucesso")
                return redirect(url_for("buscar_usuarios"))

        flash("CPF ou senha incorretos", "erro")

    return render_template("login.html")


@app.route("/usuarios")
def buscar_usuarios():

    if not sessao.esta_logado():
        flash("Você precisa estar logado.", "erro")
        return redirect(url_for("login"))

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

    if not sessao.eh_admin():
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

    sessao.encerrar()

    flash("Logout realizado.", "sucesso")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)