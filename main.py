from flask import Flask, render_template, redirect, url_for, flash, request, session
import fdb
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'

host = 'localhost'
database = r'C:\Users\SN1089702\Downloads\bancofire\LIVRO.FDB'
user = 'SYSDBA'
password = 'sysdba'

#Conexão

con = fdb.connect( host=host, database=database, user=user, password=password )

class Usuario:
    def __init__(self, id_usuario, nome, email, senha):
        self.id = id_usuario
        self.nome = nome
        self.email = email
        self.senha = senha

class Receita:
    def __init__(self, id_receita, id_usuario, nome, valor_receita, data):
        self.id_receita = id_receita
        self.id_usuario = id_usuario
        self.nome = nome
        self.valor_receita = valor_receita
        self.data = data

class Despesa:
    def __init__(self, id_despesa, id_usuario, nome, valor_despesa, data):
        self.id_despesa = id_despesa
        self.id_usuario = id_usuario
        self.nome = nome
        self.valor_despesa = valor_despesa
        self.data = data


# Rota para a página inicial
@app.route('/inicio', methods=['GET'])
def inicio():
    total_receita = 0
    total_despesa = 0
    # Verifica se o usuário está autenticado
    if 'id_usuario' not in session:
        flash('Você precisa estar logado no sistema.')
        return redirect(url_for('login'))

    id_usuario = session['id_usuario']

    cursor = con.cursor()
    try:
        cursor.execute('SELECT coalesce(VALOR_RECEITA,0) FROM RECEITA where id_usuario = ?', (id_usuario,))
        for row in cursor.fetchall():
            total_receita = total_receita + row[0]

        cursor.execute('SELECT coalesce(VALOR_DESPESA,0) FROM DESPESA where id_usuario = ?', (id_usuario,))
        for row in cursor.fetchall():
            total_despesa = total_despesa + row[0]
    except Exception as e:
        total_receita = 0
        total_despesa = 0
        print(f"Erro ao buscar total_receita: {str(e)}")
        print(f"Tipo do erro: {type(e)}")
    finally:
        cursor.close()
    # Aqui você pode renderizar um template ou retornar os valores
    return render_template('index.html', total_receita=total_receita, total_despesa=total_despesa)


@app.route('/cria_usuario', methods=['GET'])
def cria_usuario():
    return render_template('adiciona_usuario.html')

# Rota para adicionar usuário
@app.route('/adiciona_usuario', methods=['POST'])
def adiciona_usuario():
    data = request.form
    nome = data['nome']
    email = data['email']
    senha = data['senha']

    cursor = con.cursor()
    try:
        cursor.execute('SELECT FIRST 1 id_usuario FROM USUARIO WHERE EMAIL = ?', (email,))
        if cursor.fetchone() is not None:
            flash('Este email já está sendo usado!')
            return redirect(url_for('cria_usuario'))

        cursor.execute("INSERT INTO Usuario (nome, email, senha) VALUES (?, ?, ?)",
                       (nome, email, senha))
        con.commit()
    finally:
        cursor.close()
    flash('Usuario adicionado com sucesso!')
    return redirect(url_for('login'))

# Rota de Login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        cursor = con.cursor()
        try:
            cursor.execute("SELECT id_usuario,nome FROM Usuario WHERE email = ? AND senha = ?", (email, senha,))
            usuario = cursor.fetchone()
        except Exception as e:
            flash(f'Erro ao acessar o banco de dados: {e}')  # Mensagem de erro para o usuário
            return redirect(url_for('login'))  # Redireciona de volta ao login
        finally:
            cursor.close()

        if usuario:
            session['id_usuario'] = usuario[0]  # Armazena o ID do usuário na sessão
            session['nome'] = usuario[1] #nome do mané
            return redirect(url_for('inicio'))
        else:
            flash('Email ou senha incorretos!')

    return render_template('login.html')

# Rota de Logout
@app.route('/logout')
def logout():
    session.pop('id_usuario', None)
    return redirect(url_for('login'))

@app.route('/cria_receita')
def cria_receita():

    # Verifica se o usuário está autenticado
    if 'id_usuario' not in session:
        flash('Você precisa estar logado no sistema.')
        return redirect(url_for('login'))

    return render_template('nova_receita.html')


@app.route('/cria_despesa')
def cria_despesa():
    # Verifica se o usuário está autenticado
    if 'id_usuario' not in session:
        flash('Você precisa estar logado no sistema.')
        return redirect(url_for('login'))

    return render_template('nova_despesa.html')


@app.route('/adiciona_despesa', methods=['POST'])
def adiciona_despesa():

    data = request.form
    nome = data['nome']
    valor_receita = data['valor_despesa']
    data_despesa = data['data']
    id_usuario = session['id_usuario']

    cursor = con.cursor()
    try:
        cursor.execute('select 1 from despesa where nome = ? and data = ? and id_usuario = ?', (nome, data_despesa, id_usuario))
        if cursor.fetchone() is not None:
            flash('Já existe despesa cadastrada para essa data, para corrigir edite a despesa.')
            return redirect(url_for('edita_despesa'))

        cursor.execute('INSERT INTO DESPESA(NOME, VALOR_DESPESA, DATA, ID_USUARIO) VALUES (?, ?, ?, ?)', (nome, valor_receita, data_despesa, id_usuario))
        con.commit()
        flash('Despesa adicionada com sucesso!')
        return redirect(url_for('inicio'))

    except Exception as e:
        flash(f'Falha ao cadastrar despesa! {e}')
        return redirect(url_for('cria_despesa'))
    finally:
        cursor.close()


@app.route('/adiciona_receita', methods=['POST'])
def adiciona_receita():
    data = request.form
    nome = data['nome']
    valor_receita = data['valor_receita']
    data_receita = data['data']
    id_usuario = session['id_usuario']


    cursor = con.cursor()
    try:
        # Verifica se já existe uma despesa para o mesmo nome e data
        cursor.execute('SELECT 1 FROM RECEITA WHERE nome = ? AND data = ? and id_usuario = ?', (nome, data_receita, id_usuario))
        if cursor.fetchone() is not None:
            flash('Já existe despesa cadastrada para essa data. Para corrigir, edite a despesa.')
            return redirect(url_for('edita_receita'))

        # Inserir nova receita
        cursor.execute('INSERT INTO RECEITA (NOME, VALOR_RECEITA, DATA, ID_USUARIO) VALUES (?, ?, ?, ?)', (nome, valor_receita, data_receita, id_usuario))
        con.commit()
        flash('Receita adicionada com sucesso!')
        return redirect(url_for('inicio'))

    except Exception as e:
        flash(f'Falha ao cadastrar Receita! {e}')
        return redirect(url_for('cria_receita'))

    finally:
        cursor.close()

@app.route('/lista_receitas', methods=['GET'])
def lista_receitas():
    # Verifica se o usuário está autenticado
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para adicionar uma despesa.')
        return redirect(url_for('login'))

    id_usuario = session['id_usuario']

    cursor = con.cursor()
    try:
        cursor.execute('SELECT id_receita, nome, valor_receita, data FROM receita WHERE id_usuario = ?', (id_usuario,))

        receitas = cursor.fetchall()  # Retorna todas as receitas como uma lista de tuplas
    finally:
        cursor.close()

    return render_template('lista_receita.html', receitas=receitas)



@app.route('/lista_despesas', methods=['GET'])
def lista_despesas():
    if 'id_usuario' not in session:
        flash('Você precisa estar logado para adicionar uma despesa.')
        return redirect(url_for('login'))

    id_usuario = session['id_usuario']
    # Verifica se o usuário está autenticado

    cursor = con.cursor()
    try:
        cursor.execute('SELECT id_despesa, nome, valor_despesa, data FROM despesa WHERE id_usuario = ?', (id_usuario,))

        despesas = cursor.fetchall()  # Retorna todas as despesas como uma lista de tuplas
    finally:
        cursor.close()

    return render_template('lista_despesa.html', despesas=despesas)


@app.route('/edita_receita/<int:id>', methods=['GET', 'POST'])
def edita_receita(id):
    try:
        id_usuario = session['id_usuario']
        cursor = con.cursor()
        if request.method == 'POST':
            # Obter os dados do formulário
            nome = request.form['nome']
            valor_receita = request.form['valor_receita']
            data_receita = request.form['data']


            # Atualiza a receita no banco de dados
            cursor.execute('UPDATE receita SET nome = ?, valor_receita = ?, data = ? WHERE id_receita = ? and id_usuario = ?', (nome, valor_receita,data_receita, id, id_usuario))
            flash('Receita atualizada com sucesso!')
            con.commit()
            cursor.close()

            # Redireciona para a lista de receitas após a edição
            return redirect(url_for('lista_receitas'))

        # Busca a receita pelo ID para editar
        cursor.execute('SELECT * FROM receita WHERE id_receita = ? and id_usuario = ?', (id, id_usuario))
        receita = cursor.fetchone()
        cursor.close()

        return render_template('edita_receita.html', receita=receita)
    except Exception as e:
        flash(f'Ocorreu um erro: {str(e)}', 'error')
        return redirect(url_for('lista_despesas'))

@app.route('/edita_despesa/<int:id>', methods=['GET', 'POST'])
def edita_despesa(id):
    try:
        id_usuario = session['id_usuario']
        cursor = con.cursor()

        if request.method == 'POST':
            # Obter os dados do formulário
            nome = request.form['nome']
            valor_despesa = request.form['valor_despesa']
            data_despesa = request.form['data']

            # Atualiza a despesa no banco de dados
            cursor.execute('UPDATE despesa SET nome = ?, valor_despesa = ?, data = ? WHERE id_despesa = ? AND id_usuario = ?',
                           (nome, valor_despesa, data_despesa, id, id_usuario))
            con.commit()
            flash('Receita atualizada com sucesso!', 'success')

            cursor.close()

            # Redireciona para a lista de despesas após a edição
            return redirect(url_for('lista_despesas'))

        # Busca a despesa pelo ID para editar
        cursor.execute('SELECT * FROM despesa WHERE id_despesa = ? AND id_usuario = ?', (id, id_usuario))
        despesa = cursor.fetchone()
        cursor.close()

        return render_template('edita_despesa.html', despesa=despesa)

    except Exception as e:
        flash(f'Ocorreu um erro: {str(e)}', 'error')
        return redirect(url_for('lista_despesas'))

@app.route('/exclui_receita/<int:id>', methods=['POST'])
def exclui_receita(id):
    try:
        id_usuario = session['id_usuario']
        cursor = con.cursor()

        # Exclui a despesa do banco de dados pelo ID
        cursor.execute('DELETE FROM receita WHERE id_receita = ? AND id_usuario = ?', (id, id_usuario))
        con.commit()

        flash('Receita excluída com sucesso', 'success')

    except Exception as e:
        con.rollback()  # Reverte qualquer alteração em caso de erro
        flash(f'Ocorreu um erro ao excluir a receita: {str(e)}', 'error')
        return redirect(url_for('cria_receita'))
    finally:
        cursor.close()

    # Redireciona para a lista de despesas após a exclusão ou erro
    return redirect(url_for('lista_receitas'))


@app.route('/exclui_despesa/<int:id>', methods=['POST'])
def exclui_despesa(id):
    try:
        id_usuario = session['id_usuario']
        cursor = con.cursor()

        # Exclui a despesa do banco de dados pelo ID
        cursor.execute('DELETE FROM despesa WHERE id_despesa = ? AND id_usuario = ?', (id, id_usuario))
        con.commit()

        flash('Despesa excluída com sucesso', 'success')

    except Exception as e:
        con.rollback()  # Reverte qualquer alteração em caso de erro
        flash(f'Ocorreu um erro ao excluir a despesa: {str(e)}', 'error')
        return redirect(url_for('cria_despesa'))
    finally:
        cursor.close()

    # Redireciona para a lista de despesas após a exclusão ou erro
    return redirect(url_for('lista_despesas'))

if __name__ == '__main__':
    app.run(debug=True)

