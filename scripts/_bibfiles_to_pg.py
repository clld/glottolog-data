# _bifiles_to_pg.py - load bibfiles into postgres 9.4 database for inspection

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

import _bibfiles
import _bibtex

DB = 'postgresql://postgres@/bibfiles'

BIBFILES = _bibfiles.Collection()


class Entry(declarative_base()):

    __tablename__ = 'entry'

    pk = sa.Column(sa.Integer, primary_key=True)
    filename = sa.Column(sa.Text, nullable=False)
    bibkey = sa.Column(sa.Text, nullable=False)
    entrytype = sa.Column(sa.Text, nullable=False)
    fields = sa.Column(JSONB, nullable=False)
    glottolog_ref_id = sa.Column(sa.Integer)
    author = sa.Column(sa.Text)
    editor = sa.Column(sa.Text)
    year = sa.Column(sa.Text)
    title = sa.Column(sa.Text)

    __table_args__ = (sa.UniqueConstraint(filename, bibkey),)


class Contributor(Entry.__base__):

    __tablename__ = 'entrycontrib'

    entry_pk = sa.Column(sa.Integer, sa.ForeignKey('entry.pk'), primary_key=True)
    role = sa.Column(sa.Text, primary_key=True)
    index = sa.Column(sa.Integer, primary_key=True)
    prelast = sa.Column(sa.Text, nullable=False)
    last = sa.Column(sa.Text, nullable=False)
    given = sa.Column(sa.Text, nullable=False)
    lineage = sa.Column(sa.Text, nullable=False)


engine = sa.create_engine(DB)
Entry.metadata.drop_all(engine)
Entry.metadata.create_all(engine)


for b in BIBFILES:
    print(b.filepath)
    with engine.begin() as conn:
        insert_entry = Entry.__table__.insert(bind=conn).execute
        insert_contrib = Contributor.__table__.insert(bind=conn).execute
        for bibkey, (entrytype, fields) in b.iterentries():
            pk, = insert_entry(filename=b.filename, bibkey=bibkey,
                entrytype=entrytype, fields=fields,
                glottolog_ref_id=fields.get('glottolog_ref_id'),
                author=fields.get('author'), editor=fields.get('editor'),
                year=fields.get('year'), title=fields.get('title')
                ).inserted_primary_key
            contribs = [{'entry_pk': pk, 'role': role, 'index': i,
                'prelast': prelast, 'last': last, 'given': given,
                'lineage': lineage}
                for role in ('author', 'editor')
                for i, (prelast, last, given, lineage)
                in enumerate(_bibtex.names(fields.get(role, '')), 1)]
            if contribs:
                insert_contrib(contribs)
