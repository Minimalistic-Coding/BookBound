from bs4 import BeautifulSoup
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import random
# from email_sender import Email, Client

def requester(url=None):

	base_url = "https://books.toscrape.com/"

	source_url = base_url

	if url:
		source_url = base_url + url

	try:
		response = requests.get(source_url)
		if response.ok:
			response.encoding = "utf-8"
			return response.text
	except:
		return None

def scraper(page_num):

	local_url = "https://books.toscrape.com"

	soup = BeautifulSoup(requester(), 'lxml')

	total_pages = soup.find("li", class_="current").text.strip()[-2:]

	if 0 < page_num <= int(total_pages):

		page_link = f"catalogue/page-{page_num}.html"

	else:
		print("Page Number input is greater than total pages!")
		return

	response = requester(page_link)

	soup = BeautifulSoup(response, 'lxml')

	if not response:
		return

	all_books = soup.find_all("li", class_="col-xs-6 col-sm-4 col-md-3 col-lg-3")

	all_books = [f"catalogue/{link.a.get('href')}" for link in all_books]

	with ThreadPoolExecutor() as exe:
		print(f"PAGE-{page_num} | [BOOKS] Fetching {len(all_books)} book pages in parallel...")
		resultant_response = exe.map(requester, all_books)

	for url in resultant_response:
		if not url:
			continue

		book = BeautifulSoup(url, 'lxml')

		# Scraping Book Name, Price, Availability, Rating:
		try:
			book_info = book.find("div", "col-sm-6 product_main")
			book_name = book_info.h1.text
			book_price = book_info.find('p', class_="price_color").text
			# availabilty = book.find("p", class_= "instock availability").text.strip()
			rating = book.find("p", class_="star-rating").get('class')[-1:]
			rating = rating[0]
		except:
			if book_info is None:
				book_name = None
				book_price = None
				availabilty = None
				rating = None

		# Scraping Book's Description:
		try:
			book_description = book.find("div", id="product_description")
			if book_description:
				book_description = book_description.find_next_sibling().text[:-7]
		except:
			book_description = None

		# Scraping Book Image URL
		try:
			book_image = book.find('div', class_="item active").img.get("src")
			if book_image:
				book_image = book_image.split('.')[-2:]
				book_image = ".".join(book_image)
				book_image = local_url + book_image
		except:
			book_image = None

		try:
			float_book_price = float(book_price.split("£")[1])   #'price': '£51.77'
		except:
			float_book_price = None

		try:
			#'rating': 'Three'
			int_rating = None
			match rating:
				case 'One':
					int_rating = 1  
				case 'Two':
					int_rating = 2
				case 'Three':
					int_rating = 3
				case 'Four':
					int_rating = 4
				case 'Five':
					int_rating = 5 
		except:
			int_rating = None

		book_data = {
			'name': book_name,
			'price': float_book_price,
			'rating': int_rating,
			'availability': random.randint(0, 35),
			'description': book_description,
			'cover': book_image
		}

		yield book_data
		
# def main_scraper(response, page_num):
# 	if not response:
# 		return

# 	soup = BeautifulSoup(response, 'lxml')

# 	total_pages = soup.find("li", class_="current").text.strip()[-2:]

# 	if 0 < page_num <= int(total_pages):

# 		page_links = f"catalogue/page-{page_num}.html"

# 		with ThreadPoolExecutor() as exe:
# 			print(f"\n[INFO] Fetching Page No. {len(page_links)} \n")
# 			# future_to_page = {exe.submit(requester, url): url for url in page_links}
# 			# for future in as_completed(future_to_page):
# 			# 	page_url = future_to_page[future]
# 			# 	page_response = future.result()
# 			# 	yield from scraper(page_response)


if __name__ == "__main__":
	data = scraper(2)
	for book in data:
		print(book)

# def saver(scraped_data):

# 	if not scraped_data:
# 		print("No data found to scrape!")
# 		return
	
# 	with open("scraped_books.json", "w") as wf:
# 		books = []
# 		for book in scraped_data:	
# 			books.append(book)
# 		json.dump(books, wf, indent=6, ensure_ascii=False)
# 		print("successfully saved data!")

# if __name__ == "__main__":
# 	scraped_data = main_scraper(requester(), 1)
# 	saver(scraped_data)
# 	email_msg = Email("joshuaimran0000@gmail.com", ["joshuaimran6969@gmail.com", "joshuaimran666@gmail.com"])
# 	email_msg.basic_construct("Hey, Check Out the Scraped content!", "As u requested, i scraped the content fom the 'books-to-scrape' website, and saved it to a json, i attached the file with this so check it out")
# 	email_msg.add_attachment(files=True)

# 	client = Client()
# 	client.send_email(email_msg)

# scraped_data = main_scraper(requester())
# count = 0
# for book in scraped_data:
#     count += 1
#     if count % 10 == 0:
#         print(f"    [PROGRESS] {count} books scraped...")

# print(f"\n[RESULT] Total Books Scraped: {count}")

"""
FOR SCRAPER - #DONE:
1. Scraper will take in the response for the whole page of books - #DONE
2. It will Store all the book's about-link into a list - #DONE
3. then it will request those using Threads and will scrape info for each link - #DONE
4. it will then store(try to make it store as a generator) those results - #DONE
5. then it will return that scraped data - #DONE


FOR PAGINATION:
1. Make another Function which scrapes the link to the next page + the total pages - #DONE
2. Use that data to request the next pages using threads and passing the response of each page to scraper - #DONE


FOR MAIN:
1. Write a main function which takes in all those processes and then keeps storing data to a main variable
2. It is used to return a generator object to yield the scraped data one by one ensuring memory optimization
#---> NOT NEEDED ANYMORE

FOR SAVING:
1. Make another function which takes in a generator object which saves each of the iteration to JSON
"""