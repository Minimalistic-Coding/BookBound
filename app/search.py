from flask import current_app

def add_to_index(index, model):
	if not current_app.elasticsearch:
		return

	payload = {}

	for field in model.__searchable__:
		payload[field] = getattr(model, field)

	current_app.elasticsearch.index(index=index, id=model.id, document=payload)

def remove_from_index(index, model):
	if not current_app.elasticsearch:
		return
	current_app.elasticsearch.delete(index=index, id=model.id)

def query_index(index, query, page, per_page):
	if not current_app.elasticsearch:
		return [], 0

	main_query = {
		'bool': {
			'should': [
				{'multi_match': {'query': query, 'fields': None, 'fuzziness': 'AUTO'}}
			]
		}
	}

	if index == 'books':
		subquery_list = main_query['bool']['should']

		subquery_list[0]['multi_match']['fields'] = ['title^3', 'description']
		wc1 = {'wildcard': {'title': f'*{query.lower()}*'}}
		wc2 = {'wildcard': {'description': f'*{query.lower()}*'}}
		subquery_list.extend([wc1, wc2])

	elif index == 'users':
		subquery_list = main_query['bool']['should']

		subquery_list[0]['multi_match']['fields'] = ['username^2']
		subquery_list.append({'wildcard': {'username': f'*{query.lower()}*'}})
	else:
		main_query['bool']['should'][0]['multi_match']['fields'] = ['*']

	search = current_app.elasticsearch.search(
			index=index,
			query=main_query,
			from_ = (page - 1) * per_page,
			size=per_page
		)
	ids = [int(hit['_id']) for hit in search['hits']['hits']]
	return ids, search['hits']['total']['value']