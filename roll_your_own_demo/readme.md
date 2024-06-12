This is a set of Python notebooks showing how to build a dataset from the results of a Pubmed query, and use it to train models.

Pubmed Central data can be obtained by running a search here:
https://www.ncbi.nlm.nih.gov/pmc

To retrieve a reasonably small dataset, I ran the query “vaccine allergy”, limiting the results to the past one year. Results were saved to an XML file by selecting “Send to”, “File”, then “XML”. The notebook “PMC_data_extraction.ipynb” pulls a tabular dataset from this file, where each row represents a paragraph of text and includes columns for the article ID (PMID), the paragraph number within the article (paragraph 0 is the title), and the ‘section path’ (a concatenation of all the section and subsection headings leading to that paragraph). A sample of the formatted data for a few randomly selected articles in in the file 'example_data.zip'.
