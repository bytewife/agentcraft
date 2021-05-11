import src.agent

chronicle = ""

chronicle_events = {
    src.agent.Agent.Motive.LOGGING.name: {"going": [],},
    src.agent.Agent.Motive.BUILD.name: {"going": [],},
    src.agent.Agent.Motive.SOCIALIZE_LOVER.name: {"going": [],},
    src.agent.Agent.Motive.SOCIALIZE_FRIEND.name: {"going": [],},
    src.agent.Agent.Motive.SOCIALIZE_ENEMY.name: {"going": [],},
    src.agent.Agent.Motive.PROPAGATE.name: {"going": [],},
    src.agent.Agent.Motive.REST.name: {"going": [],},
    src.agent.Agent.Motive.REPLENISH_TREE.name: {"going": [],},
    src.agent.Agent.Motive.IDLE.name: {"going": [],},
    src.agent.Agent.Motive.WATER.name: {"going": [],},

}

LINES_PER_PAGE = 15
MAX_TEXT_PER_PAGE = LINES_PER_PAGE*23
MAX_PAGES_PER_BOOK = 4

chronicles = [['']]  # array of BOOKS with arrays of PAGE text
chronicle_book_index = 0
chronicle_page_index = 0

def make_book(text_pages, title ="", author ="", desc =""):
    bookstart = "pages:["
    pages_nbt = []
    for text in text_pages:
        bookpage = ''
        while len(text) > 0:
            page = text[:MAX_TEXT_PER_PAGE]
            text = text[MAX_TEXT_PER_PAGE:]
            bookpage = "'{\"text\":\""
            # bookpage = ""
            while len(page) > 0:
                line = page[:LINES_PER_PAGE]
                page = page[LINES_PER_PAGE:]
                bookpage += line+''
        bookpage += "\"}\'"
        pages_nbt.append(bookpage)


    booktitle = "title:\""+title+"\","
    bookauthor = "author:\""+author+"\","
    bookdesc = "display:{Lore:[\""+desc+"\"]}"

    result = "written_book{"+bookstart
    i = 0
    length = len(text_pages)
    for text in pages_nbt:
        result += text
        i += 1
        if i < length:
            result += ','
        else:
            result += '],'
            pass
    result += booktitle+bookauthor+bookdesc+"}"
    return result

def add_item_to_chest(x, y, z, items):
    for id,v in enumerate(items):
        command = "replaceitem block {} {} {} {} {} {}".format(x, y, z,
                                                               "container."+str(id),
                                                               v[0],
                                                               v[1])
        print(command) # run commund here

def append_to_chronicle(new_text):
    global chronicle_page_index, chronicle_book_index
    text = chronicles[chronicle_book_index][chronicle_page_index] + new_text
    if len(text) > MAX_TEXT_PER_PAGE:
        if chronicle_page_index < MAX_PAGES_PER_BOOK:
            chronicle_page_index += 1
            chronicles[chronicle_book_index].append(new_text)
        elif chronicle_book_index+1 < 30:  # add new book if there's space in chest
            chronicle_page_index = 0
            chronicle_book_index += 1
            chronicles.append([new_text])  # append BOOK with PAGE
    else:
        chronicles[chronicle_book_index][chronicle_page_index] += new_text

def create_chronicles(title, author):
    result = []
    i = 0
    for book in chronicles:
        curr_title = title+f" {str(i)}"
        result.append((make_book(book, title, author),1))
        i+=1
    return result
