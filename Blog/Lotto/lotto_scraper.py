from bs4 import BeautifulSoup
import pandas as pd
import re

# Here is where we will begin scraping
domain = "http://lottoresults.co.nz"
archive_url = domain + "/lotto/archive"

def read_url(url):
    # This reads in a url and returns a BeautifulSoup object. 
    # It also catches errors if something goes wrong
    from urllib.request import urlopen
    from urllib.error import HTTPError
    from time import sleep

    # sleep 1 second
    sleep(1)
    try:
        html = urlopen(url)
    except HTTPError as e:
        print(e)
        return None
    try:
        soup = BeautifulSoup(html.read(), "lxml")
    except AttributeError as e:
        print(e)
        return None
    return soup

# Pull the lotto archive
print("Accessing %s" %archive_url)
archive_soup = read_url(archive_url)

# Pull the tags for each month from the archive
month_tags = archive_soup.findAll("a", href=re.compile("/lotto/[a-z]+-\d+"))
# Extract the links for each month
month_links = [domain + tag.get("href") for tag in month_tags]
month_links.reverse()

results_dict = {}

for month_link in month_links:
	# Pull the data for a given month
	month_soup = read_url(month_link)

	# Isolate the result-cards for each draw 
	result_card_tags = month_soup.findAll("div", {"class":"result-card"})

	for result_card_tag in result_card_tags:
		# Instantiate dictionary for results data
		result_dict = {}

		# get link and title
		result_dict['link']  = domain + result_card_tag.find("a").get("href")
		result_dict['title'] = result_card_tag.h2.get_text()

		print("\rReading: %s" %result_dict['title'], end="")

		# get tags for details of each draw result 
		detail_tags = result_card_tag.findAll("li", {"class":"result-meta__title"})

		# get draw number and jackpot from detail_tags
		for detail_tag in detail_tags:
			if 'draw number' in detail_tag.get_text().lower():
				result_dict['draw number'] = detail_tag.span.get_text()
			elif 'jackpot' in detail_tag.get_text().lower():
				result_dict['jackpot'] = detail_tag.span.get_text()

		# extract tags for the result of the draw
		draw_result_tags = result_card_tag.findAll("ol", {"class":"draw-result"})

		for tag in draw_result_tags:
			# extract the numbers for the result
			nums = re.findall(r"\d+", tag.get_text())

			if len(nums) == 7:
				# if there are 7 numbers, first 6 are the lotto result
				# and the last is the bonus ball
				result_dict["bonus ball"]   = nums.pop()
				result_dict["lotto result"] = nums
			elif len(nums) == 4:
				# if there are 4 numbers, then it is a strike result
				result_dict["strike"]       = nums
			elif len(nums) == 1:
				# if there is only one number, then it is the powerball
				result_dict["powerball"]    = nums[0]

		# Now we use the link to fetch the soup for the detailed results
		result_soup = read_url(result_dict['link'])

		# Get the detailed results for the draw
		draw_details = result_soup.findAll("ul", {"class":"draw-details-meta"})
		
		# If no details are found, pass to next iteration of loop
		if draw_details == []:
			results_dict[result_dict["draw number"]] = result_dict
			break

		# Get the total prize pool, number of winners and average prize per winner
		draw_details = draw_details[0]
		for tag in draw_details.findAll("li"):
			text = tag.get_text()
			append_text = text.rsplit(" ",1)[-1]

			if 'total prize pool' in text.lower():
				result_dict['prize pool']    = append_text

			elif 'number of winners' in text.lower():
				result_dict['winner count']  = append_text

			elif 'average prize per winner' in text.lower():
				result_dict['average prize'] = append_text


		# Now extract the soup containing the data tables:
		table_soup = result_soup.findAll("table")[0]
		row_soups  =  table_soup.findAll("tr", {"data-row":re.compile("\d")})

		for row_soup in row_soups:
			cols = ["Division", "Matches", "Winners", "Prize"]
			result_dict["lotto divisions"]     = pd.DataFrame([], columns = cols)
			result_dict["powerball divisions"] = pd.DataFrame([], columns = cols)
			result_dict["strike divisions"]    = pd.DataFrame([], columns = cols)

			row_text = row_soup.get_text()
			row = [text for text in row_text.split("\n") if text != ""]

			if 'powerball' in row_text.lower():
			    label = 'powerball divisions'
			elif 'exact order' in row_text.lower():
			    label = 'strike divisions'
			else:
			    label = 'lotto divisions'

			length = len(result_dict[label])
			result_dict[label].loc[length] = row

		# Add result to results_dict
		results_dict[result_dict["draw number"]] = result_dict

# Save results_dict to .json file
import json
print("Saving results to json file...")
with open('results_dict.json', 'w') as fp:
    json.dump(results_dict, fp)
print("Saved!")