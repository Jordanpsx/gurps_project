from flask import Flask, jsonify, render_template, request # Importe o 'request'
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Jordanps2@localhost:5432/gurps_db?client_encoding=utf8'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELO DA TABELA ---
class Spell(db.Model):
    __tablename__ = 'spells'
    id = db.Column(db.Integer, primary_key=True)
    school = db.Column(ARRAY(db.String))
    prerequisites = db.Column(ARRAY(db.Text))
    # ... (cole aqui o resto das suas colunas do model)
    name_en = db.Column(db.String, nullable=False); name_pt = db.Column(db.String, nullable=False); cost = db.Column(db.String); cost_pt = db.Column(db.String); maintenance_cost = db.Column(db.String); maintenance_cost_pt = db.Column(db.String); description_en = db.Column(db.Text); description_pt = db.Column(db.Text); duration_en = db.Column(db.String); duration_pt = db.Column(db.String); range_en = db.Column(db.String); range_pt = db.Column(db.String); resisted_by = db.Column(db.String); spell_type = db.Column(db.String); is_very_hard = db.Column(db.Boolean, default=False); item_en = db.Column(db.Text); item_pt = db.Column(db.Text); creation_cost = db.Column(db.String); conjuration_time = db.Column(db.String); conjuration_time_pt = db.Column(db.String); reference = db.Column(db.String)
    
    def to_dict(self, lang='pt'):
        # ... (cole aqui sua função to_dict completa)
        escolas_str = ', '.join(self.school) if self.school else 'Nenhuma'; prereqs_str = ', '.join(self.prerequisites) if self.prerequisites else 'Nenhum'
        if lang == 'en': return { 'id': self.id, 'nome': self.name_en, 'descricao': self.description_en, 'custo': f"{self.cost} (Maint: {self.maintenance_cost or 'N/A'})", 'duracao': self.duration_en, 'tempo_conjuracao': self.conjuration_time, 'escola_display': escolas_str, 'escola': self.school, 'tipo': self.spell_type, 'pre_requisitos': prereqs_str, 'referencia': self.reference }
        else: return { 'id': self.id, 'nome': self.name_pt, 'descricao': self.description_pt, 'custo': f"{self.cost_pt} (Manut: {self.maintenance_cost_pt or 'N/A'})", 'duracao': self.duration_pt, 'tempo_conjuracao': self.conjuration_time_pt or self.conjuration_time, 'escola_display': escolas_str, 'escola': self.school, 'tipo': self.spell_type, 'pre_requisitos': prereqs_str, 'referencia': self.reference }

# --- ROTA PRINCIPAL ---
@app.route('/')
def index():
    return render_template('index.html')

# --- API QUE ENTREGA OS DADOS ---
@app.route('/api/magias/<lang>')
def api_magias(lang):
    try:
        # Pega o parâmetro 'sort' da URL. Se não vier, o padrão é 'id'.
        sort_by = request.args.get('sort', 'id')

        # Mapeia os valores do front-end para as colunas do banco
        if sort_by == 'custo':
            # Ordena pelo custo em português, tratando a coluna de texto como número
            order_column = db.cast(Spell.cost_pt, db.Integer)
        elif sort_by == 'nome':
            order_column = Spell.name_pt
        else: # Padrão é ordenar por ID (ordem do livro)
            order_column = Spell.id

        # A consulta agora usa a coluna de ordenação dinâmica
        spells_from_db = Spell.query.order_by(order_column).all()
        
        lista_magias_formatada = [spell.to_dict(lang) for spell in spells_from_db]
        return jsonify(lista_magias_formatada)
    except Exception as e:
        print(f"ERRO NA API: {e}")
        return jsonify({"erro": f"Ocorreu um erro ao buscar os dados: {e}"}), 500

# --- INICIALIZador do servidor ---
if __name__ == '__main__':
    app.run(debug=True)