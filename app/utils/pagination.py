from flask import url_for, request
from flask import current_app
from app import db

# page = request.args.get("page", 1, type=int)
# books = db.paginate(Book.query, page=page, per_page=app.config['COMMENTS_PER_PAGE'], error_out=False)

# next_url = url_for('/index', page=books.next_num) if books.has_next else None
# prev_url = url_for('/index', page=books.prev_num) if books.has_prev else None

# return render_template('index.html', title='Home', books=books.items, next_url=next_url, prev_url=prev_url)

def paginate_elements(query, endpoint, error_output=False, generate_links=True, **kwargs):
	page = request.args.get("page", 1, type=int)
	elements = db.paginate(query, page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=error_output)
	if not generate_links:
		return elements

	next_url = url_for(endpoint, page=elements.next_num, **kwargs) if elements.has_next else None
	prev_url = url_for(endpoint, page=elements.prev_num, **kwargs) if elements.has_prev else None
	return elements, next_url, prev_url