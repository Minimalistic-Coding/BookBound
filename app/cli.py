import os
import click
from app.utils.write_to_db import scrape_data, save_data
from flask import Blueprint

bp = Blueprint('cli', __name__, cli_group=None)

#Flask Babel Command Line Tools

@bp.cli.group()
def translate():
	"""Translation and localization comands."""
	pass

@translate.command()
def update():
	"""Update all languages."""
	if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
		raise RuntimeError('extract command failed')
	if os.system('pybabel update -i messages.pot -d app/translations'):
		raise RuntimeError('update command failed')
	os.remove('messages.pot')

@translate.command()
def compile():
	"""Compile all languages"""
	if os.system('pybabel compile -d app/translations'):
		raise RuntimeError('compile command failed')

@translate.command()
@click.argument('lang')
def init(lang):
	"""Initialize a new language."""
	if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
		raise RuntimeError('extract command failed')

	if os.system('pybabel init -i messages.pot -d app/translations -l ' + lang):
		raise RuntimeError('init command failed')
	os.remove('messages.pot')


#Saving books to db tools

@bp.cli.group()
def book():
	"""Scrape books data from BooksToScrape and Saves it to MySQL database"""
	pass

@book.command()
def save():
	"""Write the Scraped data to DataBase"""
	data = scrape_data()
	save_data(data)