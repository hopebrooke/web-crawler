import requests
import time
import json
import os
from bs4 import BeautifulSoup
from queue import Queue
import nltk
from nltk.corpus import stopwords


# print menu
def viewMenu():
    print("""\n\nAvailable commands:
    Build crawler: 'build'
    Load index: 'load'
    Print index for a word: 'print <word>'
    Find word(s) and pages it occurs in: 'find <word> <word> ...'

    See this menu again: 'menu'
    Exit this application: 'quit' or 'exit'\n""")



# error message for an inavlid command
def invalid():
    print("\nThat is not a valid command. Please try again.")



# build 
def buildIndex():

    print("\n\nDownloading stopwords...")
    # download stopwords
    nltk.download('stopwords')
    
    print("\n\nBuilding index...\n")
    # initiate index 
    # (a dictionary where keys are the words, and the values are a dictionary of url, word count pairs)
    # eg. {'hello': {'www.h.com':[0,3,4], 'www.f.com':[0,1]}, 'fish':{'www.fish.com':[2,5,7], 'www.tropical.com':[4,5,6]}}
    inverted_index = {}

    # initiate request queue and add initial url    
    seed = 'https://quotes.toscrape.com'
    frontier = Queue()
    frontier.put(seed) 

    # create set of visited urls
    visited_urls = set()

    # loop while there are urls in request queue
    while not frontier.empty():
        
        # get next url
        current_url = frontier.get()

        # check if already visited
        if current_url in visited_urls:
            continue
        else:
            print("Visiting url: " + str(current_url))
        
        # add url to visited
        visited_urls.add(current_url)

        # parse page content
        response = requests.get(current_url)
        html_doc = response.text
        soup = BeautifulSoup(html_doc, 'html.parser')

        # get all urls in that page
        for link in soup.find_all('a'):
            url = link.get('href')
            # add to request queue url exists, is not already visited
            if url and url not in visited_urls:
                # make sure it is not an external site
                if url[0] == '/' and len(url) > 1:
                    frontier.put(seed+url)
                else:
                    continue

        # get text from page
        soup_text = soup.get_text()
        words = soup_text.split()

        # make everything lower case
        words = [word.lower() for word in words]
        # encode and decode to remove non ascii unicode:
        words = [word.encode('ascii', 'ignore').decode() for word in words]
        # remove some punctuation from strings
        words = [word.replace('"', '').replace(',','').replace('.','').replace('!', '').replace(':', '').replace('(', '').replace(')', '').replace('[', '').replace(']','').replace(';', '').replace('#', '').replace('?', '') for word in words]
        # remove numbers from strings
        for i in range (0, 10):
            words = [word.replace(str(i), '') for word in words]
        # remove all words less than two chars
        words = [word for word in words if len(word) > 2]
        # remove all stop words
        words = [word for word in words if word not in stopwords.words('english')]

        # store counter for word index on the page
        word_index = 0
        # loop through all words/tokens
        for word in words:
            if word not in inverted_index:                      # if word not in index then add token, url and first position
                inverted_index[word] = {current_url : [word_index]}
            else:                                       
                if current_url not in inverted_index[word]:     # if url not in word list then add url and first position to token list 
                    inverted_index[word][current_url] = [word_index]
                    
                else:                                           # if url already in word list, just add to count
                    inverted_index[word][current_url].append(word_index)   
            word_index += 1
            
        # observe politeness window
        print("\n"+str(len(visited_urls))+"/" + str(frontier.qsize()+len(visited_urls))+"\n" )
        time.sleep(6)   

    # write index to file
    with open('inverted_index.json', 'w') as file:
        json.dump(inverted_index, file)



# load 
def loadIndex():
    # load index from file and return it
    filename = 'inverted_index.json'
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            inverted_index = json.load(file)
        print("\nInverted index loaded succesfully.")
        return inverted_index
    else:
        print(f"\nThe file '{filename}' does not exist. Build the index first and try again.")
        return None



# print <word>
def printWord(word, inverted_index):
    # adjust word for searching index:
    word = word.lower()
    # encode and decode to remove non ascii unicode:
    word = word.encode('ascii', 'ignore').decode() 
    # remove some punctuation from string
    word.replace('"', '').replace(',','').replace('.','').replace('!', '').replace(':', '').replace('(', '').replace(')', '').replace('[', '').replace(']','').replace(';', '').replace('#', '').replace('?', '')
    # remove numbers from the string
    for i in range (0, 10):
        words = word.replace(str(i), '')
        
    # return error if stop word or less than two characters
    if len(word) <= 2 or word in stopwords.words('english'):
        print("\nPlease enter words longer than two characters that are not stopwords.")
        return
    
    # print inverted index if possible
    if word in inverted_index:
        print(inverted_index[word])
    else:
        print("\nThat word is not featured in any documents. Please try again.")



# find <word> <word>...
def findWords(words, inverted_index):

    # adjust words for searching index:
    # make everything lower case
    words = [word.lower() for word in words]
    # remove some punctuation from strings
    words = [word.replace('"', '').replace(',','').replace('.','').replace('!', '').replace(':', '').replace('(', '').replace(')', '').replace('[', '').replace(']','').replace(';', '').replace('#', '').replace('?', '') for word in words]
    # remove numbers from the string
    for i in range (0, 10):
        words = [word.replace(str(i), '') for word in words]
    
    # return error if words are stop words or less than two characters
    if any(len(word)<=2 for word in words) or any(word in stopwords.words('english') for word in words):
        print("\nRemoving words entered that are stopwords or less than two characters...")
        # remove all words less than two chars
        words = [word for word in words if len(word) > 2]
        # remove all stop words
        words = [word for word in words if word not in stopwords.words('english')]

    # get rid of any words not in index
    not_present = [word for word in words if word not in inverted_index]
    words = [word for word in words if word in inverted_index ]

    # if any words entered are not in index then print message
    if len(not_present) > 0 or len(words) == 0:
        # if no words left to search print error
        if len(words) == 0: 
            print("\nThe word(s) you have entered are not present in any documents. Please try again")
            return
         # if some words are not in index, inform user and continue
        else:
            print("\nThese word(s) you have entered are not present in any documents:")
            for word in not_present:
                print(">> " + word)
            print("Searching for the following:")
            for word in words:
                print(">> " + word)


    # dictionary to store new url and frequency counts
    order = []      # urls containing all words in order
    no_order = []   # urls containing all words no order
    not_all = []     # urls containing only some of the words
    not_all_lists = [[] for i in range(len(words))]  # list containing sublists of urls containing only some of the words. 
    #eg. list[0] is a list of urls containing n-1 words, list[1] is a list of urls containing n-2 of the words
    
    if len(words) == 1:
        # if only one word, set set_counts to the dictionary for that word
        urls = inverted_index[words[0]].keys()
        order += urls
    else:
        
        # add set of all urls for each word to the list
        url_sets = [set(inverted_index[word].keys()) for word in words]
        
        # if there are urls that contain all words, add to appropriate list
        mutual_urls = set.intersection(*url_sets)
        # add all urls with words to no order:
        no_order = list(set(mutual_urls))
        
        # if no urls containing all words, add urls that have any of them but not all
        all_urls = set()
        for url_set in url_sets:
            all_urls |= url_set
        # remove any mutual urls
        all_urls = all_urls - mutual_urls
        not_all = list(set(all_urls))
        
        # check for words in order
        # loop through urls that contain all words
        for url in mutual_urls:
            # get the indices of all the words in that url
            word_indices = []   # a list of list where each sublist is positions for each word
            for word in words:
                indices_list = inverted_index[word].get(url)
                word_indices.append(indices_list)
            # check if words exist in order in this url
            found = False
            # loop for every occurance of word in first url
            for i in range (len(word_indices[0])):
                # get position of first word
                first_index = word_indices[0][i]
                # keep a check of chain
                chain = True
                # loop for every word
                for j in range(1, len(words)):
                    # check that every following indice is found for the following words
                    next_word = first_index + j
                    if next_word not in word_indices[j]:
                        chain = False
                        break
                # check if a full chain found in this url
                if chain:
                    found = True
                    break
            # if chain found then add url to ordered rl list
            if found:
                order.append(url)
    
        # get rid of any urls with all words from not all words url list
        not_all = [url for url in not_all if url not in no_order]

        # remove any urls that have words in order from the list of urls with all words but not ordered
        no_order = [url for url in no_order if url not in order]

        # for not_all split into how many words are available
        for url in not_all:
            # get the number of words given that have that url present
            count = 0
            for word in words:
                if url in inverted_index[word].keys():
                    count +=1
            # do length of words minus that number for index
            index = len(words) - count
            # add urls in the index calculated
            not_all_lists[index].append(url)
        
    # organise different url lists by frequency 
    ordered_counts = {}
    not_ordered_counts = {}
    no_intersect_counts = [{} for i in range(len(not_all_lists))]   # list of dictionaries for sub urls

    # frequency for ordered:
    for url in order:
        ordered_counts[url] = 0
        for word in words:
            if url in inverted_index.get(word, {}):
                ordered_counts[url] += len(inverted_index[word][url])
    # frequency for not ordered:
    for url in no_order:
        not_ordered_counts[url] = 0
        for word in words:
            if url in inverted_index.get(word, {}):
                not_ordered_counts[url] += len(inverted_index[word][url])
    # frequency for not all words:
    for url in not_all:
        # calculate which sublist the url is in 
        for index in range(len(not_all_lists)):
            sublist = not_all_lists[index]
            if url in sublist:
                count = 0
                for word in words:
                    if url in inverted_index.get(word, {}):
                        count += len(inverted_index[word][url])
                no_intersect_counts[index][url] = count
                break

    # order urls by frequency
    sorted_order = sorted(ordered_counts.items(), key = lambda x:x[1], reverse = True) 
    sorted_no_order = sorted(not_ordered_counts.items(), key = lambda x:x[1], reverse = True) 
    sorted_not_all = [sorted(no_intersect_counts[i].items(), key = lambda x:x[1], reverse = True) for i in range(len(no_intersect_counts))]

    # formatting different for one word
    if len(words) == 1:
        print("\n--------------------------------\nDocuments containing "+ words[0] +" (in descending order of frequency):\n")
        for url_pairs in sorted_order:
            print(url_pairs[0])
        return
    
    # if multiple words, print what is found
    if sorted_order:
        # print in nice order
        print("\n--------------------------------\nDocuments containing all words next to each other (in descending order of frequency):\n")
        for url_pairs in sorted_order:
            print(url_pairs[0])
    else:
        print("\n--------------------------------\nNo documents contain all words next to each other.")
        
    if sorted_no_order:   
        print("\n--------------------------------\nDocuments containing all words that do not occur next to each other (in descending order of frequency):\n")
        for url_pairs in sorted_no_order:
            print(url_pairs[0])
    else:
        print("\n--------------------------------\nNo documents contain all words that do not occur next to each other.")
    
    # loop through for different numbers of word subsections
    if sorted_not_all:
        for i in range(len(sorted_not_all)-1):
            if len(sorted_not_all[i+1]) > 0:
                print("\n--------------------------------\nDocuments containing " + str(len(words)-i-1)+" word(s) found (in descending order of frequency):\n")
                for url_pairs in sorted_not_all[i+1]:
                    print(url_pairs[0])
            else:
                print("\n--------------------------------\nNo documents contain " + str(len(words)-i-1)+" word(s) entered.")
    else:
        print("\n--------------------------------\nNo documents contain some words entered.")

    print("\n--------------------------------\n")



# Parser command line commands
def main():
    
    print("\nWelcome to this web crawler!")
    viewMenu()

    inverted_index = None   # this will be defined when file is loaded
    
    # loop until exit
    while True:
        # take user input
        userInput = input("\n>> ")
        # check for exit
        if userInput.lower() == 'exit' or userInput.lower() == 'quit':
            break
        if len(userInput) < 1:
            continue
        
        # parse the arguments
        args = userInput.split()
        command = args[0].lower()

        # command form : 'build'
        if command == 'build' and len(args) == 1:
            buildIndex()
        # command form: 'load'
        elif command == 'load' and len(args) == 1:
            inverted_index = loadIndex()
        # command form: 'print <word>'    ->    index must be loaded first
        elif command == 'print' and len(args) == 2:
            if inverted_index is not None:
                printWord(args[1], inverted_index)
            else:
                print("\nPlease load the index first and try again.")
        # command form: 'find <word> [<word>...]'   ->  index must be loaded first
        elif command == 'find' and len(args) > 1:
            if inverted_index is not None:
                args.pop(0)     # remove the find command
                findWords(args, inverted_index)
            else:
                print("\nPlease load the index first and try again.")
        # command form: 'menu'
        elif command == 'menu':
            viewMenu()
        else:
            invalid()
            print("\nEnter 'menu' to view the menu again.")


if __name__ == '__main__':
    main()

