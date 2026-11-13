import argparse
from getpass import getpass
import secrets

from app.auth.auth import hash_senha
from app.database import SessionLocal
from app.models.usuario import Usuario


def cpf_aleatorio():
    digitos = [secrets.randbelow(10) for _ in range(9)]
    for peso_inicial in (10, 11):
        soma = sum(digito * peso for digito, peso in zip(digitos, range(peso_inicial, 1, -1)))
        resto = soma % 11
        digitos.append(0 if resto < 2 else 11 - resto)
    return "".join(map(str, digitos))


def salvar_administrador(nome, cpf, email, senha):
    with SessionLocal.begin() as db:
        if db.query(Usuario).filter(Usuario.cpf == cpf).first():
            raise SystemExit("Já existe um usuário com esse CPF.")
        if db.query(Usuario).filter(Usuario.email == email).first():
            raise SystemExit("Já existe um usuário com esse e-mail.")
        db.add(
            Usuario(
                nome=nome,
                cpf=cpf,
                email=email,
                permissao="Administrador",
                senha_hash=hash_senha(senha),
                status=True,
            )
        )


def salvar_administrador_teste(email, cpf, senha):
    with SessionLocal.begin() as db:
        usuario = db.query(Usuario).filter(Usuario.email == email).first()
        if usuario:
            usuario.senha_hash = hash_senha(senha)
            usuario.permissao = "Administrador"
            usuario.status = True
            return
        while db.query(Usuario).filter(Usuario.cpf == cpf).first():
            cpf = cpf_aleatorio()
        db.add(
            Usuario(
                nome="Administrador de Teste",
                cpf=cpf,
                email=email,
                permissao="Administrador",
                senha_hash=hash_senha(senha),
                status=True,
            )
        )


def main():
    parser = argparse.ArgumentParser(description="Cria um usuário administrador do FourPulse.")
    parser.add_argument(
        "--test-account",
        action="store_true",
        help="Cria uma conta de teste e gera uma senha aleatória para mostrar uma única vez.",
    )
    args = parser.parse_args()

    if args.test_account:
        email = "admin.teste@fourpulse.local"
        senha = secrets.token_urlsafe(18)
        cpf = cpf_aleatorio()
        salvar_administrador_teste(email, cpf, senha)
        print("Administrador de teste criado ou senha renovada.")
        print(f"E-mail: {email}")
        print(f"Senha (guarde agora): {senha}")
        return

    nome = input("Nome do administrador: ").strip()
    cpf = input("CPF: ").strip()
    email = input("E-mail: ").strip().casefold()
    senha = getpass("Senha (mínimo 8 caracteres): ")
    confirmacao = getpass("Confirme a senha: ")

    if not nome or not cpf or not email:
        raise SystemExit("Nome, CPF e e-mail são obrigatórios.")
    if len(senha) < 8:
        raise SystemExit("A senha deve ter pelo menos 8 caracteres.")
    if senha != confirmacao:
        raise SystemExit("As senhas não coincidem.")

    salvar_administrador(nome, cpf, email, senha)
    print("Administrador cadastrado com sucesso.")


if __name__ == "__main__":
    main()
