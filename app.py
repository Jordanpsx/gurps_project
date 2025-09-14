import os
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
# Especificar a codificação é uma boa prática para evitar erros em diferentes SOs
load_dotenv(encoding="utf-8") 

# --- CONFIGURAÇÃO INICIAL ---
app = Flask(__name__)
# Lê a string de conexão do banco de dados a partir das variáveis de ambiente
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@host/db')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# --- TABELAS DE JUNÇÃO (Muitos-para-Muitos) ---
spell_schools_table = db.Table('spell_schools',
    db.Column('spell_id', db.Integer, db.ForeignKey('spells.id'), primary_key=True),
    db.Column('school_id', db.Integer, db.ForeignKey('schools.id'), primary_key=True)
)

spell_prerequisites_table = db.Table('spell_prerequisites',
    db.Column('spell_id', db.Integer, db.ForeignKey('spells.id'), primary_key=True),
    db.Column('prerequisite_spell_id', db.Integer, db.ForeignKey('spells.id'), primary_key=True)
)


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
    
    # Relações
    spell_type = db.relationship('SpellType', lazy='joined')
    schools = db.relationship('School', secondary=spell_schools_table, backref='spells', lazy='joined')
    translations = db.relationship('SpellTranslation', backref='spell', cascade="all, delete-orphan", lazy='joined')
    prerequisites = db.relationship('Spell', secondary=spell_prerequisites_table,
                                     primaryjoin=id==spell_prerequisites_table.c.spell_id,
                                     secondaryjoin=id==spell_prerequisites_table.c.prerequisite_spell_id,
                                     backref='prerequisite_for', lazy='joined')

class SpellTranslation(db.Model):
    __tablename__ = 'spell_translations'
    # Ajuste para usar a geração de ID padrão do SQLAlchemy
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

    prereqs_list = []
    for prereq_spell in spell.prerequisites:
        prereq_translation = next((t for t in prereq_spell.translations if t.lang_code == lang_code), None)
        if prereq_translation:
            prereqs_list.append({
                'name': prereq_translation.name,
                'name_unique': prereq_spell.name_unique
            })

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
        'prerequisites_obj': prereqs_list,
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
    sort_key = request.args.get('sort', 'id') # 'id' como padrão
    lang_code = 'pt-BR' if lang == 'pt' else 'en-US'
    
    school_filter = request.args.get('school')
    type_filter = request.args.get('type')

    # Mapeamento seguro de chaves de ordenação para colunas do SQLAlchemy
    ALLOWED_SORT_FIELDS = {
        'name': SpellTranslation.name,
        'cost': Spell.cost_numeric,
        'magery': Spell.magery_level,
        'id': Spell.id
    }
    order_column = ALLOWED_SORT_FIELDS.get(sort_key, Spell.id)

    query = db.session.query(Spell)

    # Aplica joins apenas quando necessário para filtros ou ordenação
    if sort_key == 'name':
        query = query.join(SpellTranslation).filter(SpellTranslation.lang_code == lang_code)
    
    if school_filter:
        query = query.join(Spell.schools).filter(School.name == school_filter)
    if type_filter:
        # Garante que o join na tradução exista antes de filtrar pelo tipo, caso não tenha sido feito antes
        if 'spelltranslation' not in [c.entity.name for c in query._join_entities]:
             query = query.join(SpellTranslation).filter(SpellTranslation.lang_code == lang_code)
        query = query.join(Spell.spell_type).filter(SpellType.name == type_filter)
    
    query = query.order_by(order_column)
    
    # Usando eager loading para otimizar o carregamento de dados relacionados
    query = query.options(
        joinedload(Spell.translations),
        joinedload(Spell.schools),
        joinedload(Spell.spell_type),
        joinedload(Spell.prerequisites).joinedload(Spell.translations)
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
```

### Próximos Passos:

1.  **Crie o arquivo `.env`** na raiz do seu projeto com a sua `DATABASE_URL`.
2.  **Instale as dependências** no seu ambiente virtual:
    ```bash
    pip install Flask Flask-SQLAlchemy psycopg2-binary python-dotenv
    

