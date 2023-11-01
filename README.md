# PMC_classifiers
Training machine learning classifiers on PubMed Central data


In this project we will try to train machine learning models that are useful for characterizing and indexing medical literature. We will work on documents that are freely available from the PubMed Central repository at the US National Library of Medicine, but our goal is to develop models that can be broadly applied to biomedical text.

Pubmed Central data can be obtained by running a search here:
https://www.ncbi.nlm.nih.gov/pmc

To retrieve a reasonably small dataset, I ran the query “vaccine allergy”, limiting the results to the past one year. Results we saved to an XML file by selecting “Send to”, “File”, then “XML”. The notebook “PMC_data_extraction.ipynb” pulls a tabular dataset from this file, where each row represents a paragraph of text and includes columns for the article ID (PMID), the paragraph number within the article (paragraph 0 is the title), and the ‘section path’ (a concatenation of all the section and subsection headings leading to that paragraph). A sample of the formatted data for 100 randomly selected articles in in the file 'example_data.zip'.

