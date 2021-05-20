import src.agent
import http_framework.interfaceUtils
import src.states
from random import choice, random
import run
import wonderwords

word_picker = wonderwords.RandomWord()

chronicle_events = {
    "LOGGING": {"going": ["{a.name} wrote one {A} song about {l.name}. It became a local hit.", "{a.name} catalogued some {A} variety of fauna during their walk."],
                "doing": ["{a.name} discovered a{n} {A} style of log-cutting! It was shared amongst friends.", "{a.name} hacked away at a{n} {A} {a.last_log_type} tree."]},
    "BUILD": {"going": ["{a.name} gathered {A} supplies to follow the {a.build_params[4][11:]} blueprint!", "{a.name} gathered advice from {l.name} for their next building project."],
              "doing": ["{a.name} built based on the {a.build_params[4][11:]} blueprint. It turned out straight {A}.", "{a.name}\\'s {A} {a.build_params[4][11:]} rendition was told of across the land!"],},
    "SOCIALIZE_LOVER": {"doing": ["{a.name} and {l.name} exchanged {A} gifts to express their honeymoon.", "{a.name} and {l.name} shouted thankful words for {a.parent_1.name}\\'s approval for their marriage!"],},
    "SOCIALIZE_FRIEND": {"doing": ["{a.name} and {s.name} found spare time perform a joint spiritual rite the {A} deity!", "{a.name} and {s.name}\\'s {A} collectively discovered how to craft with {A} logs!"],},
    "SOCIALIZE_ENEMY": {"doing": ["{a.name} insulted {s.name}\\'s parent, {s.parent_1.name}, for their {A}-ness.", "{a.name} and {s.name} broke into a{n} {A} sparring match after an insult was flung towards {l.name}."],},
    "PROPAGATE": {"doing": ["{a.name} blessed the land with {c.name}- named for their {A}-ness!", "{a.name} found time in their busy day to bear {c.name}! The deities said they\\'ll be {A}."],},
    "REST": {"going": ["{a.name} was seen sleepwalking while speaking {A} things of {l.name}.", "Gossip spread about {a.name}, saying they were ditching work to conjure {A} dreams."],
                 "doing": [""],},
    "REPLENISH_TREE": {"going": [],
                       "doing": ["{a.name} grew a tree with a distinctly {A} characteristic.", "{a.name} nurtured a tree so large, it could occupy even the most {A} of loggers!"]},
    "IDLE": {"going": [],},
    "WATER": {"doing": ["{a.name} was ailed with the {A} by drinking from the local watering hole.", "{a.name} caught a {A} fish during their water-break! {l.name} cooked it for their friends and family.", "{a.name} asserted the watering hole to be {A}. {l.name} was sent to investigate it."],},
}

LINES_PER_PAGE = 13 # actually is 18 but need buffer
MAX_TEXT_PER_PAGE = LINES_PER_PAGE*18 # actually is 23 but need buffer
MAX_PAGES_PER_BOOK = 4

chronicles_empty = [['']]
chronicles = chronicles_empty.copy()  # array of BOOKS with arrays of PAGE text
chronicle_book_index = 0
chronicle_page_index = 0

def chronicle_event(threshold_rate, motive, subcategory, time, agent, support=None):
    if not run.IS_WRITING_CHRONICLE: return
    adjective = word_picker.random_words(include_parts_of_speech=['adjectives'])[0]
    adjective_mod = 'n' if adjective[0] in ['a','e','i','o','u'] else ''
    try:
        if random() < threshold_rate:
            lover = agent.lover if agent.lover != None else agent.parent_2
            choices = choice(chronicle_events[motive][subcategory])
            child = None if len(agent.children) < 1 else agent.children[-1]
            result = choices.format(t=time, a=agent, l=lover, s=support, c=child, A=adjective, n=adjective_mod)
            result = f"{time}PC: " + result
            if run.IS_WRITING_CHRONICLE_TO_CONSOLE: print(result.replace('\\', ''))
            result += '^'  # for newline replacement
            append_to_chronicle(result)
    except TypeError:
        pass

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


def make_book(text_pages, title ="", author ="", desc =""):
    # append empty lines with spaces
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
                line = line.replace('^', ' ' * (LINES_PER_PAGE - len(line)-2) + '\\\\n')  # empty spaces up to line count
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

def add_items_to_chest(x, y, z, items):
    for id,v in enumerate(items):
        command = "replaceitem block {} {} {} {} {} {}".format(x, y, z,
                                                               "container."+str(id),
                                                               v[0],
                                                               v[1])
        http_framework.interfaceUtils.runCommand(command)

def create_chronicles(title, author):
    result = []
    i = 0
    for book in chronicles:
        curr_title = title+f" {str(i+1)}"
        result.append((make_book(book, curr_title, author),1))
        i+=1
    return result

def place_chronicles(state, x,y,z, title, author):
    nbt_books = create_chronicles(title, author)
    # src.states.set_state_block(state, x,y,z, "minecraft:chest")
    ax = state.world_x+x
    ay = state.world_y+y
    az = state.world_z+z
    add_items_to_chest(ax, ay, az, nbt_books)
    # still need to step afterwards to render

def setSignText(x, y, z, line1 = "", line2 = "", line3 = "", line4 = ""):
    l1 = 'Text1:\'{"text":"'+line1+'"}\''
    l2 = 'Text2:\'{"text":"'+line2+'"}\''
    l3 = 'Text3:\'{"text":"'+line3+'"}\''
    l4 = 'Text4:\'{"text":"'+line4+'"}\''
    blockNBT = "{"+l1+","+l2+","+l3+","+l4+"}"
    http_framework.interfaceUtils.runCommand("data merge block {} {} {} ".format(x, y, z)
                              + blockNBT)

def write_coords_to_sign(x,y,z,start_xz, chronicle_coords):
    if run.IS_WRITING_CHRONICLE:
        setSignText(x,y,z,f"result x {start_xz[0]}", f"result z {start_xz[1]}", "chronicles at", f"{start_xz[0]}, {start_xz[1]}")
    else:
        setSignText(x,y,z,f"result x {start_xz[0]}", f"result z {start_xz[1]}")
