#! /home/rmhorton/anaconda3/envs/nlp/bin/python

# This file has a symbolic link in ~/bin, and executable permissions.

import pandas as pd
import xml.etree.ElementTree as ET
import os

import argparse

parser = argparse.ArgumentParser(
    description='Extract text data from PMC XML file and format as a CSV file in the working directory.',
    epilog='''
    Example: 
    cd /data/pmc_tables
    mkdir PMC007xxxxxx
    mkdir ~/pmc_tmp/PMC007xxxxxx
    cd PMC007xxxxxx
    tar -xf /data/pmc/oa_comm_xml.PMC007xxxxxx.baseline.2023-12-18.tar.gz -C ~/pmc_tmp/PMC007xxxxxx
    sudo find ~/pmc_tmp/PMC007xxxxxx -name *.xml | parallel ~/bin/pmc_xml2csv.py >> log.txt
    rm -r ~/pmc_tmp/*
    cd ~/pmc_tmp
    tar -czvf pmc_tables_batch1.tar.gz /data/pmc_tables  # super slow! Try pigz
    tar cf - /data/pmc_tables | pigz -p 24 > pmc_tables_batch1b.tar.gz
    tar -c --use-compress-program=pigz -f pmc_tables_batch1c.tar.gz /data/pmc_tables

'''
)
parser.add_argument("xml_file", help="Full path to the PMC XML file for a single article.")
args = parser.parse_args()



def get_section_text(sec, header_path=[]):
    # sec elements can be nested.
    # Here I assume all narrative text is within <p> elements.
    my_header_path = header_path.copy()
    title_element = sec.find('title')
    if title_element is not None:  # type(title_element) != type(None): 'NoneType':
        my_header_path.append( ''.join(title_element.itertext()) ) 
    my_title = ' || '.join(my_header_path)  # flattened path for (sub)section header
    results = [] # list of tuples (title, text) tuples
    for child in sec:
        if child.tag == 'p':
            results.append( tuple(( my_title, ''.join(child.itertext()) )) )
        elif child.tag == 'sec': # subsection
            subsection_results = get_section_text(child, my_header_path)
            for ssres in subsection_results:
                results.append(ssres)
    
    return results


def get_title(art):
    title = 'MISSING'
    title_list = art.findall("front/article-meta/title-group/article-title")
    if len(title_list) > 0:
        title = ''.join(title_list[0].itertext())
    return title


def get_abstract(art):
    abstract = 'MISSING'
    abstract_element = art.find("front/article-meta/abstract")
    results = []
    if abstract_element is not None:
        for c in abstract_element:
            if c.tag == 'p':
                t = ''.join( [t for t in c.itertext()])
                results.append( tuple(( 'Abstract', t )) )
            elif c.tag == 'sec':
                sub_results = get_section_text(c, ['Abstract'])
                for sr in sub_results:
                    results.append(sr)
    return results


def get_article_id(art):
    art_id_list = art.findall('front/article-meta/article-id')

    pmid = 'MISSING'
    for aid in art_id_list:
        if aid.attrib['pub-id-type'] == 'pmid':
            pmid = aid.text
            break
    return pmid
    

def get_article_text(art):
    """
    art: an ElementTree representng an article from Pubmed Central results
    Returns a list with one tuple for each paragraph in each section in an article. 
    The elements of each tuple are a flattened section heading path and a paragraph text string.
    """
    results = []

    results.append( tuple(( 'Title', get_title(art) )) )

    abstract_rows = get_abstract(art)
    for abrow in abstract_rows:
        results.append(abrow)
    
    for sec in art.findall('body/sec'):
        for ssres in get_section_text(sec):
            results.append(ssres)
            
    return results


def get_article_df(art):
    results = []
    
    art_id = get_article_id(art)
    art_rows = get_article_text(art)
    paragraph_number = 0
    for arow in art_rows:
        results.append( tuple((art_id, paragraph_number, arow[0], arow[1])) )
        paragraph_number += 1
    
    return pd.DataFrame(results, columns=['pmid', 'paragraph_number', 'section_path', 'text'])


article_xml_file = args.xml_file

p1, f = os.path.split(article_xml_file)
_, d = os.path.split(p1)

csv_file = f"{d}_{f.replace('.xml', '.csv')}"

# print(f"Extract text from '{args.xml_file}' to '{csv_file}'")

article = ET.parse(article_xml_file).getroot()
article_df = get_article_df(article)

if article_df['pmid'][0] == 'MISSING':
    print(article_xml_file, 'MISSING_PMID')
else:
    print(article_xml_file, len(article_df))
    article_df.to_csv(csv_file, index=False)
