import os
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv(encoding="utf-8") 

# --- CONFIGURAÇÃO INICIAL ---
app = Flask(__name__)
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@host/db')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# --- TABELAS DE JUNÇÃO (Muitos-para-Muitos) ---
spell_schools_table = db.Table('spell_schools',
    db.Column('spell_id', db.Integer, db.ForeignKey('spells.id'), primary_key=True),
    db.Column('school_id', db.Integer, db.ForeignKey('schools.id'), primary_key=True)
)

# Nota: A tabela de junção para pré-requisitos lógicos (por ID) não é usada neste modelo,
# mas pode ser implementada no futuro se você migrar os dados do array de texto.


# --- MODELS (MAPEAMENTO DAS TABELAS DE MAGIAS) ---

class School(db.Model):
    __tablename__ = 'schools'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    parent_school_id = db.Column(db.Integer, db.ForeignKey('schools.id'))

class SpellType(db.Model):
    __tablename__ = 'spell_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)

class Spell(db.Model):
    __tablename__ = 'spells'
    id = db.Column(db.Integer, primary_key=True)
    name_unique = db.Column(db.String(255), unique=True, nullable=False)
    spell_type_id = db.Column(db.Integer, db.ForeignKey('spell_types.id'), nullable=False)
    resisted_by = db.Column(db.String(255))
    is_very_hard = db.Column(db.Boolean, nullable=False, default=False)
    cost_numeric = db.Column(db.Integer)
    magery_level = db.Column(db.Integer, nullable=False, default=0)
    casting_time_text = db.Column(db.Text)
    duration_text = db.Column(db.Text)
    reference = db.Column(db.String(100))
    
    # <<< LINHA ADICIONADA PARA COMPATIBILIDADE 100% >>>
    # Mapeia a coluna prerequisites TEXT[] do banco de dados.
    prerequisites = db.Column(db.ARRAY(db.Text))

    # Relações
    spell_type = db.relationship('SpellType', lazy='joined')
    schools = db.relationship('School', secondary=spell_schools_table, backref='spells', lazy='joined')
    translations = db.relationship('SpellTranslation', backref='spell', cascade="all, delete-orphan", lazy='joined')
    
class SpellTranslation(db.Model):
    __tablename__ = 'spell_translations'
    id = db.Column(db.Integer, primary_key=True)
    spell_id = db.Column(db.Integer, db.ForeignKey('spells.id'), nullable=False)
    lang_code = db.Column(db.String(5), nullable=False, default='pt-BR')
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    cost_text = db.Column(db.Text)
    maintenance_cost_text = db.Column(db.Text)
    item_description = db.Column(db.Text)
    prerequisites_text = db.Column(db.Text)


# --- FUNÇÕES AUXILIARES ---

def serialize_spell(spell, lang_code):
    """Converte um objeto Spell em um dicionário serializável para a API."""
    translation = next((t for t in spell.translations if t.lang_code == lang_code), None)
    if not translation:
        return None

    return {
        'id': spell.id,
        'name_unique': spell.name_unique,
        'name': translation.name,
        'description': translation.description,
        'cost_text': translation.cost_text,
        'maintenance_cost_text': translation.maintenance_cost_text,
        'casting_time': spell.casting_time_text,
        'duration': spell.duration_text,
        'schools': [school.name for school in spell.schools],
        'type': spell.spell_type.name,
        # Usamos o prerequisites_text para exibição, que já está na tabela de tradução
        'prerequisites_obj': [], # Deixado vazio, pois a lógica agora é baseada em texto
        'prerequisites_text': translation.prerequisites_text,
        'item_description': translation.item_description,
        'reference': spell.reference,
    }

# --- ROTAS DA APLICAÇÃO ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/filtros')
def api_filtros():
    escolas = [school.name for school in School.query.order_by(School.name).all()]
    tipos = [spell_type.name for spell_type in SpellType.query.order_by(SpellType.name).all()]
    return jsonify({'escolas': escolas, 'tipos': tipos})

@app.route('/api/magias/<lang>')
def api_magias(lang):
    page = request.args.get('page', 1, type=int)
    per_page = 50
    sort_key = request.args.get('sort', 'id')
    lang_code = 'pt-BR' if lang == 'pt' else 'en-US'
    
    school_filter = request.args.get('school')
    type_filter = request.args.get('type')

    ALLOWED_SORT_FIELDS = {
        'name': SpellTranslation.name,
        'cost': Spell.cost_numeric,
        'magery': Spell.magery_level,
        'id': Spell.id
    }
    order_column = ALLOWED_SORT_FIELDS.get(sort_key, Spell.id)

    query = db.session.query(Spell)

    if sort_key == 'name':
        query = query.join(SpellTranslation).filter(SpellTranslation.lang_code == lang_code)
    
    if school_filter:
        query = query.join(Spell.schools).filter(School.name == school_filter)
    if type_filter:
        query = query.join(Spell.spell_type).filter(SpellType.name == type_filter)
    
    query = query.order_by(order_column)
    
    query = query.options(
        joinedload(Spell.translations),
        joinedload(Spell.schools),
        joinedload(Spell.spell_type)
    )

    paginated_results = query.paginate(page=page, per_page=per_page, error_out=False)
    spells_on_page = paginated_results.items
    
    serialized_spells = [s for s in [serialize_spell(spell, lang_code) for spell in spells_on_page] if s is not None]

    return jsonify({
        'spells': serialized_spells,
        'pagination': {
            'page': paginated_results.page,
            'per_page': paginated_results.per_page,
            'total_pages': paginated_results.pages,
            'total_items': paginated_results.total,
            'has_next': paginated_results.has_next,
            'has_prev': paginated_results.has_prev
        }
    })

if __name__ == '__main__':
    app.run(debug=True)

