# These are installed dependencies
import bs4, pdfkit, PyPDF2
from selenium import webdriver
# comes with python
import re, os, io
from pathlib import Path


def make_dir_scip_files():
    path = "scipFiles"
    try:
        os.mkdir(path)
    except OSError:
        print("Creation of the directory %s failed" % path)
        return False
    else:
        print("Successfully created the directory %s " % path)
        return True


def get_info_from_site(source_url):

    browser = webdriver.Chrome(r"chromedriver.exe")
    browser.get(source_url)
    soup = bs4.BeautifulSoup(browser.page_source, features="html.parser")
    browser.close()

    # check if page is 404 and end if it is
    title = soup.select('title')[0].getText()
    if title == "404 Not Found":
        check_invalid_site = True
    else:
        check_invalid_site = False

    if check_invalid_site:
        return {"done": True}

    # get name
    chapter_title = soup.select_one('.chapter-title').getText()
    chapter_title.replace("\n", "")
    chapter_title = re.sub("\\s\\s+", " ", chapter_title)
    chapter_title = re.sub("[:\\?]", "", chapter_title)
    chapter_title = chapter_title.lstrip().rstrip()

    chapter_text = soup.select_one('.chapter-text')

    return {"done": False, "chapter_title": chapter_title, "chapter_text": chapter_text}


def create_temp_html(chapter_title, chapter_text, url):
    template = open("templateHtmlScip.html")
    template_soup = bs4.BeautifulSoup(template, features="html.parser")
    template.close()

    chapter_title_tag = template_soup.select_one('a,#a-chapter-title')
    chapter_title_tag["href"] = url
    chapter_title_tag.string = chapter_title
    template_soup.select_one('.chapter_sign').string = chapter_title

    # modify chapter_text
    for tag in chapter_text.select(".superscript"):
        del tag["href"]
    for tag in chapter_text.select(".footnote-number"):
        del tag["href"]
    template_soup.select_one('.chapter-text').replace_with(chapter_text)
    template_soup = str(template_soup)

    temp_file = io.open("tempHtml.html", "w", encoding="utf8")
    temp_file.write(template_soup)
    temp_file.close()


def scrape_and_download(start=1, end=49, chapter_txt=False):
    # scrape files from site
    website_base = "https://www.comp.nus.edu.sg/~cs1101s/sicp/chapters/"
    chapter = start
    writing = False
    if chapter_txt:
        file = open("chapterReference.txt", "w")
        writing = True
    make_dir_scip_files()
    if not Path("scipFiles").exists():
        return "scipFiles not found"
    while True:
        source_url = website_base + str(chapter)

        site_info = get_info_from_site(source_url)
        if site_info["done"]:
            print("Chapter {0} is the last chapter".format(str(chapter - 1)))
            if writing:
                file.close()
            return True
        chapter_title = site_info["chapter_title"]

        # make pdf if it doesnt already exist
        chapter_path = "scipFiles/{0}.pdf".format(chapter_title)
        if Path(chapter_path).exists():
            print("Chapter {0}: '{1}' already exists".format(chapter, chapter_title))
        else:
            # bit which actually makes the pdf file
            create_temp_html(chapter_title, site_info["chapter_text"], source_url)

            pdfkit.from_file("tempHtml.html", chapter_path, options={"log-level": "none"})
            print("Chapter {0}: '{1}' created".format(chapter, chapter_title))

        # iterate
        if writing:
            file.write("Chapter {0}: '{1}'\n".format(chapter, chapter_title))
        if chapter == end:
            if writing:
                file.close()
            os.remove("tempHtml.html")
            return True
        chapter += 1


def pdf_merge(name="SCIP Javascript Adaptation"):
    # checks
    if not Path("scipFiles").exists():
        return "scipFiles not found"
    # prepare pdf files
    output_pdf_name = name + ".pdf"
    files = os.listdir("scipFiles/")
    files.sort()
    files_to_merge = []
    file_names = []

    # get PDF files
    for file in files:
        file_path = "scipFiles/" + file
        try:
            next_pdf_file = PyPDF2.PdfFileReader(open(file_path, "rb"))
        except PyPDF2.utils.PdfReadError:
            print("{0} is not a valid PDF file.".format(file_path))
        else:
            files_to_merge.append(next_pdf_file)
            file_names.append(file[:-4])
            print(file + " appended")

    # merge page by page
    output_pdf_stream = PyPDF2.PdfFileWriter()
    j = 0
    k = 0
    for f in files_to_merge:
        for i in range(f.numPages):
            output_pdf_stream.addPage(f.getPage(i))
            if i == 0:
                output_pdf_stream.addBookmark(str(file_names[k]), j)
            j = j + 1
        k += 1

    # create output pdf file
    try:
        output_pdf_file = open(output_pdf_name, "wb")
        output_pdf_stream.write(output_pdf_file)
    finally:
        output_pdf_file.close()

    print("%s successfully created." % output_pdf_name)


# start program
# print("usable functions are scrapeAndDownload(start=1,end=1,chapter_txt=False) and pdf_merge(name='textbook')")
# print("scrape_and_download(start=1, end=49, chapter_txt=False)")
def main_program():
    if input("scrap_and_download? (y/n)") == "y":
        start = int(input("start"))
        end = int(input("end"))
        if input("chapter_txt") == "y":
            chapter_txt = True
        else:
            chapter_txt = False
        scrape_and_download(start, end, chapter_txt)
    elif input("pdf_merge? (y/n)") == "y":
        name = input("name")
        pdf_merge(name)


main_program()