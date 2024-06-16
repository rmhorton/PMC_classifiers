#! ~/anaconda3/envs/nlp/bin/python


# This file has a symbolic link in ~/bin, and executable permissions.
# ln -s ~/Documents/pmc_code/load_pubmed.py load_pubmed


# To do:
# journal.find('ISOAbbreviation') may not exist

import pandas as pd
import pickle
from collections import defaultdict
import os
import gzip
import xml.etree.ElementTree as ET
import argparse

parser = argparse.ArgumentParser(
    description="Extract tabular structured data from a single gzipped pubmed XML file and format as a collection of CSV files in the specified directory. This script also includes helper functions for collecting detail pickle files into CSV tables, and for creating and loading the tables in a PostgreSQL database. The script has executable permissions, and a softlink from ~/bin to put it on the command path. (ln -s ~/Documents/pmc_code/load_pubmed.py load_pubmed.py)",
    epilog='''
    Examples:
    # process one archived XML file
    load_pubmed /data/pubmed/pubmed24n0001.xml.gz

    # Process all of the archived XML files
    find /data/pubmed -name *.xml.gz | parallel --jobs 12 load_pubmed --out_dir ~/pubmed_tmp &>> ~/pubmed_tmp/log.txt

    Be sure not to run too many jobs in parallel, since they each take quite a bit of memory.
    
    # Collect dict files into detail tables
    load_pubmed no_xml_file --mode collect --out_dir ~/pubmed_tmp
    
    # Generate the SQL to create the tables and fill them with data from the CSV files:
    load_pubmed no_xml_file --mode load > load_pubmed_tables.sql
    
    # Run the SQL commands
    sudo su pmc_admin
    psql dbname -d pmc < load_pubmed_tables.sql
'''
)
parser.add_argument("xml_file", help="Full path to the pubmed XML file for an article set.")
parser.add_argument("--out_dir", help="output directory", default=os.getcwd())
parser.add_argument("--mode", help="extract, collect, or load", choices=['extract', 'collect', 'load'], default='extract')


def merge_defaultdicts(dd1, dd2):
    for k,v in dd2.items():
        if (k in dd1):
            dd1[k].update(dd2[k])
        else:
            dd1[k] = dd2[k]
    return dd1
    

def dds2df(dds):
    """
    Reformat a defaultdictionary(set) as a 2-column dataframe.
    """
    return pd.DataFrame( [ {'qualifier_id': k, 'qualifier_name': '|'.join(sorted(s)) } for k,s in dds.items() ] )


def get_mesh_data(article):
    
    pmid = article.find('MedlineCitation/PMID').text
    mesh_heading_list = article.findall('MedlineCitation/MeshHeadingList/MeshHeading')
    
    journal = article.find('MedlineCitation/Article/Journal')
    journal_isoabbr = journal.find('ISOAbbreviation').text
    issn_node = journal.find('ISSN')
    if issn_node is not None:
        journal_id = issn_node.text
    else:
        journal_id = journal_isoabbr
    
    journal_title_lookup = defaultdict(set)
    journal_title_lookup[journal_id].add(journal.find('Title').text + ':::' + journal_isoabbr)
    
    issue_pubdate_year = journal.find('JournalIssue/PubDate/Year') # Year
    if issue_pubdate_year is not None:
        pub_year = issue_pubdate_year.text
    else:
        medline_date = journal.find('JournalIssue/PubDate/MedlineDate').text # Always present if year is not (???)
        pub_year = medline_date.split(' ')[0]
        
    issue_info = {
        'pmid': pmid,
        'journal_id': journal_id,
        'date': pub_year
    }

    dnames = defaultdict(set)
    qnames = defaultdict(set)
    descriptor_rows = []
    qualifier_rows = []
    for mh in mesh_heading_list:
        desc = mh.find('DescriptorName')
        descriptor_id = desc.attrib['UI']
        dnames[descriptor_id].add(desc.text)
        descriptor_rows.append({'pmid': pmid, 'descriptor_id': descriptor_id, 
                                'descriptor_major': desc.attrib['MajorTopicYN']})
        q_list = mh.findall('QualifierName')
        for qualifier in q_list:
            qnames[qualifier.attrib['UI']].add(qualifier.text)
            q_row = {'pmid': pmid, 'descriptor_id': descriptor_id, 'qualifier_id': qualifier.attrib['UI'], 
                     'qualifier_major': qualifier.attrib['MajorTopicYN']}
            qualifier_rows.append(q_row)
    
    descriptor_df = pd.DataFrame(descriptor_rows)
    qualifier_df = pd.DataFrame(qualifier_rows)

    return descriptor_df, qualifier_df, dnames, qnames, issue_info, journal_title_lookup


def process_articles(articles, filestem, outdir):

    # Lists of dataframes to be collected from articles.
    ddf_list = [] # descriptors; list of dataframes, to be concatenated
    qdf_list = [] # qualifiers
    ji_rows = [] # journal issue; list of row dicts, to be made into a dataframe
    ta_rows = [] # rows for title_abstract_table: pmid, title, text

    # Collect name-lookup tables for descriptors, qualifiers, and journal titles.
    # I'm using defaultdicts where the values are sets in case more than one name is assigned to a given ID.
    # The only example I have found so far is 'D000078202  Systematic Review as Topic|Systematic Reviews as Topic'
    d_dd = defaultdict(set)
    q_dd = defaultdict(set)
    j_dd = defaultdict(set)
    
    for article in articles:
        ddf, qdf, dnames, qnames, issue_info, journal_title = get_mesh_data(article)
        ddf_list.append(ddf)
        qdf_list.append(qdf)
        ji_rows.append(issue_info)
        d_dd = merge_defaultdicts(d_dd, dnames)
        q_dd = merge_defaultdicts(q_dd, qnames)
        j_dd = merge_defaultdicts(j_dd, journal_title)  # Note: merging ordinary dict into defaultdict(set)

        pmid = article.find('MedlineCitation/PMID').text
        mca_node = article.find('MedlineCitation/Article')
        abstract_node = mca_node.find('Abstract/AbstractText')
        if abstract_node is not None:
            abstract = abstract_node.text
        else:
            abstract = ''
        ta_rows.append({'pmid': pmid, 'title':mca_node.find('ArticleTitle').text, 'abstract': abstract})

    
    descriptor_table = pd.concat(ddf_list)
    qualifier_table = pd.concat(qdf_list)
    journal_issue_table = pd.DataFrame(ji_rows)
    title_abstract_table = pd.DataFrame(ta_rows)
    
    # Save tables as CSV
    descriptor_table.to_csv(os.path.join(outdir, filestem + '_descriptor.csv'), index=False, header=False)
    qualifier_table.to_csv(os.path.join(outdir, filestem + '_qualifier.csv'), index=False, header=False)
    journal_issue_table.to_csv(os.path.join(outdir, filestem + '_journal_issue.csv'), index=False, header=False)
    title_abstract_table.to_csv(os.path.join(outdir, filestem + '_title_abstract.csv'), index=False, header=False)

    # Save ddicts as pickle files.
    with open(os.path.join(outdir, filestem + '_descriptor_ddict.pkl'), 'wb') as ddd_fh:
        pickle.dump(d_dd, ddd_fh, protocol=pickle.HIGHEST_PROTOCOL)
    with open(os.path.join(outdir, filestem + '_qualifier_ddict.pkl'), 'wb') as qdd_fh:
        pickle.dump(q_dd, qdd_fh, protocol=pickle.HIGHEST_PROTOCOL)
    with open(os.path.join(outdir, filestem + '_journal_ddict.pkl'), 'wb') as jdd_fh:
        pickle.dump(j_dd, jdd_fh, protocol=pickle.HIGHEST_PROTOCOL)


def process_pubmed_file(xmlgz, outdir):
    """ 
    Process a gzipped XML file downloaded from the [pubmed ftp site](https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/). 
    This assumes you have already validated the file against the md5 hashes pubmed provides. 
    """
    print(f"process_pubmed_file: outdir = {outdir}")
    root = ET.parse(gzip.open(xmlgz, 'r')).getroot()
    articles =  root.findall('PubmedArticle')
    filestem = os.path.basename(xmlgz).split('.')[0]
    process_articles(articles, filestem, outdir)


def collect_ddicts(suffix = 'descriptor', outdir='tmp_tables', verbose=False):
    dd_list = [f for f in os.listdir(outdir) if f.endswith(f'_{suffix}_ddict.pkl')]
    with open(os.path.join(outdir, dd_list[0]), 'rb') as fh:
        big_dd = pickle.load(fh)
        if verbose: print(f"{dd_list[0]} has length {len(big_dd)}")
    for dd_f in dd_list[1:]:
        with open(os.path.join(outdir, dd_f), 'rb') as fh:
            next_dd = pickle.load(fh)
        if verbose: print(f"{dd_f} has length {len(next_dd)}")
        big_dd = merge_defaultdicts(big_dd, next_dd)

    if verbose: print(f"collected dd has length {len(big_dd)}")
    big_df = pd.DataFrame( [ {'uid':k, 'name': '|'.join(sorted(v))} for k, v in big_dd.items()] )
    big_df.to_csv(os.path.join(outdir, suffix + '_detail.csv'), index=False, header=False)


SCHEMA = {
    'journal_issue': [ "pmid int", "journal_id text", "year text" ],
    'title_abstract': [ 'pmid int', 'title text',  'abstract text' ],
    'journal_detail': [ 'id text', 'title text' ],
    'descriptor_detail': [ 'id varchar(10)', 'name text'],
    'qualifier_detail': [ 'id varchar(10)', 'name text' ],
    'descriptor': [ 'pmid int', 'descriptor_id varchar(10)', 'MajorTopicYN char(1)'],
    'qualifier': [ 'pmid int', 'descriptor_id varchar(10)', 'qualifier_id varchar(10)', 'MajorTopicYN char(1)'],
}

def get_create_table_sql():
    sql = ''
    for table, declarations in SCHEMA.items():
        declarations_str = ",\n\t".join(declarations)
        sql += f"DROP TABLE IF EXISTS {table};\n"
        sql += f"CREATE TABLE {table}(\n\t{declarations_str}\n);\n\n"
    return sql


def get_load_tables_commands(out_dir):
	
    table_columns = { k: [col_name_type.split(' ')[0] for col_name_type in v] for k, v in SCHEMA.items() }

    detail_cmds = []
    detail_files = [f for f in os.listdir(out_dir) if f.endswith('_detail.csv')]
    for filename in detail_files:
        filepath = os.path.join(out_dir, filename)
        table = filename.replace('.csv', '')
        detail_cmds.append(f"COPY {table}({', '.join(table_columns[table])}) from '{filepath}' CSV;\n")
        
    pubmed_cmds = []
    pubmed_files = [f for f in os.listdir(out_dir) if f.startswith('pubmed') and f.endswith('.csv')]
    for filename in pubmed_files:
        filepath = os.path.join(out_dir, filename)
        parts = filename.replace('.csv', '').split('_')
        filestem = parts[0]
        table = filename.replace('.csv', '').replace(filestem + '_', '')
        pubmed_cmds.append(f"COPY {table}({', '.join(table_columns[table])}) from '{filepath}' CSV;\n")

    return "\n".join(detail_cmds) + "\n" + "\n".join(sorted(pubmed_cmds))
    

if __name__ == '__main__':
	args = parser.parse_args()

	if args.mode == 'extract':
		print(f"Processing {args.xml_file} and putting results in {args.out_dir}")
		process_pubmed_file(args.xml_file, args.out_dir)
	elif args.mode == 'collect':
		print("Collecting pickle files into CSV tables.")
		detail_tables = [dtab for dtab in SCHEMA.keys() if dtab.endswith('_detail')]
		for dtab in detail_tables:
		    my_suffix = dtab.replace('_detail', '')
		    collect_ddicts(suffix = my_suffix, outdir=args.out_dir, verbose=False)
	elif args.mode == 'load':
		print("-- Generating SQL commands to create tables and load CSV files.")
		sql = get_create_table_sql()
		sql += get_load_tables_commands(args.out_dir)
		print(sql)


# TO DO: 
#  1. collect dicts from pickle files into detail.csv files 
#  2.a create tables
#  2.b load CSV files into postgres.
# pubmed24n1218_descriptor.csv
# pubmed24n1218_descriptor_ddict.pkl  -> collect into "descriptor_detail.csv"
# pubmed24n1218_qualifier.csv
# pubmed24n1218_qualifier_ddict.pkl   -> collect into "qualifier_detail.csv"
# pubmed24n1218_journal_ddict.pkl     -> collect into "journal_detail.csv"
# pubmed24n1218_journal_issue.csv
# pubmed24n1218_title_abstract.csv
