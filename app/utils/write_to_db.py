from app.services.bookscraper import scraper
from app.models import Book
from app import db
from sqlalchemy import select, exists

"""
{'name': "It's Only the Himalayas", 
'price': 45.17, 
'rating': 2, 
'availabilty': 10, 
'description': '“Wherever you go, whatever you do, just . . . don’t do anything stupid.” —My MotherDuring her yearlong adventure backpacking from South Africa to Singapore, S. Bedford definitely did a few things her mother might classify as "stupid." She swam with great white sharks in South Africa, ran from lions in Zimbabwe, climbed a Himalayan mountain without training in Nepal, and wa “Wherever you go, whatever you do, just . . . don’t do anything stupid.” —My MotherDuring her yearlong adventure backpacking from South Africa to Singapore, S. Bedford definitely did a few things her mother might classify as "stupid." She swam with great white sharks in South Africa, ran from lions in Zimbabwe, climbed a Himalayan mountain without training in Nepal, and watched as her friend was attacked by a monkey in Indonesia.But interspersed in those slightly more crazy moments, Sue Bedfored and her friend "Sara the Stoic" experienced the sights, sounds, life, and culture of fifteen countries. Joined along the way by a few friends and their aging fathers here and there, Sue and Sara experience the trip of a 
lifetime. They fall in love with the world, cultivate an appreciation for home, and discover who, or what, they want to become.It\'s Only the Himalayas is the incredibly funny, sometimes outlandish, always entertaining confession of a young backpacker that will inspire you to take your own adventure. ', 
'cover': 'https://books.toscrape.com/media/cache/6d/41/6d418a73cc7d4ecfd75ca11d854041db.jpg'}   
"""
def scrape_data():
	total_books = Book.query.count()

	last_page = (total_books // 20) + 1

	books_gen = []
	for idx in range(last_page, last_page + 6):
		data = scraper(idx)
		books_gen.append(data)

	return books_gen

def save_data(data_gen):
	try:
		for data in data_gen:
			if not data:
				raise ValueError("Scraper returned no data!")

			for book in data:
				book_title = book.get("name")
				book_price = book.get("price")
				book_rating = book.get("rating")
				book_availability = book.get("availability")
				book_description = book.get("description")
				book_cover = book.get("cover")

				#Check if Book Exists
				# existence = select(Book).filter_by(title=book_title).exists().scalar()
				existence = db.session.execute(db.select(Book).filter_by(title=book_title)).scalar_one_or_none()

				if not existence:
					book_obj = Book(title=book_title,
									price=book_price,
									rating=book_rating,
									availability=book_availability,
									description=book_description,
									cover=book_cover)
					if book_obj:
						try:
							db.session.add(book_obj)
						except Exception as e:
							print(f"ERROR : {e}")
							continue
			
		db.session.commit()
		print("All Pages Saved Successfully!")
				
	except Exception as e:
		db.session.rollback()
		print(f"ERROR : {e}. No books were saved.")