import csv
import numpy as np
from bs4 import BeautifulSoup
import requests
import re

wordsList = []

with open('tsv_dict_original.csv', 'r', encoding="utf-8") as file:
    # Create a CSV reader object
    currentDefinition = {"headword": "", "inflectedForms": [], "html": ""}

    for line in file:
        if line[0] == "@":
            currentDefinition["headword"] = line[2:].strip()
        elif line[0] == "<":
            currentDefinition["html"] = line.strip()
            wordsList.append(currentDefinition)
            currentDefinition = {"headword": "",
                                 "inflectedForms": [], "html": ""}
        else:
            print("Error")
            break


def getIndexOfHeadword(word):
    for i in range(len(wordsList)):
        if wordsList[i]["headword"] == word:
            return i
    return -1


print(f"Number of words = {len(wordsList)}")


def getEclipsedForm(word):
    eclipsingDictionary = {
        "b": "m",
        "c": "g",
        "d": "n",
        "f": "bh",
        "g": "n",
        "p": "b",
        "t": "d"
    }

    if word[0] in "bcdfgpt":
        return eclipsingDictionary[word[0]] + word
    elif word[0] in "BCDFGPT":
        return eclipsingDictionary[word[0].lower()] + word
    elif word[0] in "aeiouáéíóú":
        return "n-" + word
    elif word[0] in "AEIOUÁÉÍÓÚ":
        return "n" + word
    else:
        return word


def getLenitedForm(word):
    if len(word) > 1:
        if word[0] in "bcdfgmpstBCDFGMPST":
            return word[0] + "h" + word[1:]
        else:
            return word
    else:
        return word


def getHProsthesis(word):
    if word[0] in "aeiouáéíóúAEIOUÁÉÍÓÚ":
        return "h" + word
    else:
        return word


def getTProsthesis(word):
    if word[0] in "aeiouáéíóú":
        return "t-" + word
    elif word[0] in "AEIOUÁÉÍÓÚsS":
        return "t" + word
    else:
        return word


def getMutatedForms(word):
    return list(set([word, getEclipsedForm(word), getLenitedForm(word), getHProsthesis(word), getTProsthesis(word)]))


def getInflectedForms(headword_index):
    headword = wordsList[headword_index]["headword"]
    print(f"Getting inflected forms for {headword} ({headword_index+1}/53998)")
    inflectedForms = []

    resp = requests.get(f"https://www.teanglann.ie/en/gram/{headword}")

    if resp.ok:
        soup = BeautifulSoup(resp.text, "html.parser")
        # print(soup.prettify())

        gram = [element for element in soup.find_all(
            class_="gram") if element.get("class") == ["gram"]]
        # print(f"len of gram = {len(gram)}")

        for g in gram:
            wordCategory = g.select(".header .property .value")[0].string

            if wordCategory == "VERB":
                vn_h3 = g.find('h3', text='VERBAL NOUN')
                if vn_h3:
                    verbal_noun = vn_h3.find_next('div').find_all("span")[0].string
                    [inflectedForms.append(x) for x in getMutatedForms(verbal_noun)]

                va_h3 = g.find('h3', text='VERBAL ADJECTIVE')
                if va_h3:
                    verbal_adj = va_h3.find_next('div').find_all("span")[0].string
                    [inflectedForms.append(x) for x in getMutatedForms(verbal_adj)]

                for tense in ["past", "present", "future", "condi", "pastConti", "imper", "subj"]:
                    formsList = [x.string for x in g.select(
                        f"#{tense} .value")]
                    for form in formsList:
                        if form.split(" ")[0] in ["ar", "níor", "an", "ní", "ná", "go", "nár"]:
                            inflectedForms.append(
                                re.sub(r'[\?!]', '', form.split(" ")[1]))
                        else:
                            inflectedForms.append(
                                re.sub(r'[\?!]', '', form.split(" ")[0]))

            elif wordCategory == "ADJECTIVE":
                forms = [x.string.split(" ")[-1]
                         for x in g.select(".content .value")]
                [inflectedForms.append(form) for form in list(set(forms))]

            elif wordCategory == "NOUN":
                forms = [x.string for x in g.select(".content .value.primary")]

                for form in forms:
                    # print(f"form = {form}")

                    for mutatedForm in getMutatedForms(form):
                        # print(f"mutatedForm = {mutatedForm}")
                        inflectedForms.append(mutatedForm)
            elif wordCategory == "PREPOSITION":
                forms = [x.string for x in g.select(".content .value.primary")]
                [inflectedForms.append(form) for form in list(set(forms))]

    else:
        print("Error {}".format(resp.status_code))
        print(resp.text)

    inflectedForms = list(set([x for x in inflectedForms if x != headword]))
    # print(inflectedForms)

    wordsList[headword_index]["inflectedForms"] = inflectedForms


# getInflectedForms(getIndexOfHeadword("glan"))

def getAllInflectedForms():
    for wordIndex in range(len(wordsList)):
        getInflectedForms(wordIndex)

def writeWordsList():
    with open('tsv_dict_inflections.csv', 'w', encoding="utf-8") as outputFile:
        for wordIndex in range(30232, len(wordsList)):
            getInflectedForms(wordIndex)

            print(f"Writing {wordsList[wordIndex]['headword']}")
            outputFile.write("@ " + wordsList[wordIndex]["headword"] + "\n")
            
            for inflectedForm in wordsList[wordIndex]["inflectedForms"]:
                outputFile.write("& " + inflectedForm + "\n")
            outputFile.write(wordsList[wordIndex]["html"] + "\n")

writeWordsList()